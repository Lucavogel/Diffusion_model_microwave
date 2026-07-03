#!/usr/bin/env python3

import math
from pathlib import Path
from typing import List, Tuple

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]

WRAPPABLE_JOINTS = {
    "shoulder_pan_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
}


def parse_sequence_file(path: Path) -> List[Tuple[str, List[float] | float]]:
    sequence: List[Tuple[str, List[float] | float]] = []
    for raw_line in path.read_text(encoding="ascii").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lowered = line.lower()
        if lowered.startswith("pause ") or lowered.startswith("wait "):
            sequence.append(("pause", float(line.split(maxsplit=1)[1])))
            continue
        if lowered.startswith("joints ") or lowered.startswith("joint "):
            values = [float(v) for v in line.split()[1:]]
            if len(values) != 6:
                raise ValueError(f"Waypoint articulaire invalide: {line}")
            sequence.append(("joints", values))
            continue
        raise ValueError(f"Ligne non supportee pour l'execution directe: {line}")
    return sequence


def wrap_near_reference(target: List[float], reference: List[float]) -> List[float]:
    adjusted = list(target)
    for index, joint_name in enumerate(JOINT_NAMES):
        if joint_name not in WRAPPABLE_JOINTS:
            continue
        best = adjusted[index]
        best_distance = abs(best - reference[index])
        for k in range(-2, 3):
            candidate = target[index] + k * 2.0 * math.pi
            distance = abs(candidate - reference[index])
            if distance < best_distance:
                best = candidate
                best_distance = distance
        adjusted[index] = best
    return adjusted


class JointSequenceExecutor(Node):
    def __init__(self, sequence_file: Path, seconds_per_segment: float) -> None:
        super().__init__("joint_sequence_executor")
        self._sequence_file = sequence_file
        self._seconds_per_segment = seconds_per_segment
        self._latest_joint_state: JointState | None = None
        self._joint_state_sub = self.create_subscription(
            JointState, "/joint_state_broadcaster/joint_states", self._joint_state_cb, 10
        )
        self._action = ActionClient(
            self,
            FollowJointTrajectory,
            "/joint_trajectory_controller/follow_joint_trajectory",
        )

    def _joint_state_cb(self, msg: JointState) -> None:
        self._latest_joint_state = msg

    def wait_for_current_state(self) -> List[float]:
        end_time = self.get_clock().now().nanoseconds + int(5.0 * 1e9)
        while self._latest_joint_state is None and self.get_clock().now().nanoseconds < end_time:
            rclpy.spin_once(self, timeout_sec=0.1)
        if self._latest_joint_state is None:
            raise RuntimeError("Aucun joint state recu.")

        positions_by_name = dict(zip(self._latest_joint_state.name, self._latest_joint_state.position))
        missing = [name for name in JOINT_NAMES if name not in positions_by_name]
        if missing:
            raise RuntimeError(f"Joint states incomplets: {missing}")
        return [positions_by_name[name] for name in JOINT_NAMES]

    def build_trajectory(self) -> JointTrajectory:
        sequence = parse_sequence_file(self._sequence_file)
        current = self.wait_for_current_state()

        trajectory = JointTrajectory()
        trajectory.joint_names = list(JOINT_NAMES)

        elapsed = 0.0
        last_positions = current
        for item_type, item_value in sequence:
            if item_type == "pause":
                elapsed += float(item_value)
                point = JointTrajectoryPoint()
                point.positions = list(last_positions)
                point.time_from_start.sec = int(elapsed)
                point.time_from_start.nanosec = int((elapsed - int(elapsed)) * 1e9)
                trajectory.points.append(point)
                continue

            target = wrap_near_reference(list(item_value), last_positions)
            elapsed += self._seconds_per_segment
            point = JointTrajectoryPoint()
            point.positions = target
            point.time_from_start.sec = int(elapsed)
            point.time_from_start.nanosec = int((elapsed - int(elapsed)) * 1e9)
            trajectory.points.append(point)
            last_positions = target

        return trajectory

    def execute(self) -> None:
        if not self._action.wait_for_server(timeout_sec=5.0):
            raise RuntimeError("Action server du joint_trajectory_controller indisponible.")

        trajectory = self.build_trajectory()
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = trajectory

        self.get_logger().info(
            f"Execution directe de {len(trajectory.points)} points depuis {self._sequence_file}"
        )
        for index, point in enumerate(trajectory.points, start=1):
            timestamp = point.time_from_start.sec + point.time_from_start.nanosec / 1e9
            positions = " ".join(f"{value:.5f}" for value in point.positions)
            self.get_logger().info(f"Point {index} @ {timestamp:.2f}s: {positions}")

        send_future = self._action.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=10.0)
        goal_handle = send_future.result()
        if goal_handle is None or not goal_handle.accepted:
            raise RuntimeError("Goal trajectoire refuse.")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=300.0)
        result = result_future.result()
        if result is None:
            raise RuntimeError("Timeout pendant l'execution de la trajectoire.")
        if result.result.error_code != 0:
            raise RuntimeError(f"Echec d'execution, code={result.result.error_code}")


def main() -> None:
    rclpy.init()
    node = JointSequenceExecutor(
        sequence_file=Path(
            "/home/ai/pince-dev-test-py/robot_ws/src/earth_robot_moveit_config/config/waypoints_example_joints.txt"
        ),
        seconds_per_segment=8.0,
    )
    try:
        node.execute()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

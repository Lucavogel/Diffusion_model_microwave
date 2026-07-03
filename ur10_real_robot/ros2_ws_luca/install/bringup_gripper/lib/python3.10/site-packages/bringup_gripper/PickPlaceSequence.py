#!/usr/bin/env python3

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from control_msgs.action import GripperCommand
from geometry_msgs.msg import PoseStamped
from moveit.planning import MoveItPy
from moveit_configs_utils import MoveItConfigsBuilder
from rclpy.action import ActionClient
from rclpy.node import Node


@dataclass(frozen=True)
class PoseTarget:
    name: str
    frame_id: str
    position: tuple[float, float, float]
    orientation: tuple[float, float, float, float]


@dataclass(frozen=True)
class SequenceConfig:
    points: list[PoseTarget]
    gripper_open_position: float
    gripper_closed_position: float
    grasp_force_n: float
    release_force_n: float
    settle_time_sec: float
    open_before_start: bool


class PickPlaceSequence(Node):
    def __init__(self) -> None:
        super().__init__("pick_place_sequence")

        default_sequence_file = str(
            Path(get_package_share_directory("bringup_gripper"))
            / "config"
            / "pick_place_sequence_example.yaml"
        )
        default_moveit_cpp_file = str(
            Path("/home/ai/pince-dev-test-py/robot_ws/src")
            / "earth_robot_moveit_config"
            / "config"
            / "moveit_cpp.yaml"
        )

        self.declare_parameter("sequence_file", default_sequence_file)
        self.declare_parameter("execute", False)
        self.declare_parameter("robot_name", "ur10_d455_support_rg2ft")
        self.declare_parameter("moveit_config_package", "earth_robot_moveit_config")
        self.declare_parameter("moveit_cpp_file", default_moveit_cpp_file)
        self.declare_parameter("arm_group_name", "arm")
        self.declare_parameter("pose_link", "tool0")
        self.declare_parameter(
            "gripper_action_name", "/gripper_action_controller/gripper_cmd"
        )
        self.declare_parameter("server_timeout_sec", 10.0)

        self.sequence_file = Path(str(self.get_parameter("sequence_file").value))
        self.execute_requested = bool(self.get_parameter("execute").value)
        self.robot_name = str(self.get_parameter("robot_name").value)
        self.moveit_config_package = str(
            self.get_parameter("moveit_config_package").value
        )
        self.moveit_cpp_file = str(self.get_parameter("moveit_cpp_file").value)
        self.arm_group_name = str(self.get_parameter("arm_group_name").value)
        self.pose_link = str(self.get_parameter("pose_link").value)
        self.gripper_action_name = str(
            self.get_parameter("gripper_action_name").value
        )
        self.server_timeout_sec = float(
            self.get_parameter("server_timeout_sec").value
        )

        self.gripper_client = ActionClient(
            self, GripperCommand, self.gripper_action_name
        )
        self.moveit: MoveItPy | None = None
        self.arm = None

    def run(self) -> int:
        try:
            sequence = self._load_sequence(self.sequence_file)
            self._log_sequence(sequence)

            if not self.execute_requested:
                self.get_logger().warn(
                    "Execution desactivee. Relancer avec le parametre execute:=true "
                    "apres avoir remplace les 4 points d'exemple."
                )
                return 0

            self._setup_moveit()
            self._wait_for_gripper_server()
            self._execute_sequence(sequence)
            self.get_logger().info("Sequence pick-and-place terminee.")
            return 0
        except Exception as exc:  # pragma: no cover - runtime protection
            self.get_logger().error(f"Echec de la sequence: {exc}")
            return 1
        finally:
            if self.moveit is not None:
                self.moveit.shutdown()

    def _setup_moveit(self) -> None:
        moveit_config = (
            MoveItConfigsBuilder(
                robot_name=self.robot_name,
                package_name=self.moveit_config_package,
            )
            .to_moveit_configs()
            .to_dict()
        )
        moveit_config.update(self._load_moveit_cpp_config(Path(self.moveit_cpp_file)))

        self.moveit = MoveItPy(
            node_name="pick_place_moveit_py",
            config_dict=moveit_config,
        )
        self.arm = self.moveit.get_planning_component(self.arm_group_name)

        planning_scene_monitor = self.moveit.get_planning_scene_monitor()
        planning_scene_monitor.start_state_monitor()
        planning_scene_monitor.start_scene_monitor()
        planning_scene_monitor.wait_for_current_robot_state(
            self.server_timeout_sec
        )

    def _wait_for_gripper_server(self) -> None:
        if self.gripper_client.wait_for_server(timeout_sec=self.server_timeout_sec):
            return
        raise RuntimeError(
            "Le serveur d'action de pince n'est pas disponible sur "
            f"{self.gripper_action_name}"
        )

    def _execute_sequence(self, sequence: SequenceConfig) -> None:
        if sequence.open_before_start:
            self._command_gripper(
                position=sequence.gripper_open_position,
                max_effort=sequence.release_force_n,
                description="ouverture initiale",
            )

        for index, point in enumerate(sequence.points, start=1):
            self._move_arm_to_pose(point)

            if index == 2:
                self._command_gripper(
                    position=sequence.gripper_closed_position,
                    max_effort=sequence.grasp_force_n,
                    description="prise",
                )
            elif index == 4:
                self._command_gripper(
                    position=sequence.gripper_open_position,
                    max_effort=sequence.release_force_n,
                    description="depose",
                )

            if sequence.settle_time_sec > 0.0:
                time.sleep(sequence.settle_time_sec)

    def _move_arm_to_pose(self, target: PoseTarget) -> None:
        if self.moveit is None or self.arm is None:
            raise RuntimeError("MoveIt n'est pas initialise")

        pose_goal = PoseStamped()
        pose_goal.header.frame_id = target.frame_id
        pose_goal.header.stamp = self.get_clock().now().to_msg()
        pose_goal.pose.position.x = target.position[0]
        pose_goal.pose.position.y = target.position[1]
        pose_goal.pose.position.z = target.position[2]
        pose_goal.pose.orientation.x = target.orientation[0]
        pose_goal.pose.orientation.y = target.orientation[1]
        pose_goal.pose.orientation.z = target.orientation[2]
        pose_goal.pose.orientation.w = target.orientation[3]

        self.get_logger().info(
            f"Planification vers {target.name}: "
            f"x={target.position[0]:.4f} y={target.position[1]:.4f} z={target.position[2]:.4f}"
        )

        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(
            pose_stamped_msg=pose_goal,
            pose_link=self.pose_link,
        )
        plan_result = self.arm.plan()
        if not plan_result:
            raise RuntimeError(f"Planification impossible vers {target.name}")

        execution_ok = self.moveit.execute(plan_result.trajectory, controllers=[])
        if execution_ok is False:
            raise RuntimeError(f"Echec d'execution vers {target.name}")

        self.get_logger().info(f"Trajectoire executee vers {target.name}")

    def _command_gripper(
        self,
        position: float,
        max_effort: float,
        description: str,
    ) -> None:
        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = max_effort

        self.get_logger().info(
            f"Commande pince {description}: position={position:.4f} effort={max_effort:.1f}"
        )

        send_goal_future = self.gripper_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(
            self, send_goal_future, timeout_sec=self.server_timeout_sec
        )
        goal_handle = send_goal_future.result()
        if goal_handle is None or not goal_handle.accepted:
            raise RuntimeError(f"Commande pince refusee pendant {description}")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(
            self, result_future, timeout_sec=self.server_timeout_sec
        )
        wrapped_result = result_future.result()
        if wrapped_result is None:
            raise RuntimeError(
                f"Pas de resultat recu de la pince pendant {description}"
            )

        if wrapped_result.status != GoalStatus.STATUS_SUCCEEDED:
            raise RuntimeError(
                f"La pince n'a pas termine correctement pendant {description} "
                f"(status={wrapped_result.status})"
            )

    def _log_sequence(self, sequence: SequenceConfig) -> None:
        self.get_logger().info(
            f"Sequence chargee depuis {self.sequence_file} avec "
            f"{len(sequence.points)} points."
        )
        for point in sequence.points:
            self.get_logger().info(
                f"  {point.name}: frame={point.frame_id} "
                f"xyz=({point.position[0]:.4f}, {point.position[1]:.4f}, {point.position[2]:.4f})"
            )

    def _load_sequence(self, path: Path) -> SequenceConfig:
        if not path.is_file():
            raise FileNotFoundError(f"Fichier de sequence introuvable: {path}")

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        frame_id = str(data.get("frame_id", "base_link"))
        default_orientation = self._parse_orientation(data.get("default_orientation"))
        if default_orientation is None:
            default_orientation = (0.0, 0.0, 0.0, 1.0)

        points_section = data.get("points")
        if not isinstance(points_section, dict):
            raise ValueError("La section 'points' doit exister dans le YAML")

        point_names = ["point_1", "point_2", "point_3", "point_4"]
        points = [
            self._parse_point(
                name=name,
                payload=points_section.get(name),
                default_frame_id=frame_id,
                default_orientation=default_orientation,
            )
            for name in point_names
        ]

        gripper = data.get("gripper", {})
        if not isinstance(gripper, dict):
            raise ValueError("La section 'gripper' doit etre un dictionnaire")

        return SequenceConfig(
            points=points,
            gripper_open_position=float(gripper.get("open_position", 0.0)),
            gripper_closed_position=float(gripper.get("closed_position", 1.18)),
            grasp_force_n=float(gripper.get("grasp_force_n", 10.0)),
            release_force_n=float(gripper.get("release_force_n", 5.0)),
            settle_time_sec=float(data.get("settle_time_sec", 0.5)),
            open_before_start=bool(data.get("open_before_start", True)),
        )

    def _load_moveit_cpp_config(self, path: Path) -> dict[str, Any]:
        if path.is_file():
            with path.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}

        self.get_logger().warn(
            f"Fichier moveit_cpp introuvable: {path}. Utilisation de la configuration integree."
        )
        return {
            "planning_scene_monitor_options": {
                "name": "planning_scene_monitor",
                "robot_description": "robot_description",
                "joint_state_topic": "/joint_states",
                "attached_collision_object_topic": "/moveit_cpp/planning_scene_monitor",
                "publish_planning_scene_topic": "/moveit_cpp/publish_planning_scene",
                "monitored_planning_scene_topic": "/moveit_cpp/monitored_planning_scene",
                "wait_for_initial_state_timeout": 10.0,
            },
            "planning_pipelines": {
                "pipeline_names": ["ompl"],
            },
            "plan_request_params": {
                "planning_attempts": 3,
                "planning_pipeline": "ompl",
                "max_velocity_scaling_factor": 0.2,
                "max_acceleration_scaling_factor": 0.2,
            },
        }

    def _parse_point(
        self,
        name: str,
        payload: Any,
        default_frame_id: str,
        default_orientation: tuple[float, float, float, float],
    ) -> PoseTarget:
        if not isinstance(payload, dict):
            raise ValueError(f"Le point '{name}' doit etre un dictionnaire")

        position = self._parse_position(payload)
        orientation = self._parse_orientation(payload.get("orientation"))
        if orientation is None:
            orientation = self._parse_orientation_from_rpy(payload)
        if orientation is None:
            orientation = default_orientation

        return PoseTarget(
            name=name,
            frame_id=str(payload.get("frame_id", default_frame_id)),
            position=position,
            orientation=orientation,
        )

    def _parse_position(self, payload: dict[str, Any]) -> tuple[float, float, float]:
        if "position" in payload:
            position = payload["position"]
            if not isinstance(position, dict):
                raise ValueError("Le champ 'position' doit etre un dictionnaire")
            x = position.get("x")
            y = position.get("y")
            z = position.get("z")
        else:
            x = payload.get("x")
            y = payload.get("y")
            z = payload.get("z")

        if x is None or y is None or z is None:
            raise ValueError("Chaque point doit definir x, y, z")

        return (float(x), float(y), float(z))

    def _parse_orientation(
        self, payload: Any
    ) -> tuple[float, float, float, float] | None:
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise ValueError("L'orientation doit etre un dictionnaire")

        required = ("x", "y", "z", "w")
        if not all(key in payload for key in required):
            return None

        quaternion = (
            float(payload["x"]),
            float(payload["y"]),
            float(payload["z"]),
            float(payload["w"]),
        )
        return self._normalize_quaternion(quaternion)

    def _parse_orientation_from_rpy(
        self, payload: dict[str, Any]
    ) -> tuple[float, float, float, float] | None:
        if not all(axis in payload for axis in ("roll", "pitch", "yaw")):
            return None

        roll = float(payload["roll"])
        pitch = float(payload["pitch"])
        yaw = float(payload["yaw"])
        return self._normalize_quaternion(self._rpy_to_quaternion(roll, pitch, yaw))

    def _normalize_quaternion(
        self, quaternion: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        norm = math.sqrt(sum(component * component for component in quaternion))
        if norm <= 1e-9:
            raise ValueError("Quaternion invalide: norme nulle")
        return tuple(component / norm for component in quaternion)

    def _rpy_to_quaternion(
        self, roll: float, pitch: float, yaw: float
    ) -> tuple[float, float, float, float]:
        half_roll = roll * 0.5
        half_pitch = pitch * 0.5
        half_yaw = yaw * 0.5

        cr = math.cos(half_roll)
        sr = math.sin(half_roll)
        cp = math.cos(half_pitch)
        sp = math.sin(half_pitch)
        cy = math.cos(half_yaw)
        sy = math.sin(half_yaw)

        return (
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy,
        )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = PickPlaceSequence()
    exit_code = 1
    try:
        exit_code = node.run()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()

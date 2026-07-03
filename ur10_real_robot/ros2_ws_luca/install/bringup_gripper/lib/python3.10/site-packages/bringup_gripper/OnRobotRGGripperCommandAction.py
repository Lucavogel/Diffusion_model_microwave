#!/usr/bin/env python3

import math
import threading
import time

import rclpy
from control_msgs.action import GripperCommand
from onrobot_rg_msgs.msg import OnRobotRGInput
from onrobot_rg_msgs.msg import OnRobotRGOutput
from rclpy.action import ActionServer
from rclpy.action import CancelResponse
from rclpy.action import GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node


class OnRobotRGGripperCommandAction(Node):
    def __init__(self):
        super().__init__("OnRobotRGGripperCommandAction")

        self.declare_parameter("action_name", "gripper_command")
        self.declare_parameter("command_topic", "OnRobotRGOutput")
        self.declare_parameter("status_topic", "OnRobotRGInput")
        self.declare_parameter("gripper", "rg2ft")
        self.declare_parameter("use_joint_position_commands", True)
        self.declare_parameter("joint_open_position", 0.0)
        self.declare_parameter("joint_closed_position", 1.18)
        self.declare_parameter("default_force_n", 10.0)
        self.declare_parameter("max_force_n", 20.0)
        self.declare_parameter("repeat", 5)
        self.declare_parameter("rate_hz", 5.0)
        self.declare_parameter("stop_first", True)
        self.declare_parameter("status_timeout_sec", 2.0)
        self.declare_parameter("motion_start_timeout_sec", 1.0)
        self.declare_parameter("motion_timeout_sec", 10.0)
        self.declare_parameter("stop_timeout_sec", 1.0)
        self.declare_parameter("goal_tolerance_mm", 1.0)

        self.action_name = str(self.get_parameter("action_name").value)
        self.command_topic = str(self.get_parameter("command_topic").value)
        self.status_topic = str(self.get_parameter("status_topic").value)
        self.gtype = str(self.get_parameter("gripper").value)
        self.use_joint_position_commands = bool(
            self.get_parameter("use_joint_position_commands").value
        )
        self.joint_open_position = float(
            self.get_parameter("joint_open_position").value
        )
        self.joint_closed_position = float(
            self.get_parameter("joint_closed_position").value
        )
        self.default_force_n = float(self.get_parameter("default_force_n").value)
        self.max_force_n = float(self.get_parameter("max_force_n").value)
        self.repeat = int(self.get_parameter("repeat").value)
        self.rate_hz = float(self.get_parameter("rate_hz").value)
        self.stop_first = bool(self.get_parameter("stop_first").value)
        self.status_timeout_sec = float(
            self.get_parameter("status_timeout_sec").value
        )
        self.motion_start_timeout_sec = float(
            self.get_parameter("motion_start_timeout_sec").value
        )
        self.motion_timeout_sec = float(
            self.get_parameter("motion_timeout_sec").value
        )
        self.stop_timeout_sec = float(self.get_parameter("stop_timeout_sec").value)
        self.goal_tolerance_mm = float(self.get_parameter("goal_tolerance_mm").value)

        self.max_width_mm = 100.0 if self.gtype == "rg2ft" else 160.0
        self.hardware_max_force_n = 40.0 if self.gtype == "rg2ft" else 120.0
        self.max_force_n = max(0.0, min(self.max_force_n, self.hardware_max_force_n))

        self._status_lock = threading.Lock()
        self._status_condition = threading.Condition(self._status_lock)
        self._latest_status = None
        self._status_seq = 0

        self._goal_lock = threading.Lock()
        self._goal_in_progress = False

        self.callback_group = ReentrantCallbackGroup()
        self.command_pub = self.create_publisher(
            OnRobotRGOutput,
            self.command_topic,
            10,
        )
        self.status_sub = self.create_subscription(
            OnRobotRGInput,
            self.status_topic,
            self.status_callback,
            10,
            callback_group=self.callback_group,
        )
        self.action_server = ActionServer(
            self,
            GripperCommand,
            self.action_name,
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.callback_group,
        )

        self.get_logger().info(
            f"Serving control_msgs/GripperCommand on /{self.action_name.lstrip('/')}"
        )

    def status_callback(self, status: OnRobotRGInput):
        with self._status_condition:
            self._latest_status = status
            self._status_seq += 1
            self._status_condition.notify_all()

    def goal_callback(self, goal_request: GripperCommand.Goal):
        validation_error = self._validate_goal(goal_request)
        if validation_error is not None:
            self.get_logger().warn(f"Rejecting gripper goal: {validation_error}")
            return GoalResponse.REJECT

        with self._goal_lock:
            if self._goal_in_progress:
                self.get_logger().warn("Rejecting gripper goal while another goal is active")
                return GoalResponse.REJECT
            self._goal_in_progress = True

        target_width_mm = self._command_position_to_width_mm(
            goal_request.command.position
        )
        target_joint_position = self._command_position_to_joint_position(
            goal_request.command.position
        )
        force_n = self._resolve_force_n(goal_request.command.max_effort)
        self.get_logger().info(
            f"Accepted gripper goal: joint={target_joint_position:.4f} "
            f"width={target_width_mm:.1f} mm force={force_n:.1f} N"
        )
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Received cancel request for gripper goal")
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        requested_width_mm = self._command_position_to_width_mm(
            goal_handle.request.command.position
        )
        requested_force_n = self._resolve_force_n(
            goal_handle.request.command.max_effort
        )

        try:
            status_seq, status = self._wait_for_status_update(
                self._status_seq,
                self.status_timeout_sec,
                require_new=False,
            )
            if status is None:
                self.get_logger().error("No gripper status received before executing goal")
                goal_handle.abort()
                return self._build_result(
                    None,
                    requested_force_n,
                    stalled=False,
                    reached_goal=False,
                )

            if self._is_goal_reached(status, requested_width_mm):
                goal_handle.succeed()
                return self._build_result(
                    status,
                    requested_force_n,
                    stalled=False,
                    reached_goal=True,
                )

            if self.stop_first and bool(status.busy):
                self._publish_burst(
                    self._status_width_mm(status),
                    requested_force_n,
                    control=0,
                )
                status_seq, status = self._wait_until_not_busy(
                    status_seq,
                    self.stop_timeout_sec,
                )

            self._publish_burst(
                requested_width_mm,
                requested_force_n,
                control=1,
            )

            command_start = time.monotonic()
            start_deadline = command_start + self.motion_start_timeout_sec
            motion_deadline = command_start + self.motion_timeout_sec
            motion_started = bool(status is not None and status.busy)

            while rclpy.ok():
                if goal_handle.is_cancel_requested:
                    self._publish_burst(
                        requested_width_mm,
                        requested_force_n,
                        control=0,
                    )
                    status = self._latest_status_or(status)
                    goal_handle.canceled()
                    return self._build_result(
                        status,
                        requested_force_n,
                        stalled=False,
                        reached_goal=False,
                    )

                status_seq, maybe_status = self._wait_for_status_update(
                    status_seq,
                    timeout_sec=min(0.2, max(0.0, motion_deadline - time.monotonic())),
                )
                status = self._latest_status_or(maybe_status or status)
                if status is None:
                    continue

                if bool(status.busy):
                    motion_started = True

                reached_goal = self._is_goal_reached(status, requested_width_mm)
                stalled = self._is_stalled(
                    status,
                    requested_width_mm,
                    motion_started,
                    time.monotonic(),
                    start_deadline,
                )
                feedback = self._build_feedback(
                    status,
                    requested_force_n,
                    stalled=stalled,
                    reached_goal=reached_goal,
                )
                goal_handle.publish_feedback(feedback)

                if reached_goal and not bool(status.busy):
                    goal_handle.succeed()
                    return self._build_result(
                        status,
                        requested_force_n,
                        stalled=False,
                        reached_goal=True,
                    )

                if stalled:
                    goal_handle.succeed()
                    return self._build_result(
                        status,
                        requested_force_n,
                        stalled=True,
                        reached_goal=False,
                    )

                if time.monotonic() >= motion_deadline:
                    self.get_logger().error(
                        "Timed out while waiting for gripper motion to finish"
                    )
                    self._publish_burst(
                        requested_width_mm,
                        requested_force_n,
                        control=0,
                    )
                    goal_handle.abort()
                    return self._build_result(
                        status,
                        requested_force_n,
                        stalled=False,
                        reached_goal=False,
                    )

            goal_handle.abort()
            return self._build_result(
            self._latest_status_or(status),
            requested_force_n,
            stalled=False,
            reached_goal=False,
        )
        finally:
            with self._goal_lock:
                self._goal_in_progress = False

    def _publish_burst(self, width_mm: float, force_n: float, control: int):
        command = OnRobotRGOutput()
        command.r_gfr = int(round(self._clamp_force_n(force_n) * 10.0))
        command.r_gwd = int(round(self._clamp_width_mm(width_mm) * 10.0))
        command.r_ctr = int(control)
        command.out_zero = 0
        command.out_prox_off_r = 0
        command.out_prox_off_l = 0

        period = 1.0 / self.rate_hz if self.rate_hz > 0.0 else 0.2
        for _ in range(max(1, self.repeat)):
            self.command_pub.publish(command)
            time.sleep(period)

    def _wait_for_status_update(
        self,
        after_seq: int,
        timeout_sec: float,
        require_new: bool = True,
    ):
        with self._status_condition:
            if self._latest_status is None:
                self._status_condition.wait(timeout=timeout_sec)
            elif require_new and self._status_seq <= after_seq:
                self._status_condition.wait(timeout=timeout_sec)
            return self._status_seq, self._latest_status

    def _wait_until_not_busy(self, after_seq: int, timeout_sec: float):
        deadline = time.monotonic() + timeout_sec
        status = self._latest_status
        status_seq = after_seq
        while time.monotonic() < deadline:
            remaining = max(0.0, deadline - time.monotonic())
            status_seq, maybe_status = self._wait_for_status_update(
                status_seq,
                min(0.2, remaining),
            )
            if maybe_status is not None:
                status = maybe_status
            if status is not None and not bool(status.busy):
                break
        return status_seq, status

    def _latest_status_or(self, fallback):
        with self._status_lock:
            return self._latest_status if self._latest_status is not None else fallback

    def _validate_goal(self, goal_request: GripperCommand.Goal):
        command_position = float(goal_request.command.position)
        if not math.isfinite(command_position):
            return "command.position must be finite"

        if self.use_joint_position_commands:
            lower = min(self.joint_open_position, self.joint_closed_position)
            upper = max(self.joint_open_position, self.joint_closed_position)
            if command_position < lower or command_position > upper:
                return (
                    "command.position is outside the gripper joint range "
                    f"[{lower:.4f}, {upper:.4f}]"
                )
        else:
            width_m = command_position
            if width_m < 0.0 or width_m > (self.max_width_mm / 1000.0):
                return (
                    "command.position is outside the physical width range "
                    f"[0.0, {self.max_width_mm / 1000.0:.4f}] m"
                )

        max_effort_n = float(goal_request.command.max_effort)
        if not math.isfinite(max_effort_n):
            return "command.max_effort must be finite"
        if max_effort_n < 0.0:
            return "command.max_effort must be >= 0.0"
        return None

    def _resolve_force_n(self, max_effort_n: float) -> float:
        if max_effort_n > 0.0:
            if max_effort_n > self.max_force_n:
                self.get_logger().warn(
                    f"Clamping requested force {max_effort_n:.1f} N "
                    f"to safe limit {self.max_force_n:.1f} N"
                )
            return self._clamp_force_n(max_effort_n)
        return self._clamp_force_n(self.default_force_n)

    def _status_width_mm(self, status: OnRobotRGInput) -> float:
        return self._clamp_width_mm(status.grip_width / 10.0)

    def _status_command_position(self, status: OnRobotRGInput) -> float:
        if not self.use_joint_position_commands:
            return self._status_width_mm(status) / 1000.0
        return self._width_mm_to_joint_position(self._status_width_mm(status))

    def _command_position_to_width_mm(self, command_position: float) -> float:
        if not self.use_joint_position_commands:
            return self._clamp_width_mm(command_position * 1000.0)
        return self._joint_position_to_width_mm(command_position)

    def _command_position_to_joint_position(self, command_position: float) -> float:
        if self.use_joint_position_commands:
            return command_position
        return self._width_mm_to_joint_position(command_position * 1000.0)

    def _joint_position_to_width_mm(self, joint_position: float) -> float:
        delta = self.joint_open_position - self.joint_closed_position
        if abs(delta) < 1e-9:
            return 0.0
        open_ratio = (joint_position - self.joint_closed_position) / delta
        return self._clamp_width_mm(open_ratio * self.max_width_mm)

    def _width_mm_to_joint_position(self, width_mm: float) -> float:
        if self.max_width_mm <= 0.0:
            return self.joint_open_position
        open_ratio = self._clamp_width_mm(width_mm) / self.max_width_mm
        return self.joint_closed_position + open_ratio * (
            self.joint_open_position - self.joint_closed_position
        )

    def _is_goal_reached(self, status: OnRobotRGInput, target_width_mm: float) -> bool:
        return abs(self._status_width_mm(status) - target_width_mm) <= self.goal_tolerance_mm

    def _is_stalled(
        self,
        status: OnRobotRGInput,
        target_width_mm: float,
        motion_started: bool,
        now_monotonic: float,
        start_deadline: float,
    ) -> bool:
        if self._is_goal_reached(status, target_width_mm):
            return False
        if bool(status.busy):
            return False
        if motion_started:
            return True
        if now_monotonic >= start_deadline:
            return True
        return False

    def _build_feedback(
        self,
        status: OnRobotRGInput,
        force_n: float,
        stalled: bool,
        reached_goal: bool,
    ) -> GripperCommand.Feedback:
        feedback = GripperCommand.Feedback()
        feedback.position = self._status_command_position(status)
        feedback.effort = force_n
        feedback.stalled = stalled
        feedback.reached_goal = reached_goal
        return feedback

    def _build_result(
        self,
        status: OnRobotRGInput | None,
        force_n: float,
        stalled: bool,
        reached_goal: bool,
    ) -> GripperCommand.Result:
        result = GripperCommand.Result()
        result.position = (
            0.0 if status is None else self._status_command_position(status)
        )
        result.effort = force_n
        result.stalled = stalled
        result.reached_goal = reached_goal
        return result

    def _clamp_width_mm(self, width_mm: float) -> float:
        return max(0.0, min(self.max_width_mm, width_mm))

    def _clamp_force_n(self, force_n: float) -> float:
        return max(0.0, min(self.max_force_n, force_n))

    def destroy_node(self):
        self.action_server.destroy()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = OnRobotRGGripperCommandAction()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

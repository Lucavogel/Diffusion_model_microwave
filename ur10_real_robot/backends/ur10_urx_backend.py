from __future__ import annotations

import time
from typing import Optional

import numpy as np
import urx

from ur10_real_robot.interfaces import RobotInterface


def rotvec_to_quat_wxyz(rotvec: np.ndarray) -> np.ndarray:
    rotvec = np.asarray(rotvec, dtype=np.float64)
    angle = float(np.linalg.norm(rotvec))

    if angle < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

    axis = rotvec / angle
    half_angle = angle / 2.0

    w = np.cos(half_angle)
    xyz = axis * np.sin(half_angle)

    return np.array([w, xyz[0], xyz[1], xyz[2]], dtype=np.float64)


class UR10UrxBackend(RobotInterface):
    def __init__(
        self,
        robot_ip: str,
        control_dt: float = 0.1,
        max_delta_deg: float = 2.0,
        enable_motion: bool = False,
    ):
        self.robot_ip = robot_ip
        self.control_dt = float(control_dt)
        self.max_delta = np.radians(float(max_delta_deg))
        self.enable_motion = bool(enable_motion)

        self.robot = None
        self.last_q_command: Optional[np.ndarray] = None

        self._last_q_for_vel: Optional[np.ndarray] = None
        self._last_time_for_vel: Optional[float] = None
        self._last_qvel = np.zeros(6, dtype=np.float64)

        self.gripper_state = -0.2

    def connect(self) -> None:
        print(f"[URX] Connecting to UR10 at {self.robot_ip}")
        self.robot = urx.Robot(self.robot_ip)

        q = self.get_joint_positions()
        self.last_q_command = q.copy()

        self._last_q_for_vel = q.copy()
        self._last_time_for_vel = time.time()

        print("[URX] Connected")
        print("[URX] Current joints rad:", q)
        print("[URX] Current joints deg:", np.degrees(q))

        if not self.enable_motion:
            print("[URX] Motion disabled: commands will not be sent.")

    def close(self) -> None:
        if self.robot is not None:
            try:
                self.stop()
            except Exception:
                pass

            self.robot.close()
            self.robot = None
            print("[URX] Connection closed.")

    def stop(self) -> None:
        if self.robot is None:
            return

        try:
            self.robot.stopj(acc=0.5)
            print("[URX] stopj sent.")
        except Exception as exc:
            print(f"[URX] Failed to stop robot: {exc}")

    def get_joint_positions(self) -> np.ndarray:
        if self.robot is None:
            raise RuntimeError("Robot is not connected.")

        return np.asarray(self.robot.getj(), dtype=np.float64)

    def get_joint_velocities(self) -> np.ndarray:
        q_now = self.get_joint_positions()
        t_now = time.time()

        if self._last_q_for_vel is None or self._last_time_for_vel is None:
            self._last_q_for_vel = q_now.copy()
            self._last_time_for_vel = t_now
            return self._last_qvel.copy()

        dt = t_now - self._last_time_for_vel

        if dt <= 1e-6:
            return self._last_qvel.copy()

        qvel = (q_now - self._last_q_for_vel) / dt

        self._last_qvel = qvel.copy()
        self._last_q_for_vel = q_now.copy()
        self._last_time_for_vel = t_now

        return qvel.astype(np.float64)

    def get_eef_pos(self) -> np.ndarray:
        if self.robot is None:
            raise RuntimeError("Robot is not connected.")

        pose = self.robot.getl()
        return np.asarray(pose[:3], dtype=np.float64)

    def get_eef_quat(self) -> np.ndarray:
        if self.robot is None:
            raise RuntimeError("Robot is not connected.")

        pose = self.robot.getl()
        rotvec = np.asarray(pose[3:6], dtype=np.float64)

        return rotvec_to_quat_wxyz(rotvec)

    def get_gripper_qpos(self) -> np.ndarray:
        return np.array([self.gripper_state], dtype=np.float64)

    def apply_joint_command(
        self,
        q_target: np.ndarray,
        gripper_command: Optional[float] = None,
    ) -> None:
        if self.robot is None:
            raise RuntimeError("Robot is not connected.")

        q_current = self.get_joint_positions()
        q_target = np.asarray(q_target, dtype=np.float64)

        if q_target.shape != (6,):
            raise ValueError(f"q_target must have shape (6,), got {q_target.shape}")

        q_safe = q_current + np.clip(
            q_target - q_current,
            -self.max_delta,
            self.max_delta,
        )

        self.last_q_command = q_safe.copy()

        if gripper_command is not None:
            self.gripper_state = float(gripper_command)

        if not self.enable_motion:
            print("[URX] Motion disabled. Command not sent.")
            print("[URX] q_safe deg:", np.degrees(q_safe))
            return

        self.robot.servoj(
            q_safe.tolist(),
            t=self.control_dt,
            lookahead_time=0.2,
            gain=100,
            wait=False,
        )

    def get_state(self) -> dict[str, np.ndarray]:
        return {
            "joint_positions": self.get_joint_positions(),
            "joint_velocities": self.get_joint_velocities(),
            "eef_pos": self.get_eef_pos(),
            "eef_quat": self.get_eef_quat(),
            "gripper_qpos": self.get_gripper_qpos(),
        }
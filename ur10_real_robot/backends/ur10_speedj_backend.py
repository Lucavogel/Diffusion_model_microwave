from __future__ import annotations

import time
from typing import Optional

import numpy as np

from ur10_real_robot.backends.ur10_rtde import UR10RealtimeSession
from ur10_real_robot.backends.fake_robot_backend import rot_to_quat_wxyz
from ur10_real_robot.interfaces import RobotInterface


class UR10SpeedjBackend(RobotInterface):
    """
    Real UR10 CB backend using realtime read + URScript speedj commands.

    This is the path validated on the CB2 robot:
    - read qActual from URRTMonitor / port 30003
    - send speedj(qd, a, t) to port 30002

    Position commands are intentionally converted to velocity commands, but
    teleop should prefer apply_joint_velocity() with the dq computed by the
    Cartesian controller.
    """

    def __init__(
        self,
        robot_ip: str,
        control_dt: float = 0.02,
        speedj_a: float = 0.06,
        speedj_t: Optional[float] = None,
        stop_deceleration: float = 1.0,
        max_joint_vel: float = 0.18,
        socket_timeout: float = 1.0,
        enable_motion: bool = False,
        kinematics=None,
    ) -> None:
        self.robot_ip = str(robot_ip)
        self.control_dt = float(control_dt)
        self.speedj_a = float(speedj_a)
        self.speedj_t = float(speedj_t) if speedj_t is not None else self.control_dt
        self.stop_deceleration = float(stop_deceleration)
        self.max_joint_vel = float(max_joint_vel)
        self.socket_timeout = float(socket_timeout)
        self.enable_motion = bool(enable_motion)
        self.kinematics = kinematics

        self.session: UR10RealtimeSession | None = None
        self.gripper_state = -0.2

        self._last_data: dict | None = None
        self._last_read_time: float | None = None
        self._last_q: np.ndarray | None = None
        self._last_qvel = np.zeros(6, dtype=np.float64)
        self._last_q_command: np.ndarray | None = None
        self._last_qd_command = np.zeros(6, dtype=np.float64)

    def connect(self) -> None:
        print(f"[UR10 SPEEDJ] Connecting to {self.robot_ip}...")
        self.session = UR10RealtimeSession(
            robot_ip=self.robot_ip,
            socket_timeout=self.socket_timeout,
        ).connect()

        q = self.get_joint_positions()
        self._last_q = q.copy()
        self._last_q_command = q.copy()
        self._last_read_time = time.monotonic()

        print("[UR10 SPEEDJ] Connected.")
        print("[UR10 SPEEDJ] Motion enabled:", self.enable_motion)
        print("[UR10 SPEEDJ] q rad:", np.round(q, 6))
        print("[UR10 SPEEDJ] q deg:", np.round(np.degrees(q), 3))
        print("[UR10 SPEEDJ] max_joint_vel:", self.max_joint_vel)
        print("[UR10 SPEEDJ] speedj a/t:", self.speedj_a, self.speedj_t)

    def close(self) -> None:
        if self.session is None:
            return

        try:
            self.stop()
        except Exception:
            pass

        self.session.close()
        self.session = None
        print("[UR10 SPEEDJ] Connection closed.")

    def stop(self) -> None:
        self._last_qd_command[:] = 0.0

        if self.session is None:
            return

        if not self.enable_motion:
            return

        try:
            self.session.stopj(self.stop_deceleration)
        except Exception as exc:
            print(f"[UR10 SPEEDJ] stopj failed: {exc}")

    def _refresh(self, wait: bool = True) -> dict:
        if self.session is None:
            raise RuntimeError("UR10SpeedjBackend is not connected.")

        data = self.session.read(wait=wait)
        now = time.monotonic()

        q = np.asarray(data["qActual"], dtype=np.float64).reshape(6)

        if "qdActual" in data:
            qvel = np.asarray(data["qdActual"], dtype=np.float64).reshape(6)
        elif self._last_q is not None and self._last_read_time is not None:
            dt = now - self._last_read_time
            if dt > 1e-6:
                qvel = (q - self._last_q) / dt
            else:
                qvel = self._last_qvel.copy()
        else:
            qvel = np.zeros(6, dtype=np.float64)

        self._last_data = data
        self._last_q = q.copy()
        self._last_qvel = qvel.copy()
        self._last_read_time = now
        return data

    def get_joint_positions(self) -> np.ndarray:
        self._refresh(wait=True)
        if self._last_q is None:
            raise RuntimeError("No robot joint state available.")
        return self._last_q.copy()

    def get_joint_velocities(self) -> np.ndarray:
        if self._last_q is None:
            self._refresh(wait=True)
        return self._last_qvel.copy()

    def get_eef_pos(self) -> np.ndarray:
        if self.kinematics is None:
            return np.zeros(3, dtype=np.float64)

        q = self._last_q if self._last_q is not None else self.get_joint_positions()
        pos, _ = self.kinematics.forward(q)
        return pos.copy()

    def get_eef_quat(self) -> np.ndarray:
        if self.kinematics is None:
            return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

        q = self._last_q if self._last_q is not None else self.get_joint_positions()
        _, rot = self.kinematics.forward(q)
        return rot_to_quat_wxyz(rot)

    def get_gripper_qpos(self) -> np.ndarray:
        return np.array([self.gripper_state], dtype=np.float64)

    def apply_joint_velocity(
        self,
        qd_target: np.ndarray,
        gripper_command: Optional[float] = None,
    ) -> None:
        if self.session is None:
            raise RuntimeError("UR10SpeedjBackend is not connected.")

        qd = np.asarray(qd_target, dtype=np.float64).reshape(6)
        qd_safe = np.clip(qd, -self.max_joint_vel, self.max_joint_vel)
        self._last_qd_command = qd_safe.copy()

        if gripper_command is not None:
            self.gripper_state = float(gripper_command)

        if not self.enable_motion:
            return

        self.session.send_speedj(qd_safe, a=self.speedj_a, t=self.speedj_t)

    def apply_joint_command(
        self,
        q_target: np.ndarray,
        gripper_command: Optional[float] = None,
    ) -> None:
        q_current = self._last_q if self._last_q is not None else self.get_joint_positions()
        q_target = np.asarray(q_target, dtype=np.float64).reshape(6)
        qd = (q_target - q_current) / max(self.control_dt, 1e-6)
        self._last_q_command = q_target.copy()
        self.apply_joint_velocity(qd, gripper_command=gripper_command)

    def get_last_velocity_command(self) -> np.ndarray:
        return self._last_qd_command.copy()

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from ur10_real_robot.interfaces import RobotInterface


def rot_to_quat_wxyz(R: np.ndarray) -> np.ndarray:
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)

    trace = np.trace(R)

    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s

    q = np.array([w, x, y, z], dtype=np.float64)
    q /= np.linalg.norm(q)
    return q


class FakeRobotBackend(RobotInterface):
    """
    Backend fake pour tester la téléop réelle sans robot.

    Il simule seulement :
    - q_current
    - qvel
    - q_target reçu
    - gripper_command

    Il ne commande aucun robot.
    """

    def __init__(
        self,
        initial_q: Optional[np.ndarray] = None,
        control_dt: float = 0.02,
        max_delta_deg: float = 2.0,
        kinematics=None,
    ) -> None:
        if initial_q is None:
            initial_q = np.array(
                [0.0, -1.3, 1.8, -0.22, 1.57, 0.0],
                dtype=np.float64,
            )

        self.q = np.asarray(initial_q, dtype=np.float64).reshape(6).copy()
        self.qvel = np.zeros(6, dtype=np.float64)

        self.control_dt = float(control_dt)
        self.max_delta = np.radians(float(max_delta_deg))

        self.connected = False
        self.last_time = time.time()

        self.last_q_command = self.q.copy()
        self.gripper_state = -0.2

        # Optionnel : si on donne servo.kin, on peut retourner eef_pos/eef_quat propres.
        self.kinematics = kinematics

    def connect(self) -> None:
        self.connected = True
        self.last_time = time.time()

        print("[FAKE ROBOT] Connected.")
        print("[FAKE ROBOT] initial q rad:", self.q)
        print("[FAKE ROBOT] initial q deg:", np.degrees(self.q))

    def close(self) -> None:
        self.connected = False
        print("[FAKE ROBOT] Closed.")

    def stop(self) -> None:
        self.qvel[:] = 0.0
        print("[FAKE ROBOT] stop() called.")

    def get_joint_positions(self) -> np.ndarray:
        if not self.connected:
            raise RuntimeError("FakeRobotBackend is not connected.")

        return self.q.copy()

    def get_joint_velocities(self) -> np.ndarray:
        if not self.connected:
            raise RuntimeError("FakeRobotBackend is not connected.")

        return self.qvel.copy()

    def get_eef_pos(self) -> np.ndarray:
        if self.kinematics is None:
            return np.zeros(3, dtype=np.float64)

        pos, _ = self.kinematics.forward(self.q)
        return pos.copy()

    def get_eef_quat(self) -> np.ndarray:
        if self.kinematics is None:
            return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

        _, rot = self.kinematics.forward(self.q)
        return rot_to_quat_wxyz(rot)

    def get_gripper_qpos(self) -> np.ndarray:
        return np.array([self.gripper_state], dtype=np.float64)

    def apply_joint_command(
        self,
        q_target: np.ndarray,
        gripper_command: Optional[float] = None,
    ) -> None:
        if not self.connected:
            raise RuntimeError("FakeRobotBackend is not connected.")

        q_target = np.asarray(q_target, dtype=np.float64).reshape(6)

        now = time.time()
        dt = now - self.last_time

        if dt <= 1e-6 or dt > 0.5:
            dt = self.control_dt

        self.last_time = now

        q_before = self.q.copy()

        # Même logique safe qu'un backend réel :
        # on ne saute pas directement à q_target si l'écart est trop grand.
        delta = q_target - self.q
        delta_safe = np.clip(delta, -self.max_delta, self.max_delta)

        self.q = self.q + delta_safe
        self.qvel = (self.q - q_before) / dt

        self.last_q_command = self.q.copy()

        if gripper_command is not None:
            self.gripper_state = float(gripper_command)

        print("[FAKE ROBOT] command received")
        print("  q_current deg :", np.round(np.degrees(q_before), 3))
        print("  q_target  deg :", np.round(np.degrees(q_target), 3))
        print("  q_safe    deg :", np.round(np.degrees(self.q), 3))
        print("  delta deg     :", np.round(np.degrees(delta_safe), 3))
        print("  qvel rad/s    :", np.round(self.qvel, 4))
        print("  gripper       :", self.gripper_state)
        print("-" * 60)

    def get_state(self) -> dict:
        return {
            "joint_positions": self.get_joint_positions(),
            "joint_velocities": self.get_joint_velocities(),
            "eef_pos": self.get_eef_pos(),
            "eef_quat": self.get_eef_quat(),
            "gripper_qpos": self.get_gripper_qpos(),
        }
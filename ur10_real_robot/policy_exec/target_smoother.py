from __future__ import annotations

import numpy as np

from dp_mujoco.common.pose_utils import quat_slerp, quat_to_rot, rot_to_quat


def rot_to_quat_wxyz(R: np.ndarray) -> np.ndarray:
    q_xyzw = rot_to_quat(R)
    q_wxyz = np.array(
        [q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]],
        dtype=np.float64,
    )
    q_wxyz /= np.linalg.norm(q_wxyz) + 1e-12
    return q_wxyz


def quat_wxyz_to_rot(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64).copy()
    q /= np.linalg.norm(q) + 1e-12
    return quat_to_rot(float(q[1]), float(q[2]), float(q[3]), float(q[0]))


class PolicyTargetSmoother:
    def __init__(
        self,
        max_target_speed: float = 0.08,
        alpha_pos: float = 0.30,
        alpha_rot: float = 0.20,
        alpha_gripper: float = 0.35,
    ) -> None:
        self.max_target_speed = float(max_target_speed)
        self.alpha_pos = float(alpha_pos)
        self.alpha_rot = float(alpha_rot)
        self.alpha_gripper = float(alpha_gripper)

        self.target_pos: np.ndarray | None = None
        self.target_quat: np.ndarray | None = None
        self.gripper_cmd: float | None = None

    def reset(self, pos: np.ndarray, quat_wxyz: np.ndarray, gripper: float) -> None:
        self.target_pos = np.asarray(pos, dtype=np.float64).reshape(3).copy()
        self.target_quat = np.asarray(quat_wxyz, dtype=np.float64).reshape(4).copy()
        self.target_quat /= np.linalg.norm(self.target_quat) + 1e-12
        self.gripper_cmd = float(gripper)

    def update(
        self,
        raw_pos: np.ndarray,
        raw_rot: np.ndarray,
        raw_gripper: float,
        dt: float,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        raw_pos = np.asarray(raw_pos, dtype=np.float64).reshape(3).copy()
        raw_quat = rot_to_quat_wxyz(raw_rot)
        raw_gripper = float(raw_gripper)

        if self.target_pos is None or self.target_quat is None or self.gripper_cmd is None:
            self.reset(raw_pos, raw_quat, raw_gripper)
            return raw_pos, raw_rot, raw_gripper

        if np.dot(self.target_quat, raw_quat) < 0.0:
            raw_quat = -raw_quat

        dpos = raw_pos - self.target_pos
        max_step = self.max_target_speed * max(float(dt), 1e-6)
        dpos_norm = float(np.linalg.norm(dpos))

        if dpos_norm > max_step and dpos_norm > 1e-12:
            dpos = dpos * (max_step / dpos_norm)

        limited_pos = self.target_pos + dpos
        self.target_pos = (
            (1.0 - self.alpha_pos) * self.target_pos
            + self.alpha_pos * limited_pos
        )

        self.target_quat = quat_slerp(
            self.target_quat.astype(np.float32),
            raw_quat.astype(np.float32),
            self.alpha_rot,
        ).astype(np.float64)
        self.target_quat /= np.linalg.norm(self.target_quat) + 1e-12

        self.gripper_cmd = (
            (1.0 - self.alpha_gripper) * self.gripper_cmd
            + self.alpha_gripper * raw_gripper
        )

        return (
            self.target_pos.copy(),
            quat_wxyz_to_rot(self.target_quat),
            float(self.gripper_cmd),
        )

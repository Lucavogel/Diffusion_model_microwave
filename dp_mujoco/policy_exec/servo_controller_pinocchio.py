from __future__ import annotations

from pathlib import Path

import numpy as np

from dp_mujoco.kinematics.ur10_pinocchio_kinematics import UR10PinocchioKinematics


def orientation_error(target_rot: np.ndarray, current_rot: np.ndarray) -> np.ndarray:
    rot_err = target_rot @ current_rot.T

    err = 0.5 * np.array(
        [
            rot_err[2, 1] - rot_err[1, 2],
            rot_err[0, 2] - rot_err[2, 0],
            rot_err[1, 0] - rot_err[0, 1],
        ],
        dtype=np.float64,
    )

    return err


class PinocchioServoController:
    def __init__(
        self,
        urdf_path: str | Path,
        home_q: np.ndarray,
        ee_frame_name: str = "tool0",
        tcp_offset_pos: np.ndarray | None = None,
        tcp_offset_rot: np.ndarray | None = None,
        base_offset_pos: np.ndarray | None = None,
        base_offset_rot: np.ndarray | None = None,
        kp_pos: float = 5.0,
        kp_rot: float = 2.0,
        damping: float = 0.05,
        max_joint_vel: float = 0.8,
        alpha_dq: float = 0.25,
        joint_min: np.ndarray | None = None,
        joint_max: np.ndarray | None = None,
    ) -> None:
        self.kin = UR10PinocchioKinematics(
            urdf_path=urdf_path,
            ee_frame_name=ee_frame_name,
            tcp_offset_pos=tcp_offset_pos,
            tcp_offset_rot=tcp_offset_rot,
            base_offset_pos=base_offset_pos,
            base_offset_rot=base_offset_rot,
        )

        self.home_q = np.asarray(home_q, dtype=np.float64).reshape(6).copy()
        self.q_target = self.home_q.copy()

        self.kp_pos = float(kp_pos)
        self.kp_rot = float(kp_rot)
        self.damping = float(damping)
        self.max_joint_vel = float(max_joint_vel)
        self.alpha_dq = float(alpha_dq)

        self.prev_dq = np.zeros(6, dtype=np.float64)

        if joint_min is None:
            joint_min = np.array(
                [-2 * np.pi, -2 * np.pi, -np.pi, -2 * np.pi, -2 * np.pi, -2 * np.pi],
                dtype=np.float64,
            )

        if joint_max is None:
            joint_max = np.array(
                [2 * np.pi, 2 * np.pi, np.pi, 2 * np.pi, 2 * np.pi, 2 * np.pi],
                dtype=np.float64,
            )

        self.joint_min = np.asarray(joint_min, dtype=np.float64).reshape(6)
        self.joint_max = np.asarray(joint_max, dtype=np.float64).reshape(6)

    def reset(self, q: np.ndarray | None = None, gripper_cmd: float | None = None) -> None:
        if q is None:
            q = self.home_q

        self.q_target = np.asarray(q, dtype=np.float64).reshape(6).copy()
        self.prev_dq[:] = 0.0

    def compute(
        self,
        q_current: np.ndarray,
        target_pos: np.ndarray,
        target_rot: np.ndarray,
        dt: float,
    ) -> tuple[np.ndarray, dict]:
            
        q_current = np.asarray(q_current, dtype=np.float64).reshape(6)
        target_pos = np.asarray(target_pos, dtype=np.float64).reshape(3)
        target_rot = np.asarray(target_rot, dtype=np.float64).reshape(3, 3)

        current_pos, current_rot, J = self.kin.forward_and_jacobian(q_current)

        pos_err = target_pos - current_pos
        rot_err = orientation_error(target_rot, current_rot)

        err = np.hstack(
            [
                self.kp_pos * pos_err,
                self.kp_rot * rot_err,
            ]
        )

        lambda2 = self.damping ** 2
        JJt = J @ J.T

        dq = J.T @ np.linalg.solve(
            JJt + lambda2 * np.eye(6),
            err,
        )

        dq = np.clip(dq, -self.max_joint_vel, self.max_joint_vel)

        dq = (1.0 - self.alpha_dq) * self.prev_dq + self.alpha_dq * dq
        self.prev_dq = dq.copy()

        # Sécurité : si q_target est trop loin du robot réel, on resynchronise.
        # Ça évite que la cible interne parte trop loin si le bras décroche.
        if np.linalg.norm(self.q_target - q_current) > 0.35:
            self.q_target = q_current.copy()

        # IMPORTANT :
        # On intègre depuis l'ancien q_target, pas depuis q_current.
        # Sinon la commande suit la chute du robot au lieu de le tenir.
        self.q_target = self.q_target + dq * dt
        self.q_target = np.clip(self.q_target, self.joint_min, self.joint_max)

        info = {
            "current_pos": current_pos,
            "current_rot": current_rot,
            "target_pos": target_pos,
            "target_rot": target_rot,
            "pos_err": pos_err,
            "rot_err": rot_err,
            "dq": dq,
            "J": J,
            "cond": float(np.linalg.cond(J @ J.T + lambda2 * np.eye(6))),
        }

        return self.q_target.copy(), info
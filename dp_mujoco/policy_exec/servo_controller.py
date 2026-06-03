from __future__ import annotations

from typing import Any, Dict

import mujoco
import numpy as np

from dp_mujoco.common.pose_utils import orientation_error


class ServoController:
    def __init__(
        self,
        home_q: np.ndarray,
        kp_pos: float = 5.0,
        kp_rot: float = 2.0,
        max_joint_vel: float = 0.8,
        alpha_dq: float = 0.2,
        alpha_grip: float = 1.0,
        pos_deadzone: float = 0.0,
        rot_deadzone: float = 0.0,
    ):
        self.kp_pos = float(kp_pos)
        self.kp_rot = float(kp_rot)
        self.max_joint_vel = float(max_joint_vel)
        self.alpha_dq = float(alpha_dq)
        self.alpha_grip = float(alpha_grip)

        self.pos_deadzone = float(pos_deadzone)
        self.rot_deadzone = float(rot_deadzone)

        self.q_target = np.asarray(home_q, dtype=np.float64).copy()
        self.smooth_dq = np.zeros(6, dtype=np.float64)
        self.smooth_gripper_cmd = -0.2

    def reset(self, q_target: np.ndarray, gripper_cmd: float = -0.2) -> None:
        self.q_target = np.asarray(q_target, dtype=np.float64).copy()
        self.smooth_dq[:] = 0.0
        self.smooth_gripper_cmd = float(gripper_cmd)

    def compute(
			self,
			model,
			data,
			grasp_site_id: int,
			joint_min: np.ndarray,
			joint_max: np.ndarray,
			target_pos: np.ndarray,
			target_rot: np.ndarray,
			gripper_cmd: float,
			dt: float | None = None,
		) -> Dict[str, Any]:
        grasp_pos = data.site_xpos[grasp_site_id].copy()
        R_current = data.site_xmat[grasp_site_id].reshape(3, 3).copy()

        pos_err = np.asarray(target_pos, dtype=np.float64) - grasp_pos
        rot_err = orientation_error(
            np.asarray(target_rot, dtype=np.float64),
            R_current
        )

        raw_pos_err = pos_err.copy()
        raw_rot_err = rot_err.copy()

        pos_err_norm = float(np.linalg.norm(pos_err))
        rot_err_norm = float(np.linalg.norm(rot_err))

        if self.pos_deadzone > 0.0 and pos_err_norm < self.pos_deadzone:
            pos_err[:] = 0.0

        if self.rot_deadzone > 0.0 and rot_err_norm < self.rot_deadzone:
            rot_err[:] = 0.0

        err = np.hstack([
            self.kp_pos * pos_err,
            self.kp_rot * rot_err
        ])

        jacp = np.zeros((3, model.nv), dtype=np.float64)
        jacr = np.zeros((3, model.nv), dtype=np.float64)
        mujoco.mj_jacSite(model, data, jacp, jacr, grasp_site_id)

        J = np.vstack([
            jacp[:, :6],
            jacr[:, :6]
        ])

        lambda2 = 5e-3
        JJt = J @ J.T

        dq = J.T @ np.linalg.solve(
            JJt + lambda2 * np.eye(6),
            err
        )

        dq = np.clip(dq, -self.max_joint_vel, self.max_joint_vel)

        self.smooth_dq = (
            self.alpha_dq * dq
            + (1.0 - self.alpha_dq) * self.smooth_dq
        )

        dt = float(model.opt.timestep) if dt is None else float(dt)

        self.q_target = np.clip(
            self.q_target + self.smooth_dq * dt,
            joint_min,
            joint_max
        )

        self.smooth_gripper_cmd = (
            self.alpha_grip * float(gripper_cmd)
            + (1.0 - self.alpha_grip) * self.smooth_gripper_cmd
        )

        return {
            "q_target": self.q_target.copy(),
            "gripper_cmd": float(self.smooth_gripper_cmd),

            "J": J,
            "dq": dq,
            "smooth_dq": self.smooth_dq.copy(),

            "pos_err": pos_err,
            "rot_err": rot_err,

            "raw_pos_err": raw_pos_err,
            "raw_rot_err": raw_rot_err,
            "pos_err_norm": pos_err_norm,
            "rot_err_norm": rot_err_norm,
        }
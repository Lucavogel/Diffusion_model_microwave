from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import torch

from dp_mujoco.common.pose_utils import quat_to_rot, rot6d_to_rotmat


def extract_action_sequence(policy_out: Dict[str, torch.Tensor]) -> np.ndarray:
	if "action" not in policy_out:
		raise KeyError("Policy output does not contain key 'action'.")

	action = policy_out["action"]

	if action.ndim == 3:
		return action[0].detach().cpu().numpy()
	if action.ndim == 2:
		return action.detach().cpu().numpy()
	if action.ndim == 1:
		return action.detach().cpu().numpy()[None, :]

	raise ValueError(f"Unexpected action shape: {tuple(action.shape)}")


def decode_action(
	action: np.ndarray,
	ignore_action_orientation: bool,
	current_rot: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, float]:
	"""
	Supporte:
	  - 8D  = [x,y,z,qx,qy,qz,qw,gripper]
	  - 10D = [x,y,z,r6d(6),gripper]
	Retourne target_pos, target_rot, gripper_cmd.
	"""
	if action.ndim != 1:
		raise ValueError(f"Expected 1D action, got shape {action.shape}")

	if action.shape[0] == 8:
		target_pos = action[:3].astype(np.float64)
		target_quat = action[3:7].astype(np.float64)
		target_quat /= np.linalg.norm(target_quat) + 1e-12
		target_rot = quat_to_rot(
			float(target_quat[0]),
			float(target_quat[1]),
			float(target_quat[2]),
			float(target_quat[3]),
		)
		gripper_cmd = float(action[7])
	elif action.shape[0] == 10:
		target_pos = action[:3].astype(np.float64)
		target_rot = rot6d_to_rotmat(action[3:9])
		gripper_cmd = float(action[9])
	else:
		raise ValueError(
			f"Unsupported action dimension {action.shape[0]}. Expected 8 (quat) or 10 (rot6d)."
		)

	if ignore_action_orientation:
		target_rot = current_rot.copy()

	return target_pos, target_rot, gripper_cmd

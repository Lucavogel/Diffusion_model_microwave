from __future__ import annotations

import collections
import importlib.util
from collections import deque
from pathlib import Path
from typing import Deque, Optional, Tuple

import numpy as np
from dp_mujoco.common.pose_utils import quat_slerp, quat_to_rot, rot_to_quat
from dp_mujoco.policy_exec.action_decoder import decode_action


class TrajectoryExecutor:
	def __init__(
		self,
		action_dt: float,
		exec_horizon: int,
		ignore_action_orientation: bool = False,
		action_quat_format: str = "xyzw",
	):
		self.action_dt = float(action_dt)
		self.exec_horizon = int(exec_horizon)
		self.ignore_action_orientation = bool(ignore_action_orientation)
		if action_quat_format not in {"xyzw", "wxyz"}:
			raise ValueError(f"Unknown action_quat_format: {action_quat_format}")
		self.action_quat_format = str(action_quat_format)

		self.action_buffer: Deque[np.ndarray] = collections.deque()
		self.current_action: Optional[np.ndarray] = None
		self.last_action_switch_sim_t = 0.0
		self.action_start_time = 0.0

		self.prev_target_pos = np.zeros(3, dtype=np.float64)
		self.prev_target_quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
		self.prev_gripper_cmd = -0.2

		self.interp_start_pos = self.prev_target_pos.copy()
		self.interp_start_quat = self.prev_target_quat.copy()
		self.interp_start_gripper = self.prev_gripper_cmd
		self.interp_end_pos = self.prev_target_pos.copy()
		self.interp_end_quat = self.prev_target_quat.copy()
		self.interp_end_gripper = self.prev_gripper_cmd

	def reset(self, initial_pos: np.ndarray, initial_quat: np.ndarray, initial_gripper: float, sim_time: float) -> None:
		self.action_buffer.clear()
		self.current_action = None
		self.last_action_switch_sim_t = float(sim_time) - self.action_dt
		self.action_start_time = self.last_action_switch_sim_t
		self.prev_target_pos = np.asarray(initial_pos, dtype=np.float64).copy()
		self.prev_target_quat = np.asarray(initial_quat, dtype=np.float32).copy()
		self.prev_gripper_cmd = float(initial_gripper)
		self.interp_start_pos = self.prev_target_pos.copy()
		self.interp_start_quat = self.prev_target_quat.copy()
		self.interp_start_gripper = self.prev_gripper_cmd
		self.interp_end_pos = self.prev_target_pos.copy()
		self.interp_end_quat = self.prev_target_quat.copy()
		self.interp_end_gripper = self.prev_gripper_cmd

	def needs_replan(self, sim_time: float) -> bool:
		return (float(sim_time) - self.last_action_switch_sim_t) >= self.action_dt

	def has_buffered_actions(self) -> bool:
		return len(self.action_buffer) > 0

	def has_active_action(self) -> bool:
		return self.current_action is not None

	def clear(self) -> None:
		self.action_buffer.clear()
		self.current_action = None

	def set_sequence(self, action_seq: np.ndarray) -> int:
		if action_seq.ndim != 2:
			raise ValueError(f"Expected [T,D] action sequence, got {action_seq.shape}")
		n_take = min(self.exec_horizon, action_seq.shape[0])
		self.action_buffer = collections.deque([a.astype(np.float32) for a in action_seq[:n_take]])
		return n_take

	def start_next_action(self, current_obs_quat: np.ndarray, current_time: float) -> bool:
		if len(self.action_buffer) == 0:
			self.current_action = None
			return False

		self.current_action = self.action_buffer.popleft()
		obs_quat = np.asarray(current_obs_quat, dtype=np.float64)
		current_rot = quat_to_rot(float(obs_quat[1]), float(obs_quat[2]), float(obs_quat[3]), float(obs_quat[0]))
		new_end_pos, new_end_rot, new_end_gripper = decode_action(
			self.current_action,
			ignore_action_orientation=self.ignore_action_orientation,
			current_rot=current_rot,
			quat_format=self.action_quat_format,
		)
		new_end_quat = rot_to_quat(new_end_rot)
		new_end_quat = np.array([new_end_quat[3], new_end_quat[0], new_end_quat[1], new_end_quat[2]], dtype=np.float32)

		self.interp_start_pos = self.prev_target_pos.copy()
		self.interp_start_quat = self.prev_target_quat.copy()
		self.interp_start_gripper = self.prev_gripper_cmd
		self.interp_end_pos = new_end_pos.copy()
		self.interp_end_quat = new_end_quat.copy()
		self.interp_end_gripper = float(new_end_gripper)

		self.prev_target_pos = self.interp_end_pos.copy()
		self.prev_target_quat = self.interp_end_quat.copy()
		self.prev_gripper_cmd = self.interp_end_gripper
		self.last_action_switch_sim_t = float(current_time)
		self.action_start_time = float(current_time)
		return True

	def get_target(self, sim_time: float) -> Tuple[np.ndarray, np.ndarray, float, float]:
		if self.action_dt > 0.0:
			alpha = float((float(sim_time) - self.action_start_time) / self.action_dt)
			alpha = max(0.0, min(1.0, alpha))
		else:
			alpha = 1.0

		target_pos = (1.0 - alpha) * self.interp_start_pos + alpha * self.interp_end_pos
		interp_quat = quat_slerp(self.interp_start_quat, self.interp_end_quat, alpha)
		target_rot = quat_to_rot(float(interp_quat[1]), float(interp_quat[2]), float(interp_quat[3]), float(interp_quat[0]))
		gripper_cmd = float((1.0 - alpha) * self.interp_start_gripper + alpha * self.interp_end_gripper)
		return target_pos, target_rot, gripper_cmd, alpha

from __future__ import annotations

import time
from typing import Dict, Optional

import numpy as np

class RealEpisodeRecorder:
    def __init__(self, record_freq: float = 10.0):
        self.record_freq = float(record_freq)
        self.last_record_time = time.time()
        self.is_recording = False

        self.current_episode_data = self._empty_episode()
    
    def _empty_episode(self) -> Dict[str, list]:
        return {
            "agentview_image": [],
            "robot0_eye_in_hand_image": [],
            "robot0_eef_pos": [],
            "robot0_eef_quat": [],
            "robot0_gripper_qpos": [],
            "action": [],
        }

    def start(self) -> None:
        self.current_episode_data = self._empty_episode()
        self.last_record_time = time.time()
        self.is_recording = True
        print("\n=== Recording Started ===")

    def cancel(self) -> None:
        self.is_recording = False
        self.current_episode_data = self._empty_episode()
        print("\n[!] Recording Canceled (Discarded) [!]")

    def stop(self) -> None:
        self.is_recording = False
        print("\n=== Recording Stopped ===")

    def should_record(self) -> bool:
        return time.time() - self.last_record_time >= (1.0 / self.record_freq)

    def has_data(self) -> bool:
        return len(self.current_episode_data["action"]) > 0
    
    def record_if_needed(
        self, 
        robot_state: Dict[str, np.ndarray],
        top_down_rgb: np.ndarray,
        wrist_rgb: np.ndarray,   
        target_pos: Optional[np.ndarray],
        target_quat: Optional[np.ndarray],
        gripper_cmd: float,
        ) -> None:

        if not self.is_recording or not self.should_record():
            return
        
        eef_pos = np.asarray(robot_state["eef_pos"], dtype=np.float32)
        eef_quat = np.asarray(robot_state["eef_quat"], dtype=np.float32)
        gripper_qpos = np.asarray(robot_state["gripper_qpos"], dtype=np.float32)

        top_down_rgb = np.asarray(top_down_rgb, dtype=np.uint8)
        wrist_rgb = np.asarray(wrist_rgb, dtype=np.uint8)

        if gripper_qpos.shape != (1,):
            raise ValueError(f"gripper_qpos must have shape (1,), got {gripper_qpos.shape}")

        if top_down_rgb.ndim != 3 or top_down_rgb.shape[2] != 3:
            raise ValueError(
                f"top_down_rgb must have shape (H, W, 3), got {top_down_rgb.shape}"
            )

        if wrist_rgb.ndim != 3 or wrist_rgb.shape[2] != 3:
            raise ValueError(
                f"wrist_rgb must have shape (H, W, 3), got {wrist_rgb.shape}"
            )
        
        target_pos_save = (
            np.asarray(target_pos, dtype=np.float32)
            if target_pos is not None
            else eef_pos
        )

        target_quat_save = (
            np.asarray(target_quat, dtype=np.float32)
            if target_quat is not None
            else eef_quat
        )

        if target_pos_save.shape != (3,):
            raise ValueError(f"target_pos must have shape (3,), got {target_pos_save.shape}")

        if target_quat_save.shape != (4,):
            raise ValueError(f"target_quat must have shape (4,), got {target_quat_save.shape}")
                
        action_vec = np.concatenate(
            [
            target_pos_save.astype(np.float32), 
            target_quat_save.astype(np.float32), 
            np.array([gripper_cmd], dtype=np.float32)
            ]
            ).astype(np.float32)
    

        if action_vec.shape != (8,):
            raise ValueError(f"action_vec must have shape (8,), got {action_vec.shape}")

        self.current_episode_data["agentview_image"].append(top_down_rgb)
        self.current_episode_data["robot0_eye_in_hand_image"].append(wrist_rgb)
        self.current_episode_data["robot0_eef_pos"].append(eef_pos)
        self.current_episode_data["robot0_eef_quat"].append(eef_quat)
        self.current_episode_data["robot0_gripper_qpos"].append(gripper_qpos)

        self.current_episode_data["action"].append(action_vec)

        self.last_record_time = time.time()

    def to_numpy(self) -> Optional[Dict[str, np.ndarray]]:
        if not self.has_data():
            return None

        episode_np = {}

        for key, values in self.current_episode_data.items():
            if key == "action":
                episode_np[key] = np.stack(values, axis=0).astype(np.float32)
            elif "image" in key:
                episode_np[key] = np.stack(values, axis=0).astype(np.uint8)
            else:
                episode_np[key] = np.stack(values, axis=0).astype(np.float32)

        return episode_np

    def __len__(self) -> int:
        return len(self.current_episode_data["action"])
from __future__ import annotations

import time
from typing import Dict, Optional

import cv2
import mujoco
import numpy as np

from dp_mujoco.policy_exec.pose_utils import rot_to_quat


class TeleopEpisodeRecorder:
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
        print("\n=== DEBUT DE L'ENREGISTREMENT ===")

    def cancel(self) -> None:
        self.is_recording = False
        self.current_episode_data = self._empty_episode()
        print("\n[!] ENREGISTREMENT ANNULÉ (Corbeille) [!]")

    def stop(self) -> None:
        self.is_recording = False
        print("\n=== FIN DE L'ENREGISTREMENT ===")

    def should_record(self) -> bool:
        return time.time() - self.last_record_time >= (1.0 / self.record_freq)

    def has_data(self) -> bool:
        return len(self.current_episode_data["action"]) > 0

    def record_if_needed(
        self,
        env,
        renderer_front,
        renderer_top,
        target_pos: Optional[np.ndarray],
        target_rot: Optional[np.ndarray],
        gripper_cmd: float,
    ) -> None:
        if not self.is_recording:
            return

        if not self.should_record():
            return

        data = env.data

        # EXACTEMENT comme ton ancien code
        rec_grasp_pos = data.site_xpos[env.grasp_site_id].copy()
        rec_R_current = data.site_xmat[env.grasp_site_id].reshape(3, 3).copy()

        img_front_84 = cv2.resize(
            renderer_front.render(),
            (84, 84),
            interpolation=cv2.INTER_AREA,
        )

        img_top_84 = cv2.resize(
            renderer_top.render(),
            (84, 84),
            interpolation=cv2.INTER_AREA,
        )

        self.current_episode_data["robot0_eye_in_hand_image"].append(img_front_84)
        self.current_episode_data["agentview_image"].append(img_top_84)

        self.current_episode_data["robot0_eef_pos"].append(
            rec_grasp_pos.astype(np.float32)
        )

        rec_rot_quat = np.empty(4)
        mujoco.mju_mat2Quat(rec_rot_quat, rec_R_current.flatten())

        self.current_episode_data["robot0_eef_quat"].append(
            rec_rot_quat.astype(np.float32)
        )

        self.current_episode_data["robot0_gripper_qpos"].append(
            np.array(
                [float(data.qpos[6] if data.qpos.shape[0] > 6 else 0.0)],
                dtype=np.float32,
            )
        )

        target_pos_save = target_pos if target_pos is not None else rec_grasp_pos
        target_rot_save = target_rot if target_rot is not None else rec_R_current
        target_rot_quat = rot_to_quat(target_rot_save).astype(np.float32)

        action_vec = np.concatenate([
            target_pos_save.astype(np.float32),
            target_rot_quat,
            np.array([gripper_cmd], dtype=np.float32),
        ]).astype(np.float32)

        self.current_episode_data["action"].append(action_vec)

        self.last_record_time = time.time()

    def to_numpy(self) -> Optional[Dict[str, np.ndarray]]:
        if not self.has_data():
            return None

        episode_np = {}

        for k, v in self.current_episode_data.items():
            if k != "action":
                episode_np[k] = np.stack(v, axis=0)
            else:
                episode_np[k] = np.stack(v, axis=0).astype(np.float32)

        return episode_np

    def __len__(self) -> int:
        return len(self.current_episode_data["action"])
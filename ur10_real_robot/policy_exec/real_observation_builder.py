from __future__ import annotations

import collections
from typing import Deque, Dict

import cv2
import numpy as np
import torch


class RealObservationBuilder:
    def __init__(
        self,
        cfg,
        device: torch.device,
        robot,
        cameras,
        image_height: int,
        image_width: int,
        gripper_qpos_fn=None,
    ) -> None:
        self.device = device
        self.robot = robot
        self.cameras = cameras
        self.gripper_qpos_fn = gripper_qpos_fn
        self.n_obs_steps = int(cfg.n_obs_steps)
        self.image_height = int(image_height)
        self.image_width = int(image_width)
        self.latest_frames = None

        self.obs_hist: Dict[str, Deque[np.ndarray]] = {
            "agentview_image": collections.deque(maxlen=self.n_obs_steps),
            "robot0_eye_in_hand_image": collections.deque(maxlen=self.n_obs_steps),
            "robot0_eef_pos": collections.deque(maxlen=self.n_obs_steps),
            "robot0_eef_quat": collections.deque(maxlen=self.n_obs_steps),
            "robot0_gripper_qpos": collections.deque(maxlen=self.n_obs_steps),
        }

    @staticmethod
    def preprocess_rgb(img: np.ndarray) -> np.ndarray:
        return np.moveaxis(img, -1, 0).astype(np.float32) / 255.0

    def initialize_history(self) -> None:
        for buf in self.obs_hist.values():
            buf.clear()
        for _ in range(self.n_obs_steps):
            self.update()

    def has_history(self) -> bool:
        return len(self.obs_hist["agentview_image"]) == self.n_obs_steps

    def get_latest_eef_pos(self) -> np.ndarray:
        return np.asarray(self.obs_hist["robot0_eef_pos"][-1], dtype=np.float64)

    def get_latest_eef_quat(self) -> np.ndarray:
        return np.asarray(self.obs_hist["robot0_eef_quat"][-1], dtype=np.float64)

    def get_latest_gripper_qpos(self) -> float:
        return float(self.obs_hist["robot0_gripper_qpos"][-1][0])

    def update(self) -> None:
        frames = self.cameras.read()
        self.latest_frames = frames

        img_agent = cv2.resize(
            frames.top_rgb,
            (self.image_width, self.image_height),
            interpolation=cv2.INTER_AREA,
        )
        img_wrist = cv2.resize(
            frames.wrist_rgb,
            (self.image_width, self.image_height),
            interpolation=cv2.INTER_AREA,
        )

        eef_pos = np.asarray(self.robot.get_eef_pos(), dtype=np.float64).reshape(3)
        eef_quat = np.asarray(self.robot.get_eef_quat(), dtype=np.float64).reshape(4)
        if self.gripper_qpos_fn is None:
            gripper_qpos = np.asarray(
                self.robot.get_gripper_qpos(),
                dtype=np.float64,
            ).reshape(1)
        else:
            gripper_qpos = np.asarray(
                self.gripper_qpos_fn(),
                dtype=np.float64,
            ).reshape(1)

        self.obs_hist["agentview_image"].append(self.preprocess_rgb(img_agent))
        self.obs_hist["robot0_eye_in_hand_image"].append(self.preprocess_rgb(img_wrist))
        self.obs_hist["robot0_eef_pos"].append(eef_pos)
        self.obs_hist["robot0_eef_quat"].append(eef_quat)
        self.obs_hist["robot0_gripper_qpos"].append(gripper_qpos)

    def build_tensor(self) -> Dict[str, torch.Tensor]:
        return {
            "agentview_image": torch.from_numpy(
                np.stack(list(self.obs_hist["agentview_image"]), axis=0)
            )[None].to(self.device),
            "robot0_eye_in_hand_image": torch.from_numpy(
                np.stack(list(self.obs_hist["robot0_eye_in_hand_image"]), axis=0)
            )[None].to(self.device),
            "robot0_eef_pos": torch.from_numpy(
                np.stack(list(self.obs_hist["robot0_eef_pos"]), axis=0)
            )[None].to(self.device),
            "robot0_eef_quat": torch.from_numpy(
                np.stack(list(self.obs_hist["robot0_eef_quat"]), axis=0)
            )[None].to(self.device),
            "robot0_gripper_qpos": torch.from_numpy(
                np.stack(list(self.obs_hist["robot0_gripper_qpos"]), axis=0)
            )[None].to(self.device),
        }

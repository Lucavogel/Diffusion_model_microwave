from typing import Dict
import copy
import numpy as np
import torch

from diffusion_policy.common.pytorch_util import dict_apply
from diffusion_policy.common.replay_buffer import ReplayBuffer
from diffusion_policy.common.sampler import SequenceSampler, get_val_mask, downsample_mask
from diffusion_policy.model.common.normalizer import LinearNormalizer
from diffusion_policy.dataset.base_dataset import BaseImageDataset
from diffusion_policy.common.normalize_util import get_image_range_normalizer


class GenericImageDataset(BaseImageDataset):
    def __init__(
        self,
        shape_meta: dict,
        dataset_path: str,
        horizon: int = 1,
        pad_before: int = 0,
        pad_after: int = 0,
        n_obs_steps: int = None,
        n_latency_steps: int = 0,
        use_cache: bool = False,
        seed: int = 42,
        val_ratio: float = 0.0,
        max_train_episodes: int = None,
        delta_action: bool = False,
    ):
        super().__init__()
        self.shape_meta = shape_meta
        self.horizon = horizon
        self.pad_before = pad_before
        self.pad_after = pad_after
        self.n_obs_steps = n_obs_steps if n_obs_steps is not None else horizon
        self.n_latency_steps = n_latency_steps
        self.use_cache = use_cache
        self.delta_action = delta_action

        # Clés nécessaires depuis le zarr
        obs_keys = list(shape_meta["obs"].keys())
        dataset_keys = obs_keys + ["action"]

        self.replay_buffer = ReplayBuffer.copy_from_path(
            dataset_path,
            keys=dataset_keys
        )

        val_mask = get_val_mask(
            n_episodes=self.replay_buffer.n_episodes,
            val_ratio=val_ratio,
            seed=seed
        )
        train_mask = ~val_mask

        if max_train_episodes is not None:
            train_mask = downsample_mask(
                mask=train_mask,
                max_n=max_train_episodes,
                seed=seed
            )

        self.train_mask = train_mask

        self.sampler = SequenceSampler(
            replay_buffer=self.replay_buffer,
            sequence_length=horizon,
            pad_before=pad_before,
            pad_after=pad_after,
            episode_mask=train_mask
        )

    def get_validation_dataset(self):
        val_set = copy.copy(self)
        val_set.sampler = SequenceSampler(
            replay_buffer=self.replay_buffer,
            sequence_length=self.horizon,
            pad_before=self.pad_before,
            pad_after=self.pad_after,
            episode_mask=~self.train_mask
        )
        return val_set

    def get_normalizer(self, mode="limits", **kwargs):
        data = {
            "action": self.replay_buffer["action"][:]
        }

        # normalisation seulement des observations low-dim
        for key, attr in self.shape_meta["obs"].items():
            if attr.get("type") != "rgb":
                data[key] = self.replay_buffer[key][:]

        normalizer = LinearNormalizer()
        normalizer.fit(data=data, last_n_dims=1, mode=mode, **kwargs)

        # normaliseur image séparé
        for key, attr in self.shape_meta["obs"].items():
            if attr.get("type") == "rgb":
                normalizer[key] = get_image_range_normalizer()

        return normalizer

    def __len__(self) -> int:
        return len(self.sampler)

    def _sample_to_data(self, sample: Dict[str, np.ndarray]) -> Dict[str, Dict[str, np.ndarray]]:
        obs_dict = {}

        # On ne garde que les n_obs_steps premières observations
        T_obs = self.n_obs_steps

        for key, attr in self.shape_meta["obs"].items():
            arr = sample[key][:T_obs]

            if attr.get("type") == "rgb":
                # sample[key] : (T, H, W, C) -> (T, C, H, W)
                arr = np.moveaxis(arr, -1, 1).astype(np.float32) / 255.0
            else:
                arr = arr.astype(np.float32)

            obs_dict[key] = arr

        action = sample["action"].astype(np.float32)

        # Optionnel : décaler l'action si latency steps
        if self.n_latency_steps > 0:
            action = action[self.n_latency_steps:]
            if action.shape[0] == 0:
                raise RuntimeError(
                    f"Action sequence became empty after applying n_latency_steps={self.n_latency_steps}"
                )

        if self.delta_action:
            action = np.diff(action, axis=0, prepend=action[:1])

        data = {
            "obs": obs_dict,
            "action": action
        }
        return data

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.sampler.sample_sequence(idx)
        data = self._sample_to_data(sample)
        torch_data = dict_apply(data, torch.from_numpy)
        return torch_data
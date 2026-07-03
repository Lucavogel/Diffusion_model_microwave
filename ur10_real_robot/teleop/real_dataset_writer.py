from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

try:
    from diffusion_policy.common.replay_buffer import ReplayBuffer
except ImportError:
    ReplayBuffer = None


class RealZarrEpisodeWriter:
    def __init__(self, dataset_path: str) -> None:
        if ReplayBuffer is None:
            raise RuntimeError(
                "diffusion_policy ReplayBuffer is not available. "
                "Check your PYTHONPATH / venv."
            )

        self.dataset_path = str(Path(dataset_path).expanduser())
        self.replay_buffer = ReplayBuffer.create_from_path(
            self.dataset_path,
            mode="a",
        )

    @property
    def n_episodes(self) -> int:
        return int(self.replay_buffer.n_episodes)

    def add_episode(self, episode_np: dict[str, np.ndarray]) -> int:
        self.replay_buffer.add_episode(
            episode_np,
            compressors="disk",
        )
        return self.n_episodes


def make_default_real_dataset_path(
    timestamp: Optional[str] = None,
    root: str = "data/datasets",
) -> str:
    import time

    if timestamp is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")

    return str(
        Path(root).expanduser()
        / f"real_demo_data_{timestamp}.zarr"
    )

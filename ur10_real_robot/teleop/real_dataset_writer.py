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


def find_latest_real_dataset_path(
    root: str = "data/datasets",
    pattern: str = "real_demo_data_*.zarr",
) -> Optional[str]:
    root_path = Path(root).expanduser()
    if not root_path.exists():
        return None

    candidates = [
        path
        for path in root_path.glob(pattern)
        if path.is_dir()
    ]
    if not candidates:
        return None

    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    return str(latest)


def resolve_real_dataset_path(
    dataset_path: Optional[str] = None,
    append_latest: bool = False,
    root: str = "data/datasets",
) -> tuple[str, str]:
    if dataset_path:
        return str(Path(dataset_path).expanduser()), "explicit"

    if append_latest:
        latest_path = find_latest_real_dataset_path(root=root)
        if latest_path is not None:
            return latest_path, "latest"

    return make_default_real_dataset_path(root=root), "new"

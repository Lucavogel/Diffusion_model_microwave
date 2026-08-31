#!/usr/bin/env python3
"""Load one simulation Zarr dataset and print a representative sample.

This is a manual diagnostic, not an automated unit test. Requiring the dataset
path on the command line keeps imports and test discovery independent of one
developer's local files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from diffusion_policy.dataset.generic_image_dataset import GenericImageDataset


SHAPE_META = {
    "obs": {
        "agentview_image": {"shape": [3, 84, 84], "type": "rgb"},
        "robot0_eye_in_hand_image": {"shape": [3, 84, 84], "type": "rgb"},
        "robot0_eef_pos": {"shape": [3], "type": "low_dim"},
        "robot0_eef_quat": {"shape": [4], "type": "low_dim"},
        "robot0_gripper_qpos": {"shape": [1], "type": "low_dim"},
    },
    "action": {"shape": [8]},
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="Path to a simulation .zarr dataset")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    dataset_path = args.dataset.expanduser().resolve()
    if not dataset_path.is_dir():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    dataset = GenericImageDataset(
        shape_meta=SHAPE_META,
        dataset_path=str(dataset_path),
        horizon=16,
        n_obs_steps=2,
        pad_before=0,
        pad_after=0,
        val_ratio=0.1,
    )
    sample = dataset[0]

    print(f"dataset: {dataset_path}")
    print(f"len(dataset): {len(dataset)}")
    for key, value in sample["obs"].items():
        print(f"obs/{key}: shape={tuple(value.shape)} dtype={value.dtype}")
    print(f"action: shape={tuple(sample['action'].shape)} dtype={sample['action'].dtype}")
    image = sample["obs"]["agentview_image"]
    print(f"agentview_image min/max: {image.min().item():.4f}/{image.max().item():.4f}")


if __name__ == "__main__":
    main()

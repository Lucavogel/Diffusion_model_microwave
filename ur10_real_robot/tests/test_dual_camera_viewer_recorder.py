#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2
import numpy as np

from ur10_real_robot.camera import DualCameraRig
from ur10_real_robot.teleop.real_dataset_writer import (
    RealZarrEpisodeWriter,
    resolve_real_dataset_path,
)
from ur10_real_robot.teleop.real_episode_recorder import RealEpisodeRecorder


CONFIG_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "ur10_real_robot/camera/config/d435i_config.json"
)
TOP_CONFIG_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "ur10_real_robot/camera/config/d435_config_dataset.json"
)
WRIST_CONFIG_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "ur10_real_robot/camera/config/d455_config_dataset.json"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview two cameras and test real dataset recording.",
    )
    parser.add_argument("--fake", action="store_true", help="Use synthetic cameras.")
    parser.add_argument("--top-serial", default="332322072359", help="Top-down camera serial.")
    parser.add_argument("--wrist-serial", default="043422251624", help="Wrist camera serial.")
    parser.add_argument("--config-path", default=CONFIG_PATH, help="RealSense JSON config.")
    parser.add_argument("--top-config-path", default=TOP_CONFIG_PATH)
    parser.add_argument("--wrist-config-path", default=WRIST_CONFIG_PATH)
    parser.add_argument("--no-advanced-config", action="store_true")
    parser.add_argument("--capture-width", type=int, default=640)
    parser.add_argument("--capture-height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--dataset-width", type=int, default=320)
    parser.add_argument("--dataset-height", type=int, default=240)
    parser.add_argument("--display-width", type=int, default=640)
    parser.add_argument("--display-height", type=int, default=480)
    parser.add_argument(
        "--top-crop",
        nargs=4,
        type=int,
        metavar=("X", "Y", "W", "H"),
        default=None,
        help="Crop top camera in raw capture pixels before resizing.",
    )
    parser.add_argument(
        "--wrist-crop",
        nargs=4,
        type=int,
        metavar=("X", "Y", "W", "H"),
        default=None,
        help="Crop wrist camera in raw capture pixels before resizing.",
    )
    parser.add_argument("--record-freq", type=float, default=10.0)
    parser.add_argument(
        "--min-episode-steps",
        type=int,
        default=3,
        help="Do not save an episode with fewer recorded steps than this.",
    )
    parser.add_argument(
        "--dataset-path",
        default=None,
        help="Output zarr path. If it exists, new episodes are appended.",
    )
    parser.add_argument(
        "--append-latest-dataset",
        action="store_true",
        help="Append to the latest data/datasets/real_demo_data_*.zarr.",
    )
    parser.add_argument("--dataset-root", default="data/datasets")
    return parser


def draw_overlay(
    image_bgr: np.ndarray,
    title: str,
    recording: bool,
    steps: int,
    saved_episodes: int,
) -> np.ndarray:
    out = image_bgr.copy()
    color = (0, 0, 255) if recording else (0, 180, 0)
    status = "REC" if recording else "READY"
    cv2.putText(
        out,
        f"{title} | {status} | steps={steps} saved={saved_episodes}",
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        out,
        "space=start/stop  backspace=cancel  q/esc=quit",
        (12, out.shape[0] - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return out


def make_dummy_robot_state(gripper_cmd: float) -> dict[str, np.ndarray]:
    return {
        "eef_pos": np.zeros(3, dtype=np.float32),
        "eef_quat": np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
        "gripper_qpos": np.array([float(gripper_cmd)], dtype=np.float32),
    }


def main() -> None:
    args = build_parser().parse_args()

    dataset_size = (args.dataset_width, args.dataset_height)
    display_size = (args.display_width, args.display_height)
    dataset_path, dataset_mode = resolve_real_dataset_path(
        dataset_path=args.dataset_path,
        append_latest=args.append_latest_dataset,
        root=args.dataset_root,
    )

    print("-------------------------------------------")
    print("DUAL CAMERA VIEWER / RECORDER")
    print("-------------------------------------------")
    print(f"fake          : {args.fake}")
    print(f"top serial    : {args.top_serial}")
    print(f"wrist serial  : {args.wrist_serial}")
    print(f"top config    : {args.top_config_path}")
    print(f"wrist config  : {args.wrist_config_path}")
    print(f"advanced cfg  : {not args.no_advanced_config}")
    print(f"capture       : {args.capture_width}x{args.capture_height} @ {args.fps}")
    print(f"dataset image : {args.dataset_width}x{args.dataset_height}")
    print(f"top crop      : {args.top_crop}")
    print(f"wrist crop    : {args.wrist_crop}")
    print(f"record freq   : {args.record_freq:.1f} Hz")
    print(f"dataset path  : {dataset_path}")
    print(f"dataset mode  : {dataset_mode}")
    print(f"min steps     : {args.min_episode_steps}")
    print("-------------------------------------------")

    cameras = DualCameraRig(
        top_serial=args.top_serial,
        wrist_serial=args.wrist_serial,
        config_path=args.config_path,
        top_config_path=args.top_config_path,
        wrist_config_path=args.wrist_config_path,
        capture_width=args.capture_width,
        capture_height=args.capture_height,
        fps=args.fps,
        dataset_size=dataset_size,
        display_size=display_size,
        fake=args.fake,
        apply_advanced_config=not args.no_advanced_config,
        top_crop=args.top_crop,
        wrist_crop=args.wrist_crop,
    )
    recorder = RealEpisodeRecorder(enabled=True, record_freq=args.record_freq)
    writer = None

    saved_episodes = 0
    if Path(dataset_path).exists():
        writer = RealZarrEpisodeWriter(dataset_path)
        saved_episodes = writer.n_episodes

    last_space = 0.0
    gripper_cmd = -0.2

    cameras.start()

    try:
        while True:
            frames = cameras.read()

            # Dummy action/state: this script validates cameras + zarr only.
            robot_state = make_dummy_robot_state(gripper_cmd)
            recorder.record_if_needed(
                robot_state=robot_state,
                top_down_rgb=frames.top_rgb,
                wrist_rgb=frames.wrist_rgb,
                target_pos=robot_state["eef_pos"],
                target_quat=robot_state["eef_quat"],
                gripper_cmd=gripper_cmd,
                timestamp=frames.timestamp,
            )

            top_display = draw_overlay(
                frames.top_display_bgr,
                "top_down",
                recorder.is_recording,
                len(recorder),
                saved_episodes,
            )
            wrist_display = draw_overlay(
                frames.wrist_display_bgr,
                "wrist",
                recorder.is_recording,
                len(recorder),
                saved_episodes,
            )

            cv2.imshow("real top_down camera", top_display)
            cv2.imshow("real wrist camera", wrist_display)

            top_dataset_bgr = cv2.cvtColor(frames.top_rgb, cv2.COLOR_RGB2BGR)
            wrist_dataset_bgr = cv2.cvtColor(frames.wrist_rgb, cv2.COLOR_RGB2BGR)
            cv2.imshow("dataset top_down image", top_dataset_bgr)
            cv2.imshow("dataset wrist image", wrist_dataset_bgr)

            key = cv2.waitKey(1) & 0xFF
            now = time.monotonic()

            if key in (ord("q"), 27):
                break

            if key == 32 and now - last_space > 0.5:
                if recorder.is_recording:
                    recorder.stop()
                    episode_np = recorder.to_numpy()
                    if episode_np is None:
                        print("[REC] Empty episode, not saved.")
                    elif len(recorder) < args.min_episode_steps:
                        print(
                            f"[REC] Episode too short ({len(recorder)} steps), "
                            "not saved."
                        )
                        recorder.cancel()
                    else:
                        if writer is None:
                            writer = RealZarrEpisodeWriter(dataset_path)
                        saved_episodes = writer.add_episode(episode_np)
                        print(
                            f"[REC] Saved episode with {len(recorder)} steps. "
                            f"Total episodes: {saved_episodes}"
                        )
                else:
                    recorder.start()
                last_space = now

            if key in (8, 127):
                recorder.cancel()

    finally:
        cameras.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

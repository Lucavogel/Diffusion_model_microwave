import argparse
import time
from pathlib import Path

import cv2
import numpy as np
import zarr

from ur10_real_robot.camera import DualCameraRig


def parse_crop(values):
    if values is None:
        return None
    if len(values) != 4:
        raise ValueError("Crop must contain four integers: x y width height")
    return tuple(int(v) for v in values)


def episode_start_end(episode_ends, episode_index):
    if episode_index < 0 or episode_index >= len(episode_ends):
        raise ValueError(
            f"Episode index {episode_index} outside [0, {len(episode_ends) - 1}]"
        )
    start = 0 if episode_index == 0 else int(episode_ends[episode_index - 1])
    end = int(episode_ends[episode_index])
    return start, end


def resize_max_width(img, max_width):
    if max_width is None or img.shape[1] <= max_width:
        return img
    scale = max_width / float(img.shape[1])
    return cv2.resize(
        img,
        (max_width, int(round(img.shape[0] * scale))),
        interpolation=cv2.INTER_AREA,
    )


def label(img, text, color=(0, 255, 0)):
    out = img.copy()
    cv2.putText(
        out,
        text,
        (8, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        color,
        2,
        cv2.LINE_AA,
    )
    return out


def make_row(name, dataset_rgb, live_rgb):
    dataset_bgr = cv2.cvtColor(dataset_rgb, cv2.COLOR_RGB2BGR)
    live_bgr = cv2.cvtColor(live_rgb, cv2.COLOR_RGB2BGR)

    diff = cv2.absdiff(dataset_bgr, live_bgr)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    diff_color = cv2.applyColorMap(diff_gray, cv2.COLORMAP_INFERNO)

    row = np.hstack(
        (
            label(dataset_bgr, f"{name} dataset"),
            label(live_bgr, f"{name} live"),
            label(diff_color, f"{name} abs diff", color=(255, 255, 255)),
        )
    )
    return row


def build_display(dataset_top, dataset_wrist, live_top, live_wrist, info, max_width):
    top_row = make_row("top", dataset_top, live_top)
    wrist_row = make_row("wrist", dataset_wrist, live_wrist)

    sep = np.full((18, top_row.shape[1], 3), 255, dtype=np.uint8)
    canvas = np.vstack((top_row, sep, wrist_row))
    canvas = resize_max_width(canvas, max_width)
    cv2.putText(
        canvas,
        info,
        (10, canvas.shape[0] - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        info,
        (10, canvas.shape[0] - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    return canvas


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare one frame from a zarr dataset with the current live "
            "RealSense images after the same crop/resize preprocessing."
        )
    )
    parser.add_argument("zarr_path", type=str, help="Path to the dataset .zarr folder.")
    parser.add_argument("--episode", type=int, default=0, help="Episode index, 0-based.")
    parser.add_argument(
        "--frame",
        type=int,
        default=0,
        help="Frame index inside the selected episode, 0-based.",
    )
    parser.add_argument("--top-serial", default="332322072359")
    parser.add_argument("--wrist-serial", default="043422251624")
    parser.add_argument(
        "--top-camera-config",
        default="ur10_real_robot/camera/config/d435_config_dataset.json",
    )
    parser.add_argument(
        "--wrist-camera-config",
        default="ur10_real_robot/camera/config/d455_config_microwave_auto.json",
    )
    parser.add_argument("--top-crop", nargs=4, type=int, default=(40, 30, 560, 420))
    parser.add_argument("--wrist-crop", nargs=4, type=int, default=(0, 0, 640, 480))
    parser.add_argument("--dataset-width", type=int, default=320)
    parser.add_argument("--dataset-height", type=int, default=240)
    parser.add_argument("--capture-width", type=int, default=640)
    parser.add_argument("--capture-height", type=int, default=480)
    parser.add_argument("--camera-fps", type=int, default=30)
    parser.add_argument("--max-display-width", type=int, default=1500)
    parser.add_argument(
        "--save-once",
        type=str,
        default=None,
        help="Capture one comparison image, save it to this path, and exit.",
    )
    parser.add_argument(
        "--warmup-frames",
        type=int,
        default=30,
        help="Number of live frames to discard before a one-shot capture.",
    )
    parser.add_argument("--no-advanced-config", action="store_true")
    parser.add_argument("--fake", action="store_true")
    args = parser.parse_args()

    root = zarr.open(args.zarr_path, mode="r")
    top_data = root["data/agentview_image"]
    wrist_data = root["data/robot0_eye_in_hand_image"]
    episode_ends = root["meta/episode_ends"][:]

    episode = int(args.episode)
    ep_start, ep_end = episode_start_end(episode_ends, episode)
    frame = int(np.clip(args.frame, 0, ep_end - ep_start - 1))

    cameras = DualCameraRig(
        top_serial=args.top_serial,
        wrist_serial=args.wrist_serial,
        top_config_path=args.top_camera_config,
        wrist_config_path=args.wrist_camera_config,
        capture_width=args.capture_width,
        capture_height=args.capture_height,
        fps=args.camera_fps,
        dataset_size=(args.dataset_width, args.dataset_height),
        display_size=(640, 480),
        fake=args.fake,
        apply_advanced_config=not args.no_advanced_config,
        top_crop=parse_crop(args.top_crop),
        wrist_crop=parse_crop(args.wrist_crop),
    )

    print("--------------------------------------------------")
    print("LIVE CAMERA VS DATASET IMAGE COMPARISON")
    print("--------------------------------------------------")
    print(f"Dataset       : {args.zarr_path}")
    print(f"Episodes      : {len(episode_ends)}")
    print(f"Initial ep/fr : {episode}/{frame}")
    print("Controls:")
    print("  N / Right : next dataset frame")
    print("  B / Left  : previous dataset frame")
    print("  ]         : next episode")
    print("  [         : previous episode")
    print("  S         : save current comparison PNG in /tmp")
    print("  Q / Esc   : quit")
    print("--------------------------------------------------")

    cameras.start()
    try:
        if args.save_once is not None:
            live = None
            for _ in range(max(1, args.warmup_frames)):
                live = cameras.read()

            global_idx = ep_start + frame
            display = build_display(
                top_data[global_idx],
                wrist_data[global_idx],
                live.top_rgb,
                live.wrist_rgb,
                f"episode={episode} frame={frame} global={global_idx}",
                args.max_display_width,
            )
            output_path = Path(args.save_once).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(output_path), display):
                raise RuntimeError(f"Could not save comparison image: {output_path}")
            print(f"[saved] {output_path}")
            return

        while True:
            global_idx = ep_start + frame
            dataset_top = top_data[global_idx]
            dataset_wrist = wrist_data[global_idx]

            live = cameras.read()
            info = (
                f"episode={episode} frame={frame}/{ep_end - ep_start - 1} "
                f"global={global_idx} | q/esc quit, n/b frame, [/ ] episode, s save"
            )
            display = build_display(
                dataset_top,
                dataset_wrist,
                live.top_rgb,
                live.wrist_rgb,
                info,
                args.max_display_width,
            )
            cv2.imshow("dataset vs live cameras", display)

            key_raw = cv2.waitKeyEx(20)
            key = key_raw & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("s"):
                out = Path("/tmp") / (
                    f"dataset_live_compare_ep{episode:03d}_frame{frame:04d}.png"
                )
                cv2.imwrite(str(out), display)
                print(f"[saved] {out}")
            elif key == ord("n") or key_raw in (65363, 2555904):
                frame = min(frame + 1, ep_end - ep_start - 1)
            elif key == ord("b") or key_raw in (65361, 2424832):
                frame = max(frame - 1, 0)
            elif key == ord("]"):
                episode = min(episode + 1, len(episode_ends) - 1)
                ep_start, ep_end = episode_start_end(episode_ends, episode)
                frame = min(frame, ep_end - ep_start - 1)
            elif key == ord("["):
                episode = max(episode - 1, 0)
                ep_start, ep_end = episode_start_end(episode_ends, episode)
                frame = min(frame, ep_end - ep_start - 1)

            time.sleep(0.005)
    finally:
        cameras.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

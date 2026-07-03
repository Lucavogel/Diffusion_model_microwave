from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from ur10_real_robot.camera.realsense_camera import RealSenseCamera


@dataclass
class DualCameraFrames:
    top_rgb: np.ndarray
    wrist_rgb: np.ndarray
    top_display_bgr: np.ndarray
    wrist_display_bgr: np.ndarray
    timestamp: float


class FakeCamera:
    """Synthetic camera stream used when the real cameras are not plugged in."""

    def __init__(
        self,
        name: str,
        output_size: tuple[int, int] = (320, 240),
        display_size: tuple[int, int] = (640, 480),
    ) -> None:
        self.name = str(name)
        self.output_size = tuple(output_size)
        self.display_size = tuple(display_size)
        self.started = False
        self.frame_idx = 0

    def start(self) -> None:
        self.started = True
        self.frame_idx = 0
        print(f"[FakeCamera] {self.name} started.")

    def stop(self) -> None:
        self.started = False
        print(f"[FakeCamera] {self.name} stopped.")

    def read(self) -> dict[str, np.ndarray]:
        if not self.started:
            raise RuntimeError(f"FakeCamera {self.name} is not started.")

        width, height = self.output_size
        x = np.linspace(0, 255, width, dtype=np.uint8)[None, :]
        y = np.linspace(0, 255, height, dtype=np.uint8)[:, None]
        phase = (self.frame_idx * 3) % 255

        if "top" in self.name.lower():
            rgb = np.stack(
                [
                    np.repeat(x, height, axis=0),
                    np.repeat(y, width, axis=1),
                    np.full((height, width), phase, dtype=np.uint8),
                ],
                axis=-1,
            )
        else:
            rgb = np.stack(
                [
                    np.full((height, width), phase, dtype=np.uint8),
                    np.repeat(x, height, axis=0),
                    np.repeat(y, width, axis=1),
                ],
                axis=-1,
            )

        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        cv2.putText(
            bgr,
            f"{self.name} fake",
            (18, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            bgr,
            f"frame {self.frame_idx}",
            (18, 68),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        display_bgr = cv2.resize(
            bgr,
            self.display_size,
            interpolation=cv2.INTER_NEAREST,
        )
        self.frame_idx += 1

        return {
            "bgr": bgr,
            "display_bgr": display_bgr,
            "rgb_resized": rgb,
        }


class DualCameraRig:
    """
    Two-camera capture helper for real data collection.

    Dataset names follow the simulation recorder:
    - top camera -> agentview_image
    - wrist camera -> robot0_eye_in_hand_image
    """

    def __init__(
        self,
        top_serial: Optional[str] = None,
        wrist_serial: Optional[str] = None,
        config_path: Optional[str] = None,
        capture_width: int = 640,
        capture_height: int = 480,
        fps: int = 30,
        dataset_size: tuple[int, int] = (320, 240),
        display_size: tuple[int, int] = (640, 480),
        fake: bool = False,
        apply_advanced_config: bool = True,
    ) -> None:
        self.fake = bool(fake)
        self.dataset_size = tuple(dataset_size)
        self.display_size = tuple(display_size)

        camera_cls = FakeCamera if self.fake else RealSenseCamera

        if self.fake:
            self.top_camera = camera_cls(
                name="top_down",
                output_size=self.dataset_size,
                display_size=self.display_size,
            )
            self.wrist_camera = camera_cls(
                name="wrist",
                output_size=self.dataset_size,
                display_size=self.display_size,
            )
        else:
            self.top_camera = camera_cls(
                config_path=config_path,
                width=capture_width,
                height=capture_height,
                fps=fps,
                output_size=self.dataset_size,
                display_size=self.display_size,
                serial_number=top_serial,
                apply_advanced_config=apply_advanced_config,
            )
            self.wrist_camera = camera_cls(
                config_path=config_path,
                width=capture_width,
                height=capture_height,
                fps=fps,
                output_size=self.dataset_size,
                display_size=self.display_size,
                serial_number=wrist_serial,
                apply_advanced_config=apply_advanced_config,
            )

        self.started = False

    def start(self) -> None:
        if self.started:
            return

        self.top_camera.start()
        try:
            self.wrist_camera.start()
        except Exception:
            self.top_camera.stop()
            raise

        self.started = True
        print("[DualCameraRig] Started.")
        print(f"[DualCameraRig] Dataset image size: {self.dataset_size}")

    def read(self) -> DualCameraFrames:
        if not self.started:
            raise RuntimeError("DualCameraRig is not started.")

        top = self.top_camera.read()
        wrist = self.wrist_camera.read()

        return DualCameraFrames(
            top_rgb=top["rgb_resized"],
            wrist_rgb=wrist["rgb_resized"],
            top_display_bgr=top["display_bgr"],
            wrist_display_bgr=wrist["display_bgr"],
            timestamp=time.monotonic(),
        )

    def stop(self) -> None:
        if not self.started:
            return

        try:
            self.wrist_camera.stop()
        finally:
            self.top_camera.stop()
            self.started = False
            print("[DualCameraRig] Stopped.")

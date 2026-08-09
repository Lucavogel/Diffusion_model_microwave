from __future__ import annotations

import time
import threading
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
        crop: tuple[int, int, int, int] | None = None,
    ) -> None:
        self.name = str(name)
        self.output_size = tuple(output_size)
        self.display_size = tuple(display_size)
        self.crop = crop
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
            "cropped_bgr": bgr,
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
        top_config_path: Optional[str] = None,
        wrist_config_path: Optional[str] = None,
        capture_width: int = 640,
        capture_height: int = 480,
        fps: int = 30,
        dataset_size: tuple[int, int] = (320, 240),
        display_size: tuple[int, int] = (640, 480),
        fake: bool = False,
        apply_advanced_config: bool = True,
        top_crop: tuple[int, int, int, int] | None = None,
        wrist_crop: tuple[int, int, int, int] | None = None,
    ) -> None:
        self.fake = bool(fake)
        self.dataset_size = tuple(dataset_size)
        self.display_size = tuple(display_size)
        self.top_crop = None if top_crop is None else tuple(int(v) for v in top_crop)
        self.wrist_crop = None if wrist_crop is None else tuple(int(v) for v in wrist_crop)
        self.top_config_path = top_config_path if top_config_path is not None else config_path
        self.wrist_config_path = wrist_config_path if wrist_config_path is not None else config_path
        top_serial = None if top_serial is None else str(top_serial)
        wrist_serial = None if wrist_serial is None else str(wrist_serial)

        camera_cls = FakeCamera if self.fake else RealSenseCamera

        if self.fake:
            self.top_camera = camera_cls(
                name="top_down",
                output_size=self.dataset_size,
                display_size=self.display_size,
                crop=self.top_crop,
            )
            self.wrist_camera = camera_cls(
                name="wrist",
                output_size=self.dataset_size,
                display_size=self.display_size,
                crop=self.wrist_crop,
            )
        else:
            self.top_camera = camera_cls(
                config_path=self.top_config_path,
                width=capture_width,
                height=capture_height,
                fps=fps,
                output_size=self.dataset_size,
                display_size=self.display_size,
                serial_number=top_serial,
                apply_advanced_config=apply_advanced_config,
                crop=self.top_crop,
            )
            self.wrist_camera = camera_cls(
                config_path=self.wrist_config_path,
                width=capture_width,
                height=capture_height,
                fps=fps,
                output_size=self.dataset_size,
                display_size=self.display_size,
                serial_number=wrist_serial,
                apply_advanced_config=apply_advanced_config,
                crop=self.wrist_crop,
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

        if not self.fake:
            missing = []
            for name, camera in (
                ("top", self.top_camera),
                ("wrist", self.wrist_camera),
            ):
                if getattr(camera, "apply_advanced_config", False) and not getattr(
                    camera,
                    "advanced_config_loaded",
                    False,
                ):
                    missing.append(name)
            if missing:
                try:
                    self.wrist_camera.stop()
                finally:
                    self.top_camera.stop()
                raise RuntimeError(
                    "RealSense advanced JSON config was not loaded for: "
                    + ", ".join(missing)
                )

        self.started = True
        print("[DualCameraRig] Started.")
        print(f"[DualCameraRig] Dataset image size: {self.dataset_size}")
        print(f"[DualCameraRig] Top crop: {self.top_crop}")
        print(f"[DualCameraRig] Wrist crop: {self.wrist_crop}")
        print(f"[DualCameraRig] Top config: {self.top_config_path}")
        print(f"[DualCameraRig] Wrist config: {self.wrist_config_path}")

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


class AsyncDualCameraCapture:
    """
    Background camera reader.

    This keeps RealSense wait_for_frames() out of the robot control loop.
    """

    def __init__(self, rig: DualCameraRig, poll_period: float = 0.0) -> None:
        self.rig = rig
        self.poll_period = float(poll_period)
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.latest_frames: DualCameraFrames | None = None
        self.latest_error: str | None = None
        self.frame_count = 0

    def start(self) -> None:
        self.rig.start()
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        print("[AsyncDualCameraCapture] Started.")

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
        self.rig.stop()
        print("[AsyncDualCameraCapture] Stopped.")

    def get_latest(self) -> tuple[DualCameraFrames | None, str | None, int]:
        with self.lock:
            return self.latest_frames, self.latest_error, self.frame_count

    def _worker(self) -> None:
        while not self.stop_event.is_set():
            try:
                frames = self.rig.read()
                with self.lock:
                    self.latest_frames = frames
                    self.latest_error = None
                    self.frame_count += 1
            except Exception as exc:
                with self.lock:
                    self.latest_error = str(exc)

            if self.poll_period > 0.0:
                self.stop_event.wait(self.poll_period)

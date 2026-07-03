from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

try:
    import pyrealsense2 as rs
except ImportError:
    rs = None


class RealSenseCamera:
    def __init__(
        self,
        config_path: Optional[str] = None,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        output_size: tuple[int, int] = (84, 84),
        display_size: tuple[int, int] = (640, 480),
        serial_number: Optional[str] = None,
        apply_advanced_config: bool = True,
    ):
        self.config_path = config_path
        self.width = int(width)
        self.height = int(height)
        self.fps = int(fps)
        self.output_size = output_size
        self.display_size = display_size
        self.serial_number = serial_number
        self.apply_advanced_config = apply_advanced_config

        self.pipeline: Optional[rs.pipeline] = None
        self.profile = None
        self.started = False

    def _get_device(self):
        if rs is None:
            raise RuntimeError(
                "pyrealsense2 is not installed. Use --fake for software tests."
            )

        ctx = rs.context()
        devices = ctx.query_devices()

        if len(devices) == 0:
            raise RuntimeError("No RealSense camera detected.")

        if self.serial_number is None:
            dev = devices[0]
        else:
            dev = None
            for device in devices:
                serial = device.get_info(rs.camera_info.serial_number)
                if serial == self.serial_number:
                    dev = device
                    break

            if dev is None:
                raise RuntimeError(
                    f"RealSense camera with serial {self.serial_number} not found."
                )

        print("[RealSense] Camera detected:", dev.get_info(rs.camera_info.name))
        print("[RealSense] Serial:", dev.get_info(rs.camera_info.serial_number))

        return dev

    def _load_advanced_json_config(self) -> None:
        if self.config_path is None:
            return

        json_path = Path(self.config_path)

        if not json_path.exists():
            raise FileNotFoundError(f"RealSense config not found: {json_path}")

        dev = self._get_device()
        adv = rs.rs400_advanced_mode(dev)

        if not adv.is_enabled():
            print("[RealSense] Enabling advanced mode...")
            adv.toggle_advanced_mode(True)
            time.sleep(5.0)

            dev = self._get_device()
            adv = rs.rs400_advanced_mode(dev)

        json_text = json_path.read_text()
        json.loads(json_text)

        adv.load_json(json_text)
        print("[RealSense] Advanced JSON config loaded.")

    def start(self) -> None:
        if self.started:
            return

        if rs is None:
            raise RuntimeError(
                "pyrealsense2 is not installed. Use --fake for software tests."
            )

        if self.apply_advanced_config:
            self._load_advanced_json_config()

        self.pipeline = rs.pipeline()
        config = rs.config()

        if self.serial_number is not None:
            config.enable_device(self.serial_number)

        config.enable_stream(
            rs.stream.color,
            self.width,
            self.height,
            rs.format.bgr8,
            self.fps,
        )

        self.profile = self.pipeline.start(config)
        self.started = True

        print("[RealSense] Pipeline started.")
        print(f"[RealSense] Capture: {self.width}x{self.height} @ {self.fps} FPS")
        print(f"[RealSense] Display size: {self.display_size}")
        print(f"[RealSense] Dataset size: {self.output_size}")

    def read_bgr(self) -> np.ndarray:
        if self.pipeline is None or not self.started:
            raise RuntimeError("RealSense camera is not started.")

        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            raise RuntimeError("No color frame received.")

        return np.asanyarray(color_frame.get_data())

    def process_bgr(self, bgr: np.ndarray) -> dict[str, np.ndarray]:
        display_bgr = cv2.resize(
            bgr,
            self.display_size,
            interpolation=cv2.INTER_NEAREST,
        )

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        rgb_resized = cv2.resize(
            rgb,
            self.output_size,
            interpolation=cv2.INTER_AREA,
        )

        return {
            "bgr": bgr,
            "display_bgr": display_bgr,
            "rgb_resized": rgb_resized,
        }

    def read(self) -> dict[str, np.ndarray]:
        bgr = self.read_bgr()
        return self.process_bgr(bgr)

    def read_rgb_resized(self) -> np.ndarray:
        return self.read()["rgb_resized"]

    def stop(self) -> None:
        if self.pipeline is not None and self.started:
            self.pipeline.stop()

        self.pipeline = None
        self.profile = None
        self.started = False

        print("[RealSense] Pipeline stopped.")

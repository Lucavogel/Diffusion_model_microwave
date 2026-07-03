#!/usr/bin/env python3
from __future__ import annotations

import argparse
import threading
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from dp_mujoco.common.pose_utils import quat_to_rot


def project_to_so3(R: np.ndarray) -> np.ndarray:
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)
    U, _, Vt = np.linalg.svd(R)
    R_proj = U @ Vt
    if np.linalg.det(R_proj) < 0.0:
        U[:, -1] *= -1.0
        R_proj = U @ Vt
    return R_proj


def rot_to_rotvec(R: np.ndarray) -> np.ndarray:
    R = project_to_so3(R)
    cos_angle = (float(np.trace(R)) - 1.0) * 0.5
    cos_angle = float(np.clip(cos_angle, -1.0, 1.0))
    angle = float(np.arccos(cos_angle))

    if angle < 1e-9:
        return np.zeros(3, dtype=np.float64)

    axis = np.array(
        [
            R[2, 1] - R[1, 2],
            R[0, 2] - R[2, 0],
            R[1, 0] - R[0, 1],
        ],
        dtype=np.float64,
    )
    axis = axis / (2.0 * np.sin(angle))
    return axis * angle


def axis_map(name: str) -> np.ndarray:
    maps = {
        "identity": np.eye(3, dtype=np.float64),
        "swap_xy": np.array(
            [
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        ),
        "swap_xy_neg": np.array(
            [
                [0.0, -1.0, 0.0],
                [-1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        ),
        "swap_xy_neg_y": np.array(
            [
                [0.0, 1.0, 0.0],
                [-1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        ),
        "swap_xy_neg_x": np.array(
            [
                [0.0, -1.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        ),
        "neg_xy": np.array(
            [
                [-1.0, 0.0, 0.0],
                [0.0, -1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        ),
    }
    return maps[name]


@dataclass
class TouchSample:
    pos: np.ndarray
    rot: np.ndarray
    stamp: float


class TouchPoseProbe(Node):
    def __init__(self) -> None:
        super().__init__("touch_orientation_mapping_probe")
        self.lock = threading.Lock()
        self.sample: Optional[TouchSample] = None

        sensor_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.create_subscription(PoseStamped, "/touch/pose", self.pose_cb, sensor_qos)

    def pose_cb(self, msg: PoseStamped) -> None:
        pos = np.array(
            [msg.pose.position.x, msg.pose.position.y, msg.pose.position.z],
            dtype=np.float64,
        )
        rot = quat_to_rot(
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        )
        rot = project_to_so3(rot)

        with self.lock:
            self.sample = TouchSample(
                pos=pos,
                rot=rot,
                stamp=time.monotonic(),
            )

    def get_sample(self) -> Optional[TouchSample]:
        with self.lock:
            if self.sample is None:
                return None
            return TouchSample(
                pos=self.sample.pos.copy(),
                rot=self.sample.rot.copy(),
                stamp=self.sample.stamp,
            )


def wait_for_sample(node: TouchPoseProbe, timeout: float = 5.0) -> TouchSample:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        sample = node.get_sample()
        if sample is not None:
            return sample
        time.sleep(0.02)
    raise RuntimeError("No /touch/pose received. Is touch_ros2_driver running?")


def print_trial(name: str, start: TouchSample, end: TouchSample) -> None:
    dpos = end.pos - start.pos
    delta_rot_world = end.rot @ start.rot.T
    delta_rot_local = start.rot.T @ end.rot

    rv_world = rot_to_rotvec(delta_rot_world)
    rv_local = rot_to_rotvec(delta_rot_local)

    print("\n" + "=" * 70)
    print(f"TRIAL: {name}")
    print("=" * 70)
    print("Touch dpos        :", np.round(dpos, 6))
    print("Touch dpos mm     :", np.round(dpos * 1000.0, 2))
    print("Touch rotvec world:", np.round(rv_world, 6), "rad")
    print("Touch rotvec local:", np.round(rv_local, 6), "rad")
    print("Touch rotvec world deg:", np.round(np.degrees(rv_world), 3))
    print("Touch rotvec local deg:", np.round(np.degrees(rv_local), 3))
    print("-" * 70)
    print("Candidate mapped rotvecs from WORLD delta:")
    for map_name in [
        "identity",
        "swap_xy",
        "swap_xy_neg",
        "swap_xy_neg_y",
        "swap_xy_neg_x",
        "neg_xy",
    ]:
        M = axis_map(map_name)
        mapped = M @ rv_world
        mapped_inv = -mapped
        print(
            f"{map_name:14s} rotvec={np.round(mapped, 6)} "
            f"deg={np.round(np.degrees(mapped), 2)} | "
            f"inv_deg={np.round(np.degrees(mapped_inv), 2)}"
        )
    print("-" * 70)
    print("Candidate mapped rotvecs from LOCAL delta:")
    for map_name in [
        "identity",
        "swap_xy",
        "swap_xy_neg",
        "swap_xy_neg_y",
        "swap_xy_neg_x",
        "neg_xy",
    ]:
        M = axis_map(map_name)
        mapped = M @ rv_local
        mapped_inv = -mapped
        print(
            f"{map_name:14s} rotvec={np.round(mapped, 6)} "
            f"deg={np.round(np.degrees(mapped), 2)} | "
            f"inv_deg={np.round(np.degrees(mapped_inv), 2)}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record Touch pure rotation gestures to infer orientation mapping."
    )
    parser.add_argument(
        "--trials",
        nargs="+",
        default=["yaw_z", "pitch_x", "roll_y"],
        help="Trial names. For each one, press Enter before and after the gesture.",
    )
    return parser


def spin_thread(node: Node) -> None:
    rclpy.spin(node)


def main() -> None:
    args = build_parser().parse_args()

    rclpy.init()
    node = TouchPoseProbe()
    thread = threading.Thread(target=spin_thread, args=(node,), daemon=True)
    thread.start()

    try:
        wait_for_sample(node)
        print("-------------------------------------------")
        print("TOUCH ORIENTATION MAPPING TEST")
        print("-------------------------------------------")
        print("This script DOES NOT command the robot.")
        print("For each trial:")
        print("  1. Hold Touch still, press Enter.")
        print("  2. Do one pure rotation, press Enter again.")
        print("Send me the full output.")
        print("-------------------------------------------")

        for trial_name in args.trials:
            input(f"\n[{trial_name}] Hold still at START, then press Enter...")
            start = wait_for_sample(node)

            input(f"[{trial_name}] Do the gesture, hold END, then press Enter...")
            end = wait_for_sample(node)

            print_trial(trial_name, start, end)

    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        try:
            rclpy.shutdown()
        except Exception:
            pass
        print("\nDone.")


if __name__ == "__main__":
    main()

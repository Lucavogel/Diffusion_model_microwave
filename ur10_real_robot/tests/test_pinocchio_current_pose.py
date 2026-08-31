#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

import numpy as np

from dp_mujoco.kinematics.ur10_pinocchio_kinematics import UR10PinocchioKinematics
from ur10_real_robot.backends.ur10_rtde import UR10RealtimeSession


ROBOT_IP = os.environ.get("ROBOT_IP", "192.168.2.100")
REPO_ROOT = Path(__file__).resolve().parents[2]
URDF_PATH = str(
    REPO_ROOT
    / "dp_mujoco/models/universal_robots_ur10e/ur10_d455_support_rg2ft_fixed_gripper.urdf"
)


def rot_to_rotvec(R: np.ndarray) -> np.ndarray:
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)
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


def rotz(angle: float) -> np.ndarray:
    c = math.cos(float(angle))
    s = math.sin(float(angle))
    return np.array(
        [
            [c, -s, 0.0],
            [s, c, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def pose_vector(pos: np.ndarray, rot: np.ndarray) -> np.ndarray:
    return np.concatenate([pos, rot_to_rotvec(rot)])


def print_pose_block(title: str, pos: np.ndarray, rot: np.ndarray) -> None:
    vec = pose_vector(pos, rot)
    print(title)
    print("  pos m        :", np.round(pos, 6))
    print("  pos mm       :", np.round(pos * 1000.0, 2))
    print("  rotvec rad   :", np.round(vec[3:], 6))
    print("  rotvec deg   :", np.round(np.degrees(vec[3:]), 3))
    print("  [x y z rx ry rz]:", np.round(vec, 6))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read current UR10 joints and compute TCP/tool0 pose with Pinocchio."
    )
    parser.add_argument("--robot-ip", default=ROBOT_IP)
    parser.add_argument("--urdf", default=URDF_PATH)
    parser.add_argument("--ee-frame-name", default="tool0")
    parser.add_argument("--tcp-offset", nargs=3, type=float, default=[0.0, 0.0, 0.0])
    parser.add_argument("--base-offset", nargs=3, type=float, default=[0.0, 0.0, 0.0])
    parser.add_argument(
        "--base-rz-deg",
        type=float,
        default=0.0,
        help="Extra base rotation around Z in degrees for Pinocchio output.",
    )
    parser.add_argument("--socket-timeout", type=float, default=1.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()

    session = None
    try:
        print("[INFO] Connecting to robot realtime session...")
        session = UR10RealtimeSession(
            robot_ip=args.robot_ip,
            socket_timeout=args.socket_timeout,
        ).connect()

        data = session.read(wait=True)
        q = np.asarray(data["qActual"], dtype=float).reshape(6)
        robot_tcp = None
        if "tcp" in data and data["tcp"] is not None:
            robot_tcp = np.asarray(data["tcp"], dtype=float).reshape(-1)

        kin = UR10PinocchioKinematics(
            urdf_path=args.urdf,
            ee_frame_name=args.ee_frame_name,
            tcp_offset_pos=np.asarray(args.tcp_offset, dtype=np.float64),
            base_offset_pos=np.asarray(args.base_offset, dtype=np.float64),
            base_offset_rot=rotz(math.radians(args.base_rz_deg)),
        )

        pos, rot = kin.forward(q)
        vec = pose_vector(pos, rot)

        pos_rz_pi = rotz(math.pi) @ pos
        rot_rz_pi = rotz(math.pi) @ rot
        vec_rz_pi = pose_vector(pos_rz_pi, rot_rz_pi)

        print("\n" + "=" * 60)
        print("PINOCCHIO CURRENT ROBOT POSE")
        print("=" * 60)
        print(f"Robot IP      : {args.robot_ip}")
        print(f"URDF          : {args.urdf}")
        print(f"EE frame      : {args.ee_frame_name}")
        print("TCP offset    :", np.asarray(args.tcp_offset, dtype=float))
        print("Base offset   :", np.asarray(args.base_offset, dtype=float))
        print(f"Base rz deg   : {args.base_rz_deg:.3f}")
        print("-" * 60)
        print("q rad         :", np.round(q, 6))
        print("q deg         :", np.round(np.degrees(q), 3))
        print("-" * 60)
        if robot_tcp is not None and robot_tcp.shape[0] >= 6:
            print("Robot tcp raw :", np.round(robot_tcp[:6], 6))
            print("Robot pos mm  :", np.round(robot_tcp[:3] * 1000.0, 2))
            print("Robot rv deg  :", np.round(np.degrees(robot_tcp[3:6]), 3))
            print("-" * 60)
        print_pose_block("Pinocchio pose:", pos, rot)
        print("-" * 60)
        print_pose_block("Pinocchio pose with extra Rz(pi) base rotation:", pos_rz_pi, rot_rz_pi)
        print("-" * 60)
        if robot_tcp is not None and robot_tcp.shape[0] >= 6:
            err = vec - robot_tcp[:6]
            err_rz_pi = vec_rz_pi - robot_tcp[:6]
            print("Error Pin - robot tcp:")
            print("  pos mm       :", np.round(err[:3] * 1000.0, 2))
            print("  rotvec rad   :", np.round(err[3:], 6))
            print("Error Pin Rz(pi) - robot tcp:")
            print("  pos mm       :", np.round(err_rz_pi[:3] * 1000.0, 2))
            print("  rotvec rad   :", np.round(err_rz_pi[3:], 6))
            print("-" * 60)
        print("UR tablet pose convention is usually X,Y,Z meters + RX,RY,RZ rotvec rad.")
        print("If robot tcp raw matches the tablet but Pinocchio does not, the issue is")
        print("a URDF/base/tool frame convention, not the socket read.")
        print("=" * 60)

    finally:
        if session is not None:
            session.close()
        print("Session closed.")


if __name__ == "__main__":
    main()

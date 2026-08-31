#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np

from dp_mujoco.kinematics.ur10_pinocchio_kinematics import UR10PinocchioKinematics
from ur10_real_robot.backends.fake_robot_backend import FakeRobotBackend


REPO_ROOT = Path(__file__).resolve().parents[2]
URDF_PATH = str(REPO_ROOT / "dp_mujoco/models/universal_robots_ur10e/ur10.urdf")


def rot_to_quat_wxyz(R: np.ndarray) -> np.ndarray:
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)

    trace = np.trace(R)

    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s

    q = np.array([w, x, y, z], dtype=np.float64)
    q /= np.linalg.norm(q)
    return q


def rot_to_rotvec(R: np.ndarray) -> np.ndarray:
    """
    Convertit une matrice de rotation en rotvec UR :
    [rx, ry, rz] = axe * angle, en radians.
    C'est le format que l'UR affiche souvent pour la pose TCP.
    """
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)

    cos_angle = (np.trace(R) - 1.0) / 2.0
    cos_angle = np.clip(cos_angle, -1.0, 1.0)

    angle = float(np.arccos(cos_angle))

    if angle < 1e-12:
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


def print_array(name: str, arr: np.ndarray) -> None:
    arr = np.asarray(arr)
    print(f"{name}:")
    print(np.array2string(arr, precision=8, separator=", "))
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--urdf",
        type=str,
        default=URDF_PATH,
        help="Path to UR10 URDF.",
    )

    parser.add_argument(
        "--q-deg",
        nargs=6,
        type=float,
        default=None,
        help="Joint positions in degrees: shoulder_pan shoulder_lift elbow wrist_1 wrist_2 wrist_3",
    )

    parser.add_argument(
        "--q-rad",
        nargs=6,
        type=float,
        default=None,
        help="Joint positions in radians.",
    )

    parser.add_argument(
        "--tcp-offset",
        nargs=3,
        type=float,
        default=[0.0, 0.0, 0.0],
        help="TCP offset from tool0 in tool0 frame, in meters.",
    )

    parser.add_argument(
        "--tablet-tcp",
        nargs=6,
        type=float,
        default=None,
        help=(
            "Optional TCP from UR tablet: x y z rx ry rz. "
            "Use meters and radians if possible."
        ),
    )

    parser.add_argument(
        "--tablet-pos-mm",
        action="store_true",
        help="Use this if tablet TCP x y z are in millimeters.",
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.q_rad is not None:
        q = np.asarray(args.q_rad, dtype=np.float64)
    elif args.q_deg is not None:
        q = np.radians(np.asarray(args.q_deg, dtype=np.float64))
    else:
        q = np.array(
            [0.0, -1.3, 1.8, -0.22, 1.57, 0.0],
            dtype=np.float64,
        )

    tcp_offset = np.asarray(args.tcp_offset, dtype=np.float64)

    kin = UR10PinocchioKinematics(
        urdf_path=args.urdf,
        ee_frame_name="tool0",
        tcp_offset_pos=tcp_offset,

        # Pour le vrai robot : pas de base_offset z=0.4.
        base_offset_pos=np.array([0.0, 0.0, 0.0], dtype=np.float64),
    )

    # Fake backend juste pour garder la même logique "robot.get_joint_positions()".
    robot = FakeRobotBackend(
        initial_q=q,
        control_dt=0.02,
        max_delta_deg=2.0,
        kinematics=kin,
    )

    robot.connect()

    q_current = robot.get_joint_positions()

    tcp_pos, tcp_rot, J = kin.forward_and_jacobian(q_current)
    tcp_quat_wxyz = rot_to_quat_wxyz(tcp_rot)
    tcp_rotvec = rot_to_rotvec(tcp_rot)

    print("\n==============================")
    print("UR10 PINOCCHIO FK TEST")
    print("==============================")
    print("URDF:", args.urdf)
    print("Frame:", "tool0")
    print("tcp_offset:", tcp_offset)
    print()

    print_array("q_current_rad", q_current)
    print_array("q_current_deg", np.degrees(q_current))

    print("==============================")
    print("PINOCCHIO TCP POSE")
    print("==============================")
    print_array("tcp_pos_m", tcp_pos)
    print_array("tcp_pos_mm", tcp_pos * 1000.0)
    print_array("tcp_rot_matrix", tcp_rot)
    print_array("tcp_quat_wxyz", tcp_quat_wxyz)
    print_array("tcp_rotvec_ur_rx_ry_rz", tcp_rotvec)

    print("==============================")
    print("UR TABLET FORMAT")
    print("==============================")
    print("Pose format usually:")
    print("p[x, y, z, rx, ry, rz]")
    print()
    print(
        "pinocchio_pose_m_rad = "
        f"p[{tcp_pos[0]:.6f}, {tcp_pos[1]:.6f}, {tcp_pos[2]:.6f}, "
        f"{tcp_rotvec[0]:.6f}, {tcp_rotvec[1]:.6f}, {tcp_rotvec[2]:.6f}]"
    )
    print(
        "pinocchio_pose_mm_rad = "
        f"p[{tcp_pos[0] * 1000.0:.3f}, {tcp_pos[1] * 1000.0:.3f}, {tcp_pos[2] * 1000.0:.3f}, "
        f"{tcp_rotvec[0]:.6f}, {tcp_rotvec[1]:.6f}, {tcp_rotvec[2]:.6f}]"
    )

    if args.tablet_tcp is not None:
        tablet_tcp = np.asarray(args.tablet_tcp, dtype=np.float64)

        tablet_pos = tablet_tcp[:3].copy()
        tablet_rotvec = tablet_tcp[3:6].copy()

        if args.tablet_pos_mm:
            tablet_pos = tablet_pos / 1000.0

        pos_diff = tcp_pos - tablet_pos
        rotvec_diff = tcp_rotvec - tablet_rotvec

        print("\n==============================")
        print("COMPARISON WITH TABLET")
        print("==============================")
        print_array("tablet_pos_m", tablet_pos)
        print_array("tablet_rotvec", tablet_rotvec)

        print_array("pos_diff_pinocchio_minus_tablet_m", pos_diff)
        print_array("pos_diff_pinocchio_minus_tablet_mm", pos_diff * 1000.0)
        print_array("rotvec_diff_pinocchio_minus_tablet", rotvec_diff)

        print("pos_error_norm_mm:", float(np.linalg.norm(pos_diff) * 1000.0))
        print("rotvec_error_norm:", float(np.linalg.norm(rotvec_diff)))

    print("\n==============================")
    print("JACOBIAN")
    print("==============================")
    print("J shape:", J.shape)
    print("cond:", float(np.linalg.cond(J @ J.T + 0.12**2 * np.eye(6))))

    robot.close()


if __name__ == "__main__":
    main()

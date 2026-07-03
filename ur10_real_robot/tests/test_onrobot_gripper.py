#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import time

from ur10_real_robot.backends.onrobot_gripper import (
    OnRobotGripperStatus,
    OnRobotRG2FTModbus,
)


def print_status(label: str, status: OnRobotGripperStatus) -> None:
    print(f"[{label}] status:", status.as_dict())
    print(f"[{label}] width : {status.width_mm:.1f} mm")
    print(
        f"[{label}] busy={status.busy} grip_det={status.grip_det} "
        f"in_zero={status.in_zero}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OnRobot RG2FT Modbus smoke test.",
    )
    parser.add_argument(
        "--gripper-ip",
        default=os.environ.get("GRIPPER_IP", "192.168.1.1"),
        help="OnRobot gripper IP.",
    )
    parser.add_argument(
        "--gripper-port",
        type=int,
        default=int(os.environ.get("GRIPPER_PORT", "502")),
        help="OnRobot gripper Modbus/TCP port.",
    )
    parser.add_argument(
        "--mode",
        choices=["read", "hold", "open", "close", "width", "sequence"],
        default="read",
        help="Test mode. read never commands the gripper.",
    )
    parser.add_argument(
        "--width-mm",
        type=float,
        default=60.0,
        help="Target width for --mode width.",
    )
    parser.add_argument(
        "--open-width-mm",
        type=float,
        default=85.0,
        help="Open width for --mode open/sequence.",
    )
    parser.add_argument(
        "--close-width-mm",
        type=float,
        default=35.0,
        help="Close width for --mode close/sequence.",
    )
    parser.add_argument(
        "--force-n",
        type=float,
        default=8.0,
        help="Command force in N. Start low for smoke tests.",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=2.0,
        help="Time to monitor status after each command.",
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=0.10,
        help="Status poll period while waiting.",
    )
    return parser


def monitor(gripper: OnRobotRG2FTModbus, duration: float, poll: float) -> None:
    start = time.monotonic()
    count = 0

    while time.monotonic() - start < duration:
        status = gripper.read_status()
        print(
            f"[{count:03d}] width={status.width_mm:5.1f} mm "
            f"busy={status.busy} grip_det={status.grip_det}"
        )
        count += 1
        time.sleep(poll)


def main() -> None:
    args = build_parser().parse_args()

    print("-------------------------------------------")
    print("ONROBOT RG2FT GRIPPER SMOKE TEST")
    print("-------------------------------------------")
    print(f"Gripper IP    : {args.gripper_ip}")
    print(f"Gripper port  : {args.gripper_port}")
    print(f"Mode          : {args.mode}")
    print(f"Force         : {args.force_n:.1f} N")
    if args.mode == "width":
        print(f"Target width  : {args.width_mm:.1f} mm")
    if args.mode in {"open", "sequence"}:
        print(f"Open width    : {args.open_width_mm:.1f} mm")
    if args.mode in {"close", "sequence"}:
        print(f"Close width   : {args.close_width_mm:.1f} mm")
    print("-------------------------------------------")

    if args.mode != "read":
        print("ATTENTION : ce test commande la vraie pince.")
        print("Garde les doigts/objets fragiles hors de la pince.")
        print("-------------------------------------------")
        answer = input("Tape YES pour lancer le test : ")
        if answer.strip() != "YES":
            print("Annulé.")
            return

    gripper = OnRobotRG2FTModbus(
        ip=args.gripper_ip,
        port=args.gripper_port,
        timeout=1.0,
    ).connect()

    try:
        print("\n[INFO] Connected.")
        print_status("before", gripper.read_status())

        if args.mode == "read":
            print("[INFO] Read-only test done. No command sent.")
            return

        if args.mode == "hold":
            print("[CMD] Hold current width.")
            gripper.hold_current_width(force_n=args.force_n)
            monitor(gripper, duration=args.wait, poll=args.poll)

        elif args.mode == "open":
            print(f"[CMD] Open to {args.open_width_mm:.1f} mm.")
            gripper.command_width(args.open_width_mm, force_n=args.force_n)
            monitor(gripper, duration=args.wait, poll=args.poll)

        elif args.mode == "close":
            print(f"[CMD] Close to {args.close_width_mm:.1f} mm.")
            gripper.command_width(args.close_width_mm, force_n=args.force_n)
            monitor(gripper, duration=args.wait, poll=args.poll)

        elif args.mode == "width":
            print(f"[CMD] Move to {args.width_mm:.1f} mm.")
            gripper.command_width(args.width_mm, force_n=args.force_n)
            monitor(gripper, duration=args.wait, poll=args.poll)

        elif args.mode == "sequence":
            print(f"[CMD] Open to {args.open_width_mm:.1f} mm.")
            gripper.command_width(args.open_width_mm, force_n=args.force_n)
            monitor(gripper, duration=args.wait, poll=args.poll)

            print(f"[CMD] Close to {args.close_width_mm:.1f} mm.")
            gripper.command_width(args.close_width_mm, force_n=args.force_n)
            monitor(gripper, duration=args.wait, poll=args.poll)

            print(f"[CMD] Re-open to {args.open_width_mm:.1f} mm.")
            gripper.command_width(args.open_width_mm, force_n=args.force_n)
            monitor(gripper, duration=args.wait, poll=args.poll)

        print_status("after", gripper.read_status())

    finally:
        gripper.close()
        print("Session closed.")


if __name__ == "__main__":
    main()

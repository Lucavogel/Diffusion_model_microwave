#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import time

import numpy as np

from ur10_real_robot.backends.ur10_speedj_backend import UR10SpeedjBackend
from ur10_real_robot.safety.watchdog import ControlLoopWatchdog


ROBOT_IP = os.environ.get("ROBOT_IP", "192.168.2.100")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test the UR10SpeedjBackend used by real teleop."
    )
    parser.add_argument("--robot-ip", default=ROBOT_IP)
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--control-hz", type=float, default=50.0)
    parser.add_argument("--max-joint-vel", type=float, default=0.08)
    parser.add_argument("--speedj-a", type=float, default=0.06)
    parser.add_argument("--socket-timeout", type=float, default=1.0)
    parser.add_argument("--stop-deceleration", type=float, default=1.0)
    parser.add_argument(
        "--enable-motion",
        action="store_true",
        help="Allow sending commands to the real robot.",
    )
    parser.add_argument(
        "--send-zero-speedj",
        action="store_true",
        help="Send speedj([0..0]) every cycle. Requires --enable-motion.",
    )
    parser.add_argument("--yes", action="store_true", help="Skip YES prompt.")
    return parser


def require_yes(args: argparse.Namespace, q_start: np.ndarray) -> None:
    print("-------------------------------------------")
    print("UR10 SPEEDJ BACKEND SMOKE TEST")
    print("-------------------------------------------")
    print(f"Robot IP          : {args.robot_ip}")
    print(f"Duration          : {args.duration:.2f} s")
    print(f"Control Hz        : {args.control_hz:.2f}")
    print(f"Motion enabled    : {args.enable_motion}")
    print(f"Send zero speedj  : {args.send_zero_speedj}")
    print(f"speedj a          : {args.speedj_a:.3f}")
    print(f"max joint vel     : {args.max_joint_vel:.3f} rad/s")
    print("Initial q deg     :", np.round(np.degrees(q_start), 3))
    print("-------------------------------------------")

    if args.send_zero_speedj and not args.enable_motion:
        raise ValueError("--send-zero-speedj requires --enable-motion")

    if args.enable_motion:
        print("ATTENTION : ce test peut envoyer speedj([0..0]) au vrai robot.")
        print("Le robot doit rester immobile. Main proche de l'arret d'urgence.")
        print("-------------------------------------------")

    if args.yes:
        return

    answer = input("Tape YES pour lancer ce test : ")
    if answer.strip() != "YES":
        raise RuntimeError("Test annule par l'utilisateur.")


def main() -> None:
    args = build_parser().parse_args()

    if args.duration <= 0.0:
        raise ValueError("--duration must be positive")
    if args.control_hz <= 0.0:
        raise ValueError("--control-hz must be positive")

    control_dt = 1.0 / float(args.control_hz)
    robot = UR10SpeedjBackend(
        robot_ip=args.robot_ip,
        control_dt=control_dt,
        speedj_a=args.speedj_a,
        speedj_t=control_dt,
        stop_deceleration=args.stop_deceleration,
        max_joint_vel=args.max_joint_vel,
        socket_timeout=args.socket_timeout,
        enable_motion=args.enable_motion,
    )

    loop_watchdog = ControlLoopWatchdog(
        expected_dt=control_dt,
        warn_factor=2.0,
        stop_factor=5.0,
    )

    timestamps: list[float] = []
    q_samples: list[np.ndarray] = []
    qvel_samples: list[np.ndarray] = []

    try:
        print("[INFO] Connecting UR10SpeedjBackend...")
        robot.connect()

        q_start = robot.get_joint_positions()
        require_yes(args, q_start)

        print("\n[INFO] Starting backend smoke test...")
        start_t = time.perf_counter()
        last_loop_t = start_t
        next_t = start_t
        loop_count = 0

        while True:
            now = time.perf_counter()
            elapsed = now - start_t
            if elapsed >= args.duration:
                break

            real_dt = now - last_loop_t
            if real_dt <= 1e-6 or real_dt > 0.5:
                real_dt = control_dt
            last_loop_t = now

            loop_status = loop_watchdog.check(real_dt)
            if loop_status.should_stop:
                raise RuntimeError(loop_status.reason)

            q = robot.get_joint_positions()
            qvel = robot.get_joint_velocities()

            if args.send_zero_speedj:
                robot.apply_joint_velocity(np.zeros(6, dtype=np.float64))

            timestamps.append(now)
            q_samples.append(q.copy())
            qvel_samples.append(qvel.copy())

            if loop_count % 25 == 0:
                drift = float(np.max(np.abs(q - q_start)))
                msg = (
                    f"[{loop_count:04d}] elapsed={elapsed:.2f}s "
                    f"q_drift={np.degrees(drift):.5f} deg "
                    f"max_qvel={float(np.max(np.abs(qvel))):.5f} rad/s"
                )
                if loop_status.status == "warn":
                    msg += f" WARN {loop_status.reason}"
                print(msg)

            loop_count += 1
            next_t += control_dt
            sleep_t = next_t - time.perf_counter()
            if sleep_t > 0.0:
                time.sleep(sleep_t)
            else:
                next_t = time.perf_counter()

        print("\n[INFO] Sending stop...")
        robot.stop()

        loop_deltas = np.diff(timestamps)
        freq = 1.0 / float(np.mean(loop_deltas)) if len(loop_deltas) else 0.0
        q_arr = np.asarray(q_samples, dtype=float) if q_samples else np.empty((0, 6))
        qvel_arr = np.asarray(qvel_samples, dtype=float) if qvel_samples else np.empty((0, 6))

        print("\n" + "=" * 50)
        print("UR10 SPEEDJ BACKEND TEST RESULTS")
        print("=" * 50)
        print(f"Total cycles:       {len(timestamps)}")
        print(f"Loop frequency:     {freq:.2f} Hz")
        if len(q_arr):
            max_drift = np.max(np.abs(q_arr - q_start), axis=0)
            span = np.ptp(q_arr, axis=0)
            print(f"Max q drift deg:    {float(np.degrees(np.max(max_drift))):.5f}")
            print("Joint span deg:     ", np.round(np.degrees(span), 5))
        if len(qvel_arr):
            print(f"Max qvel rad/s:     {float(np.max(np.abs(qvel_arr))):.5f}")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        try:
            robot.stop()
        except Exception:
            pass

    finally:
        robot.close()
        print("Session closed.")


if __name__ == "__main__":
    main()

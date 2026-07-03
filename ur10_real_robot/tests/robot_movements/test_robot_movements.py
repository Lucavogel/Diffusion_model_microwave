#!/usr/bin/env python3


# ROBOT_IP=192.168.2.100 python3 -m ur10_real_robot.tests.test_robot_movements \
#   --test line \
#   --line-axis x \
#   --line-distance 0.10 \
#   --duration 14 \
#   --tcp-offset 0 0 0 \
#   --cart-max-joint-vel 0.12 \
#   --cart-kp-pos 0.55 \
#   --cart-alpha-dq 0.04 \
#   --speedj-a 0.06

# --control-hz 50
# --tcp-offset 0 0 0
# --cart-kp-pos 0.55
# --cart-alpha-dq 0.04
# --speedj-a 0.06

from __future__ import annotations

import argparse
import math
import os
import time
from dataclasses import dataclass

import numpy as np

from ur10_real_robot.backends import UR10RealtimeSession
from ur10_real_robot.safety.watchdog import ControlLoopWatchdog


ROBOT_IP = os.environ.get("ROBOT_IP", "192.168.2.100")
URDF_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "dp_mujoco/models/universal_robots_ur10e/ur10_d455_support_rg2ft_fixed_gripper.urdf"
)


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


@dataclass
class RunStats:
    loop_timestamps: list[float]
    max_abs_q_error: list[float]
    max_abs_q_step: list[float]
    q_actual: list[np.ndarray]
    q_target: list[np.ndarray]
    tcp_actual: list[np.ndarray]
    tcp_target: list[np.ndarray]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Progressive real UR10 movement smoke tests over socket/servoj."
    )

    parser.add_argument("--robot-ip", default=ROBOT_IP)
    parser.add_argument(
        "--test",
        choices=["hold", "joint", "all-joints", "line", "circle", "movej-step", "speedj-joint"],
        default="hold",
    )
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--control-hz", type=float, default=50.0)
    parser.add_argument("--servoj-t", type=float, default=None)
    parser.add_argument("--servoj-a", type=float, default=0.5)
    parser.add_argument("--servoj-v", type=float, default=0.2)
    parser.add_argument("--socket-timeout", type=float, default=1.0)
    parser.add_argument("--stop-deceleration", type=float, default=1.0)
    parser.add_argument("--yes", action="store_true", help="Skip YES prompt.")

    parser.add_argument(
        "--joint-index",
        type=int,
        default=6,
        help="Joint index for --test joint, user-facing 1..6.",
    )
    parser.add_argument(
        "--amp-deg",
        type=float,
        default=1.0,
        help="Amplitude in degrees for --test joint.",
    )
    parser.add_argument(
        "--movej-a",
        type=float,
        default=0.15,
        help="movej acceleration for --test movej-step.",
    )
    parser.add_argument(
        "--movej-v",
        type=float,
        default=0.05,
        help="movej velocity for --test movej-step.",
    )
    parser.add_argument(
        "--movej-settle",
        type=float,
        default=3.0,
        help="Seconds to monitor after sending movej-step.",
    )
    parser.add_argument(
        "--speedj-max-vel-deg",
        type=float,
        default=1.0,
        help="Peak joint velocity in deg/s for --test speedj-joint.",
    )
    parser.add_argument(
        "--speedj-a",
        type=float,
        default=0.10,
        help="speedj acceleration for --test speedj-joint.",
    )
    parser.add_argument(
        "--all-amps-deg",
        nargs=6,
        type=float,
        default=[0.3, 0.3, 0.3, 1.0, 1.0, 1.0],
        help="Six joint amplitudes in degrees for --test all-joints.",
    )

    parser.add_argument("--urdf", default=URDF_PATH)
    parser.add_argument("--tcp-offset", nargs=3, type=float, default=[0.0, 0.0, 0.0])
    parser.add_argument(
        "--base-rz-deg",
        type=float,
        default=180.0,
        help="Real UR controller base frame correction around Z, in degrees.",
    )
    parser.add_argument("--line-axis", choices=["x", "y", "z"], default="x")
    parser.add_argument("--line-distance", type=float, default=0.02)
    parser.add_argument("--circle-radius", type=float, default=0.01)
    parser.add_argument("--cart-kp-pos", type=float, default=0.35)
    parser.add_argument("--cart-damping", type=float, default=0.12)
    parser.add_argument("--cart-max-joint-vel", type=float, default=0.03)
    parser.add_argument("--cart-alpha-dq", type=float, default=0.08)
    parser.add_argument(
        "--cart-settle",
        type=float,
        default=0.0,
        help="Extra seconds after cartesian trajectory to converge to final pose.",
    )
    parser.add_argument(
        "--cart-settle-threshold",
        type=float,
        default=0.003,
        help="Stop settle phase when TCP error is below this value in meters.",
    )

    parser.add_argument("--loop-watchdog-warn-factor", type=float, default=2.0)
    parser.add_argument("--loop-watchdog-stop-factor", type=float, default=5.0)

    return parser


def require_yes(args: argparse.Namespace, q_start: np.ndarray) -> None:
    print("-------------------------------------------")
    print("UR10 CB2 - REAL MOVEMENT SMOKE TEST")
    print("-------------------------------------------")
    print(f"Robot IP      : {args.robot_ip}")
    print(f"Test          : {args.test}")
    print(f"Duration      : {args.duration:.2f} s")
    print(f"Control Hz    : {args.control_hz:.2f}")
    print(f"servoj t      : {args.servoj_t:.4f} s")
    print(f"servoj a/v    : {args.servoj_a:.3f} / {args.servoj_v:.3f}")
    print("Initial q deg :", np.round(np.degrees(q_start), 3))
    print("-------------------------------------------")
    print("ATTENTION : ce script fait bouger le vrai robot sauf en mode hold.")
    print("Speed slider tablette recommandé : 5% ou 10%.")
    print("Workspace dégagé, main proche de l'arrêt d'urgence.")
    print("-------------------------------------------")

    if args.test == "joint":
        print(
            f"Joint movement : J{args.joint_index}, "
            f"+/- {args.amp_deg:.3f} deg sinus."
        )
    elif args.test == "speedj-joint":
        print(
            f"speedj joint   : J{args.joint_index}, "
            f"peak velocity {args.speedj_max_vel_deg:.3f} deg/s."
        )
    elif args.test == "movej-step":
        print(
            f"movej step     : J{args.joint_index}, "
            f"+ {args.amp_deg:.3f} deg, a={args.movej_a:.3f}, v={args.movej_v:.3f}."
        )
    elif args.test == "all-joints":
        print("All-joints amps deg:", np.asarray(args.all_amps_deg, dtype=float))
    elif args.test == "line":
        print(
            f"TCP line       : axis {args.line_axis}, "
            f"distance {args.line_distance * 100.0:.1f} cm, orientation fixed."
        )
    elif args.test == "circle":
        print(
            f"TCP circle     : radius {args.circle_radius * 100.0:.1f} cm, "
            "XY plane, orientation fixed."
        )
    else:
        print("Hold position  : q_target = q_current.")

    print("-------------------------------------------")
    if args.test in {"line", "circle"} and args.cart_settle > 0.0:
        print(
            f"Cartesian settle: up to {args.cart_settle:.2f} s, "
            f"threshold {args.cart_settle_threshold * 100.0:.2f} cm."
        )
        print("-------------------------------------------")

    if args.yes:
        return

    answer = input("Tape YES pour lancer ce test : ")
    if answer.strip() != "YES":
        raise RuntimeError("Test annulé par l'utilisateur.")


def smooth_sine(elapsed: float, duration: float) -> float:
    phase = np.clip(elapsed / duration, 0.0, 1.0)
    return float(np.sin(2.0 * np.pi * phase))


def make_joint_target(args: argparse.Namespace, q_start: np.ndarray, elapsed: float) -> np.ndarray:
    q_target = q_start.copy()

    if args.test == "hold":
        return q_target

    s = smooth_sine(elapsed, args.duration)

    if args.test == "joint":
        idx = int(args.joint_index) - 1
        if idx < 0 or idx >= 6:
            raise ValueError("--joint-index must be in 1..6")
        q_target[idx] += np.radians(float(args.amp_deg)) * s
        return q_target

    if args.test == "all-joints":
        amps = np.radians(np.asarray(args.all_amps_deg, dtype=np.float64).reshape(6))
        q_target += amps * s
        return q_target

    raise ValueError(f"Joint target not available for test {args.test}")


def make_cartesian_servo(args: argparse.Namespace, q_start: np.ndarray):
    from dp_mujoco.policy_exec.servo_controller_pinocchio import PinocchioServoController

    servo = PinocchioServoController(
        urdf_path=args.urdf,
        home_q=q_start,
        ee_frame_name="tool0",
        tcp_offset_pos=np.asarray(args.tcp_offset, dtype=np.float64),
        base_offset_pos=np.zeros(3, dtype=np.float64),
        base_offset_rot=rotz(math.radians(args.base_rz_deg)),
        kp_pos=args.cart_kp_pos,
        kp_rot=0.0,
        damping=args.cart_damping,
        max_joint_vel=args.cart_max_joint_vel,
        alpha_dq=args.cart_alpha_dq,
    )
    servo.reset(q_start)
    return servo


def make_cartesian_target(
    args: argparse.Namespace,
    start_pos: np.ndarray,
    start_rot: np.ndarray,
    elapsed: float,
) -> tuple[np.ndarray, np.ndarray]:
    phase = np.clip(elapsed / args.duration, 0.0, 1.0)

    if args.test == "line":
        axis_map = {
            "x": np.array([1.0, 0.0, 0.0], dtype=np.float64),
            "y": np.array([0.0, 1.0, 0.0], dtype=np.float64),
            "z": np.array([0.0, 0.0, 1.0], dtype=np.float64),
        }
        # Smooth out-and-back: start -> distance -> start.
        offset_scale = 0.5 - 0.5 * np.cos(2.0 * np.pi * phase)
        target_pos = start_pos + axis_map[args.line_axis] * args.line_distance * offset_scale
        return target_pos, start_rot

    if args.test == "circle":
        angle = 2.0 * np.pi * phase
        target_pos = start_pos + args.circle_radius * np.array(
            [np.cos(angle) - 1.0, np.sin(angle), 0.0],
            dtype=np.float64,
        )
        return target_pos, start_rot

    raise ValueError(f"Cartesian target not available for test {args.test}")


def run_motion(args: argparse.Namespace, session: UR10RealtimeSession, q_start: np.ndarray) -> RunStats:
    control_dt = 1.0 / float(args.control_hz)
    loop_watchdog = ControlLoopWatchdog(
        expected_dt=control_dt,
        warn_factor=args.loop_watchdog_warn_factor,
        stop_factor=args.loop_watchdog_stop_factor,
    )

    cartesian = args.test in {"line", "circle"}
    servo = None
    start_pos = None
    start_rot = None

    if cartesian:
        servo = make_cartesian_servo(args, q_start)
        start_pos, start_rot, _ = servo.kin.forward_and_jacobian(q_start)
        print("Start TCP pos :", np.round(start_pos, 5))
        print("TCP offset    :", np.asarray(args.tcp_offset, dtype=float))

    stats = RunStats(
        loop_timestamps=[],
        max_abs_q_error=[],
        max_abs_q_step=[],
        q_actual=[],
        q_target=[],
        tcp_actual=[],
        tcp_target=[],
    )

    start_t = time.perf_counter()
    last_loop_t = start_t
    next_t = start_t
    last_q_target = q_start.copy()
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

        data = session.read(wait=True)
        q_actual = np.asarray(data["qActual"], dtype=float).reshape(6)

        if cartesian:
            target_pos, target_rot = make_cartesian_target(
                args,
                start_pos,
                start_rot,
                elapsed,
            )
            q_target, info = servo.compute(
                q_current=q_actual,
                target_pos=target_pos,
                target_rot=target_rot,
                dt=real_dt,
            )
            qd_cmd = np.asarray(info["dq"], dtype=np.float64).reshape(6)
        else:
            q_target = make_joint_target(args, q_start, elapsed)
            info = None
            qd_cmd = None

        q_step = float(np.max(np.abs(q_target - last_q_target)))
        q_error = float(np.max(np.abs(q_actual - q_target)))

        if cartesian:
            session.send_speedj(qd_cmd, a=args.speedj_a, t=args.servoj_t)
        else:
            session.send_servoj(
                q_target,
                t=args.servoj_t,
                a=args.servoj_a,
                v=args.servoj_v,
            )

        stats.loop_timestamps.append(now)
        stats.max_abs_q_error.append(q_error)
        stats.max_abs_q_step.append(q_step)
        stats.q_actual.append(q_actual.copy())
        stats.q_target.append(q_target.copy())
        if info is not None:
            stats.tcp_actual.append(np.asarray(info["current_pos"], dtype=float).copy())
            stats.tcp_target.append(np.asarray(info["target_pos"], dtype=float).copy())
        last_q_target = q_target.copy()

        if loop_count % 25 == 0:
            msg = (
                f"[{loop_count:04d}] elapsed={elapsed:.2f}s "
                f"q_err={np.degrees(q_error):.4f} deg "
                f"q_step={np.degrees(q_step):.4f} deg"
            )
            if info is not None:
                msg += f" pos_err={np.linalg.norm(info['pos_err']):.4f} m"
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

    if cartesian and float(args.cart_settle) > 0.0:
        settle_start_t = time.perf_counter()
        print(
            f"[INFO] Cartesian settle phase: final target for "
            f"{args.cart_settle:.2f}s max."
        )

        while True:
            now = time.perf_counter()
            settle_elapsed = now - settle_start_t
            if settle_elapsed >= float(args.cart_settle):
                break

            real_dt = now - last_loop_t
            if real_dt <= 1e-6 or real_dt > 0.5:
                real_dt = control_dt
            last_loop_t = now

            loop_status = loop_watchdog.check(real_dt)
            if loop_status.should_stop:
                raise RuntimeError(loop_status.reason)

            data = session.read(wait=True)
            q_actual = np.asarray(data["qActual"], dtype=float).reshape(6)

            target_pos, target_rot = make_cartesian_target(
                args,
                start_pos,
                start_rot,
                args.duration,
            )
            q_target, info = servo.compute(
                q_current=q_actual,
                target_pos=target_pos,
                target_rot=target_rot,
                dt=real_dt,
            )
            qd_cmd = np.asarray(info["dq"], dtype=np.float64).reshape(6)
            pos_err_norm = float(np.linalg.norm(info["pos_err"]))

            q_step = float(np.max(np.abs(q_target - last_q_target)))
            q_error = float(np.max(np.abs(q_actual - q_target)))

            session.send_speedj(qd_cmd, a=args.speedj_a, t=args.servoj_t)

            stats.loop_timestamps.append(now)
            stats.max_abs_q_error.append(q_error)
            stats.max_abs_q_step.append(q_step)
            stats.q_actual.append(q_actual.copy())
            stats.q_target.append(q_target.copy())
            stats.tcp_actual.append(np.asarray(info["current_pos"], dtype=float).copy())
            stats.tcp_target.append(np.asarray(info["target_pos"], dtype=float).copy())
            last_q_target = q_target.copy()

            if loop_count % 25 == 0:
                msg = (
                    f"[settle {loop_count:04d}] elapsed={settle_elapsed:.2f}s "
                    f"q_err={np.degrees(q_error):.4f} deg "
                    f"q_step={np.degrees(q_step):.4f} deg "
                    f"pos_err={pos_err_norm:.4f} m"
                )
                if loop_status.status == "warn":
                    msg += f" WARN {loop_status.reason}"
                print(msg)

            loop_count += 1

            if pos_err_norm <= float(args.cart_settle_threshold):
                print(
                    f"[INFO] Cartesian settle reached "
                    f"{pos_err_norm * 100.0:.2f} cm TCP error."
                )
                break

            next_t += control_dt
            sleep_t = next_t - time.perf_counter()
            if sleep_t > 0.0:
                time.sleep(sleep_t)
            else:
                next_t = time.perf_counter()

    return stats


def run_movej_step(
    args: argparse.Namespace,
    session: UR10RealtimeSession,
    q_start: np.ndarray,
) -> RunStats:
    idx = int(args.joint_index) - 1
    if idx < 0 or idx >= 6:
        raise ValueError("--joint-index must be in 1..6")

    q_target = q_start.copy()
    q_target[idx] += np.radians(float(args.amp_deg))

    stats = RunStats(
        loop_timestamps=[],
        max_abs_q_error=[],
        max_abs_q_step=[],
        q_actual=[],
        q_target=[],
        tcp_actual=[],
        tcp_target=[],
    )

    print("[INFO] Sending one movej command...")
    print("q_start deg :", np.round(np.degrees(q_start), 4))
    print("q_target deg:", np.round(np.degrees(q_target), 4))
    session.send_movej(q_target, a=args.movej_a, v=args.movej_v)

    start_t = time.perf_counter()
    while time.perf_counter() - start_t < float(args.movej_settle):
        now = time.perf_counter()
        data = session.read(wait=True)
        q_actual = np.asarray(data["qActual"], dtype=float).reshape(6)
        q_error = float(np.max(np.abs(q_actual - q_target)))

        stats.loop_timestamps.append(now)
        stats.max_abs_q_error.append(q_error)
        stats.max_abs_q_step.append(float(np.max(np.abs(q_target - q_start))))
        stats.q_actual.append(q_actual.copy())
        stats.q_target.append(q_target.copy())

        if len(stats.loop_timestamps) % 25 == 0:
            print(
                f"[movej] q_actual J{idx + 1}="
                f"{np.degrees(q_actual[idx]):.4f} deg | "
                f"target={np.degrees(q_target[idx]):.4f} deg | "
                f"err={np.degrees(q_target[idx] - q_actual[idx]):.4f} deg"
            )

    return stats


def run_speedj_joint(
    args: argparse.Namespace,
    session: UR10RealtimeSession,
    q_start: np.ndarray,
) -> RunStats:
    idx = int(args.joint_index) - 1
    if idx < 0 or idx >= 6:
        raise ValueError("--joint-index must be in 1..6")

    control_dt = 1.0 / float(args.control_hz)
    loop_watchdog = ControlLoopWatchdog(
        expected_dt=control_dt,
        warn_factor=args.loop_watchdog_warn_factor,
        stop_factor=args.loop_watchdog_stop_factor,
    )

    stats = RunStats(
        loop_timestamps=[],
        max_abs_q_error=[],
        max_abs_q_step=[],
        q_actual=[],
        q_target=[],
        tcp_actual=[],
        tcp_target=[],
    )

    max_vel = np.radians(float(args.speedj_max_vel_deg))
    start_t = time.perf_counter()
    last_loop_t = start_t
    next_t = start_t
    q_integrated_target = q_start.copy()

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

        phase = np.clip(elapsed / args.duration, 0.0, 1.0)
        qd = np.zeros(6, dtype=np.float64)
        qd[idx] = max_vel * np.sin(2.0 * np.pi * phase)
        q_integrated_target = q_integrated_target + qd * real_dt

        data = session.read(wait=True)
        q_actual = np.asarray(data["qActual"], dtype=float).reshape(6)
        q_error = float(np.max(np.abs(q_actual - q_integrated_target)))

        session.send_speedj(qd, a=args.speedj_a, t=args.servoj_t)

        stats.loop_timestamps.append(now)
        stats.max_abs_q_error.append(q_error)
        stats.max_abs_q_step.append(float(np.max(np.abs(qd * real_dt))))
        stats.q_actual.append(q_actual.copy())
        stats.q_target.append(q_integrated_target.copy())

        if len(stats.loop_timestamps) % 25 == 0:
            print(
                f"[speedj] J{idx + 1} actual={np.degrees(q_actual[idx]):.4f} deg | "
                f"vel_cmd={np.degrees(qd[idx]):.4f} deg/s"
            )

        next_t += control_dt
        sleep_t = next_t - time.perf_counter()
        if sleep_t > 0.0:
            time.sleep(sleep_t)
        else:
            next_t = time.perf_counter()

    session.stopj(args.stop_deceleration)
    return stats


def print_stats(stats: RunStats) -> None:
    loop_deltas = np.diff(stats.loop_timestamps)
    freq = 1.0 / float(np.mean(loop_deltas)) if len(loop_deltas) else 0.0

    q_errors = np.asarray(stats.max_abs_q_error, dtype=float)
    q_steps = np.asarray(stats.max_abs_q_step, dtype=float)

    print("\n" + "=" * 50)
    print("ROBOT MOVEMENT TEST RESULTS")
    print("=" * 50)
    print(f"Total cycles:        {len(stats.loop_timestamps)}")
    print(f"Loop frequency:      {freq:.2f} Hz")
    if len(q_errors):
        print(f"Max q error:         {float(np.degrees(np.max(q_errors))):.5f} deg")
        print(f"Mean q error:        {float(np.degrees(np.mean(q_errors))):.5f} deg")
    if len(q_steps):
        print(f"Max q target step:   {float(np.degrees(np.max(q_steps))):.5f} deg")

    if stats.q_actual:
        q_actual = np.asarray(stats.q_actual, dtype=float)
        q_target = np.asarray(stats.q_target, dtype=float)
        actual_span = np.ptp(q_actual, axis=0)
        target_span = np.ptp(q_target, axis=0)
        print("-" * 50)
        print("Actual q span deg:   ", np.round(np.degrees(actual_span), 5))
        print("Target q span deg:   ", np.round(np.degrees(target_span), 5))

    if stats.tcp_actual:
        tcp_actual = np.asarray(stats.tcp_actual, dtype=float)
        tcp_target = np.asarray(stats.tcp_target, dtype=float)
        actual_span = np.ptp(tcp_actual, axis=0)
        target_span = np.ptp(tcp_target, axis=0)
        print("-" * 50)
        print("Actual TCP span m:   ", np.round(actual_span, 5))
        print("Target TCP span m:   ", np.round(target_span, 5))
        print("Actual TCP span cm:  ", np.round(actual_span * 100.0, 3))
        print("Target TCP span cm:  ", np.round(target_span * 100.0, 3))
    print("=" * 50)


def main() -> None:
    args = build_parser().parse_args()

    if args.control_hz <= 0.0:
        raise ValueError("--control-hz must be positive")
    if args.duration <= 0.0:
        raise ValueError("--duration must be positive")
    if args.servoj_t is None:
        args.servoj_t = 1.0 / float(args.control_hz)

    session = None

    try:
        print("[INFO] Connecting to robot...")
        session = UR10RealtimeSession(
            robot_ip=args.robot_ip,
            socket_timeout=args.socket_timeout,
        ).connect()

        q_start = session.current_q()
        require_yes(args, q_start)

        print("\n[INFO] Starting movement test...")
        if args.test == "movej-step":
            stats = run_movej_step(args, session, q_start)
        elif args.test == "speedj-joint":
            stats = run_speedj_joint(args, session, q_start)
        else:
            stats = run_motion(args, session, q_start)

        print("\n[INFO] Sending stopj...")
        session.stopj(args.stop_deceleration)
        print_stats(stats)

    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        if session is not None:
            try:
                session.stopj(args.stop_deceleration)
            except Exception:
                pass

    except Exception as exc:
        print("\n[ERROR]", exc)
        if session is not None:
            try:
                session.stopj(args.stop_deceleration)
            except Exception:
                pass

    finally:
        if session is not None:
            try:
                session.close()
            except Exception:
                pass
        print("Session closed.")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import numpy as np
import torch

from dp_mujoco.policy_exec.action_decoder import extract_action_sequence
from dp_mujoco.policy_exec.policy_loader import infer_image_shape, load_policy
from dp_mujoco.policy_exec.servo_controller_pinocchio import (
    PinocchioServoController,
    orientation_error,
)
from dp_mujoco.policy_exec.trajectory_executor import TrajectoryExecutor

from ur10_real_robot.backends.fake_robot_backend import FakeRobotBackend
from ur10_real_robot.backends.onrobot_gripper import AsyncOnRobotGripperController
from ur10_real_robot.backends.ur10_speedj_backend import UR10SpeedjBackend
from ur10_real_robot.camera import DualCameraRig
from ur10_real_robot.policy_exec.real_observation_builder import RealObservationBuilder
from ur10_real_robot.policy_exec.target_smoother import PolicyTargetSmoother
from ur10_real_robot.safety.safety_config import SafetyConfig, SafetyChecker
from ur10_real_robot.safety.watchdog import ControlLoopWatchdog


ROOT_DIR = Path(__file__).resolve().parents[2]
URDF_PATH = (
    ROOT_DIR
    / "dp_mujoco"
    / "models"
    / "universal_robots_ur10e"
    / "ur10_d455_support_rg2ft_fixed_gripper.urdf"
)
CAMERA_CONFIG_PATH = (
    ROOT_DIR
    / "ur10_real_robot"
    / "camera"
    / "config"
    / "d435i_config.json"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a diffusion policy on the real UR10 stack.",
    )

    parser.add_argument("--checkpoint", required=True, help="Path to trained .ckpt")
    parser.add_argument("--device", default="cpu", help="torch device: cpu or cuda:0")

    parser.add_argument("--backend", choices=["fake", "speedj"], default="fake")
    parser.add_argument("--robot-ip", default="192.168.2.100")
    parser.add_argument("--enable-motion", action="store_true")

    parser.add_argument("--camera-mode", choices=["fake", "realsense"], default="fake")
    parser.add_argument("--top-serial", default=None)
    parser.add_argument("--wrist-serial", default=None)
    parser.add_argument("--camera-config", default=str(CAMERA_CONFIG_PATH))
    parser.add_argument("--no-advanced-config", action="store_true")
    parser.add_argument("--capture-width", type=int, default=640)
    parser.add_argument("--capture-height", type=int, default=480)
    parser.add_argument("--camera-fps", type=int, default=30)
    parser.add_argument("--dataset-width", type=int, default=320)
    parser.add_argument("--dataset-height", type=int, default=240)

    parser.add_argument("--urdf", default=str(URDF_PATH))
    parser.add_argument("--tcp-offset", nargs=3, type=float, default=[0.0, 0.0, 0.022])
    parser.add_argument("--base-rz-deg", type=float, default=180.0)

    parser.add_argument("--control-hz", type=float, default=50.0)
    parser.add_argument("--policy-hz", type=float, default=5.0)
    parser.add_argument("--exec-horizon", type=int, default=None)

    parser.add_argument("--kp-pos", type=float, default=0.35)
    parser.add_argument("--kp-rot", type=float, default=0.0)
    parser.add_argument("--damping", type=float, default=0.12)
    parser.add_argument("--max-joint-vel", type=float, default=0.08)
    parser.add_argument("--alpha-dq", type=float, default=0.04)
    parser.add_argument("--speedj-a", type=float, default=0.05)
    parser.add_argument("--speedj-t", type=float, default=None)
    parser.add_argument("--stop-deceleration", type=float, default=1.0)
    parser.add_argument("--socket-timeout", type=float, default=1.0)

    parser.add_argument("--ignore-action-orientation", action="store_true")
    parser.add_argument("--max-target-speed", type=float, default=0.05)
    parser.add_argument("--smooth-alpha-pos", type=float, default=0.25)
    parser.add_argument("--smooth-alpha-rot", type=float, default=0.15)
    parser.add_argument("--smooth-alpha-gripper", type=float, default=0.35)

    parser.add_argument("--max-pos-error-stop", type=float, default=0.12)
    parser.add_argument("--max-rot-error-stop", type=float, default=0.50)
    parser.add_argument("--loop-watchdog-warn-factor", type=float, default=2.0)
    parser.add_argument("--loop-watchdog-stop-factor", type=float, default=5.0)
    parser.add_argument("--disable-loop-watchdog", action="store_true")

    parser.add_argument("--gripper-enable", action="store_true")
    parser.add_argument("--gripper-motion-enable", action="store_true")
    parser.add_argument("--gripper-ip", default="192.168.1.1")
    parser.add_argument("--gripper-port", type=int, default=502)
    parser.add_argument("--gripper-open-width-mm", type=float, default=85.0)
    parser.add_argument("--gripper-close-width-mm", type=float, default=35.0)
    parser.add_argument("--gripper-force-n", type=float, default=8.0)
    parser.add_argument("--gripper-command-period", type=float, default=0.10)
    parser.add_argument("--gripper-deadband-mm", type=float, default=1.0)

    parser.add_argument("--print-period", type=float, default=0.5)
    parser.add_argument("--max-run-time", type=float, default=30.0)
    parser.add_argument("--verbose-plan", action="store_true")
    parser.add_argument("--debug-timing", action="store_true")

    return parser


def make_robot(args: argparse.Namespace, control_dt: float):
    if args.backend == "fake":
        return FakeRobotBackend(
            control_dt=control_dt,
            max_delta_deg=2.0,
            kinematics=None,
            verbose=False,
        )

    if args.backend == "speedj":
        return UR10SpeedjBackend(
            robot_ip=args.robot_ip,
            control_dt=control_dt,
            speedj_a=args.speedj_a,
            speedj_t=args.speedj_t,
            stop_deceleration=args.stop_deceleration,
            max_joint_vel=args.max_joint_vel,
            socket_timeout=args.socket_timeout,
            enable_motion=args.enable_motion,
            kinematics=None,
        )

    raise ValueError(f"Unknown backend: {args.backend}")


def main() -> None:
    args = build_parser().parse_args()

    if args.control_hz <= 0.0:
        raise ValueError("--control-hz must be positive.")
    if args.policy_hz <= 0.0:
        raise ValueError("--policy-hz must be positive.")

    if args.backend == "speedj" and args.enable_motion:
        print("-------------------------------------------")
        print("ATTENTION: REAL DIFFUSION EXECUTION")
        print("-------------------------------------------")
        print("This can move the real robot from policy outputs.")
        print("Start with speed slider low and hand near E-stop.")
        print("-------------------------------------------")
        answer = input("Tape YES pour lancer avec mouvement réel : ")
        if answer.strip() != "YES":
            print("Annulé.")
            return

    device = torch.device(args.device)
    control_dt = 1.0 / float(args.control_hz)

    print("[INFO] Loading policy...")
    policy, cfg = load_policy(args.checkpoint, device)
    _, obs_h, obs_w = infer_image_shape(cfg)

    n_obs_steps = int(cfg.n_obs_steps)
    pred_horizon = int(cfg.horizon)
    exec_horizon = (
        int(args.exec_horizon)
        if args.exec_horizon is not None
        else int(cfg.n_action_steps)
    )
    if not (1 <= exec_horizon <= pred_horizon):
        raise ValueError(f"exec_horizon must be in [1, {pred_horizon}], got {exec_horizon}")

    robot = make_robot(args, control_dt)
    cameras = DualCameraRig(
        top_serial=args.top_serial,
        wrist_serial=args.wrist_serial,
        config_path=args.camera_config,
        capture_width=args.capture_width,
        capture_height=args.capture_height,
        fps=args.camera_fps,
        dataset_size=(args.dataset_width, args.dataset_height),
        display_size=(640, 480),
        fake=args.camera_mode == "fake",
        apply_advanced_config=not args.no_advanced_config,
    )

    gripper = None
    safety_stop_triggered = False
    safety_stop_reason = ""

    loop_watchdog = ControlLoopWatchdog(
        expected_dt=control_dt,
        warn_factor=args.loop_watchdog_warn_factor,
        stop_factor=args.loop_watchdog_stop_factor,
        enabled=not args.disable_loop_watchdog,
    )

    try:
        robot.connect()
        cameras.start()

        if args.gripper_enable:
            gripper = AsyncOnRobotGripperController(
                ip=args.gripper_ip,
                port=args.gripper_port,
                timeout=1.0,
                open_width_mm=args.gripper_open_width_mm,
                close_width_mm=args.gripper_close_width_mm,
                force_n=args.gripper_force_n,
                command_period=args.gripper_command_period,
                command_deadband_mm=args.gripper_deadband_mm,
                control_mode="width",
                enabled=args.gripper_motion_enable,
            )
            gripper.connect()

        q_current = robot.get_joint_positions()
        safety_checker = SafetyChecker(config=SafetyConfig(), q=q_current)

        servo = PinocchioServoController(
            urdf_path=args.urdf,
            home_q=q_current,
            ee_frame_name="tool0",
            tcp_offset_pos=np.array(args.tcp_offset, dtype=np.float64),
            base_offset_pos=np.zeros(3, dtype=np.float64),
            base_offset_rot=rotz(math.radians(args.base_rz_deg)),
            kp_pos=args.kp_pos,
            kp_rot=args.kp_rot,
            damping=args.damping,
            max_joint_vel=args.max_joint_vel,
            alpha_dq=args.alpha_dq,
        )
        robot.kinematics = servo.kin

        builder = RealObservationBuilder(
            cfg=cfg,
            device=device,
            robot=robot,
            cameras=cameras,
            image_height=obs_h,
            image_width=obs_w,
        )
        builder.initialize_history()

        init_eef_pos = builder.get_latest_eef_pos()
        init_eef_quat = builder.get_latest_eef_quat()
        init_gripper = builder.get_latest_gripper_qpos()

        traj_exec = TrajectoryExecutor(
            action_dt=1.0 / float(args.policy_hz),
            exec_horizon=exec_horizon,
            ignore_action_orientation=args.ignore_action_orientation,
        )
        traj_exec.reset(init_eef_pos, init_eef_quat, init_gripper, time.monotonic())

        target_smoother = PolicyTargetSmoother(
            max_target_speed=args.max_target_speed,
            alpha_pos=args.smooth_alpha_pos,
            alpha_rot=args.smooth_alpha_rot,
            alpha_gripper=args.smooth_alpha_gripper,
        )
        target_smoother.reset(init_eef_pos, init_eef_quat, init_gripper)
        servo.reset(q_current)

        print()
        print("===========================================")
        print("REAL DIFFUSION RUNNER STARTED")
        print("===========================================")
        print(f"backend        : {args.backend}")
        print(f"motion enabled : {args.enable_motion}")
        print(f"camera mode    : {args.camera_mode}")
        print(f"device         : {device}")
        print(f"obs            : {obs_h}x{obs_w} x {n_obs_steps}")
        print(f"policy_hz      : {args.policy_hz}")
        print(f"exec_horizon   : {exec_horizon}")
        print(f"control_hz     : {args.control_hz}")
        print(f"tcp offset     : {np.array(args.tcp_offset, dtype=np.float64)}")
        print(f"kp_pos/rot     : {args.kp_pos:.3f} / {args.kp_rot:.3f}")
        print(f"max_joint_vel  : {args.max_joint_vel:.3f}")
        print(f"max_run_time   : {args.max_run_time:.1f} s")
        print("===========================================")
        print()

        start_t = time.monotonic()
        last_loop_t = time.monotonic()
        next_t = time.monotonic()
        last_print_t = 0.0
        last_qvel = np.zeros(6, dtype=np.float64)

        while True:
            now = time.monotonic()
            if args.max_run_time > 0.0 and now - start_t >= args.max_run_time:
                print("[INFO] max-run-time reached.")
                break

            real_dt = now - last_loop_t
            if real_dt <= 1e-6 or real_dt > 0.5:
                real_dt = control_dt
            last_loop_t = now

            loop_status = loop_watchdog.check(real_dt)

            q_current = robot.get_joint_positions()
            qvel = robot.get_joint_velocities()
            qacc = (qvel - last_qvel) / max(real_dt, 1e-6)
            last_qvel = qvel.copy()

            current_tcp_pos, current_tcp_rot, J = servo.kin.forward_and_jacobian(q_current)
            target_pos = current_tcp_pos.copy()
            target_rot = current_tcp_rot.copy()
            gripper_cmd = float(robot.get_gripper_qpos()[0])
            current_policy_t = time.monotonic()

            if loop_status.should_stop:
                safety_stop_triggered = True
                safety_stop_reason = loop_status.reason

            if safety_stop_triggered:
                robot.stop()
                traj_exec.clear()
                servo.reset(q_current)
            else:
                if traj_exec.needs_replan(current_policy_t):
                    builder.update()

                    if not traj_exec.has_buffered_actions():
                        obs_tensor = builder.build_tensor()
                        infer_start = time.monotonic()
                        with torch.inference_mode():
                            policy_out = policy.predict_action(obs_tensor)
                        infer_dt = time.monotonic() - infer_start

                        action_seq = extract_action_sequence(policy_out)
                        n_take = traj_exec.set_sequence(action_seq)

                        if args.verbose_plan:
                            print(
                                f"[PLAN] predicted={action_seq.shape[0]} "
                                f"execute={n_take} inference={infer_dt:.3f}s"
                            )
                        elif args.debug_timing:
                            print(f"[TIMING] inference_dt={infer_dt:.3f}s")

                    traj_exec.start_next_action(
                        builder.get_latest_eef_quat(),
                        current_policy_t,
                    )

                if traj_exec.has_active_action():
                    raw_pos, raw_rot, raw_gripper, alpha = traj_exec.get_target(current_policy_t)
                    target_pos, target_rot, gripper_cmd = target_smoother.update(
                        raw_pos=raw_pos,
                        raw_rot=raw_rot,
                        raw_gripper=raw_gripper,
                        dt=real_dt,
                    )

                pos_err_norm = float(np.linalg.norm(target_pos - current_tcp_pos))
                rot_err_norm = float(np.linalg.norm(orientation_error(target_rot, current_tcp_rot)))

                safety_res = safety_checker.check_loop(qvel=qvel, qacc=qacc, J=J)

                if pos_err_norm > args.max_pos_error_stop:
                    safety_stop_triggered = True
                    safety_stop_reason = f"target pos error too large: {pos_err_norm:.3f} m"
                    robot.stop()
                    traj_exec.clear()
                    servo.reset(q_current)

                elif rot_err_norm > args.max_rot_error_stop:
                    safety_stop_triggered = True
                    safety_stop_reason = f"target rot error too large: {rot_err_norm:.3f} rad"
                    robot.stop()
                    traj_exec.clear()
                    servo.reset(q_current)

                elif safety_res["status"] == "stop":
                    safety_stop_triggered = True
                    safety_stop_reason = (
                        f"SafetyChecker stop: {safety_res['reason']} "
                        f"(cond={safety_res['metrics'].get('cond', 0):.1f})"
                    )
                    robot.stop()
                    traj_exec.clear()
                    servo.reset(q_current)

                else:
                    q_target, servo_info = servo.compute(
                        q_current=q_current,
                        target_pos=target_pos,
                        target_rot=target_rot,
                        dt=real_dt,
                    )

                    if args.backend == "speedj":
                        robot.apply_joint_velocity(
                            qd_target=servo_info["dq"],
                            gripper_command=gripper_cmd,
                        )
                    else:
                        robot.apply_joint_command(
                            q_target=q_target,
                            gripper_command=gripper_cmd,
                        )

                    if gripper is not None:
                        gripper.set_command(gripper_cmd)

            if time.monotonic() - last_print_t >= args.print_period:
                print("target_pos     :", np.round(target_pos, 4))
                print("current_tcp_pos:", np.round(current_tcp_pos, 4))
                print("q_current deg  :", np.round(np.degrees(q_current), 2))
                print("gripper_cmd    :", round(float(gripper_cmd), 3))
                print("safety_stop    :", safety_stop_triggered, safety_stop_reason)
                if loop_status.status == "warn":
                    print("loop watchdog  :", loop_status.reason)
                print("-" * 60)
                last_print_t = time.monotonic()

            next_t += control_dt
            sleep_time = next_t - time.monotonic()
            if sleep_time > 0.0:
                time.sleep(sleep_time)
            else:
                next_t = time.monotonic()

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")

    finally:
        try:
            robot.stop()
        except Exception:
            pass
        try:
            if gripper is not None:
                gripper.close()
        except Exception:
            pass
        try:
            cameras.stop()
        except Exception:
            pass
        try:
            robot.close()
        except Exception:
            pass
        print("[INFO] Real diffusion runner stopped.")


if __name__ == "__main__":
    main()

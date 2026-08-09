from __future__ import annotations

import argparse
import math
import threading
import time
from pathlib import Path

import numpy as np
import torch
import cv2

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
TOP_CAMERA_CONFIG_PATH = (
    ROOT_DIR
    / "ur10_real_robot"
    / "camera"
    / "config"
    / "d435_config_dataset.json"
)
WRIST_CAMERA_CONFIG_PATH = (
    ROOT_DIR
    / "ur10_real_robot"
    / "camera"
    / "config"
    / "d455_config_dataset.json"
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
    parser.add_argument(
        "--num-inference-steps",
        type=int,
        default=None,
        help="Override diffusion sampling steps at execution time. Lower is faster but can reduce quality.",
    )
    parser.add_argument(
        "--torch-num-threads",
        type=int,
        default=None,
        help="Optional torch CPU thread count override.",
    )
    parser.add_argument(
        "--async-inference",
        action="store_true",
        help="Run policy inference in a background thread so the robot loop keeps streaming commands.",
    )

    parser.add_argument("--backend", choices=["fake", "speedj"], default="fake")
    parser.add_argument("--robot-ip", default="192.168.2.100")
    parser.add_argument("--enable-motion", action="store_true")

    parser.add_argument("--camera-mode", choices=["fake", "realsense"], default="fake")
    parser.add_argument("--top-serial", default=None)
    parser.add_argument("--wrist-serial", default=None)
    parser.add_argument("--camera-config", default=str(CAMERA_CONFIG_PATH))
    parser.add_argument("--top-camera-config", default=str(TOP_CAMERA_CONFIG_PATH))
    parser.add_argument("--wrist-camera-config", default=str(WRIST_CAMERA_CONFIG_PATH))
    parser.add_argument("--no-advanced-config", action="store_true")
    parser.add_argument("--capture-width", type=int, default=640)
    parser.add_argument("--capture-height", type=int, default=480)
    parser.add_argument("--camera-fps", type=int, default=30)
    parser.add_argument("--dataset-width", type=int, default=320)
    parser.add_argument("--dataset-height", type=int, default=240)
    parser.add_argument(
        "--top-crop",
        nargs=4,
        type=int,
        metavar=("X", "Y", "W", "H"),
        default=None,
        help="Crop top camera in raw capture pixels before resizing.",
    )
    parser.add_argument(
        "--wrist-crop",
        nargs=4,
        type=int,
        metavar=("X", "Y", "W", "H"),
        default=None,
        help="Crop wrist camera in raw capture pixels before resizing.",
    )

    parser.add_argument("--urdf", default=str(URDF_PATH))
    parser.add_argument("--tcp-offset", nargs=3, type=float, default=[0.0, 0.0, 0.022])
    parser.add_argument("--base-rz-deg", type=float, default=180.0)

    parser.add_argument("--control-hz", type=float, default=50.0)
    parser.add_argument("--policy-hz", type=float, default=5.0)
    parser.add_argument("--exec-horizon", type=int, default=None)
    parser.add_argument(
        "--action-quat-format",
        choices=["wxyz", "xyzw"],
        default="wxyz",
        help="Quaternion order used in 8D policy actions. Real datasets are saved as wxyz.",
    )

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
    parser.add_argument(
        "--target-smoother-dt-cap",
        type=float,
        default=None,
        help=(
            "Cap dt used by target smoothing/speed limiting. Defaults to the "
            "robot control dt so slow inference cannot permit a large target jump."
        ),
    )
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
    parser.add_argument(
        "--initial-gripper-width-mm",
        type=float,
        default=None,
        help="Initial gripper width requested before the first policy observation. Defaults to open width.",
    )
    parser.add_argument("--gripper-command-period", type=float, default=0.10)
    parser.add_argument("--gripper-deadband-mm", type=float, default=1.0)
    parser.add_argument(
        "--gripper-latch",
        action="store_true",
        help="Latch gripper closed once policy command crosses close threshold.",
    )
    parser.add_argument("--gripper-latch-close-threshold", type=float, default=0.30)
    parser.add_argument("--gripper-latch-open-threshold", type=float, default=-0.05)
    parser.add_argument("--gripper-latch-close-command", type=float, default=1.20)
    parser.add_argument("--gripper-latch-open-command", type=float, default=-0.20)
    parser.add_argument(
        "--gripper-close-boost",
        action="store_true",
        help=(
            "Simple gripper post-process: if policy command is above a "
            "threshold, send a full close command; otherwise keep the policy "
            "command unchanged."
        ),
    )
    parser.add_argument("--gripper-close-boost-threshold", type=float, default=0.40)
    parser.add_argument("--gripper-close-boost-command", type=float, default=1.20)
    parser.add_argument(
        "--gripper-quantize",
        action="store_true",
        help="Snap predicted gripper commands to a fixed set of command values.",
    )
    parser.add_argument(
        "--gripper-quantize-values",
        nargs="+",
        type=float,
        default=[-0.2, 0.30, 0.70],
        help="Command values used by --gripper-quantize.",
    )
    parser.add_argument(
        "--gripper-quantize-thresholds",
        nargs="*",
        type=float,
        default=None,
        help=(
            "Optional thresholds between quantized gripper values. "
            "For values [-0.2, 0.3, 0.7], thresholds [0.15, 0.40] mean "
            "cmd < 0.15 -> -0.2, cmd < 0.40 -> 0.3, otherwise 0.7. "
            "Defaults to nearest-value quantization."
        ),
    )

    parser.add_argument("--print-period", type=float, default=0.5)
    parser.add_argument("--max-run-time", type=float, default=30.0)
    parser.add_argument("--verbose-plan", action="store_true")
    parser.add_argument("--debug-timing", action="store_true")
    parser.add_argument(
        "--debug-gripper-plan",
        action="store_true",
        help="Print raw predicted gripper values for every new policy plan.",
    )
    parser.add_argument(
        "--show-cameras",
        action="store_true",
        help="Show the latest camera observations used by the policy.",
    )
    parser.add_argument(
        "--camera-display-period",
        type=float,
        default=0.10,
        help="Minimum delay between camera display refreshes, in seconds.",
    )
    parser.add_argument(
        "--camera-display-scale",
        type=int,
        default=2,
        help="Nearest-neighbor display scale for the exact policy images.",
    )

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

    if args.torch_num_threads is not None:
        torch.set_num_threads(int(args.torch_num_threads))

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
    target_smoother_dt_cap = (
        control_dt
        if args.target_smoother_dt_cap is None
        else max(1e-6, float(args.target_smoother_dt_cap))
    )

    print("[INFO] Loading policy...")
    policy, cfg = load_policy(args.checkpoint, device)
    if args.num_inference_steps is not None:
        if not hasattr(policy, "num_inference_steps"):
            raise AttributeError("Loaded policy does not expose num_inference_steps.")
        policy.num_inference_steps = int(args.num_inference_steps)
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
        top_config_path=args.top_camera_config,
        wrist_config_path=args.wrist_camera_config,
        capture_width=args.capture_width,
        capture_height=args.capture_height,
        fps=args.camera_fps,
        dataset_size=(args.dataset_width, args.dataset_height),
        display_size=(640, 480),
        fake=args.camera_mode == "fake",
        apply_advanced_config=not args.no_advanced_config,
        top_crop=args.top_crop,
        wrist_crop=args.wrist_crop,
    )

    gripper = None
    safety_stop_triggered = False
    safety_stop_reason = ""
    inference_thread = None
    camera_display_thread = None
    camera_display_stop = threading.Event()
    camera_display_lock = threading.Lock()
    camera_display_frames = {"top": None, "wrist": None}

    def camera_display_worker() -> None:
        while not camera_display_stop.is_set():
            with camera_display_lock:
                top = None if camera_display_frames["top"] is None else camera_display_frames["top"].copy()
                wrist = (
                    None
                    if camera_display_frames["wrist"] is None
                    else camera_display_frames["wrist"].copy()
                )

            if top is None or wrist is None:
                time.sleep(0.02)
                continue

            cv2.imshow("diffusion real top_down", top)
            cv2.imshow("diffusion real wrist", wrist)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                camera_display_stop.set()
                break
            time.sleep(max(0.0, float(args.camera_display_period)))

    loop_watchdog = ControlLoopWatchdog(
        expected_dt=control_dt,
        warn_factor=args.loop_watchdog_warn_factor,
        stop_factor=args.loop_watchdog_stop_factor,
        enabled=not args.disable_loop_watchdog,
    )

    try:
        robot.connect()
        cameras.start()
        if args.show_cameras:
            camera_display_thread = threading.Thread(
                target=camera_display_worker,
                daemon=True,
            )
            camera_display_thread.start()

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
            initial_width_mm = (
                args.gripper_open_width_mm
                if args.initial_gripper_width_mm is None
                else args.initial_gripper_width_mm
            )
            actual_width_mm = gripper.move_to_width_sync(initial_width_mm)
            print(
                f"[GRIPPER] Initial width requested: "
                f"{initial_width_mm:.1f} mm, actual: {actual_width_mm:.1f} mm."
            )

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

        def get_observed_gripper_qpos() -> np.ndarray:
            if gripper is None:
                return robot.get_gripper_qpos()

            gripper_status, _ = gripper.get_status_snapshot()
            if gripper_status is None:
                return robot.get_gripper_qpos()

            return np.array(
                [gripper.width_to_command(gripper_status.width_mm)],
                dtype=np.float64,
            )

        builder = RealObservationBuilder(
            cfg=cfg,
            device=device,
            robot=robot,
            cameras=cameras,
            image_height=obs_h,
            image_width=obs_w,
            gripper_qpos_fn=get_observed_gripper_qpos,
        )
        builder.initialize_history()

        init_eef_pos = builder.get_latest_eef_pos()
        init_eef_quat = builder.get_latest_eef_quat()
        init_gripper = builder.get_latest_gripper_qpos()

        traj_exec = TrajectoryExecutor(
            action_dt=1.0 / float(args.policy_hz),
            exec_horizon=exec_horizon,
            ignore_action_orientation=args.ignore_action_orientation,
            action_quat_format=args.action_quat_format,
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
        if hasattr(policy, "num_inference_steps"):
            print(f"infer steps    : {policy.num_inference_steps}")
        if args.torch_num_threads is not None:
            print(f"torch threads  : {torch.get_num_threads()}")
        print(f"obs            : {obs_h}x{obs_w} x {n_obs_steps}")
        print(f"policy_hz      : {args.policy_hz}")
        print(f"exec_horizon   : {exec_horizon}")
        print(f"action quat    : {args.action_quat_format}")
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
        last_camera_display_t = 0.0
        last_qvel = np.zeros(6, dtype=np.float64)
        gripper_latched_closed = False
        gripper_close_boost_active = False
        last_raw_pos = None
        last_raw_gripper = None
        inference_lock = threading.Lock()
        inference_state = {
            "busy": False,
            "action_seq": None,
            "infer_dt": None,
            "error": None,
        }

        def start_async_inference(obs_tensor):
            nonlocal inference_thread

            def _worker():
                infer_start = time.monotonic()
                try:
                    with torch.inference_mode():
                        policy_out = policy.predict_action(obs_tensor)
                    action_seq = extract_action_sequence(policy_out)
                    infer_dt = time.monotonic() - infer_start
                    with inference_lock:
                        inference_state["action_seq"] = action_seq
                        inference_state["infer_dt"] = infer_dt
                        inference_state["error"] = None
                        inference_state["busy"] = False
                except Exception as exc:
                    with inference_lock:
                        inference_state["action_seq"] = None
                        inference_state["infer_dt"] = None
                        inference_state["error"] = exc
                        inference_state["busy"] = False

            with inference_lock:
                inference_state["busy"] = True
                inference_state["action_seq"] = None
                inference_state["infer_dt"] = None
                inference_state["error"] = None
            inference_thread = threading.Thread(target=_worker)
            inference_thread.start()

        def print_gripper_plan(action_seq: np.ndarray, label: str) -> None:
            if not args.debug_gripper_plan:
                return
            if action_seq.ndim != 2 or action_seq.shape[1] < 1:
                return
            gripper_values = action_seq[:exec_horizon, -1].astype(np.float64)
            print(
                f"[GRIPPER PLAN {label}] "
                f"min={gripper_values.min():.3f} "
                f"max={gripper_values.max():.3f} "
                f"seq={np.round(gripper_values, 3)}"
            )

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
            gripper_cmd_for_obs = gripper_cmd
            gripper_cmd_before_latch = gripper_cmd
            gripper_close_boost_active = False
            last_raw_pos = None
            last_raw_gripper = None
            current_policy_t = time.monotonic()

            if loop_status.should_stop:
                safety_stop_triggered = True
                safety_stop_reason = loop_status.reason

            if safety_stop_triggered:
                robot.stop()
                traj_exec.clear()
                servo.reset(q_current)
            else:
                if args.async_inference:
                    with inference_lock:
                        async_action_seq = inference_state["action_seq"]
                        async_infer_dt = inference_state["infer_dt"]
                        async_error = inference_state["error"]
                        if async_action_seq is not None or async_error is not None:
                            inference_state["action_seq"] = None
                            inference_state["infer_dt"] = None
                            inference_state["error"] = None

                    if async_error is not None:
                        raise async_error

                    if async_action_seq is not None:
                        print_gripper_plan(async_action_seq, "async")
                        n_take = traj_exec.set_sequence(async_action_seq)
                        if args.verbose_plan:
                            print(
                                f"[PLAN] predicted={async_action_seq.shape[0]} "
                                f"execute={n_take} inference={async_infer_dt:.3f}s async"
                            )
                        elif args.debug_timing:
                            print(f"[TIMING] inference_dt={async_infer_dt:.3f}s async")

                if traj_exec.needs_replan(current_policy_t):
                    if args.async_inference:
                        if traj_exec.has_buffered_actions():
                            traj_exec.start_next_action(
                                builder.get_latest_eef_quat(),
                                current_policy_t,
                            )
                        else:
                            with inference_lock:
                                inference_busy = bool(inference_state["busy"])
                            if not inference_busy:
                                builder.update()
                                obs_tensor = builder.build_tensor()
                                start_async_inference(obs_tensor)
                    else:
                        builder.update()

                        if not traj_exec.has_buffered_actions():
                            obs_tensor = builder.build_tensor()
                            infer_start = time.monotonic()
                            with torch.inference_mode():
                                policy_out = policy.predict_action(obs_tensor)
                            infer_dt = time.monotonic() - infer_start

                            action_seq = extract_action_sequence(policy_out)
                            print_gripper_plan(action_seq, "sync")
                            n_take = traj_exec.set_sequence(action_seq)

                            if args.verbose_plan:
                                print(
                                    f"[PLAN] predicted={action_seq.shape[0]} "
                                    f"execute={n_take} inference={infer_dt:.3f}s"
                                )
                            elif args.debug_timing:
                                print(f"[TIMING] inference_dt={infer_dt:.3f}s")

                        # Inference can be slow on CPU. Start the action timeline
                        # after inference, otherwise the action may already be
                        # considered elapsed before the robot can follow it.
                        current_policy_t = time.monotonic()
                        traj_exec.start_next_action(
                            builder.get_latest_eef_quat(),
                            current_policy_t,
                        )

                if args.show_cameras and builder.latest_frames is not None:
                    display_now = time.monotonic()
                    if display_now - last_camera_display_t >= args.camera_display_period:
                        frames = builder.latest_frames
                        top_policy_rgb = cv2.resize(
                            frames.top_rgb,
                            (obs_w, obs_h),
                            interpolation=cv2.INTER_AREA,
                        )
                        wrist_policy_rgb = cv2.resize(
                            frames.wrist_rgb,
                            (obs_w, obs_h),
                            interpolation=cv2.INTER_AREA,
                        )
                        top = cv2.cvtColor(top_policy_rgb, cv2.COLOR_RGB2BGR)
                        wrist = cv2.cvtColor(wrist_policy_rgb, cv2.COLOR_RGB2BGR)
                        display_scale = max(1, int(args.camera_display_scale))
                        if display_scale > 1:
                            display_size = (
                                obs_w * display_scale,
                                obs_h * display_scale,
                            )
                            top = cv2.resize(
                                top,
                                display_size,
                                interpolation=cv2.INTER_NEAREST,
                            )
                            wrist = cv2.resize(
                                wrist,
                                display_size,
                                interpolation=cv2.INTER_NEAREST,
                            )
                        cv2.putText(
                            top,
                            f"top-down | policy obs {obs_w}x{obs_h} x{display_scale}",
                            (10, 28),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2,
                            cv2.LINE_AA,
                        )
                        cv2.putText(
                            wrist,
                            f"wrist | policy obs {obs_w}x{obs_h} x{display_scale}",
                            (10, 28),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2,
                            cv2.LINE_AA,
                        )
                        with camera_display_lock:
                            camera_display_frames["top"] = top
                            camera_display_frames["wrist"] = wrist
                        last_camera_display_t = display_now

                if traj_exec.has_active_action():
                    raw_pos, raw_rot, raw_gripper, alpha = traj_exec.get_target(current_policy_t)
                    last_raw_pos = raw_pos.copy()
                    last_raw_gripper = float(raw_gripper)
                    target_pos, target_rot, gripper_cmd = target_smoother.update(
                        raw_pos=raw_pos,
                        raw_rot=raw_rot,
                        raw_gripper=raw_gripper,
                        dt=min(real_dt, target_smoother_dt_cap),
                    )
                    gripper_cmd_before_latch = gripper_cmd
                    gripper_cmd_for_obs = gripper_cmd

                    if args.gripper_quantize:
                        quantize_values = np.asarray(
                            args.gripper_quantize_values,
                            dtype=np.float64,
                        )
                        if quantize_values.size > 0:
                            quantize_thresholds = (
                                np.asarray(args.gripper_quantize_thresholds, dtype=np.float64)
                                if args.gripper_quantize_thresholds is not None
                                else np.array([], dtype=np.float64)
                            )
                            if quantize_thresholds.size == max(0, quantize_values.size - 1):
                                nearest_idx = int(np.searchsorted(
                                    quantize_thresholds,
                                    gripper_cmd,
                                    side="right",
                                ))
                            else:
                                nearest_idx = int(np.argmin(np.abs(quantize_values - gripper_cmd)))
                            gripper_cmd = float(quantize_values[nearest_idx])
                            gripper_cmd_for_obs = gripper_cmd

                    if args.gripper_close_boost and not args.gripper_latch:
                        gripper_close_boost_active = (
                            gripper_cmd >= args.gripper_close_boost_threshold
                        )
                        if gripper_close_boost_active:
                            gripper_cmd = args.gripper_close_boost_command

                    if args.gripper_latch:
                        if gripper_latched_closed:
                            if gripper_cmd <= args.gripper_latch_open_threshold:
                                gripper_latched_closed = False
                                gripper_cmd = args.gripper_latch_open_command
                            else:
                                gripper_cmd = args.gripper_latch_close_command
                        elif gripper_cmd >= args.gripper_latch_close_threshold:
                            gripper_latched_closed = True
                            gripper_cmd = args.gripper_latch_close_command

                pos_err_norm = float(np.linalg.norm(target_pos - current_tcp_pos))
                rot_err_norm = float(np.linalg.norm(orientation_error(target_rot, current_tcp_rot)))

                safety_res = safety_checker.check_loop(qvel=qvel, qacc=qacc, J=J)

                if pos_err_norm > args.max_pos_error_stop:
                    safety_stop_triggered = True
                    safety_stop_reason = f"target pos error too large: {pos_err_norm:.3f} m"
                    print("[SAFETY STOP] target position error too large")
                    print("  current_tcp_pos:", np.round(current_tcp_pos, 4))
                    print("  limited_target :", np.round(target_pos, 4))
                    if last_raw_pos is not None:
                        print("  raw_policy_pos :", np.round(last_raw_pos, 4))
                        print("  raw_gripper    :", round(float(last_raw_gripper), 3))
                    print("  pos_err_m     :", round(pos_err_norm, 4))
                    print("  threshold_m   :", round(float(args.max_pos_error_stop), 4))
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
                            gripper_command=gripper_cmd_for_obs,
                        )
                    else:
                        robot.apply_joint_command(
                            q_target=q_target,
                            gripper_command=gripper_cmd_for_obs,
                        )

                    if gripper is not None:
                        gripper.set_command(gripper_cmd)

            if time.monotonic() - last_print_t >= args.print_period:
                gripper_target_width_mm = None
                gripper_actual_width_mm = None
                if gripper is not None:
                    gripper_target_width_mm = gripper.command_to_width(gripper_cmd)
                    gripper_status, _ = gripper.get_status_snapshot()
                    if gripper_status is not None:
                        gripper_actual_width_mm = gripper_status.width_mm

                print("target_pos     :", np.round(target_pos, 4))
                print("current_tcp_pos:", np.round(current_tcp_pos, 4))
                print("q_current deg  :", np.round(np.degrees(q_current), 2))
                if last_raw_gripper is not None:
                    print("gripper_raw    :", round(float(last_raw_gripper), 3))
                print("gripper_pre    :", round(float(gripper_cmd_before_latch), 3))
                print("gripper_sent   :", round(float(gripper_cmd), 3))
                if gripper_target_width_mm is not None:
                    print("gripper_target :", round(float(gripper_target_width_mm), 1), "mm")
                if gripper_actual_width_mm is not None:
                    print("gripper_actual :", round(float(gripper_actual_width_mm), 1), "mm")
                if args.gripper_latch:
                    print("gripper_latch  :", gripper_latched_closed)
                elif args.gripper_close_boost:
                    print("gripper_obs    :", round(float(gripper_cmd_for_obs), 3))
                    print("gripper_boost  :", gripper_close_boost_active)
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
            if inference_thread is not None and inference_thread.is_alive():
                print("[INFO] Waiting for inference thread to finish...")
                inference_thread.join()
        except Exception:
            pass
        try:
            camera_display_stop.set()
            if camera_display_thread is not None and camera_display_thread.is_alive():
                camera_display_thread.join(timeout=1.0)
        except Exception:
            pass
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
            if args.show_cameras:
                cv2.destroyAllWindows()
        except Exception:
            pass
        try:
            robot.close()
        except Exception:
            pass
        print("[INFO] Real diffusion runner stopped.")


if __name__ == "__main__":
    main()

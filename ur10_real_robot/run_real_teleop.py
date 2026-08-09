#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import rclpy
from rclpy.node import Node

from dp_mujoco.policy_exec.pose_utils import orientation_error
from dp_mujoco.policy_exec.servo_controller_pinocchio import PinocchioServoController

from ur10_real_robot.teleop.real_teleop_target_listener import RealTeleopTargetListener
from ur10_real_robot.backends.onrobot_gripper import AsyncOnRobotGripperController
from ur10_real_robot.backends.fake_robot_backend import FakeRobotBackend, rot_to_quat_wxyz
from ur10_real_robot.backends.ur10_speedj_backend import UR10SpeedjBackend
from ur10_real_robot.camera import AsyncDualCameraCapture, DualCameraRig
from ur10_real_robot.teleop.real_dataset_writer import (
    RealZarrEpisodeWriter,
    resolve_real_dataset_path,
)
from ur10_real_robot.teleop.real_episode_recorder import RealEpisodeRecorder
from ur10_real_robot.safety.safety_config import SafetyConfig, SafetyChecker
from ur10_real_robot.safety.watchdog import ControlLoopWatchdog, TouchTargetWatchdog

"""
Bench mark 1 
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim

ROBOT_IP=192.168.2.100 REAL_BACKEND=speedj ENABLE_MOTION=1 \
TCP_OFFSET="0 0 0.022" \
GRIPPER_ENABLE=1 GRIPPER_MOTION_ENABLE=1 \
GRIPPER_CONTROL_MODE=button \
GRIPPER_OPEN_WIDTH_MM=85 GRIPPER_CLOSE_WIDTH_MM=30 GRIPPER_FORCE_N=8 \
CAMERA_ENABLE=1 SHOW_CAMERAS=1 RECORD_ENABLE=1 \
NO_ADVANCED_CONFIG=0 \
TOP_SERIAL=332322072359 WRIST_SERIAL=043422251624 \
TOP_CAMERA_CONFIG="/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/camera/config/d435_config_dataset.json" \
WRIST_CAMERA_CONFIG="/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/camera/config/d455_config_dataset.json" \
TOP_CROP="40 30 560 420" \
WRIST_CROP="0 0 640 480" \
DATASET_WIDTH=320 DATASET_HEIGHT=240 RECORD_FREQ=10 \
MIN_EPISODE_STEPS=5 \
TOUCH_AXIS_MAP=swap_xy_neg_y \
TOUCH_ROT_MAP=same_as_position TOUCH_ROT_APPLY=world TOUCH_ROT_METHOD=matrix \
KP_POS=0.40 KP_ROT=0.20 \
MAX_JOINT_VEL=0.10 \
POSITION_SCALE=0.50 MAX_TARGET_SPEED=0.08 \     

/home/luca/venvs/mujoco_ros/bin/python \
  -m ur10_real_robot.policy_exec.run_diffusion_real \
  --checkpoint data/checkpoints/first_real_model.ckpt \
  --backend speedj \
  --robot-ip 192.168.2.100 \
  --enable-motion \
  --camera-mode realsense \
  --top-serial 332322072359 \
  --wrist-serial 043422251624 \
  --top-camera-config ur10_real_robot/camera/config/d435_config_dataset.json \
  --wrist-camera-config ur10_real_robot/camera/config/d455_config_dataset.json \
  --top-crop 40 30 560 420 \
  --wrist-crop 0 0 640 480 \
  --tcp-offset 0 0 0.022 \
  --policy-hz 0.2 \
  --exec-horizon 1 \
  --kp-pos 0.45 \
  --kp-rot 0.0 \
  --max-joint-vel 0.08 \
  --max-target-speed 0.04 \
  --alpha-dq 0.04 \
  --speedj-a 0.04 \
  --debug-timing \


"""





URDF_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "dp_mujoco/models/universal_robots_ur10e/ur10_d455_support_rg2ft_fixed_gripper.urdf"
)
CAMERA_CONFIG_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "ur10_real_robot/camera/config/d435i_config.json"
)
TOP_CAMERA_CONFIG_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "ur10_real_robot/camera/config/d435_config_dataset.json"
)
WRIST_CAMERA_CONFIG_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "ur10_real_robot/camera/config/d455_config_dataset.json"
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


def ros_spin_thread(node: Node) -> None:
    rclpy.spin(node)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--backend",
        choices=["fake", "speedj"],
        default="fake",
        help="Robot backend. fake never commands the real robot.",
    )

    parser.add_argument(
        "--robot-ip",
        type=str,
        default="192.168.2.100",
        help="UR10 controller IP for --backend speedj.",
    )

    parser.add_argument(
        "--enable-motion",
        action="store_true",
        help="Actually send speedj/stopj commands when --backend speedj is used.",
    )

    parser.add_argument(
        "--urdf",
        type=str,
        default=URDF_PATH,
        help="Path to UR10 URDF used by Pinocchio.",
    )

    parser.add_argument(
        "--control-hz",
        type=float,
        default=50.0,
        help="Control frequency in Hz.",
    )

    parser.add_argument(
        "--position-scale",
        type=float,
        default=0.4,
        help="Touch to robot position scale.",
    )

    parser.add_argument(
        "--max-target-speed",
        type=float,
        default=0.30,
        help="Max cartesian target speed in m/s.",
    )

    parser.add_argument(
        "--touch-axis-map",
        choices=[
            "identity",
            "swap_xy",
            "swap_xy_neg",
            "swap_xy_neg_y",
            "swap_xy_neg_x",
            "neg_xy",
        ],
        default="swap_xy_neg_y",
        help="Position axis mapping from Touch deltas to robot deltas.",
    )

    parser.add_argument(
        "--touch-rot-map",
        choices=[
            "same_as_position",
            "identity",
            "swap_xy",
            "swap_xy_neg",
            "swap_xy_neg_y",
            "swap_xy_neg_x",
            "neg_xy",
        ],
        default="same_as_position",
        help="Orientation axis mapping from Touch delta rotations to robot delta rotations.",
    )

    parser.add_argument(
        "--touch-rot-apply",
        choices=["world", "local"],
        default="world",
        help="Apply Touch delta rotation in robot world frame or tool/local frame.",
    )

    parser.add_argument(
        "--touch-rot-method",
        choices=["matrix", "rotvec", "rotvec_inv"],
        default="matrix",
        help="How Touch delta rotations are mapped into robot rotations.",
    )

    parser.add_argument(
        "--target-alpha-pos",
        type=float,
        default=0.25,
        help="Target position smoothing alpha.",
    )

    parser.add_argument(
        "--target-alpha-rot",
        type=float,
        default=0.15,
        help="Target orientation smoothing alpha.",
    )

    parser.add_argument(
        "--tcp-offset",
        nargs=3,
        type=float,
        default=[0.0, 0.0, 0.022],
        help="TCP offset from tool0 in tool0 frame.",
    )

    parser.add_argument(
        "--base-rz-deg",
        type=float,
        default=180.0,
        help="Real UR controller base frame correction around Z, in degrees.",
    )

    parser.add_argument(
        "--kp-pos",
        type=float,
        default=0.5,
        help="Cartesian position gain.",
    )

    parser.add_argument(
        "--kp-rot",
        type=float,
        default=0.0,
        help="Cartesian orientation gain. Start with 0.0 on real robot.",
    )

    parser.add_argument(
        "--damping",
        type=float,
        default=0.12,
        help="Damped least squares damping.",
    )

    parser.add_argument(
        "--max-joint-vel",
        type=float,
        default=0.05,
        help="Max joint velocity in rad/s inside servo controller.",
    )

    parser.add_argument(
        "--alpha-dq",
        type=float,
        default=0.05,
        help="Joint velocity smoothing alpha.",
    )

    parser.add_argument(
        "--speedj-a",
        type=float,
        default=0.06,
        help="speedj acceleration for --backend speedj.",
    )

    parser.add_argument(
        "--speedj-t",
        type=float,
        default=None,
        help="speedj command duration. Default: control dt.",
    )

    parser.add_argument(
        "--socket-timeout",
        type=float,
        default=1.0,
        help="Socket timeout for --backend speedj.",
    )

    parser.add_argument(
        "--stop-deceleration",
        type=float,
        default=1.0,
        help="stopj deceleration for --backend speedj.",
    )

    parser.add_argument(
        "--print-period",
        type=float,
        default=0.5,
        help="Debug print period in seconds.",
    )

    parser.add_argument(
        "--home-reset-kp",
        type=float,
        default=1.0,
        help="Joint-space gain for the camera-window h home reset.",
    )

    parser.add_argument(
        "--home-reset-max-joint-vel",
        type=float,
        default=0.08,
        help="Max joint velocity in rad/s for the camera-window h home reset.",
    )

    parser.add_argument(
        "--home-reset-threshold-deg",
        type=float,
        default=0.5,
        help="Stop home reset when max joint error is below this threshold.",
    )

    parser.add_argument(
        "--watchdog-timeout",
        type=float,
        default=0.30,
        help="Stop if no fresh Touch target is received for this many seconds.",
    )

    parser.add_argument(
        "--disable-watchdog",
        action="store_true",
        help="Disable Touch target watchdog.",
    )

    parser.add_argument(
        "--loop-watchdog-warn-factor",
        type=float,
        default=2.0,
        help="Warn if loop dt is greater than control_dt times this factor.",
    )

    parser.add_argument(
        "--loop-watchdog-stop-factor",
        type=float,
        default=5.0,
        help="Stop if loop dt is greater than control_dt times this factor.",
    )

    parser.add_argument(
        "--disable-loop-watchdog",
        action="store_true",
        help="Disable robot control loop timing watchdog.",
    )

    parser.add_argument(
        "--gripper-enable",
        action="store_true",
        help="Connect to the OnRobot gripper and send teleop gripper commands.",
    )

    parser.add_argument(
        "--gripper-motion-enable",
        action="store_true",
        help="Actually send Modbus motion commands to the gripper.",
    )

    parser.add_argument(
        "--gripper-ip",
        type=str,
        default="192.168.1.1",
        help="OnRobot gripper IP.",
    )

    parser.add_argument(
        "--gripper-port",
        type=int,
        default=502,
        help="OnRobot Modbus/TCP port.",
    )

    parser.add_argument(
        "--gripper-open-width-mm",
        type=float,
        default=85.0,
        help="Width command when the teleop gripper value is open.",
    )

    parser.add_argument(
        "--gripper-close-width-mm",
        type=float,
        default=35.0,
        help="Width command when the teleop gripper value is closed.",
    )

    parser.add_argument(
        "--gripper-force-n",
        type=float,
        default=8.0,
        help="OnRobot gripper force in N.",
    )

    parser.add_argument(
        "--initial-gripper-width-mm",
        type=float,
        default=None,
        help="Initial gripper width requested at startup and home. Defaults to open width.",
    )

    parser.add_argument(
        "--gripper-command-period",
        type=float,
        default=0.10,
        help="Minimum period between gripper Modbus updates.",
    )

    parser.add_argument(
        "--gripper-deadband-mm",
        type=float,
        default=1.0,
        help="Minimum target width change before sending another gripper command.",
    )

    parser.add_argument(
        "--gripper-control-mode",
        choices=["button", "width"],
        default="button",
        help="button sends endpoint commands on press/release; width streams width targets.",
    )

    parser.add_argument(
        "--gripper-command-mode",
        choices=["continuous", "three_state"],
        default="continuous",
        help=(
            "How Touch gripper buttons produce the recorded gripper command. "
            "three_state uses open -> narrow -> grasp on close-button clicks."
        ),
    )

    parser.add_argument(
        "--gripper-step-values",
        nargs=3,
        type=float,
        default=[-0.2, 0.30, 0.70],
        metavar=("OPEN", "NARROW", "GRASP"),
        help="Gripper command values used by --gripper-command-mode three_state.",
    )

    parser.add_argument(
        "--record-gripper-qpos-source",
        choices=["actual_width", "command"],
        default="actual_width",
        help="Source for robot0_gripper_qpos in recorded datasets.",
    )

    parser.add_argument(
        "--record-gripper-action-source",
        choices=["button_target", "actual_width", "command"],
        default="actual_width",
        help="Source for the gripper component of recorded actions.",
    )

    parser.add_argument(
        "--camera-enable",
        action="store_true",
        help="Enable top-down + wrist camera capture.",
    )

    parser.add_argument(
        "--camera-mode",
        choices=["fake", "realsense"],
        default="realsense",
        help="Camera backend.",
    )

    parser.add_argument("--top-serial", type=str, default="332322072359")
    parser.add_argument("--wrist-serial", type=str, default="043422251624")
    parser.add_argument("--camera-config", type=str, default=CAMERA_CONFIG_PATH)
    parser.add_argument("--top-camera-config", type=str, default=TOP_CAMERA_CONFIG_PATH)
    parser.add_argument("--wrist-camera-config", type=str, default=WRIST_CAMERA_CONFIG_PATH)
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

    parser.add_argument(
        "--show-cameras",
        action="store_true",
        help="Display camera previews. q/esc quits, space starts/stops recording.",
    )

    parser.add_argument(
        "--record-enable",
        action="store_true",
        help="Enable real teleop episode recording to zarr.",
    )

    parser.add_argument(
        "--record-freq",
        type=float,
        default=10.0,
        help="Recording frequency in Hz.",
    )

    parser.add_argument(
        "--min-episode-steps",
        type=int,
        default=3,
        help="Do not save an episode with fewer recorded steps than this.",
    )

    parser.add_argument(
        "--dataset-path",
        type=str,
        default=None,
        help="Output zarr path. If it exists, new episodes are appended.",
    )

    parser.add_argument(
        "--append-latest-dataset",
        action="store_true",
        help=(
            "Append to the latest data/datasets/real_demo_data_*.zarr "
            "when --dataset-path is not provided."
        ),
    )

    parser.add_argument(
        "--dataset-root",
        type=str,
        default="data/datasets",
        help="Root directory used for new datasets and --append-latest-dataset.",
    )

    return parser


def draw_camera_overlay(
    image_bgr: np.ndarray,
    title: str,
    recording: bool,
    paused: bool,
    homing: bool,
    steps: int,
    saved_episodes: int,
) -> np.ndarray:
    out = image_bgr.copy()
    color = (
        (255, 120, 0)
        if homing
        else ((0, 220, 255) if paused else ((0, 0, 255) if recording else (0, 180, 0)))
    )
    status = "HOME" if homing else ("PAUSED" if paused else ("REC" if recording else "READY"))
    cv2.putText(
        out,
        f"{title} | {status} | steps={steps} saved={saved_episodes}",
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        out,
        "space=start/stop  p=pause  h=home  backspace=cancel  q/esc=quit",
        (12, out.shape[0] - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return out


def main() -> None:
    args = build_parser().parse_args()

    control_hz = float(args.control_hz)
    control_dt = 1.0 / control_hz

    rclpy.init()

    ros_node = RealTeleopTargetListener(
        position_scale=args.position_scale,
        max_target_speed=args.max_target_speed,
        target_filter_alpha_pos=args.target_alpha_pos,
        target_filter_alpha_rot=args.target_alpha_rot,
        gripper_min=-0.2,
        gripper_max=1.2,
        gripper_speed=0.5,
        gripper_command_mode=args.gripper_command_mode,
        gripper_step_values=tuple(args.gripper_step_values),
        touch_axis_map=args.touch_axis_map,
        touch_rot_map=args.touch_rot_map,
        touch_rot_apply=args.touch_rot_apply,
        touch_rot_method=args.touch_rot_method,
    )

    ros_thread = threading.Thread(
        target=ros_spin_thread,
        args=(ros_node,),
        daemon=True,
    )
    ros_thread.start()

    if args.backend == "fake":
        initial_q = np.array(
            [0.0, -1.3, 1.8, -0.22, 1.57, 0.0],
            dtype=np.float64,
        )
        robot = FakeRobotBackend(
            initial_q=initial_q,
            control_dt=control_dt,
            max_delta_deg=2.0,
            kinematics=None,
        )
    elif args.backend == "speedj":
        robot = UR10SpeedjBackend(
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
    else:
        raise ValueError(f"Unknown backend: {args.backend}")

    safety_stop_triggered = False
    safety_stop_reason = ""
    gripper = None
    camera_capture = None
    recorder = None
    dataset_writer = None
    saved_episodes = 0
    initial_gripper_cmd = -0.2

    touch_watchdog = TouchTargetWatchdog(
        timeout=args.watchdog_timeout,
        enabled=not args.disable_watchdog,
    )
    loop_watchdog = ControlLoopWatchdog(
        expected_dt=control_dt,
        warn_factor=args.loop_watchdog_warn_factor,
        stop_factor=args.loop_watchdog_stop_factor,
        enabled=not args.disable_loop_watchdog,
    )

    SAFETY_POS_ERROR_STOP = 0.20
    SAFETY_ROT_ERROR_STOP = 0.60

    try:
        robot.connect()

        if args.camera_enable or args.record_enable:
            camera_rig = DualCameraRig(
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
            camera_capture = AsyncDualCameraCapture(camera_rig)
            camera_capture.start()

        if args.record_enable:
            if camera_capture is None:
                raise RuntimeError("--record-enable requires cameras.")
            dataset_path, dataset_mode = resolve_real_dataset_path(
                dataset_path=args.dataset_path,
                append_latest=args.append_latest_dataset,
                root=args.dataset_root,
            )
            recorder = RealEpisodeRecorder(enabled=True, record_freq=args.record_freq)
            if Path(dataset_path).exists():
                dataset_writer = RealZarrEpisodeWriter(dataset_path)
                saved_episodes = dataset_writer.n_episodes
            print(f"[REC] Dataset path: {dataset_path}")
            print(f"[REC] Dataset mode: {dataset_mode}")
            print(f"[REC] Existing episodes: {saved_episodes}")
            print(f"[REC] Min episode steps: {args.min_episode_steps}")

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
                control_mode=args.gripper_control_mode,
                enabled=args.gripper_motion_enable,
            )
            gripper.connect()
            initial_width_mm = (
                args.gripper_open_width_mm
                if args.initial_gripper_width_mm is None
                else args.initial_gripper_width_mm
            )
            actual_width_mm = gripper.move_to_width_sync(initial_width_mm)
            initial_gripper_cmd = gripper.width_to_command(actual_width_mm)
            print(
                f"[GRIPPER] Initial width requested: "
                f"{initial_width_mm:.1f} mm, actual: {actual_width_mm:.1f} mm."
            )

        q_current = robot.get_joint_positions()
        home_q = q_current.copy()
        safety_checker = SafetyChecker(config=SafetyConfig(), q=q_current)

        servo = PinocchioServoController(
            urdf_path=args.urdf,
            home_q=q_current,
            ee_frame_name="tool0",
            tcp_offset_pos=np.array(args.tcp_offset, dtype=np.float64),

            # Important :
            # Sur robot réel, pas de socle MuJoCo à z=0.4.
            base_offset_pos=np.array([0.0, 0.0, 0.0], dtype=np.float64),
            base_offset_rot=rotz(math.radians(args.base_rz_deg)),

            kp_pos=args.kp_pos,
            kp_rot=args.kp_rot,
            damping=args.damping,
            max_joint_vel=args.max_joint_vel,
            alpha_dq=args.alpha_dq,
        )

        # Optionnel pour que les backends puissent retourner eef_pos/eef_quat
        # calculés avec le même modèle Pinocchio que le contrôleur.
        robot.kinematics = servo.kin

        current_tcp_pos, current_tcp_rot, _ = servo.kin.forward_and_jacobian(q_current)

        ros_node.set_robot_reference(
            pos=current_tcp_pos,
            rot=current_tcp_rot,
        )

        servo.reset(q_current)

        print("\n-------------------------------------------")
        print("REAL TELEOP")
        print("-------------------------------------------")
        print(f"Backend        : {args.backend}")
        if args.backend == "speedj":
            print(f"Robot IP       : {args.robot_ip}")
            print(f"Motion enabled : {args.enable_motion}")
            print(f"speedj a       : {args.speedj_a}")
            print(f"speedj t       : {robot.speedj_t:.4f} s")
            print(f"stopj decel    : {args.stop_deceleration}")
        else:
            print("Motion         : aucun vrai robot commandé")
        print(f"Control Hz     : {control_hz}")
        print(f"Control dt     : {control_dt:.4f} s")
        print(f"URDF           : {args.urdf}")
        print(f"TCP offset     : {np.array(args.tcp_offset, dtype=np.float64)}")
        print(f"Base rz deg    : {args.base_rz_deg}")
        print(f"kp_pos         : {args.kp_pos}")
        print(f"kp_rot         : {args.kp_rot}")
        print(f"damping        : {args.damping}")
        print(f"max_joint_vel  : {args.max_joint_vel}")
        print(f"alpha_dq       : {args.alpha_dq}")
        print(f"touch axis map : {args.touch_axis_map}")
        print(f"touch rot map  : {args.touch_rot_map}")
        print(f"touch rot apply: {args.touch_rot_apply}")
        print(f"touch rot meth : {args.touch_rot_method}")
        print(f"touch watchdog : {touch_watchdog.enabled}")
        print(f"touch timeout  : {touch_watchdog.timeout:.3f} s")
        print(f"loop watchdog  : {loop_watchdog.enabled}")
        print(f"loop warn dt   : {loop_watchdog.warn_dt:.3f} s")
        print(f"loop stop dt   : {loop_watchdog.stop_dt:.3f} s")
        print(f"home reset q   : {np.round(np.degrees(home_q), 3)} deg")
        print("home reset key : h")
        print(f"camera enable  : {args.camera_enable or args.record_enable}")
        if args.camera_enable or args.record_enable:
            print(f"camera mode    : {args.camera_mode}")
            print(f"top serial     : {args.top_serial}")
            print(f"wrist serial   : {args.wrist_serial}")
            print(f"top config     : {args.top_camera_config}")
            print(f"wrist config   : {args.wrist_camera_config}")
            print(f"advanced config: {not args.no_advanced_config}")
            print(f"dataset image  : {args.dataset_width}x{args.dataset_height}")
            print(f"top crop       : {args.top_crop}")
            print(f"wrist crop     : {args.wrist_crop}")
            print(f"show cameras   : {args.show_cameras}")
            print(f"record enable  : {args.record_enable}")
            print(f"record freq    : {args.record_freq:.1f} Hz")
        print(f"gripper enable : {args.gripper_enable}")
        if args.gripper_enable:
            print(f"gripper ip     : {args.gripper_ip}:{args.gripper_port}")
            print(f"gripper motion : {args.gripper_motion_enable}")
            print(f"gripper mode   : {args.gripper_control_mode}")
            print(f"grip cmd mode  : {args.gripper_command_mode}")
            print(f"grip steps     : {np.round(args.gripper_step_values, 3)}")
            print(f"gripper widths : {args.gripper_open_width_mm:.1f} / {args.gripper_close_width_mm:.1f} mm")
            print(f"gripper force  : {args.gripper_force_n:.1f} N")
            print(f"record grip q  : {args.record_gripper_qpos_source}")
            print(f"record grip act: {args.record_gripper_action_source}")
        print("Initial q rad  :", q_current)
        print("Initial q deg  :", np.degrees(q_current))
        print("Initial TCP pos:", current_tcp_pos)
        print("-------------------------------------------")
        print("CTRL+C pour quitter.")
        print("-------------------------------------------\n")

        last_print = time.monotonic()
        last_loop_t = time.monotonic()
        next_t = time.monotonic()

        latched_target_pos = None
        latched_target_rot = None
        latched_gripper_cmd = initial_gripper_cmd
        last_hw_gripper_cmd = latched_gripper_cmd
        
        last_qvel = np.zeros(6, dtype=np.float64)
        last_space_press = 0.0
        manual_pause = False
        manual_pause_stop_sent = False
        reset_home_active = False

        while True:
            q_current = robot.get_joint_positions()
            qvel = robot.get_joint_velocities()
            
            # Estimer l'accélération (dérivée de la vitesse)
            now = time.monotonic()
            real_dt = now - last_loop_t
            if real_dt <= 1e-6 or real_dt > 0.5:
                real_dt = control_dt
            last_loop_t = now

            loop_watchdog_status = loop_watchdog.check(real_dt)
            
            qacc = (qvel - last_qvel) / real_dt
            last_qvel = qvel

            current_tcp_pos, current_tcp_rot, J = servo.kin.forward_and_jacobian(q_current)
            current_eef_quat = rot_to_quat_wxyz(current_tcp_rot)

            raw_target_pos, raw_target_rot, raw_gripper_cmd = ros_node.get_target()
            touch_target_age = ros_node.get_target_age_seconds()
            gripper_buttons = ros_node.get_gripper_buttons()

            if raw_target_pos is not None and raw_target_rot is not None:
                latched_target_pos = raw_target_pos
                latched_target_rot = raw_target_rot
                if (
                    touch_watchdog.stop_active
                    and touch_target_age is not None
                    and touch_target_age <= touch_watchdog.timeout
                ):
                    touch_watchdog.reset_stop()
                    ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)
                    print("[TOUCH WATCHDOG] Fresh target received. Teleop resumed.")

            if raw_gripper_cmd is not None:
                latched_gripper_cmd = float(raw_gripper_cmd)

            gripper_width_cmd = None
            gripper_actual_cmd = None
            if gripper is not None:
                if args.gripper_control_mode == "button":
                    gripper_width_cmd = gripper.set_button_direction(gripper_buttons)
                else:
                    gripper_should_update = (
                        gripper_buttons != 0
                        or abs(latched_gripper_cmd - last_hw_gripper_cmd) > 1e-3
                    )
                    if gripper_should_update:
                        gripper_width_cmd = gripper.set_command(latched_gripper_cmd)
                        last_hw_gripper_cmd = latched_gripper_cmd

                gripper_status_snapshot, _ = gripper.get_status_snapshot()
                if gripper_status_snapshot is not None:
                    gripper_actual_cmd = gripper.width_to_command(
                        gripper_status_snapshot.width_mm
                    )

            touch_watchdog_status = touch_watchdog.check_age(touch_target_age)

            latest_frames = None
            camera_error = None
            camera_frame_count = 0
            if camera_capture is not None:
                latest_frames, camera_error, camera_frame_count = camera_capture.get_latest()

            if recorder is not None and latest_frames is not None:
                recorded_gripper_qpos = latched_gripper_cmd
                if (
                    args.record_gripper_qpos_source == "actual_width"
                    and gripper_actual_cmd is not None
                ):
                    recorded_gripper_qpos = gripper_actual_cmd

                recorded_gripper_action = latched_gripper_cmd
                if args.record_gripper_action_source == "actual_width":
                    if gripper_actual_cmd is not None:
                        recorded_gripper_action = gripper_actual_cmd
                elif args.record_gripper_action_source == "button_target":
                    if args.gripper_control_mode == "button":
                        if gripper_buttons > 0:
                            recorded_gripper_action = -0.2
                        elif gripper_buttons < 0:
                            recorded_gripper_action = 1.2
                        elif gripper_actual_cmd is not None:
                            recorded_gripper_action = gripper_actual_cmd

                target_pos_for_record = (
                    latched_target_pos
                    if latched_target_pos is not None
                    else current_tcp_pos
                )
                target_rot_for_record = (
                    latched_target_rot
                    if latched_target_rot is not None
                    else current_tcp_rot
                )
                robot_state = {
                    "eef_pos": current_tcp_pos.astype(np.float32),
                    "eef_quat": current_eef_quat.astype(np.float32),
                    "gripper_qpos": np.array(
                        [recorded_gripper_qpos],
                        dtype=np.float32,
                    ),
                }
                recorder.record_if_needed(
                    robot_state=robot_state,
                    top_down_rgb=latest_frames.top_rgb,
                    wrist_rgb=latest_frames.wrist_rgb,
                    target_pos=target_pos_for_record,
                    target_quat=rot_to_quat_wxyz(target_rot_for_record),
                    gripper_cmd=recorded_gripper_action,
                    timestamp=latest_frames.timestamp,
                )

            if args.show_cameras and latest_frames is not None:
                top_display = draw_camera_overlay(
                    latest_frames.top_display_bgr,
                    "top_down",
                    bool(recorder is not None and recorder.is_recording),
                    manual_pause,
                    reset_home_active,
                    len(recorder) if recorder is not None else 0,
                    saved_episodes,
                )
                wrist_display = draw_camera_overlay(
                    latest_frames.wrist_display_bgr,
                    "wrist",
                    bool(recorder is not None and recorder.is_recording),
                    manual_pause,
                    reset_home_active,
                    len(recorder) if recorder is not None else 0,
                    saved_episodes,
                )
                cv2.imshow("real top_down camera", top_display)
                cv2.imshow("real wrist camera", wrist_display)

                key = cv2.waitKey(1) & 0xFF
                now_key = time.monotonic()

                if key in (ord("q"), 27):
                    print("[INFO] Camera window requested quit.")
                    break

                if key == ord("p"):
                    if recorder is not None and recorder.is_recording:
                        print("[PAUSE] Stop recording with space before pausing the robot.")
                    elif reset_home_active:
                        print("[PAUSE] Home reset is active. Press h to cancel it first.")
                    else:
                        manual_pause = not manual_pause
                        manual_pause_stop_sent = False
                        if manual_pause:
                            print("[PAUSE] Robot command stream paused. Try tablet/manual reset now.")
                        else:
                            ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)
                            latched_target_pos = current_tcp_pos.copy()
                            latched_target_rot = current_tcp_rot.copy()
                            print("[PAUSE] Robot command stream resumed. Target synced to current pose.")

                if key == ord("h"):
                    if recorder is not None and recorder.is_recording:
                        print("[HOME] Stop recording with space before returning home.")
                    else:
                        reset_home_active = not reset_home_active
                        manual_pause = False
                        manual_pause_stop_sent = False
                        if reset_home_active:
                            initial_width_mm = (
                                args.gripper_open_width_mm
                                if args.initial_gripper_width_mm is None
                                else args.initial_gripper_width_mm
                            )
                            if gripper is not None:
                                home_gripper_width = gripper.request_width(initial_width_mm)
                                latched_gripper_cmd = gripper.width_to_command(home_gripper_width)
                            else:
                                home_gripper_width = initial_width_mm
                                latched_gripper_cmd = initial_gripper_cmd
                            last_hw_gripper_cmd = latched_gripper_cmd
                            if gripper is not None:
                                print(
                                    f"[HOME] Gripper moving to "
                                    f"{home_gripper_width:.1f} mm."
                                )
                            print("[HOME] Returning slowly to startup q. Press h again to cancel.")
                        else:
                            robot.stop()
                            ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)
                            latched_target_pos = current_tcp_pos.copy()
                            latched_target_rot = current_tcp_rot.copy()
                            print("[HOME] Home reset cancelled. Target synced to current pose.")

                if key == 32 and recorder is not None and now_key - last_space_press > 0.5:
                    if recorder.is_recording:
                        recorder.stop()
                        episode_np = recorder.to_numpy()
                        if episode_np is None:
                            print("[REC] Empty episode, not saved.")
                        elif len(recorder) < args.min_episode_steps:
                            print(
                                f"[REC] Episode too short ({len(recorder)} steps), "
                                "not saved."
                            )
                            recorder.cancel()
                        else:
                            if dataset_writer is None:
                                dataset_writer = RealZarrEpisodeWriter(dataset_path)
                            saved_episodes = dataset_writer.add_episode(episode_np)
                            print(
                                f"[REC] Saved episode with {len(recorder)} steps. "
                                f"Total episodes: {saved_episodes}"
                            )
                    else:
                        recorder.start()
                    last_space_press = now_key

                if key in (8, 127) and recorder is not None:
                    recorder.cancel()

            if manual_pause:
                if not manual_pause_stop_sent:
                    robot.stop()
                    manual_pause_stop_sent = True
                    ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)
                    latched_target_pos = current_tcp_pos.copy()
                    latched_target_rot = current_tcp_rot.copy()

                if time.monotonic() - last_print > args.print_period:
                    print("[PAUSE] No robot velocity command is being sent.")
                    print("current tcp   :", np.round(current_tcp_pos, 4))
                    print("Use p again to resume.")
                    print("-" * 60)
                    last_print = time.monotonic()

            elif safety_stop_triggered:
                robot.stop()
                ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)

                if time.monotonic() - last_print > args.print_period:
                    print(f"[SAFETY STOP] {safety_stop_reason}")
                    print("Robot stopped. Target synced to current TCP pose.")
                    print("-" * 60)
                    last_print = time.monotonic()

            elif loop_watchdog_status.should_stop:
                robot.stop()
                ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)
                latched_target_pos = current_tcp_pos.copy()
                latched_target_rot = current_tcp_rot.copy()

                if time.monotonic() - last_print > args.print_period:
                    print(f"[LOOP WATCHDOG STOP] {loop_watchdog_status.reason}")
                    print("Robot stopped. Target synced to current TCP pose.")
                    print("-" * 60)
                    last_print = time.monotonic()

            elif reset_home_active:
                q_err_home = home_q - q_current
                max_home_err_deg = float(np.degrees(np.max(np.abs(q_err_home))))

                if max_home_err_deg <= args.home_reset_threshold_deg:
                    robot.stop()
                    reset_home_active = False
                    ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)
                    latched_target_pos = current_tcp_pos.copy()
                    latched_target_rot = current_tcp_rot.copy()
                    print(f"[HOME] Reached startup q within {max_home_err_deg:.3f} deg.")
                    print("[HOME] Target synced to current pose.")
                    print("-" * 60)
                else:
                    qd_home = args.home_reset_kp * q_err_home
                    max_home_vel = abs(float(args.home_reset_max_joint_vel))
                    qd_home = np.clip(qd_home, -max_home_vel, max_home_vel)

                    robot.apply_joint_velocity(
                        qd_target=qd_home,
                        gripper_command=latched_gripper_cmd,
                    )

                    if time.monotonic() - last_print > args.print_period:
                        print("[HOME] Returning to startup q.")
                        print("max q err deg :", round(max_home_err_deg, 3))
                        print("qd_home rad/s :", np.round(qd_home, 4))
                        print("current q deg :", np.round(np.degrees(q_current), 3))
                        print("home q deg    :", np.round(np.degrees(home_q), 3))
                        print("-" * 60)
                        last_print = time.monotonic()

            elif touch_watchdog_status.should_stop:
                robot.stop()
                ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)
                latched_target_pos = current_tcp_pos.copy()
                latched_target_rot = current_tcp_rot.copy()

                if time.monotonic() - last_print > args.print_period:
                    print(f"[TOUCH WATCHDOG STOP] {touch_watchdog_status.reason}")
                    print("Robot stopped. Target synced to current TCP pose.")
                    print("-" * 60)
                    last_print = time.monotonic()

            elif latched_target_pos is None or latched_target_rot is None:
                # Pas encore de target Touch : on garde la pose actuelle.
                ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)

                if time.monotonic() - last_print > args.print_period:
                    print("[WAITING] No Touch target yet.")
                    print("current q deg :", np.round(np.degrees(q_current), 3))
                    print("current tcp   :", np.round(current_tcp_pos, 4))
                    print("-" * 60)
                    last_print = time.monotonic()

            else:
                pos_err = latched_target_pos - current_tcp_pos
                rot_err = orientation_error(latched_target_rot, current_tcp_rot)

                pos_err_norm = float(np.linalg.norm(pos_err))
                rot_err_norm = float(np.linalg.norm(rot_err))
                
                safety_res = safety_checker.check_loop(qvel=qvel, qacc=qacc, J=J)

                if pos_err_norm > SAFETY_POS_ERROR_STOP or rot_err_norm > SAFETY_ROT_ERROR_STOP:
                    safety_stop_triggered = True
                    safety_stop_reason = (
                        f"touch/robot error too large: "
                        f"pos={pos_err_norm:.3f} m, rot={rot_err_norm:.3f} rad"
                    )

                    robot.stop()
                    ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)

                    print(f"[SAFETY STOP] {safety_stop_reason}")
                    print("-" * 60)

                elif safety_res["status"] == "stop":
                    safety_stop_triggered = True
                    safety_stop_reason = f"SafetyChecker bounds exceeded: {safety_res['reason']} (cond={safety_res['metrics'].get('cond', 0):.1f})"

                    robot.stop()
                    ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)

                    print(f"[SAFETY STOP] {safety_stop_reason}")
                    print("-" * 60)

                else:
                    q_target, servo_info = servo.compute(
                        q_current=q_current,
                        target_pos=latched_target_pos,
                        target_rot=latched_target_rot,
                        dt=real_dt,
                    )

                    if args.backend == "speedj":
                        robot.apply_joint_velocity(
                            qd_target=servo_info["dq"],
                            gripper_command=latched_gripper_cmd,
                        )
                    else:
                        robot.apply_joint_command(
                            q_target=q_target,
                            gripper_command=latched_gripper_cmd,
                        )

                    if time.monotonic() - last_print > args.print_period:
                        print("target_pos     :", np.round(latched_target_pos, 4))
                        print("current_tcp_pos:", np.round(current_tcp_pos, 4))
                        print("pin_pos_err    :", np.round(servo_info["pos_err"], 4))
                        print("pin_rot_err    :", np.round(servo_info["rot_err"], 4))
                        print("pin_dq         :", np.round(servo_info["dq"], 5))
                        print("delta_q        :", np.round(q_target - q_current, 5))
                        print("q_current deg  :", np.round(np.degrees(q_current), 3))
                        print("q_target deg   :", np.round(np.degrees(q_target), 3))
                        print("qvel rad/s     :", np.round(qvel, 4))
                        print("cond           :", round(safety_res['metrics'].get('cond', 0.0), 3))
                        if loop_watchdog_status.status == "warn":
                            print("loop watchdog  :", loop_watchdog_status.reason)
                        print("gripper        :", latched_gripper_cmd)
                        if camera_capture is not None:
                            print("camera frames  :", camera_frame_count)
                            if camera_error is not None:
                                print("camera error   :", camera_error)
                        if recorder is not None:
                            print(
                                "recording      :",
                                recorder.is_recording,
                                "steps=",
                                len(recorder),
                                "saved=",
                                saved_episodes,
                            )
                        if gripper is not None:
                            gripper_status, gripper_error = gripper.get_status_snapshot()
                            print(
                                "gripper width  :",
                                None if gripper_width_cmd is None else round(gripper_width_cmd, 2),
                            )
                            if gripper_status is not None:
                                print(
                                    "gripper actual :",
                                    round(gripper_status.width_mm, 2),
                                    "busy=",
                                    gripper_status.busy,
                                    "grip_det=",
                                    gripper_status.grip_det,
                                )
                            if gripper_error is not None:
                                print("gripper error  :", gripper_error)
                        print("-" * 60)
                        last_print = time.monotonic()

            next_t += control_dt
            sleep_time = next_t - time.monotonic()

            if sleep_time > 0.0:
                time.sleep(sleep_time)
            else:
                next_t = time.monotonic()

    except KeyboardInterrupt:
        print("\nArrêt demandé par CTRL+C.")

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
            if camera_capture is not None:
                camera_capture.stop()
        except Exception:
            pass

        try:
            robot.close()
        except Exception:
            pass

        try:
            ros_node.destroy_node()
        except Exception:
            pass

        try:
            rclpy.shutdown()
        except Exception:
            pass

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

        print("Fin du script real teleop.")


if __name__ == "__main__":
    main()

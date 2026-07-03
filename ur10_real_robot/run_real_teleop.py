#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import threading
import time

import numpy as np
import rclpy
from rclpy.node import Node

from dp_mujoco.policy_exec.pose_utils import orientation_error
from dp_mujoco.policy_exec.servo_controller_pinocchio import PinocchioServoController

from ur10_real_robot.teleop.real_teleop_target_listener import RealTeleopTargetListener
from ur10_real_robot.backends.onrobot_gripper import AsyncOnRobotGripperController
from ur10_real_robot.backends.fake_robot_backend import FakeRobotBackend
from ur10_real_robot.backends.ur10_speedj_backend import UR10SpeedjBackend
from ur10_real_robot.safety.safety_config import SafetyConfig, SafetyChecker
from ur10_real_robot.safety.watchdog import ControlLoopWatchdog, TouchTargetWatchdog

"""
ROBOT_IP=192.168.2.100 REAL_BACKEND=speedj ENABLE_MOTION=1 \                                                                                       1 err | mujoco_ros py 
TCP_OFFSET="0 0 0.022" \
GRIPPER_ENABLE=1 GRIPPER_MOTION_ENABLE=1 \
GRIPPER_CONTROL_MODE=button \
GRIPPER_OPEN_WIDTH_MM=85 GRIPPER_CLOSE_WIDTH_MM=30 GRIPPER_FORCE_N=8 \
TOUCH_AXIS_MAP=swap_xy_neg_y \
TOUCH_ROT_MAP=same_as_position TOUCH_ROT_APPLY=world TOUCH_ROT_METHOD=matrix \
KP_POS=0.40 KP_ROT=0.20 \
MAX_JOINT_VEL=0.10 \
POSITION_SCALE=0.50 MAX_TARGET_SPEED=0.08 \
ALPHA_DQ=0.03 SPEEDJ_A=0.04 \
./ur10_real_robot/run_teleop.sh

"""





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

    return parser


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

        q_current = robot.get_joint_positions()
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
        print(f"gripper enable : {args.gripper_enable}")
        if args.gripper_enable:
            print(f"gripper ip     : {args.gripper_ip}:{args.gripper_port}")
            print(f"gripper motion : {args.gripper_motion_enable}")
            print(f"gripper mode   : {args.gripper_control_mode}")
            print(f"gripper widths : {args.gripper_open_width_mm:.1f} / {args.gripper_close_width_mm:.1f} mm")
            print(f"gripper force  : {args.gripper_force_n:.1f} N")
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
        latched_gripper_cmd = -0.2
        last_hw_gripper_cmd = latched_gripper_cmd
        
        last_qvel = np.zeros(6, dtype=np.float64)

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

            touch_watchdog_status = touch_watchdog.check_age(touch_target_age)

            if safety_stop_triggered:
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

        print("Fin du script real teleop.")


if __name__ == "__main__":
    main()

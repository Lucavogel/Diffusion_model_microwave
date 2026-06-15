#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import threading
import time

import numpy as np
import rclpy
from rclpy.node import Node

from dp_mujoco.policy_exec.pose_utils import orientation_error
from dp_mujoco.policy_exec.servo_controller_pinocchio import PinocchioServoController

from ur10_real_robot.teleop.real_teleop_target_listener import RealTeleopTargetListener
from ur10_real_robot.backends.fake_robot_backend import FakeRobotBackend


URDF_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "dp_mujoco/models/universal_robots_ur10e/ur10.urdf"
)


def ros_spin_thread(node: Node) -> None:
    rclpy.spin(node)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

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
        default=[0.0, 0.0, 0.24],
        help="TCP offset from tool0 in tool0 frame.",
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
        "--print-period",
        type=float,
        default=0.5,
        help="Debug print period in seconds.",
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
    )

    ros_thread = threading.Thread(
        target=ros_spin_thread,
        args=(ros_node,),
        daemon=True,
    )
    ros_thread.start()

    # Pour l'instant : backend fake.
    # Plus tard on remplacera seulement cette classe par URX / RTDE / ROS driver.
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

    safety_stop_triggered = False
    safety_stop_reason = ""

    SAFETY_POS_ERROR_STOP = 0.15
    SAFETY_ROT_ERROR_STOP = 0.60
    SAFETY_QVEL_STOP = 1.2
    SAFETY_COND_STOP = 1000.0

    try:
        robot.connect()

        q_current = robot.get_joint_positions()

        servo = PinocchioServoController(
            urdf_path=args.urdf,
            home_q=q_current,
            ee_frame_name="tool0",
            tcp_offset_pos=np.array(args.tcp_offset, dtype=np.float64),

            # Important :
            # Sur robot réel, pas de socle MuJoCo à z=0.4.
            base_offset_pos=np.array([0.0, 0.0, 0.0], dtype=np.float64),

            kp_pos=args.kp_pos,
            kp_rot=args.kp_rot,
            damping=args.damping,
            max_joint_vel=args.max_joint_vel,
            alpha_dq=args.alpha_dq,
        )

        # Optionnel pour que FakeRobotBackend puisse retourner eef_pos/eef_quat.
        robot.kinematics = servo.kin

        current_tcp_pos, current_tcp_rot, _ = servo.kin.forward_and_jacobian(q_current)

        ros_node.set_robot_reference(
            pos=current_tcp_pos,
            rot=current_tcp_rot,
        )

        servo.reset(q_current)

        print("\n-------------------------------------------")
        print("REAL TELEOP DRY-RUN")
        print("-------------------------------------------")
        print("Backend        : FakeRobotBackend")
        print("Motion         : aucun vrai robot commandé")
        print(f"Control Hz     : {control_hz}")
        print(f"Control dt     : {control_dt:.4f} s")
        print(f"URDF           : {args.urdf}")
        print(f"TCP offset     : {np.array(args.tcp_offset, dtype=np.float64)}")
        print(f"kp_pos         : {args.kp_pos}")
        print(f"kp_rot         : {args.kp_rot}")
        print(f"damping        : {args.damping}")
        print(f"max_joint_vel  : {args.max_joint_vel}")
        print(f"alpha_dq       : {args.alpha_dq}")
        print("Initial q rad  :", q_current)
        print("Initial q deg  :", np.degrees(q_current))
        print("Initial TCP pos:", current_tcp_pos)
        print("-------------------------------------------")
        print("CTRL+C pour quitter.")
        print("-------------------------------------------\n")

        last_print = time.time()
        last_loop = time.time()

        latched_target_pos = None
        latched_target_rot = None
        latched_gripper_cmd = -0.2

        while True:
            loop_start = time.time()

            q_current = robot.get_joint_positions()
            qvel = robot.get_joint_velocities()

            current_tcp_pos, current_tcp_rot, _ = servo.kin.forward_and_jacobian(q_current)

            raw_target_pos, raw_target_rot, raw_gripper_cmd = ros_node.get_target()

            if raw_target_pos is not None and raw_target_rot is not None:
                latched_target_pos = raw_target_pos
                latched_target_rot = raw_target_rot

            if raw_gripper_cmd is not None:
                latched_gripper_cmd = float(raw_gripper_cmd)

            if safety_stop_triggered:
                robot.stop()
                ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)

                if time.time() - last_print > args.print_period:
                    print(f"[SAFETY STOP] {safety_stop_reason}")
                    print("Robot stopped. Target synced to current TCP pose.")
                    print("-" * 60)
                    last_print = time.time()

            elif latched_target_pos is None or latched_target_rot is None:
                # Pas encore de target Touch : on garde la pose actuelle.
                ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)

                if time.time() - last_print > args.print_period:
                    print("[WAITING] No Touch target yet.")
                    print("current q deg :", np.round(np.degrees(q_current), 3))
                    print("current tcp   :", np.round(current_tcp_pos, 4))
                    print("-" * 60)
                    last_print = time.time()

            else:
                pos_err = latched_target_pos - current_tcp_pos
                rot_err = orientation_error(latched_target_rot, current_tcp_rot)

                pos_err_norm = float(np.linalg.norm(pos_err))
                rot_err_norm = float(np.linalg.norm(rot_err))

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

                elif float(np.max(np.abs(qvel))) > SAFETY_QVEL_STOP:
                    safety_stop_triggered = True
                    safety_stop_reason = (
                        f"joint velocity too high: "
                        f"max_qvel={float(np.max(np.abs(qvel))):.3f} rad/s"
                    )

                    robot.stop()
                    ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)

                    print(f"[SAFETY STOP] {safety_stop_reason}")
                    print("-" * 60)

                else:
                    now = time.time()
                    dt = now - last_loop
                    last_loop = now

                    if dt <= 1e-6 or dt > 0.5:
                        dt = control_dt

                    q_target, servo_info = servo.compute(
                        q_current=q_current,
                        target_pos=latched_target_pos,
                        target_rot=latched_target_rot,
                        dt=dt,
                    )

                    cond = float(servo_info["cond"])

                    if cond > SAFETY_COND_STOP:
                        safety_stop_triggered = True
                        safety_stop_reason = f"Jacobian condition too high: cond={cond:.2f}"

                        robot.stop()
                        ros_node.sync_to_pose(current_tcp_pos, current_tcp_rot)

                        print(f"[SAFETY STOP] {safety_stop_reason}")
                        print("-" * 60)

                    else:
                        robot.apply_joint_command(
                            q_target=q_target,
                            gripper_command=latched_gripper_cmd,
                        )

                        if time.time() - last_print > args.print_period:
                            print("target_pos     :", np.round(latched_target_pos, 4))
                            print("current_tcp_pos:", np.round(current_tcp_pos, 4))
                            print("pin_pos_err    :", np.round(servo_info["pos_err"], 4))
                            print("pin_rot_err    :", np.round(servo_info["rot_err"], 4))
                            print("pin_dq         :", np.round(servo_info["dq"], 5))
                            print("delta_q        :", np.round(q_target - q_current, 5))
                            print("q_current deg  :", np.round(np.degrees(q_current), 3))
                            print("q_target deg   :", np.round(np.degrees(q_target), 3))
                            print("qvel rad/s     :", np.round(qvel, 4))
                            print("cond           :", round(cond, 3))
                            print("gripper        :", latched_gripper_cmd)
                            print("-" * 60)
                            last_print = time.time()

            elapsed = time.time() - loop_start
            sleep_time = control_dt - elapsed

            if sleep_time > 0.0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nArrêt demandé par CTRL+C.")

    finally:
        try:
            robot.stop()
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

        print("Fin du script real teleop dry-run.")


if __name__ == "__main__":
    main()
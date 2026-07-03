#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import threading
import time
import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../diffusion_policy")
    )
)

try:
    from diffusion_policy.common.replay_buffer import ReplayBuffer
except ImportError:
    print(
        "Avertissement : Le module ReplayBuffer n'est pas trouvé. "
        "Assurez-vous d'avoir zarr installé dans votre environnement conda/venv."
    )
    ReplayBuffer = None

import cv2
import mujoco
import mujoco.viewer
import numpy as np
import rclpy
from rclpy.node import Node

from dp_mujoco.env.scene_utils import randomize_microwave_objects
from dp_mujoco.policy_exec.pose_utils import orientation_error
from dp_mujoco.teleop.teleop_target_listener import TeleopTargetListener

from dp_mujoco.env.mujoco_env import MujocoEnv
from dp_mujoco.teleop.teleop_episode_recorder import TeleopEpisodeRecorder

from dp_mujoco.utils.safety_config import SafetyChecker, SafetyConfig
from dp_mujoco.policy_exec.servo_controller_pinocchio import PinocchioServoController


MODEL_PATH = Path(
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "dp_mujoco/models/universal_robots_ur10e/scene_microwave_camera.xml"
)

URDF_PATH = (
    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
    "dp_mujoco/models/universal_robots_ur10e/ur10_d455_support_rg2ft_fixed_gripper.urdf"
)


def ros_spin_thread(node: Node) -> None:
    rclpy.spin(node)


def make_safety_checker(home_q: np.ndarray) -> SafetyChecker:
    safety_config = SafetyConfig(
        velocity_stop_threshold=1.2,
        acceleration_stop_threshold=80.0,
        acceleration_emergency_threshold=150.0,
        acceleration_filter_window=5,
        acceleration_emergency_consecutive=3,
        cond_threshold_stop=1000.0,
        manip_threshold_stop=1e-6,
        consecutive_stop_count=20,
        consecutive_recover_count=10,
        metrics_history_size=200,
    )

    return SafetyChecker(config=safety_config, q=home_q)


def hard_reset_robot(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    env: MujocoEnv,
    home_q: np.ndarray,
    gripper_q: float = -0.2,
    settle_steps: int = 50,
) -> None:
    env.reset(home_q=home_q, gripper_q=gripper_q)

    data.qpos[:6] = home_q
    data.qvel[:] = 0.0
    data.ctrl[:6] = home_q
    if model.nu >= 7:
        data.ctrl[6] = gripper_q

    mujoco.mj_forward(model, data)

    for _ in range(settle_steps):
        data.ctrl[:6] = home_q
        if model.nu >= 7:
            data.ctrl[6] = gripper_q
        mujoco.mj_step(model, data)

    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)


def main() -> None:
    rclpy.init()

    ros_node = TeleopTargetListener()
    thread = threading.Thread(target=ros_spin_thread, args=(ros_node,), daemon=True)
    thread.start()

    env = MujocoEnv(
        model_xml=MODEL_PATH,
        camera_agentview="top_table",
        camera_wrist="wrist_cam",
        render_width=640,
        render_height=480,
    )

    model = env.model
    data = env.data

    home_q = np.array(
        [0.0, -1.3, 1.8, -0.22, 1.57, 0.0],
        dtype=np.float64,
    )

    hard_reset_robot(
        model=model,
        data=data,
        env=env,
        home_q=home_q,
        gripper_q=-0.2,
    )
    q_before = data.qpos[:6].copy()

    for _ in range(300):
        data.ctrl[:6] = home_q
        if model.nu >= 7:
            data.ctrl[6] = -0.2
        mujoco.mj_step(model, data)

    q_after = data.qpos[:6].copy()

    print("SAG TEST")
    print("q_before:", q_before)
    print("q_after :", q_after)
    print("diff    :", q_after - q_before)

    servo = PinocchioServoController(
        urdf_path=URDF_PATH,
        home_q=home_q,
        ee_frame_name="tool0",
        tcp_offset_pos=np.array([0.0, 0.0, 0.24], dtype=np.float64),
        base_offset_pos=np.array([0.0, 0.0, 0.4], dtype=np.float64),
        joint_min=env.joint_min,
        joint_max=env.joint_max,
        kp_pos=5.0,
        kp_rot=2.0,
        damping=0.05,
        max_joint_vel=0.8,
        alpha_dq=0.25,
    )

    mujoco_start_pos = env.get_eef_pos()

    pin_start_pos, pin_start_rot, pin_J = servo.kin.forward_and_jacobian(home_q)

    print("START mujoco grasp_pos :", mujoco_start_pos)
    print("START pinocchio tcp_pos:", pin_start_pos)
    print("START diff mujoco-pin  :", mujoco_start_pos - pin_start_pos)

    servo.reset(home_q)

    safety_checker = make_safety_checker(home_q)

    q_hold = home_q.copy()
    gripper_hold = -0.2
    smooth_gripper_cmd = -0.2

    randomize_microwave_objects(model, data)
    mujoco.mj_forward(model, data)

    safety_stop_triggered = False
    safety_stop_reason = ""

    SAFETY_POS_ERROR_STOP = 0.25
    SAFETY_ROT_ERROR_STOP = 0.80

    dt = float(model.opt.timestep)
    print(f"Simulation timestep (dt) : {dt:.4f} s")

    viewer = None
    renderer_front = None
    renderer_top = None

    if ros_node.free_camera_flag:
        viewer = mujoco.viewer.launch_passive(model, data)
    else:
        width = 640
        height = 480
        renderer_front = mujoco.Renderer(model, height=height, width=width)
        renderer_top = mujoco.Renderer(model, height=height, width=width)

    recorder = TeleopEpisodeRecorder(record_freq=10.0)

    dataset_path = None
    replay_buffer = None

    saved_episodes_total = 0
    saved_episodes_session = 0

    APPEND_TO_LATEST = False

    try:
        repo_root = Path(__file__).resolve().parents[2]
        datasets_dir = repo_root / "data" / "datasets"

        if datasets_dir.exists():
            candidates = [
                p for p in datasets_dir.iterdir()
                if p.is_dir() and p.name.endswith(".zarr")
            ]

            if candidates:
                latest = max(candidates, key=lambda p: p.stat().st_mtime)
                latest_path = str(latest)

                if APPEND_TO_LATEST:
                    dataset_path = latest_path
                    print(f"[*] Reprise du dataset existant pre-selectionne : {dataset_path}")

                try:
                    if ReplayBuffer is not None:
                        rb_temp = ReplayBuffer.create_from_path(latest_path, mode="r")
                        saved_episodes_total = int(rb_temp.n_episodes)
                    else:
                        try:
                            import zarr as _zarr

                            g = _zarr.open(latest_path, mode="r")
                            if "meta" in g and "episode_ends" in g["meta"]:
                                ep = g["meta"]["episode_ends"]
                                saved_episodes_total = len(ep)
                        except Exception:
                            saved_episodes_total = 0
                except Exception:
                    saved_episodes_total = 0

    except Exception:
        pass

    print("\n-------------------------------------------")
    print("Contrôles clavier (en mode OpenCV uniquement):")
    print("ESPACE  : Démarrer/Arrêter l'enregistrement")
    print("SUPPR   : Annuler la trajectoire en cours")
    print("R       : Réinitialiser la simulation au point de départ")
    print("ECHAP   : Quitter programme")
    print("-------------------------------------------\n")

    try:
        last_print = time.time()
        last_render = time.time()
        last_space_press = 0.0
        prev_sim_time = data.time

        render_hz = 60.0
        render_period = 1.0 / render_hz

        control_hz = 10.0
        control_period = 1.0 / control_hz
        last_control_time = time.time()

        latched_target_pos = None
        latched_target_rot = None
        latched_gripper_cmd = -0.2

        try:
            print(f"model.nv={model.nv}, model.nu={model.nu}")
        except Exception:
            pass

        while True:
            if viewer is not None and not viewer.is_running():
                break

            if data.time < prev_sim_time:
                mujoco.mj_resetData(model, data)

                hard_reset_robot(
                    model=model,
                    data=data,
                    env=env,
                    home_q=home_q,
                    gripper_q=-0.2,
                )

                servo.reset(home_q)
                safety_checker = make_safety_checker(home_q)

                q_hold = home_q.copy()
                gripper_hold = -0.2
                smooth_gripper_cmd = -0.2

                latched_target_pos = None
                latched_target_rot = None
                latched_gripper_cmd = -0.2
                last_control_time = time.time()

                safety_stop_triggered = False
                safety_stop_reason = ""

                try:
                    ros_node.reset_after_sim_reset()
                except Exception:
                    pass

                randomize_microwave_objects(model, data)
                mujoco.mj_forward(model, data)

                print(">>> RESET MUJOCO DÉTECTÉ AVEC VARIATION DES OBJETS <<<")

            prev_sim_time = data.time

            step_start = time.time()

            now_control = time.time()

            if now_control - last_control_time >= control_period:
                raw_target_pos, raw_target_rot, raw_gripper_cmd = ros_node.get_target()

                latched_target_pos = raw_target_pos
                latched_target_rot = raw_target_rot

                if raw_gripper_cmd is not None:
                    latched_gripper_cmd = float(raw_gripper_cmd)

                last_control_time = now_control

            if safety_stop_triggered:
                if time.time() - last_print > 0.5:
                    print(f"[SAFETY STOP] {safety_stop_reason}")
                    last_print = time.time()

            elif latched_target_pos is None or latched_target_rot is None:
                pass

            else:
                grasp_pos = env.get_eef_pos()
                R_current = env.get_eef_rot()

                pos_err = latched_target_pos - grasp_pos
                rot_err = orientation_error(latched_target_rot, R_current)

                pos_err_norm = float(np.linalg.norm(pos_err))
                rot_err_norm = float(np.linalg.norm(rot_err))

                if pos_err_norm > SAFETY_POS_ERROR_STOP or rot_err_norm > SAFETY_ROT_ERROR_STOP:
                    safety_stop_triggered = True
                    safety_stop_reason = (
                        f"touch/robot error too large: pos={pos_err_norm:.3f} m, "
                        f"rot={rot_err_norm:.3f} rad"
                    )

                    if recorder.is_recording:
                        recorder.cancel()

                    print(f"[SAFETY STOP] {safety_stop_reason}")
                    last_print = time.time()

                else:
                    q_current = data.qpos[:6].copy()

                    q_target_candidate, servo_info = servo.compute(
                        q_current=q_current,
                        target_pos=latched_target_pos,
                        target_rot=latched_target_rot,
                        dt=dt,
                    )

                    smooth_gripper_cmd_candidate = float(
                        np.clip(latched_gripper_cmd, -0.2, 1.2)
                    )

                    J = servo_info.get("J", None)

                    if data.qvel is not None and data.qvel.size >= 6:
                        qvel = data.qvel[:6].copy()
                    else:
                        qvel = None

                    if data.qacc is not None and data.qacc.size >= 6:
                        qacc = data.qacc[:6].copy()
                    else:
                        qacc = None

                    safety_result = safety_checker.check_loop(
                        qvel=qvel,
                        qacc=qacc,
                        J=J,
                    )

                    if safety_result["status"] == "stop":
                        safety_stop_triggered = True
                        safety_stop_reason = (
                            f"SafetyChecker stop: {safety_result['reason']} | "
                            f"metrics={safety_result['metrics']}"
                        )

                        if recorder.is_recording:
                            recorder.cancel()

                        print(f"[SAFETY STOP] {safety_stop_reason}")
                        last_print = time.time()

                    else:
                        q_target = q_target_candidate
                        smooth_gripper_cmd = smooth_gripper_cmd_candidate

                        q_hold = q_target.copy()
                        gripper_hold = smooth_gripper_cmd

                        if time.time() - last_print > 0.5:
                            print(f"target_pos      : {latched_target_pos}")
                            print(f"mujoco_grasp_pos: {grasp_pos}")
                            print(f"pin_current_pos : {servo_info['current_pos']}")
                            print(f"pin_pos_err     : {servo_info['pos_err']}")
                            print(f"pin_rot_err     : {servo_info['rot_err']}")
                            print(f"pin_cond        : {servo_info['cond']}")
                            print(f"gripper         : {smooth_gripper_cmd}")
                            print(f"safety          : {safety_result['reason']}")
                            print(f"metrics         : {safety_result['metrics']}")
                            print(f"pin_dq          : {servo_info['dq']}")
                            print(f"delta_q         : {q_target_candidate - q_current}")

                            try:
                                print(f"qpos[:6]  : {data.qpos[:6]}")
                                print(f"qvel[:6]  : {data.qvel[:6]}")
                                print(f"qacc[:6]  : {data.qacc[:6]}")
                                nu_shown = min(int(model.nu), 8)
                                print(f"ctrl[:{nu_shown}] : {data.ctrl[:nu_shown]}")
                            except Exception:
                                pass

                            print("-" * 60)
                            last_print = time.time()

            env.apply_joint_command(q_hold, gripper_command=gripper_hold)
            env.step()

            now = time.time()

            if now - last_render >= render_period:
                if viewer is not None:
                    viewer.sync()

                else:
                    renderer_front.update_scene(data, camera="wrist_cam")
                    img_front = renderer_front.render()

                    renderer_top.update_scene(data, camera="top_table")
                    img_top = renderer_top.render()

                    img_front = cv2.cvtColor(img_front, cv2.COLOR_RGB2BGR)
                    img_top = cv2.cvtColor(img_top, cv2.COLOR_RGB2BGR)

                    cv2.putText(
                        img_front,
                        "Eye_in_hand",
                        (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (20, 20, 20),
                        2,
                        cv2.LINE_AA,
                    )

                    cv2.putText(
                        img_top,
                        "Eye_to_hand",
                        (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (20, 20, 20),
                        2,
                        cv2.LINE_AA,
                    )

                    try:
                        cv2.putText(
                            img_front,
                            f"SAVED: {saved_episodes_total} (+{saved_episodes_session})",
                            (20, 65),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 255),
                            2,
                            cv2.LINE_AA,
                        )
                    except Exception:
                        pass

                    try:
                        cv2.putText(
                            img_top,
                            f"SAVED: {saved_episodes_total} (+{saved_episodes_session})",
                            (20, 65),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 255),
                            2,
                            cv2.LINE_AA,
                        )
                    except Exception:
                        pass

                    if recorder.is_recording:
                        cv2.circle(img_front, (600, 40), 10, (0, 0, 255), -1)
                        cv2.putText(
                            img_front,
                            "REC",
                            (550, 45),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 255),
                            2,
                            cv2.LINE_AA,
                        )

                    cv2.imshow("Eye_in_hand", img_front)
                    cv2.imshow("Eye_to_hand", img_top)

                    key = cv2.waitKey(1) & 0xFF

                    if key == 27:
                        break

                    elif key == 32:
                        if time.time() - last_space_press > 0.5:
                            if not recorder.is_recording:
                                recorder.start()

                            else:
                                recorder.stop()
                                episode_np = recorder.to_numpy()

                                if episode_np is not None:
                                    if ReplayBuffer is not None:
                                        if replay_buffer is None:
                                            if dataset_path is None:
                                                timestamp = time.strftime("%Y%m%d_%H%M%S")
                                                dataset_path = (
                                                    "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/"
                                                    f"data/datasets/demo_data_{timestamp}.zarr"
                                                )
                                                print(f"Dataset cree: {dataset_path}")
                                            else:
                                                print(f"Dataset existant utilise : {dataset_path}")

                                            replay_buffer = ReplayBuffer.create_from_path(
                                                dataset_path,
                                                mode="a",
                                            )

                                        replay_buffer.add_episode(
                                            episode_np,
                                            compressors="disk",
                                        )

                                        try:
                                            saved_episodes_total = int(
                                                replay_buffer.n_episodes
                                            )
                                        except Exception:
                                            pass

                                        saved_episodes_session += 1

                                        print(
                                            f"Trajectoire enregistrée. "
                                            f"({len(recorder)} pas, "
                                            f"{saved_episodes_total} épisodes totaux "
                                            f"(+{saved_episodes_session} cette session))"
                                        )

                                    else:
                                        print("Erreur: pas de ReplayBuffer disponible.")

                                else:
                                    print(
                                        "Erreur : La trajectoire était vide, non sauvegardée."
                                    )

                            last_space_press = time.time()

                    elif key == 8 or key == 127:
                        if recorder.is_recording:
                            recorder.cancel()

                    elif key == ord("r"):
                        mujoco.mj_resetData(model, data)

                        hard_reset_robot(
                            model=model,
                            data=data,
                            env=env,
                            home_q=home_q,
                            gripper_q=-0.2,
                        )

                        servo.reset(home_q)
                        safety_checker = make_safety_checker(home_q)

                        q_hold = home_q.copy()
                        gripper_hold = -0.2
                        smooth_gripper_cmd = -0.2

                        latched_target_pos = None
                        latched_target_rot = None
                        latched_gripper_cmd = -0.2
                        last_control_time = time.time()

                        safety_stop_triggered = False
                        safety_stop_reason = ""

                        try:
                            ros_node.reset_after_sim_reset()
                        except Exception:
                            pass

                        randomize_microwave_objects(model, data)
                        mujoco.mj_forward(model, data)

                        print("\n>>> SIMULATION RÉINITIALISÉE AVEC VARIATION DES OBJETS ! <<<")

                        if recorder.is_recording:
                            print("[!] Enregistrement annulé car la simulation a été reset [!]")
                            recorder.cancel()

                if renderer_front is not None and renderer_top is not None:
                    recorder.record_if_needed(
                        env=env,
                        renderer_front=renderer_front,
                        renderer_top=renderer_top,
                        target_pos=latched_target_pos,
                        target_rot=latched_target_rot,
                        gripper_cmd=latched_gripper_cmd,
                    )

                last_render = time.time()

            elapsed = time.time() - step_start

            if elapsed < dt:
                time.sleep(dt - elapsed)

    except KeyboardInterrupt:
        print("Arrêt demandé.")

    finally:
        if viewer is not None:
            viewer.close()

        if not ros_node.free_camera_flag:
            cv2.destroyAllWindows()

        ros_node.destroy_node()
        rclpy.shutdown()

        print("Fin du script.")


if __name__ == "__main__":
    main()

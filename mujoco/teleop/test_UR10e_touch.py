#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import threading
import time
import sys
import os

# Ajout du chemin vers diffusion_policy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../diffusion_policy")))
try:
    from diffusion_policy.common.replay_buffer import ReplayBuffer
except ImportError:
    print("Avertissement : Le module ReplayBuffer n'est pas trouvé. Assurez-vous d'avoir zarr installé dans votre environnement conda/venv.")
    ReplayBuffer = None

import cv2
import mujoco
import mujoco.viewer
import numpy as np
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32, Int8
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from mujoco_scene_utils import randomize_microwave_objects, hide_free_body, show_free_body


MODEL_PATH = Path("/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_microwave_camera.xml")


def quat_to_rot(qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
    x, y, z, w = qx, qy, qz, qw
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z

    return np.array([
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz),       2.0 * (xz + wy)],
        [2.0 * (xy + wz),       1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
        [2.0 * (xz - wy),       2.0 * (yz + wx),       1.0 - 2.0 * (xx + yy)],
    ], dtype=float)


def rot_to_quat(R: np.ndarray) -> np.ndarray:
    trace = np.trace(R)
    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0
        qw = 0.25 * s
        qx = (R[2, 1] - R[1, 2]) / s
        qy = (R[0, 2] - R[2, 0]) / s
        qz = (R[1, 0] - R[0, 1]) / s
    else:
        if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
            qw = (R[2, 1] - R[1, 2]) / s
            qx = 0.25 * s
            qy = (R[0, 1] + R[1, 0]) / s
            qz = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
            qw = (R[0, 2] - R[2, 0]) / s
            qx = (R[0, 1] + R[1, 0]) / s
            qy = 0.25 * s
            qz = (R[1, 2] + R[2, 1]) / s
        else:
            s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
            qw = (R[1, 0] - R[0, 1]) / s
            qx = (R[0, 2] + R[2, 0]) / s
            qy = (R[1, 2] + R[2, 1]) / s
            qz = 0.25 * s

    q = np.array([qx, qy, qz, qw], dtype=float)
    q /= np.linalg.norm(q) + 1e-12
    return q


def orientation_error(R_target: np.ndarray, R_current: np.ndarray) -> np.ndarray:
    R_err = R_target @ R_current.T
    return 0.5 * np.array([
        R_err[2, 1] - R_err[1, 2],
        R_err[0, 2] - R_err[2, 0],
        R_err[1, 0] - R_err[0, 1],
    ], dtype=float)


class TeleopTargetListener(Node):
    def __init__(self) -> None:
        super().__init__("teleop_target_listener")

        self.free_camera_flag = False

        # Cible robot (calculée localement à partir des poses brutes du Touch)
        self.target_pos = None
        self.target_rot = None
        self.gripper_cmd = -0.2

        self.lock = threading.Lock()

        # Mapping touch -> target (reprise de la logique du node intermédiaire)
        self.position_scale = 0.4
        self.initial_robot_pos = np.array([0.929841, 0.174247, 0.696912], dtype=float)

        self.initial_robot_rot = np.array([
            [ -0.000765, 0.276356, 0.961055],
            [ 1.000000, 0.000000, 0.000796],
            [ 0.000220, 0.961055, -0.276356],
        ], dtype=float)


        self.prev_touch_pos = None
        self.prev_touch_rot = None
        self.touch_initialized = False

        # Gripper integration from /touch/buttons
        self.current_buttons = 0
        self.gripper_speed = 0.5
        self.gripper_value = -0.2
        self.last_gripper_time = self.get_clock().now()

        self.target_filter_alpha_pos = 0.2
        self.target_filter_alpha_rot = 0.15

        sensor_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.pose_sub = self.create_subscription(PoseStamped, "/touch/pose", self.pose_cb, sensor_qos)
        self.buttons_sub = self.create_subscription(Int8, "/touch/buttons", self.buttons_cb, sensor_qos)
        self.gripper_sub = self.create_subscription(Float32, "/teleop/gripper_cmd", self.gripper_cb, sensor_qos)

        # Timer pour intégration continue de la commande pince
        self.gripper_timer = self.create_timer(0.005, self.update_gripper)

    def reset_after_sim_reset(self) -> None:
        with self.lock:
            # reset pince
            self.current_buttons = 0
            self.gripper_value = -0.2
            self.gripper_cmd = -0.2
            self.last_gripper_time = self.get_clock().now()

            # reset référence téléop pour éviter un saut après reset
            self.target_pos = None
            self.target_rot = None
            self.prev_touch_pos = None
            self.prev_touch_rot = None
            self.touch_initialized = False

    def pose_cb(self, msg: PoseStamped) -> None:
        touch_pos = np.array([
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z,
        ], dtype=float)

        touch_rot = quat_to_rot(
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        )

        with self.lock:
            if not self.touch_initialized:
                # Initialisation de la référence (position robot au home)
                self.prev_touch_pos = touch_pos.copy()
                self.prev_touch_rot = touch_rot.copy()

                self.target_pos = self.initial_robot_pos.copy()
                self.target_rot = self.initial_robot_rot.copy()

                self.touch_initialized = True
                try:
                    self.get_logger().info("Première pose touch reçue : référence initialisée (robot à sa position intiale).")
                except Exception:
                    pass
                return

            # Différentiel de position
            dpos_touch = touch_pos - self.prev_touch_pos
            dpos_robot = self.position_scale * dpos_touch
            self.target_pos += dpos_robot

            # Différentiel de rotation (multiplicatif)
            delta_rot = touch_rot @ self.prev_touch_rot.T
            self.target_rot = delta_rot @ self.target_rot

            # Correction de la dérive numérique (orthogonalisation)
            U, _, Vt = np.linalg.svd(self.target_rot)
            self.target_rot = U @ Vt

            self.prev_touch_pos = touch_pos
            self.prev_touch_rot = touch_rot

    def gripper_cb(self, msg: Float32) -> None:
        with self.lock:
            # override direct si un autre node publie /teleop/gripper_cmd
            self.gripper_cmd = float(msg.data)
            self.gripper_value = float(msg.data)

    def buttons_cb(self, msg: Int8) -> None:
        with self.lock:
            self.current_buttons = int(msg.data)

    def update_gripper(self) -> None:
        with self.lock:
            now = self.get_clock().now()
            dt = (now - self.last_gripper_time).nanoseconds * 1e-9
            self.last_gripper_time = now

            if self.current_buttons == 1:
                self.gripper_value -= self.gripper_speed * dt   # ouvrir
            elif self.current_buttons == -1:
                self.gripper_value += self.gripper_speed * dt   # fermer

            self.gripper_value = max(-0.2, min(1.2, self.gripper_value))
            self.gripper_cmd = float(self.gripper_value)

    def get_target(self):
        with self.lock:
            if self.target_pos is None or self.target_rot is None:
                return None, None, float(self.gripper_cmd)
            return self.target_pos.copy(), self.target_rot.copy(), float(self.gripper_cmd)

    def sync_to_pose(self, pos: np.ndarray, rot: np.ndarray) -> None:
        with self.lock:
            if self.target_pos is not None and self.target_rot is not None:
                self.target_pos = pos.copy()
                self.target_rot = rot.copy()

    def progressive_sync(self, pos: np.ndarray, rot: np.ndarray, freeze_alpha: float = 0.15) -> None:
        with self.lock:
            if self.target_pos is not None and self.target_rot is not None:
                self.target_pos = (1.0 - freeze_alpha) * self.target_pos + freeze_alpha * pos
                R_blend = (1.0 - freeze_alpha) * self.target_rot + freeze_alpha * rot
                U, _, Vt = np.linalg.svd(R_blend)
                self.target_rot = U @ Vt


def ros_spin_thread(node: Node):
    rclpy.spin(node)


def main() -> None:
    rclpy.init()
    ros_node = TeleopTargetListener()
    thread = threading.Thread(target=ros_spin_thread, args=(ros_node,), daemon=True)
    thread.start()

    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)

    joint_min = np.empty(6, dtype=float)
    joint_max = np.empty(6, dtype=float)
    for i in range(6):
        joint_min[i] = model.jnt_range[i, 0]
        joint_max[i] = model.jnt_range[i, 1]

    home_q = np.array([0.0, -1.3, 1.8, -0.22, 1.57, 0.0], dtype=float)
    data.qpos[:6] = home_q
    data.ctrl[:6] = home_q

    if model.nu > 6:
        data.ctrl[6] = -0.2

    grasp_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "grasp_site")
    if grasp_site_id == -1:
        raise ValueError("Site 'grasp_site' introuvable.")

    randomize_microwave_objects(model, data)
    mujoco.mj_forward(model, data)

    q_target = home_q.copy()
    smooth_dq = np.zeros(6) # Mémoire du filtre passe-bas pour l'IK
    smooth_gripper_cmd = -0.2

    # Variables anti-blocage
    last_grasp_pos = None
    blocked_counter = 0

    # Gains ajustés pour éviter l'overshoot (oscillation continue)
    Kp_pos = 5.0
    Kp_rot = 3.0
    dt = model.opt.timestep

    viewer = None
    renderer_front = None
    renderer_top = None

    if ros_node.free_camera_flag:
        viewer = mujoco.viewer.launch_passive(model, data)
    else:
        WIDTH = 640
        HEIGHT = 480
        renderer_front = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)
        renderer_top = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)

    # ------------------
    # VARIABLES D'ENREGISTREMENT
    # ------------------
    is_recording = False
    record_freq = 10.0 # 10 Hz
    last_record_time = time.time()
    current_episode_data = {
        'agentview_image': [],
        'robot0_eye_in_hand_image': [],
        'robot0_eef_pos': [],
        'robot0_eef_quat': [],
        'robot0_gripper_qpos': [],
        'action': []
    }
    
    # Le dataset Zarr est cree uniquement lors du premier enregistrement valide.
    dataset_path = None
    replay_buffer = None
    # Compteur d'épisodes sauvegardés (affiché dans les fenêtres OpenCV)
    saved_episodes_total = 0
    saved_episodes_session = 0

    
    APPEND_TO_LATEST = False  # Met a False si tu veux forcer la creation d'un NOUVEAU dossier .zarr

    try:
        repo_root = Path(__file__).resolve().parents[2]
        datasets_dir = repo_root / "data" / "datasets"
        if datasets_dir.exists():
            candidates = [p for p in datasets_dir.iterdir() if p.is_dir() and p.name.endswith('.zarr')]
            if candidates:
                latest = max(candidates, key=lambda p: p.stat().st_mtime)
                latest_path = str(latest)
                if APPEND_TO_LATEST:
                    dataset_path = latest_path
                    print(f"[*] Reprise du dataset existant pre-selectionne : {dataset_path}")
                try:
                    if ReplayBuffer is not None:
                        rb_temp = ReplayBuffer.create_from_path(latest_path, mode='r')
                        saved_episodes_total = int(rb_temp.n_episodes)
                    else:
                        try:
                            import zarr as _zarr
                            g = _zarr.open(latest_path, mode='r')
                            if 'meta' in g and 'episode_ends' in g['meta']:
                                ep = g['meta']['episode_ends']
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
        last_space_press = 0.0 # Anti-rebond pour la touche ESPACE
        prev_sim_time = data.time

        render_hz = 60.0
        render_period = 1.0 / render_hz

        # Diagnostic initial: afficher quelques infos modèle/actuateurs
        try:
            print(f"model.nv={model.nv}, model.nu={model.nu}")
        except Exception:
            pass

        while True:
            if viewer is not None and not viewer.is_running():
                break

            # --- DÉTECTION DU RESET DU VIEWER MUJOCO (Touche Retour Arrière) ---
            if data.time < prev_sim_time:
                mujoco.mj_resetData(model, data)

                # reset robot
                data.qpos[:6] = home_q
                data.ctrl[:6] = home_q

                if model.nu > 6:
                    data.qpos[6] = -0.2
                    smooth_gripper_cmd = -0.2
                    data.ctrl[6] = -0.2

                q_target = home_q.copy()
                smooth_dq[:] = 0.0

                # reset du node ROS (pince et référence téléop)
                try:
                    ros_node.reset_after_sim_reset()
                except Exception:
                    pass

                # randomisation des objets
                randomize_microwave_objects(model, data)

                mujoco.mj_forward(model, data)

                print(">>> RESET MUJOCO DÉTECTÉ AVEC VARIATION DES OBJETS <<<")
            
            prev_sim_time = data.time

            step_start = time.time()

            target_pos, target_rot, gripper_cmd = ros_node.get_target()

            if target_pos is None:
                data.ctrl[:6] = home_q
                if model.nu > 6:
                    data.ctrl[6] = gripper_cmd
                    smooth_gripper_cmd = gripper_cmd

                mujoco.mj_step(model, data)
            else:
                grasp_pos = data.site_xpos[grasp_site_id].copy()
                R_current = data.site_xmat[grasp_site_id].reshape(3, 3).copy()

                pos_err = target_pos - grasp_pos
                rot_err = orientation_error(target_rot, R_current)

                POS_DEADZONE = 0.0025   # 2.5 mm
                ROT_DEADZONE = 0.03     # à ajuster

                if np.linalg.norm(pos_err) < POS_DEADZONE:
                    pos_err[:] = 0.0
                if np.linalg.norm(rot_err) < ROT_DEADZONE:
                    rot_err[:] = 0.0

                err = np.hstack([Kp_pos * pos_err, Kp_rot * rot_err])

                jacp = np.zeros((3, model.nv))
                jacr = np.zeros((3, model.nv))
                mujoco.mj_jacSite(model, data, jacp, jacr, grasp_site_id)

                J = np.vstack([jacp[:, :6], jacr[:, :6]])

                lambda2 = 5e-3
                JJt = J @ J.T
                dq = J.T @ np.linalg.solve(JJt + lambda2 * np.eye(6), err)
                dq = np.clip(dq, -0.8, 0.8)

                alpha_dq = 0.2
                smooth_dq = alpha_dq * dq + (1.0 - alpha_dq) * smooth_dq

                q_target = q_target + smooth_dq * dt
                q_target = np.clip(q_target, joint_min, joint_max)

                data.ctrl[:6] = q_target

                
                    

                if model.nu > 6:
                    data.ctrl[6] = gripper_cmd
                    smooth_gripper_cmd = gripper_cmd

                mujoco.mj_step(model, data)

                if time.time() - last_print > 0.5:
                    print(f"target_pos: {target_pos}")
                    print(f"grasp_pos : {grasp_pos}")
                    print(f"pos_err   : {pos_err}")
                    print(f"rot_err   : {rot_err}")
                    print(f"gripper   : {gripper_cmd}")
                    # Diagnostics: qpos / qvel / ctrl
                    try:
                        print(f"qpos[:6]  : {data.qpos[:6]}")
                        print(f"qvel[:6]  : {data.qvel[:6]}")
                        # Afficher au maximum 8 commandes d'action pour éviter le flood
                        nu_shown = min(int(model.nu), 8)
                        print(f"ctrl[:{nu_shown}] : {data.ctrl[:nu_shown]}")
                    except Exception:
                        pass
                    print("-" * 60)
                    last_print = time.time()

            # --- RENDU VISUEL ---
            now = time.time()
            if now - last_render >= render_period:
                if viewer is not None:
                    viewer.sync()
                else:
                    renderer_front.update_scene(data, camera="wrist_cam")
                    img_front = renderer_front.render()

                    renderer_top.update_scene(data, camera="top_table")
                    img_top = renderer_top.render()

                    # --- ANCIEN CODE (Pour la gestion de ton dataset actuel) ---
                    # img_front = cv2.rotate(img_front, cv2.ROTATE_180)
                    # img_top = cv2.rotate(img_top, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    # img_front = cv2.cvtColor(img_front, cv2.COLOR_RGB2BGR)
                    # img_top = cv2.cvtColor(img_top, cv2.COLOR_RGB2BGR)

                    # --- CODE POUR LE FUTUR (Quand les cameras XML seront tournées) ---
                    img_front = cv2.cvtColor(img_front, cv2.COLOR_RGB2BGR)
                    img_top = cv2.cvtColor(img_top, cv2.COLOR_RGB2BGR)

                    cv2.putText(img_front, "Eye_in_hand", (20, 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2, cv2.LINE_AA)
                    cv2.putText(img_top, "Eye_to_hand", (20, 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2, cv2.LINE_AA)

                    # Afficher le compteur d'épisodes sauvegardés (total + cette session)
                    try:
                        cv2.putText(img_front, f"SAVED: {saved_episodes_total} (+{saved_episodes_session})", (20, 65),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    except Exception:
                        pass
                    try:
                        cv2.putText(img_top, f"SAVED: {saved_episodes_total} (+{saved_episodes_session})", (20, 65),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    except Exception:
                        pass

                    if is_recording:
                        cv2.circle(img_front, (600, 40), 10, (0, 0, 255), -1)
                        cv2.putText(img_front, "REC", (550, 45),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

                    cv2.imshow("Eye_in_hand", img_front)
                    cv2.imshow("Eye_to_hand", img_top)

                    key = cv2.waitKey(1) & 0xFF
                                
                    if key == 27: # Touche ECHAP pour quitter
                        break
                    elif key == 32: # ESPACE -> Démarrer ou Valider l'enregistrement
                        if time.time() - last_space_press > 0.5: # 0.5 sec de sécurité anti-rebond
                            if not is_recording:
                                # START RECORDING
                                print("\n=== DEBUT DE L'ENREGISTREMENT ===")
                                is_recording = True
                                for k in current_episode_data:
                                    current_episode_data[k] = []
                            else:
                                # STOP & SAVE RECORDING
                                print("\n=== FIN DE L'ENREGISTREMENT ===")
                                is_recording = False
                                
                                # Convertir les listes en numpy arrays 
                                episode_np = {}
                                if len(current_episode_data['action']) > 0:
                                    for k, v in current_episode_data.items():
                                        episode_np[k] = np.stack(v, axis=0) if k != "action" else np.stack(v, axis=0).astype(np.float32)

                                    if ReplayBuffer is not None:
                                        if replay_buffer is None:
                                            if dataset_path is None:
                                                timestamp = time.strftime("%Y%m%d_%H%M%S")
                                                dataset_path = f"/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/data/datasets/demo_data_{timestamp}.zarr"
                                                print(f"Dataset cree: {dataset_path}")
                                            else:
                                                print(f"Dataset existant utilise : {dataset_path}")
                                            replay_buffer = ReplayBuffer.create_from_path(dataset_path, mode='a')

                                        replay_buffer.add_episode(episode_np, compressors="disk")
                                        # Mettre à jour compteurs affichés
                                        try:
                                            saved_episodes_total = int(replay_buffer.n_episodes)
                                        except Exception:
                                            saved_episodes_total = saved_episodes_total
                                        saved_episodes_session += 1
                                        print(f"Trajectoire enregistrée. ({len(current_episode_data['action'])} pas, {saved_episodes_total} épisodes totaux ( +{saved_episodes_session} cette session ))")
                                    else:
                                        print("Erreur: pas de ReplayBuffer disponible.")
                                else:
                                    print("Erreur : La trajectoire était vide, non sauvegardée.")
                                    
                            last_space_press = time.time() 
                        
                                
                    elif key == 8 or key == 127: # BACKSPACE / DELETE -> Annuler la trajectoire
                        if is_recording:
                            print("\n[!] ENREGISTREMENT ANNULÉ (Corbeille) [!]")
                            is_recording = False
                            # Vidage de la trajectoire
                            for k in current_episode_data:
                                current_episode_data[k] = []
                    elif key == ord('r'):  # R -> Reset de la simulation et robot au départ
                        mujoco.mj_resetData(model, data)

                        # reset robot
                        data.qpos[:6] = home_q
                        data.ctrl[:6] = home_q

                        if model.nu > 6:
                            data.qpos[6] = -0.2
                            smooth_gripper_cmd = -0.2
                            data.ctrl[6] = -0.2

                        q_target = home_q.copy()
                        smooth_dq[:] = 0.0

                            # reset du node ROS (pince et référence téléop)
                        try:
                            ros_node.reset_after_sim_reset()
                        except Exception:
                            pass

                    
                        # randomisation des objets
                        randomize_microwave_objects(model, data)


                        mujoco.mj_forward(model, data)

                        print("\n>>> SIMULATION RÉINITIALISÉE AVEC VARIATION DES OBJETS ! <<<")

                        if is_recording:
                            print("[!] Enregistrement annulé car la simulation a été reset [!]")
                            is_recording = False
                            for k in current_episode_data:
                                current_episode_data[k] = []
                last_render = now

                # --- 10 HZ RECORDING LOGIC ---
                if is_recording:
                    if time.time() - last_record_time >= (1.0 / record_freq):
                        # Récupérer les poses depuis mujoco directement (pour être toujours valides)
                        rec_grasp_pos = data.site_xpos[grasp_site_id].copy()
                        rec_R_current = data.site_xmat[grasp_site_id].reshape(3, 3).copy()
                       
                        img_front_84 = cv2.resize(renderer_front.render(), (84, 84), interpolation=cv2.INTER_AREA)
                        img_top_84 = cv2.resize(renderer_top.render(), (84, 84), interpolation=cv2.INTER_AREA)

                        current_episode_data['robot0_eye_in_hand_image'].append(img_front_84)
                        current_episode_data['agentview_image'].append(img_top_84)
                        
                        current_episode_data['robot0_eef_pos'].append(rec_grasp_pos.astype(np.float32))
                        
                        rec_rot_quat = np.empty(4)
                        mujoco.mju_mat2Quat(rec_rot_quat, rec_R_current.flatten())
                        
                        current_episode_data['robot0_eef_quat'].append(rec_rot_quat.astype(np.float32))
                        current_episode_data['robot0_gripper_qpos'].append(
                            np.array([float(data.qpos[6] if data.qpos.shape[0] > 6 else 0.0)], dtype=np.float32)
                        )

                        target_pos_save = target_pos if target_pos is not None else rec_grasp_pos
                        target_rot_save = target_rot if target_rot is not None else rec_R_current
                        target_rot_quat = rot_to_quat(target_rot_save).astype(np.float32)

                        action_vec = np.concatenate([
                            target_pos_save.astype(np.float32),
                            target_rot_quat,
                            np.array([gripper_cmd], dtype=np.float32)
                        ]).astype(np.float32)
                        
                        current_episode_data['action'].append(action_vec)
                        last_record_time = time.time()

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
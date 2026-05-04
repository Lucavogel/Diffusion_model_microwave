#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import sys
import time
from pathlib import Path
from typing import Deque, Dict, Optional, Tuple

import cv2
import dill
import hydra
import mujoco
import mujoco.viewer
import numpy as np
import torch

from scene_utils import randomize_microwave_objects, hide_free_body

# ============================================================
# Paths
# ============================================================
ROOT_DIR = Path(__file__).resolve().parents[2]

DP_DIR = ROOT_DIR / "diffusion_policy"
TELEOP_DIR = ROOT_DIR / "mujoco" / "teleop"
if str(DP_DIR) not in sys.path:
    sys.path.insert(0, str(DP_DIR))


# ============================================================
# Geometry helpers
# ============================================================
def quat_to_rot(qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
    x, y, z, w = qx, qy, qz, qw
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z

    return np.array(
        [
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
            [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
            [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
        ],
        dtype=np.float64,
    )


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

    q = np.array([qx, qy, qz, qw], dtype=np.float64)
    q /= np.linalg.norm(q) + 1e-12
    return q.astype(np.float32)


def quat_slerp(q0: np.ndarray, q1: np.ndarray, t: float) -> np.ndarray:
    """Spherical linear interpolation between quaternions (qx,qy,qz,qw)."""
    q0 = q0.astype(np.float64)
    q1 = q1.astype(np.float64)
    dot = float(np.dot(q0, q1))
    if dot < 0.0:
        q1 = -q1
        dot = -dot
    DOT_THRESHOLD = 0.9995
    if dot > DOT_THRESHOLD:
        result = q0 + t * (q1 - q0)
        result = result / (np.linalg.norm(result) + 1e-12)
        return result.astype(np.float32)
    theta_0 = np.arccos(np.clip(dot, -1.0, 1.0))
    sin_theta_0 = np.sin(theta_0)
    theta = theta_0 * t
    s0 = np.sin(theta_0 - theta) / sin_theta_0
    s1 = np.sin(theta) / sin_theta_0
    q = s0 * q0 + s1 * q1
    return (q / (np.linalg.norm(q) + 1e-12)).astype(np.float32)


def rot6d_to_rotmat(x: np.ndarray) -> np.ndarray:
    """
    Convertit une rotation 6D en matrice 3x3.
    x shape: (6,)
    """
    a1 = x[:3].astype(np.float64)
    a2 = x[3:6].astype(np.float64)

    b1 = a1 / (np.linalg.norm(a1) + 1e-12)
    a2_ortho = a2 - np.dot(b1, a2) * b1
    b2 = a2_ortho / (np.linalg.norm(a2_ortho) + 1e-12)
    b3 = np.cross(b1, b2)

    R = np.stack([b1, b2, b3], axis=1)
    return R.astype(np.float64)


def orientation_error(R_target: np.ndarray, R_current: np.ndarray) -> np.ndarray:
    """
    Erreur orientation petite-angle.
    """
    R_err = R_target @ R_current.T
    return 0.5 * np.array(
        [
            R_err[2, 1] - R_err[1, 2],
            R_err[0, 2] - R_err[2, 0],
            R_err[1, 0] - R_err[0, 1],
        ],
        dtype=np.float64,
    )


# ============================================================
# IO / Policy helpers
# ============================================================
def preprocess_rgb(img: np.ndarray) -> np.ndarray:
    return np.moveaxis(img, -1, 0).astype(np.float32) / 255.0


def load_policy(checkpoint_path: str, device: torch.device):
    payload = torch.load(checkpoint_path, map_location=device, pickle_module=dill)
    cfg = payload["cfg"]

    cls = hydra.utils.get_class(cfg._target_)
    workspace = cls(cfg, output_dir=str(ROOT_DIR / "mujoco" / "outputs"))
    workspace.load_payload(payload, exclude_keys=None, include_keys=None)

    policy = workspace.model
    if cfg.training.use_ema:
        policy = workspace.ema_model

    policy.to(device)
    policy.eval()
    return policy, cfg


def extract_action_sequence(policy_out: Dict[str, torch.Tensor]) -> np.ndarray:
    if "action" not in policy_out:
        raise KeyError("Policy output does not contain key 'action'.")

    action = policy_out["action"]

    if action.ndim == 3:
        # [B, T, D]
        return action[0].detach().cpu().numpy()
    if action.ndim == 2:
        # [T, D]
        return action.detach().cpu().numpy()
    if action.ndim == 1:
        # [D]
        return action.detach().cpu().numpy()[None, :]

    raise ValueError(f"Unexpected action shape: {tuple(action.shape)}")


def infer_image_shape(cfg) -> Tuple[int, int, int]:
    """
    Renvoie (C,H,W).
    """
    if hasattr(cfg, "task") and hasattr(cfg.task, "image_shape"):
        shape = tuple(cfg.task.image_shape)
        if len(shape) != 3:
            raise ValueError(f"Expected image_shape [C,H,W], got {shape}")
        return int(shape[0]), int(shape[1]), int(shape[2])

    # fallback shape_meta
    if hasattr(cfg, "shape_meta") and hasattr(cfg.shape_meta, "obs"):
        obs = cfg.shape_meta.obs
        if hasattr(obs, "agentview_image") and hasattr(obs.agentview_image, "shape"):
            shape = tuple(obs.agentview_image.shape)
            if len(shape) == 3:
                return int(shape[0]), int(shape[1]), int(shape[2])

    raise ValueError("Unable to infer image shape from config.")


def decode_action(
    action: np.ndarray,
    ignore_action_orientation: bool,
    current_rot: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Supporte:
      - 8D  = [x,y,z,qx,qy,qz,qw,gripper]
      - 10D = [x,y,z,r6d(6),gripper]
    Retourne:
      target_pos (3,), target_rot (3,3), gripper_cmd (float)
    """
    if action.ndim != 1:
        raise ValueError(f"Expected 1D action, got shape {action.shape}")

    if action.shape[0] == 8:
        target_pos = action[:3].astype(np.float64)
        target_quat = action[3:7].astype(np.float64)
        target_quat /= np.linalg.norm(target_quat) + 1e-12
        target_rot = quat_to_rot(
            float(target_quat[0]),
            float(target_quat[1]),
            float(target_quat[2]),
            float(target_quat[3]),
        )
        gripper_cmd = float(action[7])

    elif action.shape[0] == 10:
        target_pos = action[:3].astype(np.float64)
        target_rot = rot6d_to_rotmat(action[3:9])
        gripper_cmd = float(action[9])

    else:
        raise ValueError(
            f"Unsupported action dimension {action.shape[0]}. "
            f"Expected 8 (quat) or 10 (rot6d)."
        )

    if ignore_action_orientation:
        target_rot = current_rot.copy()

    return target_pos, target_rot, gripper_cmd


# ============================================================
# Main
# ============================================================
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run trained Diffusion Policy in MuJoCo (sequence execution faithful to paper)"
    )
    parser.add_argument("--checkpoint", required=True, help="Path to trained .ckpt")
    parser.add_argument(
        "--model_xml",
        default=str(ROOT_DIR / "mujoco" / "models" / "universal_robots_ur10e" / "scene_custom.xml"),
        help="MuJoCo XML scene",
    )
    parser.add_argument("--device", default="cpu", help="torch device: cpu or cuda:0")
    parser.add_argument("--policy_hz", type=float, default=10.0, help="Policy inference/action tick frequency")
    parser.add_argument(
        "--exec_horizon",
        type=int,
        default=None,
        help="Number of predicted actions to execute before replanning. Default = cfg.n_action_steps",
    )
    parser.add_argument("--camera_agentview", default="top_table", help="MuJoCo camera name for agentview_image")
    parser.add_argument("--camera_wrist", default="wrist_cam", help="MuJoCo camera name for robot0_eye_in_hand_image")

    parser.add_argument("--kp_pos", type=float, default=5.0, help="Position gain for IK controller")
    parser.add_argument("--kp_rot", type=float, default=2.0, help="Orientation gain for IK controller")
    parser.add_argument("--max_joint_vel", type=float, default=0.8, help="Max joint velocity command (rad/s)")
    parser.add_argument(
        "--alpha_dq",
        type=float,
        default=0.2,
        help="EMA smoothing on joint velocity (higher=faster response)",
    )
    parser.add_argument(
        "--alpha_grip",
        type=float,
        default=1.0,
        help="EMA smoothing on gripper command",
    )
    parser.add_argument(
        "--ignore_action_orientation",
        action="store_true",
        help="Ignore predicted orientation and keep current orientation (debug mode).",
    )
    parser.add_argument(
        "--viewer_fps",
        type=float,
        default=30.0,
        help="Viewer sync FPS cap",
    )
    parser.add_argument(
        "--home_q",
        type=float,
        nargs=6,
        default=[0.0, -1.3, 1.8, -0.22, 1.57, 0.0],
        help="Initial 6 joint values",
    )
    parser.add_argument(
        "--verbose_plan",
        action="store_true",
        help="Print each new predicted plan",
    )
    args = parser.parse_args()

    device = torch.device(args.device)
    policy, cfg = load_policy(args.checkpoint, device)

    # Image shape from training config
    _, obs_h, obs_w = infer_image_shape(cfg)

    n_obs_steps = int(cfg.n_obs_steps)
    pred_horizon = int(cfg.horizon)
    exec_horizon = int(args.exec_horizon) if args.exec_horizon is not None else int(cfg.n_action_steps)

    if not (1 <= exec_horizon <= pred_horizon):
        raise ValueError(
            f"exec_horizon must be in [1, {pred_horizon}], got {exec_horizon}"
        )

    if args.policy_hz <= 0.0:
        raise ValueError("policy_hz must be > 0")

    action_dt = 1.0 / float(args.policy_hz)

    # ========================================================
    # MuJoCo init
    # ========================================================
    # randomisation des objets
    
    model = mujoco.MjModel.from_xml_path(args.model_xml)
    data = mujoco.MjData(model)

    home_q = np.array(args.home_q, dtype=np.float64)
    if home_q.shape != (6,):
        raise ValueError(f"home_q must have 6 values, got {home_q.shape}")

    data.qpos[:6] = home_q
    data.ctrl[:6] = home_q
    if model.nu > 6:
        data.ctrl[6] = -0.2

    # randomisation des objets
    randomize_microwave_objects(model, data)

    # masquer éventuellement un objet (utiliser RNG local pour éviter la dépendance
    # au seed global qui peut rendre le choix déterministe)
    
    mode = ["both", "rectangle_only", "transformer_only"][int(np.random.randint(0, 3))]
    print(f"DEBUG: sampled visibility mode: {mode}")
    if mode == "both":
        pass
    elif mode == "rectangle_only":
        hide_free_body(model, data, "microwave_transformer")
    elif mode == "transformer_only":
        hide_free_body(model, data, "microwave_rectangle")

    mujoco.mj_forward(model, data)

    # Joint limits
    joint_min = model.jnt_range[:6, 0].copy()
    joint_max = model.jnt_range[:6, 1].copy()

    # End-effector site
    grasp_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "grasp_site")
    if grasp_site_id == -1:
        raise ValueError("Site 'grasp_site' not found in model.")

    mujoco.mj_forward(model, data)

    # Renderers: render at collection resolution (e.g. 640x480),
    # then downsample to (obs_h, obs_w) in `preprocess_rgb` to match data collection.
    RENDER_WIDTH = 640
    RENDER_HEIGHT = 480
    renderer_agent = mujoco.Renderer(model, height=RENDER_HEIGHT, width=RENDER_WIDTH)
    renderer_wrist = mujoco.Renderer(model, height=RENDER_HEIGHT, width=RENDER_WIDTH)

    # ========================================================
    # Buffers / controller state
    # ========================================================
    obs_hist: Dict[str, Deque[np.ndarray]] = {
        "agentview_image": collections.deque(maxlen=n_obs_steps),
        "robot0_eye_in_hand_image": collections.deque(maxlen=n_obs_steps),
        "robot0_eef_pos": collections.deque(maxlen=n_obs_steps),
        "robot0_eef_quat": collections.deque(maxlen=n_obs_steps),
        "robot0_gripper_qpos": collections.deque(maxlen=n_obs_steps),
    }

    action_buffer: Deque[np.ndarray] = collections.deque()
    current_action: Optional[np.ndarray] = None

    # force first action tick immediately
    last_action_switch_sim_t = data.time - action_dt
    last_viewer_sync_wall_t = 0.0

    q_target = home_q.copy()
    smooth_dq = np.zeros(6, dtype=np.float64)
    smooth_gripper_cmd = -0.2

    Kp_pos = float(args.kp_pos)
    Kp_rot = float(args.kp_rot)
    alpha_dq = float(args.alpha_dq)
    alpha_grip = float(args.alpha_grip)

    prev_sim_time = data.time

    # ========================================================
    # Observation helpers
    # ========================================================
    def push_observation() -> None:
        renderer_agent.update_scene(data, camera=args.camera_agentview)
        renderer_wrist.update_scene(data, camera=args.camera_wrist)

        img_agent = renderer_agent.render()
        img_wrist = renderer_wrist.render()
        # même convention que pendant la collecte:
        # render at 640x480, rotate, then downsample to 84x84 before preprocessing
        img_agent = cv2.rotate(img_agent, cv2.ROTATE_90_COUNTERCLOCKWISE)
        img_wrist = cv2.rotate(img_wrist, cv2.ROTATE_180)

        DATA_COLLECTION_H = 84
        DATA_COLLECTION_W = 84
        img_agent_84 = cv2.resize(img_agent, (DATA_COLLECTION_W, DATA_COLLECTION_H), interpolation=cv2.INTER_AREA)
        img_wrist_84 = cv2.resize(img_wrist, (DATA_COLLECTION_W, DATA_COLLECTION_H), interpolation=cv2.INTER_AREA)

        eef_pos = data.site_xpos[grasp_site_id].copy().astype(np.float32)
        eef_quat = rot_to_quat(data.site_xmat[grasp_site_id].reshape(3, 3)).astype(np.float32)
        gripper_qpos = np.array(
            [data.qpos[6] if data.qpos.shape[0] > 6 else 0.0],
            dtype=np.float32,
        )

        obs_hist["agentview_image"].append(preprocess_rgb(img_agent_84))
        obs_hist["robot0_eye_in_hand_image"].append(preprocess_rgb(img_wrist_84))
        obs_hist["robot0_eef_pos"].append(eef_pos)
        obs_hist["robot0_eef_quat"].append(eef_quat)
        obs_hist["robot0_gripper_qpos"].append(gripper_qpos)


    def build_obs_tensor() -> Dict[str, torch.Tensor]:
        return {
            "agentview_image": torch.from_numpy(
                np.stack(list(obs_hist["agentview_image"]), axis=0)
            )[None].to(device),
            "robot0_eye_in_hand_image": torch.from_numpy(
                np.stack(list(obs_hist["robot0_eye_in_hand_image"]), axis=0)
            )[None].to(device),
            "robot0_eef_pos": torch.from_numpy(
                np.stack(list(obs_hist["robot0_eef_pos"]), axis=0)
            )[None].to(device),
            "robot0_eef_quat": torch.from_numpy(
                np.stack(list(obs_hist["robot0_eef_quat"]), axis=0)
            )[None].to(device),
            "robot0_gripper_qpos": torch.from_numpy(
                np.stack(list(obs_hist["robot0_gripper_qpos"]), axis=0)
            )[None].to(device),
        }

    def refill_initial_obs_history() -> None:
        for buf in obs_hist.values():
            buf.clear()
        for _ in range(n_obs_steps):
            push_observation()

    # initial obs history
    refill_initial_obs_history()

    # --- interpolation targets initialization -----------------
    init_eef_pos = np.array(obs_hist["robot0_eef_pos"][-1], dtype=np.float64)
    init_eef_quat = np.array(obs_hist["robot0_eef_quat"][-1], dtype=np.float64)
    init_gripper = float(obs_hist["robot0_gripper_qpos"][-1][0])
    prev_target_pos = init_eef_pos.copy()
    prev_target_quat = init_eef_quat.copy()
    prev_gripper_cmd = init_gripper
    interp_start_pos = prev_target_pos.copy()
    interp_start_quat = prev_target_quat.copy()
    interp_start_gripper = prev_gripper_cmd
    interp_end_pos = prev_target_pos.copy()
    interp_end_quat = prev_target_quat.copy()
    interp_end_gripper = prev_gripper_cmd
    # interpolation start time in sim seconds
    action_start_time = last_action_switch_sim_t

    orient_mode = "IGNORED" if args.ignore_action_orientation else "FOLLOWED"
    print(
        f"Policy-driven MuJoCo test started | "
        f"policy_hz={args.policy_hz:.1f} | "
        f"pred_horizon={pred_horizon} | "
        f"exec_horizon={exec_horizon} | "
        f"orientation={orient_mode}"
    )

    # ========================================================
    # Main loop
    # ========================================================
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            # --------------------------------------------
            # Detect manual reset from viewer if any
            # --------------------------------------------
            if data.time < prev_sim_time:
                print("[Info] MuJoCo reset detected. Resetting internal buffers/state.")
                mujoco.mj_forward(model, data)

                q_target = data.qpos[:6].copy()
                smooth_dq[:] = 0.0
                smooth_gripper_cmd = float(data.qpos[6] if data.qpos.shape[0] > 6 else -0.2)

                action_buffer.clear()
                current_action = None
                last_action_switch_sim_t = data.time - action_dt
                refill_initial_obs_history()

            prev_sim_time = data.time

            # --------------------------------------------
            # Policy/action tick based on SIMULATION TIME
            # --------------------------------------------
            if (data.time - last_action_switch_sim_t) >= action_dt:
                push_observation()

                # replan only when buffer is empty
                if len(action_buffer) == 0:
                    obs_tensor = build_obs_tensor()

                    with torch.inference_mode():
                        policy_out = policy.predict_action(obs_tensor)

                    action_seq = extract_action_sequence(policy_out)
                    if action_seq.ndim != 2:
                        raise ValueError(f"Expected action sequence [T,D], got {action_seq.shape}")

                    n_take = min(exec_horizon, action_seq.shape[0])
                    action_buffer = collections.deque([a.astype(np.float32) for a in action_seq[:n_take]])

                    if args.verbose_plan:
                        print(f"[Plan] predicted={action_seq.shape[0]} | execute={n_take}")

                # activate next action for the next policy interval
                if len(action_buffer) > 0:
                    current_action = action_buffer.popleft()
                    # decode into execution-space targets (pos, rot matrix, gripper)
                    # use most recent observed orientation as current reference for decode_action
                    obs_quat = np.array(obs_hist["robot0_eef_quat"][-1], dtype=np.float64)
                    R_ref = quat_to_rot(float(obs_quat[0]), float(obs_quat[1]), float(obs_quat[2]), float(obs_quat[3]))
                    new_end_pos, new_end_rot, new_end_gripper = decode_action(
                        current_action,
                        ignore_action_orientation=args.ignore_action_orientation,
                        current_rot=R_ref,
                    )
                    new_end_quat = rot_to_quat(new_end_rot)

                    # set interpolation window: from previous target -> new_end over [action_start_time, action_start_time+action_dt]
                    interp_start_pos = prev_target_pos.copy()
                    interp_start_quat = prev_target_quat.copy()
                    interp_start_gripper = prev_gripper_cmd
                    interp_end_pos = new_end_pos.copy()
                    interp_end_quat = new_end_quat.copy()
                    interp_end_gripper = new_end_gripper

                    # update prev targets for next window
                    prev_target_pos = interp_end_pos.copy()
                    prev_target_quat = interp_end_quat.copy()
                    prev_gripper_cmd = interp_end_gripper

                # mark the start time of this action (simulation time)
                # start now to avoid beginning the interpolation in the past
                last_action_switch_sim_t = data.time
                action_start_time = data.time

            # --------------------------------------------
            # Fast IK controller at each mj_step
            # --------------------------------------------
            if current_action is not None:
                grasp_pos = data.site_xpos[grasp_site_id].copy()
                R_current = data.site_xmat[grasp_site_id].reshape(3, 3).copy()

                # Interpolate between interp_start_* and interp_end_* over the policy interval
                if action_dt > 0:
                    alpha = float((data.time - action_start_time) / action_dt)
                    alpha = max(0.0, min(1.0, alpha))
                else:
                    alpha = 1.0

                target_pos = (1.0 - alpha) * interp_start_pos + alpha * interp_end_pos
                interp_quat = quat_slerp(interp_start_quat, interp_end_quat, alpha)
                target_rot = quat_to_rot(float(interp_quat[0]), float(interp_quat[1]), float(interp_quat[2]), float(interp_quat[3]))
                gripper_cmd = float((1.0 - alpha) * interp_start_gripper + alpha * interp_end_gripper)

                pos_err = target_pos - grasp_pos
                rot_err = orientation_error(target_rot, R_current)
                err = np.hstack([Kp_pos * pos_err, Kp_rot * rot_err])

                jacp = np.zeros((3, model.nv), dtype=np.float64)
                jacr = np.zeros((3, model.nv), dtype=np.float64)
                mujoco.mj_jacSite(model, data, jacp, jacr, grasp_site_id)

                J = np.vstack([jacp[:, :6], jacr[:, :6]])

                lambda2 = 5e-3
                JJt = J @ J.T
                dq = J.T @ np.linalg.inv(JJt + lambda2 * np.eye(6)) @ err
                dq = np.clip(dq, -args.max_joint_vel, args.max_joint_vel)

                smooth_dq = alpha_dq * dq + (1.0 - alpha_dq) * smooth_dq

                dt = model.opt.timestep
                q_target = np.clip(q_target + smooth_dq * dt, joint_min, joint_max)
                data.ctrl[:6] = q_target

                if model.nu > 6:
                    smooth_gripper_cmd = alpha_grip * gripper_cmd + (1.0 - alpha_grip) * smooth_gripper_cmd
                    data.ctrl[6] = float(np.clip(smooth_gripper_cmd, -0.2, 1.2))
            else:
                data.ctrl[:6] = q_target

            # --------------------------------------------
            # One physics step only
            # --------------------------------------------
            mujoco.mj_step(model, data)

            # --------------------------------------------
            # Viewer sync cap
            # --------------------------------------------
            if (time.time() - last_viewer_sync_wall_t) >= (1.0 / args.viewer_fps):
                viewer.sync()
                last_viewer_sync_wall_t = time.time()


if __name__ == "__main__":
    main()
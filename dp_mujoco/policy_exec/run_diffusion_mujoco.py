from __future__ import annotations

import argparse
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np
import torch

from dp_mujoco.env.mujoco_env import MujocoEnv
from dp_mujoco.utils.scene_utils import randomize_microwave_objects
from dp_mujoco.utils.safety_config import SafetyChecker

from dp_mujoco.common.pose_utils import quat_slerp, quat_to_rot, rot_to_quat
from dp_mujoco.policy_exec.action_decoder import extract_action_sequence
from dp_mujoco.policy_exec.observation_builder import ObservationBuilder
from dp_mujoco.policy_exec.policy_loader import infer_image_shape, load_policy
from dp_mujoco.policy_exec.servo_controller import ServoController
from dp_mujoco.policy_exec.trajectory_executor import TrajectoryExecutor


ROOT_DIR = Path(__file__).resolve().parents[2]


def project_to_so3(R: np.ndarray) -> np.ndarray:
    U, _, Vt = np.linalg.svd(R)
    R_proj = U @ Vt

    if np.linalg.det(R_proj) < 0.0:
        U[:, -1] *= -1.0
        R_proj = U @ Vt

    return R_proj


def rot_to_quat_wxyz(R: np.ndarray) -> np.ndarray:
    q_xyzw = rot_to_quat(R)
    q_wxyz = np.array(
        [q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]],
        dtype=np.float64,
    )
    q_wxyz /= np.linalg.norm(q_wxyz)
    return q_wxyz


def quat_wxyz_to_rot(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64).copy()
    q /= np.linalg.norm(q)
    return quat_to_rot(float(q[1]), float(q[2]), float(q[3]), float(q[0]))


class PolicyTargetSmoother:
    def __init__(
        self,
        max_target_speed: float = 0.35,
        alpha_pos: float = 0.35,
        alpha_rot: float = 0.25,
        alpha_gripper: float = 0.35,
    ) -> None:
        self.max_target_speed = float(max_target_speed)
        self.alpha_pos = float(alpha_pos)
        self.alpha_rot = float(alpha_rot)
        self.alpha_gripper = float(alpha_gripper)

        self.target_pos: np.ndarray | None = None
        self.target_quat: np.ndarray | None = None
        self.gripper_cmd: float | None = None

    def reset(self, pos: np.ndarray, quat_wxyz: np.ndarray, gripper: float) -> None:
        self.target_pos = np.asarray(pos, dtype=np.float64).copy()
        self.target_quat = np.asarray(quat_wxyz, dtype=np.float64).copy()
        self.target_quat /= np.linalg.norm(self.target_quat)
        self.gripper_cmd = float(gripper)

    def update(
        self,
        raw_pos: np.ndarray,
        raw_rot: np.ndarray,
        raw_gripper: float,
        dt: float,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        raw_pos = np.asarray(raw_pos, dtype=np.float64).copy()
        raw_quat = rot_to_quat_wxyz(raw_rot)
        raw_gripper = float(raw_gripper)

        if self.target_pos is None or self.target_quat is None or self.gripper_cmd is None:
            self.reset(raw_pos, raw_quat, raw_gripper)
            return raw_pos, raw_rot, raw_gripper

        if np.dot(self.target_quat, raw_quat) < 0.0:
            raw_quat = -raw_quat

        dpos = raw_pos - self.target_pos

        max_step = self.max_target_speed * max(float(dt), 1e-6)
        dpos_norm = float(np.linalg.norm(dpos))

        if dpos_norm > max_step and dpos_norm > 1e-12:
            dpos = dpos * (max_step / dpos_norm)

        limited_pos = self.target_pos + dpos

        self.target_pos = (
            (1.0 - self.alpha_pos) * self.target_pos
            + self.alpha_pos * limited_pos
        )

        self.target_quat = quat_slerp(
            self.target_quat.astype(np.float32),
            raw_quat.astype(np.float32),
            self.alpha_rot,
        ).astype(np.float64)

        self.target_quat /= np.linalg.norm(self.target_quat)

        self.gripper_cmd = (
            (1.0 - self.alpha_gripper) * self.gripper_cmd
            + self.alpha_gripper * raw_gripper
        )

        smooth_rot = quat_wxyz_to_rot(self.target_quat)

        return self.target_pos.copy(), smooth_rot, float(self.gripper_cmd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run diffusion policy smoothly in MuJoCo")

    parser.add_argument("--checkpoint", required=True, help="Path to trained .ckpt")

    parser.add_argument(
        "--model_xml",
        default=str(
            ROOT_DIR
            / "dp_mujoco"
            / "models"
            / "universal_robots_ur10e"
            / "scene_custom.xml"
        ),
        help="MuJoCo XML scene",
    )

    parser.add_argument("--device", default="cpu", help="torch device: cpu or cuda:0")

    parser.add_argument(
        "--policy_hz",
        type=float,
        default=10.0,
        help="Policy action frequency",
    )

    parser.add_argument(
        "--exec_horizon",
        type=int,
        default=None,
        help="Number of predicted actions to execute before replanning",
    )

    parser.add_argument("--camera_agentview", default="top_table")
    parser.add_argument("--camera_wrist", default="wrist_cam")

    parser.add_argument("--kp_pos", type=float, default=5.0)
    parser.add_argument("--kp_rot", type=float, default=2.0)
    parser.add_argument("--max_joint_vel", type=float, default=0.8)
    parser.add_argument("--alpha_dq", type=float, default=0.2)
    parser.add_argument("--alpha_grip", type=float, default=1.0)

    parser.add_argument(
        "--ignore_action_orientation",
        action="store_true",
        help="Keep current orientation",
    )

    parser.add_argument(
        "--viewer_fps",
        type=float,
        default=20.0,
        help="Viewer sync FPS cap",
    )

    parser.add_argument(
        "--real_time_sync",
        action="store_true",
        help="Sleep to keep MuJoCo close to real time",
    )

    parser.add_argument(
        "--debug_timing",
        action="store_true",
        help="Print inference and loop timing",
    )

    parser.add_argument(
        "--max_target_speed",
        type=float,
        default=0.35,
        help="Max cartesian target speed in m/s after policy",
    )

    parser.add_argument(
        "--smooth_alpha_pos",
        type=float,
        default=0.35,
        help="Post-policy target position smoothing",
    )

    parser.add_argument(
        "--smooth_alpha_rot",
        type=float,
        default=0.25,
        help="Post-policy target rotation smoothing",
    )

    parser.add_argument(
        "--smooth_alpha_gripper",
        type=float,
        default=0.35,
        help="Post-policy gripper smoothing",
    )

    parser.add_argument(
        "--home_q",
        type=float,
        nargs=6,
        default=[0.0, -1.3, 1.8, -0.22, 1.57, 0.0],
    )

    parser.add_argument("--verbose_plan", action="store_true")

    parser.add_argument("--save_traj", action="store_true")

    parser.add_argument(
        "--save_traj_path",
        default=str(ROOT_DIR / "data" / "outputs" / "smooth_trajectory.npz"),
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    device = torch.device(args.device)

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

    if args.policy_hz <= 0.0:
        raise ValueError("policy_hz must be > 0")

    env = MujocoEnv(
        model_xml=args.model_xml,
        camera_agentview=args.camera_agentview,
        camera_wrist=args.camera_wrist,
    )

    sim_dt = float(env.model.opt.timestep)

    home_q = np.array(args.home_q, dtype=np.float64)

    env.reset(home_q=home_q)
    randomize_microwave_objects(env.model, env.data)
    mujoco.mj_forward(env.model, env.data)

    builder = ObservationBuilder(
        cfg,
        device,
        env,
        image_height=obs_h,
        image_width=obs_w,
    )

    builder.initialize_history()

    traj_exec = TrajectoryExecutor(
        action_dt=1.0 / float(args.policy_hz),
        exec_horizon=exec_horizon,
        ignore_action_orientation=args.ignore_action_orientation,
    )

    servo = ServoController(
        home_q=home_q,
        kp_pos=args.kp_pos,
        kp_rot=args.kp_rot,
        max_joint_vel=args.max_joint_vel,
        alpha_dq=args.alpha_dq,
        alpha_grip=args.alpha_grip,
    )

    target_smoother = PolicyTargetSmoother(
        max_target_speed=args.max_target_speed,
        alpha_pos=args.smooth_alpha_pos,
        alpha_rot=args.smooth_alpha_rot,
        alpha_gripper=args.smooth_alpha_gripper,
    )

    kinematic_safety_checker = SafetyChecker(q=np.zeros(6, dtype=np.float64))
    dynamic_safety_checker = SafetyChecker(q=np.zeros(6, dtype=np.float64))

    init_eef_pos = builder.get_latest_eef_pos()
    init_eef_quat = builder.get_latest_eef_quat()
    init_gripper = builder.get_latest_gripper_qpos()

    traj_exec.reset(init_eef_pos, init_eef_quat, init_gripper, env.data.time)
    target_smoother.reset(init_eef_pos, init_eef_quat, init_gripper)

    print()
    print("===========================================")
    print("Policy-driven MuJoCo smooth run started")
    print("===========================================")
    print(f"device          : {device}")
    print(f"policy_hz       : {args.policy_hz}")
    print(f"pred_horizon    : {pred_horizon}")
    print(f"exec_horizon    : {exec_horizon}")
    print(f"obs             : {obs_h}x{obs_w}")
    print(f"viewer_fps      : {args.viewer_fps}")
    print(f"sim_dt          : {sim_dt}")
    print(f"real_time_sync  : {args.real_time_sync}")
    print(f"max_target_speed: {args.max_target_speed}")
    print("===========================================")
    print()

    recorded_qpos = []
    recorded_qvel = []
    recorded_qacc = []
    recorded_time = []

    prev_sim_time = env.data.time
    last_viewer_sync_wall_t = 0.0
    last_debug_wall_t = time.time()
    safety_hold = False

    with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
        while viewer.is_running():
            step_wall_start = time.time()

            if env.data.time < prev_sim_time:
                print("[Info] MuJoCo reset detected. Resetting internal buffers/state.")

                env.reset(home_q=home_q)
                randomize_microwave_objects(env.model, env.data)
                mujoco.mj_forward(env.model, env.data)

                builder.initialize_history()

                init_eef_pos = builder.get_latest_eef_pos()
                init_eef_quat = builder.get_latest_eef_quat()
                init_gripper = builder.get_latest_gripper_qpos()

                traj_exec.reset(init_eef_pos, init_eef_quat, init_gripper, env.data.time)
                target_smoother.reset(init_eef_pos, init_eef_quat, init_gripper)

                servo.reset(
                    env.data.qpos[:6],
                    gripper_cmd=float(env.data.qpos[6] if env.data.qpos.shape[0] > 6 else -0.2),
                )

                safety_hold = False

            prev_sim_time = env.data.time

            current_result = None

            if (not safety_hold) and traj_exec.needs_replan(env.data.time):
                builder.update()

                if not traj_exec.has_buffered_actions():
                    obs_tensor = builder.build_tensor()

                    infer_wall_start = time.time()

                    with torch.inference_mode():
                        policy_out = policy.predict_action(obs_tensor)

                    infer_dt = time.time() - infer_wall_start

                    action_seq = extract_action_sequence(policy_out)
                    n_take = traj_exec.set_sequence(action_seq)

                    if args.verbose_plan:
                        print(
                            f"[Plan] predicted={action_seq.shape[0]} | "
                            f"execute={n_take} | inference={infer_dt:.3f}s"
                        )

                    elif args.debug_timing:
                        print(f"[TIMING] inference_dt={infer_dt:.3f}s")

                current_obs_quat = builder.get_latest_eef_quat()
                traj_exec.start_next_action(current_obs_quat, env.data.time)

            if traj_exec.has_active_action() and not safety_hold:
                raw_target_pos, raw_target_rot, raw_gripper_cmd, alpha = traj_exec.get_target(
                    env.data.time
                )

                target_pos, target_rot, gripper_cmd = target_smoother.update(
                    raw_pos=raw_target_pos,
                    raw_rot=raw_target_rot,
                    raw_gripper=raw_gripper_cmd,
                    dt=sim_dt,
                )

                current_result = servo.compute(
                    env.model,
                    env.data,
                    env.grasp_site_id,
                    env.joint_min,
                    env.joint_max,
                    target_pos,
                    target_rot,
                    gripper_cmd,
                )

                env.apply_joint_command(
                    current_result["q_target"],
                    current_result["gripper_cmd"],
                )

            else:
                env.apply_joint_command(
                    servo.q_target,
                    servo.smooth_gripper_cmd,
                )

            kinematic_status = kinematic_safety_checker.check_loop(
                qvel=None,
                qacc=None,
                J=current_result["J"] if current_result is not None else None,
            )

            if kinematic_status.get("status", "").lower() != "ok":
                print(
                    f"[SAFETY CHECK] status={kinematic_status.get('status')} | "
                    f"reason={kinematic_status.get('reason')} | "
                    f"metrics={kinematic_status.get('metrics')}"
                )

                safety_hold = True
                traj_exec.clear()

                servo.reset(
                    env.data.qpos[:6],
                    gripper_cmd=float(env.data.qpos[6] if env.data.qpos.shape[0] > 6 else -0.2),
                )

                env.apply_joint_command(
                    env.data.qpos[:6],
                    env.data.qpos[6] if env.data.qpos.shape[0] > 6 else -0.2,
                )

                mujoco.mj_step(env.model, env.data)

                if args.save_traj:
                    recorded_qpos.append(env.data.qpos.copy())
                    recorded_qvel.append(env.data.qvel.copy())
                    recorded_qacc.append(env.data.qacc.copy())
                    recorded_time.append(float(env.data.time))

                if (time.time() - last_viewer_sync_wall_t) >= (1.0 / args.viewer_fps):
                    viewer.sync()
                    last_viewer_sync_wall_t = time.time()

                if args.real_time_sync:
                    elapsed = time.time() - step_wall_start
                    if elapsed < sim_dt:
                        time.sleep(sim_dt - elapsed)

                continue

            mujoco.mj_step(env.model, env.data)

            dynamic_status = dynamic_safety_checker.check_loop(
                qvel=env.data.qvel,
                qacc=env.data.qacc,
                J=None,
            )

            if dynamic_status.get("status", "").lower() != "ok":
                print(
                    f"[SAFETY CHECK] status={dynamic_status.get('status')} | "
                    f"reason={dynamic_status.get('reason')} | "
                    f"metrics={dynamic_status.get('metrics')}"
                )

                safety_hold = True
                traj_exec.clear()

                servo.reset(
                    env.data.qpos[:6],
                    gripper_cmd=float(env.data.qpos[6] if env.data.qpos.shape[0] > 6 else -0.2),
                )

                env.apply_joint_command(
                    env.data.qpos[:6],
                    env.data.qpos[6] if env.data.qpos.shape[0] > 6 else -0.2,
                )

            if args.save_traj:
                recorded_qpos.append(env.data.qpos.copy())
                recorded_qvel.append(env.data.qvel.copy())
                recorded_qacc.append(env.data.qacc.copy())
                recorded_time.append(float(env.data.time))

            now_wall = time.time()

            if (now_wall - last_viewer_sync_wall_t) >= (1.0 / args.viewer_fps):
                viewer.sync()
                last_viewer_sync_wall_t = now_wall

            if args.debug_timing and (now_wall - last_debug_wall_t) > 1.0:
                real_loop_dt = now_wall - step_wall_start
                print(
                    f"[LOOP] sim_time={env.data.time:.3f} | "
                    f"loop_wall_dt={real_loop_dt:.4f}s | "
                    f"qpos[:6]={np.round(env.data.qpos[:6], 3)}"
                )
                last_debug_wall_t = now_wall

            if args.real_time_sync:
                elapsed = time.time() - step_wall_start
                if elapsed < sim_dt:
                    time.sleep(sim_dt - elapsed)

    if args.save_traj and len(recorded_qpos) > 0:
        Path(args.save_traj_path).parent.mkdir(parents=True, exist_ok=True)

        np.savez(
            args.save_traj_path,
            qpos=np.array(recorded_qpos),
            qvel=np.array(recorded_qvel),
            qacc=np.array(recorded_qacc),
            time=np.array(recorded_time, dtype=np.float64),
        )

        print(f"\n[INFO] Trajectory saved to: {args.save_traj_path}")
        print(f"       ({len(recorded_qpos)} frames recorded)")


if __name__ == "__main__":
    main()
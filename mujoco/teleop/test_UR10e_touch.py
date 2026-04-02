#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import threading
import time

import mujoco
import mujoco.viewer
import numpy as np
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32


MODEL_PATH = Path("/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_custom.xml")


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

        self.target_pos = None
        self.target_rot = None
        self.gripper_cmd = -0.2

        self.lock = threading.Lock()

        self.pose_sub = self.create_subscription(PoseStamped, "/teleop/target_pose", self.pose_cb, 10)
        self.gripper_sub = self.create_subscription(Float32, "/teleop/gripper_cmd", self.gripper_cb, 10)

    def pose_cb(self, msg: PoseStamped) -> None:
        pos = np.array([
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z,
        ], dtype=float)

        rot = quat_to_rot(
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        )

        with self.lock:
            self.target_pos = pos
            self.target_rot = rot

    def gripper_cb(self, msg: Float32) -> None:
        with self.lock:
            self.gripper_cmd = float(msg.data)

    def get_target(self):
        with self.lock:
            if self.target_pos is None or self.target_rot is None:
                return None, None, float(self.gripper_cmd)
            return self.target_pos.copy(), self.target_rot.copy(), float(self.gripper_cmd)


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

    home_q = np.array([0.0, -1.2, 1.6, -1.2, -1.57, 0.0], dtype=float)
    data.qpos[:6] = home_q
    data.ctrl[:6] = home_q

    if model.nu > 6:
        data.ctrl[6] = -0.2

    grasp_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "grasp_site")
    if grasp_site_id == -1:
        raise ValueError("Site 'grasp_site' introuvable.")

    mujoco.mj_forward(model, data)

    q_target = home_q.copy()

    # Gains ajustés pour éviter l'overshoot (oscillation continue)
    Kp_pos = 8.0
    Kp_rot = 1.5
    dt = model.opt.timestep

    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            last_print = time.time()
            last_render = time.time()

            while viewer.is_running():
                step_start = time.time()

                target_pos, target_rot, gripper_cmd = ros_node.get_target()

                if target_pos is None or target_rot is None:
                    data.ctrl[:6] = home_q
                    if model.nu > 6:
                        data.ctrl[6] = gripper_cmd

                    mujoco.mj_step(model, data)
                    
                    if time.time() - last_render > 1.0 / 60.0:
                        viewer.sync()
                        last_render = time.time()
                    
                    elapsed = time.time() - step_start
                    if elapsed < dt:
                        time.sleep(dt - elapsed)
                    continue

                grasp_pos = data.site_xpos[grasp_site_id].copy()
                R_current = data.site_xmat[grasp_site_id].reshape(3, 3).copy()

                pos_err = target_pos - grasp_pos
                rot_err = orientation_error(target_rot, R_current)

                err = np.hstack([Kp_pos * pos_err, Kp_rot * rot_err])

                jacp = np.zeros((3, model.nv))
                jacr = np.zeros((3, model.nv))
                mujoco.mj_jacSite(model, data, jacp, jacr, grasp_site_id)

                J = np.vstack([jacp[:, :6], jacr[:, :6]])

                lambda2 = 1e-3
                JJt = J @ J.T
                dq = J.T @ np.linalg.inv(JJt + lambda2 * np.eye(6)) @ err
                # Augmenter la limite de vitesse (avant: 0.5 rad/s, maintenant: 1.0 rad/s pour eviter l'overshoot)
                dq = np.clip(dq, -1.0, 1.0)

                # Augmenter la raideur du gain proportionnel
                q_target = q_target + dq * dt
                q_target = np.clip(q_target, joint_min, joint_max)

                data.ctrl[:6] = q_target
                if model.nu > 6:
                    data.ctrl[6] = gripper_cmd

                mujoco.mj_step(model, data)

                if time.time() - last_print > 0.5:
                    print(f"target_pos: {target_pos}")
                    print(f"grasp_pos : {grasp_pos}")
                    print(f"pos_err   : {pos_err}")
                    print(f"rot_err   : {rot_err}")
                    print(f"gripper   : {gripper_cmd}")
                    print("-" * 60)
                    last_print = time.time()

                if time.time() - last_render > 1.0 / 60.0:
                    viewer.sync()
                    last_render = time.time()

                elapsed = time.time() - step_start
                if elapsed < dt:
                    time.sleep(dt - elapsed)

    except KeyboardInterrupt:
        print("Arrêt demandé.")
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()
        print("Fin du script.")


if __name__ == "__main__":
    main()
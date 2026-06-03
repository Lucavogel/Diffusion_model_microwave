#!/usr/bin/env python3
from __future__ import annotations

import math
from typing import Optional

import numpy as np
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Int8, Float32


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
        s = math.sqrt(trace + 1.0) * 2.0
        qw = 0.25 * s
        qx = (R[2, 1] - R[1, 2]) / s
        qy = (R[0, 2] - R[2, 0]) / s
        qz = (R[1, 0] - R[0, 1]) / s
    else:
        if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
            qw = (R[2, 1] - R[1, 2]) / s
            qx = 0.25 * s
            qy = (R[0, 1] + R[1, 0]) / s
            qz = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
            qw = (R[0, 2] - R[2, 0]) / s
            qx = (R[0, 1] + R[1, 0]) / s
            qy = 0.25 * s
            qz = (R[1, 2] + R[2, 1]) / s
        else:
            s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
            qw = (R[1, 0] - R[0, 1]) / s
            qx = (R[0, 2] + R[2, 0]) / s
            qy = (R[1, 2] + R[2, 1]) / s
            qz = 0.25 * s

    q = np.array([qx, qy, qz, qw], dtype=float)
    q /= np.linalg.norm(q) + 1e-12
    return q


class TouchToTargetPoseNode(Node):
    def __init__(self) -> None:
        super().__init__("touch_to_target_pose")

        self.position_scale = 0.4

        # Position initiale exacte du robot (calculée à partir de home_q)
        self.initial_robot_pos = np.array([0.997007, 0.174247, 0.694586], dtype=float)

        # Orientation initiale exacte du robot pour éviter que ça tire sur le poignet
        self.initial_robot_rot = np.array([
            [-0.000795, 0.049979, 0.998750],
            [1.000000, 0.000000, 0.000796],
            [0.000040, 0.998750, -0.049979],
        ], dtype=float)

        self.target_pos: Optional[np.ndarray] = None
        self.target_rot: Optional[np.ndarray] = None

        self.prev_touch_pos: Optional[np.ndarray] = None
        self.prev_touch_rot: Optional[np.ndarray] = None
        self.touch_initialized = False

        self.current_buttons = 0
        self.gripper_speed = 1.2
        self.gripper_value = -0.2
        self.last_gripper_time = self.get_clock().now()

        self.target_pub = self.create_publisher(PoseStamped, "/teleop/target_pose", 10)
        self.gripper_pub = self.create_publisher(Float32, "/teleop/gripper_cmd", 10)

        self.pose_sub = self.create_subscription(PoseStamped, "/touch/pose", self.pose_cb, 10)
        self.buttons_sub = self.create_subscription(Int8, "/touch/buttons", self.buttons_cb, 10)

        self.gripper_timer = self.create_timer(
            0.005,
            self.update_gripper
        )

        self.get_logger().info("touch_to_target_pose started")

    def buttons_cb(self, msg: Int8) -> None:
        self.current_buttons = int(msg.data)

    def update_gripper(self) -> None:
        now = self.get_clock().now()
        dt = (now - self.last_gripper_time).nanoseconds * 1e-9
        self.last_gripper_time = now

        if self.current_buttons == 1:
            self.gripper_value -= self.gripper_speed * dt   # ouvrir
        elif self.current_buttons == -1:
            self.gripper_value += self.gripper_speed * dt   # fermer

        self.gripper_value = max(-0.2, min(1.2, self.gripper_value))

        g = Float32()
        g.data = float(self.gripper_value)
        self.gripper_pub.publish(g)

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

        if not self.touch_initialized:
            self.prev_touch_pos = touch_pos.copy()
            self.prev_touch_rot = touch_rot.copy()

            # Démarre la cible robot à sa position initiale
            self.target_pos = self.initial_robot_pos.copy()
            self.target_rot = self.initial_robot_rot.copy()

            self.touch_initialized = True
            self.get_logger().info("Première pose touch reçue : référence initialisée (robot à sa position intiale).")
            return

        assert self.prev_touch_pos is not None
        assert self.prev_touch_rot is not None
        assert self.target_pos is not None
        assert self.target_rot is not None

        dpos_touch = touch_pos - self.prev_touch_pos
        dpos_robot = self.position_scale * dpos_touch

        self.target_pos += dpos_robot

        # Différentiel de rotation !
        delta_rot = touch_rot @ self.prev_touch_rot.T
        self.target_rot = delta_rot @ self.target_rot

        self.prev_touch_pos = touch_pos
        self.prev_touch_rot = touch_rot
        
        self.publish_target()

    def publish_target(self) -> None:
        if not self.touch_initialized:
            return
        if self.target_pos is None or self.target_rot is None:
            return

        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "world"

        msg.pose.position.x = float(self.target_pos[0])
        msg.pose.position.y = float(self.target_pos[1])
        msg.pose.position.z = float(self.target_pos[2])

        q = rot_to_quat(self.target_rot)
        msg.pose.orientation.x = float(q[0])
        msg.pose.orientation.y = float(q[1])
        msg.pose.orientation.z = float(q[2])
        msg.pose.orientation.w = float(q[3])

        self.target_pub.publish(msg)

       


def main() -> None:
    rclpy.init()
    node = TouchToTargetPoseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
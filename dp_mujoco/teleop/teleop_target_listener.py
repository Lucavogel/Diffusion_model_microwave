import threading
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Int8, Float32
from dp_mujoco.common.pose_utils import quat_to_rot


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
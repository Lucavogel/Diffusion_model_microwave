from __future__ import annotations

import threading
from typing import Optional

import numpy as np

from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Int8, Float32

from dp_mujoco.common.pose_utils import quat_to_rot


def project_to_so3(R: np.ndarray) -> np.ndarray:
    """
    Reprojette une matrice proche d'une rotation vers SO(3).
    Ça évite la dérive numérique après les multiplications/blends.
    """
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)

    U, _, Vt = np.linalg.svd(R)
    R_proj = U @ Vt

    if np.linalg.det(R_proj) < 0.0:
        U[:, -1] *= -1.0
        R_proj = U @ Vt

    return R_proj


def rot_to_rotvec(R: np.ndarray) -> np.ndarray:
    R = project_to_so3(R)
    cos_angle = (float(np.trace(R)) - 1.0) * 0.5
    cos_angle = float(np.clip(cos_angle, -1.0, 1.0))
    angle = float(np.arccos(cos_angle))

    if angle < 1e-9:
        return np.zeros(3, dtype=np.float64)

    axis = np.array(
        [
            R[2, 1] - R[1, 2],
            R[0, 2] - R[2, 0],
            R[1, 0] - R[0, 1],
        ],
        dtype=np.float64,
    )
    axis = axis / (2.0 * np.sin(angle))
    return axis * angle


def rotvec_to_rot(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64).reshape(3)
    angle = float(np.linalg.norm(v))

    if angle < 1e-9:
        return np.eye(3, dtype=np.float64)

    axis = v / angle
    x, y, z = axis
    K = np.array(
        [
            [0.0, -z, y],
            [z, 0.0, -x],
            [-y, x, 0.0],
        ],
        dtype=np.float64,
    )
    R = (
        np.eye(3, dtype=np.float64)
        + np.sin(angle) * K
        + (1.0 - np.cos(angle)) * (K @ K)
    )
    return project_to_so3(R)


class RealTeleopTargetListener(Node):
    """
    Version robot réel basée sur la version simulation validée.

    Différence avec la simulation :
    - pas de initial_robot_pos / initial_robot_rot hardcodés
    - il faut appeler set_robot_reference(pos, rot)
      avec la pose TCP actuelle du vrai robot calculée par Pinocchio

    Cette classe ne commande PAS le robot.
    Elle produit seulement :
    - target_pos
    - target_rot
    - gripper_cmd
    """

    def __init__(
        self,
        initial_robot_pos: Optional[np.ndarray] = None,
        initial_robot_rot: Optional[np.ndarray] = None,
        position_scale: float = 0.4,
        max_target_speed: float = 0.30,
        target_filter_alpha_pos: float = 0.25,
        target_filter_alpha_rot: float = 0.15,
        gripper_min: float = -0.2,
        gripper_max: float = 1.2,
        gripper_speed: float = 0.5,
        gripper_command_mode: str = "continuous",
        gripper_step_values: tuple[float, float, float] = (-0.2, 0.30, 0.70),
        touch_axis_map: str = "identity",
        touch_rot_map: str = "same_as_position",
        touch_rot_apply: str = "world",
        touch_rot_method: str = "matrix",
    ) -> None:
        super().__init__("real_teleop_target_listener")

        self.free_camera_flag = False

        self.lock = threading.Lock()

        # --------------------------------------------------
        # Target robot
        # --------------------------------------------------
        self.target_pos: Optional[np.ndarray] = None
        self.target_rot: Optional[np.ndarray] = None

        # Target brute avant filtrage
        self.target_raw_pos: Optional[np.ndarray] = None
        self.target_raw_rot: Optional[np.ndarray] = None

        self.gripper_cmd = float(gripper_min)

        # --------------------------------------------------
        # Mapping Touch -> robot
        # --------------------------------------------------
        self.position_scale = float(position_scale)
        self.touch_axis_map = str(touch_axis_map)
        self.touch_pos_map = self._build_touch_pos_map(self.touch_axis_map)
        self.touch_rot_map_name = str(touch_rot_map)
        if self.touch_rot_map_name == "same_as_position":
            self.touch_rot_map = self.touch_pos_map.copy()
        else:
            self.touch_rot_map = self._build_touch_pos_map(self.touch_rot_map_name)
        if touch_rot_apply not in {"world", "local"}:
            raise ValueError(f"Unknown touch_rot_apply: {touch_rot_apply}")
        self.touch_rot_apply = str(touch_rot_apply)
        if touch_rot_method not in {"matrix", "rotvec", "rotvec_inv"}:
            raise ValueError(f"Unknown touch_rot_method: {touch_rot_method}")
        self.touch_rot_method = str(touch_rot_method)

        self.initial_robot_pos = (
            np.asarray(initial_robot_pos, dtype=np.float64).reshape(3).copy()
            if initial_robot_pos is not None
            else None
        )

        self.initial_robot_rot = (
            project_to_so3(np.asarray(initial_robot_rot, dtype=np.float64).reshape(3, 3))
            if initial_robot_rot is not None
            else None
        )

        self.prev_touch_pos: Optional[np.ndarray] = None
        self.prev_touch_rot: Optional[np.ndarray] = None
        self.touch_initialized = False

        # --------------------------------------------------
        # Paramètres validés en simulation
        # --------------------------------------------------

        # Limite de vitesse cartésienne de la target en m/s.
        # Ce n'est PAS pareil que max_joint_vel dans le servo.
        self.max_target_speed = float(max_target_speed)

        # Filtre position :
        # 1.0 = pas de filtre
        # 0.25 = fluide mais encore réactif
        self.target_filter_alpha_pos = float(target_filter_alpha_pos)

        # Filtre orientation :
        # utile seulement si kp_rot > 0 côté servo.
        self.target_filter_alpha_rot = float(target_filter_alpha_rot)

        self.last_pose_time = self.get_clock().now()

        # --------------------------------------------------
        # Gripper
        # --------------------------------------------------
        self.current_buttons = 0

        self.gripper_min = float(gripper_min)
        self.gripper_max = float(gripper_max)
        self.gripper_speed = float(gripper_speed)
        if gripper_command_mode not in {"continuous", "three_state"}:
            raise ValueError(f"Unknown gripper_command_mode: {gripper_command_mode}")
        self.gripper_command_mode = str(gripper_command_mode)
        self.gripper_step_values = tuple(
            max(self.gripper_min, min(self.gripper_max, float(v)))
            for v in gripper_step_values
        )
        if len(self.gripper_step_values) != 3:
            raise ValueError("gripper_step_values must contain exactly three values.")
        self.gripper_step_index = 0
        self.prev_buttons_for_gripper = 0

        self.gripper_value = float(gripper_min)
        self.last_gripper_time = self.get_clock().now()

        sensor_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.pose_sub = self.create_subscription(
            PoseStamped,
            "/touch/pose",
            self.pose_cb,
            sensor_qos,
        )

        self.buttons_sub = self.create_subscription(
            Int8,
            "/touch/buttons",
            self.buttons_cb,
            sensor_qos,
        )

        self.gripper_sub = self.create_subscription(
            Float32,
            "/teleop/gripper_cmd",
            self.gripper_cb,
            sensor_qos,
        )

        self.gripper_timer = self.create_timer(
            0.005,
            self.update_gripper,
        )

    @staticmethod
    def _build_touch_pos_map(name: str) -> np.ndarray:
        if name == "identity":
            return np.eye(3, dtype=np.float64)

        if name == "swap_xy":
            return np.array(
                [
                    [0.0, 1.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float64,
            )

        if name == "swap_xy_neg":
            return np.array(
                [
                    [0.0, -1.0, 0.0],
                    [-1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float64,
            )

        if name == "swap_xy_neg_y":
            return np.array(
                [
                    [0.0, 1.0, 0.0],
                    [-1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float64,
            )

        if name == "swap_xy_neg_x":
            return np.array(
                [
                    [0.0, -1.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float64,
            )

        if name == "neg_xy":
            return np.array(
                [
                    [-1.0, 0.0, 0.0],
                    [0.0, -1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float64,
            )

        raise ValueError(f"Unknown touch_axis_map: {name}")

    def set_robot_reference(self, pos: np.ndarray, rot: np.ndarray) -> None:
        """
        Définit la pose TCP de référence du vrai robot.

        À appeler au démarrage avec la pose actuelle calculée par Pinocchio :

            q_current = robot.get_joint_positions()
            pos, rot, _ = servo.kin.forward_and_jacobian(q_current)
            listener.set_robot_reference(pos, rot)

        pos et rot doivent être dans le repère base robot.
        """
        with self.lock:
            self.initial_robot_pos = np.asarray(pos, dtype=np.float64).reshape(3).copy()
            self.initial_robot_rot = project_to_so3(
                np.asarray(rot, dtype=np.float64).reshape(3, 3)
            )

            self.target_pos = None
            self.target_rot = None

            self.target_raw_pos = None
            self.target_raw_rot = None

            self.prev_touch_pos = None
            self.prev_touch_rot = None
            self.touch_initialized = False

            self.last_pose_time = self.get_clock().now()

            try:
                self.get_logger().info("Robot reference pose updated.")
            except Exception:
                pass

    def reset_after_robot_reset(self) -> None:
        """
        Même logique que reset_after_sim_reset().
        À appeler si tu recales/recentres le robot.
        """
        with self.lock:
            self.current_buttons = 0
            self.gripper_value = self.gripper_min
            self.gripper_cmd = self.gripper_min
            self.gripper_step_index = 0
            self.prev_buttons_for_gripper = 0
            self.last_gripper_time = self.get_clock().now()

            self.target_pos = None
            self.target_rot = None

            self.target_raw_pos = None
            self.target_raw_rot = None

            self.prev_touch_pos = None
            self.prev_touch_rot = None
            self.touch_initialized = False

            self.last_pose_time = self.get_clock().now()

    def pose_cb(self, msg: PoseStamped) -> None:
        touch_pos = np.array(
            [
                msg.pose.position.x,
                msg.pose.position.y,
                msg.pose.position.z,
            ],
            dtype=np.float64,
        )

        touch_rot = quat_to_rot(
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        )

        touch_rot = project_to_so3(touch_rot)

        now = self.get_clock().now()

        with self.lock:
            dt = (now - self.last_pose_time).nanoseconds * 1e-9
            self.last_pose_time = now

            # Protection si le callback a été interrompu longtemps
            if dt <= 1e-6 or dt > 0.5:
                dt = 0.01

            if self.initial_robot_pos is None or self.initial_robot_rot is None:
                return

            if not self.touch_initialized:
                self.prev_touch_pos = touch_pos.copy()
                self.prev_touch_rot = touch_rot.copy()

                self.target_raw_pos = self.initial_robot_pos.copy()
                self.target_raw_rot = self.initial_robot_rot.copy()

                self.target_pos = self.initial_robot_pos.copy()
                self.target_rot = self.initial_robot_rot.copy()

                self.touch_initialized = True

                try:
                    self.get_logger().info(
                        "Première pose Touch reçue : référence robot réel initialisée."
                    )
                except Exception:
                    pass

                return

            # --------------------------------------------------
            # 1. Différentiel position Touch -> robot
            # --------------------------------------------------
            dpos_touch = touch_pos - self.prev_touch_pos
            dpos_robot = self.position_scale * (self.touch_pos_map @ dpos_touch)

            # --------------------------------------------------
            # 2. Max speed cartésien de la target
            # --------------------------------------------------
            max_step = self.max_target_speed * dt
            step_norm = float(np.linalg.norm(dpos_robot))

            if step_norm > max_step and step_norm > 1e-12:
                dpos_robot = dpos_robot * (max_step / step_norm)

            self.target_raw_pos = self.target_raw_pos + dpos_robot

            # --------------------------------------------------
            # 3. Différentiel orientation
            # --------------------------------------------------
            delta_rot = touch_rot @ self.prev_touch_rot.T

            if self.touch_rot_method == "matrix":
                delta_rot_robot = self.touch_rot_map @ delta_rot @ self.touch_rot_map.T
            else:
                delta_rotvec = rot_to_rotvec(delta_rot)
                if self.touch_rot_method == "rotvec_inv":
                    delta_rotvec = -delta_rotvec
                delta_rotvec_robot = self.touch_rot_map @ delta_rotvec
                delta_rot_robot = rotvec_to_rot(delta_rotvec_robot)

            if self.touch_rot_apply == "world":
                self.target_raw_rot = delta_rot_robot @ self.target_raw_rot
            else:
                self.target_raw_rot = self.target_raw_rot @ delta_rot_robot
            self.target_raw_rot = project_to_so3(self.target_raw_rot)

            # --------------------------------------------------
            # 4. Filtre position
            # --------------------------------------------------
            alpha_pos = float(np.clip(self.target_filter_alpha_pos, 0.0, 1.0))

            self.target_pos = (
                (1.0 - alpha_pos) * self.target_pos
                + alpha_pos * self.target_raw_pos
            )

            # --------------------------------------------------
            # 5. Orientation smoothing
            # --------------------------------------------------
            alpha_rot = float(np.clip(self.target_filter_alpha_rot, 0.0, 1.0))

            R_blend = (
                (1.0 - alpha_rot) * self.target_rot
                + alpha_rot * self.target_raw_rot
            )

            self.target_rot = project_to_so3(R_blend)

            self.prev_touch_pos = touch_pos.copy()
            self.prev_touch_rot = touch_rot.copy()

    def gripper_cb(self, msg: Float32) -> None:
        with self.lock:
            if self.gripper_command_mode == "three_state":
                return

            value = float(msg.data)
            value = max(self.gripper_min, min(self.gripper_max, value))

            self.gripper_cmd = value
            self.gripper_value = value

    def buttons_cb(self, msg: Int8) -> None:
        with self.lock:
            self.current_buttons = int(msg.data)

    def update_gripper(self) -> None:
        with self.lock:
            now = self.get_clock().now()
            dt = (now - self.last_gripper_time).nanoseconds * 1e-9
            self.last_gripper_time = now

            if dt <= 1e-6 or dt > 0.5:
                dt = 0.005

            if self.gripper_command_mode == "three_state":
                # Edge-triggered gripper: one close-button click moves
                # open -> narrow -> grasp, while the open button returns to open.
                if self.current_buttons != 0 and self.prev_buttons_for_gripper == 0:
                    if self.current_buttons == -1:
                        self.gripper_step_index = min(2, self.gripper_step_index + 1)
                    elif self.current_buttons == 1:
                        self.gripper_step_index = 0

                self.prev_buttons_for_gripper = int(self.current_buttons)
                self.gripper_value = float(self.gripper_step_values[self.gripper_step_index])
                self.gripper_cmd = float(self.gripper_value)
                return

            if self.current_buttons == 1:
                self.gripper_value -= self.gripper_speed * dt
            elif self.current_buttons == -1:
                self.gripper_value += self.gripper_speed * dt

            self.gripper_value = max(
                self.gripper_min,
                min(self.gripper_max, self.gripper_value),
            )

            self.gripper_cmd = float(self.gripper_value)

    def get_target(self):
        with self.lock:
            if self.target_pos is None or self.target_rot is None:
                return None, None, float(self.gripper_cmd)

            return (
                self.target_pos.copy(),
                self.target_rot.copy(),
                float(self.gripper_cmd),
            )

    def get_target_age_seconds(self) -> Optional[float]:
        with self.lock:
            if not self.touch_initialized:
                return None

            now = self.get_clock().now()
            return float((now - self.last_pose_time).nanoseconds * 1e-9)

    def get_gripper_buttons(self) -> int:
        with self.lock:
            return int(self.current_buttons)

    def sync_to_pose(self, pos: np.ndarray, rot: np.ndarray) -> None:
        """
        Force la target à suivre la pose actuelle du robot.
        À utiliser en pause/safety/stop.
        """
        with self.lock:
            if self.target_pos is not None and self.target_rot is not None:
                pos = np.asarray(pos, dtype=np.float64).reshape(3)
                rot = project_to_so3(np.asarray(rot, dtype=np.float64).reshape(3, 3))

                self.target_pos = pos.copy()
                self.target_rot = rot.copy()

                self.target_raw_pos = pos.copy()
                self.target_raw_rot = rot.copy()

    def progressive_sync(
        self,
        pos: np.ndarray,
        rot: np.ndarray,
        freeze_alpha: float = 0.15,
    ) -> None:
        """
        Même logique que la simulation.
        Ramène progressivement la target vers la pose réelle du robot.
        """
        with self.lock:
            if self.target_pos is not None and self.target_rot is not None:
                pos = np.asarray(pos, dtype=np.float64).reshape(3)
                rot = project_to_so3(np.asarray(rot, dtype=np.float64).reshape(3, 3))

                self.target_pos = (
                    (1.0 - freeze_alpha) * self.target_pos
                    + freeze_alpha * pos
                )

                R_blend = (
                    (1.0 - freeze_alpha) * self.target_rot
                    + freeze_alpha * rot
                )

                self.target_rot = project_to_so3(R_blend)

                self.target_raw_pos = self.target_pos.copy()
                self.target_raw_rot = self.target_rot.copy()

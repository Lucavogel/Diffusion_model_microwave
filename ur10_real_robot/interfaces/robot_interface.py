from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class RobotInterface(ABC):
    """
    Interface commune pour le robot réel UR10.

    Le backend peut être :
    - URX
    - RTDE
    - ROS driver
    - Fake backend / dry-run

    Convention importante :
    - joint positions : radians, shape (6,)
    - joint velocities : rad/s, shape (6,)
    - eef_quat : quaternion wxyz, shape (4,)
    """

    @abstractmethod
    def connect(self) -> None:
        """Connect to the robot."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the robot."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the robot safely."""
        pass

    @abstractmethod
    def get_joint_positions(self) -> np.ndarray:
        """Return current joint positions q, shape (6,), in radians."""
        pass

    @abstractmethod
    def get_joint_velocities(self) -> np.ndarray:
        """Return current joint velocities qvel, shape (6,), in rad/s."""
        pass

    @abstractmethod
    def get_eef_pos(self) -> np.ndarray:
        """Return current TCP/end-effector position, shape (3,), in robot base frame."""
        pass

    @abstractmethod
    def get_eef_quat(self) -> np.ndarray:
        """
        Return current TCP/end-effector orientation as quaternion wxyz, shape (4,).

        Important:
        In ROS PoseStamped, quaternion is xyzw.
        In our dataset/controller convention, quaternion is wxyz.
        """
        pass

    @abstractmethod
    def get_gripper_qpos(self) -> np.ndarray:
        """Return current gripper position, shape (1,) or compatible."""
        pass

    @abstractmethod
    def apply_joint_command(
        self,
        q_target: np.ndarray,
        gripper_command: Optional[float] = None,
    ) -> None:
        """
        Apply a joint position command to the robot.

        q_target:
            shape (6,), radians

        gripper_command:
            optional command for gripper
        """
        pass

    def apply_joint_velocity(
        self,
        qd_target: np.ndarray,
        gripper_command: Optional[float] = None,
    ) -> None:
        """
        Optional joint velocity command, shape (6,), rad/s.

        Backends that do not support velocity control can keep the position
        command path. Real CB2 speedj teleop overrides this method.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement apply_joint_velocity()."
        )

    def get_state(self) -> dict[str, np.ndarray]:
        """
        Return common robot state.

        This default implementation avoids rewriting the same function
        in every backend.
        """
        return {
            "joint_positions": self.get_joint_positions(),
            "joint_velocities": self.get_joint_velocities(),
            "eef_pos": self.get_eef_pos(),
            "eef_quat": self.get_eef_quat(),
            "gripper_qpos": self.get_gripper_qpos(),
        }

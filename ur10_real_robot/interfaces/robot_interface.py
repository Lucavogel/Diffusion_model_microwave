from __future__ import annotations
from typing import Optional
import numpy as np
from abc import ABC, abstractmethod

class RobotInterface(ABC):
    "Robot interface for UR10 real robot."

    @abstractmethod
    def connect(self) -> None:
        "Connect to the robot."
        pass

    @abstractmethod
    def close(self) -> None:
        "Close the connection to the robot."
        pass

    @abstractmethod
    def stop(self) -> None:
        "Stop the robot immediately."
        pass

    @abstractmethod
    def get_joint_positions(self) -> np.ndarray:
        "Get the current joint positions."
        pass

    @abstractmethod
    def get_joint_velocities(self) -> np.ndarray:
        "Get the current joint velocities."
        pass

    @abstractmethod
    def get_eef_pos(self) -> np.ndarray:
        "Get the current end-effector position (x, y, z)."
        pass

    @abstractmethod
    def get_eef_quat(self) -> np.ndarray:
        "Get the current end-effector orientation as a quaternion (x, y, z, w)."
        pass

    @abstractmethod
    def get_gripper_qpos(self) -> np.ndarray:
        "Get the current gripper joint positions."
        pass

    @abstractmethod
    def apply_joint_command(self, q_target: np.ndarray, gripper_command: Optional[float] = None) -> None:
        "Apply a joint position command to the robot. Optionally include a gripper command."
        pass

    @abstractmethod
    def get_state(self) -> dict:
        "Get the current state of the robot as a dictionary containing joint positions, velocities, end-effector pose, etc."
        pass
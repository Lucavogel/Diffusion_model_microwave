from __future__ import annotations

from pathlib import Path

import numpy as np
import pinocchio as pin


def skew(v: np.ndarray) -> np.ndarray:
    x, y, z = v
    return np.array(
        [
            [0.0, -z, y],
            [z, 0.0, -x],
            [-y, x, 0.0],
        ],
        dtype=np.float64,
    )


class UR10PinocchioKinematics:
    def __init__(
        self,
        urdf_path: str | Path,
        ee_frame_name: str = "tool0",
        tcp_offset_pos: np.ndarray | None = None,
        tcp_offset_rot: np.ndarray | None = None,
        base_offset_pos: np.ndarray | None = None,
        base_offset_rot: np.ndarray | None = None,
    ) -> None:
        self.urdf_path = str(urdf_path)

        self.model = pin.buildModelFromUrdf(self.urdf_path)
        self.data = self.model.createData()

        self.ee_frame_name = ee_frame_name
        self.ee_frame_id = self.model.getFrameId(ee_frame_name)

        if self.ee_frame_id >= len(self.model.frames):
            raise ValueError(f"Frame not found in URDF: {ee_frame_name}")

        if tcp_offset_pos is None:
            tcp_offset_pos = np.zeros(3, dtype=np.float64)

        if tcp_offset_rot is None:
            tcp_offset_rot = np.eye(3, dtype=np.float64)

        if base_offset_pos is None:
            base_offset_pos = np.zeros(3, dtype=np.float64)

        if base_offset_rot is None:
            base_offset_rot = np.eye(3, dtype=np.float64)

        self.tcp_offset_pos = np.asarray(tcp_offset_pos, dtype=np.float64)
        self.tcp_offset_rot = np.asarray(tcp_offset_rot, dtype=np.float64)

        self.base_offset_pos = np.asarray(base_offset_pos, dtype=np.float64)
        self.base_offset_rot = np.asarray(base_offset_rot, dtype=np.float64)

    def forward(self, q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        q = np.asarray(q, dtype=np.float64).reshape(-1)

        pin.forwardKinematics(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)

        frame_pose = self.data.oMf[self.ee_frame_id]

        pos_tool = frame_pose.translation.copy()
        rot_tool = frame_pose.rotation.copy()

        pos_tcp_local = pos_tool + rot_tool @ self.tcp_offset_pos
        rot_tcp_local = rot_tool @ self.tcp_offset_rot

        pos_tcp_world = self.base_offset_pos + self.base_offset_rot @ pos_tcp_local
        rot_tcp_world = self.base_offset_rot @ rot_tcp_local

        return pos_tcp_world, rot_tcp_world

    def jacobian(self, q: np.ndarray) -> np.ndarray:
        q = np.asarray(q, dtype=np.float64).reshape(-1)

        pin.forwardKinematics(self.model, self.data, q)
        pin.computeJointJacobians(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)

        frame_pose = self.data.oMf[self.ee_frame_id]
        rot_tool = frame_pose.rotation.copy()

        J_tool = pin.computeFrameJacobian(
            self.model,
            self.data,
            q,
            self.ee_frame_id,
            pin.ReferenceFrame.LOCAL_WORLD_ALIGNED,
        )

        J_tool = np.asarray(J_tool, dtype=np.float64)

        Jv_tool = J_tool[:3, :]
        Jw_tool = J_tool[3:, :]

        r_local = rot_tool @ self.tcp_offset_pos
        r_world = self.base_offset_rot @ r_local

        Jv_world = self.base_offset_rot @ Jv_tool
        Jw_world = self.base_offset_rot @ Jw_tool

        Jv_tcp = Jv_world - skew(r_world) @ Jw_world

        J_tcp = np.vstack([Jv_tcp, Jw_world])

        return J_tcp

    def forward_and_jacobian(self, q: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        pos, rot = self.forward(q)
        J = self.jacobian(q)

        return pos, rot, J
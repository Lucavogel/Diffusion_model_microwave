from __future__ import annotations

import importlib.util
from pathlib import Path


_COMMON_POSE_UTILS = Path(__file__).resolve().parents[1] / "common" / "pose_utils.py"
_spec = importlib.util.spec_from_file_location("mujoco_common_pose_utils", _COMMON_POSE_UTILS)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load pose utils from {_COMMON_POSE_UTILS}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

quat_to_rot = _module.quat_to_rot
rot_to_quat = _module.rot_to_quat
quat_slerp = _module.quat_slerp
rot6d_to_rotmat = _module.rot6d_to_rotmat
orientation_error = _module.orientation_error

__all__ = [
    "quat_to_rot",
    "rot_to_quat",
    "quat_slerp",
    "rot6d_to_rotmat",
    "orientation_error",
]

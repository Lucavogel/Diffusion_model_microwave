import numpy as np


__all__ = [
    "quat_to_rot",
    "rot_to_quat",
    "quat_slerp",
    "rot6d_to_rotmat",
    "orientation_error",
]

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
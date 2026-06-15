import argparse
import numpy as np
import mujoco


def rot_to_quat_wxyz(R: np.ndarray) -> np.ndarray:
    R = np.asarray(R, dtype=np.float64)
    trace = np.trace(R)

    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s

    q = np.array([w, x, y, z], dtype=np.float64)
    q /= np.linalg.norm(q)
    return q


def print_array(name: str, arr: np.ndarray) -> None:
    arr = np.asarray(arr)
    print(f"{name} = np.array(")
    print(np.array2string(arr, precision=8, separator=", "))
    print(", dtype=np.float64)")


def get_body_pose(model, data, body_name: str) -> tuple[np.ndarray, np.ndarray]:
    body_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        body_name,
    )

    if body_id == -1:
        print("\nBodies disponibles :")
        for i in range(model.nbody):
            name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
            print(i, name)
        raise ValueError(f"Body not found: {body_name}")

    pos = data.xpos[body_id].copy()
    rot = data.xmat[body_id].reshape(3, 3).copy()

    return pos, rot


def apply_manual_offset(
    pos: np.ndarray,
    rot: np.ndarray,
    offset: np.ndarray,
    frame: str,
) -> np.ndarray:
    pos = np.asarray(pos, dtype=np.float64).reshape(3)
    rot = np.asarray(rot, dtype=np.float64).reshape(3, 3)
    offset = np.asarray(offset, dtype=np.float64).reshape(3)

    if frame == "local":
        return pos + rot @ offset

    if frame == "world":
        return pos + offset

    raise ValueError(f"Unknown offset frame: {frame}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--xml",
        required=True,
        help="Path to the MuJoCo scene XML",
    )

    parser.add_argument(
        "--body",
        default="tool0",
        help="Body name used as tool reference. Default: tool0",
    )

    parser.add_argument(
        "--home",
        nargs=6,
        type=float,
        default=[0.0, -1.3, 1.8, -0.22, 1.57, 0.0],
        help="Initial robot joint pose",
    )

    parser.add_argument(
        "--gripper",
        type=float,
        default=-0.2,
        help="Initial gripper command",
    )

    parser.add_argument(
        "--manual-offset",
        nargs=3,
        type=float,
        default=[0.0, 0.0, 0.24],
        help="Manual TCP offset from tool0, expressed in tool0 frame",
    )

    parser.add_argument(
        "--offset-frame",
        choices=["local", "world"],
        default="local",
        help="local = offset in tool0 frame, world = offset in MuJoCo world",
    )

    args = parser.parse_args()

    model = mujoco.MjModel.from_xml_path(args.xml)
    data = mujoco.MjData(model)

    home_q = np.asarray(args.home, dtype=np.float64)
    manual_offset = np.asarray(args.manual_offset, dtype=np.float64)

    data.qpos[:6] = home_q

    if model.nu >= 6:
        data.ctrl[:6] = home_q

    if model.nu >= 7:
        data.ctrl[6] = args.gripper

    mujoco.mj_forward(model, data)

    tool_pos, tool_rot = get_body_pose(
        model=model,
        data=data,
        body_name=args.body,
    )

    tool_quat_wxyz = rot_to_quat_wxyz(tool_rot)

    tcp_pos = apply_manual_offset(
        pos=tool_pos,
        rot=tool_rot,
        offset=manual_offset,
        frame=args.offset_frame,
    )

    tcp_rot = tool_rot.copy()
    tcp_quat_wxyz = rot_to_quat_wxyz(tcp_rot)

    print("\n==============================")
    print("MODEL INFO")
    print("==============================")
    print("xml:", args.xml)
    print("nq:", model.nq)
    print("nv:", model.nv)
    print("nu:", model.nu)
    print("njnt:", model.njnt)
    print("tool body:", args.body)

    print("\n==============================")
    print("HOME")
    print("==============================")
    print_array("home_q", home_q)

    print("\n==============================")
    print("TOOL0 POSE")
    print("==============================")
    print_array("tool0_pos", tool_pos)
    print_array("tool0_rot", tool_rot)
    print_array("tool0_quat_wxyz", tool_quat_wxyz)

    print("\n==============================")
    print("MANUAL OFFSET FROM TOOL0")
    print("==============================")
    print_array("manual_offset", manual_offset)
    print("offset_frame:", args.offset_frame)

    print("\n==============================")
    print("TCP / GRIPPER POSE COMPUTED FROM TOOL0 + OFFSET")
    print("==============================")
    print_array("initial_robot_pos", tcp_pos)
    print_array("initial_robot_rot", tcp_rot)
    print_array("initial_robot_quat_wxyz", tcp_quat_wxyz)

    print("\n==============================")
    print("DIFF TCP - TOOL0")
    print("==============================")
    print_array("diff_pos", tcp_pos - tool_pos)

    print("\n==============================")
    print("CAMERAS")
    print("==============================")
    for i in range(model.ncam):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_CAMERA, i)
        print(i, name)

    print("\n==============================")
    print("ACTUATORS")
    print("==============================")
    for i in range(model.nu):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
        print(i, name)

    print("\n==============================")
    print("JOINTS")
    print("==============================")
    for i in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        print(i, name)


if __name__ == "__main__":
    main()
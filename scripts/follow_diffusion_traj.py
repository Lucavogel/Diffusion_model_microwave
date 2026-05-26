import argparse
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np
import matplotlib.pyplot as plt

def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a recorded MuJoCo qpos trajectory")
    parser.add_argument(
        "npz_path",
        nargs="?",
        default="/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/data/outputs/smooth_trajectory.npz",
        help="Path to the recorded NPZ file",
    )
    parser.add_argument(
        "--model_xml",
        default="/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_microwave.xml",
        help="MuJoCo XML scene used for replay",
    )
    parser.add_argument(
        "--fallback_fps",
        type=float,
        default=30.0,
        help="Playback FPS used when the NPZ does not contain timestamps",
    )
    parser.add_argument(
        "--speed_factor",
        type=float,
        default=1.0,
        help="Replay speed multiplier. >1 is faster, <1 is slower",
    )
    args = parser.parse_args()

    npz = np.load(args.npz_path)
    qpos_traj = npz["qpos"]
    recorded_time = npz["time"]
    print (f"Loaded trajectory from {args.npz_path}: {len(qpos_traj)} steps, time range = [{recorded_time[0]:.2f}s, {recorded_time[-1]:.2f}s]")
    
    # Calcul de la vitesse et de l'accélération par différences finies
    qvel_traj = np.gradient(qpos_traj, recorded_time, axis=0)
    qacc_traj = np.gradient(qvel_traj, recorded_time, axis=0)

    fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    # Plot positions
    axs[0].plot(recorded_time, qpos_traj[:, :6])
    axs[0].set_ylabel("Positions (rad)")
    axs[0].set_title("Trajectories des joints (qpos, qvel, qacc)")
    axs[0].grid()

    # Plot vitesses
    axs[1].plot(recorded_time, qvel_traj[:, :6])
    axs[1].set_ylabel("Vitesses (rad/s)")
    axs[1].grid()

    # Plot accélérations
    axs[2].plot(recorded_time, qacc_traj[:, :6])
    axs[2].set_xlabel("Time (s)")
    axs[2].set_ylabel("Accélérations (rad/s²)")
    axs[2].grid()

    fig.legend([f"joint_{i}" for i in range(6)], loc='upper right')
    plt.tight_layout()
    plt.show()
    
    if args.speed_factor <= 0.0:
        raise ValueError("speed_factor must be > 0")

    # Rendering is the bottleneck for very large speed factors.
    # Skip frames when speed_factor > 1 to make the acceleration visible.
    frame_stride = max(1, int(np.floor(args.speed_factor)))
    if frame_stride > 1:
        print(f"Using frame stride {frame_stride} for faster replay")
    
        

    model_path = Path(args.model_xml)
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data_model = mujoco.MjData(model)

    home_qpos = np.array([0.0, -1.3, 1.8, -0.22, 1.57, 0.0], dtype=float)
    data_model.qpos[:6] = home_qpos.copy()
    data_model.qvel[:6] = 0.0
    mujoco.mj_forward(model, data_model)

    try:
        with mujoco.viewer.launch_passive(model, data_model) as viewer:
            prev_t = None
            for idx in range(0, len(qpos_traj), frame_stride):
                if not viewer.is_running():
                    break

                data_model.qpos[:] = qpos_traj[idx]
                data_model.qvel[:] = 0.0
                mujoco.mj_forward(model, data_model)
                viewer.sync()

                if recorded_time is not None and idx < len(recorded_time):
                    current_t = float(recorded_time[idx])
                    if prev_t is not None:
                        dt = max(0.0, current_t - prev_t)
                        time.sleep(dt / max(args.speed_factor, 1e-6))
                    prev_t = current_t
                else:
                    time.sleep(1.0 / max(args.fallback_fps * max(args.speed_factor, 1e-6), 1e-6))

    except KeyboardInterrupt:
        print("Arrêt demandé.")
    finally:
        print("Fin du script.")


if __name__ == "__main__":
    main()
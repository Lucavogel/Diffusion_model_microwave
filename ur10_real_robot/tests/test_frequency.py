#!/usr/bin/env python3
from __future__ import annotations

import os
import time
import numpy as np
import urx


ROBOT_IP = os.environ.get("ROBOT_IP", "192.168.2.100")
TARGET_HZ = 150.0   # commence à 10 Hz
N_STEPS = 300


def pose_to_xyzrpy(transform):
    pv = transform.pose_vector
    pose = np.array(pv.get_array(), dtype=np.float64).reshape(-1)

    if pose.shape[0] != 6:
        raise ValueError(f"Pose inattendue: shape={pose.shape}, value={pose}")

    return pose


def main() -> None:
    dt_target = 1.0 / TARGET_HZ

    rob = None
    read_times = []
    loop_times = []
    missed_deadlines = 0

    print("-------------------------------------------")
    print("UR10 CB2 - URX READ FREQUENCY TEST")
    print("-------------------------------------------")
    print(f"Robot IP  : {ROBOT_IP}")
    print(f"Target Hz : {TARGET_HZ}")
    print(f"Target dt : {dt_target:.4f} s")
    print(f"Steps     : {N_STEPS}")
    print("Motion    : disabled / lecture seule")
    print("-------------------------------------------")

    try:
        rob = urx.Robot(ROBOT_IP)
        print("[OK] Connected to robot.")

        next_t = time.monotonic()
        last_loop_t = time.monotonic()

        for i in range(N_STEPS):
            loop_start = time.monotonic()

            read_start = time.monotonic()

            q = np.array(rob.getj(), dtype=np.float64)
            pose = pose_to_xyzrpy(rob.get_pose())

            read_end = time.monotonic()

            read_times.append(read_end - read_start)
            loop_times.append(loop_start - last_loop_t)
            last_loop_t = loop_start

            if i % 50 == 0:
                print(
                    f"[{i:04d}] "
                    f"read={1000.0 * read_times[-1]:.2f} ms | "
                    f"q deg={np.round(np.degrees(q), 2)} | "
                    f"tcp z={pose[2]:.4f}"
                )

            next_t += dt_target
            sleep_time = next_t - time.monotonic()

            if sleep_time > 0.0:
                time.sleep(sleep_time)
            else:
                missed_deadlines += 1
                next_t = time.monotonic()

        read_times = np.array(read_times, dtype=np.float64)
        loop_times = np.array(loop_times[1:], dtype=np.float64)

        effective_hz = 1.0 / np.mean(loop_times)

        print("\n-------------------------------------------")
        print("RESULTS")
        print("-------------------------------------------")

        print("READ TIME:")
        print(f"mean : {np.mean(read_times):.6f} s")
        print(f"min  : {np.min(read_times):.6f} s")
        print(f"max  : {np.max(read_times):.6f} s")
        print(f"p95  : {np.percentile(read_times, 95):.6f} s")
        print(f"p99  : {np.percentile(read_times, 99):.6f} s")

        print("\nLOOP PERIOD:")
        print(f"mean : {np.mean(loop_times):.6f} s")
        print(f"min  : {np.min(loop_times):.6f} s")
        print(f"max  : {np.max(loop_times):.6f} s")
        print(f"p95  : {np.percentile(loop_times, 95):.6f} s")
        print(f"p99  : {np.percentile(loop_times, 99):.6f} s")

        print("\nFREQUENCY:")
        print(f"target Hz        : {TARGET_HZ:.2f}")
        print(f"effective Hz     : {effective_hz:.2f}")
        print(f"missed deadlines : {missed_deadlines}/{N_STEPS}")

        print("-------------------------------------------")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        if rob is not None:
            try:
                rob.close()
                print("[OK] Robot connection closed.")
            except Exception:
                pass


if __name__ == "__main__":
    main()
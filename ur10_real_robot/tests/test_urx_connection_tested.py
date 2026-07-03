#!/usr/bin/env python3
from __future__ import annotations

import os
import time

import numpy as np
import urx


ROBOT_IP = os.environ.get("ROBOT_IP", "192.168.2.100")


def pose_to_xyzrpy(transform):
    """
    Convertit rob.get_pose() en [x, y, z, rx, ry, rz].
    """
    pv = transform.pose_vector
    pose = np.array(pv.get_array(), dtype=np.float64).reshape(-1)

    if pose.shape[0] != 6:
        raise ValueError(f"Pose inattendue: shape={pose.shape}, value={pose}")

    return pose


def main() -> None:
    rob = None

    print("-------------------------------------------")
    print("UR10 CB2 - URX READ ONLY TEST")
    print("-------------------------------------------")
    print(f"Robot IP : {ROBOT_IP}")
    print("Mode     : lecture seule, aucun mouvement")
    print("-------------------------------------------")

    try:
        print("[INFO] Connexion au robot...")
        rob = urx.Robot(ROBOT_IP)
        print("[OK] Connexion URX OK")

        for i in range(10):
            q = np.array(rob.getj(), dtype=np.float64)

            pose_transform = rob.get_pose()
            pose = pose_to_xyzrpy(pose_transform)

            print(f"\n[{i}]")
            print("q rad :", np.round(q, 6))
            print("q deg :", np.round(np.degrees(q), 3))
            print("tcp   :", np.round(pose, 6))
            print("format tcp = [x, y, z, rx, ry, rz]")
            print("-" * 40)

            time.sleep(0.5)

        print("\nLecture stable OK.")

    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur.")

    except Exception as e:
        print("[ERREUR]", e)

    finally:
        if rob is not None:
            try:
                rob.close()
                print("[OK] Connexion fermée.")
            except Exception:
                pass


if __name__ == "__main__":
    main()
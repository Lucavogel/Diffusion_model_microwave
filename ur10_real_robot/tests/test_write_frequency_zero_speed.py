#!/usr/bin/env python3
from __future__ import annotations

import os
import time
import numpy as np
import urx


ROBOT_IP = os.environ.get("ROBOT_IP", "192.168.2.100")

TARGET_HZ = 10.0   # commence à 10, puis 20, puis 30
DURATION = 5.0

ACC = 0.05         # rad/s², très faible
Q_ZERO = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


def main():
    dt = 1.0 / TARGET_HZ
    n_steps = int(DURATION * TARGET_HZ)

    print("-------------------------------------------")
    print("UR10 CB2 - ZERO SPEED WRITE FREQUENCY TEST")
    print("-------------------------------------------")
    print(f"Robot IP   : {ROBOT_IP}")
    print(f"Target Hz  : {TARGET_HZ}")
    print(f"Duration   : {DURATION} s")
    print(f"Steps      : {n_steps}")
    print("Command    : speedj([0,0,0,0,0,0])")
    print("-------------------------------------------")
    print("ATTENTION : ce test envoie des commandes au vrai robot.")
    print("La vitesse demandée est zéro, donc il ne devrait pas bouger.")
    print("Speed slider tablette : 5% ou 10%.")
    print("Main proche de l'arrêt d'urgence.")
    print("-------------------------------------------")

    answer = input("Tape YES pour lancer : ")
    if answer.strip() != "YES":
        print("Annulé.")
        return

    rob = None
    send_times = []
    loop_periods = []
    missed_deadlines = 0

    try:
        rob = urx.Robot(ROBOT_IP)
        print("[OK] Connected.")

        q_start = np.array(rob.getj(), dtype=np.float64)
        print("q start deg:", np.round(np.degrees(q_start), 4))

        next_t = time.monotonic()
        last_loop_t = time.monotonic()

        for i in range(n_steps):
            loop_start = time.monotonic()
            loop_periods.append(loop_start - last_loop_t)
            last_loop_t = loop_start

            send_start = time.monotonic()

            # Commande vitesse articulaire nulle pendant un peu plus qu'un cycle
            # Si ton URX n'a pas speedj(), on fera une version raw URScript.
            rob.speedj(Q_ZERO, ACC, dt * 1.5)

            send_end = time.monotonic()
            send_times.append(send_end - send_start)

            if i % max(1, int(TARGET_HZ)) == 0:
                q_now = np.array(rob.getj(), dtype=np.float64)
                drift_deg = np.degrees(q_now - q_start)
                print(
                    f"[{i:04d}] "
                    f"send={1000.0 * send_times[-1]:.2f} ms | "
                    f"drift max={np.max(np.abs(drift_deg)):.5f} deg"
                )

            next_t += dt
            sleep_time = next_t - time.monotonic()

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                missed_deadlines += 1
                next_t = time.monotonic()

        # Stop propre après le test
        try:
            rob.stopj(acc=0.1)
        except Exception:
            try:
                rob.stop()
            except Exception:
                pass

        q_end = np.array(rob.getj(), dtype=np.float64)
        drift_deg = np.degrees(q_end - q_start)

        send_times = np.array(send_times, dtype=np.float64)
        loop_periods = np.array(loop_periods[1:], dtype=np.float64)

        print("\n-------------------------------------------")
        print("RESULTS")
        print("-------------------------------------------")
        print("SEND TIME:")
        print(f"mean : {np.mean(send_times):.6f} s")
        print(f"min  : {np.min(send_times):.6f} s")
        print(f"max  : {np.max(send_times):.6f} s")
        print(f"p95  : {np.percentile(send_times, 95):.6f} s")
        print(f"p99  : {np.percentile(send_times, 99):.6f} s")

        print("\nLOOP PERIOD:")
        print(f"mean : {np.mean(loop_periods):.6f} s")
        print(f"min  : {np.min(loop_periods):.6f} s")
        print(f"max  : {np.max(loop_periods):.6f} s")

        print("\nFREQUENCY:")
        print(f"target Hz        : {TARGET_HZ:.2f}")
        print(f"effective Hz     : {1.0 / np.mean(loop_periods):.2f}")
        print(f"missed deadlines : {missed_deadlines}/{n_steps}")

        print("\nDRIFT:")
        print("q drift deg      :", np.round(drift_deg, 6))
        print("max drift deg    :", np.max(np.abs(drift_deg)))
        print("-------------------------------------------")

    except Exception as e:
        print("[ERROR]", e)
        if rob is not None:
            try:
                rob.stop()
                print("[OK] Stop envoyé.")
            except Exception:
                pass

    finally:
        if rob is not None:
            try:
                rob.close()
                print("[OK] Connection closed.")
            except Exception:
                pass


if __name__ == "__main__":
    main()
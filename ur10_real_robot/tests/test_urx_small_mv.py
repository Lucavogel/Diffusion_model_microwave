import urx
import time
import numpy as np

ROBOT_IP = "192.168.0.60"

ACCELERATION = 0.05   # très lent
VELOCITY = 0.03       # très lent

JOINT_ID = 0          # 0 = base, 1 = shoulder, etc.
DELTA_DEG = 2.0       # petit mouvement en degrés


def main():
    rob = None

    try:
        print(f"Connexion à {ROBOT_IP}...")
        rob = urx.Robot(ROBOT_IP)
        print("Connexion URX OK")

        # Lire la position actuelle
        q_current = np.array(rob.getj(), dtype=float)
        print("Joints actuels en radians :")
        print(q_current)

        print("Joints actuels en degrés :")
        print(np.degrees(q_current))

        # Créer une cible proche de la position actuelle
        q_target = q_current.copy()
        q_target[JOINT_ID] += np.radians(DELTA_DEG)

        print("-" * 50)
        print(f"Petit mouvement sur le joint {JOINT_ID}")
        print(f"Delta : {DELTA_DEG} degrés")
        print("Target en radians :")
        print(q_target)
        print("Target en degrés :")
        print(np.degrees(q_target))
        print("-" * 50)

        input("Appuie sur Entrée pour lancer le petit mouvement, ou Ctrl+C pour annuler...")

        rob.movej(
            q_target.tolist(),
            acc=ACCELERATION,
            vel=VELOCITY,
            wait=True,
        )

        print("Petit mouvement terminé.")
        print("Joints finaux :")
        print(rob.getj())

        retour = input("Revenir à la position initiale ? [y/N] : ").lower().strip()

        if retour == "y":
            print("Retour à la position initiale...")
            rob.movej(
                q_current.tolist(),
                acc=ACCELERATION,
                vel=VELOCITY,
                wait=True,
            )
            print("Retour terminé.")

    except KeyboardInterrupt:
        print("\nAnnulé par utilisateur.")
        if rob is not None:
            try:
                rob.stopj(acc=0.5)
            except Exception:
                pass

    except Exception as e:
        print("Erreur :", e)

    finally:
        if rob is not None:
            try:
                rob.stopj(acc=0.5)
            except Exception:
                pass

            rob.close()
            print("Connexion fermée.")


if __name__ == "__main__":
    main()
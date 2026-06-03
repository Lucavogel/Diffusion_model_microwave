import urx
import time

ROBOT_IP = "192.168.0.60"

def main():
    rob = None

    try:
        rob = urx.Robot(ROBOT_IP)
        print("Connexion URX OK")

        for i in range(10):
            q = rob.getj()
            pose = rob.getl()

            print(f"[{i}] q = {q}")
            print(f"[{i}] tcp = {pose}")
            print("-" * 40)

            time.sleep(0.5)

        print("Lecture stable OK.")

    except Exception as e:
        print("Erreur :", e)

    finally:
        if rob is not None:
            rob.close()
            print("Connexion fermée.")

if __name__ == "__main__":
    main()
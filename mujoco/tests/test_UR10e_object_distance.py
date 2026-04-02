from pathlib import Path
import time
import mujoco
import mujoco.viewer
import numpy as np

MODEL_PATH = Path("/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_custom.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)


home_q = np.array([0.0, -1.2, 1.6, -1.2, -1.57, 0.0], dtype=float)

data.qpos[:6] = home_q
data.ctrl[:6] = home_q


if model.nu > 6:
    data.ctrl[6] = -0.2  
    
# IDs utiles
grasp_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "grasp_site")
object_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "object_cube")
object_joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "object_cube_freejoint")

if grasp_site_id == -1:
    raise ValueError("Site 'grasp_site' introuvable.")
if object_body_id == -1:
    raise ValueError("Body 'object_cube' introuvable.")
if object_joint_id == -1:
    raise ValueError("Joint 'object_cube_freejoint' introuvable.")

# Placement explicite de l'objet
object_qpos_adr = model.jnt_qposadr[object_joint_id]
data.qpos[object_qpos_adr : object_qpos_adr + 3] = np.array([0.70, 0.0, 0.50], dtype=float)
data.qpos[object_qpos_adr + 3 : object_qpos_adr + 7] = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)

mujoco.mj_forward(model, data)

# Orientation cible = orientation initiale du grasp_site
R_target = data.site_xmat[grasp_site_id].reshape(3, 3).copy()

# Cible articulaire courante
q_target = home_q.copy()

# État de la mission
mission_state = "APPROACH"  # APPROACH, GRASP, MOVE_AWAY
grasp_time = 0.0

# ----------------------------
# Fonctions utilitaires
# ----------------------------
def orientation_error(R_target: np.ndarray, R_current: np.ndarray) -> np.ndarray:
    """
    Retourne un vecteur d'erreur d'orientation 3D.
    Petit-angle approximation classique.
    """
    R_err = R_target @ R_current.T
    return 0.5 * np.array([
        R_err[2, 1] - R_err[1, 2],
        R_err[0, 2] - R_err[2, 0],
        R_err[1, 0] - R_err[0, 1],
    ], dtype=float)

# Gains
Kp_pos = 2.0
Kp_rot = 1.5
dt = model.opt.timestep

try:
    with mujoco.viewer.launch_passive(model, data) as viewer:
        last_print = time.time()

        while viewer.is_running():
            # ----------------------------
            # Mesures actuelles
            # ----------------------------
            grasp_pos = data.site_xpos[grasp_site_id].copy()
            R_current = data.site_xmat[grasp_site_id].reshape(3, 3).copy()
            object_pos = data.xpos[object_body_id].copy()

            # ----------------------------
            # Cible cartésienne
            # ----------------------------
            if mission_state == "APPROACH":
                target_pos = object_pos.copy()
                if np.linalg.norm(object_pos - grasp_pos) < 0.015:
                    mission_state = "GRASP"
                    grasp_time = time.time()
                    
            elif mission_state == "GRASP":
                target_pos = object_pos.copy()  # Reste sur place
                if time.time() - grasp_time > 4.0: # Attendre 1s de fermeture 
                    mission_state = "MOVE_AWAY"
                    
            elif mission_state == "MOVE_AWAY":
                # Position en l'air une fois l'objet attrapé
                target_pos = np.array([0.5, 0.4, 0.6], dtype=float)

            # ----------------------------
            # Erreurs
            # ----------------------------
            pos_err = target_pos - grasp_pos
            rot_err = orientation_error(R_target, R_current)

            # Erreur complète 6D
            err = np.hstack([
                Kp_pos * pos_err,
                Kp_rot * rot_err
            ])

            # ----------------------------
            # Jacobiennes du site
            # ----------------------------
            jacp = np.zeros((3, model.nv))
            jacr = np.zeros((3, model.nv))
            mujoco.mj_jacSite(model, data, jacp, jacr, grasp_site_id)

            # On ne garde que les 6 joints du bras
            J = np.vstack([jacp[:, :6], jacr[:, :6]])

            # ----------------------------
            # IK locale / resolved-rate
            # ----------------------------
            dq = np.linalg.pinv(J) @ err

            # Limiter un peu la vitesse articulaire pour éviter les gros sauts
            dq = np.clip(dq, -0.5, 0.5)

            # Intégration
            q_target = q_target + dq * dt

            # Commande du bras
            data.ctrl[:6] = q_target

            if model.nu > 6:
                if mission_state in ["GRASP", "MOVE_AWAY"]:
                    data.ctrl[6] = 0.80  # Pince fermée
                else:
                    data.ctrl[6] = -0.2 # Pince ouverte

            mujoco.mj_step(model, data)
            


            # ----------------------------
            # Logs
            # ----------------------------
            if time.time() - last_print > 0.5:
                print(f"grasp_pos : {grasp_pos}")
                print(f"target_pos: {target_pos}")
                print(f"pos_err   : {pos_err}")
                print(f"rot_err   : {rot_err}")
                print(f"||pos_err|| = {np.linalg.norm(pos_err):.4f}")
                print("-" * 60)
                last_print = time.time()

            viewer.sync()
            time.sleep(dt)

except KeyboardInterrupt:
    print("Arrêt demandé.")
finally:
    print("Fin du script.")
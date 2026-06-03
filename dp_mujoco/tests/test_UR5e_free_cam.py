from pathlib import Path
import time
import mujoco
import mujoco.viewer
import numpy as np

MODEL_PATH = Path("/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_microwave.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

# robot: définir la pose "home" et l'appliquer dès le départ
HOME_QPOS = np.array([0.0, -1.4, 2.3, -0.82, 1.57, 0.0], dtype=float)
data.qpos[:6] = HOME_QPOS.copy()
data.qvel[:6] = 0.0

# Trouver l'adresse dynamique du cube libre au lieu de coder "12" en dur
cube_joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "object_cube_freejoint")
if cube_joint_id != -1:
    qpos_adr = model.jnt_qposadr[cube_joint_id]
    
    # cube libre
    data.qpos[qpos_adr : qpos_adr+3] = np.array([0.70, 0.0, 0.50], dtype=float)
    data.qpos[qpos_adr+3 : qpos_adr+7] = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)

mujoco.mj_forward(model, data)

try:
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
                mujoco.mj_step(model, data)

                # forcer la pose 'home' et annuler les vitesses pour la maintenir
                data.qpos[:6] = HOME_QPOS.copy()
                data.qvel[:6] = 0.0
                mujoco.mj_forward(model, data)

                viewer.sync()
                time.sleep(model.opt.timestep)
except KeyboardInterrupt:
    print("Arrêt demandé.")
finally:
    print("Fin du script.")
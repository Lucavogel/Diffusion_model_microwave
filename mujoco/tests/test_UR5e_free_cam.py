from pathlib import Path
import time
import mujoco
import mujoco.viewer
import numpy as np

MODEL_PATH = Path("/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_custom.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

# robot
data.qpos[:6] = np.array([0.0, -1.2, 1.6, -1.2, -1.57, 0.0], dtype=float)

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
            viewer.sync()
            time.sleep(model.opt.timestep)
except KeyboardInterrupt:
    print("Arrêt demandé.")
finally:
    print("Fin du script.")
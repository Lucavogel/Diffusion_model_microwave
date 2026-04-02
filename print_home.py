import mujoco
import numpy as np
from pathlib import Path

MODEL_PATH = Path("/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_custom.xml")
model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

home_q = np.array([0.0, -1.2, 1.6, -1.2, -1.57, 0.0])
data.qpos[:6] = home_q
mujoco.mj_forward(model, data)
grasp_site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "grasp_site")

pos = data.site_xpos[grasp_site_id]
mat = data.site_xmat[grasp_site_id].reshape(3, 3)

print("POS:", pos.tolist())
print("ROT:")
for row in mat:
    print(f"  [{row[0]:.4f}, {row[1]:.4f}, {row[2]:.4f}],")


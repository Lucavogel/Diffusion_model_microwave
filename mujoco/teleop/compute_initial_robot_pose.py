#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import mujoco

MODEL_PATH = "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_microwave.xml"

home_q = np.array([0.0, -1.05, 1.50, -0.22, 1.6, 0.0], dtype=float)
site_name = "grasp_site"

model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

# mettre le robot en position home
data.qpos[:6] = home_q
data.ctrl[:6] = home_q

# ouvrir la pince si elle existe
if model.nu > 6:
    data.ctrl[6] = -0.2

mujoco.mj_forward(model, data)

site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
if site_id == -1:
    raise ValueError(f"Site '{site_name}' introuvable")

pos = data.site_xpos[site_id].copy()
rot = data.site_xmat[site_id].reshape(3, 3).copy()

print("self.initial_robot_pos = np.array([%.6f, %.6f, %.6f], dtype=float)" %
      (pos[0], pos[1], pos[2]))

print("\nself.initial_robot_rot = np.array([")
for row in rot:
    print("    [ %.6f, %.6f, %.6f]," % (row[0], row[1], row[2]))
print("], dtype=float)")
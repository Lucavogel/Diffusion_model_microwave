from pathlib import Path
import cv2
import mujoco
import numpy as np

MODEL_PATH = Path("/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_custom.xml")

WIDTH = 640
HEIGHT = 480

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

# robot
data.qpos[:6] = np.array([0.0, -1.2, 1.6, -1.2, -1.57, 0.0], dtype=float)

# cube libre
data.qpos[12:15] = np.array([0.65, 0.0, 0.50], dtype=float)
data.qpos[15:19] = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)

mujoco.mj_forward(model, data)

renderer_front = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)
renderer_top = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)

print("ESC pour quitter")

while True:
    mujoco.mj_step(model, data)

    renderer_front.update_scene(data, camera="wrist_cam")
    img_front = renderer_front.render()

    renderer_top.update_scene(data, camera="top_table")
    img_top = renderer_top.render()

    # adapte selon ton orientation actuelle
    img_front = cv2.rotate(img_front, cv2.ROTATE_180)
    img_top = cv2.rotate(img_top, cv2.ROTATE_180)

    img_front = cv2.cvtColor(img_front, cv2.COLOR_RGB2BGR)
    img_top = cv2.cvtColor(img_top, cv2.COLOR_RGB2BGR)

    cv2.putText(img_front, "wrist_cam", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2, cv2.LINE_AA)
    cv2.putText(img_top, "top_table", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2, cv2.LINE_AA)

    cv2.imshow("Camera Front", img_front)
    cv2.imshow("Camera Top", img_top)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

cv2.destroyAllWindows()
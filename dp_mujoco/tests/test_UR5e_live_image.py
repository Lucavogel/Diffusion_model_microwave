from pathlib import Path
import cv2
import mujoco
import numpy as np

MODEL_PATH = Path("/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/mujoco/models/universal_robots_ur10e/scene_custom.xml")

WIDTH = 640
HEIGHT = 480

# load model and data
model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

# target 'home' joint pose (6 first dofs) and interpolation settings
HOME_QPOS = np.array([0.0, -1.2, 1.8, -0.6, 1.57, 0.0], dtype=float)
MOVE_STEPS = 200  # frames to interpolate to home
step = 0

# cube libre
data.qpos[12:15] = np.array([0.65, 0.0, 0.50], dtype=float)
data.qpos[15:19] = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)

mujoco.mj_forward(model, data)

# record starting joint positions to interpolate from
start_qpos = data.qpos[:6].copy()

renderer_front = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)
renderer_top = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)

print("ESC pour quitter")

while True:
    # interpolate qpos towards HOME_QPOS over MOVE_STEPS frames, then hold
    if step < MOVE_STEPS:
        alpha = float(step + 1) / MOVE_STEPS
        data.qpos[:6] = (1.0 - alpha) * start_qpos + alpha * HOME_QPOS
        mujoco.mj_forward(model, data)
        step += 1
    else:
        # keep the robot at home by forcing qpos each frame
        data.qpos[:6] = HOME_QPOS
        mujoco.mj_forward(model, data)

    mujoco.mj_step(model, data)

    renderer_front.update_scene(data, camera="wrist_cam")
    img_front = renderer_front.render()

    renderer_top.update_scene(data, camera="top_table")
    img_top = renderer_top.render()

    # adapte selon ton orientation actuelle
    img_front = cv2.rotate(img_front, cv2.ROTATE_180)
    img_top = cv2.rotate(img_top, cv2.ROTATE_90_COUNTERCLOCKWISE)

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
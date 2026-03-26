from pathlib import Path
import cv2
import mujoco
import numpy as np

MODEL_PATH = Path("mujoco/models/arm2dof.xml")

WIDTH = 640
HEIGHT = 480

CTRL_STEP = 0.08
DECAY = 0.85

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

initial_qpos = np.array([0.6, -0.8], dtype=float)
data.qpos[:2] = initial_qpos
mujoco.mj_forward(model, data)

renderer_front = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)
renderer_wrist = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)

ctrl = np.zeros(model.nu, dtype=float)

print("Contrôles :")
print("  q / a : joint1 +/-")
print("  w / s : joint2 +/-")
print("  espace: stop")
print("  r     : reset")
print("  esc   : quitter")

while True:
    data.ctrl[:] = ctrl
    mujoco.mj_step(model, data)

    renderer_front.update_scene(data, camera="front")
    img_front = renderer_front.render()

    # essaie sans flip vertical pour la front
    img_front = cv2.cvtColor(img_front, cv2.COLOR_RGB2BGR)

    renderer_wrist.update_scene(data, camera="wrist_cam")
    img_wrist = renderer_wrist.render()
    img_wrist = np.flipud(img_wrist)
    img_wrist = cv2.cvtColor(img_wrist, cv2.COLOR_RGB2BGR)

    j1 = float(data.qpos[0])
    j2 = float(data.qpos[1])
    c1 = float(ctrl[0])
    c2 = float(ctrl[1])

    cv2.putText(img_front, f"FRONT | joint1: {j1:.2f} | ctrl1: {c1:.2f}", (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2, cv2.LINE_AA)
    cv2.putText(img_front, f"joint2: {j2:.2f} | ctrl2: {c2:.2f}", (15, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2, cv2.LINE_AA)

    cv2.putText(img_wrist, "WRIST CAM", (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2, cv2.LINE_AA)

    cv2.imshow("MuJoCo Teleop - Front", img_front)
    cv2.imshow("MuJoCo Teleop - Wrist", img_wrist)

    key = cv2.waitKey(1) & 0xFF

    if key == 27:
        break
    elif key == ord('q'):
        ctrl[0] = min(1.0, ctrl[0] + CTRL_STEP)
    elif key == ord('a'):
        ctrl[0] = max(-1.0, ctrl[0] - CTRL_STEP)
    elif key == ord('w'):
        ctrl[1] = min(1.0, ctrl[1] + CTRL_STEP)
    elif key == ord('s'):
        ctrl[1] = max(-1.0, ctrl[1] - CTRL_STEP)
    elif key == ord(' '):
        ctrl[:] = 0.0
    elif key == ord('r'):
        data.qpos[:2] = initial_qpos
        data.qvel[:] = 0.0
        ctrl[:] = 0.0
        mujoco.mj_forward(model, data)

    ctrl *= DECAY

cv2.destroyAllWindows()
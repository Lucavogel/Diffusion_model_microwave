# First import the library
import pyrealsense2 as rs
import numpy as np
import cv2
import json
import time


CONFIG_PATH = "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/scripts/realsense/config/d435i_config.json"

def get_first_realsense_device():
    ctx = rs.context()
    devices = ctx.query_devices()

    if len(devices) == 0:
        raise RuntimeError("Aucune caméra RealSense détectée.")

    dev = devices[0]
    print("Caméra détectée :", dev.get_info(rs.camera_info.name))
    print("Serial :", dev.get_info(rs.camera_info.serial_number))
    return dev


def load_advanced_json_config(json_path):
    dev = get_first_realsense_device()

    # Mode avancé pour les caméras D400 / D435 / D435i
    adv = rs.rs400_advanced_mode(dev)

    if not adv.is_enabled():
        print("Advanced mode désactivé. Activation...")
        adv.toggle_advanced_mode(True)

        # La caméra peut redémarrer après activation
        time.sleep(5)

        dev = get_first_realsense_device()
        adv = rs.rs400_advanced_mode(dev)

    with open(json_path, "r") as f:
        json_text = f.read()

    # Vérifie que le JSON est valide
    json.loads(json_text)

    adv.load_json(json_text)
    print("Config JSON chargée avec succès.")


# 1) Charger la config avant de lancer le pipeline
load_advanced_json_config(CONFIG_PATH)


pipeline = rs.pipeline()
config = rs.config()


config.enable_stream(rs.stream.color, 320, 240, rs.format.bgr8, 30)


# Start streaming with the default recommended configuration
pipeline.start(config)

try:
    while True:
        # Create a pipeline object. This object configures the streaming camera and owns it's handle
        frames = pipeline.wait_for_frames()

        color = frames.get_color_frame()
        

        if not color :
            continue
        #asany keeps the same classes
        color_image = np.asanyarray(color.get_data())
        
        display_color = cv2.resize(color_image, (640, 480), interpolation=cv2.INTER_NEAREST)


        cv2.imshow("RealSense RGB 320x240 agrandie", display_color)

        

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


finally:
    pipeline.stop()
    cv2.destroyAllWindows()
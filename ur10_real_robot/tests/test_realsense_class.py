from ur10_real_robot.camera import RealSenseCamera

import cv2


CONFIG_PATH = "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/camera/config/d435i_config.json"
SERIAL_NUMBER_TOP_DOWN = "332322072359"
SERIAL_NUMBER_FRONT = "043422251624"


def main() -> None:

    top_down_camera = RealSenseCamera(
        config_path=CONFIG_PATH,
        width=640,
        height=480,
        fps=30,
        output_size=(320, 240),
        display_size=(640, 480),
        serial_number=SERIAL_NUMBER_FRONT,
        apply_advanced_config=True,
    )

    top_down_camera.start()

    try:
        while True:
            frame = top_down_camera.read()

            display_bgr = frame["display_bgr"]
            rgb_84 = frame["rgb_resized"]

            # Convert RGB 84x84 back to BGR for OpenCV display
            bgr_84 = cv2.cvtColor(rgb_84, cv2.COLOR_RGB2BGR)

            # Enlarge the 84x84 image so you can see the pixels
            pixelized_preview = cv2.resize(
                bgr_84,
                (640, 640),
                interpolation=cv2.INTER_NEAREST,
            )
            

            cv2.imshow("Normal Eye-in-Hand camera", display_bgr)
            cv2.imshow("Pixelized dataset view 360 x 240", pixelized_preview)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        top_down_camera.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
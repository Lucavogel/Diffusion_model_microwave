import zarr
import cv2
import argparse
import sys
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Replay a diffusion policy zarr dataset")
    parser.add_argument("zarr_path", type=str, help="Path to the .zarr folder")
    parser.add_argument("--fps", type=int, default=10, help="Playback speed in frames per second")
    parser.add_argument("--scale", type=float, default=3.0, help="Scale factor for viewing")
    parser.add_argument(
        "--max-width",
        type=int,
        default=None,
        help="Optional maximum displayed image width in pixels, preserving aspect ratio.",
    )
    args = parser.parse_args()

    try:
        root = zarr.open(args.zarr_path, mode="r")
    except Exception as e:
        print(f"Failed to open zarr dataset at {args.zarr_path}: {e}")
        return
    
    if 'data/agentview_image' not in root or 'data/robot0_eye_in_hand_image' not in root:
        print("Error: Could not find image data arrays in zarr structure.")
        return

    agentview = root['data/agentview_image']
    wristview = root['data/robot0_eye_in_hand_image']
    
    if 'meta/episode_ends' not in root:
        print("Error: episode_ends not found in meta.")
        return
    episode_ends = root['meta/episode_ends'][:]
    
    print(f"Dataset summary:")
    print(f"  - Path: {args.zarr_path}")
    print(f"  - Total episodes: {len(episode_ends)}")
    print(f"  - Image shape: {agentview.shape} (dtype: {agentview.dtype})")
    print(f"\nControls:")
    print(f"  [Q] or [ESC] : Quit script")
    print(f"  [S]          : Skip to next episode")
    print(f"  [P]          : Pause / Resume")
    print(f"  [N] / [Right]: Next frame when paused")
    print(f"  [B] / [Left] : Previous frame when paused")
    print("--------------------------------------------------")
    
    start_idx = 0
    paused = False
    
    for i, end_idx in enumerate(episode_ends):
        print(f"Replaying episode {i+1}/{len(episode_ends)} ({end_idx - start_idx} frames)")
        
        t = start_idx
        while t < end_idx:
            if not paused:
                img_ag = agentview[t]
                img_wr = wristview[t]
                
                # MuJoCo renderer outputs RGB. OpenCV expects BGR for viewing.
                img_ag_bgr = cv2.cvtColor(img_ag, cv2.COLOR_RGB2BGR)
                img_wr_bgr = cv2.cvtColor(img_wr, cv2.COLOR_RGB2BGR)
                
                # Combine side by side
                comb = np.hstack((img_ag_bgr, img_wr_bgr))
                
                # Scale for viewing only. The dataset itself is not modified.
                if args.scale != 1.0:
                    interpolation = cv2.INTER_AREA if args.scale < 1.0 else cv2.INTER_NEAREST
                    comb = cv2.resize(
                        comb,
                        (0, 0),
                        fx=args.scale,
                        fy=args.scale,
                        interpolation=interpolation,
                    )
                if args.max_width is not None and comb.shape[1] > args.max_width:
                    resize_scale = args.max_width / float(comb.shape[1])
                    comb = cv2.resize(
                        comb,
                        (args.max_width, int(round(comb.shape[0] * resize_scale))),
                        interpolation=cv2.INTER_AREA,
                    )
                
                # Add text
                cv2.putText(comb, f"Ep: {i+1} | Frame: {t-start_idx+1}/{end_idx - start_idx}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(comb, "Left: Agent View | Right: Wrist View", (10, comb.shape[0] - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
                
                cv2.imshow("Dataset Replay", comb)
                t += 1
            else:
                img_ag = agentview[t]
                img_wr = wristview[t]

                # MuJoCo renderer outputs RGB. OpenCV expects BGR for viewing.
                img_ag_bgr = cv2.cvtColor(img_ag, cv2.COLOR_RGB2BGR)
                img_wr_bgr = cv2.cvtColor(img_wr, cv2.COLOR_RGB2BGR)

                # Combine side by side
                comb = np.hstack((img_ag_bgr, img_wr_bgr))

                # Scale for viewing only. The dataset itself is not modified.
                if args.scale != 1.0:
                    interpolation = cv2.INTER_AREA if args.scale < 1.0 else cv2.INTER_NEAREST
                    comb = cv2.resize(
                        comb,
                        (0, 0),
                        fx=args.scale,
                        fy=args.scale,
                        interpolation=interpolation,
                    )
                if args.max_width is not None and comb.shape[1] > args.max_width:
                    resize_scale = args.max_width / float(comb.shape[1])
                    comb = cv2.resize(
                        comb,
                        (args.max_width, int(round(comb.shape[0] * resize_scale))),
                        interpolation=cv2.INTER_AREA,
                    )

                # Add text
                cv2.putText(comb, f"PAUSED | Ep: {i+1} | Frame: {t-start_idx+1}/{end_idx - start_idx}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(comb, "Left: Agent View | Right: Wrist View", (10, comb.shape[0] - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

                cv2.imshow("Dataset Replay", comb)

            delay = 0 if paused else max(1, 1000 // args.fps)
            key_raw = cv2.waitKeyEx(delay)
            key = key_raw & 0xFF
            
            if key == 27 or key == ord('q'):
                print("Exit requested.")
                cv2.destroyAllWindows()
                return
            elif key == ord('s'):
                print("Skipping to next episode...")
                break
            elif key == ord('p'):
                paused = not paused
                print("Paused" if paused else "Resumed")
            elif paused and (key == ord('n') or key_raw == 65363 or key_raw == 2555904):
                t = min(t + 1, end_idx - 1)
            elif paused and (key == ord('b') or key_raw == 65361 or key_raw == 2424832):
                t = max(t - 1, start_idx)
                
        start_idx = end_idx
        

    cv2.destroyAllWindows()
    print("Replay finished.")

if __name__ == "__main__":
    main()

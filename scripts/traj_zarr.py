import zarr
import argparse
import numpy as np
import matplotlib.pyplot as plt


def print_zarr_tree(g, prefix=''):
    try:
        for k in sorted(g.keys()):
            item = g[k]
            path = f"{prefix}{k}"
            try:
                shape = getattr(item, 'shape', None)
            except Exception:
                shape = None
            if hasattr(item, 'keys'):
                print(f"{path}/ (group)")
                print_zarr_tree(item, prefix=path + '/')
            else:
                print(f"{path} (array) shape={shape}")
    except Exception as e:
        print("Failed to list zarr tree:", e)


def main():
    parser = argparse.ArgumentParser(description="Replay a diffusion policy zarr dataset (XYZ trajectory only)")
    parser.add_argument("zarr_path", type=str, help="Path to the .zarr folder")
    parser.add_argument("--pos-key", type=str, default='data/robot0_eef_pos', help="Zarr key for end-effector positions")
    parser.add_argument("--fps", type=int, default=10, help="Playback speed in frames per second")
    args = parser.parse_args()

    try:
        root = zarr.open(args.zarr_path, mode="r")
    except Exception as e:
        print(f"Failed to open zarr dataset at {args.zarr_path}: {e}")
        return

    pos_key = args.pos_key

    if pos_key not in root:
        print(f"Error: could not find expected positions array '{pos_key}' in zarr.")
        print("Partial zarr tree:")
        print_zarr_tree(root)
        print("Re-run with --pos-key to specify the correct key.")
        return

    agentview = root[pos_key]

    # episode ends may be located under meta/episode_ends or other key
    episode_ends = None
    if 'meta' in root and 'episode_ends' in root['meta']:
        episode_ends = root['meta']['episode_ends'][:]
    else:
        # try top-level candidates
        candidates = [k for k in root.keys() if 'episode' in k.lower() or 'ends' in k.lower()]
        if candidates:
            print('Warning: using candidate episode_ends key:', candidates[0])
            episode_ends = root[candidates[0]][:]
        else:
            # try meta group keys if present
            if 'meta' in root:
                print('Warning: meta group keys:', list(root['meta'].keys()))
            print("Error: episode_ends not found. Provide episode boundaries or add meta/episode_ends in the zarr.")
            return

    episode_ends = np.asarray(episode_ends, dtype=int)

    print(f"Dataset summary:")
    print(f"  - Path: {args.zarr_path}")
    print(f"  - Total episodes: {len(episode_ends)}")

    plt.ion()
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('End Effector Trajectory (XYZ)')

    start_idx = 0
    for i, end_idx in enumerate(episode_ends):
        start = int(start_idx)
        end = int(end_idx)
        end = min(end, len(agentview))
        start = max(0, min(start, end))
        pos_seq = np.asarray(agentview[start:end])
        if pos_seq.size == 0:
            start_idx = end_idx
            continue

        # compute axis limits with margin
        mins = pos_seq.min(axis=0)
        maxs = pos_seq.max(axis=0)
        margin = (maxs - mins) * 0.1
        margin[margin == 0] = 0.1

        ax.clear()
        ax.set_xlim(mins[0] - margin[0], maxs[0] + margin[0])
        ax.set_ylim(mins[1] - margin[1], maxs[1] + margin[1])
        ax.set_zlim(mins[2] - margin[2], maxs[2] + margin[2])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')

        line, = ax.plot([], [], [], '-', color='gray', linewidth=1)
        point, = ax.plot([], [], [], 'o', color='red')

        for k in range(1, len(pos_seq) + 1):
            xs = pos_seq[:k, 0]
            ys = pos_seq[:k, 1]
            zs = pos_seq[:k, 2]
            line.set_data(xs, ys)
            line.set_3d_properties(zs)
            point.set_data(xs[-1:], ys[-1:])
            point.set_3d_properties(zs[-1:])
            plt.pause(1.0 / args.fps)

        start_idx = end_idx

    plt.ioff()
    print('Done')


if __name__ == '__main__':
    main()

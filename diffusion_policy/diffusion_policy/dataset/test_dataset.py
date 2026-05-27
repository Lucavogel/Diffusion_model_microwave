from pathlib import Path
from diffusion_policy.dataset.generic_image_dataset import GenericImageDataset

shape_meta = {
    "obs": {
        "agentview_image": {"shape": [3, 84, 84], "type": "rgb"},
        "robot0_eye_in_hand_image": {"shape": [3, 84, 84], "type": "rgb"},
        "robot0_eef_pos": {"shape": [3], "type": "low_dim"},
        "robot0_eef_quat": {"shape": [4], "type": "low_dim"},
        "robot0_gripper_qpos": {"shape": [1], "type": "low_dim"},
    },
    "action": {"shape": [8]}
}

dataset_path = "/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/data/datasets/demo_data_20260422_151211.zarr"

dataset = GenericImageDataset(
    shape_meta=shape_meta,
    dataset_path=dataset_path,
    horizon=16,
    n_obs_steps=2,
    pad_before=0,
    pad_after=0,
    val_ratio=0.1,
)

print("len(dataset) =", len(dataset))

sample = dataset[0]

print("agentview_image:", sample["obs"]["agentview_image"].shape)
print("robot0_eye_in_hand_image:", sample["obs"]["robot0_eye_in_hand_image"].shape)
print("robot0_eef_pos:", sample["obs"]["robot0_eef_pos"].shape)
print("robot0_eef_quat:", sample["obs"]["robot0_eef_quat"].shape)
print("robot0_gripper_qpos:", sample["obs"]["robot0_gripper_qpos"].shape)
print("action:", sample["action"].shape)

print("dtype image:", sample["obs"]["agentview_image"].dtype)
print("dtype action:", sample["action"].dtype)

print("image min/max:",
      sample["obs"]["agentview_image"].min().item(),
      sample["obs"]["agentview_image"].max().item())
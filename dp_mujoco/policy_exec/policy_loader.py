from pathlib import Path

import dill
import hydra
import torch


ROOT_DIR = Path(__file__).resolve().parents[2]


def load_policy(checkpoint_path: str, device: torch.device, root_dir: Path = ROOT_DIR):
    ckpt_path = Path(checkpoint_path)
    if not ckpt_path.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

    # Large training checkpoints can be several GB because they include optimizer
    # states. mmap reduces peak RAM usage when supported by torch.
    try:
        payload = torch.load(str(ckpt_path), map_location='cpu', pickle_module=dill, mmap=True)
    except TypeError:
        payload = torch.load(str(ckpt_path), map_location='cpu', pickle_module=dill)

    if "state_dicts" in payload and isinstance(payload["state_dicts"], dict):
        payload["state_dicts"].pop("optimizer", None)

    cfg = payload["cfg"]

    cls = hydra.utils.get_class(cfg._target_)
    workspace = cls(cfg, output_dir=str(ROOT_DIR / "dp_mujoco" / "mujoco" / "outputs"))
    workspace.load_payload(payload, exclude_keys=("optimizer",), include_keys=None)

    policy = workspace.model
    if cfg.training.use_ema:
        policy = workspace.ema_model

    policy.to(device)
    policy.eval()
    return policy, cfg


def infer_image_shape(cfg):
    """Return the image shape as (C, H, W)."""
    if hasattr(cfg, "task") and hasattr(cfg.task, "image_shape"):
        shape = tuple(cfg.task.image_shape)
        if len(shape) != 3:
            raise ValueError(f"Expected image_shape [C,H,W], got {shape}")
        return int(shape[0]), int(shape[1]), int(shape[2])

    if hasattr(cfg, "shape_meta") and hasattr(cfg.shape_meta, "obs"):
        obs = cfg.shape_meta.obs
        if hasattr(obs, "agentview_image") and hasattr(obs.agentview_image, "shape"):
            shape = tuple(obs.agentview_image.shape)
            if len(shape) == 3:
                return int(shape[0]), int(shape[1]), int(shape[2])

    raise ValueError("Unable to infer image shape from config.")
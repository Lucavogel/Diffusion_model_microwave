#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dp_mujoco.policy_exec.policy_loader import load_policy


def _to_plain(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value


def _shape_tuple(shape: Any) -> tuple[int, ...]:
    return tuple(int(_to_plain(x)) for x in shape)


def count_params(module: torch.nn.Module | None) -> int:
    if module is None:
        return 0
    return int(sum(p.numel() for p in module.parameters()))


def infer_architecture(policy: torch.nn.Module) -> str:
    policy_name = policy.__class__.__name__
    model = getattr(policy, "model", None)
    model_name = model.__class__.__name__ if model is not None else ""
    if model_name:
        return f"{policy_name} / {model_name}"
    return policy_name


def build_fake_obs(
    policy: torch.nn.Module,
    cfg: Any,
    batch_size: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    n_obs_steps = int(getattr(policy, "n_obs_steps", cfg.n_obs_steps))
    obs = {}
    for key, attr in cfg.shape_meta.obs.items():
        shape = _shape_tuple(attr.shape)
        obs_type = str(attr.get("type", "low_dim"))
        if obs_type == "rgb":
            tensor = torch.rand((batch_size, n_obs_steps, *shape), dtype=torch.float32, device=device)
        else:
            tensor = torch.zeros((batch_size, n_obs_steps, *shape), dtype=torch.float32, device=device)
        obs[key] = tensor
    return obs


def sync_if_needed(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def benchmark_checkpoint(
    checkpoint: Path,
    device: torch.device,
    repeats: int,
    warmup: int,
    batch_size: int,
    num_inference_steps: int | None,
) -> dict[str, Any]:
    policy, cfg = load_policy(str(checkpoint), device)
    if num_inference_steps is not None and hasattr(policy, "num_inference_steps"):
        policy.num_inference_steps = int(num_inference_steps)

    obs = build_fake_obs(policy, cfg, batch_size=batch_size, device=device)
    policy.eval()

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    times_ms = []
    with torch.inference_mode():
        for _ in range(warmup):
            _ = policy.predict_action(obs)
        sync_if_needed(device)

        for _ in range(repeats):
            sync_if_needed(device)
            t0 = time.perf_counter()
            _ = policy.predict_action(obs)
            sync_if_needed(device)
            times_ms.append((time.perf_counter() - t0) * 1000.0)

    obs_encoder = getattr(policy, "obs_encoder", None)
    diffusion_model = getattr(policy, "model", None)
    image_shapes = []
    lowdim_shapes = []
    for key, attr in cfg.shape_meta.obs.items():
        shape = _shape_tuple(attr.shape)
        if str(attr.get("type", "low_dim")) == "rgb":
            image_shapes.append(f"{key}:{shape}")
        else:
            lowdim_shapes.append(f"{key}:{shape}")

    peak_mem_mb = ""
    if device.type == "cuda":
        peak_mem_mb = f"{torch.cuda.max_memory_allocated(device) / (1024 ** 2):.1f}"

    return {
        "checkpoint": str(checkpoint),
        "checkpoint_size_gb": f"{checkpoint.stat().st_size / (1024 ** 3):.2f}",
        "architecture": infer_architecture(policy),
        "device": str(device),
        "batch_size": batch_size,
        "num_inference_steps": int(getattr(policy, "num_inference_steps", -1)),
        "obs_horizon_To": int(getattr(policy, "n_obs_steps", -1)),
        "prediction_horizon_Tp": int(getattr(policy, "horizon", -1)),
        "action_horizon_Ta": int(getattr(policy, "n_action_steps", -1)),
        "action_dim": int(getattr(policy, "action_dim", -1)),
        "image_shapes": "; ".join(image_shapes),
        "lowdim_shapes": "; ".join(lowdim_shapes),
        "total_params_m": f"{count_params(policy) / 1e6:.2f}",
        "diffusion_params_m": f"{count_params(diffusion_model) / 1e6:.2f}",
        "vision_params_m": f"{count_params(obs_encoder) / 1e6:.2f}",
        "mean_inference_ms": f"{statistics.mean(times_ms):.2f}",
        "std_inference_ms": f"{statistics.pstdev(times_ms):.2f}",
        "p95_inference_ms": f"{float(np.percentile(times_ms, 95)):.2f}",
        "min_inference_ms": f"{min(times_ms):.2f}",
        "max_inference_ms": f"{max(times_ms):.2f}",
        "cuda_peak_mem_mb": peak_mem_mb,
    }


def parse_steps_overrides(values: list[str]) -> dict[str, int]:
    overrides: dict[str, int] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(
                "Expected --checkpoint-inference-steps as CHECKPOINT=STEPS, "
                f"got: {value}"
            )
        checkpoint, steps = value.rsplit("=", 1)
        overrides[str(Path(checkpoint))] = int(steps)
    return overrides


def get_steps_for_checkpoint(
    checkpoint: Path,
    global_steps: int | None,
    per_checkpoint_steps: dict[str, int],
) -> int | None:
    keys = {
        str(checkpoint),
        str(checkpoint.resolve()),
        checkpoint.name,
    }
    for key in keys:
        if key in per_checkpoint_steps:
            return per_checkpoint_steps[key]
    return global_steps


def print_table(rows: list[dict[str, Any]]) -> None:
    columns = [
        "checkpoint",
        "architecture",
        "num_inference_steps",
        "total_params_m",
        "diffusion_params_m",
        "vision_params_m",
        "mean_inference_ms",
        "std_inference_ms",
        "p95_inference_ms",
        "cuda_peak_mem_mb",
    ]
    widths = {col: max(len(col), *(len(str(row.get(col, ""))) for row in rows)) for col in columns}
    print(" | ".join(col.ljust(widths[col]) for col in columns))
    print("-+-".join("-" * widths[col] for col in columns))
    for row in rows:
        print(" | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Diffusion Policy checkpoint inference without robot or cameras.",
    )
    parser.add_argument("checkpoints", nargs="+", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--num-inference-steps", type=int, default=None)
    parser.add_argument(
        "--checkpoint-inference-steps",
        action="append",
        default=[],
        metavar="CHECKPOINT=STEPS",
        help=(
            "Override denoising steps for one checkpoint only. The checkpoint "
            "can be a full path or just the filename. Useful when U-Net uses "
            "DDIM with fewer steps while Transformer keeps its trained default."
        ),
    )
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--torch-num-threads", type=int, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    args = parser.parse_args()

    if args.torch_num_threads is not None:
        torch.set_num_threads(int(args.torch_num_threads))

    device = torch.device(args.device)
    per_checkpoint_steps = parse_steps_overrides(args.checkpoint_inference_steps)
    rows = [
        benchmark_checkpoint(
            checkpoint=checkpoint,
            device=device,
            repeats=args.repeats,
            warmup=args.warmup,
            batch_size=args.batch_size,
            num_inference_steps=get_steps_for_checkpoint(
                checkpoint,
                args.num_inference_steps,
                per_checkpoint_steps,
            ),
        )
        for checkpoint in args.checkpoints
    ]
    print_table(rows)

    if args.output_csv is not None:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.output_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nSaved CSV: {args.output_csv}")


if __name__ == "__main__":
    main()

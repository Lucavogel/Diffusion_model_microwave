#!/usr/bin/env python3
"""Minimal MuJoCo model/data/control example used by the internal tutorial."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import time

import mujoco


SCENE_PATH = Path(__file__).with_name("minimal_scene.xml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument(
        "--viewer",
        action="store_true",
        help="Show the interactive viewer and synchronize close to real time.",
    )
    return parser


def step_model(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    actuator_id: int,
    duration: float,
    viewer=None,
) -> None:
    next_print_time = 0.0

    while data.time < duration and (viewer is None or viewer.is_running()):
        data.ctrl[actuator_id] = 0.8 * math.sin(2.0 * math.pi * 0.25 * data.time)
        mujoco.mj_step(model, data)

        if data.time >= next_print_time:
            print(
                f"t={data.time:4.1f}s  "
                f"qpos[0]={data.qpos[0]:+.3f}  "
                f"ctrl[0]={data.ctrl[0]:+.3f}"
            )
            next_print_time += 0.5

        if viewer is not None:
            viewer.sync()
            time.sleep(model.opt.timestep)


def main() -> None:
    args = build_parser().parse_args()

    model = mujoco.MjModel.from_xml_path(str(SCENE_PATH))
    data = mujoco.MjData(model)
    actuator_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_ACTUATOR,
        "arm_position",
    )

    print(f"scene: {SCENE_PATH}")
    print(f"timestep: {model.opt.timestep:.4f} s")
    print(f"nq={model.nq}, nv={model.nv}, nu={model.nu}")

    if args.viewer:
        from mujoco import viewer as mj_viewer

        with mj_viewer.launch_passive(model, data) as viewer:
            step_model(model, data, actuator_id, args.duration, viewer)
    else:
        step_model(model, data, actuator_id, args.duration)

    tool_site_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_SITE,
        "tool_site",
    )
    print("final tool position:", data.site_xpos[tool_site_id].round(4))


if __name__ == "__main__":
    main()

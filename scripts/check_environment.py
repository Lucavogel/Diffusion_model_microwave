#!/usr/bin/env python3
"""Check the local project environment without moving or connecting a robot."""

from __future__ import annotations

import importlib
import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass(frozen=True)
class ImportCheck:
    module: str
    label: str
    required: bool = True
    distribution: str | None = None


CORE_IMPORTS = (
    ImportCheck("numpy", "NumPy"),
    ImportCheck("torch", "PyTorch"),
    ImportCheck("torchvision", "TorchVision"),
    ImportCheck("cv2", "OpenCV", distribution="opencv-python"),
    ImportCheck("mujoco", "MuJoCo"),
    ImportCheck("zarr", "Zarr"),
    ImportCheck("hydra", "Hydra", distribution="hydra-core"),
    ImportCheck("diffusers", "Diffusers"),
    ImportCheck("pinocchio", "Pinocchio", distribution="pin"),
    ImportCheck("diffusion_policy", "Local Diffusion Policy package"),
    ImportCheck("dp_mujoco", "MuJoCo project package"),
    ImportCheck("ur10_real_robot", "Real-robot project package"),
)

HARDWARE_IMPORTS = (
    ImportCheck("pyrealsense2", "RealSense Python wrapper", False),
    ImportCheck("pymodbus", "Modbus gripper library", False),
    ImportCheck("urx", "UR robot library", False),
    ImportCheck("rclpy", "ROS 2 Python client", False),
)


def version_for(check: ImportCheck, module: object) -> str:
    module_version = getattr(module, "__version__", None)
    if module_version:
        return str(module_version)

    distribution = check.distribution or check.module
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "version unknown"


def check_import(check: ImportCheck) -> bool:
    try:
        module = importlib.import_module(check.module)
    except Exception as exc:  # An import can fail for reasons other than absence.
        level = "FAIL" if check.required else "WARN"
        print(f"[{level}] {check.label}: {type(exc).__name__}: {exc}")
        return not check.required

    print(f"[OK]   {check.label}: {version_for(check, module)}")
    return True


def check_command(command: str, required: bool = True) -> bool:
    path = shutil.which(command)
    if path:
        print(f"[OK]   command `{command}`: {path}")
        return True

    level = "FAIL" if required else "WARN"
    print(f"[{level}] command `{command}` was not found in PATH")
    return not required


def git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def openhaptics_status() -> None:
    root_value = os.environ.get("OPENHAPTICS_ROOT")
    if not root_value:
        print("[WARN] OPENHAPTICS_ROOT is not set (required only for the Touch)")
        return

    root = Path(root_value).expanduser()
    required_paths = (
        root / "usr/include/HD/hd.h",
        root / "usr/lib/libHD.so",
        root / "usr/lib/libHL.so",
        root / "usr/lib/libHDU.a",
    )
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"[WARN] OpenHaptics root is incomplete: {root}")
        for path in missing:
            print(f"       missing: {path}")
    else:
        print(f"[OK]   OpenHaptics SDK: {root}")


def main() -> int:
    print("=" * 68)
    print("DIFFUSION POLICY LOCAL ENVIRONMENT CHECK")
    print("=" * 68)
    print(f"Repository : {REPO_ROOT}")
    print(f"Git commit : {git_revision()}")
    print(f"OS         : {platform.platform()}")
    print(f"Python     : {platform.python_version()} ({sys.executable})")
    print()

    failures = 0
    if sys.version_info[:2] != (3, 10):
        print("[FAIL] Python 3.10 is required by the reference environment")
        failures += 1
    else:
        print("[OK]   Python major/minor version: 3.10")

    print("\nCore Python packages")
    print("-" * 68)
    for check in CORE_IMPORTS:
        if not check_import(check):
            failures += 1

    print("\nOptional hardware packages")
    print("-" * 68)
    for check in HARDWARE_IMPORTS:
        check_import(check)

    print("\nSystem commands")
    print("-" * 68)
    for command in ("git", "cmake", "ffmpeg"):
        if not check_command(command):
            failures += 1
    check_command("ros2", required=False)
    check_command("realsense-viewer", required=False)
    openhaptics_status()

    print("\nResult")
    print("-" * 68)
    if failures:
        print(f"[FAIL] {failures} required check(s) failed.")
        print("       Follow README_ENV.md before using the project.")
        return 1

    print("[OK]   All required local checks passed.")
    print("       Hardware warnings are acceptable for simulation-only work.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

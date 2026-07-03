from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Any

import numpy as np
from urx.urrtmon import URRTMonitor


ROBOT_IP = "192.168.2.100"
PORT = 30002

ROBOT_FREQ = 125.0
ROBOT_DT = 1.0 / ROBOT_FREQ


def format_joint_list(q) -> str:
    q_arr = np.asarray(q, dtype=float).reshape(-1)

    if q_arr.shape[0] != 6:
        raise ValueError(f"Expected 6 joints, got shape {q_arr.shape}")

    if not np.all(np.isfinite(q_arr)):
        raise ValueError(f"Invalid joint values: {q_arr}")

    return "[" + ", ".join(f"{float(v):.9f}" for v in q_arr) + "]"


@dataclass
class UR10RealtimeSession:
    robot_ip: str = ROBOT_IP
    port: int = PORT
    socket_timeout: float = 2.0

    def __post_init__(self) -> None:
        self.rt: URRTMonitor | None = None
        self.sock: socket.socket | None = None

    def connect(self) -> "UR10RealtimeSession":
        print(f"[INFO] Starting URRTMonitor on {self.robot_ip}...")
        self.rt = URRTMonitor(self.robot_ip)
        self.rt.start()
        self.rt.wait()

        print(f"[INFO] Opening command socket {self.robot_ip}:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.socket_timeout)

        # Important pour éviter le buffering TCP.
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self.sock.connect((self.robot_ip, self.port))

        print("[OK] UR10RealtimeSession connected.")
        return self

    def read(self, wait: bool = True) -> dict[str, Any]:
        if self.rt is None:
            raise RuntimeError("UR10 realtime session is not connected")

        data = self.rt.get_all_data(wait=wait)

        if data is None:
            raise RuntimeError("No realtime data received")

        return data

    def current_q(self) -> np.ndarray:
        data = self.read(wait=True)

        if "qActual" not in data:
            raise KeyError(f"'qActual' not found in realtime data. Keys: {list(data.keys())}")

        q = np.asarray(data["qActual"], dtype=float).reshape(-1)

        if q.shape[0] != 6:
            raise ValueError(f"Expected 6 joints from qActual, got shape {q.shape}")

        return q

    def send(self, command: str) -> None:
        if self.sock is None:
            raise RuntimeError("UR10 realtime session is not connected")

        self.sock.sendall(command.encode("utf-8"))

    def send_servoj(self, q, t: float = 0.008, a: float = 0.0, v: float = 0.0) -> None:
        q_str = format_joint_list(q)

        # Syntaxe simple compatible CB :
        # servoj(q, a, v, t)
        cmd = f"servoj({q_str}, {float(a):.6f}, {float(v):.6f}, {float(t):.6f})\n"
        self.send(cmd)

    def send_movej(self, q, a: float = 0.2, v: float = 0.1) -> None:
        q_str = format_joint_list(q)
        cmd = f"movej({q_str}, {float(a):.6f}, {float(v):.6f})\n"
        self.send(cmd)

    def send_speedj(self, qd, a: float = 0.1, t: float = 0.02) -> None:
        qd_str = format_joint_list(qd)
        cmd = f"speedj({qd_str}, {float(a):.6f}, {float(t):.6f})\n"
        self.send(cmd)

    def stopj(self, deceleration: float = 1.0) -> None:
        self.send(f"stopj({float(deceleration):.6f})\n")

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

        if self.rt is not None:
            try:
                self.rt.stop()
            except Exception:
                pass
            self.rt = None


def format_servoj(q, t: float = 0.008, a: float = 0.0, v: float = 0.0) -> str:
    q_str = format_joint_list(q)
    return f"servoj({q_str}, {float(a):.6f}, {float(v):.6f}, {float(t):.6f})\n"

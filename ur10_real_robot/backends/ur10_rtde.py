from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Any

import numpy as np
from urx.urrtmon import URRTMonitor

ROBOT_IP = "192.168.0.60"
PORT = 30002
ROBOT_FREQ = 125.0
ROBOT_DT = 1.0 / ROBOT_FREQ


@dataclass
class UR10RealtimeSession:
    robot_ip: str = ROBOT_IP
    port: int = PORT
    socket_timeout: float = 2.0

    def __post_init__(self) -> None:
        self.rt: URRTMonitor | None = None
        self.sock: socket.socket | None = None

    def connect(self) -> "UR10RealtimeSession":
        self.rt = URRTMonitor(self.robot_ip)
        self.rt.start()
        self.rt.wait()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.socket_timeout)
        self.sock.connect((self.robot_ip, self.port))
        return self

    def read(self, wait: bool = True) -> dict[str, Any]:
        if self.rt is None:
            raise RuntimeError("UR10 realtime session is not connected")
        return self.rt.get_all_data(wait=wait)

    def current_q(self) -> np.ndarray:
        data = self.read(wait=True)
        return np.asarray(data["qActual"], dtype=float)

    def send(self, command: str) -> None:
        if self.sock is None:
            raise RuntimeError("UR10 realtime session is not connected")
        self.sock.sendall(command.encode("utf-8"))

    def send_servoj(self, q, t: float = 0.08) -> None:
        q_list = list(np.asarray(q, dtype=float))
        self.send(f"servoj({q_list}, 0, 0, {t})\n")

    def send_movej(self, q, a: float = 0.5, v: float = 0.5) -> None:
        q_list = list(np.asarray(q, dtype=float))
        self.send(f"movej({q_list}, {a}, {v})\n")

    def stopj(self, deceleration: float = 2.0) -> None:
        self.send(f"stopj({deceleration})\n")

    def close(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        if self.rt is not None:
            self.rt.stop()
            self.rt = None


def format_servoj(q, t: float = 0.08) -> str:
    q_list = list(np.asarray(q, dtype=float))
    return f"servoj({q_list}, 0, 0, {t})\n"

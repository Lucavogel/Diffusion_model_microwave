from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OnRobotGripperStatus:
    prox_off_l: int
    prox_off_r: int
    g_gwd: int
    g_wdf: int
    busy: int
    grip_det: int
    in_zero: int

    @property
    def width_mm(self) -> float:
        return float(self.g_wdf) / 10.0

    def as_dict(self) -> dict[str, int]:
        return {
            "prox_off_l": self.prox_off_l,
            "prox_off_r": self.prox_off_r,
            "g_gwd": self.g_gwd,
            "g_wdf": self.g_wdf,
            "busy": self.busy,
            "grip_det": self.grip_det,
            "in_zero": self.in_zero,
        }


class OnRobotRG2FTModbus:
    """
    Minimal Modbus/TCP client for the OnRobot RG2FT gripper.

    Units match the ROS driver already present in the workspace:
    - width command/status: 1/10 mm
    - force command: 1/10 N
    - r_ctr: 1 starts grip/move, 0 stops
    """

    DEVICE_ID = 65
    MAX_WIDTH_MM = 100.0
    MAX_FORCE_N = 40.0

    def __init__(self, ip: str, port: int = 502, timeout: float = 1.0) -> None:
        self.ip = str(ip)
        self.port = int(port)
        self.timeout = float(timeout)
        self.client: Any | None = None
        self.device_id_kwarg = "unit"
        self.lock = threading.Lock()

    def connect(self) -> "OnRobotRG2FTModbus":
        try:
            from pymodbus.client import ModbusTcpClient

            self.device_id_kwarg = "device_id"
        except ImportError:
            from pymodbus.client.sync import ModbusTcpClient

            self.device_id_kwarg = "unit"

        self.client = ModbusTcpClient(
            self.ip,
            port=self.port,
            timeout=self.timeout,
        )
        if not self.client.connect():
            raise RuntimeError(f"Failed to connect to gripper at {self.ip}:{self.port}")
        return self

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def _device_kwargs(self) -> dict[str, int]:
        return {self.device_id_kwarg: self.DEVICE_ID}

    def _check_connected(self) -> None:
        if self.client is None:
            raise RuntimeError("OnRobot gripper is not connected.")

    @staticmethod
    def _check_response(response, label: str):
        if response is None:
            raise RuntimeError(f"{label}: no Modbus response")
        if hasattr(response, "isError") and response.isError():
            raise RuntimeError(f"{label}: Modbus error response {response}")
        if not hasattr(response, "registers") and "read" in label:
            raise RuntimeError(f"{label}: response has no registers: {response}")
        return response

    def _read_holding_registers(self, address: int, count: int) -> list[int]:
        self._check_connected()
        response = self.client.read_holding_registers(
            address=int(address),
            count=int(count),
            **self._device_kwargs(),
        )
        response = self._check_response(response, f"read address {address}")
        return list(response.registers)

    def _write_register(self, address: int, value: int) -> None:
        self._check_connected()
        response = self.client.write_register(
            address=int(address),
            value=int(value),
            **self._device_kwargs(),
        )
        self._check_response(response, f"write address {address}")

    def read_status(self) -> OnRobotGripperStatus:
        with self.lock:
            prox_offsets = self._read_holding_registers(address=5, count=2)
            status = self._read_holding_registers(address=257, count=26)
            out_zero = self._read_holding_registers(address=0, count=1)

        raw = prox_offsets + status + out_zero
        return OnRobotGripperStatus(
            prox_off_l=int(raw[0]),
            prox_off_r=int(raw[1]),
            g_gwd=int(raw[25]),
            g_wdf=int(raw[25]),
            busy=int(raw[26]),
            grip_det=int(raw[27]),
            in_zero=int(raw[28]),
        )

    def send_command_raw(self, width_01mm: int, force_01n: int, control: int) -> None:
        width_01mm = max(0, min(int(round(self.MAX_WIDTH_MM * 10.0)), int(width_01mm)))
        force_01n = max(0, min(int(round(self.MAX_FORCE_N * 10.0)), int(force_01n)))
        control = 1 if int(control) else 0

        with self.lock:
            self._write_register(address=0, value=0)
            self._write_register(address=2, value=force_01n)
            self._write_register(address=3, value=width_01mm)
            self._write_register(address=4, value=control)

    def command_width(self, width_mm: float, force_n: float = 8.0) -> None:
        self.send_command_raw(
            width_01mm=int(round(float(width_mm) * 10.0)),
            force_01n=int(round(float(force_n) * 10.0)),
            control=1,
        )

    def hold_current_width(self, force_n: float = 8.0) -> None:
        status = self.read_status()
        self.command_width(width_mm=status.width_mm, force_n=force_n)

    def stop_motion(self) -> None:
        status = self.read_status()
        self.send_command_raw(
            width_01mm=status.g_wdf,
            force_01n=0,
            control=0,
        )

    def wait_until_idle(
        self,
        timeout: float = 4.0,
        poll_period: float = 0.10,
    ) -> OnRobotGripperStatus:
        deadline = time.monotonic() + float(timeout)
        last_status = self.read_status()

        while time.monotonic() < deadline:
            last_status = self.read_status()
            if last_status.busy == 0:
                return last_status
            time.sleep(float(poll_period))

        return last_status


class AsyncOnRobotGripperController:
    """
    Small non-blocking teleop helper around the RG2FT Modbus client.

    The robot control loop can call set_command() at 50 Hz; the Modbus writes
    happen in a separate thread at a lower rate.
    """

    def __init__(
        self,
        ip: str,
        port: int = 502,
        timeout: float = 1.0,
        open_width_mm: float = 85.0,
        close_width_mm: float = 35.0,
        force_n: float = 8.0,
        command_period: float = 0.10,
        command_deadband_mm: float = 1.0,
        cmd_min: float = -0.2,
        cmd_max: float = 1.2,
        control_mode: str = "button",
        enabled: bool = False,
    ) -> None:
        self.gripper = OnRobotRG2FTModbus(ip=ip, port=port, timeout=timeout)
        self.open_width_mm = float(open_width_mm)
        self.close_width_mm = float(close_width_mm)
        self.force_n = float(force_n)
        self.command_period = float(command_period)
        self.command_deadband_mm = float(command_deadband_mm)
        self.cmd_min = float(cmd_min)
        self.cmd_max = float(cmd_max)
        if control_mode not in {"button", "width"}:
            raise ValueError(f"Unknown gripper control mode: {control_mode}")
        self.control_mode = str(control_mode)
        self.enabled = bool(enabled)

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.target_width_mm: float | None = None
        self.last_sent_width_mm: float | None = None
        self.button_direction = 0
        self.last_button_direction = 0
        self.stop_requested = False
        self.last_status: OnRobotGripperStatus | None = None
        self.last_error: str | None = None

    def connect(self) -> None:
        self.gripper.connect()
        self.last_status = self.gripper.read_status()
        self.target_width_mm = self.last_status.width_mm
        self.last_sent_width_mm = self.last_status.width_mm

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

        print("[GRIPPER] Connected.")
        print("[GRIPPER] Motion enabled:", self.enabled)
        print("[GRIPPER] Control mode:", self.control_mode)
        print(f"[GRIPPER] width: {self.last_status.width_mm:.1f} mm")
        print(f"[GRIPPER] open/close: {self.open_width_mm:.1f}/{self.close_width_mm:.1f} mm")

    def close(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
        self.gripper.close()
        print("[GRIPPER] Connection closed.")

    def set_command(self, command: float) -> float:
        width_mm = self.command_to_width(command)
        with self.lock:
            self.target_width_mm = width_mm
        return width_mm

    def set_button_direction(self, direction: int) -> float | None:
        direction = max(-1, min(1, int(direction)))
        target_width_mm = None

        if direction > 0:
            target_width_mm = self.open_width_mm
        elif direction < 0:
            target_width_mm = self.close_width_mm

        with self.lock:
            if direction != self.button_direction and direction == 0:
                self.stop_requested = True
            self.button_direction = direction
            if target_width_mm is not None:
                self.target_width_mm = target_width_mm

        return target_width_mm

    def command_to_width(self, command: float) -> float:
        if self.cmd_max <= self.cmd_min:
            alpha = 0.0
        else:
            alpha = (float(command) - self.cmd_min) / (self.cmd_max - self.cmd_min)
        alpha = max(0.0, min(1.0, alpha))
        return (1.0 - alpha) * self.open_width_mm + alpha * self.close_width_mm

    def get_status_snapshot(self) -> tuple[OnRobotGripperStatus | None, str | None]:
        with self.lock:
            return self.last_status, self.last_error

    def _worker(self) -> None:
        while not self.stop_event.is_set():
            with self.lock:
                target_width_mm = self.target_width_mm
                last_sent_width_mm = self.last_sent_width_mm
                button_direction = self.button_direction
                stop_requested = self.stop_requested
                if stop_requested:
                    self.stop_requested = False

            try:
                status = self.gripper.read_status()
                with self.lock:
                    self.last_status = status
                    self.last_error = None

                if self.enabled and self.control_mode == "button":
                    if button_direction != self.last_button_direction:
                        if button_direction > 0:
                            self.gripper.command_width(
                                self.open_width_mm,
                                force_n=self.force_n,
                            )
                            with self.lock:
                                self.last_sent_width_mm = self.open_width_mm
                        elif button_direction < 0:
                            self.gripper.command_width(
                                self.close_width_mm,
                                force_n=self.force_n,
                            )
                            with self.lock:
                                self.last_sent_width_mm = self.close_width_mm
                        elif stop_requested:
                            self.gripper.stop_motion()

                        self.last_button_direction = button_direction

                elif self.enabled:
                    should_send = (
                        target_width_mm is not None
                        and (
                            last_sent_width_mm is None
                            or abs(target_width_mm - last_sent_width_mm)
                            >= self.command_deadband_mm
                        )
                        and status.busy == 0
                    )

                    if should_send:
                        self.gripper.command_width(target_width_mm, force_n=self.force_n)
                        with self.lock:
                            self.last_sent_width_mm = target_width_mm

            except Exception as exc:
                with self.lock:
                    self.last_error = str(exc)

            self.stop_event.wait(self.command_period)

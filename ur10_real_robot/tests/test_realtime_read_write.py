#!/usr/bin/env python3
from __future__ import annotations

import os
import time

import numpy as np

from ur10_real_robot.backends import UR10RealtimeSession


ROBOT_IP = os.environ.get("ROBOT_IP", "192.168.2.100")
GRIPPER_IP = os.environ.get("GRIPPER_IP", "192.168.1.1")
GRIPPER_PORT = int(os.environ.get("GRIPPER_PORT", "502"))
TEST_GRIPPER = os.environ.get("TEST_GRIPPER", "0") == "1"
GRIPPER_SEND_HOLD = os.environ.get("GRIPPER_SEND_HOLD", "0") == "1"
GRIPPER_FORCE_10N = int(os.environ.get("GRIPPER_FORCE_10N", "80"))

TEST_DURATION = 3.0

# Premier test safe : 0.02 s.
# Ensuite tu pourras tester 0.008 s si tout est stable.
SERVO_T = 0.02

WRITE_WARNING_MS = 5.0


class OnRobotGripperModbus:
    """Minimal OnRobot RG2FT Modbus client used by this real robot smoke test."""

    def __init__(self, ip: str, port: int, timeout: float = 1.0) -> None:
        self.ip = ip
        self.port = int(port)
        self.timeout = float(timeout)
        self.client = None
        self.device_id_kwarg = "unit"

    def connect(self) -> "OnRobotGripperModbus":
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

    def _device_kwargs(self) -> dict[str, int]:
        return {self.device_id_kwarg: 65}

    def _check_response(self, response, label: str):
        if response is None:
            raise RuntimeError(f"{label}: no Modbus response")
        if hasattr(response, "isError") and response.isError():
            raise RuntimeError(f"{label}: Modbus error response {response}")
        return response

    def _read_holding_registers(self, address: int, count: int) -> list[int]:
        response = self.client.read_holding_registers(
            address=address,
            count=count,
            **self._device_kwargs(),
        )
        response = self._check_response(response, f"read address {address}")
        return list(response.registers)

    def _write_register(self, address: int, value: int) -> None:
        response = self.client.write_register(
            address=address,
            value=int(value),
            **self._device_kwargs(),
        )
        self._check_response(response, f"write address {address}")

    def read_status(self) -> dict[str, int]:
        # Same register layout as bringup_gripper/comModbusTcp.py.
        prox_offsets = self._read_holding_registers(address=5, count=2)
        status = self._read_holding_registers(address=257, count=26)
        out_zero = self._read_holding_registers(address=0, count=1)
        raw = prox_offsets + status + out_zero

        return {
            "prox_off_l": raw[0],
            "prox_off_r": raw[1],
            "g_gwd": raw[25],
            "g_wdf": raw[25],
            "busy": raw[26],
            "grip_det": raw[27],
            "in_zero": raw[28],
        }

    def send_command(self, width_10mm: int, force_10n: int, control: int) -> None:
        # Registers copied from bringup_gripper/comModbusTcp.py:
        # address 0 out_zero, 2 force, 3 width, 4 control.
        self._write_register(address=0, value=0)
        self._write_register(address=2, value=max(0, min(400, int(force_10n))))
        self._write_register(address=3, value=max(0, min(1000, int(width_10mm))))
        self._write_register(address=4, value=int(control))


def run_gripper_smoke_test() -> None:
    print("\n[INFO] Connecting to OnRobot gripper...")
    print(f"Gripper IP    : {GRIPPER_IP}")
    print(f"Gripper port  : {GRIPPER_PORT}")
    print(f"Send hold cmd : {GRIPPER_SEND_HOLD}")

    gripper = OnRobotGripperModbus(
        ip=GRIPPER_IP,
        port=GRIPPER_PORT,
        timeout=1.0,
    ).connect()

    try:
        status = gripper.read_status()
        width_mm = float(status["g_wdf"]) / 10.0

        print("[GRIPPER] status:", status)
        print(f"[GRIPPER] width : {width_mm:.1f} mm")

        if GRIPPER_SEND_HOLD:
            print("[GRIPPER] Sending hold-current-width command.")
            gripper.send_command(
                width_10mm=int(status["g_wdf"]),
                force_10n=GRIPPER_FORCE_10N,
                control=1,
            )
            time.sleep(0.2)
            print("[GRIPPER] status after hold:", gripper.read_status())
        else:
            print("[GRIPPER] Read-only test done. No command sent.")

    finally:
        gripper.close()


def stats_ms(values: list[float]) -> tuple[float, float, float, float, float, float]:
    arr = np.asarray(values, dtype=float) * 1000.0
    return (
        float(np.mean(arr)),
        float(np.std(arr)),
        float(np.min(arr)),
        float(np.max(arr)),
        float(np.percentile(arr, 95)),
        float(np.percentile(arr, 99)),
    )


def main() -> None:
    print("-------------------------------------------")
    print("UR10 CB2 - REALTIME SERVOJ HOLD TEST")
    print("-------------------------------------------")
    print(f"Robot IP      : {ROBOT_IP}")
    print(f"Test duration : {TEST_DURATION:.1f} s")
    print(f"servoj t      : {SERVO_T:.4f} s")
    print("Command       : servoj(q_hold)")
    print(f"Gripper test  : {TEST_GRIPPER}")
    if TEST_GRIPPER:
        print(f"Gripper IP    : {GRIPPER_IP}:{GRIPPER_PORT}")
        print(f"Gripper cmd   : {'hold current width' if GRIPPER_SEND_HOLD else 'read-only'}")
    print("-------------------------------------------")
    print("ATTENTION : ce test envoie des commandes au vrai robot.")
    print("Le robot devrait rester immobile car q_hold = position actuelle.")
    if TEST_GRIPPER and GRIPPER_SEND_HOLD:
        print("La pince recevra aussi une commande hold sur sa largeur actuelle.")
    print("Speed slider tablette recommandé : 5% ou 10%.")
    print("Main proche de l'arrêt d'urgence.")
    print("-------------------------------------------")

    answer = input("Tape YES pour lancer le test : ")
    if answer.strip() != "YES":
        print("Annulé.")
        return

    session = None

    try:
        print("\n[INFO] Connecting to UR10 realtime session...")
        session = UR10RealtimeSession(
            robot_ip=ROBOT_IP,
            socket_timeout=1.0,
        ).connect()

        print("\n[INFO] Reading initial robot state...")
        init_data = session.read(wait=True)

        if "qActual" not in init_data:
            raise KeyError(f"'qActual' not found. Available keys: {list(init_data.keys())}")

        q_hold = np.asarray(init_data["qActual"], dtype=float).reshape(-1)

        if q_hold.shape[0] != 6:
            raise ValueError(f"Expected 6 joints, got {q_hold.shape}")

        print("Initial joints rad:", np.round(q_hold, 6))
        print("Initial joints deg:", np.round(np.degrees(q_hold), 3))

        if TEST_GRIPPER:
            run_gripper_smoke_test()

        print("\n[INFO] Starting read + write hold test...")
        print("The robot should not move. It only receives servoj(q_hold).")

        loop_timestamps = []
        read_times = []
        write_times = []
        q_errors = []
        ctrl_timestamps = []

        start_time = time.perf_counter()
        loop_count = 0

        while time.perf_counter() - start_time < TEST_DURATION:
            loop_start = time.perf_counter()

            read_start = time.perf_counter()
            data = session.read(wait=True)
            read_end = time.perf_counter()

            write_start = time.perf_counter()
            session.send_servoj(q_hold, t=SERVO_T)
            write_end = time.perf_counter()

            q_actual = np.asarray(data["qActual"], dtype=float).reshape(-1)
            q_error = float(np.max(np.abs(q_actual - q_hold)))

            ctrl_ts = data.get("ctrltimestamp", None)
            if ctrl_ts is not None:
                ctrl_timestamps.append(float(ctrl_ts))

            read_times.append(read_end - read_start)
            write_times.append(write_end - write_start)
            q_errors.append(q_error)
            loop_timestamps.append(loop_start)

            if loop_count % 50 == 0:
                print(
                    f"[{loop_count:04d}] "
                    f"q drift max = {np.degrees(q_error):.6f} deg"
                )

            loop_count += 1

        print("\n[INFO] Sending stopj...")
        try:
            session.stopj(1.0)
        except Exception as e:
            print("[WARN] stopj failed:", e)

        loop_deltas = np.diff(loop_timestamps)

        if len(loop_deltas) > 0:
            avg_loop_dt = float(np.mean(loop_deltas))
            std_loop_dt = float(np.std(loop_deltas))
            loop_freq = 1.0 / avg_loop_dt
        else:
            avg_loop_dt = 0.0
            std_loop_dt = 0.0
            loop_freq = 0.0

        read_avg, read_std, read_min, read_max, read_p95, read_p99 = stats_ms(read_times)
        write_avg, write_std, write_min, write_max, write_p95, write_p99 = stats_ms(write_times)

        q_errors = np.asarray(q_errors, dtype=float)

        print("\n" + "=" * 50)
        print("REALTIME READ + WRITE TEST RESULTS")
        print("=" * 50)
        print(f"Total cycles:          {loop_count}")
        print(f"Loop frequency:        {loop_freq:.2f} Hz")
        print(f"Loop avg interval:     {avg_loop_dt * 1000.0:.3f} ms")
        print(f"Loop jitter std:       {std_loop_dt * 1000.0:.3f} ms")
        print("-" * 50)
        print(f"Read avg time:         {read_avg:.3f} ms")
        print(f"Read std time:         {read_std:.3f} ms")
        print(f"Read min / max:        {read_min:.3f} / {read_max:.3f} ms")
        print(f"Read p95 / p99:        {read_p95:.3f} / {read_p99:.3f} ms")
        print("-" * 50)
        print(f"Write avg time:        {write_avg:.3f} ms")
        print(f"Write std time:        {write_std:.3f} ms")
        print(f"Write min / max:       {write_min:.3f} / {write_max:.3f} ms")
        print(f"Write p95 / p99:       {write_p95:.3f} / {write_p99:.3f} ms")
        print("-" * 50)
        print(f"Max joint drift rad:   {float(np.max(q_errors)):.8f}")
        print(f"Max joint drift deg:   {float(np.degrees(np.max(q_errors))):.6f}")
        print("=" * 50)

        if len(ctrl_timestamps) > 2:
            ctrl_deltas = np.diff(ctrl_timestamps)
            ctrl_avg_dt = float(np.mean(ctrl_deltas))
            ctrl_freq = 1.0 / ctrl_avg_dt
            print(f"Controller stream freq from timestamps: {ctrl_freq:.2f} Hz")

        if write_max > WRITE_WARNING_MS:
            print("\nWARNING: write time sometimes becomes high.")
            print("The 30002 socket may be slowing down or buffering commands.")
        else:
            print("\nWrite socket looks fast. No obvious blocking detected.")

        if 115.0 <= loop_freq <= 135.0:
            print("Loop frequency is close to 125 Hz.")
        elif 55.0 <= loop_freq <= 70.0:
            print("Loop frequency is around 60 Hz.")
        else:
            print("Loop frequency is not close to 125 Hz.")

    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        if session is not None:
            try:
                session.stopj(1.0)
            except Exception:
                pass

    except Exception as e:
        print("\n[ERROR]", e)
        if session is not None:
            try:
                session.stopj(1.0)
            except Exception:
                pass

    finally:
        if session is not None:
            try:
                session.close()
            except Exception:
                pass

        print("\nSession closed.")


if __name__ == "__main__":
    main()

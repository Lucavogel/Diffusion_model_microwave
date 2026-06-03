import time

import numpy as np

from ur10_real_robot.backends import UR10RealtimeSession


ROBOT_IP = "192.168.0.60"

TEST_DURATION = 10.0
SERVO_T = 0.008

WRITE_WARNING_MS = 5.0


def stats_ms(values: list[float]) -> tuple[float, float, float, float]:
    arr = np.asarray(values, dtype=float) * 1000.0
    return (
        float(np.mean(arr)),
        float(np.std(arr)),
        float(np.min(arr)),
        float(np.max(arr)),
    )


def main() -> None:
    print("Connecting to UR10 realtime session...")
    print(f"Robot IP: {ROBOT_IP}")
    print(f"Test duration: {TEST_DURATION:.1f} s")
    print(f"servoj t: {SERVO_T:.4f} s")

    session = UR10RealtimeSession(
        robot_ip=ROBOT_IP,
        socket_timeout=1.0,
    ).connect()

    try:
        print("\nReading initial robot state...")
        init_data = session.read(wait=True)

        q_hold = np.asarray(init_data["qActual"], dtype=float)
        print("Initial joints rad:", q_hold)
        print("Initial joints deg:", np.degrees(q_hold))

        print("\nStarting read + write hold test...")
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

            q_actual = np.asarray(data["qActual"], dtype=float)
            q_error = float(np.max(np.abs(q_actual - q_hold)))

            ctrl_ts = data.get("ctrltimestamp", None)
            if ctrl_ts is not None:
                ctrl_timestamps.append(float(ctrl_ts))

            read_times.append(read_end - read_start)
            write_times.append(write_end - write_start)
            q_errors.append(q_error)
            loop_timestamps.append(loop_start)

            loop_count += 1

        session.stopj(1.0)

        loop_deltas = np.diff(loop_timestamps)

        if len(loop_deltas) > 0:
            avg_loop_dt = float(np.mean(loop_deltas))
            std_loop_dt = float(np.std(loop_deltas))
            loop_freq = 1.0 / avg_loop_dt
        else:
            avg_loop_dt = 0.0
            std_loop_dt = 0.0
            loop_freq = 0.0

        read_avg, read_std, read_min, read_max = stats_ms(read_times)
        write_avg, write_std, write_min, write_max = stats_ms(write_times)

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
        print("-" * 50)
        print(f"Write avg time:        {write_avg:.3f} ms")
        print(f"Write std time:        {write_std:.3f} ms")
        print(f"Write min / max:       {write_min:.3f} / {write_max:.3f} ms")
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

    finally:
        try:
            session.stopj(1.0)
        except Exception:
            pass

        session.close()
        print("\nSession closed.")


if __name__ == "__main__":
    main()
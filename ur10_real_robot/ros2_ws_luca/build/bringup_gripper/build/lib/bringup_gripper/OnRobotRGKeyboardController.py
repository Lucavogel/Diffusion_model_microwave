#!/usr/bin/env python3

import select
import sys
import termios
import time
import tty

import rclpy
from rclpy.node import Node

from onrobot_rg_msgs.msg import OnRobotRGInput
from onrobot_rg_msgs.msg import OnRobotRGOutput


class RawTerminal:
    def __init__(self, stream):
        self.stream = stream
        self.fd = stream.fileno()
        self.original = None

    def __enter__(self):
        if self.stream.isatty():
            self.original = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.original is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.original)


class OnRobotRGKeyboardController(Node):
    def __init__(self):
        super().__init__("OnRobotRGKeyboardController")

        self.declare_parameter("open_width_mm", 80.0)
        self.declare_parameter("close_width_mm", 50.0)
        self.declare_parameter("width_step_mm", 5.0)
        self.declare_parameter("force_n", 2.0)
        self.declare_parameter("force_step_n", 0.5)
        self.declare_parameter("repeat", 5)
        self.declare_parameter("rate_hz", 5.0)
        self.declare_parameter("stop_first", True)

        self.open_width_mm = float(self.get_parameter("open_width_mm").value)
        self.close_width_mm = float(self.get_parameter("close_width_mm").value)
        self.width_step_mm = float(self.get_parameter("width_step_mm").value)
        self.force_n = float(self.get_parameter("force_n").value)
        self.force_step_n = float(self.get_parameter("force_step_n").value)
        self.repeat = int(self.get_parameter("repeat").value)
        self.rate_hz = float(self.get_parameter("rate_hz").value)
        self.stop_first = bool(self.get_parameter("stop_first").value)

        self.latest_width_mm = None
        self.latest_busy = None
        self.latest_grip_det = None
        self.latest_prox_l = None
        self.latest_prox_r = None
        self.target_width_mm = self.open_width_mm
        self.max_width_mm = 100.0

        self.pub = self.create_publisher(OnRobotRGOutput, "OnRobotRGOutput", 10)
        self.sub = self.create_subscription(
            OnRobotRGInput,
            "OnRobotRGInput",
            self.status_callback,
            10,
        )

    def status_callback(self, status: OnRobotRGInput):
        self.latest_width_mm = status.grip_width / 10.0
        self.latest_busy = status.busy
        self.latest_grip_det = status.grip_det
        self.latest_prox_l = status.prox_l / 10.0
        self.latest_prox_r = status.prox_r / 10.0
        if self.target_width_mm is None:
            self.target_width_mm = self.latest_width_mm

    def print_help(self):
        print(
            "\nKeyboard control\n"
            "  o: open to preset width\n"
            "  c: close to preset width\n"
            "  Right / k: open by one step\n"
            "  Left / j: close by one step\n"
            "  + / Up: increase force\n"
            "  - / Down: decrease force\n"
            "  s or Space: stop\n"
            "  p: print current status\n"
            "  q: quit\n"
        )

    def print_status(self):
        width = "?" if self.latest_width_mm is None else f"{self.latest_width_mm:.1f} mm"
        busy = "?" if self.latest_busy is None else str(self.latest_busy)
        grip = "?" if self.latest_grip_det is None else str(self.latest_grip_det)
        prox_l = "?" if self.latest_prox_l is None else f"{self.latest_prox_l:.1f} mm"
        prox_r = "?" if self.latest_prox_r is None else f"{self.latest_prox_r:.1f} mm"
        print(
            f"status: width={width} busy={busy} grip_det={grip} "
            f"prox_l={prox_l} prox_r={prox_r} "
            f"target={self.target_width_mm:.1f} mm force={self.force_n:.1f} N"
        )

    def clamp_width(self, width_mm: float) -> float:
        return max(0.0, min(self.max_width_mm, width_mm))

    def clamp_force(self, force_n: float) -> float:
        return max(0.0, min(40.0, force_n))

    def publish_burst(self, width_mm: float, force_n: float, control: int):
        command = OnRobotRGOutput()
        command.r_gfr = int(round(self.clamp_force(force_n) * 10.0))
        command.r_gwd = int(round(self.clamp_width(width_mm) * 10.0))
        command.r_ctr = control
        command.out_zero = 0
        command.out_prox_off_r = 0
        command.out_prox_off_l = 0

        period = 1.0 / self.rate_hz if self.rate_hz > 0 else 0.2
        for _ in range(max(1, self.repeat)):
            self.pub.publish(command)
            time.sleep(period)

    def stop_motion(self):
        self.get_logger().info("Stop")
        self.publish_burst(self.target_width_mm, self.force_n, 0)

    def move_to(self, width_mm: float):
        self.target_width_mm = self.clamp_width(width_mm)
        self.get_logger().info(
            f"Move to {self.target_width_mm:.1f} mm with {self.force_n:.1f} N"
        )
        if self.stop_first:
            self.publish_burst(self.target_width_mm, self.force_n, 0)
            time.sleep(0.4)
        self.publish_burst(self.target_width_mm, self.force_n, 1)

    def step_width(self, delta_mm: float):
        base_width = self.latest_width_mm if self.latest_width_mm is not None else self.target_width_mm
        self.move_to(base_width + delta_mm)

    def adjust_force(self, delta_n: float):
        self.force_n = self.clamp_force(self.force_n + delta_n)
        self.get_logger().info(f"Force set to {self.force_n:.1f} N")
        self.print_status()

    def read_key(self, timeout_sec: float = 0.1):
        ready, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if not ready:
            return None

        first = sys.stdin.read(1)
        if first != "\x1b":
            return first

        if not select.select([sys.stdin], [], [], 0.01)[0]:
            return first
        second = sys.stdin.read(1)
        if second != "[":
            return first + second
        if not select.select([sys.stdin], [], [], 0.01)[0]:
            return first + second
        third = sys.stdin.read(1)
        return first + second + third

    def handle_key(self, key: str) -> bool:
        if key in ("q", "Q"):
            return False
        if key in ("o", "O"):
            self.move_to(self.open_width_mm)
        elif key in ("c", "C"):
            self.move_to(self.close_width_mm)
        elif key in ("k", "\x1b[C"):
            self.step_width(+self.width_step_mm)
        elif key in ("j", "\x1b[D"):
            self.step_width(-self.width_step_mm)
        elif key in ("+", "\x1b[A"):
            self.adjust_force(+self.force_step_n)
        elif key in ("-", "\x1b[B"):
            self.adjust_force(-self.force_step_n)
        elif key in ("s", "S", " "):
            self.stop_motion()
        elif key in ("p", "P"):
            self.print_status()
        elif key in ("h", "H", "?"):
            self.print_help()
        return True

    def run(self):
        self.print_help()
        self.get_logger().info("Waiting for status on /OnRobotRGInput ...")

        with RawTerminal(sys.stdin):
            running = True
            while running and rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.05)
                key = self.read_key(timeout_sec=0.05)
                if key is not None:
                    running = self.handle_key(key)


def main(args=None):
    rclpy.init(args=args)
    node = OnRobotRGKeyboardController()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node

from onrobot_rg_msgs.msg import OnRobotRGOutput


class OnRobotRGMove(Node):
    def __init__(self):
        super().__init__("OnRobotRGMove")

        self.declare_parameter("width_mm", 80.0)
        self.declare_parameter("force_n", 2.0)
        self.declare_parameter("stop_first", False)
        self.declare_parameter("repeat", 5)
        self.declare_parameter("rate_hz", 5.0)

        self.width_mm = float(self.get_parameter("width_mm").value)
        self.force_n = float(self.get_parameter("force_n").value)
        self.stop_first = bool(self.get_parameter("stop_first").value)
        self.repeat = int(self.get_parameter("repeat").value)
        self.rate_hz = float(self.get_parameter("rate_hz").value)

        self.pub = self.create_publisher(OnRobotRGOutput, "OnRobotRGOutput", 10)

    def _publish(self, width_mm: float, force_n: float, control: int):
        command = OnRobotRGOutput()
        command.r_gfr = max(0, min(400, int(round(force_n * 10.0))))
        command.r_gwd = max(0, min(1000, int(round(width_mm * 10.0))))
        command.r_ctr = control
        command.out_zero = 0
        command.out_prox_off_r = 0
        command.out_prox_off_l = 0

        period = 1.0 / self.rate_hz if self.rate_hz > 0 else 0.2
        for _ in range(max(1, self.repeat)):
            self.pub.publish(command)
            time.sleep(period)

    def run(self):
        if self.stop_first:
            self.get_logger().info("Sending stop before motion")
            self._publish(self.width_mm, self.force_n, 0)
            time.sleep(0.5)

        self.get_logger().info(
            f"Sending grip command: width={self.width_mm:.1f} mm force={self.force_n:.1f} N"
        )
        self._publish(self.width_mm, self.force_n, 1)


def main(args=None):
    rclpy.init(args=args)
    node = OnRobotRGMove()
    try:
        node.run()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

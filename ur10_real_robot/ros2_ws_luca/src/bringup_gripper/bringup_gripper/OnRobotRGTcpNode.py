#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from onrobot_rg_msgs.msg import OnRobotRGInput
from onrobot_rg_msgs.msg import OnRobotRGOutput

from bringup_gripper.baseOnRobotRG import onrobotbaseRG
from bringup_gripper.comModbusTcp import Communication


class OnRobotRGTcpNode(Node):
    def __init__(self):
        super().__init__("OnRobotRGTcpNode")

        self.declare_parameter("ip", "192.168.1.1")
        self.declare_parameter("port", 502)
        self.declare_parameter("gripper", "rg2ft")
        self.declare_parameter("dummy", False)
        self.declare_parameter("poll_period", 0.1)
        self.declare_parameter("publish_joint_states", True)
        self.declare_parameter("joint_state_topic", "joint_states")
        self.declare_parameter("joint_name", "")
        self.declare_parameter("joint_prefix", "")
        self.declare_parameter("joint_open_position", 0.0)
        self.declare_parameter("joint_closed_position", 1.18)

        self.ip = self.get_parameter("ip").value
        self.port = int(self.get_parameter("port").value)
        self.gtype = self.get_parameter("gripper").value
        self.dummy = bool(self.get_parameter("dummy").value)
        self.poll_period = float(self.get_parameter("poll_period").value)
        self.publish_joint_states = bool(
            self.get_parameter("publish_joint_states").value
        )
        self.joint_state_topic = str(self.get_parameter("joint_state_topic").value)
        self.joint_name = str(self.get_parameter("joint_name").value)
        self.joint_prefix = str(self.get_parameter("joint_prefix").value)
        self.joint_open_position = float(
            self.get_parameter("joint_open_position").value
        )
        self.joint_closed_position = float(
            self.get_parameter("joint_closed_position").value
        )

        if not self.joint_name:
            self.joint_name = f"{self.joint_prefix}finger_joint"

        self.pub = self.create_publisher(OnRobotRGInput, "OnRobotRGInput", 10)
        self.sub = self.create_subscription(
            OnRobotRGOutput,
            "OnRobotRGOutput",
            self.command_callback,
            10,
        )
        self.joint_state_pub = None
        if self.publish_joint_states:
            self.joint_state_pub = self.create_publisher(
                JointState,
                self.joint_state_topic,
                10,
            )

        self.gripper = onrobotbaseRG(self.gtype)
        self.communication = Communication(dummy=self.dummy, logger=self.get_logger())
        self.gripper.client = self.communication
        self.max_width_mm = 100.0 if self.gtype == "rg2ft" else 160.0

        if not self.dummy:
            connected = self.communication.connectToDevice(self.ip, self.port)
            if not connected:
                raise RuntimeError(
                    f"Unable to connect to OnRobot gripper at {self.ip}:{self.port}"
                )
            self.get_logger().info(
                f"Connected to OnRobot {self.gtype} at {self.ip}:{self.port}"
            )
            self.get_logger().info(
                "Topics: subscribe /OnRobotRGOutput, publish /OnRobotRGInput"
            )
            if self.joint_state_pub is not None:
                self.get_logger().info(
                    f"Publishing {self.joint_name} to /{self.joint_state_topic.lstrip('/')}"
                )

        self.timer = self.create_timer(self.poll_period, self.publish_status)

    def command_callback(self, command):
        try:
            self.gripper.refreshCommand(command)
            self.gripper.sendCommand()
        except Exception as exc:
            self.get_logger().error(f"Failed to send command: {exc}")

    def publish_status(self):
        try:
            status = self.gripper.getStatus()
            self.pub.publish(status)
            self.publish_joint_state(status)
        except Exception as exc:
            self.get_logger().error(f"Failed to read status: {exc}")

    def publish_joint_state(self, status):
        if self.joint_state_pub is None:
            return

        width_mm = max(0.0, min(self.max_width_mm, status.grip_width / 10.0))
        open_ratio = width_mm / self.max_width_mm if self.max_width_mm > 0.0 else 0.0
        joint_position = self.joint_closed_position + open_ratio * (
            self.joint_open_position - self.joint_closed_position
        )

        message = JointState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.name = [self.joint_name]
        message.position = [joint_position]
        self.joint_state_pub.publish(message)

    def destroy_node(self):
        try:
            self.communication.disconnectFromDevice()
        except Exception:
            pass
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = OnRobotRGTcpNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

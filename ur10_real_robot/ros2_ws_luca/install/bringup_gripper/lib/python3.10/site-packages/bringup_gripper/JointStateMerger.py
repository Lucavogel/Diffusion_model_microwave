#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class JointStateMerger(Node):
    def __init__(self):
        super().__init__("JointStateMerger")

        self.declare_parameter(
            "robot_joint_states_topic", "/joint_state_broadcaster/joint_states"
        )
        self.declare_parameter(
            "gripper_joint_states_topic", "gripper_joint_states"
        )
        self.declare_parameter("output_topic", "joint_states")

        self.robot_joint_states_topic = str(
            self.get_parameter("robot_joint_states_topic").value
        )
        self.gripper_joint_states_topic = str(
            self.get_parameter("gripper_joint_states_topic").value
        )
        self.output_topic = str(self.get_parameter("output_topic").value)

        input_topics = {
            self.robot_joint_states_topic,
            self.gripper_joint_states_topic,
        }
        if self.output_topic in input_topics:
            raise RuntimeError(
                "output_topic must be different from input topics to avoid a feedback loop"
            )

        self.joint_order = []
        self.joint_positions = {}

        self.publisher = self.create_publisher(JointState, self.output_topic, 10)
        self.robot_subscription = self.create_subscription(
            JointState,
            self.robot_joint_states_topic,
            self.joint_state_callback,
            100,
        )
        self.gripper_subscription = self.create_subscription(
            JointState,
            self.gripper_joint_states_topic,
            self.joint_state_callback,
            100,
        )

        self.get_logger().info(
            "Merging "
            f"{self.robot_joint_states_topic} + {self.gripper_joint_states_topic} "
            f"-> /{self.output_topic.lstrip('/')}"
        )

    def joint_state_callback(self, message: JointState):
        updated = False
        for index, joint_name in enumerate(message.name):
            if index >= len(message.position):
                continue
            if joint_name not in self.joint_positions:
                self.joint_order.append(joint_name)
            self.joint_positions[joint_name] = message.position[index]
            updated = True

        if updated:
            self.publish_merged_joint_state()

    def publish_merged_joint_state(self):
        message = JointState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.name = list(self.joint_order)
        message.position = [self.joint_positions[name] for name in self.joint_order]
        self.publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = JointStateMerger()
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

import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import (
    generate_move_group_launch,
)


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    with open(absolute_file_path, "r") as file:
        return yaml.safe_load(file)


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder(
        "ur10_d455_support_rg2ft",
        package_name="earth_robot_moveit_config",
    ).to_moveit_configs()

    move_group_launch = generate_move_group_launch(moveit_config)
    servo_yaml = load_yaml("earth_robot_moveit_config", "config/ur10_servo.yaml")
    servo_params = {"moveit_servo": servo_yaml}

    rviz_config_file = os.path.join(
        get_package_share_directory("earth_robot_moveit_config"),
        "config",
        "moveit.rviz",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
        ],
    )

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node_main",
        name="servo_node_main",
        output="screen",
        parameters=[
            servo_params,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
        ],
    )

    return LaunchDescription(move_group_launch.entities + [rviz_node, servo_node])

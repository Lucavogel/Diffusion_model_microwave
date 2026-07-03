import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    with open(absolute_file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def generate_launch_description():
    robot_ip = LaunchConfiguration("robot_ip")
    launch_gripper = LaunchConfiguration("launch_gripper")
    start_servo = LaunchConfiguration("start_servo")

    moveit_config = MoveItConfigsBuilder(
        "ur10_d455_support_rg2ft",
        package_name="earth_robot_moveit_config",
    ).to_moveit_configs()

    servo_yaml = load_yaml("earth_robot_moveit_config", "config/ur10_servo.yaml")
    servo_params = {"moveit_servo": servo_yaml}

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

    return LaunchDescription(
        [
            DeclareLaunchArgument("robot_ip", default_value="192.168.2.100"),
            DeclareLaunchArgument("launch_gripper", default_value="true"),
            DeclareLaunchArgument("start_servo", default_value="false"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("earth_robot_moveit_config"),
                            "launch",
                            "real.launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "robot_ip": robot_ip,
                    "launch_moveit_rviz": "false",
                    "launch_rviz": "false",
                    "headless_mode": "false",
                    "launch_gripper": launch_gripper,
                    "joint_state_merger": "true",
                    "robot_joint_states_topic": "/joint_state_broadcaster/joint_states",
                    "merged_joint_states_topic": "/joint_states",
                    "gripper_default_force_n": "10.0",
                    "gripper_command_max_force_n": "20.0",
                    "activate_joint_controller_on_startup": "false",
                }.items(),
            ),
            TimerAction(period=8.0, actions=[servo_node], condition=IfCondition(start_servo)),
        ]
    )
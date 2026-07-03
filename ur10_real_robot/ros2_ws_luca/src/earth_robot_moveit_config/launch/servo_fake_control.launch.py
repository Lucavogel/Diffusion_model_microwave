import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch.substitutions import Command
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    with open(absolute_file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_text(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    with open(absolute_file_path, "r", encoding="utf-8") as file:
        return file.read()


def generate_launch_description():
    description_package = get_package_share_directory("earth_robot_moveit_config")
    robot_description_xacro = os.path.join(
        description_package,
        "config",
        "ur10_d455_support_rg2ft.urdf.xacro",
    )
    ros2_control_xacro = os.path.join(
        get_package_share_directory("realsense2_description"),
        "urdf",
        "ur10_d455_support_rg2ft_driver.urdf",
    )

    moveit_config = (
        MoveItConfigsBuilder(
            "ur10_d455_support_rg2ft",
            package_name="earth_robot_moveit_config",
        )
        .to_moveit_configs()
    )

    servo_yaml = load_yaml("earth_robot_moveit_config", "config/ur10_servo.yaml")
    servo_params = {"moveit_servo": servo_yaml}

    robot_description = {
        "robot_description": Command([
            "xacro ",
            robot_description_xacro,
        ])
    }
    robot_description_with_control = {
        "robot_description": load_text("realsense2_description", "urdf/ur10_d455_support_rg2ft_driver.urdf")
    }

    fake_controllers_yaml = os.path.join(
        get_package_share_directory("earth_robot_moveit_config"),
        "config",
        "fake_servo_controllers.yaml",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        name="controller_manager",
        output="screen",
        parameters=[
            robot_description_with_control,
            fake_controllers_yaml,
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=[
            "joint_trajectory_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {
                "publish_robot_description_semantic": True,
            },
        ],
    )

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
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
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

    return LaunchDescription(
        [
            robot_state_publisher,
            ros2_control_node,
            TimerAction(
                period=2.0,
                actions=[
                    joint_state_broadcaster_spawner,
                    joint_trajectory_controller_spawner,
                ],
            ),
            TimerAction(
                period=3.0,
                actions=[move_group_node, rviz_node],
            ),
            TimerAction(
                period=4.0,
                actions=[servo_node],
            ),
        ]
    )
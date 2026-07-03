from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("robot_ip", default_value="192.168.21.128"),
            DeclareLaunchArgument("ur_type", default_value="ur10"),
            DeclareLaunchArgument("launch_rviz", default_value="true"),
            DeclareLaunchArgument("headless_mode", default_value="false"),
            DeclareLaunchArgument("launch_gripper", default_value="true"),
            DeclareLaunchArgument("gripper_default_force_n", default_value="40.0"),
            DeclareLaunchArgument(
                "gripper_command_max_force_n", default_value="40.0"
            ),
            DeclareLaunchArgument(
                "activate_joint_controller_on_startup", default_value="false"
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [FindPackageShare("earth_robot_moveit_config"), "launch", "real.launch.py"]
                    )
                ),
                launch_arguments={
                    "robot_ip": LaunchConfiguration("robot_ip"),
                    "ur_type": LaunchConfiguration("ur_type"),
                    "launch_moveit_rviz": LaunchConfiguration("launch_rviz"),
                    "headless_mode": LaunchConfiguration("headless_mode"),
                    "launch_gripper": LaunchConfiguration("launch_gripper"),
                    "gripper_default_force_n": LaunchConfiguration(
                        "gripper_default_force_n"
                    ),
                    "gripper_command_max_force_n": LaunchConfiguration(
                        "gripper_command_max_force_n"
                    ),
                    "activate_joint_controller_on_startup": LaunchConfiguration(
                        "activate_joint_controller_on_startup"
                    ),
                }.items(),
            )
        ]
    )

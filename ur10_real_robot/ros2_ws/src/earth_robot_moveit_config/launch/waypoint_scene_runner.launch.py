from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    package_share = FindPackageShare("earth_robot_moveit_config")
    moveit_config = MoveItConfigsBuilder(
        "ur10_d455_support_rg2ft",
        package_name="earth_robot_moveit_config",
    ).to_moveit_configs()

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "scene_file",
                default_value=PathJoinSubstitution(
                    [package_share, "config", "empty.scene"]
                ),
            ),
            DeclareLaunchArgument(
                "waypoints_file",
                default_value=PathJoinSubstitution(
                    [package_share, "config", "waypoints_example.txt"]
                ),
            ),
            DeclareLaunchArgument("planning_group", default_value="arm"),
            DeclareLaunchArgument("pose_link", default_value="tool0"),
            DeclareLaunchArgument("scene_frame", default_value="world"),
            DeclareLaunchArgument("cartesian_mode", default_value="true"),
            DeclareLaunchArgument("fallback_to_sequential", default_value="true"),
            DeclareLaunchArgument("execute", default_value="false"),
            DeclareLaunchArgument("validate_inputs_only", default_value="false"),
            DeclareLaunchArgument("eef_step", default_value="0.01"),
            DeclareLaunchArgument("min_fraction", default_value="0.99"),
            DeclareLaunchArgument("planning_time", default_value="5.0"),
            DeclareLaunchArgument("num_planning_attempts", default_value="1"),
            DeclareLaunchArgument("velocity_scaling", default_value="0.1"),
            DeclareLaunchArgument("acceleration_scaling", default_value="0.1"),
            DeclareLaunchArgument("gripper_command_topic", default_value="OnRobotRGOutput"),
            DeclareLaunchArgument("gripper_status_topic", default_value="OnRobotRGInput"),
            DeclareLaunchArgument("gripper_open_width_mm", default_value="47.3"),
            DeclareLaunchArgument("gripper_open_force_n", default_value="10.0"),
            DeclareLaunchArgument("gripper_close_width_mm", default_value="0.0"),
            DeclareLaunchArgument("gripper_close_force_n", default_value="40.0"),
            DeclareLaunchArgument("gripper_command_timeout_sec", default_value="10.0"),
            DeclareLaunchArgument("gripper_width_tolerance_mm", default_value="2.0"),
            DeclareLaunchArgument("planning_pipeline", default_value=""),
            DeclareLaunchArgument("planner_id", default_value=""),
            Node(
                package="earth_robot_moveit_config",
                executable="scene_waypoint_runner",
                name="scene_waypoint_runner",
                output="screen",
                parameters=[
                    moveit_config.to_dict(),
                    {
                        "scene_file": LaunchConfiguration("scene_file"),
                        "waypoints_file": LaunchConfiguration("waypoints_file"),
                        "planning_group": LaunchConfiguration("planning_group"),
                        "pose_link": LaunchConfiguration("pose_link"),
                        "scene_frame": LaunchConfiguration("scene_frame"),
                        "cartesian_mode": LaunchConfiguration("cartesian_mode"),
                        "fallback_to_sequential": LaunchConfiguration(
                            "fallback_to_sequential"
                        ),
                        "execute": LaunchConfiguration("execute"),
                        "validate_inputs_only": LaunchConfiguration(
                            "validate_inputs_only"
                        ),
                        "eef_step": LaunchConfiguration("eef_step"),
                        "min_fraction": LaunchConfiguration("min_fraction"),
                        "planning_time": LaunchConfiguration("planning_time"),
                        "num_planning_attempts": LaunchConfiguration(
                            "num_planning_attempts"
                        ),
                        "velocity_scaling": LaunchConfiguration("velocity_scaling"),
                        "acceleration_scaling": LaunchConfiguration(
                            "acceleration_scaling"
                        ),
                        "gripper_command_topic": LaunchConfiguration(
                            "gripper_command_topic"
                        ),
                        "gripper_status_topic": LaunchConfiguration(
                            "gripper_status_topic"
                        ),
                        "gripper_open_width_mm": LaunchConfiguration(
                            "gripper_open_width_mm"
                        ),
                        "gripper_open_force_n": LaunchConfiguration(
                            "gripper_open_force_n"
                        ),
                        "gripper_close_width_mm": LaunchConfiguration(
                            "gripper_close_width_mm"
                        ),
                        "gripper_close_force_n": LaunchConfiguration(
                            "gripper_close_force_n"
                        ),
                        "gripper_command_timeout_sec": LaunchConfiguration(
                            "gripper_command_timeout_sec"
                        ),
                        "gripper_width_tolerance_mm": LaunchConfiguration(
                            "gripper_width_tolerance_mm"
                        ),
                        "planning_pipeline": LaunchConfiguration("planning_pipeline"),
                        "planner_id": LaunchConfiguration("planner_id"),
                    }
                ],
            ),
        ]
    )

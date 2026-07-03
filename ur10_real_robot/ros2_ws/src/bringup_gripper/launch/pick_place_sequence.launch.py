from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "sequence_file",
                default_value=PathJoinSubstitution(
                    [
                        FindPackageShare("bringup_gripper"),
                        "config",
                        "pick_place_sequence_example.yaml",
                    ]
                ),
                description="YAML file containing the 4-point pick-and-place sequence",
            ),
            DeclareLaunchArgument(
                "execute",
                default_value="false",
                description="If true, execute the sequence. If false, only validate and print it.",
            ),
            Node(
                package="bringup_gripper",
                executable="pick_place_sequence",
                name="pick_place_sequence",
                output="screen",
                parameters=[
                    {"sequence_file": LaunchConfiguration("sequence_file")},
                    {"execute": LaunchConfiguration("execute")},
                ],
            ),
        ]
    )

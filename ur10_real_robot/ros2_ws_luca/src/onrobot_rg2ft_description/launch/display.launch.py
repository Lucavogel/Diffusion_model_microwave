from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch.substitutions import FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare("onrobot_rg2ft_description")
    default_rviz = PathJoinSubstitution([package_share, "config", "urdf.rviz"])
    default_xacro = PathJoinSubstitution([package_share, "urdf", "onrobot_rg2ft.xacro"])

    gui = LaunchConfiguration("gui")
    rviz_config = LaunchConfiguration("rvizconfig")
    urdf_path = LaunchConfiguration("urdf_path")
    transmission_hw_interface = LaunchConfiguration("transmission_hw_interface")

    robot_description = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            urdf_path,
            " transmission_hw_interface:=",
            transmission_hw_interface,
        ]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("gui", default_value="true"),
            DeclareLaunchArgument("rvizconfig", default_value=default_rviz),
            DeclareLaunchArgument("urdf_path", default_value=default_xacro),
            DeclareLaunchArgument(
                "transmission_hw_interface",
                default_value="hardware_interface/PositionJointInterface",
            ),
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
                condition=IfCondition(gui),
            ),
            Node(
                package="joint_state_publisher",
                executable="joint_state_publisher",
                name="joint_state_publisher",
                condition=UnlessCondition(gui),
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=["-d", rviz_config],
            ),
        ]
    )

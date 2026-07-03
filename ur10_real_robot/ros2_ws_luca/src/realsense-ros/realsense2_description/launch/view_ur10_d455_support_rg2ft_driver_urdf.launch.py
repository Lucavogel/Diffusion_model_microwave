from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    model_file = PathJoinSubstitution(
        [
            FindPackageShare("realsense2_description"),
            "urdf",
            "ur10_d455_support_rg2ft_driver.urdf",
        ]
    )
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("realsense2_description"), "rviz", "urdf.rviz"]
    )

    return LaunchDescription(
        [
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                arguments=[model_file],
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

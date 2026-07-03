from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    model_file = PathJoinSubstitution(
        [FindPackageShare("realsense2_description"), "urdf", "test_ur10_d455_support.urdf.xacro"]
    )
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("ur_robot_description_cb2"), "rviz", "view_robot.rviz"]
    )

    ur_type = LaunchConfiguration("ur_type")
    use_nominal_extrinsics = LaunchConfiguration("use_nominal_extrinsics")

    robot_description = Command(
        [
            "xacro ",
            model_file,
            " ur_type:=",
            ur_type,
            " use_nominal_extrinsics:=",
            use_nominal_extrinsics,
        ]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("ur_type", default_value="ur10"),
            DeclareLaunchArgument("use_nominal_extrinsics", default_value="true"),
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

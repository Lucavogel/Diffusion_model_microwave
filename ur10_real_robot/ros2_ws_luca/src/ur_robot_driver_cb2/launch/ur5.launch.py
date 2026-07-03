from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, ThisLaunchFileDir
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_ip",
            description="IP address by which the robot can be reached.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_fake_hardware",
            default_value="false",
            description="Start robot with fake hardware mirroring command to its states.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "fake_sensor_commands",
            default_value="false",
            description="Enable fake command interfaces for sensors used for simple simulations. \
            Used only if 'use_fake_hardware' parameter is true.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "initial_joint_controller",
            default_value="joint_trajectory_controller",
            description="Initially loaded robot controller.",
            choices=[
                "joint_trajectory_controller",
                "forward_position_controller",
                # "cartesian_motion_controller"
            ],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "activate_joint_controller_on_startup",
            default_value="false",
            description="Activate the selected joint controller during startup.",
        )
    )

    # Initialize Arguments
    robot_ip = LaunchConfiguration("robot_ip")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    fake_sensor_commands = LaunchConfiguration("fake_sensor_commands")
    initial_joint_controller = LaunchConfiguration("initial_joint_controller")
    activate_joint_controller_on_startup = LaunchConfiguration(
        "activate_joint_controller_on_startup"
    )

    base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare("ur_robot_driver_cb2"), "/launch/ur_control.launch.py"]),
        launch_arguments={
            "ur_type": "ur5",
            "robot_ip": robot_ip,
            "use_fake_hardware": use_fake_hardware,
            "fake_sensor_commands": fake_sensor_commands,
            "initial_joint_controller": initial_joint_controller,
            "activate_joint_controller_on_startup": activate_joint_controller_on_startup,
            "launch_rviz": "true",
        }.items(),
    )

    return LaunchDescription(declared_arguments + [base_launch])

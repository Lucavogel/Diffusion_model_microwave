from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Le noeud qui lit le bras haptique Touch
        Node(
            package='touch_ros2_driver',
            executable='touch_node',
            name='touch_node',
            output='screen'
        )
    ])

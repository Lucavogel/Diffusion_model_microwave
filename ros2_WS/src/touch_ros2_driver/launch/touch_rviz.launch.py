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
        ),
        
        # Le noeud qui publie les transformations TF
        Node(
            package='touch_ros2_driver',
            executable='tf_broadcaster_node',
            name='touch_tf_broadcaster',
            output='screen'
        ),
        
        # Le noeud RViz2 avec le frame de base
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', ''], # On ouvrira une configuration vide au départ
            output='screen'
        )
    ])

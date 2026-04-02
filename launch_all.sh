#!/bin/zsh
# Script pour lancer toute la stack Mujoco + Touch 3D + ROS2

# Terminal 1 : Simulation Mujoco (téléop)

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim
python mujoco/teleop/test_UR10e_touch.py
') &

# Terminal 2 : ROS2 + Touch driver + RViz

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ros2_WS
colcon build 
source install/setup.zsh
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim
ros2 launch touch_ros2_driver touch_rviz.launch.py
') &

# Terminal 3 : Node follower (mapping Touch vers cible robot)

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim
python mujoco/tests/test_UR10e_ik_follower.py
') &

wait

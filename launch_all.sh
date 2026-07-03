#!/bin/zsh
# Script pour lancer toute la stack Mujoco + Touch 3D + ROS2

# Terminal 1 : Simulation Mujoco (téléop)

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim
python -m dp_mujoco.teleop.test_UR10e_touch
status=$?
echo ""
echo "[simu] process exited with status $status"
echo "Press Enter to close this terminal..."
read
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
status=$?
echo ""
echo "[ros2] process exited with status $status"
echo "Press Enter to close this terminal..."
read
') &



wait

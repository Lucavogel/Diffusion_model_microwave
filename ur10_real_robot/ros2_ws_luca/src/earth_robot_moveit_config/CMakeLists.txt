cmake_minimum_required(VERSION 3.22)
project(earth_robot_moveit_config)

find_package(ament_cmake REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(onrobot_rg_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(shape_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

option(BUILD_SCENE_WAYPOINT_RUNNER "Build the waypoint runner node" OFF)

if(BUILD_SCENE_WAYPOINT_RUNNER)
  add_executable(scene_waypoint_runner src/scene_waypoint_runner.cpp)
  target_compile_features(scene_waypoint_runner PUBLIC cxx_std_17)
  ament_target_dependencies(
    scene_waypoint_runner
    ament_index_cpp
    geometry_msgs
    moveit_msgs
    moveit_ros_planning_interface
    onrobot_rg_msgs
    rclcpp
    shape_msgs
    tf2
    tf2_geometry_msgs
    tf2_ros
  )
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
  install(
    DIRECTORY launch
    DESTINATION share/${PROJECT_NAME}
    PATTERN "setup_assistant.launch" EXCLUDE)
endif()

install(DIRECTORY config DESTINATION share/${PROJECT_NAME})
install(FILES .setup_assistant DESTINATION share/${PROJECT_NAME})

if(BUILD_SCENE_WAYPOINT_RUNNER)
  install(TARGETS scene_waypoint_runner DESTINATION lib/${PROJECT_NAME})
endif()

ament_package()

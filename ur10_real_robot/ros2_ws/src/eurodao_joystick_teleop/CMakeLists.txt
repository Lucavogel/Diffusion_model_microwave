cmake_minimum_required(VERSION 3.8)
project(eurodao_joystick_teleop)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(onrobot_rg_msgs REQUIRED)

add_executable(joystick_teleop_node
  src/joystick_teleop_node.cpp
  src/joystick_teleop_node_main.cpp
)

target_include_directories(joystick_teleop_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

target_compile_features(joystick_teleop_node PUBLIC cxx_std_17)

ament_target_dependencies(joystick_teleop_node
  rclcpp
  sensor_msgs
  geometry_msgs
  std_msgs
  std_srvs
  trajectory_msgs
  builtin_interfaces
  onrobot_rg_msgs
)

install(DIRECTORY
  config
  launch
  DESTINATION share/${PROJECT_NAME}
)

install(TARGETS
  joystick_teleop_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  include/
  DESTINATION include
)

install(FILES
  package.xml
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

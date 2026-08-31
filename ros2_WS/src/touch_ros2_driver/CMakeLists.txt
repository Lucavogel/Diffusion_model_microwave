cmake_minimum_required(VERSION 3.8)
project(touch_ros2_driver)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ROS 2 dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

set(OPENHAPTICS_ROOT "" CACHE PATH
  "OpenHaptics SDK root containing usr/include and usr/lib")
if(NOT OPENHAPTICS_ROOT AND DEFINED ENV{OPENHAPTICS_ROOT})
  set(OPENHAPTICS_ROOT "$ENV{OPENHAPTICS_ROOT}")
endif()

find_path(OPENHAPTICS_INCLUDE_DIR
  NAMES HD/hd.h
  PATHS
    "${OPENHAPTICS_ROOT}/usr/include"
    "${OPENHAPTICS_ROOT}/include"
  NO_DEFAULT_PATH
)
find_library(OPENHAPTICS_HD_LIBRARY
  NAMES HD
  PATHS "${OPENHAPTICS_ROOT}/usr/lib" "${OPENHAPTICS_ROOT}/lib"
  NO_DEFAULT_PATH
)
find_library(OPENHAPTICS_HL_LIBRARY
  NAMES HL
  PATHS "${OPENHAPTICS_ROOT}/usr/lib" "${OPENHAPTICS_ROOT}/lib"
  NO_DEFAULT_PATH
)
find_library(OPENHAPTICS_HDU_LIBRARY
  NAMES HDU
  PATHS "${OPENHAPTICS_ROOT}/usr/lib" "${OPENHAPTICS_ROOT}/lib"
  NO_DEFAULT_PATH
)

if(NOT OPENHAPTICS_INCLUDE_DIR OR
   NOT OPENHAPTICS_HD_LIBRARY OR
   NOT OPENHAPTICS_HL_LIBRARY OR
   NOT OPENHAPTICS_HDU_LIBRARY)
  message(FATAL_ERROR
    "OpenHaptics 3.4 was not found. Set OPENHAPTICS_ROOT to the SDK "
    "directory containing usr/include/HD/hd.h and usr/lib/libHD.so.")
endif()

add_executable(touch_node src/touch_node.cpp)
ament_target_dependencies(touch_node 
  rclcpp 
  geometry_msgs 
  std_msgs
  tf2
  tf2_ros
)

add_executable(orientation_test_node src/orientation_test.cpp)
ament_target_dependencies(orientation_test_node 
  rclcpp 
  geometry_msgs 
  std_msgs
  tf2
  tf2_ros
)


foreach(touch_target touch_node orientation_test_node)
  target_include_directories(${touch_target} PRIVATE ${OPENHAPTICS_INCLUDE_DIR})
  target_link_libraries(${touch_target}
    ${OPENHAPTICS_HD_LIBRARY}
    ${OPENHAPTICS_HL_LIBRARY}
    ${OPENHAPTICS_HDU_LIBRARY}
    rt
    pthread
  )
endforeach()

install(TARGETS
  touch_node
  orientation_test_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

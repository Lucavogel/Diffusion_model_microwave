cmake_minimum_required(VERSION 3.8)
project(touch_ros2_driver)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. Trouver les dépendances ROS 2
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

include_directories(/home/luca/Master/openhaptics_3.4-0-developer-edition-amd64/usr/include)

# Chemin vers les librairies
link_directories(/home/luca/Master/openhaptics_3.4-0-developer-edition-amd64/usr/lib)

add_executable(touch_node src/touch_node.cpp)
ament_target_dependencies(touch_node 
  rclcpp 
  geometry_msgs 
  std_msgs
  tf2
)









# Lien direct vers les fichiers trouvés dans ton terminal
target_link_libraries(touch_node 
    /home/luca/Master/openhaptics_3.4-0-developer-edition-amd64/usr/lib/libHD.so
  /home/luca/Master/openhaptics_3.4-0-developer-edition-amd64/usr/lib/libHL.so
    /home/luca/Master/openhaptics_3.4-0-developer-edition-amd64/usr/lib/libHDU.a
    rt 
    pthread
)

# 5. INSTALLATION
# Pour que la commande "ros2 run" puisse trouver ton programme
install(TARGETS
  touch_node

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
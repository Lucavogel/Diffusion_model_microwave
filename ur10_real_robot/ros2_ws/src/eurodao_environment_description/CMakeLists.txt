cmake_minimum_required(VERSION 3.8)
project(eurodao_environment_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    meshes
  DESTINATION share/${PROJECT_NAME}
)

install(FILES README.md scene_final_1.scene DESTINATION share/${PROJECT_NAME})

ament_package()

cmake_minimum_required(VERSION 3.8)
project(artemis_assets)

find_package(ament_cmake REQUIRED)

install(DIRECTORY models
  DESTINATION share/${PROJECT_NAME}
)

# Add the models directory to GZ_SIM_RESOURCE_PATH so model:// URIs resolve.
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")

ament_package()

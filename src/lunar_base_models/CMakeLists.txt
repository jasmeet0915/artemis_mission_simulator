cmake_minimum_required(VERSION 3.8)
project(lunar_base_models)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  models
  DESTINATION share/${PROJECT_NAME}
)

# Environment hook for GZ_SIM_RESOURCE_PATH
ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/hooks/environment/lunar_base_models.dsv.in"
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

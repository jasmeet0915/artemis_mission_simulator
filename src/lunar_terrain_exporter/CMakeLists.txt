cmake_minimum_required(VERSION 3.8)
project(lunar_terrain_exporter)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Install the Python package
ament_python_install_package(${PROJECT_NAME})

# Install the console-script entry point
install(PROGRAMS
  scripts/lunar_terrain_exporter
  DESTINATION bin
)

install(DIRECTORY models config
  DESTINATION share/${PROJECT_NAME}
)

# Env hooks
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_site_catalog test/test_site_catalog.py)
  ament_add_pytest_test(test_site_config test/test_site_config.py)
  ament_add_pytest_test(test_cli test/test_cli.py)
  ament_add_pytest_test(test_integration test/test_integration.py)
  ament_add_pytest_test(test_heightmap test/test_heightmap.py)
  ament_add_pytest_test(test_terrain_processing test/test_terrain_processing.py)
endif()

ament_package()

cmake_minimum_required(VERSION 3.8)
project(artemis_mission_launcher)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Python package holding the artemis CLI logic.
ament_python_install_package(artemis_cli)

# Bare `artemis` command: ament prepends <install-prefix>/bin to PATH.
install(PROGRAMS
  bin/artemis
  DESTINATION bin
)

install(DIRECTORY
  launch
  worlds
  config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_epoch test/test_epoch.py)
  ament_add_pytest_test(test_home_dashboard test/test_home_dashboard.py)
  ament_add_pytest_test(test_home_metrics test/test_home_metrics.py)
  ament_add_pytest_test(test_lunar_world_gz_args test/test_lunar_world_gz_args.py)
endif()

ament_package()

cmake_minimum_required(VERSION 3.8)
project(lunar_terrain_exporter)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Install the Python package
ament_python_install_package(${PROJECT_NAME})

# Install the console-script entry point
install(PROGRAMS
  bin/lunar_terrain_exporter
  DESTINATION bin
)

install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_cli test/test_cli.py)
  ament_add_pytest_test(test_downloader test/test_downloader.py)
  ament_add_pytest_test(test_dem_processor test/test_dem_processor.py)
  ament_add_pytest_test(test_raster_utils test/test_raster_utils.py)
  ament_add_pytest_test(test_site_catalog test/test_site_catalog.py)
  ament_add_pytest_test(test_types test/test_types.py)
  ament_add_pytest_test(test_integration test/test_integration.py)
  ament_add_pytest_test(test_sdf_model_writer test/test_sdf_model_writer.py)
endif()

ament_package()

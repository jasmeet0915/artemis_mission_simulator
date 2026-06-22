cmake_minimum_required(VERSION 3.8)
project(artemis_mission_manager)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(artemis_mission_interfaces REQUIRED)
find_package(yaml-cpp REQUIRED)

add_library(site_metadata_reader src/site_metadata_reader.cpp)
target_include_directories(site_metadata_reader PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(site_metadata_reader ament_index_cpp artemis_mission_interfaces)
target_link_libraries(site_metadata_reader yaml-cpp)

add_executable(mission_manager src/mission_manager_node.cpp)
target_link_libraries(mission_manager site_metadata_reader)
ament_target_dependencies(mission_manager rclcpp artemis_mission_interfaces)

install(TARGETS mission_manager
  DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY include/
  DESTINATION include)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_site_metadata_reader test/test_site_metadata_reader.cpp)
  target_link_libraries(test_site_metadata_reader site_metadata_reader)
  ament_target_dependencies(test_site_metadata_reader artemis_mission_interfaces)

  find_package(launch_testing_ament_cmake REQUIRED)
  add_launch_test(test/test_site_metadata_publisher_launch.py)

  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

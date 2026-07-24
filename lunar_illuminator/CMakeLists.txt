cmake_minimum_required(VERSION 3.8)
project(lunar_illuminator)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(artemis_mission_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(gz-transport13 REQUIRED)
find_package(gz-msgs10 REQUIRED)

# --- simulator-agnostic core -------------------------------------------------
# Deliberately links nothing from Gazebo or ROS: a gz/rclcpp type leaking in
# here fails to link, which is what keeps the package portable.
add_library(sun_direction src/sun_direction.cpp)
target_include_directories(sun_direction PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)

# --- Gazebo-specific layer ---------------------------------------------------
add_library(gz_illuminator
  src/gazebo/gz_light_publisher.cpp
  src/gazebo/gz_illuminator_node.cpp)
target_include_directories(gz_illuminator PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_link_libraries(gz_illuminator
  sun_direction
  gz-transport13::core
  gz-msgs10::core)
ament_target_dependencies(gz_illuminator rclcpp artemis_mission_interfaces geometry_msgs)

add_executable(gz_illuminator_node src/gazebo/gz_illuminator_main.cpp)
target_link_libraries(gz_illuminator_node gz_illuminator)
ament_target_dependencies(gz_illuminator_node rclcpp)

install(TARGETS gz_illuminator_node
  DESTINATION lib/${PROJECT_NAME})
install(TARGETS sun_direction gz_illuminator
  DESTINATION lib)
install(DIRECTORY include/
  DESTINATION include)
install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_gtest REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()

  ament_add_gtest(test_sun_direction test/test_sun_direction.cpp)
  target_link_libraries(test_sun_direction sun_direction)

  ament_add_gtest(test_gz_light_publisher test/test_gz_light_publisher.cpp)
  target_link_libraries(test_gz_light_publisher gz_illuminator)
endif()

ament_package()

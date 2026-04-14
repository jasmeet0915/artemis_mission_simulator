"""
Launch Gazebo with a specified world file.

Usage:
    ros2 launch artemis_mission_launcher lunar_world.launch.py
    ros2 launch artemis_mission_launcher lunar_world.launch.py world:=lunar_surface.sdf
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    artemis_mission_launcher_pkg = get_package_share_directory("artemis_mission_launcher")
    pkg_worlds_dir = os.path.join(artemis_mission_launcher_pkg, "worlds")

    declare_world_name_arg = DeclareLaunchArgument(
        "world",
        default_value="lunar_empty_world.sdf",
        description="Name of the world to open",
    )

    world_name = LaunchConfiguration("world")
    world_file = PathJoinSubstitution([pkg_worlds_dir, world_name])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                get_package_share_directory("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py",
            ])
        ),
        launch_arguments={"gz_args": ["-v 4 -r ", world_file]}.items(),
    )

    return LaunchDescription([
        declare_world_name_arg,
        gz_sim,
    ])

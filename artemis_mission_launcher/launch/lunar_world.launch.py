# Copyright 2026 Jasmeet Singh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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
    gui_config = os.path.join(
        artemis_mission_launcher_pkg, "config", "gz", "gui.config",
    )

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
        launch_arguments={
            "gz_args": ["-v 4 -r --gui-config ", gui_config, " ", world_file],
        }.items(),
    )

    return LaunchDescription([
        declare_world_name_arg,
        gz_sim,
    ])

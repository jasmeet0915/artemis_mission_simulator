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
Launch Gazebo with a specified world file and an optional mission epoch.

Usage:
    ros2 launch artemis_mission_launcher lunar_world.launch.py
    ros2 launch artemis_mission_launcher lunar_world.launch.py world:=lunar_surface.sdf
    ros2 launch artemis_mission_launcher lunar_world.launch.py initial_sim_time:=1782216000
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def build_gz_args(gui_config, world_file, initial_sim_time):
    """Assemble the gz_args string, seeding sim time only when provided."""
    args = f'-v 4 -r --gui-config {gui_config} '
    if initial_sim_time:
        args += f'--initial-sim-time {initial_sim_time} '
    args += world_file
    return args


def launch_setup(context, *args, **kwargs):
    pkg = get_package_share_directory('artemis_mission_launcher')
    gui_config = os.path.join(pkg, 'config', 'gz', 'gui.config')

    world_name = LaunchConfiguration('world').perform(context)
    initial_sim_time = LaunchConfiguration('initial_sim_time').perform(context)
    world_file = os.path.join(pkg, 'worlds', world_name)

    gz_args = build_gz_args(gui_config, world_file, initial_sim_time)

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            )
        ),
        launch_arguments={'gz_args': gz_args}.items(),
    )
    return [gz_sim]


def generate_launch_description():
    declare_world_name_arg = DeclareLaunchArgument(
        'world',
        default_value='lunar_empty_world.sdf',
        description='Name of the world to open',
    )

    declare_initial_sim_time_arg = DeclareLaunchArgument(
        'initial_sim_time',
        default_value='',
        description='Initial Gazebo sim time in Unix seconds (UTC). '
                    'Empty leaves the gz default.',
    )

    return LaunchDescription([
        declare_world_name_arg,
        declare_initial_sim_time_arg,
        OpaqueFunction(function=launch_setup),
    ])

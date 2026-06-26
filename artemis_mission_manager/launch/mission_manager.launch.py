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
Launch the mission manager node for orchestration of mission activities.

Usage:
    ros2 launch artemis_mission_manager mission_manager.launch.py
    ros2 launch artemis_mission_manager mission_manager.launch.py site:=shackleton_rim
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    declare_site_arg = DeclareLaunchArgument(
        'site',
        default_value='',
        description='Mission site name; used for retrieving site metadata',
    )

    # Mission manager node
    mission_manager_node = Node(
        package='artemis_mission_manager',
        executable='mission_manager',
        name='mission_manager',
        parameters=[{
            'site': LaunchConfiguration('site'),
        }]
    )

    return LaunchDescription([
        declare_site_arg,
        mission_manager_node
    ])

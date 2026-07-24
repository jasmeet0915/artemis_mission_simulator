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
Launch the lunar illuminator, which drives Gazebo's sun light from the sky tracker.

Usage:
    ros2 launch lunar_illuminator lunar_illuminator.launch.py use_sim_time:=true
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    lunar_illuminator_pkg = get_package_share_directory('lunar_illuminator')
    lunar_illuminator_config = os.path.join(
        lunar_illuminator_pkg, 'config', 'lunar_illuminator_config.yaml')

    declare_use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true',
    )

    # Illuminator node
    illuminator_node = Node(
        package='lunar_illuminator',
        executable='gz_illuminator_node',
        name='lunar_illuminator',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            lunar_illuminator_config
        ],
    )

    return LaunchDescription([
        declare_use_sim_time_arg,
        illuminator_node
    ])

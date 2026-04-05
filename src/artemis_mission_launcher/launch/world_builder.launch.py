"""
Launch Gazebo in world-builder sandbox mode with the Resource Spawner GUI.

Users can browse and place terrain models interactively.

Usage:
    ros2 launch artemis_mission_launcher world_builder.launch.py
"""

import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, LogInfo, OpaqueFunction
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    launcher_share = FindPackageShare("artemis_mission_launcher").perform(context)
    terrain_share = FindPackageShare("generate_lunar_sdf").perform(context)

    world_file = os.path.join(launcher_share, "worlds", "lunar_surface.world")
    gui_config = os.path.join(launcher_share, "config", "gui.config")
    model_path = os.path.join(terrain_share, "models")

    gz_sim = ExecuteProcess(
        cmd=[
            "gz", "sim", "-r",
            world_file,
            "--gui-config", gui_config,
        ],
        additional_env={"GZ_SIM_RESOURCE_PATH": model_path},
        output="screen",
    )

    return [
        LogInfo(msg="Launching Gazebo in world-builder mode with Resource Spawner"),
        gz_sim,
    ]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup),
    ])

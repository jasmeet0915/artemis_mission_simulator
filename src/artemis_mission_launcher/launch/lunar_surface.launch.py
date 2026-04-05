"""
Launch Gazebo with a pre-loaded lunar terrain model.

Usage:
    ros2 launch artemis_mission_launcher lunar_surface.launch.py
    ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=shackleton_rim
"""

import atexit
import os
import tempfile

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    site = LaunchConfiguration("site").perform(context)
    launcher_share = FindPackageShare("artemis_mission_launcher").perform(context)
    terrain_share = FindPackageShare("generate_lunar_sdf").perform(context)

    world_file = os.path.join(launcher_share, "worlds", "lunar_surface.world")
    model_path = os.path.join(terrain_share, "models")

    site_model_dir = os.path.join(model_path, site)
    if not os.path.isdir(site_model_dir):
        available = [
            d for d in os.listdir(model_path)
            if os.path.isdir(os.path.join(model_path, d))
        ]
        raise RuntimeError(
            f"Site '{site}' not found in {model_path}. "
            f"Available sites: {', '.join(sorted(available))}"
        )

    with open(world_file, "r") as f:
        world_content = f.read()

    include_sdf = (
        f'    <include>\n'
        f'      <uri>model://{site}</uri>\n'
        f'      <pose>0 0 0 0 0 0</pose>\n'
        f'    </include>\n'
    )
    modified_world = world_content.replace("</world>", include_sdf + "  </world>")

    tmp_path = os.path.join(tempfile.gettempdir(), f"lunar_{site}.world")
    with open(tmp_path, "w") as f:
        f.write(modified_world)
    atexit.register(lambda p=tmp_path: os.remove(p) if os.path.exists(p) else None)

    gz_sim = ExecuteProcess(
        cmd=["gz", "sim", "-r", tmp_path],
        additional_env={"GZ_SIM_RESOURCE_PATH": model_path},
        output="screen",
    )

    return [
        LogInfo(msg=f"Loading lunar terrain: {site}"),
        gz_sim,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "site",
            default_value="connecting_ridge",
            description="Lunar site to load (e.g., connecting_ridge, shackleton_rim)",
        ),
        OpaqueFunction(function=launch_setup),
    ])

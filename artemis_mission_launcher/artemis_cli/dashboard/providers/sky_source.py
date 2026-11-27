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
"""Live Sun az/el read off the lunar_sky_tracker topic."""
from __future__ import annotations

import threading
from typing import Optional, Tuple

SUN_TOPIC = '/lunar_sky_tracker/sun'


class SkySource:
    """
    Background subscription exposing the most recent Sun angles.

    ROS is imported lazily inside :meth:`start` so the dashboard still runs
    where no ROS installation exists at all.
    """

    def __init__(self, topic: str = SUN_TOPIC) -> None:
        self._topic = topic
        self._latest: Optional[Tuple[float, float]] = None
        self._node = None
        self._executor = None
        self._thread = None
        self._owns_context = False

    @property
    def latest(self) -> Optional[Tuple[float, float]]:
        """Return the newest (azimuth_deg, elevation_deg), or None."""
        return self._latest

    def start(self) -> bool:
        """Spin a subscriber on a daemon thread; report success, never raise."""
        try:
            import rclpy
            from rclpy.executors import SingleThreadedExecutor
            from rclpy.signals import SignalHandlerOptions

            from artemis_mission_interfaces.msg import SkyObject

            if not rclpy.ok():
                # Leave signals to the dashboard. rclpy's own SIGINT/SIGTERM
                # handlers only shut the context down, so the render loop would
                # sleep on none the wiser and the process would ignore a kill.
                rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
                self._owns_context = True
            self._node = rclpy.create_node('artemis_dashboard_sky')
            # Depth 10 volatile, matching the tracker's publisher.
            self._node.create_subscription(
                SkyObject, self._topic, self._on_sky_object, 10)
            self._executor = SingleThreadedExecutor()
            self._executor.add_node(self._node)
            self._thread = threading.Thread(
                target=self._executor.spin, daemon=True)
            self._thread.start()
            return True
        except Exception:
            # A dashboard has to render even with no ROS graph; a missing sun
            # row is a far better outcome than a dead mission-control screen.
            self._teardown()
            return False

    def stop(self) -> None:
        """Tear the subscriber down. Safe to call before start or twice."""
        self._teardown()

    def _on_sky_object(self, msg) -> None:
        # One tuple rebind: atomic under the GIL, so the render thread never
        # sees a half-updated pair and no lock is needed.
        self._latest = (msg.azimuth_deg, msg.elevation_deg)

    def _teardown(self) -> None:
        if self._executor is not None:
            try:
                self._executor.shutdown()
            except Exception:
                pass
            self._executor = None
        # Join before destroying the node: tearing the node out from under a
        # thread still inside spin() aborts the process on the way out.
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._node is not None:
            try:
                self._node.destroy_node()
            except Exception:
                pass
            self._node = None
        if self._owns_context:
            try:
                import rclpy
                rclpy.shutdown()
            except Exception:
                pass
            self._owns_context = False
        self._thread = None

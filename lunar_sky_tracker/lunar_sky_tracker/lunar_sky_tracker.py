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

"""Sky tracker for lunar locations."""

from pathlib import Path

from artemis_mission_interfaces.msg import SiteMetadata, SkyObject
from lunar_sky_tracker.spice.celestial_ephemeris import get_solar_system_body_position
from lunar_sky_tracker.spice.kernel_manager import KernelManager
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
from spiceypy.utils.exceptions import SpiceyError

# SPICE bodies to track
SUN = 'sun'


class LunarSkyTracker(Node):
    """Publishes the Sun's azimuth/elevation over the mission site's horizon."""

    def __init__(self):
        super().__init__('lunar_sky_tracker')

        self.site_id: str = None
        self.site_display_name: str = None
        self.origin_latitude: float = None
        self.origin_longitude: float = None
        self._tracking_timer = None

        self.declare_parameter('site_metadata_topic', '/mission/site_metadata')
        self.site_metadata_topic: str = self.get_parameter(
            'site_metadata_topic').value

        self.declare_parameter('sun_topic', '/lunar_sky_tracker/sun')
        self.sun_topic: str = self.get_parameter('sun_topic').value

        self.declare_parameter('observer_frame', 'site_origin')
        self.observer_frame: str = self.get_parameter('observer_frame').value

        # The Sun drifts ~1.5e-4 deg/s, so 1 Hz already oversamples its motion.
        self.declare_parameter('update_rate', 1.0)
        self.update_rate: float = self.get_parameter('update_rate').value

        self.declare_parameter('kernel_dir', '/opt/spice_kernels')
        self.kernel_dir: str = self.get_parameter('kernel_dir').value

        # Furnish required kernels using KernelManager
        self.kernel_manager = KernelManager(Path(self.kernel_dir))
        self.kernel_manager.furnish()

        # Publishers
        self.sun_publisher = self.create_publisher(
            SkyObject, self.sun_topic, 10)

        qos = QoSProfile(depth=10, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.site_metadata_subscriber = self.create_subscription(
            SiteMetadata,
            self.site_metadata_topic,
            self.site_metadata_callback,
            qos
        )

        self.get_logger().info('Lunar Sky Tracker node has been initialized.')

    def site_metadata_callback(self, msg: SiteMetadata):
        """Store the site origin and start tracking once metadata is known."""
        self.get_logger().info(f'Received site metadata for: {msg.display_name}')
        self.site_id = msg.site_id
        self.site_display_name = msg.display_name
        self.origin_latitude = msg.origin_latitude
        self.origin_longitude = msg.origin_longitude

        # Start tracking timer once site metadata is received
        if self._tracking_timer is None:
            self._tracking_timer = self.create_timer(
                1.0 / self.update_rate, self.track_sky_objects)
            self.get_logger().info(
                f'Tracking the sun at {self.update_rate} Hz, '
                f'publishing on {self.sun_topic}.')

    def track_sky_objects(self):
        """Compute and publish the tracked sky objects for the site."""
        # Only the Sun is tracked today; more bodies get added here.
        now = self.get_clock().now()

        try:
            position = get_solar_system_body_position(
                SUN,
                now.nanoseconds * 1e-9,
                self.origin_latitude,
                self.origin_longitude,
            )
        except (SpiceyError, ValueError) as exc:
            # Keep the timer alive: a transient bad epoch must not stop tracking.
            self.get_logger().error(
                f'Could not compute the sun position: {exc}',
                throttle_duration_sec=10.0)
            return

        msg = SkyObject()
        # Stamp with the same instant the angles were computed for.
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = self.observer_frame
        msg.name = position.name
        msg.direction_enu.x = float(position.direction_enu[0])
        msg.direction_enu.y = float(position.direction_enu[1])
        msg.direction_enu.z = float(position.direction_enu[2])
        msg.azimuth_deg = position.azimuth_deg
        msg.elevation_deg = position.elevation_deg

        self.sun_publisher.publish(msg)

    def destroy_node(self):
        """Release the furnished kernels before the node goes away."""
        self.kernel_manager.unload()
        return super().destroy_node()

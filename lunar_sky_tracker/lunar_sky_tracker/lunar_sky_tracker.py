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

"""Sky tracker for lunar locations"""

from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy

from artemis_mission_intefaces.msg import SiteMetadata


class LunarSkyTracker(Node):

    def __init__(self):
        super().__init__('lunar_sky_tracker')

        self.site_id: str = None
        self.site_display_name: str = None
        self.origin_latitude: float = None
        self.origin_longitude: float = None

        self.declare_parameter('site_metadata_topic', '/mission/site_metadata')
        self.site_metadata_topic: str = self.get_parameter('site_metadata_topic').value

        self.declare_parameter('update_rate', 20.0)
        self.update_rate: float = self.get_parameter('update_rate').value

        qos = QoSProfile(depth=10, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.site_metadata_subscriber = self.create_subscription(
            SiteMetadata,
            self.site_metadata_topic,
            self.site_metadata_callback,
            qos
        )

        self.get_logger().info('Lunar Sky Tracker node has been initialized.')


    def site_metadata_callback(self, msg: SiteMetadata):
        self.get_logger().info(f'Received site metadata for: {msg.display_name}')
        self.site_id = msg.site_id
        self.site_name = msg.site_display_name
        self.origin_latitude = msg.origin_latitude
        self.origin_longitude = msg.origin_longitude

    def start_tracking(self):
        if self.site_id is None:
            self.get_logger().warn('Site metadata not received yet. Cannot start tracking.')
            return

        # Compute the sun position w.r.t the site origin and current time

        # Publish the computed sun position to a topic for other nodes to use

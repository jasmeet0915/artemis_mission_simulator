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

import time
import unittest

from artemis_mission_interfaces.msg import SiteMetadata
import launch
import launch_ros.actions
import launch_testing.actions
import pytest
import rclpy
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)


@pytest.mark.launch_test
def generate_test_description():
    mission_manager = launch_ros.actions.Node(
        package='artemis_mission_manager',
        executable='mission_manager',
        parameters=[{'site': 'shackleton_rim'}],
    )
    return (
        launch.LaunchDescription([
            mission_manager,
            launch_testing.actions.ReadyToTest(),
        ]),
        {},
    )


class TestLatchedSiteMetadata(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def test_late_joiner_receives_latched_site(self):
        node = rclpy.create_node('site_metadata_test_subscriber')
        received = []
        qos = QoSProfile(
            depth=1,
            history=QoSHistoryPolicy.KEEP_LAST,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        node.create_subscription(
            SiteMetadata, '/mission/site_metadata', lambda m: received.append(m), qos)

        deadline = time.time() + 10.0
        while time.time() < deadline and not received:
            rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()

        self.assertTrue(received, 'no latched SiteMetadata received within 10s')
        msg = received[0]
        self.assertEqual(msg.site_id, 'shackleton_rim')
        self.assertEqual(msg.display_name, 'Shackleton Rim')
        self.assertAlmostEqual(msg.origin_latitude, -89.76681145214992, places=4)
        self.assertEqual(msg.source, 'nasa_pgda_78')

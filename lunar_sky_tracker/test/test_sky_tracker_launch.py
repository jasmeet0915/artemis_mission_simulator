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

"""End-to-end launch test for the lunar_sky_tracker node."""

import math
import unittest

from ament_index_python.packages import get_package_share_directory
from artemis_mission_interfaces.msg import SiteMetadata, SkyObject
import launch
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from rclpy.qos import QoSDurabilityPolicy, QoSProfile

SUN_TOPIC = '/lunar_sky_tracker/sun'
METADATA_TOPIC = '/mission/site_metadata'
OBSERVER_FRAME = 'site_origin'
SITE_LAT = -89.9
SITE_LON = 12.5


@pytest.mark.launch_test
def generate_test_description():
    """Launch the node via its packaged launch file, on wall-clock time."""
    launch_under_test = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            get_package_share_directory('lunar_sky_tracker')
            + '/launch/lunar_sky_tracker.launch.py'),
        launch_arguments={'use_sim_time': 'false'}.items(),
    )

    return (
        launch.LaunchDescription([
            launch_under_test,
            launch_testing.actions.ReadyToTest(),
        ]),
        {},
    )


def _transient_local(depth=10):
    """Build QoS matching the node's TRANSIENT_LOCAL metadata subscription."""
    return QoSProfile(
        depth=depth, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)


class TestSkyTrackerLive(unittest.TestCase):
    """
    Active tests: run while the node process is up.

    The launched node persists across both methods, and once it receives site
    metadata it tracks forever. So the methods are numbered to force order --
    the silence check must run *before* any metadata is published.
    """

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        self.node = rclpy.create_node('sky_tracker_test_peer')

    def tearDown(self):
        self.node.destroy_node()

    def _spin_until(self, predicate, timeout_sec):
        """Spin the test node until predicate() is true or the timeout lapses."""
        end = self.node.get_clock().now().nanoseconds + timeout_sec * 1e9
        while self.node.get_clock().now().nanoseconds < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if predicate():
                return True
        return predicate()

    def test_no_publish_until_metadata_arrives(self):
        received = []
        self.node.create_subscription(
            SkyObject, SUN_TOPIC, received.append, 10)

        # No metadata yet: the node must publish nothing. Give it time, then
        # confirm silence. Runs before test_2 so no metadata has been sent.
        self._spin_until(lambda: len(received) > 0, timeout_sec=3.0)
        self.assertEqual(received, [], 'Published a SkyObject with no site set.')

    def test_publishes_a_sun_skyobject_after_metadata(self):
        received = []
        self.node.create_subscription(
            SkyObject, SUN_TOPIC, received.append, 10)

        # TRANSIENT_LOCAL so the already-running node still receives this.
        metadata_pub = self.node.create_publisher(
            SiteMetadata, METADATA_TOPIC, _transient_local())
        metadata = SiteMetadata()
        metadata.site_id = 'shackleton_rim'
        metadata.display_name = 'Shackleton Rim'
        metadata.origin_latitude = SITE_LAT
        metadata.origin_longitude = SITE_LON
        metadata_pub.publish(metadata)

        got = self._spin_until(lambda: len(received) > 0, timeout_sec=20.0)
        self.assertTrue(got, 'No SkyObject was published within 20 s.')

        msg = received[0]
        self.assertEqual(msg.name, 'sun')
        self.assertEqual(msg.header.frame_id, OBSERVER_FRAME)

        # The stamp must identify the instant the angles describe, not be zero.
        self.assertGreater(msg.header.stamp.sec, 0)

        self.assertGreaterEqual(msg.azimuth_deg, 0.0)
        self.assertLess(msg.azimuth_deg, 360.0)
        self.assertGreaterEqual(msg.elevation_deg, -90.0)
        self.assertLessEqual(msg.elevation_deg, 90.0)

        # direction_enu is the same direction as the angles, and unit length.
        d = msg.direction_enu
        self.assertAlmostEqual(
            math.sqrt(d.x * d.x + d.y * d.y + d.z * d.z), 1.0, places=9)
        az, el = math.radians(msg.azimuth_deg), math.radians(msg.elevation_deg)
        self.assertAlmostEqual(d.x, math.cos(el) * math.sin(az), places=6)
        self.assertAlmostEqual(d.y, math.cos(el) * math.cos(az), places=6)
        self.assertAlmostEqual(d.z, math.sin(el), places=6)


@launch_testing.post_shutdown_test()
class TestCleanShutdown(unittest.TestCase):
    """Post-shutdown tests: run after the node process has exited."""

    def test_node_exited_cleanly(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)

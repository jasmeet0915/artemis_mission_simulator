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
"""Launch the Artemis mission stacks inside a dedicated tmux session."""
import os
import time

import libtmux

SESSION_NAME = 'artemis'


class MissionAlreadyRunning(RuntimeError):
    """Raised when the artemis tmux session already exists."""


def default_workspace_setup():
    """
    Return a best-effort path to the workspace's install/setup.bash.

    Overridable via ARTEMIS_WS_SETUP; otherwise derived from the first
    entry of COLCON_PREFIX_PATH. Returns None when it cannot be found,
    in which case the in-pane source step is skipped.
    """
    override = os.environ.get('ARTEMIS_WS_SETUP')
    if override:
        return override
    prefix_path = os.environ.get('COLCON_PREFIX_PATH', '')
    for prefix in prefix_path.split(os.pathsep):
        if prefix:
            candidate = os.path.join(prefix, 'setup.bash')
            if os.path.exists(candidate):
                return candidate
    return None


class StackLauncher:
    """Create the tmux session and launch each mission stack in a pane."""

    def __init__(self, epoch_sec, site, session_name=SESSION_NAME,
                 workspace_setup=None):
        self.epoch_sec = epoch_sec
        self.site = site
        self.session_name = session_name
        self.workspace_setup = (
            workspace_setup if workspace_setup is not None
            else default_workspace_setup()
        )
        self.close_time = 5

        self.server = libtmux.Server()
        if self.server.has_session(self.session_name):
            raise MissionAlreadyRunning(
                'a mission is already in progress (tmux session '
                f"'{self.session_name}'). Kill it with: "
                f'tmux kill-session -t {self.session_name}'
            )

        self.session = self.server.new_session(self.session_name, attach=False)
        self.mission_window = self.session.windows[0]
        self.mission_window.rename_window('mission-control')
        self.simulation_window = self.session.new_window(
            window_name='simulation', attach=False)
        self.mission_manager_window = self.session.new_window(
            window_name='mission_manager', attach=False)
        self.sky_tracker_window = self.session.new_window(
            window_name='sky_tracker', attach=False)
        self.mission_window.select()  # land here on attach
        print(f"[artemis] created tmux session '{self.session_name}'")

    def _source_workspace(self, pane):
        if self.workspace_setup:
            pane.send_keys(f'source {self.workspace_setup}', enter=True)

    def launch_home(self):
        print('[artemis] booting mission control...')
        pane = self.mission_window.panes[0]
        self._source_workspace(pane)
        pane.send_keys(
            'python3 -m artemis_cli.dashboard '
            f'--site {self.site} --epoch-sec {self.epoch_sec}',
            enter=True,
        )

    def launch_simulation(self):
        print('[artemis] launching simulation stack...')
        pane = self.simulation_window.panes[0]
        self._source_workspace(pane)
        pane.send_keys(
            'ros2 launch artemis_mission_launcher lunar_world.launch.py '
            f'site:={self.site} initial_sim_time:={self.epoch_sec}',
            enter=True,
        )

    def launch_mission_manager(self):
        print('[artemis] launching mission manager stack...')
        pane = self.mission_manager_window.panes[0]
        self._source_workspace(pane)
        pane.send_keys(
            'ros2 launch artemis_mission_manager mission_manager.launch.py '
            f'site:={self.site} use_sim_time:=true',
            enter=True,
        )

    def launch_sky_tracker(self):
        print('[artemis] launching sky tracker stack...')
        pane = self.sky_tracker_window.panes[0]
        self._source_workspace(pane)
        # No site argument: the tracker picks the site up from the mission
        # manager's site metadata topic.
        pane.send_keys(
            'ros2 launch lunar_sky_tracker lunar_sky_tracker.launch.py '
            'use_sim_time:=true',
            enter=True,
        )

    def attach(self):
        os.execvp('tmux', ['tmux', 'attach-session', '-t', self.session_name])

    def smooth_shutdown(self):
        if not self.server.has_session(self.session_name):
            print('[artemis] tmux session already terminated.')
            return
        print('[artemis] shutting down mission...')
        for window in self.session.windows:
            for pane in window.panes:
                pane.send_keys('C-c')
        time.sleep(self.close_time)
        self.session.kill()
        print('[artemis] tmux session terminated cleanly.')

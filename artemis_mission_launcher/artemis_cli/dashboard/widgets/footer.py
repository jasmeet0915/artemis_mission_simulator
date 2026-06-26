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
"""Footer widget: one centred framework status line."""
from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from .. import theme
from ..state import DashboardState


class FooterPanel(Static):
    """Single centred line naming the framework and the press-to-exit hint."""

    def update_state(self, state: DashboardState) -> None:
        line = Text(justify='center')
        line.append('ARTEMIS DIGITAL TWIN FRAMEWORK', style=f'bold {theme.PRIMARY}')
        line.append('    ·    ', style=theme.FAINT)
        line.append('ROS 2 | Gazebo | SPICE | Lunar Robotics', style=theme.MUTED)
        line.append('    ·    ', style=theme.FAINT)
        line.append('press q to exit', style=theme.FAINT)
        self.update(line)

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
"""Footer widget: one centred status line."""
from __future__ import annotations

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from .. import theme
from ..state import DashboardState


def render(state: DashboardState) -> RenderableType:
    framework = Text.assemble(
        ('ARTEMIS DIGITAL TWIN FRAMEWORK', f'bold {theme.PRIMARY}'),
        ('    ·    ', theme.FAINT),
        ('ROS 2 | Gazebo | SPICE | Lunar Robotics', theme.MUTED))
    grid = Table.grid(expand=True)
    grid.style = theme.ON_BG
    grid.add_column(justify='left', ratio=1)
    grid.add_column(justify='center')
    grid.add_column(justify='right', ratio=1)
    grid.add_row('', framework, Text('Press Ctrl+C to exit', style=theme.FAINT))
    return grid

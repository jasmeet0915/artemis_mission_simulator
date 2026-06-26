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
"""Header widgets: ARTEMIS wordmark, Welcome card, and UTC/uptime/host box."""
from __future__ import annotations

from rich.align import Align
from rich.console import Group
from rich.table import Table
from rich.text import Text
from textual.widgets import Static

from .. import theme
from ..state import DashboardState
from .glyphs import big_text


class WordmarkPanel(Static):
    """ARTEMIS block-font wordmark with a small subtitle."""

    def update_state(self, state: DashboardState) -> None:
        self.update(Group(
            big_text('ARTEMIS', style=f'bold {theme.ACCENT}'),
            Text('MISSION LAUNCHER      v1.0.0', style=theme.MUTED),
        ))


class WelcomeCard(Static):
    """Centre greeting in its own bordered card; 'nominal' shown in green."""

    @staticmethod
    def render_text() -> Text:
        text = Text(justify='center')
        text.append('Welcome, Commander', style=f'bold {theme.ACCENT}')
        text.append('\n')
        text.append('All systems ', style=theme.MUTED)
        text.append('nominal', style=f'bold {theme.OK}')
        text.append('.', style=theme.MUTED)
        return text

    def update_state(self, state: DashboardState) -> None:
        self.update(Align.center(self.render_text(), vertical='middle'))


class StatusPanel(Static):
    """Top-right box: UTC time, uptime and host."""

    def update_state(self, state: DashboardState) -> None:
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style=theme.MUTED, justify='left')
        grid.add_column(style=theme.PRIMARY, justify='left')
        grid.add_row('◷ UTC TIME', Text(state.utc_time, style=theme.ACCENT))
        grid.add_row('⊙ UPTIME', Text(state.uptime, style=theme.PRIMARY))
        grid.add_row('◆ HOST', Text(state.hostname, style=theme.OK))
        self.update(grid)

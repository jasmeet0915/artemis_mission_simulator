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
"""Textual application hosting the Artemis mission-control dashboard."""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical

from . import theme
from .providers import Provider
from .state import DashboardState
from .widgets.footer import FooterPanel
from .widgets.header import StatusPanel, WelcomeCard, WordmarkPanel
from .widgets.mission_clock import MissionClockPanel
from .widgets.mission_overview import MissionOverviewPanel
from .widgets.system_monitor import SystemMonitorPanel

_CSS = f"""
Screen {{
    background: {theme.BG};
    color: {theme.PRIMARY};
}}
/* flexible spacers vertically centre the fixed-height content block */
#top-spacer, #bottom-spacer {{ height: 1fr; }}
#header {{ height: 8; }}
#main {{ height: 15; }}
#monitor {{ height: 14; }}
#footer {{ height: 1; color: {theme.FAINT}; }}

/* three equal columns keep the Welcome card centred on screen */
#wordmark {{ width: 1fr; padding: 0 1; }}
#welcome {{ width: 1fr; }}
#status-wrap {{ width: 1fr; align-horizontal: right; }}
#status {{ width: 34; }}

#overview {{ width: 3fr; }}
#clock {{ width: 2fr; }}

.panel {{ background: {theme.BG}; }}

/* bordered mission-control cards */
#welcome, #status, #overview, #clock, #monitor {{
    border: round {theme.FAINT};
    background: {theme.PANEL_BG};
}}
#overview, #clock, #monitor {{ border-title-color: {theme.ACCENT}; }}
"""


class ArtemisDashboardApp(App):
    """Live mission-control dashboard rendered with Textual."""

    CSS = _CSS
    BINDINGS = [('q', 'quit', 'Quit'), ('ctrl+c', 'quit', 'Quit')]

    def __init__(self, provider: Provider, *, fps: int = 10) -> None:
        super().__init__()
        self.provider = provider
        self.state = DashboardState()
        self.fps = fps

    def compose(self) -> ComposeResult:
        with Vertical(id='root'):
            yield Container(id='top-spacer')
            with Horizontal(id='header'):
                yield WordmarkPanel(id='wordmark', classes='panel')
                yield WelcomeCard(id='welcome', classes='panel')
                with Container(id='status-wrap'):
                    yield StatusPanel(id='status', classes='panel')
            with Horizontal(id='main'):
                yield MissionOverviewPanel(id='overview', classes='panel')
                yield MissionClockPanel(id='clock', classes='panel')
            yield SystemMonitorPanel(id='monitor', classes='panel')
            yield FooterPanel(id='footer', classes='panel')
            yield Container(id='bottom-spacer')

    def on_mount(self) -> None:
        # Defer the first paint until the whole widget tree (including nested
        # panel children) has mounted, then refresh on every tick.
        self.call_after_refresh(self._tick)
        self.set_interval(1.0 / self.fps, self._tick)

    def _tick(self) -> None:
        self.provider.update(self.state)
        self._refresh_panels()

    def _refresh_panels(self) -> None:
        """Push the latest ``state`` into every panel that consumes it."""
        for node in self.query('.panel'):
            update = getattr(node, 'update_state', None)
            if callable(update):
                update(self.state)

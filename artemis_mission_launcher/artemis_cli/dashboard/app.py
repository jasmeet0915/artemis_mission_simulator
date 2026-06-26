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
"""Textual application hosting the Artemis mission-control dashboard.

The data layer (``providers`` + ``DashboardState``) is unchanged; this module
owns only the Textual layout, the refresh tick, and the fan-out of ``state`` to
each panel widget. Colours live in :mod:`theme`; the CSS below is built from
those constants so the palette stays in one place.
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from . import theme
from .providers import Provider
from .state import DashboardState
from .widgets.header import StatusPanel, WelcomeCard, WordmarkPanel
from .widgets.mission_overview import MissionOverviewPanel

_CSS = f"""
Screen {{
    background: {theme.BG};
    color: {theme.PRIMARY};
}}
#header {{ height: 9; }}
#main {{ height: 1fr; }}
#monitor {{ height: 15; }}
#footer {{ height: 1; color: {theme.FAINT}; }}

#wordmark {{ width: 1fr; padding: 0 1; }}
#welcome {{ width: 1fr; }}
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
            with Horizontal(id='header'):
                yield WordmarkPanel(id='wordmark', classes='panel')
                yield WelcomeCard(id='welcome', classes='panel')
                yield StatusPanel(id='status', classes='panel')
            with Horizontal(id='main'):
                yield MissionOverviewPanel(id='overview', classes='panel')
                yield Static('', id='clock', classes='panel')
            yield Static('', id='monitor', classes='panel')
            yield Static('', id='footer', classes='panel')

    def on_mount(self) -> None:
        self.provider.update(self.state)
        self._refresh_panels()
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

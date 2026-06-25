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
"""Render the mission-control dashboard frame (pure, no I/O)."""
from artemis_cli.utils.epoch import format_iso
from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

_CYAN = 'bright_cyan'
_DIM = 'cyan'
_ACCENT = 'bright_white'
_OK = 'bright_green'
_WARN = 'yellow'
_VERSION = '0.1.0'

_BLOCKS = '▁▂▃▄▅▆▇█'

_BANNER_LINES = (
    '  _    ____ _____ _____ __  __ ___ ____',
    ' / \\  |  _ \\_   _| ____|  \\/  |_ _/ ___|',
    '/ _ \\ | |_) || | |  _| | |\\/| || |\\___ \\',
    '/ ___ \\|  _ < | | | |___| |  | || | ___) |',
    '/_/   \\_\\_| \\_\\|_| |_____|_|  |_|___|____/',
)
_BANNER = '\n'.join(_BANNER_LINES)


def sparkline(values, width, vmax=None):
    """Render a list of numbers as a fixed-width block sparkline."""
    series = [v for v in values if v is not None][-width:]
    if not series:
        return ' ' * width
    hi = vmax if vmax is not None else max(series)
    if not hi or hi <= 0:
        hi = 1.0
    glyphs = [
        _BLOCKS[round(min(max(v / hi, 0.0), 1.0) * (len(_BLOCKS) - 1))]
        for v in series
    ]
    return ''.join(glyphs).rjust(width)


def _bar(pct, width):
    filled = int(round(min(max(pct, 0.0), 100.0) / 100.0 * width))
    return '█' * filled + '░' * (width - filled)


def _hms(seconds):
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}'


def _status(metrics):
    hot = metrics.temp_c is not None and metrics.temp_c >= 85.0
    if metrics.cpu_pct >= 90.0 or hot:
        return ('CAUTION', _WARN)
    return ('NOMINAL', _OK)


def _header(status_text, status_style):
    grid = Table.grid(expand=True)
    grid.add_column(justify='left')
    grid.add_column(justify='center')
    grid.add_column(justify='right')
    grid.add_row(
        Text('ARTEMIS // MISSION CONTROL', style=f'bold {_CYAN}'),
        Text('WELCOME, COMMANDER', style=f'bold {_ACCENT}'),
        Text.assemble((f'● {status_text}', status_style),
                      (f'  ·  v{_VERSION}', _DIM)),
    )
    return grid


def _mission_panel(site, clock_iso, tplus):
    grid = Table.grid(padding=(0, 3))
    grid.add_column(style=_DIM, justify='left')
    grid.add_column(style=_ACCENT, justify='left')
    grid.add_row('MISSION CLOCK', f'{clock_iso} ⟳')
    grid.add_row('T+ ELAPSED', tplus)
    grid.add_row('SITE', site)
    return Panel(grid, title='MISSION', title_align='left',
                 border_style=_CYAN, padding=(1, 2))


def _systems_panel(metrics, history):
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style=_DIM, justify='left', min_width=6)
    grid.add_column(style=_CYAN, justify='left')
    grid.add_column(style=_ACCENT, justify='left')
    temp_val = '--' if metrics.temp_c is None else f'{metrics.temp_c:.0f} °C'
    grid.add_row('CPU', sparkline(history.get('cpu', []), 12, vmax=100),
                 f'{metrics.cpu_pct:.0f}%')
    grid.add_row('MEM', sparkline(history.get('mem', []), 12, vmax=100),
                 f'{metrics.mem_used_gb:.1f}/{metrics.mem_total_gb:.1f} GB '
                 f'({metrics.mem_pct:.0f}%)')
    grid.add_row('TEMP', sparkline(history.get('temp', []), 12, vmax=100),
                 temp_val)
    grid.add_row('DISK', _bar(metrics.disk_pct, 12), f'{metrics.disk_pct:.0f}%')
    grid.add_row('NET', sparkline(history.get('net', []), 12),
                 f'↑{metrics.net_up_kbs:.1f}  ↓{metrics.net_down_kbs:.1f} KB/s')
    grid.add_row('UPTIME', '', f'{metrics.uptime_s / 3600.0:.1f} h')
    return Panel(grid, title='SYSTEMS', title_align='left',
                 border_style=_CYAN, padding=(1, 2))


def render_frame(*, site, epoch_sec, elapsed_s, metrics, history):
    """Assemble the full dashboard as a rich Layout for the given sample."""
    clock_iso = format_iso(epoch_sec + int(elapsed_s))
    status_text, status_style = _status(metrics)

    layout = Layout()
    layout.split_column(
        Layout(_header(status_text, status_style), name='header', size=1),
        Layout(Align.center(Text(_BANNER, style=f'bold {_CYAN}')),
               name='banner', size=6),
        Layout(name='body'),
        Layout(Align.center(
            Text('Ctrl-b 1 → simulation     ·     Ctrl-C → abort mission',
                 style=_DIM)),
            name='footer', size=1),
    )
    layout['body'].split_row(
        Layout(_mission_panel(site, clock_iso, _hms(elapsed_s)), name='mission'),
        Layout(_systems_panel(metrics, history), name='systems'),
    )
    return layout

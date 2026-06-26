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
from artemis_cli.home.render import block_text, line_graph
from artemis_cli.utils.epoch import format_iso
from rich import box
from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

_CYAN = 'bright_cyan'
_DIM = 'cyan'
_ACCENT = 'bright_white'
_OK = 'bright_green'
_WARN = 'yellow'
_VERSION = '0.1.0'

_BLOCKS = '▁▂▃▄▅▆▇█'
_GRAPH_W = 18
_GRAPH_H = 2


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


def _header():
    grid = Table.grid(expand=True)
    grid.add_column(justify='left')
    grid.add_column(justify='right')
    grid.add_row(
        Text('ARTEMIS // MISSION CONTROL', style=f'bold {_CYAN}'),
        Text(f'v{_VERSION}', style=_DIM),
    )
    return grid


def _mission_panel(site, date_str, time_str, epoch_total, tplus,
                   status_text, status_style):
    body = Table.grid(padding=(0, 0))
    body.add_column()
    body.add_row(Text(date_str, style=_DIM))
    body.add_row(block_text(time_str, style=f'bold {_CYAN}'))
    body.add_row(Text(''))
    body.add_row(Text(f'{epoch_total:,} s', style=_DIM))
    body.add_row(Text.assemble(('T+ ELAPSED  ', _DIM), (tplus, _ACCENT)))
    body.add_row(Rule(style=_DIM))
    body.add_row(Text('CURRENT SITE', style=_DIM))
    body.add_row(block_text(site.upper(), style=f'bold {_ACCENT}', gap=0))
    title = Text.assemble(('MISSION STATUS  ', f'bold {_CYAN}'),
                          (f'● {status_text}', status_style))
    return Panel(body, title=title, title_align='left',
                 border_style=_DIM, box=box.SQUARE, padding=(1, 2))


def _welcome():
    inner = Table.grid()
    inner.add_column(justify='center')
    inner.add_row(Text(''))
    inner.add_row(block_text('WELCOME', style=f'bold {_ACCENT}'))
    inner.add_row(Text(''))
    inner.add_row(block_text('COMMANDER', style=f'bold {_ACCENT}'))
    return Align.center(inner, vertical='top')


def _systems_panel(metrics, history):
    grid = Table.grid(padding=(1, 2))
    grid.add_column(style=_DIM, justify='left', min_width=8)
    grid.add_column(justify='left')
    grid.add_column(style=_ACCENT, justify='right')
    temp_val = '--' if metrics.temp_c is None else f'{metrics.temp_c:.0f} °C'
    grid.add_row(
        'CPU',
        line_graph(history.get('cpu', []), _GRAPH_W, _GRAPH_H,
                   vmax=100, style=_CYAN),
        f'{metrics.cpu_pct:.0f}%')
    grid.add_row(
        'MEMORY',
        Text(_bar(metrics.mem_pct, _GRAPH_W), style=_CYAN),
        f'{metrics.mem_used_gb:.1f}/{metrics.mem_total_gb:.1f} GB')
    grid.add_row(
        'TEMP',
        line_graph(history.get('temp', []), _GRAPH_W, _GRAPH_H, style=_CYAN),
        temp_val)
    grid.add_row(
        'DISK',
        Text(_bar(metrics.disk_pct, _GRAPH_W), style=_CYAN),
        f'{metrics.disk_pct:.0f}%')
    grid.add_row(
        'NETWORK',
        line_graph(history.get('net', []), _GRAPH_W, _GRAPH_H, style=_CYAN),
        f'↑{metrics.net_up_kbs:.1f} ↓{metrics.net_down_kbs:.1f}')
    grid.add_row('UPTIME', Text(''), f'{metrics.uptime_s / 3600.0:.1f} h')
    return Panel(grid, title='SYSTEM OVERVIEW', title_align='left',
                 border_style=_DIM, box=box.SQUARE, padding=(1, 2))


def render_frame(*, site, epoch_sec, elapsed_s, metrics, history):
    """Assemble the full dashboard as a rich Layout for the given sample."""
    epoch_total = epoch_sec + int(elapsed_s)
    clock_iso = format_iso(epoch_total)
    date_str, time_part = clock_iso.split('T')
    time_str = time_part.rstrip('Z')
    status_text, status_style = _status(metrics)

    footer = Align.center(Text(
        'Ctrl-b 1 → simulation     ·     Ctrl-C → abort mission', style=_DIM))

    layout = Layout()
    layout.split_column(
        Layout(_header(), name='header', size=1),
        Layout(name='body'),
        Layout(footer, name='footer', size=1),
    )
    layout['body'].split_row(
        Layout(_mission_panel(site, date_str, time_str, epoch_total,
                              _hms(elapsed_s), status_text, status_style),
               name='mission'),
        Layout(_welcome(), name='welcome'),
        Layout(_systems_panel(metrics, history), name='systems'),
    )
    return layout

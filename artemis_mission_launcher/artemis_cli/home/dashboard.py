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
import os

from artemis_cli.home.render import line_graph, seven_seg
from artemis_cli.utils.epoch import format_iso
from rich import box
from rich.align import Align
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# Palette tuned to the concept art: cyan glow on near-black, dim teal chrome.
_CYAN = '#46d9df'    # primary — clock, live values
_LABEL = '#5f9ea1'   # field labels
_DIM = '#3c7174'     # secondary text
_MUTE = '#2c5659'    # quietest — quote, separators
_ACCENT = '#e8f4f4'  # bright readouts (numbers)
_BORDER = '#1d3f42'  # thin panel borders / rules
_OK = '#56d98c'
_WARN = '#e3c24d'
_VERSION = '0.1.0'

_GRAPH_W = 18
_GRAPH_H = 3

_QUOTE = (
    'WE CHOOSE TO GO TO THE MOON IN',
    'THIS DECADE AND DO THE OTHER THINGS,',
    'NOT BECAUSE THEY ARE EASY,',
    'BUT BECAUSE THEY ARE HARD.',
)


def _card(renderable, title=None):
    """Wrap a renderable in a thin, dim 'card' panel."""
    title_text = Text(title, style=_LABEL) if title else None
    return Panel(renderable, title=title_text, title_align='left',
                 border_style=_BORDER, box=box.SQUARE, padding=(0, 1))


def _seg_bar(pct, width):
    """Segmented gauge: filled segments cyan, empties dim."""
    filled = int(round(min(max(pct, 0.0), 100.0) / 100.0 * width))
    return Text.assemble(
        ('▮' * filled, _CYAN),
        ('▮' * (width - filled), _BORDER),
    )


def _hms(seconds):
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}'


def _dhms(seconds):
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return f'{days:02d}:{hours:02d}:{minutes:02d}:{secs:02d}'


def _status(metrics):
    hot = metrics.temp_c is not None and metrics.temp_c >= 85.0
    if metrics.cpu_pct >= 90.0 or hot:
        return ('CAUTION', _WARN)
    return ('NOMINAL', _OK)


# --- header ----------------------------------------------------------------
def _header(clock_label):
    grid = Table.grid(expand=True)
    grid.add_column(justify='left', ratio=1)
    grid.add_column(justify='center', ratio=1)
    grid.add_column(justify='right', ratio=1)
    grid.add_row(
        Text('▚ ARTEMIS // MISSION CONTROL', style=f'bold {_CYAN}'),
        Text('WELCOME TO ARTEMIS STACK', style=_DIM),
        Text(f'ARTEMIS LAUNCHER · v{_VERSION}', style=_DIM),
    )
    return Group(grid, Rule(style=_BORDER, characters='─'))


def _section_title(label, suffix=None):
    parts = [(label, f'bold {_CYAN}')]
    if suffix is not None:
        text, style = suffix
        parts.append((f'   ● {text}', style))
    return Text.assemble(*parts)


# --- left: mission status --------------------------------------------------
def _clock_card(date_str, time_str, epoch_total, sim_str):
    body = Table.grid()
    body.add_column()
    body.add_row(Text('MISSION TIME (UTC)', style=_LABEL))
    body.add_row(seven_seg(date_str, style=_CYAN))
    body.add_row(seven_seg(time_str, style=f'bold {_CYAN}'))
    body.add_row(Text(''))
    body.add_row(Text.assemble(('TDB       ', _LABEL),
                               (f'{epoch_total:,} s', _ACCENT)))
    body.add_row(Text.assemble(('SIM TIME  ', _LABEL), (sim_str, _ACCENT)))
    return _card(body)


def _site_card(site):
    body = Table.grid()
    body.add_column()
    body.add_row(Text(site.replace('_', ' ').upper(),
                      style=f'bold {_ACCENT}'))
    body.add_row(Text('LANDING REGION · SOUTH POLE', style=_DIM))
    return _card(body, title='CURRENT SITE')


def _mission_column(site, date_str, time_str, epoch_total, sim_str,
                    status_text, status_style):
    col = Table.grid(padding=(1, 0), expand=True)
    col.add_column()
    col.add_row(_section_title('MISSION STATUS', (status_text, status_style)))
    col.add_row(_clock_card(date_str, time_str, epoch_total, sim_str))
    col.add_row(_site_card(site))
    return col


# --- center: welcome + JFK quote -------------------------------------------
def _center():
    user = (os.environ.get('USER') or 'commander').upper()
    inner = Table.grid()
    inner.add_column(justify='center')
    inner.add_row(Text(f'WELCOME, {user}', style=f'bold {_CYAN}'))
    inner.add_row(Text(''))
    inner.add_row(Text('ARTEMIS LUNAR SURFACE PROGRAM', style=_DIM))
    inner.add_row(Text(''))
    inner.add_row(Text(''))
    for line in _QUOTE:
        inner.add_row(Text(f'// {line}', style=_MUTE))
    inner.add_row(Text(''))
    inner.add_row(Text('— J. F. KENNEDY, 1962', style=_DIM))
    return Align.center(inner, vertical='middle')


# --- right: system overview ------------------------------------------------
def _metric(label, gauge, value, sub=None):
    grid = Table.grid(expand=True)
    grid.add_column(style=_LABEL, justify='left', min_width=8)
    grid.add_column(justify='center', ratio=1)
    grid.add_column(style=_ACCENT, justify='right')
    grid.add_row(label, gauge, value)
    if sub is not None:
        grid.add_row('', '', Text(sub, style=_DIM))
    return grid


def _systems_column(metrics, history):
    temp_val = '--' if metrics.temp_c is None else f'{metrics.temp_c:.0f} °C'
    ghz = '' if metrics.cpu_ghz is None else f' {metrics.cpu_ghz:.1f} GHz'
    body = Table.grid(padding=(1, 0), expand=True)
    body.add_column()
    body.add_row(_metric(
        'CPU',
        line_graph(history.get('cpu', []), _GRAPH_W, _GRAPH_H,
                   vmax=100, style=_CYAN),
        f'{metrics.cpu_pct:.0f}%',
        sub=f'{metrics.cpu_model}{ghz}'))
    body.add_row(_metric(
        'MEMORY',
        _seg_bar(metrics.mem_pct, _GRAPH_W),
        f'{metrics.mem_pct:.0f}%',
        sub=f'{metrics.mem_used_gb:.1f} / {metrics.mem_total_gb:.1f} GB'))
    body.add_row(_metric(
        'TEMP',
        line_graph(history.get('temp', []), _GRAPH_W, _GRAPH_H, style=_CYAN),
        temp_val))
    body.add_row(_metric(
        'DISK',
        _seg_bar(metrics.disk_pct, _GRAPH_W),
        f'{metrics.disk_pct:.0f}%'))
    body.add_row(_metric(
        'NETWORK',
        line_graph(history.get('net', []), _GRAPH_W, _GRAPH_H, style=_CYAN),
        f'↑{metrics.net_up_kbs:.0f} ↓{metrics.net_down_kbs:.0f}'))
    body.add_row(_metric(
        'UPTIME', Text(''), f'{metrics.uptime_s / 3600.0:.1f} h'))

    col = Table.grid(padding=(1, 0), expand=True)
    col.add_column()
    col.add_row(_section_title('SYSTEM OVERVIEW'))
    col.add_row(_card(body))
    return col


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
        Layout(_header(time_str), name='header', size=2),
        Layout(name='body'),
        Layout(footer, name='footer', size=1),
    )
    layout['body'].split_row(
        Layout(_mission_column(site, date_str, time_str, epoch_total,
                               _dhms(elapsed_s), status_text, status_style),
               name='mission', ratio=11),
        Layout(_center(), name='center', ratio=10),
        Layout(_systems_column(metrics, history), name='systems', ratio=11),
    )
    return layout

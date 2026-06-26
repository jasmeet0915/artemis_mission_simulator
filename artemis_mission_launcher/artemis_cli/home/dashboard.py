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

from artemis_cli.home.moon import lunar_phase, moon_art
from artemis_cli.home.render import big_text, line_graph, seven_seg
from artemis_cli.utils.epoch import format_iso
from rich import box
from rich.align import Align
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# Site catalog (real PGDA-78 metadata) — optional dependency, degrade if absent.
try:
    from lunar_terrain_exporter.utils.site_catalog import get_site
except Exception:  # pragma: no cover - package may be unbuilt in some envs
    get_site = None

# Palette: glowy electric blue on near-black.
_BLUE = '#54c5ff'     # primary glow — clock, live values, titles
_BRIGHT = '#a6e4ff'   # brightest highlights / big readouts
_ACCENT = '#e3f4ff'   # near-white key numbers
_LABEL = '#5f8fc4'    # field labels
_DIM = '#3d6f9e'      # secondary text
_MUTE = '#27506e'     # quietest — moon shadow, separators
_BORDER = '#1b3a57'   # thin, subtle panel borders / rules
_OK = '#5fe0a0'
_WARN = '#ffcf5a'
_VERSION = '0.1.0'

_GRAPH_W = 18
_GRAPH_H = 2


def _card(renderable, title=None):
    """Wrap a renderable in a thin, dim 'card' panel (subtle 1px border)."""
    title_text = Text(title, style=_LABEL) if title else None
    return Panel(renderable, title=title_text, title_align='left',
                 border_style=_BORDER, box=box.SQUARE, padding=(0, 1))


def _seg_bar(pct, width):
    """Segmented gauge: filled segments glow blue, empties subtle."""
    filled = int(round(min(max(pct, 0.0), 100.0) / 100.0 * width))
    return Text.assemble(
        ('▮' * filled, _BLUE),
        ('▮' * (width - filled), _BORDER),
    )


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


def _section_title(label, suffix=None):
    parts = [(label, f'bold {_BLUE}')]
    if suffix is not None:
        text, style = suffix
        parts.append((f'   ● {text}', style))
    return Text.assemble(*parts)


# --- header ----------------------------------------------------------------
def _header():
    grid = Table.grid(expand=True)
    grid.add_column(justify='left', ratio=1)
    grid.add_column(justify='center', ratio=1)
    grid.add_column(justify='right', ratio=1)
    grid.add_row(
        Text('▚ ARTEMIS // MISSION CONTROL', style=f'bold {_BLUE}'),
        Text('WELCOME TO ARTEMIS STACK', style=_DIM),
        Text(f'ARTEMIS LAUNCHER · v{_VERSION}', style=_DIM),
    )
    # Leading blank line gives the header a little breathing room from the top.
    return Group(Text(''), grid, Rule(style=_BORDER, characters='─'))


# --- left column: mission status -------------------------------------------
def _clock_card(date_str, time_str, epoch_total, sim_str):
    body = Table.grid()
    body.add_column()
    body.add_row(Text('MISSION TIME (UTC)', style=_LABEL))
    body.add_row(seven_seg(date_str, style=_BLUE))
    body.add_row(seven_seg(time_str, style=f'bold {_BLUE}'))
    body.add_row(Text(''))
    body.add_row(Text.assemble(('TDB       ', _LABEL),
                               (f'{epoch_total:,} s', _ACCENT)))
    body.add_row(Text.assemble(('SIM TIME  ', _LABEL), (sim_str, _ACCENT)))
    return _card(body)


def _site_card(site):
    body = Table.grid()
    body.add_column()
    body.add_row(Text(site.replace('_', ' ').upper(), style=f'bold {_BRIGHT}'))
    code = desc = None
    if get_site is not None:
        try:
            entry = get_site(site)
            code, desc = entry['site_code'], entry['description']
        except Exception:
            pass
    if code:
        body.add_row(Text(f'PGDA-78 · {code}', style=_BLUE))
    body.add_row(Text('LUNAR SOUTH POLE', style=_DIM))
    if desc:
        clean = desc.split('–', 1)[-1].strip() if '–' in desc else desc
        body.add_row(Text(clean, style=_DIM))
    return _card(body, title='CURRENT SITE')


def _phase_card(epoch_sec):
    ph = lunar_phase(epoch_sec)
    body = Table.grid(expand=True)
    body.add_column(style=_LABEL, justify='left')
    body.add_column(style=_ACCENT, justify='right')
    body.add_row(Text(ph['name'], style=f'bold {_BLUE}'), '')
    body.add_row('ILLUMINATION', f"{ph['fraction'] * 100:.0f}%")
    body.add_row('MOON AGE', f"{ph['age_days']:.1f} d")
    return _card(body, title='LUNAR PHASE')


def _mission_column(site, date_str, time_str, epoch_total, sim_str,
                    status_text, status_style, epoch_sec):
    col = Table.grid(padding=(1, 0), expand=True)
    col.add_column()
    col.add_row(_section_title('MISSION STATUS', (status_text, status_style)))
    col.add_row(_clock_card(date_str, time_str, epoch_total, sim_str))
    col.add_row(_site_card(site))
    col.add_row(_phase_card(epoch_sec))
    return col


# --- center column: welcome + ASCII moon -----------------------------------
def _center(epoch_sec):
    user = (os.environ.get('USER') or 'commander').upper()
    banner = Table.grid()
    banner.add_column(justify='center')
    banner.add_row(big_text('WELCOME', style=f'bold {_BLUE}'))
    banner.add_row(Text(''))
    banner.add_row(big_text(user, style=f'bold {_BRIGHT}'))
    welcome_card = _card(Align.center(banner))

    ph = lunar_phase(epoch_sec)
    caption = Text.assemble(
        ('☾ ', _BRIGHT), (ph['name'], f'bold {_BLUE}'),
        (f"   ·   {ph['fraction'] * 100:.0f}% ILLUMINATED", _DIM))

    col = Table.grid(expand=True)
    col.add_column(justify='center')
    col.add_row(welcome_card)
    col.add_row(Text('ARTEMIS LUNAR SURFACE PROGRAM', style=_DIM))
    col.add_row(Text(''))
    col.add_row(moon_art(epoch_sec, lit_style=f'bold {_BLUE}',
                         shadow_style=_MUTE))
    col.add_row(Text(''))
    col.add_row(caption)
    return Align.center(col, vertical='middle')


# --- right column: system overview (one card per metric) -------------------
def _metric_card(label, value, gauge=None, sub=None):
    head = Table.grid(expand=True)
    head.add_column(justify='left', style=_DIM, ratio=1)
    head.add_column(justify='right', style=f'bold {_BRIGHT}')
    head.add_row(sub or '', value)
    body = Group(head, gauge) if gauge is not None else head
    return _card(body, title=label)


def _systems_column(metrics, history):
    temp_val = '--' if metrics.temp_c is None else f'{metrics.temp_c:.0f} °C'
    ghz = '' if metrics.cpu_ghz is None else f' · {metrics.cpu_ghz:.1f} GHz'
    col = Table.grid(padding=(2, 0), expand=True)
    col.add_column()
    col.add_row(_section_title('SYSTEM OVERVIEW'))
    col.add_row(_metric_card(
        'CPU', f'{metrics.cpu_pct:.0f}%',
        gauge=line_graph(history.get('cpu', []), _GRAPH_W, _GRAPH_H,
                         vmax=100, style=_BLUE),
        sub=f'{metrics.cpu_model}{ghz}'))
    col.add_row(_metric_card(
        'MEMORY', f'{metrics.mem_pct:.0f}%',
        gauge=_seg_bar(metrics.mem_pct, _GRAPH_W),
        sub=f'{metrics.mem_used_gb:.1f} / {metrics.mem_total_gb:.1f} GB'))
    col.add_row(_metric_card(
        'TEMPERATURE', temp_val,
        gauge=line_graph(history.get('temp', []), _GRAPH_W, _GRAPH_H,
                         style=_BLUE)))
    col.add_row(_metric_card(
        'STORAGE', f'{metrics.disk_pct:.0f}%',
        gauge=_seg_bar(metrics.disk_pct, _GRAPH_W)))
    col.add_row(_metric_card(
        'NETWORK', f'↑{metrics.net_up_kbs:.0f} ↓{metrics.net_down_kbs:.0f}',
        gauge=line_graph(history.get('net', []), _GRAPH_W, _GRAPH_H,
                         style=_BLUE),
        sub='KB/S'))
    col.add_row(_metric_card('UPTIME', f'{metrics.uptime_s / 3600.0:.1f} h'))
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
        Layout(_header(), name='header', size=3),
        Layout(name='body'),
        Layout(footer, name='footer', size=1),
    )
    layout['body'].split_row(
        Layout(_mission_column(site, date_str, time_str, epoch_total,
                               _dhms(elapsed_s), status_text, status_style,
                               epoch_sec),
               name='mission', ratio=42),
        Layout(_center(epoch_sec), name='center', ratio=52),
        Layout(_systems_column(metrics, history), name='systems', ratio=38),
    )
    return layout

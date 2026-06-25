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
"""Boot sequence and live render loop for the mission-control home."""
import argparse
import collections
import time

from artemis_cli.home.dashboard import render_frame
from artemis_cli.home.metrics import MetricsReader
from artemis_cli.utils.epoch import format_iso
from rich.console import Console
from rich.live import Live

_REFRESH_HZ = 4.0
_HISTORY = 12
_BOOT_LINES = (
    'Initializing flight computer',
    'Establishing telemetry link',
    'Spinning up host metrics',
    'Syncing mission clock',
)


def _boot_sequence(console, epoch_sec):
    console.clear()
    console.print('\n[bold bright_cyan]  ARTEMIS // MISSION CONTROL[/]\n')
    for line in _BOOT_LINES:
        console.print(f'  [cyan][ ✦ ] {line:<32}[/] [bright_green]OK[/]')
        time.sleep(0.3)
    console.print(f'  [cyan][ ✦ ] Mission epoch · '
                  f'{format_iso(epoch_sec):<18}[/] [bright_green]OK[/]')
    console.print('\n  [bold bright_green]▸ ALL SYSTEMS GO[/]')
    time.sleep(0.6)


def run(site, epoch_sec, *, refresh_hz=_REFRESH_HZ, ticks=None):
    """Boot, then drive the live dashboard until interrupted (or `ticks`)."""
    console = Console()
    _boot_sequence(console, epoch_sec)
    reader = MetricsReader()
    history = {
        key: collections.deque(maxlen=_HISTORY)
        for key in ('cpu', 'mem', 'temp', 'net')
    }
    start = time.monotonic()
    period = 1.0 / refresh_hz
    count = 0
    with Live(console=console, screen=True, refresh_per_second=refresh_hz) as live:
        while ticks is None or count < ticks:
            metrics = reader.read()
            history['cpu'].append(metrics.cpu_pct)
            history['mem'].append(metrics.mem_pct)
            history['temp'].append(metrics.temp_c)
            history['net'].append(metrics.net_down_kbs)
            live.update(render_frame(
                site=site,
                epoch_sec=epoch_sec,
                elapsed_s=time.monotonic() - start,
                metrics=metrics,
                history=history,
            ))
            count += 1
            time.sleep(period)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='artemis-home',
        description='Artemis mission-control home dashboard',
    )
    parser.add_argument('--site', default='lunar_empty')
    parser.add_argument('--epoch-sec', type=int, required=True)
    args = parser.parse_args(argv)
    try:
        run(args.site, args.epoch_sec)
    except KeyboardInterrupt:
        pass
    return 0

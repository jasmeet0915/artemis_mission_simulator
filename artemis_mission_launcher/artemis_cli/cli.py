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
"""argparse entry point for the `artemis` command."""
import argparse
from datetime import datetime, timezone
import signal
import sys
import time

from artemis_cli.launch_stack import (
    MissionAlreadyRunning,
    SESSION_NAME,
    StackLauncher,
)
from artemis_cli.utils.epoch import EpochParseError, parse_epoch

DEFAULT_SITE = 'empty_lunar'


def build_parser():
    parser = argparse.ArgumentParser(
        prog='artemis', description='Artemis mission control CLI'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    liftoff = subparsers.add_parser(
        'liftoff', help='Launch the Artemis mission simulation'
    )
    liftoff.add_argument(
        '--epoch', default='now',
        help='Mission UTC epoch: now | now+<N>{s,m,h,d} | '
             'YYYY-MM-DD | YYYY-MM-DDTHH:MM:SSZ (default: now)',
    )
    liftoff.add_argument(
        '--site', default=DEFAULT_SITE,
        help=f'Mission site to launch (default: {DEFAULT_SITE})',
    )
    liftoff.add_argument(
        '-d', '--detached', action='store_true',
        help='Launch in the background instead of attaching to the tmux session',
    )
    liftoff.add_argument(
        '--no-home', dest='home', action='store_false',
        help='Do not launch the home mission-control dashboard',
    )
    liftoff.set_defaults(func=_run_liftoff, home=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


def _run_liftoff(args):
    try:
        epoch_sec = parse_epoch(args.epoch, datetime.now(timezone.utc))
    except EpochParseError as exc:
        print(f'artemis liftoff: {exc}', file=sys.stderr)
        return 2

    try:
        launcher = StackLauncher(epoch_sec=epoch_sec, site=args.site)
    except MissionAlreadyRunning as exc:
        print(f'artemis liftoff: {exc}', file=sys.stderr)
        return 3

    if args.home:
        launcher.launch_home()
    launcher.launch_simulation()
    launcher.launch_mission_manager()
    print(f'[artemis] mission epoch {epoch_sec} (Unix UTC), site {args.site}')

    if not args.detached:
        launcher.attach()  # replaces this process; does not return
        return 0

    def _shutdown(signum, frame):
        launcher.smooth_shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    print(f'[artemis] running in background. Attach: tmux attach -t {SESSION_NAME}')
    print('[artemis] Press Ctrl-C to shut down the mission.')
    while True:
        time.sleep(1)

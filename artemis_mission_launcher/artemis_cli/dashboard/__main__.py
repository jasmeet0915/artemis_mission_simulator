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
"""``python3 -m artemis_cli.dashboard`` entry point."""
from __future__ import annotations

import argparse
import sys

from .dashboard import run
from .providers import MockProvider, SystemProvider


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog='artemis-dashboard',
        description='Artemis mission-control dashboard')
    parser.add_argument('--site', default='shackleton_rim')
    parser.add_argument('--epoch-sec', type=int, default=None)
    parser.add_argument('--accel', type=float, default=100.0)
    parser.add_argument('--mock', action='store_true',
                        help='use synthetic telemetry instead of psutil')
    args = parser.parse_args(argv)

    kwargs = {'site': args.site, 'acceleration': args.accel}
    if args.epoch_sec is not None:
        kwargs['epoch_sec'] = args.epoch_sec
    provider = MockProvider(**kwargs) if args.mock else SystemProvider(**kwargs)

    try:
        run(provider)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())

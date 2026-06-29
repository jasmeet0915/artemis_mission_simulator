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
"""Resolve a friendly mission-epoch string to whole Unix seconds (UTC)."""
from datetime import datetime, timezone
import re

_DURATION_RE = re.compile(r'^now(?P<sign>[+-])(?P<num>\d+)(?P<unit>[smhd])$')
_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_ISO_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

_UNIT_SECONDS = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}

_ACCEPTED = (
    'now | now+<N>{s,m,h,d} | now-<N>{s,m,h,d} | '
    'YYYY-MM-DD | YYYY-MM-DDTHH:MM:SSZ'
)


class EpochParseError(ValueError):
    """Raised when an --epoch value cannot be parsed."""


def parse_epoch(value, now):
    """
    Return whole Unix seconds (UTC) for a friendly epoch string.

    `now` must be a timezone-aware UTC datetime; it is injected so the
    'now' / 'now±delta' forms are deterministic and testable.
    """
    text = value.strip()

    if text == 'now':
        return int(now.timestamp())

    match = _DURATION_RE.match(text)
    if match:
        delta = int(match['num']) * _UNIT_SECONDS[match['unit']]
        if match['sign'] == '-':
            delta = -delta
        return int(now.timestamp()) + delta

    if _DATE_RE.match(text):
        return _strict_utc(text, '%Y-%m-%d')

    if _ISO_RE.match(text):
        return _strict_utc(text, '%Y-%m-%dT%H:%M:%SZ')

    raise EpochParseError(
        f'unrecognized --epoch value {value!r}; accepted: {_ACCEPTED}'
    )


def format_iso(epoch_sec):
    """Format whole Unix seconds (UTC) as 'YYYY-MM-DDTHH:MM:SSZ'."""
    return datetime.fromtimestamp(epoch_sec, tz=timezone.utc).strftime(
        '%Y-%m-%dT%H:%M:%SZ'
    )


def _strict_utc(text, fmt):
    try:
        parsed = datetime.strptime(text, fmt)
    except ValueError as exc:
        raise EpochParseError(
            f'invalid date/time {text!r}; accepted: {_ACCEPTED}'
        ) from exc
    return int(parsed.replace(tzinfo=timezone.utc).timestamp())

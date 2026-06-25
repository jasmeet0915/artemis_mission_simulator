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
"""Tests for artemis_cli.epoch.parse_epoch."""
from datetime import datetime, timezone

import pytest

from artemis_cli.epoch import EpochParseError, parse_epoch

# 2026-06-23T12:00:00Z == 1782216000
NOW = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
NOW_SEC = 1782216000


def test_now_truncates_to_whole_seconds():
    now = NOW.replace(microsecond=750000)
    assert parse_epoch("now", now) == NOW_SEC


def test_now_plus_hours():
    assert parse_epoch("now+6h", NOW) == NOW_SEC + 6 * 3600


def test_now_minus_minutes():
    assert parse_epoch("now-30m", NOW) == NOW_SEC - 30 * 60


def test_now_plus_days():
    assert parse_epoch("now+2d", NOW) == NOW_SEC + 2 * 86400


def test_now_plus_seconds():
    assert parse_epoch("now+45s", NOW) == NOW_SEC + 45


def test_date_only_is_midnight_utc():
    # 2026-06-23T00:00:00Z == 1782172800
    assert parse_epoch("2026-06-23", NOW) == 1782172800


def test_full_iso_roundtrip():
    assert parse_epoch("2026-06-23T12:00:00Z", NOW) == NOW_SEC


def test_surrounding_whitespace_is_ignored():
    assert parse_epoch("  now  ", NOW) == NOW_SEC


@pytest.mark.parametrize(
    "bad",
    ["6h", "now+", "now+6x", "now*2", "2026-13-01", "2026-06-23T12:00:00",
     "2026-06-23 12:00:00", "", "tomorrow"],
)
def test_malformed_raises(bad):
    with pytest.raises(EpochParseError):
        parse_epoch(bad, NOW)

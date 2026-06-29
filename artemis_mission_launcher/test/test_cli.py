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
"""Tests for the artemis CLI argument parser."""
from artemis_cli.cli import build_parser
import pytest


def test_detached_defaults_to_false():
    args = build_parser().parse_args(['liftoff'])
    assert args.detached is False


def test_detached_flag_sets_true():
    args = build_parser().parse_args(['liftoff', '--detached'])
    assert args.detached is True
    assert build_parser().parse_args(['liftoff', '-d']).detached is True


def test_interactive_flag_is_removed():
    with pytest.raises(SystemExit):
        build_parser().parse_args(['liftoff', '-i'])

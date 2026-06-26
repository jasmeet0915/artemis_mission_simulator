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
"""Tests for artemis_cli.home.dashboard."""
from artemis_cli.home.dashboard import render_frame
from artemis_cli.home.metrics import SystemMetrics
from rich.console import Console


def _metrics(cpu_pct=12.0, temp_c=57.0):
    return SystemMetrics(
        cpu_pct=cpu_pct,
        cpu_model='Intel i7-12700H',
        cpu_ghz=2.1,
        mem_used_gb=6.7,
        mem_total_gb=16.0,
        mem_pct=42.0,
        temp_c=temp_c,
        disk_pct=28.0,
        net_up_kbs=1.2,
        net_down_kbs=12.4,
        uptime_s=17.4 * 3600,
    )


def _render_text(metrics):
    history = {key: [10, 20, 30, 40] for key in ('cpu', 'mem', 'temp', 'net')}
    frame = render_frame(
        site='lunar_empty',
        epoch_sec=1782216000,
        elapsed_s=9,
        metrics=metrics,
        history=history,
    )
    console = Console(width=170, height=48, record=True)
    console.print(frame)
    return console.export_text()


def test_frame_shows_titles_and_metric_labels():
    text = _render_text(_metrics())
    assert 'MISSION STATUS' in text
    assert 'SYSTEM OVERVIEW' in text
    assert 'CURRENT SITE' in text
    assert 'MISSION TIME' in text
    assert 'SIM TIME' in text
    for label in ('CPU', 'MEMORY', 'TEMP', 'DISK', 'NETWORK', 'UPTIME'):
        assert label in text


def test_frame_shows_cpu_model():
    assert 'Intel i7-12700H' in _render_text(_metrics())


def test_frame_status_nominal_then_caution():
    assert 'NOMINAL' in _render_text(_metrics(cpu_pct=12.0))
    assert 'CAUTION' in _render_text(_metrics(cpu_pct=99.0))


def test_frame_handles_missing_temperature():
    text = _render_text(_metrics(temp_c=None))
    assert 'TEMP' in text
    assert '--' in text

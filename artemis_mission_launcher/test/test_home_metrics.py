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
"""Tests for artemis_cli.home.metrics."""
from artemis_cli.home.metrics import MetricsReader, SystemMetrics


def test_reader_returns_system_metrics_with_sane_values():
    metrics = MetricsReader().read()
    assert isinstance(metrics, SystemMetrics)
    assert 0.0 <= metrics.cpu_pct <= 100.0
    assert 0.0 <= metrics.mem_pct <= 100.0
    assert metrics.mem_total_gb > 0.0
    assert 0.0 <= metrics.disk_pct <= 100.0
    assert metrics.net_up_kbs >= 0.0
    assert metrics.net_down_kbs >= 0.0
    assert metrics.uptime_s > 0.0
    assert metrics.temp_c is None or metrics.temp_c > 0.0
    assert isinstance(metrics.cpu_model, str) and metrics.cpu_model
    assert metrics.cpu_ghz is None or metrics.cpu_ghz > 0.0

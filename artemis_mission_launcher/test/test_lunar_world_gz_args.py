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
"""Tests for build_gz_args in lunar_world.launch.py."""
import importlib.util
from pathlib import Path


def _load_launch_module():
    path = Path(__file__).resolve().parents[1] / "launch" / "lunar_world.launch.py"
    spec = importlib.util.spec_from_file_location("lunar_world_launch", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gz_args_includes_initial_sim_time_when_set():
    mod = _load_launch_module()
    args = mod.build_gz_args("/g/gui.config", "/w/world.sdf", "1782216000")
    assert "--initial-sim-time 1782216000" in args


def test_gz_args_omits_initial_sim_time_when_empty():
    mod = _load_launch_module()
    args = mod.build_gz_args("/g/gui.config", "/w/world.sdf", "")
    assert "--initial-sim-time" not in args
    assert args.endswith("/w/world.sdf")

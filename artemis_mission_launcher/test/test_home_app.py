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
"""Tests for artemis_cli.home.app argument handling."""
from artemis_cli.home.app import main

import pytest


def test_main_requires_epoch_sec():
    with pytest.raises(SystemExit):
        main([])


def test_main_rejects_non_integer_epoch():
    with pytest.raises(SystemExit):
        main(['--epoch-sec', 'not-a-number'])

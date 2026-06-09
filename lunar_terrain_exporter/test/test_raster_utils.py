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


"""Tests for raster utility functions."""

from lunar_terrain_exporter.utils.raster_utils import normalize_array
import numpy as np
import pytest


class TestNormalizeArray:
    """Test normalization to 0-1 range."""

    def test_normalize_range(self):
        data = np.array([[100.0, 200.0], [150.0, 300.0]])
        normalized = normalize_array(data)
        assert normalized.min() == pytest.approx(0.0)
        assert normalized.max() == pytest.approx(1.0)

    def test_normalize_flat_surface(self):
        data = np.full((10, 10), 42.0)
        normalized = normalize_array(data)
        assert np.all(normalized == 0.0)

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

"""Tests for the runtime SPICE KernelManager (kernels baked at /opt/spice_kernels)."""

from pathlib import Path
import tempfile

from lunar_sky_tracker.spice.kernel_manager import KernelManager, KERNELS
import pytest
import spiceypy
from spiceypy.utils.exceptions import SpiceNOSUCHFILE

KERNEL_DIR = Path('/opt/spice_kernels')

EXPECTED_KERNELS = [
    'naif0012.tls',
    'de440s.bsp',
    'pck00011.tpc',
    'moon_pa_de440_200625.bpc',
    'moon_de440_250416.tf',
]


@pytest.fixture
def clear_spice_pool():
    """Clear the pool after each test so none leaks into (or from) the next."""
    yield
    spiceypy.kclear()


class TestKernelManager:
    def test_pinned_kernel_set_in_order(self):
        assert list(KERNELS) == EXPECTED_KERNELS

    def test_kernel_filenames_are_unique(self):
        assert len(KERNELS) == len(set(KERNELS))

    def test_missing_kernels_lists_all_when_dir_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KernelManager(Path(tmpdir))
            assert manager.missing_kernels() == list(KERNELS)

    def test_missing_kernels_empty_when_all_present(self):
        manager = KernelManager(KERNEL_DIR)
        assert manager.missing_kernels() == []

    def test_furnish_raises_no_such_file_when_kernels_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KernelManager(Path(tmpdir))
            with pytest.raises(SpiceNOSUCHFILE) as exc:
                manager.furnish()
            assert 'naif0012.tls' in str(exc.value)
            assert tmpdir in str(exc.value)

    def test_furnish_then_unload_roundtrip(self, clear_spice_pool):
        manager = KernelManager(KERNEL_DIR)
        assert manager.loaded_count() == 0
        assert KernelManager.kernels_furnished() is False
        manager.furnish()
        assert manager.loaded_count() == len(KERNELS)
        assert KernelManager.kernels_furnished() is True
        manager.unload()
        assert manager.loaded_count() == 0
        assert KernelManager.kernels_furnished() is False

    def test_kernel_info_reports_type_for_furnished_kernel(self, clear_spice_pool):
        manager = KernelManager(KERNEL_DIR)
        manager.furnish()
        filetype, _source, _handle = manager.kernel_info('de440s.bsp')
        assert filetype == 'SPK'

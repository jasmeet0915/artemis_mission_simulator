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

"""Runtime SPICE kernel lifecycle: verify presence, furnish, unload."""

from pathlib import Path

import spiceypy
from spiceypy.utils.exceptions import SpiceNOSUCHFILE


# Kernels need by the tracker. Installed in the container during build
KERNELS: tuple[str, ...] = (
    'naif0012.tls',              # LSK — leapseconds (UTC<->ET, str2et)
    'de440s.bsp',                # SPK — Sun/Earth/Moon ephemeris (DE440 subset)
    'pck00011.tpc',              # Text PCK — Moon radii/flattening (georec)
    'moon_pa_de440_200625.bpc',  # Binary PCK — lunar orientation over time
    'moon_de440_250416.tf',      # FK — MOON_ME/MOON_PA frame definitions
)


class KernelManager:
    """Verifies and furnishes the pinned kernel set from a directory."""

    def __init__(self, kernel_dir: Path = Path('/opt/spice_kernels')) -> None:
        self._kernel_dir = Path(kernel_dir)
        self._furnished: list[str] = []

    def missing_kernels(self) -> list[str]:
        """Return the manifest kernels not present in the kernel directory."""
        return [
            filename
            for filename in KERNELS
            if not (self._kernel_dir / filename).is_file()
        ]

    def furnish(self) -> None:
        """Verify every manifest kernel exists, then furnsh them in one call."""
        missing = self.missing_kernels()
        if missing:
            raise SpiceNOSUCHFILE(
                f'Missing SPICE kernels in {self._kernel_dir}: '
                f'{", ".join(missing)}')

        paths = [str(self._kernel_dir / filename) for filename in KERNELS]
        spiceypy.furnsh(paths)
        self._furnished = paths

    def unload(self) -> None:
        """Unload every kernel this manager furnished."""
        if self._furnished:
            spiceypy.unload(self._furnished)
            self._furnished = []

    @staticmethod
    def kernels_furnished() -> bool:
        """Return whether every manifest kernel is in the SPICE pool."""
        # Name match: a count breaks on extras; a flag goes stale on kclear().
        furnished = {
            Path(spiceypy.kdata(index, 'ALL')[0]).name
            for index in range(spiceypy.ktotal('ALL'))
        }
        return all(filename in furnished for filename in KERNELS)

    @staticmethod
    def loaded_count() -> int:
        """Return the number of kernels currently in the SPICE pool."""
        return spiceypy.ktotal('ALL')

    def kernel_info(self, filename: str) -> tuple[str, str, int]:
        """Return SPICE kinfo (file type, source, handle) for a furnished kernel."""
        return spiceypy.kinfo(str(self._kernel_dir / filename))

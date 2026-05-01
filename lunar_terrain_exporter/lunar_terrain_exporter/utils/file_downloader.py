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


"""File download utility with local caching."""

from pathlib import Path
from urllib.parse import urlparse

import requests
from tqdm import tqdm


class FileDownloader:
    """Downloads remote files with simple filename-based caching."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: str) -> Path:
        """Download a file if not already cached. Returns local path."""
        filename = Path(urlparse(url).path).name or "download"
        dest = self._cache_dir / filename
        if dest.exists():
            print(f"  Using cached: {dest}")
            return dest

        print(f"  Downloading: {url}")
        print("  Connecting…", end=" ", flush=True)
        with requests.get(url, stream=True, timeout=(15, 120)) as resp:
            resp.raise_for_status()
            print("connected.")
            total = int(resp.headers.get("content-length", 0))
            with (
                open(dest, "wb") as f,
                tqdm(
                    total=total or None,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=f"  {filename}",
                    leave=True,
                ) as bar,
            ):
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bar.update(len(chunk))
        print(f"  DEM downloaded to: {dest}")
        return dest

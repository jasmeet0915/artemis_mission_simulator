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

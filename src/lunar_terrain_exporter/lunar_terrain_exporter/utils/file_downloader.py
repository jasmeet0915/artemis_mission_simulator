"""File download utility with URL-hash-based local caching."""

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


class FileDownloader:
    """Downloads remote files with URL-hash-based cache to avoid collisions."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, url: str) -> Path:
        """Compute a collision-resistant cache path from a URL.

        Format: <sha256[:16]>_<filename>
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        filename = Path(urlparse(url).path).name or "download"
        return self._cache_dir / f"{url_hash}_{filename}"

    def download(self, url: str) -> Path:
        """Download a file if not already cached. Returns local path."""
        dest = self._cache_path(url)
        if dest.exists():
            print(f"  Using cached: {dest}")
            return dest

        print(f"  Downloading: {url}")
        with requests.get(url, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"  Saved to: {dest}")
        return dest

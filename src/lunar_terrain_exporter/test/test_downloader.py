"""Tests for the file downloader with URL-hash caching."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from lunar_terrain_exporter.utils.file_downloader import FileDownloader


class TestFileDownloader:
    def test_cache_key_includes_url_hash(self):
        """Two different URLs with same filename get different cache paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = FileDownloader(Path(tmpdir))
            key_a = dl._cache_path("https://server-a.com/data/dem.img")
            key_b = dl._cache_path("https://server-b.com/data/dem.img")
            assert key_a != key_b
            assert key_a.name.endswith("_dem.img")
            assert key_b.name.endswith("_dem.img")

    def test_same_url_gives_same_cache_path(self):
        """Same URL always maps to the same cache path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = FileDownloader(Path(tmpdir))
            key_a = dl._cache_path("https://example.com/dem.img")
            key_b = dl._cache_path("https://example.com/dem.img")
            assert key_a == key_b

    def test_returns_cached_file_without_download(self):
        """If file exists in cache, return it without downloading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = FileDownloader(Path(tmpdir))
            url = "https://example.com/test.img"
            cache_path = dl._cache_path(url)
            cache_path.write_bytes(b"cached data")

            with patch("lunar_terrain_exporter.utils.file_downloader.requests") as mock_req:
                result = dl.download(url)
                mock_req.get.assert_not_called()
            assert result == cache_path

    def test_downloads_when_not_cached(self):
        """Downloads and saves file when not in cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = FileDownloader(Path(tmpdir))
            url = "https://example.com/test.img"

            mock_resp = MagicMock()
            mock_resp.iter_content.return_value = [b"chunk1", b"chunk2"]
            mock_resp.raise_for_status = MagicMock()

            with patch("lunar_terrain_exporter.utils.file_downloader.requests") as mock_req:
                mock_req.get.return_value.__enter__ = MagicMock(
                    return_value=mock_resp)
                mock_req.get.return_value.__exit__ = MagicMock(
                    return_value=False)
                result = dl.download(url)

            assert result.exists()
            assert result.read_bytes() == b"chunk1chunk2"

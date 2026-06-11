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


"""Tests for the file downloader with local caching."""

from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

from lunar_terrain_exporter.utils.file_downloader import FileDownloader


class TestFileDownloader:
    def test_cache_hit_returns_file_without_downloading(self):
        """If file exists in cache, return it by URL-derived filename without downloading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = FileDownloader(Path(tmpdir))
            url = 'https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif'
            expected = Path(tmpdir) / 'Site01_final_adj_5mpp_surf.tif'
            expected.write_bytes(b'data')

            with patch('lunar_terrain_exporter.utils.file_downloader.requests') as mock_req:
                result = dl.download(url)
                mock_req.get.assert_not_called()
            assert result == expected
            assert result.name == 'Site01_final_adj_5mpp_surf.tif'

    def test_downloads_when_not_cached(self):
        """Downloads and saves file when not in cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = FileDownloader(Path(tmpdir))
            url = 'https://example.com/test.img'

            mock_resp = MagicMock()
            mock_resp.iter_content.return_value = [b'chunk1', b'chunk2']
            mock_resp.raise_for_status = MagicMock()

            with patch('lunar_terrain_exporter.utils.file_downloader.requests') as mock_req:
                mock_req.get.return_value.__enter__ = MagicMock(
                    return_value=mock_resp)
                mock_req.get.return_value.__exit__ = MagicMock(
                    return_value=False)
                result = dl.download(url)

            assert result.exists()
            assert result.read_bytes() == b'chunk1chunk2'

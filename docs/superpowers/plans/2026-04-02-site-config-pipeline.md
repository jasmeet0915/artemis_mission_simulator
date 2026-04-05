# Site Config & Pipeline Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add YAML-based site configuration for 13 Artemis III landing regions and fix the terrain generation pipeline to correctly handle LOLA PDS3 polar stereographic DEMs.

**Architecture:** A `SiteConfig` dataclass parsed from YAML becomes the single input contract. The CLI supports two modes: `--config` (batch from YAML) and `--name/--lat/--lon/--dem-url` (one-off). HeightmapGenerator is rewritten with manual polar stereographic coordinate conversion and correctly reads int16 PDS3 data with 0.5 scaling factor.

**Tech Stack:** Python 3.12, ROS 2 ament_python, rasterio, numpy, PyYAML, argparse, pytest

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `lunar_terrain_generator/site_config.py` | Create | `SiteConfig` dataclass + YAML parser + validation |
| `config/artemis_sites.yaml` | Create | Preset 13 Artemis III landing sites |
| `lunar_terrain_generator/cli.py` | Rewrite | argparse with `--config` and direct modes |
| `lunar_terrain_generator/heightmap.py` | Rewrite | Polar stereographic projection + int16 scaling |
| `lunar_terrain_generator/albedo.py` | Modify | CRS-aware windowed reads |
| `lunar_terrain_generator/downloader.py` | Modify | URL-hash-based caching |
| `lunar_terrain_generator/terrain_generator.py` | Modify | Accept `SiteConfig`, remove broken default URL |
| `setup.py` | Modify | Add config to `data_files` |
| `test/test_integration.py` | Create | End-to-end integration test with mocked downloads |
| `test/test_site_config.py` | Create | SiteConfig parsing + validation tests |
| `test/test_heightmap.py` | Create | Polar stereographic math + int16 scaling tests |
| `test/test_cli.py` | Create | CLI argument parsing tests |
| `test/test_downloader.py` | Create | URL-hash caching tests |
| `test/test_terrain_processing.py` | No change | Existing NormalMap + ModelWriter tests (7 passing) |

All paths below are relative to `src/lunar_terrain_generator/`.

---

### Task 1: Install Dependencies

**Files:**
- (No file changes — runtime dependency install only)

- [ ] **Step 1: Install rasterio**

Run:
```bash
pip install rasterio
```

- [ ] **Step 2: Verify installation**

Run:
```bash
python3 -c "import rasterio; print(rasterio.__version__)"
```
Expected: Prints version number without errors.

- [ ] **Step 3: Verify existing tests still pass**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```
Expected: 7 passed.

- [ ] **Step 4: Commit**

No commit needed — no file changes in this task.

---

### Task 2: SiteConfig Dataclass & YAML Parser

**Files:**
- Create: `lunar_terrain_generator/site_config.py`
- Create: `test/test_site_config.py`

- [ ] **Step 1: Write the failing tests**

Create `test/test_site_config.py`:

```python
"""Tests for site configuration parsing and validation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from lunar_terrain_generator.site_config import SiteConfig, load_sites, load_site


class TestSiteConfig:
    def test_create_with_required_fields(self):
        config = SiteConfig(
            name="test_site",
            lat=-86.5,
            lon=-4.0,
            dem_url="https://example.com/dem.img",
        )
        assert config.name == "test_site"
        assert config.lat == -86.5
        assert config.lon == -4.0
        assert config.dem_url == "https://example.com/dem.img"
        assert config.region_size_km == 10.0
        assert config.description == ""

    def test_create_with_all_fields(self):
        config = SiteConfig(
            name="haworth",
            lat=-86.5,
            lon=-4.0,
            dem_url="https://example.com/dem.img",
            region_size_km=5.0,
            lroc_url="https://example.com/lroc.tif",
            description="Haworth crater rim",
        )
        assert config.region_size_km == 5.0
        assert config.lroc_url == "https://example.com/lroc.tif"
        assert config.description == "Haworth crater rim"

    def test_validate_rejects_lat_above_minus_80(self):
        with pytest.raises(ValueError, match="lat"):
            SiteConfig(
                name="bad", lat=-70.0, lon=0.0,
                dem_url="https://example.com/dem.img",
            ).validate()

    def test_validate_rejects_empty_name(self):
        with pytest.raises(ValueError, match="name"):
            SiteConfig(
                name="", lat=-85.0, lon=0.0,
                dem_url="https://example.com/dem.img",
            ).validate()

    def test_validate_rejects_invalid_name_chars(self):
        with pytest.raises(ValueError, match="name"):
            SiteConfig(
                name="bad name/here", lat=-85.0, lon=0.0,
                dem_url="https://example.com/dem.img",
            ).validate()

    def test_validate_rejects_empty_dem_url(self):
        with pytest.raises(ValueError, match="dem_url"):
            SiteConfig(
                name="test", lat=-85.0, lon=0.0,
                dem_url="",
            ).validate()

    def test_validate_rejects_non_positive_region_size(self):
        with pytest.raises(ValueError, match="region_size_km"):
            SiteConfig(
                name="test", lat=-85.0, lon=0.0,
                dem_url="https://example.com/dem.img",
                region_size_km=0,
            ).validate()

    def test_validate_accepts_valid_config(self):
        config = SiteConfig(
            name="haworth", lat=-86.5, lon=-4.0,
            dem_url="https://example.com/dem.img",
        )
        config.validate()  # Should not raise


class TestLoadSites:
    def _write_yaml(self, data: dict, path: Path) -> Path:
        config_file = path / "sites.yaml"
        with open(config_file, "w") as f:
            yaml.dump(data, f)
        return config_file

    def test_load_single_site(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{
                    "name": "test_site",
                    "lat": -86.5,
                    "lon": -4.0,
                    "dem_url": "https://example.com/dem.img",
                }]
            }, Path(tmpdir))
            sites = load_sites(config_file)
            assert len(sites) == 1
            assert sites[0].name == "test_site"
            assert sites[0].region_size_km == 10.0

    def test_load_multiple_sites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [
                    {"name": "a", "lat": -86.0, "lon": 0.0,
                     "dem_url": "https://example.com/a.img"},
                    {"name": "b", "lat": -87.0, "lon": 10.0,
                     "dem_url": "https://example.com/b.img",
                     "region_size_km": 5.0},
                ]
            }, Path(tmpdir))
            sites = load_sites(config_file)
            assert len(sites) == 2
            assert sites[1].region_size_km == 5.0

    def test_load_site_by_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [
                    {"name": "a", "lat": -86.0, "lon": 0.0,
                     "dem_url": "https://example.com/a.img"},
                    {"name": "b", "lat": -87.0, "lon": 10.0,
                     "dem_url": "https://example.com/b.img"},
                ]
            }, Path(tmpdir))
            site = load_site(config_file, "b")
            assert site.name == "b"
            assert site.lat == -87.0

    def test_load_site_not_found_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [
                    {"name": "a", "lat": -86.0, "lon": 0.0,
                     "dem_url": "https://example.com/a.img"},
                ]
            }, Path(tmpdir))
            with pytest.raises(ValueError, match="no_such_site"):
                load_site(config_file, "no_such_site")

    def test_missing_required_field_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{"name": "bad", "lat": -86.0}]
            }, Path(tmpdir))
            with pytest.raises((KeyError, TypeError)):
                load_sites(config_file)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_site_config.py -v --tb=short
```
Expected: ERRORS — `ModuleNotFoundError: No module named 'lunar_terrain_generator.site_config'`

- [ ] **Step 3: Write the implementation**

Create `lunar_terrain_generator/site_config.py`:

```python
"""Site configuration dataclass and YAML parser."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_LROC_WAC_URL = (
    "https://planetarymaps.usgs.gov/mosaic/"
    "Lunar_LRO_LROC_WAC_Mosaic_Global_303ppd_v02.tif"
)

_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


@dataclass
class SiteConfig:
    """Configuration for a single terrain generation site."""

    name: str
    lat: float
    lon: float
    dem_url: str
    region_size_km: float = 10.0
    lroc_url: str = field(default_factory=lambda: DEFAULT_LROC_WAC_URL)
    description: str = ""

    def validate(self) -> None:
        """Validate configuration values. Raises ValueError on invalid data."""
        if not self.name or not _VALID_NAME_RE.match(self.name):
            raise ValueError(
                f"name must be non-empty and contain only alphanumeric, "
                f"hyphens, or underscores (got: {self.name!r})"
            )
        if self.lat > -80.0:
            raise ValueError(
                f"lat must be <= -80.0 for south pole DEMs (got: {self.lat})"
            )
        if not self.dem_url:
            raise ValueError("dem_url must be a non-empty string")
        if self.region_size_km <= 0:
            raise ValueError(
                f"region_size_km must be > 0 (got: {self.region_size_km})"
            )


def load_sites(config_path: Path) -> list[SiteConfig]:
    """Parse a YAML config file and return a list of validated SiteConfig objects."""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    sites = []
    for entry in data["sites"]:
        config = SiteConfig(
            name=entry["name"],
            lat=float(entry["lat"]),
            lon=float(entry["lon"]),
            dem_url=entry["dem_url"],
            region_size_km=float(entry.get("region_size_km", 10.0)),
            lroc_url=entry.get("lroc_url", DEFAULT_LROC_WAC_URL),
            description=entry.get("description", ""),
        )
        config.validate()
        sites.append(config)
    return sites


def load_site(config_path: Path, site_name: str) -> SiteConfig:
    """Load a single named site from a YAML config file."""
    sites = load_sites(config_path)
    for site in sites:
        if site.name == site_name:
            return site
    available = [s.name for s in sites]
    raise ValueError(
        f"Site {site_name!r} not found in {config_path}. "
        f"Available: {available}"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_site_config.py -v --tb=short
```
Expected: All tests pass.

- [ ] **Step 5: Run full test suite**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```
Expected: All tests pass (7 existing + new site_config tests).

- [ ] **Step 6: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/site_config.py src/lunar_terrain_generator/test/test_site_config.py
git commit -m "feat: add SiteConfig dataclass and YAML parser

Dataclass with validation for name, lat, lon, dem_url, region_size_km,
lroc_url, and description. load_sites() and load_site() parse YAML.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 3: Preset Artemis Sites YAML & setup.py

**Files:**
- Create: `config/artemis_sites.yaml`
- Modify: `setup.py`

- [ ] **Step 1: Create the preset config**

Create `config/artemis_sites.yaml`:

```yaml
# Artemis III Candidate Landing Regions
# Source: NASA, August 2022 (13 candidate regions near the lunar south pole)
# DEM: LOLA Polar Gridded Data Records from PDS Geosciences Node
# Coordinates are estimates based on parent crater geometry.

sites:
  - name: faustini_rim_a
    description: "Rim of Faustini crater, near Shoemaker and Amundsen"
    lat: -87.0
    lon: 77.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_875s_5m.img"
    region_size_km: 10

  - name: peak_near_shackleton
    description: "Peak near Shackleton crater at the lunar south pole"
    lat: -89.5
    lon: 130.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_875s_5m.img"
    region_size_km: 10

  - name: connecting_ridge
    description: "Ridge connecting Shackleton crater to de Gerlache crater"
    lat: -89.0
    lon: -60.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_875s_5m.img"
    region_size_km: 10

  - name: connecting_ridge_extension
    description: "Extension of the connecting ridge between Shackleton and de Gerlache"
    lat: -88.5
    lon: -50.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_875s_5m.img"
    region_size_km: 10

  - name: de_gerlache_rim_1
    description: "Northern rim of de Gerlache crater"
    lat: -88.2
    lon: -80.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_875s_5m.img"
    region_size_km: 10

  - name: de_gerlache_rim_2
    description: "Eastern rim of de Gerlache crater"
    lat: -88.5
    lon: -70.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_875s_5m.img"
    region_size_km: 10

  - name: de_gerlache_kocher_massif
    description: "Highland massif between de Gerlache and Kocher craters"
    lat: -86.0
    lon: -110.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_85s_10m.img"
    region_size_km: 10

  - name: haworth
    description: "Northern rim of Haworth crater"
    lat: -86.5
    lon: -4.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_85s_10m.img"
    region_size_km: 10

  - name: malapert_massif
    description: "Malapert Mountain, southwestern rim of Malapert crater"
    lat: -86.0
    lon: 0.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_85s_10m.img"
    region_size_km: 10

  - name: leibnitz_beta_plateau
    description: "Mons Mouton (Leibnitz Beta) flat-topped mountain plateau"
    lat: -84.6
    lon: 31.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80s_20m.img"
    region_size_km: 10

  - name: nobile_rim_1
    description: "Western rim of Nobile crater"
    lat: -85.3
    lon: 36.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_85s_10m.img"
    region_size_km: 10

  - name: nobile_rim_2
    description: "Northern rim of Nobile crater"
    lat: -84.5
    lon: 53.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80s_20m.img"
    region_size_km: 10

  - name: amundsen_rim
    description: "Northern rim of Amundsen crater"
    lat: -83.5
    lon: 83.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80s_20m.img"
    region_size_km: 10
```

- [ ] **Step 2: Verify the YAML parses correctly**

Run:
```bash
cd src/lunar_terrain_generator && python3 -c "
from lunar_terrain_generator.site_config import load_sites
sites = load_sites('config/artemis_sites.yaml')
print(f'Loaded {len(sites)} sites')
for s in sites:
    print(f'  {s.name}: ({s.lat}, {s.lon})')
"
```
Expected: `Loaded 13 sites` followed by all 13 site names with coordinates.

- [ ] **Step 3: Update setup.py to include config in data_files**

In `setup.py`, change the `data_files` list to add the config directory. Replace the existing `data_files` block:

```python
setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/environment',
            ['hooks/' + package_name + '.dsv',
             'hooks/' + package_name + '.sh']),
        ('share/' + package_name + '/config',
            ['config/artemis_sites.yaml']),
    ] + collect_data_files('models', 'share/' + package_name),
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'generate_lunar_sdf = lunar_terrain_generator.cli:main',
        ],
    },
)
```

The key change is adding:
```python
        ('share/' + package_name + '/config',
            ['config/artemis_sites.yaml']),
```

- [ ] **Step 4: Run full test suite**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_terrain_generator/config/artemis_sites.yaml src/lunar_terrain_generator/setup.py
git commit -m "feat: add preset Artemis III landing sites config

13 NASA candidate landing regions with LOLA DEM URLs, coordinates,
and region sizes. Config installed to share/ via setup.py data_files.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: Downloader URL-Hash Caching

**Files:**
- Modify: `lunar_terrain_generator/downloader.py`
- Create: `test/test_downloader.py`

- [ ] **Step 1: Write the failing tests**

Create `test/test_downloader.py`:

```python
"""Tests for the file downloader with URL-hash caching."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from lunar_terrain_generator.downloader import FileDownloader


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

            with patch("lunar_terrain_generator.downloader.requests") as mock_req:
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

            with patch("lunar_terrain_generator.downloader.requests") as mock_req:
                mock_req.get.return_value.__enter__ = MagicMock(return_value=mock_resp)
                mock_req.get.return_value.__exit__ = MagicMock(return_value=False)
                result = dl.download(url)

            assert result.exists()
            assert result.read_bytes() == b"chunk1chunk2"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_downloader.py -v --tb=short
```
Expected: FAIL — `FileDownloader` has no `_cache_path` method, `download` signature changed.

- [ ] **Step 3: Rewrite the downloader**

Replace the contents of `lunar_terrain_generator/downloader.py`:

```python
"""File download utility with URL-hash-based local caching."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse


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

        import requests

        print(f"  Downloading: {url}")
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  Saved to: {dest}")
        return dest
```

Note: The `download()` method signature changed — it no longer takes a `filename` parameter. The filename is derived from the URL hash. This will require updating `terrain_generator.py` callers (done in Task 7).

- [ ] **Step 4: Run downloader tests**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_downloader.py -v --tb=short
```
Expected: All downloader tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/downloader.py src/lunar_terrain_generator/test/test_downloader.py
git commit -m "feat: URL-hash-based download caching

Cache key is now sha256(url)[:16]_filename, preventing collisions
when different DEM URLs share the same base filename.
download() no longer takes a filename parameter.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 5: HeightmapGenerator Rewrite

**Files:**
- Rewrite: `lunar_terrain_generator/heightmap.py`
- Create: `test/test_heightmap.py`

- [ ] **Step 1: Write the failing tests**

Create `test/test_heightmap.py`:

```python
"""Tests for heightmap generation with polar stereographic projection."""

import numpy as np
import pytest

from lunar_terrain_generator.heightmap import HeightmapGenerator


class TestPolarStereographicConversion:
    """Test the lat/lon to polar stereographic coordinate conversion."""

    def test_south_pole_maps_to_origin(self):
        """The south pole (-90, 0) should map to (0, 0) in polar stereo."""
        x, y = HeightmapGenerator.latlon_to_stereo(-90.0, 0.0)
        assert abs(x) < 1.0  # within 1 meter of origin
        assert abs(y) < 1.0

    def test_south_pole_any_longitude(self):
        """Any longitude at -90 lat should map near the origin."""
        x, y = HeightmapGenerator.latlon_to_stereo(-90.0, 45.0)
        assert abs(x) < 1.0
        assert abs(y) < 1.0

    def test_known_offset_from_pole(self):
        """A point at -85 lat, 0 lon should be ~150km from pole.

        At -85°, the colatitude is 5°. On the Moon (R=1737.4km):
        polar stereo distance = 2R * tan(colat/2) ≈ 2*1737400*tan(2.5°)
        ≈ 2*1737400*0.04366 ≈ 151,700 m
        The point should be along the +Y axis (lon=0).
        """
        x, y = HeightmapGenerator.latlon_to_stereo(-85.0, 0.0)
        distance = np.sqrt(x**2 + y**2)
        assert 140_000 < distance < 165_000  # ~151.7 km
        assert abs(x) < 1000  # mostly along Y axis

    def test_longitude_rotates_position(self):
        """Different longitudes at same latitude should give different x,y
        but same distance from origin."""
        x1, y1 = HeightmapGenerator.latlon_to_stereo(-85.0, 0.0)
        x2, y2 = HeightmapGenerator.latlon_to_stereo(-85.0, 90.0)
        d1 = np.sqrt(x1**2 + y1**2)
        d2 = np.sqrt(x2**2 + y2**2)
        assert abs(d1 - d2) < 100  # same distance
        assert abs(x1 - x2) > 10_000  # different positions


class TestInt16Scaling:
    """Test the PDS3 int16 to elevation conversion."""

    def test_scaling_factor(self):
        raw = np.array([[100, 200], [300, 400]], dtype=np.int16)
        elevations = HeightmapGenerator.apply_pds3_scaling(raw, scale=0.5)
        np.testing.assert_array_almost_equal(
            elevations, [[50.0, 100.0], [150.0, 200.0]]
        )

    def test_nodata_handling(self):
        """NoData values (-32768 for int16) should become NaN."""
        raw = np.array([[100, -32768], [200, 300]], dtype=np.int16)
        elevations = HeightmapGenerator.apply_pds3_scaling(
            raw, scale=0.5, nodata=-32768
        )
        assert np.isnan(elevations[0, 1])
        assert elevations[0, 0] == 50.0


class TestHeightmapNormalization:
    """Test normalization to 0-1 range and resize to 2^n+1."""

    def test_normalize_range(self):
        data = np.array([[100.0, 200.0], [150.0, 300.0]])
        normalized = HeightmapGenerator.normalize(data)
        assert normalized.min() == pytest.approx(0.0)
        assert normalized.max() == pytest.approx(1.0)

    def test_normalize_flat_surface(self):
        data = np.full((10, 10), 42.0)
        normalized = HeightmapGenerator.normalize(data)
        assert np.all(normalized == 0.0)

    def test_nearest_gazebo_size(self):
        assert HeightmapGenerator.nearest_gazebo_size(500) == 513
        assert HeightmapGenerator.nearest_gazebo_size(513) == 513
        assert HeightmapGenerator.nearest_gazebo_size(514) == 1025
        assert HeightmapGenerator.nearest_gazebo_size(1000) == 1025
        assert HeightmapGenerator.nearest_gazebo_size(1025) == 1025
        assert HeightmapGenerator.nearest_gazebo_size(1026) == 2049
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_heightmap.py -v --tb=short
```
Expected: FAIL — `HeightmapGenerator` has no `latlon_to_stereo`, `apply_pds3_scaling`, `normalize`, `nearest_gazebo_size` methods.

- [ ] **Step 3: Rewrite heightmap.py**

Replace the contents of `lunar_terrain_generator/heightmap.py`:

```python
"""Heightmap generation from LOLA PDS3 polar stereographic DEMs."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

# Lunar radius in meters (IAU mean)
_LUNAR_RADIUS_M = 1_737_400.0


class HeightmapGenerator:
    """Generates normalized heightmap arrays from LOLA polar DEM data.

    Handles the polar stereographic projection used by LOLA south pole DEMs
    and the int16 PDS3 data format with scaling factor.
    """

    @staticmethod
    def latlon_to_stereo(lat: float, lon: float) -> tuple[float, float]:
        """Convert geographic lat/lon to lunar south pole stereographic (x, y).

        Projection: polar stereographic centered on south pole (-90, 0).
        Sphere radius: 1,737,400 m (IAU lunar mean).

        Returns (x, y) in meters.
        """
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        # Colatitude from south pole
        colat = -(math.pi / 2 + lat_rad)
        r = 2.0 * _LUNAR_RADIUS_M * math.tan(colat / 2.0)
        x = r * math.sin(lon_rad)
        y = r * math.cos(lon_rad)
        return x, y

    @staticmethod
    def apply_pds3_scaling(
        raw: np.ndarray,
        scale: float = 0.5,
        nodata: int = -32768,
    ) -> np.ndarray:
        """Convert PDS3 int16 raw pixel values to elevation in meters.

        elevation_m = raw * scale
        NoData pixels become NaN.
        """
        result = raw.astype(np.float64) * scale
        if nodata is not None:
            result[raw == nodata] = np.nan
        return result

    @staticmethod
    def normalize(data: np.ndarray) -> np.ndarray:
        """Normalize elevation data to [0, 1] range. NaN becomes 0."""
        data = np.nan_to_num(data, nan=np.nanmin(data) if not np.all(np.isnan(data)) else 0.0)
        vmin = float(np.min(data))
        vmax = float(np.max(data))
        if vmax > vmin:
            return (data - vmin) / (vmax - vmin)
        return np.zeros_like(data, dtype=np.float64)

    @staticmethod
    def nearest_gazebo_size(n: int) -> int:
        """Return the smallest 2^k + 1 >= n (Gazebo heightmap requirement)."""
        if n <= 3:
            return 3
        k = math.ceil(math.log2(n - 1))
        return (1 << k) + 1

    @staticmethod
    def from_dem(
        dem_path: Path,
        lat: float,
        lon: float,
        region_size_km: float,
    ) -> tuple[np.ndarray, float, float]:
        """Crop a region from a LOLA PDS3 polar DEM and return a heightmap.

        Args:
            dem_path: Local path to the .img DEM file (with .lbl sidecar).
            lat: Center latitude in degrees (negative for south).
            lon: Center longitude in degrees.
            region_size_km: Side length of the square region in km.

        Returns:
            (heightmap_float64_01, elevation_min_m, elevation_max_m)
            Heightmap is resized to the nearest 2^n+1 dimension.
        """
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.enums import Resampling

        x_center, y_center = HeightmapGenerator.latlon_to_stereo(lat, lon)
        half_size = region_size_km * 1000.0 / 2.0
        x_min = x_center - half_size
        x_max = x_center + half_size
        y_min = y_center - half_size
        y_max = y_center + half_size

        with rasterio.open(dem_path) as src:
            window = from_bounds(x_min, y_min, x_max, y_max, src.transform)
            raw_width = max(int(window.width), 1)
            raw_height = max(int(window.height), 1)
            target_size = HeightmapGenerator.nearest_gazebo_size(
                max(raw_width, raw_height)
            )

            raw = src.read(
                1,
                window=window,
                out_shape=(target_size, target_size),
                resampling=Resampling.bilinear,
            )

        nodata = -32768
        elevations = HeightmapGenerator.apply_pds3_scaling(
            raw, scale=0.5, nodata=nodata
        )

        elev_min = float(np.nanmin(elevations))
        elev_max = float(np.nanmax(elevations))
        heightmap = HeightmapGenerator.normalize(elevations)

        return heightmap, elev_min, elev_max
```

- [ ] **Step 4: Run heightmap tests**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_heightmap.py -v --tb=short
```
Expected: All heightmap tests pass.

- [ ] **Step 5: Run full test suite**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py src/lunar_terrain_generator/test/test_heightmap.py
git commit -m "feat: rewrite HeightmapGenerator for LOLA polar stereographic DEMs

Manual lat/lon to polar stereo conversion (no pyproj needed for the
math). Handles int16 PDS3 format with 0.5 scaling factor. Auto-resizes
to nearest 2^n+1 for Gazebo. Replaces broken geographic coord math.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 6: AlbedoGenerator Fix

**Files:**
- Modify: `lunar_terrain_generator/albedo.py`

- [ ] **Step 1: Rewrite albedo.py**

The LROC WAC global mosaic is a simple cylindrical GeoTIFF. Near the poles, cylindrical projection causes E-W stretching, but we can still use geographic lat/lon bounds since the GeoTIFF is in geographic CRS. The key fix: use proper lunar meters-to-degrees math instead of the approximation `1/30000`.

Replace the contents of `lunar_terrain_generator/albedo.py`:

```python
"""Albedo texture generation from LROC WAC GeoTIFFs."""

from __future__ import annotations

from pathlib import Path

import numpy as np

# Lunar circumference / 360 ≈ 30.34 km per degree latitude
_LUNAR_M_PER_DEG = 1_737_400.0 * np.pi / 180.0  # ~30,326 m


class AlbedoGenerator:
    """Generates RGB albedo textures from LROC WAC data.

    The LROC WAC mosaic is in simple cylindrical (equirectangular) projection.
    Geographic lat/lon bounds work directly for windowed reads.
    """

    @staticmethod
    def from_geotiff(
        geotiff_path: Path,
        lat: float,
        lon: float,
        region_size_km: float,
        resolution: int,
    ) -> np.ndarray:
        """Crop and resample LROC WAC albedo data.

        Returns uint8 RGB array of shape (resolution, resolution, 3).
        """
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.enums import Resampling

        half_m = region_size_km * 1000.0 / 2.0
        half_lat = half_m / _LUNAR_M_PER_DEG
        cos_lat = max(np.cos(np.radians(lat)), 0.01)
        half_lon = half_m / (_LUNAR_M_PER_DEG * cos_lat)

        with rasterio.open(geotiff_path) as src:
            window = from_bounds(
                lon - half_lon, lat - half_lat,
                lon + half_lon, lat + half_lat,
                src.transform,
            )
            band_count = min(src.count, 3)
            bands = src.read(
                list(range(1, band_count + 1)),
                window=window,
                out_shape=(band_count, resolution, resolution),
                resampling=Resampling.bilinear,
            )

        if band_count == 1:
            grey = np.clip(bands[0], 0, 255).astype(np.uint8)
            return np.stack([grey, grey, grey], axis=-1)

        return np.moveaxis(bands[:3], 0, -1).astype(np.uint8)
```

- [ ] **Step 2: Run full test suite**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```
Expected: All tests pass (albedo has no unit tests — it requires real rasterio data).

- [ ] **Step 3: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/albedo.py
git commit -m "fix: use correct lunar meters-per-degree in AlbedoGenerator

Replace 1/30000 approximation with proper lunar radius constant.
Add docstrings explaining cylindrical projection handling.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 7: TerrainGenerator & CLI Rewrite

**Files:**
- Rewrite: `lunar_terrain_generator/terrain_generator.py`
- Rewrite: `lunar_terrain_generator/cli.py`
- Create: `test/test_cli.py`

- [ ] **Step 1: Write CLI tests**

Create `test/test_cli.py`:

```python
"""Tests for the CLI argument parsing."""

import pytest

from lunar_terrain_generator.cli import build_parser


class TestCLIConfigMode:
    def test_config_mode_all_sites(self):
        parser = build_parser()
        args = parser.parse_args([
            "--config", "sites.yaml",
            "--output-dir", "/tmp/out",
        ])
        assert args.config == "sites.yaml"
        assert args.output_dir == "/tmp/out"
        assert args.site is None

    def test_config_mode_single_site(self):
        parser = build_parser()
        args = parser.parse_args([
            "--config", "sites.yaml",
            "--site", "haworth",
            "--output-dir", "/tmp/out",
        ])
        assert args.config == "sites.yaml"
        assert args.site == "haworth"


class TestCLIDirectMode:
    def test_direct_mode_required_args(self):
        parser = build_parser()
        args = parser.parse_args([
            "--name", "custom",
            "--lat", "-85.0",
            "--lon", "30.0",
            "--dem-url", "https://example.com/dem.img",
            "--output-dir", "/tmp/out",
        ])
        assert args.name == "custom"
        assert args.lat == -85.0
        assert args.lon == 30.0
        assert args.dem_url == "https://example.com/dem.img"

    def test_direct_mode_optional_args(self):
        parser = build_parser()
        args = parser.parse_args([
            "--name", "custom",
            "--lat", "-85.0",
            "--lon", "30.0",
            "--dem-url", "https://example.com/dem.img",
            "--output-dir", "/tmp/out",
            "--region-size", "5.0",
        ])
        assert args.region_size == 5.0


class TestCLIMutualExclusion:
    def test_config_and_name_together_fails(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([
                "--config", "sites.yaml",
                "--name", "bad",
                "--output-dir", "/tmp/out",
            ])

    def test_no_mode_specified_fails(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--output-dir", "/tmp/out"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_cli.py -v --tb=short
```
Expected: FAIL — current `build_parser()` doesn't support `--config`/`--output-dir` args.

- [ ] **Step 3: Rewrite terrain_generator.py**

Replace the contents of `lunar_terrain_generator/terrain_generator.py`:

```python
"""Orchestrates the full terrain generation pipeline."""

from __future__ import annotations

from pathlib import Path

from .site_config import SiteConfig
from .heightmap import HeightmapGenerator
from .albedo import AlbedoGenerator
from .normal_map import NormalMapGenerator
from .downloader import FileDownloader
from .model_writer import ModelWriter


class TerrainGenerator:
    """Coordinates terrain generation from NASA data to finished Gazebo model."""

    def __init__(self, output_dir: Path, cache_dir: Path) -> None:
        self._output_dir = output_dir
        self._downloader = FileDownloader(cache_dir)

    def generate(self, site: SiteConfig) -> Path:
        """Generate a complete Gazebo terrain model for a site.

        Returns the path to the generated model directory.
        """
        print(f"\n=== Generating: {site.name} ===")
        print(f"    Lat: {site.lat}, Lon: {site.lon}, "
              f"Region: {site.region_size_km}km")

        dem_file = self._downloader.download(site.dem_url)
        heightmap, elev_min, elev_max = HeightmapGenerator.from_dem(
            dem_file, site.lat, site.lon, site.region_size_km
        )

        lroc_file = self._downloader.download(site.lroc_url)
        resolution = heightmap.shape[0]
        albedo = AlbedoGenerator.from_geotiff(
            lroc_file, site.lat, site.lon, site.region_size_km, resolution
        )

        normal_map = NormalMapGenerator.from_heightmap(heightmap)

        size_m = int(site.region_size_km * 1000)
        model_dir = self._output_dir / site.name
        writer = ModelWriter(model_dir)
        writer.write(
            site_id=site.name,
            display_name=site.name.replace("_", " ").title(),
            description=site.description or f"Lunar terrain at ({site.lat}, {site.lon})",
            heightmap=heightmap,
            albedo=albedo,
            normal_map=normal_map,
            size_m=size_m,
            elevation_min=elev_min,
            elevation_max=elev_max,
            lat=site.lat,
            lon=site.lon,
            source="nasa_lola_lroc",
        )
        return model_dir
```

- [ ] **Step 4: Rewrite cli.py**

Replace the contents of `lunar_terrain_generator/cli.py`:

```python
"""Command-line interface for the lunar terrain generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .site_config import SiteConfig, load_sites, load_site, DEFAULT_LROC_WAC_URL
from .terrain_generator import TerrainGenerator


def _default_cache_dir() -> Path:
    """Default cache: data/ directory at repository root."""
    return Path(__file__).resolve().parents[3] / "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Gazebo SDF terrain models from NASA LOLA/LROC data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Config mode (batch from YAML):\n"
            "  generate_lunar_sdf --config sites.yaml --output-dir ./models\n"
            "  generate_lunar_sdf --config sites.yaml --site haworth --output-dir ./models\n"
            "\n"
            "Direct mode (one-off):\n"
            "  generate_lunar_sdf --name my_site --lat -85.0 --lon 30.0 \\\n"
            "    --dem-url https://...ldem_85s_10m.img --output-dir ./models\n"
        ),
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--config", type=str, metavar="FILE",
        help="Path to YAML site configuration file",
    )
    mode.add_argument(
        "--name", type=str,
        help="Site name for direct (one-off) generation",
    )

    parser.add_argument(
        "--output-dir", type=str, required=True,
        help="Output directory for generated models",
    )
    parser.add_argument(
        "--cache-dir", type=str, default=None,
        help="Cache directory for downloaded data (default: <repo>/data/)",
    )

    # Config mode options
    parser.add_argument(
        "--site", type=str, default=None,
        help="Generate only this site from the config file",
    )

    # Direct mode options
    parser.add_argument("--lat", type=float, help="Center latitude")
    parser.add_argument("--lon", type=float, help="Center longitude")
    parser.add_argument("--dem-url", type=str, help="URL for LOLA DEM file")
    parser.add_argument(
        "--region-size", type=float, default=10.0,
        help="Region size in km (default: 10)",
    )
    parser.add_argument(
        "--lroc-url", type=str, default=DEFAULT_LROC_WAC_URL,
        help="URL for LROC WAC albedo GeoTIFF",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir) if args.cache_dir else _default_cache_dir()

    generator = TerrainGenerator(output_dir=output_dir, cache_dir=cache_dir)

    if args.config:
        config_path = Path(args.config)
        if args.site:
            site = load_site(config_path, args.site)
            generator.generate(site)
        else:
            sites = load_sites(config_path)
            for site in sites:
                generator.generate(site)
    else:
        # Direct mode — validate required args
        if not all([args.lat is not None, args.lon is not None, args.dem_url]):
            parser.error("Direct mode requires --lat, --lon, and --dem-url")

        site = SiteConfig(
            name=args.name,
            lat=args.lat,
            lon=args.lon,
            dem_url=args.dem_url,
            region_size_km=args.region_size,
            lroc_url=args.lroc_url,
        )
        site.validate()
        generator.generate(site)

    print("\nDone!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run CLI tests**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_cli.py -v --tb=short
```
Expected: All CLI tests pass.

- [ ] **Step 6: Run full test suite**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```
Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/terrain_generator.py src/lunar_terrain_generator/lunar_terrain_generator/cli.py src/lunar_terrain_generator/test/test_cli.py
git commit -m "feat: rewrite CLI and TerrainGenerator for config-based workflow

CLI supports --config mode (batch from YAML) and --name mode (one-off).
TerrainGenerator.generate() now takes a SiteConfig instead of individual
parameters. Removes broken DEFAULT_LOLA_URL.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 8: Update __init__.py Exports & README

**Files:**
- Modify: `lunar_terrain_generator/__init__.py`
- Modify: `README.md` (package-level)

- [ ] **Step 1: Update __init__.py**

Replace the contents of `lunar_terrain_generator/__init__.py`:

```python
"""Lunar terrain generation tool for Gazebo Harmonic."""

from .site_config import SiteConfig, load_sites, load_site
from .terrain_generator import TerrainGenerator

__all__ = ["SiteConfig", "load_sites", "load_site", "TerrainGenerator"]
```

- [ ] **Step 2: Update the package README**

Replace the contents of `README.md` (in `src/lunar_terrain_generator/`):

```markdown
# Lunar Terrain Generator

ROS 2 (ament_python) package that generates Gazebo SDF terrain models from NASA LOLA elevation data and LROC WAC albedo imagery.

## Features

- Generates 16-bit heightmap PNGs from LOLA Polar DEM data (PDS3 format)
- Generates albedo textures from LROC WAC global mosaic
- Derives normal maps using Sobel gradients
- Outputs complete Gazebo SDF model directories
- Ships with preset configurations for 13 NASA Artemis III candidate landing regions
- Supports custom site generation via YAML config or CLI arguments

## Usage

### Generate all Artemis III sites from preset config

```bash
generate_lunar_sdf --config config/artemis_sites.yaml --output-dir ./models
```

### Generate a single site from config

```bash
generate_lunar_sdf --config config/artemis_sites.yaml --site haworth --output-dir ./models
```

### Generate a custom site directly

```bash
generate_lunar_sdf --name my_site --lat -85.0 --lon 30.0 \
  --dem-url "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_85s_10m.img" \
  --output-dir ./models
```

## Site Configuration Format

Sites are defined in YAML files:

```yaml
sites:
  - name: haworth
    description: "Northern rim of Haworth crater"
    lat: -86.5
    lon: -4.0
    dem_url: "https://pds-geosciences.wustl.edu/.../ldem_85s_10m.img"
    region_size_km: 10  # optional, default: 10
```

## Available LOLA DEMs (South Pole)

| File | Coverage | Resolution |
|------|----------|------------|
| `ldem_80s_20m.img` | 80°S to pole | 20 m/px |
| `ldem_85s_10m.img` | 85°S to pole | 10 m/px |
| `ldem_875s_5m.img` | 87.5°S to pole | 5 m/px |

Use the highest-resolution DEM that covers your site's latitude.
```

- [ ] **Step 3: Run full test suite**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/__init__.py src/lunar_terrain_generator/README.md
git commit -m "docs: update package exports and README for config-based workflow

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 9: Integration Test & Final Cleanup

**Files:**
- Create: `test/test_integration.py`
- All modified files (validation pass)

- [ ] **Step 1: Write the integration test**

Create `test/test_integration.py`:

```python
"""Integration tests: SiteConfig → TerrainGenerator → output files.

Uses mocked downloads to avoid network access. Verifies the full pipeline
from YAML config to output model directory structure.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
import yaml

from lunar_terrain_generator.site_config import SiteConfig, load_sites
from lunar_terrain_generator.terrain_generator import TerrainGenerator


def _make_fake_dem(tmp_path: Path) -> Path:
    """Create a fake PDS3-format DEM file (int16, polar stereo)."""
    dem_path = tmp_path / "fake_dem.img"
    size = 100
    data = np.random.randint(-1000, 5000, (size, size), dtype=np.int16)
    data.tofile(dem_path)
    return dem_path


def _make_fake_albedo(tmp_path: Path) -> Path:
    """Create a fake albedo GeoTIFF."""
    albedo_path = tmp_path / "fake_albedo.tif"
    albedo_path.write_bytes(b"\x00" * 1000)
    return albedo_path


class TestIntegrationConfigLoad:
    """Verify the preset Artemis sites config loads correctly."""

    def test_load_all_artemis_sites(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        assert len(sites) == 13
        names = [s.name for s in sites]
        assert "faustini_rim_a" in names
        assert "amundsen_rim" in names

    def test_all_sites_have_valid_coords(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        for site in sites:
            site.validate()
            assert -90.0 <= site.lat <= -80.0
            assert -180.0 <= site.lon <= 180.0
            assert site.dem_url.startswith("https://")

    def test_all_site_names_are_unique(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        names = [s.name for s in sites]
        assert len(names) == len(set(names))


class TestIntegrationPipeline:
    """End-to-end pipeline with mocked downloads."""

    def test_terrain_generator_creates_output_structure(self, tmp_path):
        """Verify TerrainGenerator produces model dir with expected files."""
        config = SiteConfig(
            name="test_site",
            lat=-86.5,
            lon=-4.0,
            dem_url="https://example.com/ldem_85s_10m.img",
            region_size_km=2.0,
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create fake rasterio dataset that returns realistic data
        fake_dem_data = np.random.randint(-500, 2000, (513, 513), dtype=np.int16)
        fake_albedo_data = np.random.randint(0, 255, (513, 513), dtype=np.uint8)

        mock_dem_dataset = MagicMock()
        mock_dem_dataset.read.return_value = fake_dem_data
        mock_dem_dataset.transform = MagicMock()
        mock_dem_dataset.crs = MagicMock()
        mock_dem_dataset.bounds = MagicMock()
        mock_dem_dataset.width = 10000
        mock_dem_dataset.height = 10000
        mock_dem_dataset.__enter__ = MagicMock(return_value=mock_dem_dataset)
        mock_dem_dataset.__exit__ = MagicMock(return_value=False)

        mock_albedo_dataset = MagicMock()
        mock_albedo_dataset.read.return_value = fake_albedo_data
        mock_albedo_dataset.transform = MagicMock()
        mock_albedo_dataset.bounds = MagicMock()
        mock_albedo_dataset.width = 5000
        mock_albedo_dataset.height = 5000
        mock_albedo_dataset.__enter__ = MagicMock(return_value=mock_albedo_dataset)
        mock_albedo_dataset.__exit__ = MagicMock(return_value=False)

        with patch("lunar_terrain_generator.downloader.Downloader.download") as mock_dl, \
             patch("rasterio.open") as mock_rio:

            # Downloader returns cached paths
            mock_dl.side_effect = lambda url: tmp_path / url.split("/")[-1]

            # Write fake files so rasterio.open can "find" them
            for name in ["ldem_85s_10m.img"]:
                (tmp_path / name).write_bytes(b"\x00" * 100)

            mock_rio.side_effect = [mock_dem_dataset, mock_albedo_dataset]

            generator = TerrainGenerator(output_dir=str(output_dir))
            generator.generate(config)

        model_dir = output_dir / "test_site"
        assert model_dir.exists(), f"Model dir not created: {model_dir}"

        expected_files = [
            "model.sdf",
            "model.config",
        ]
        for fname in expected_files:
            assert (model_dir / fname).exists(), f"Missing: {fname}"

        textures_dir = model_dir / "materials" / "textures"
        assert textures_dir.exists(), "materials/textures dir not created"

        texture_files = ["heightmap.png", "normal.png"]
        for fname in texture_files:
            assert (textures_dir / fname).exists(), f"Missing texture: {fname}"
```

- [ ] **Step 2: Run the integration tests**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/test_integration.py -v --tb=short
```
Expected: All integration tests pass.

- [ ] **Step 3: Run the complete test suite**

Run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```
Expected: All tests pass — site_config, heightmap, downloader, cli, integration, normal_map, model_writer.

- [ ] **Step 4: Verify CLI help text**

Run:
```bash
cd src/lunar_terrain_generator && python -m lunar_terrain_generator.cli --help
```
Expected: Help text showing both config and direct modes.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_terrain_generator/test/test_integration.py
git commit -m "test: add integration tests with mocked downloads

Verifies full pipeline from SiteConfig → TerrainGenerator → output
model directory. Also tests loading all 13 Artemis sites from YAML.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

- [ ] **Step 6: Fix any issues found during integration**

If integration tests reveal bugs, fix them and re-run:
```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v --tb=short
```

Commit fixes:
```bash
git add -A
git commit -m "fix: integration test fixes

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

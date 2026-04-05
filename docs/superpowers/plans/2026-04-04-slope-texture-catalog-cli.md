# Slope Texture + Site Catalog + CLI Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add slope-derived diffuse textures from PGDA-78 data, build a 27-site catalog with deterministic URLs, and redesign the CLI for site-centric workflow with interactive selection.

**Architecture:** A `SlopeTextureGenerator` reads slope GeoTIFFs and produces grayscale diffuse textures. A `site_catalog` module registers all 27 PGDA-78 sites with computed URLs. The CLI supports three modes: interactive site selection, `--site <name>` flag, and `--config <file>` batch. `SiteConfig` gains `from_catalog()` and `slope_url` property. `ModelWriter` adds `<diffuse>` back to SDF template.

**Tech Stack:** Python 3.12, rasterio, numpy, scipy, PIL, argparse, pytest

**Spec:** `docs/superpowers/specs/2026-04-04-slope-texture-and-catalog-design.md`

---

### Task 1: Site Catalog

**Files:**
- Create: `src/generate_lunar_sdf/generate_lunar_sdf/utils/site_catalog.py`
- Create: `src/generate_lunar_sdf/test/test_site_catalog.py`
- Modify: `src/generate_lunar_sdf/generate_lunar_sdf/utils/__init__.py`

- [ ] **Step 1: Write test_site_catalog.py**

```python
"""Tests for the PGDA-78 site catalog."""

import pytest

from generate_lunar_sdf.utils.site_catalog import (
    CatalogSite, SITE_CATALOG, list_sites, get_site,
)

_BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"


class TestCatalogSite:
    def test_dem_url_generation(self):
        site = CatalogSite("Site01", "connecting_ridge", "Connecting Ridge", "desc")
        assert site.dem_url == f"{_BASE_URL}/Site01/Site01_final_adj_5mpp_surf.tif"

    def test_slope_url_generation(self):
        site = CatalogSite("Site01", "connecting_ridge", "Connecting Ridge", "desc")
        assert site.slope_url == f"{_BASE_URL}/Site01/Site01_final_adj_5mpp_slp.tif"

    def test_non_numeric_pgda_id(self):
        """Sites like Haworth, DM1, LM2 have non-SiteNN pgda_ids."""
        site = CatalogSite("Haworth", "haworth", "Haworth", "desc")
        assert site.dem_url == f"{_BASE_URL}/Haworth/Haworth_final_adj_5mpp_surf.tif"

    def test_frozen_dataclass(self):
        site = CatalogSite("Site01", "connecting_ridge", "Connecting Ridge", "desc")
        with pytest.raises(AttributeError):
            site.name = "other"


class TestSiteCatalog:
    def test_catalog_has_27_sites(self):
        assert len(SITE_CATALOG) == 27

    def test_known_sites_present(self):
        for name in ["connecting_ridge", "shackleton_rim", "peak_near_shackleton",
                      "de_gerlache_rim", "haworth", "shoemaker", "amundsen_rim"]:
            assert name in SITE_CATALOG

    def test_all_names_are_snake_case(self):
        for name in SITE_CATALOG:
            assert name == name.lower()
            assert " " not in name

    def test_all_pgda_ids_unique(self):
        ids = [s.pgda_id for s in SITE_CATALOG.values()]
        assert len(ids) == len(set(ids))


class TestListSites:
    def test_returns_all_27(self):
        sites = list_sites()
        assert len(sites) == 27

    def test_returns_catalog_site_objects(self):
        sites = list_sites()
        assert all(isinstance(s, CatalogSite) for s in sites)


class TestGetSite:
    def test_known_site(self):
        site = get_site("connecting_ridge")
        assert site.pgda_id == "Site01"
        assert site.display_name == "Connecting Ridge"

    def test_unknown_site_raises(self):
        with pytest.raises(KeyError, match="no_such_site"):
            get_site("no_such_site")

    def test_error_lists_available(self):
        with pytest.raises(KeyError, match="connecting_ridge"):
            get_site("bad_name")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/generate_lunar_sdf/test/test_site_catalog.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement site_catalog.py**

```python
"""PGDA Product 78 site catalog — all 27 south pole landing sites.

URL patterns are deterministic from the PGDA ID:
  DEM:   https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/{id}/{id}_final_adj_5mpp_surf.tif
  Slope: https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/{id}/{id}_final_adj_5mpp_slp.tif
"""

from __future__ import annotations

from dataclasses import dataclass

_BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"


@dataclass(frozen=True)
class CatalogSite:
    """Metadata for a single PGDA-78 south pole site."""

    pgda_id: str
    name: str
    display_name: str
    description: str

    @property
    def dem_url(self) -> str:
        """DEM (surface elevation) GeoTIFF URL."""
        return f"{_BASE_URL}/{self.pgda_id}/{self.pgda_id}_final_adj_5mpp_surf.tif"

    @property
    def slope_url(self) -> str:
        """Slope map GeoTIFF URL."""
        return f"{_BASE_URL}/{self.pgda_id}/{self.pgda_id}_final_adj_5mpp_slp.tif"


SITE_CATALOG: dict[str, CatalogSite] = {s.name: s for s in [
    CatalogSite("Site01", "connecting_ridge", "Connecting Ridge",
                "Site 01 – Connecting ridge between Shackleton and de Gerlache craters"),
    CatalogSite("Site04", "shackleton_rim", "Shackleton Rim",
                "Site 04 – Rim of Shackleton crater"),
    CatalogSite("Site06", "nobile_rim_1", "Nobile Rim 1",
                "Site 06 – Nobile rim 1"),
    CatalogSite("Site07", "peak_near_shackleton", "Peak Near Shackleton",
                "Site 07 – Isolated peak near Shackleton crater"),
    CatalogSite("Site11", "de_gerlache_rim", "de Gerlache Rim",
                "Site 11 – Rim of de Gerlache crater"),
    CatalogSite("Site20", "leibnitz_beta", "Leibnitz Beta Plateau",
                "Site 20 – Leibnitz beta plateau"),
    CatalogSite("Site20v2", "leibnitz_beta_v2", "Leibnitz Beta Plateau (Extended)",
                "Site 20v2 – Leibnitz beta plateau, extended boundaries"),
    CatalogSite("Site23", "malapert_massif", "Malapert Massif",
                "Site 23 – Malapert massif"),
    CatalogSite("Site42", "de_gerlache_kocher", "de Gerlache-Kocher Massif",
                "Site 42 – de Gerlache-Kocher massif"),
    CatalogSite("Haworth", "haworth", "Haworth",
                "Haworth crater"),
    CatalogSite("Shoemaker", "shoemaker", "Shoemaker",
                "Shoemaker crater"),
    CatalogSite("DM1", "amundsen_rim", "Amundsen Rim",
                "DM1 – Amundsen rim"),
    CatalogSite("DM2", "nobile_rim_2", "Nobile Rim 2",
                "DM2 – Nobile rim 2"),
    CatalogSite("SL2", "de_gerlache_rim_2", "de Gerlache Rim (SL2)",
                "SL2 – de Gerlache rim"),
    CatalogSite("SL3", "connecting_ridge_ext", "Connecting Ridge Extension",
                "SL3 – Connecting ridge extension"),
    CatalogSite("NPA", "cabeus_wall", "Cabeus Exterior Wall 1",
                "NPA – Cabeus exterior wall 1"),
    CatalogSite("NPB", "amundsen_1", "Amundsen 1",
                "NPB – Amundsen 1"),
    CatalogSite("NPC", "idelson_l", "Idel'son L Crater 1",
                "NPC – Idel'son L crater 1"),
    CatalogSite("NPD", "malapert_crater", "Malapert Crater 1",
                "NPD – Malapert crater 1"),
    CatalogSite("LM1", "shackleton_rim_b", "Shackleton Rim B",
                "LM1 – Shackleton Rim B"),
    CatalogSite("LM2", "shoemaker_rim_a", "Shoemaker Rim A",
                "LM2 – Shoemaker Rim A"),
    CatalogSite("LM3", "shoemaker_rim_b", "Shoemaker Rim B",
                "LM3 – Shoemaker Rim B"),
    CatalogSite("LM4", "shoemaker_rim_c", "Shoemaker Rim C",
                "LM4 – Shoemaker Rim C"),
    CatalogSite("LM5", "shoemaker_rim_d", "Shoemaker Rim D",
                "LM5 – Shoemaker Rim D"),
    CatalogSite("LM6", "shoemaker_rim_e", "Shoemaker Rim E",
                "LM6 – Shoemaker Rim E"),
    CatalogSite("LM7", "faustini_rim_a", "Faustini Rim A",
                "LM7 – Faustini Rim A"),
    CatalogSite("LM8", "shoemaker_rim_f", "Shoemaker Rim F",
                "LM8 – Shoemaker Rim F"),
]}


def list_sites() -> list[CatalogSite]:
    """Return all catalog sites in insertion order."""
    return list(SITE_CATALOG.values())


def get_site(name: str) -> CatalogSite:
    """Get a catalog site by name. Raises KeyError if not found."""
    try:
        return SITE_CATALOG[name]
    except KeyError:
        available = sorted(SITE_CATALOG.keys())
        raise KeyError(
            f"Site {name!r} not in catalog. Available: {available}"
        ) from None
```

- [ ] **Step 4: Update utils/__init__.py**

Add to `src/generate_lunar_sdf/generate_lunar_sdf/utils/__init__.py`:

```python
"""Utility modules for terrain generation: downloading, writing, config parsing, site catalog."""

from .site_config_parser import BoundingBox, Extent, SiteConfig, load_sites, load_site
from .file_downloader import FileDownloader
from .model_writer import ModelWriter
from .site_catalog import CatalogSite, SITE_CATALOG, list_sites as list_catalog_sites, get_site as get_catalog_site

__all__ = [
    "BoundingBox", "Extent", "SiteConfig", "load_sites", "load_site",
    "FileDownloader", "ModelWriter",
    "CatalogSite", "SITE_CATALOG", "list_catalog_sites", "get_catalog_site",
]
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest src/generate_lunar_sdf/test/test_site_catalog.py -v`
Expected: All 11 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/generate_lunar_sdf/generate_lunar_sdf/utils/site_catalog.py \
        src/generate_lunar_sdf/generate_lunar_sdf/utils/__init__.py \
        src/generate_lunar_sdf/test/test_site_catalog.py
git commit -m "feat: add PGDA-78 site catalog with all 27 south pole sites

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: Slope Texture Generator

**Files:**
- Create: `src/generate_lunar_sdf/generate_lunar_sdf/map_generators/slope_texture_generator.py`
- Create: `src/generate_lunar_sdf/test/test_slope_texture.py`
- Modify: `src/generate_lunar_sdf/generate_lunar_sdf/map_generators/__init__.py`

- [ ] **Step 1: Write test_slope_texture.py**

```python
"""Tests for slope-based diffuse texture generation."""

import numpy as np
import pytest
from pathlib import Path

from generate_lunar_sdf.map_generators.slope_texture_generator import SlopeTextureGenerator


class TestSlopeToGrayscale:
    def test_flat_surface_is_light(self):
        """Flat areas (0° slope) should map to light gray (~190)."""
        slope = np.zeros((64, 64), dtype=np.float64)
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        assert result.shape == (64, 64, 3)
        assert result.dtype == np.uint8
        assert result[0, 0, 0] == 190

    def test_steep_surface_is_dark(self):
        """Steep areas (>=45° slope) should map to dark gray (~60)."""
        slope = np.full((64, 64), 45.0, dtype=np.float64)
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        assert result[0, 0, 0] == 60

    def test_clamps_above_max(self):
        """Slopes above 45° should clamp to the same dark gray as 45°."""
        slope = np.full((64, 64), 90.0, dtype=np.float64)
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        assert result[0, 0, 0] == 60

    def test_intermediate_slope(self):
        """Mid-range slope should produce mid-range gray."""
        slope = np.full((64, 64), 22.5, dtype=np.float64)
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        gray = result[0, 0, 0]
        assert 100 < gray < 160

    def test_rgb_channels_equal(self):
        """All 3 RGB channels should be identical (grayscale)."""
        slope = np.random.uniform(0, 30, (64, 64))
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        np.testing.assert_array_equal(result[:, :, 0], result[:, :, 1])
        np.testing.assert_array_equal(result[:, :, 0], result[:, :, 2])

    def test_monotonic_darker_with_slope(self):
        """Higher slope values should produce darker (lower) gray values."""
        slopes = [0, 10, 20, 30, 45]
        grays = []
        for s in slopes:
            arr = np.full((4, 4), float(s))
            result = SlopeTextureGenerator.slope_to_grayscale(arr)
            grays.append(int(result[0, 0, 0]))
        for i in range(len(grays) - 1):
            assert grays[i] >= grays[i + 1]


class TestFromSlopeGeotiff:
    def _make_test_slope_geotiff(self, tmp_path: Path, size: int = 64) -> Path:
        """Create a small slope GeoTIFF in south polar stereographic."""
        import rasterio
        from rasterio.transform import from_bounds

        slope_path = tmp_path / "test_slope.tif"
        transform = from_bounds(-500, -500, 500, 500, size, size)
        data = np.linspace(0.0, 30.0, size * size, dtype=np.float32).reshape(size, size)

        with rasterio.open(
            slope_path, "w", driver="GTiff", height=size, width=size,
            count=1, dtype="float32",
            crs="EPSG:3031",
            transform=transform, nodata=-9999.0,
        ) as dst:
            dst.write(data, 1)
        return slope_path

    def test_full_extent_shape_and_dtype(self, tmp_path):
        slope_path = self._make_test_slope_geotiff(tmp_path)
        result = SlopeTextureGenerator.from_slope_geotiff(slope_path, 33, 33)
        assert result.shape == (33, 33, 3)
        assert result.dtype == np.uint8

    def test_full_extent_grayscale_range(self, tmp_path):
        slope_path = self._make_test_slope_geotiff(tmp_path)
        result = SlopeTextureGenerator.from_slope_geotiff(slope_path, 33, 33)
        assert result.min() >= 60
        assert result.max() <= 190

    def test_cropped_shape_and_dtype(self, tmp_path):
        slope_path = self._make_test_slope_geotiff(tmp_path, size=128)
        result = SlopeTextureGenerator.from_slope_geotiff_cropped(
            slope_path, -90.0, 0.0, 0.5, 0.5, 17, 17
        )
        assert result.shape == (17, 17, 3)
        assert result.dtype == np.uint8
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/generate_lunar_sdf/test/test_slope_texture.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement slope_texture_generator.py**

```python
"""Slope-based diffuse texture generation from PGDA Product 78 slope GeoTIFFs.

Maps slope values (degrees) to grayscale: flat areas appear light gray
(accumulated regolith), steep areas appear dark gray (exposed rock).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

_MAX_SLOPE_DEG = 45.0
_GRAY_FLAT = 190
_GRAY_STEEP = 60


class SlopeTextureGenerator:
    """Generates grayscale diffuse textures from PGDA-78 slope GeoTIFFs."""

    @staticmethod
    def slope_to_grayscale(slope_deg: np.ndarray) -> np.ndarray:
        """Map slope values (degrees) to grayscale RGB.

        Flat (0°) → 190, steep (≥45°) → 60.
        Returns uint8 RGB array (H, W, 3).
        """
        clamped = np.clip(slope_deg, 0.0, _MAX_SLOPE_DEG)
        normalized = clamped / _MAX_SLOPE_DEG
        gray = (_GRAY_FLAT - normalized * (_GRAY_FLAT - _GRAY_STEEP)).astype(np.uint8)
        return np.stack([gray, gray, gray], axis=-1)

    @staticmethod
    def from_slope_geotiff(
        slope_path: Path,
        target_height: int,
        target_width: int,
    ) -> np.ndarray:
        """Read full slope GeoTIFF and resample to target dimensions.

        Returns uint8 RGB array (target_height, target_width, 3).
        """
        import rasterio
        from rasterio.enums import Resampling

        with rasterio.open(slope_path) as src:
            slope = src.read(
                1,
                out_shape=(target_height, target_width),
                resampling=Resampling.bilinear,
            )
            nodata = src.nodata

        slope = slope.astype(np.float64)
        if nodata is not None:
            slope[np.isclose(slope, float(nodata))] = 0.0

        return SlopeTextureGenerator.slope_to_grayscale(slope)

    @staticmethod
    def from_slope_geotiff_cropped(
        slope_path: Path,
        lat: float,
        lon: float,
        width_km: float,
        height_km: float,
        target_height: int,
        target_width: int,
    ) -> np.ndarray:
        """Crop slope GeoTIFF to bounding box and resample.

        Uses the same polar stereographic projection as HeightmapGenerator.

        Returns uint8 RGB array (target_height, target_width, 3).
        """
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.enums import Resampling
        from .heightmap_generator import HeightmapGenerator

        x_center, y_center = HeightmapGenerator.latlon_to_stereo(lat, lon)
        half_w = width_km * 1000.0 / 2.0
        half_h = height_km * 1000.0 / 2.0

        with rasterio.open(slope_path) as src:
            window = from_bounds(
                x_center - half_w, y_center - half_h,
                x_center + half_w, y_center + half_h,
                src.transform,
            )
            slope = src.read(
                1,
                window=window,
                out_shape=(target_height, target_width),
                resampling=Resampling.bilinear,
            )
            nodata = src.nodata

        slope = slope.astype(np.float64)
        if nodata is not None:
            slope[np.isclose(slope, float(nodata))] = 0.0

        return SlopeTextureGenerator.slope_to_grayscale(slope)
```

- [ ] **Step 4: Update map_generators/__init__.py**

Replace with:

```python
"""Map generator modules: heightmap, normal map, and slope texture generation."""

from .heightmap_generator import HeightmapGenerator
from .normal_map_generator import NormalMapGenerator
from .slope_texture_generator import SlopeTextureGenerator

__all__ = ["HeightmapGenerator", "NormalMapGenerator", "SlopeTextureGenerator"]
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest src/generate_lunar_sdf/test/test_slope_texture.py -v`
Expected: All 9 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/generate_lunar_sdf/generate_lunar_sdf/map_generators/slope_texture_generator.py \
        src/generate_lunar_sdf/generate_lunar_sdf/map_generators/__init__.py \
        src/generate_lunar_sdf/test/test_slope_texture.py
git commit -m "feat: add SlopeTextureGenerator for PGDA-78 slope-derived diffuse textures

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 3: ModelWriter — Add Diffuse Texture

**Files:**
- Modify: `src/generate_lunar_sdf/generate_lunar_sdf/utils/model_writer.py`
- Modify: `src/generate_lunar_sdf/test/test_terrain_processing.py`

- [ ] **Step 1: Update test_terrain_processing.py**

Add a `_make_diffuse()` helper and update all 3 ModelWriter test methods to
pass `diffuse_map=` and assert `diffuse.png` exists. Also update the SDF
assertion to check for diffuse path.

Replace the `_make_heightmap()` function and everything below `# ModelWriter` with:

```python
def _make_heightmap(size: int = 65) -> np.ndarray:
    """Create a simple test heightmap (float64, [0,1])."""
    rng = np.random.default_rng(42)
    return rng.random((size, size))


def _make_diffuse(size: int = 65) -> np.ndarray:
    """Create a simple test diffuse map (uint8 RGB)."""
    rng = np.random.default_rng(42)
    return rng.integers(60, 190, (size, size, 3), dtype=np.uint8)
```

Update `TestModelWriter.test_writes_all_files`:

```python
    def test_writes_all_files(self):
        hm = _make_heightmap()
        diffuse = _make_diffuse()
        nm = NormalMapGenerator.from_heightmap(hm)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ModelWriter(Path(tmpdir) / "test_site")
            writer.write(
                site_id="test_site",
                display_name="Test Site",
                description="A test site",
                heightmap=hm,
                diffuse_map=diffuse,
                normal_map=nm,
                size_x_m=5000,
                size_y_m=4000,
                elevation_min=0.0,
                elevation_max=500.0,
                lat=-89.7,
                lon=0.0,
                source="nasa_pgda_78",
            )
            out = Path(tmpdir) / "test_site"
            assert (out / "model.sdf").exists()
            assert (out / "model.config").exists()
            assert (out / "metadata.yaml").exists()
            assert (out / "materials" / "textures" / "heightmap.png").exists()
            assert (out / "materials" / "textures" / "diffuse.png").exists()
            assert (out / "materials" / "textures" / "normal.png").exists()
```

Update `TestModelWriter.test_sdf_contains_site_id_and_sizes`:

```python
    def test_sdf_contains_site_id_and_sizes(self):
        hm = _make_heightmap()
        diffuse = _make_diffuse()
        nm = NormalMapGenerator.from_heightmap(hm)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ModelWriter(Path(tmpdir) / "my_site")
            writer.write(
                site_id="my_site",
                display_name="My Site",
                description="Desc",
                heightmap=hm,
                diffuse_map=diffuse,
                normal_map=nm,
                size_x_m=3000,
                size_y_m=2000,
                elevation_min=-100.0,
                elevation_max=200.0,
                lat=-85.0,
                lon=10.0,
                source="nasa_pgda_78",
            )
            sdf = (Path(tmpdir) / "my_site" / "model.sdf").read_text()
            assert 'name="my_site"' in sdf
            assert "3000" in sdf
            assert "2000" in sdf
            assert "diffuse.png" in sdf
```

Update `TestModelWriter.test_metadata_yaml_valid`:

```python
    def test_metadata_yaml_valid(self):
        hm = _make_heightmap()
        diffuse = _make_diffuse()
        nm = NormalMapGenerator.from_heightmap(hm)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ModelWriter(Path(tmpdir) / "meta_test")
            writer.write(
                site_id="meta_test",
                display_name="Meta Test",
                description="Testing metadata",
                heightmap=hm,
                diffuse_map=diffuse,
                normal_map=nm,
                size_x_m=5000,
                size_y_m=4000,
                elevation_min=0.0,
                elevation_max=500.0,
                lat=-89.7,
                lon=0.0,
                source="nasa_pgda_78",
            )
            with open(Path(tmpdir) / "meta_test" / "metadata.yaml") as f:
                meta = yaml.safe_load(f)
            assert meta["site_id"] == "meta_test"
            assert meta["size_x_m"] == 5000
            assert meta["size_y_m"] == 4000
            assert meta["elevation_range_m"] == 500.0
            assert meta["coordinates"]["lat"] == -89.7
            assert meta["source"] == "nasa_pgda_78"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/generate_lunar_sdf/test/test_terrain_processing.py -v`
Expected: FAIL — `write()` got unexpected keyword argument `diffuse_map`

- [ ] **Step 3: Update model_writer.py**

Add `<diffuse>` line back to the SDF template:

```xml
            <texture>
              <diffuse>model://${site_id}/materials/textures/diffuse.png</diffuse>
              <normal>model://${site_id}/materials/textures/normal.png</normal>
              <size>10</size>
            </texture>
```

Add `diffuse_map: np.ndarray` parameter to `write()` after `heightmap`:

```python
    def write(
        self,
        site_id: str,
        display_name: str,
        description: str,
        heightmap: np.ndarray,
        diffuse_map: np.ndarray,
        normal_map: np.ndarray,
        size_x_m: int,
        size_y_m: int,
        elevation_min: float,
        elevation_max: float,
        lat: float,
        lon: float,
        source: str,
    ) -> None:
```

Add diffuse PNG save after the normal map save:

```python
        # RGB diffuse texture PNG
        Image.fromarray(diffuse_map, mode="RGB").save(textures_dir / "diffuse.png")
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest src/generate_lunar_sdf/test/test_terrain_processing.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/generate_lunar_sdf/generate_lunar_sdf/utils/model_writer.py \
        src/generate_lunar_sdf/test/test_terrain_processing.py
git commit -m "feat: add diffuse texture support to ModelWriter and SDF template

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: SiteConfig — from_catalog() and slope_url

**Files:**
- Modify: `src/generate_lunar_sdf/generate_lunar_sdf/utils/site_config_parser.py`
- Modify: `src/generate_lunar_sdf/test/test_site_config.py`

- [ ] **Step 1: Add tests to test_site_config.py**

Add a new test class at the end of the file:

```python
class TestFromCatalog:
    def test_creates_config_from_catalog_name(self):
        config = SiteConfig.from_catalog("connecting_ridge")
        assert config.name == "connecting_ridge"
        assert "Site01" in config.dem_url
        assert config.extent.use_full is True
        assert config.description != ""

    def test_custom_extent(self):
        extent = Extent(
            use_full=False,
            bounding_box=BoundingBox(lat=-86.5, lon=-4.0, width_km=5.0, height_km=5.0),
        )
        config = SiteConfig.from_catalog("shackleton_rim", extent=extent)
        assert config.extent.use_full is False
        assert config.extent.bounding_box.lat == -86.5

    def test_unknown_site_raises(self):
        with pytest.raises(KeyError, match="no_such_site"):
            SiteConfig.from_catalog("no_such_site")


class TestSlopeUrl:
    def test_derives_slope_url_from_dem_url(self):
        config = SiteConfig(
            name="test",
            dem_url="https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif",
            extent=Extent(use_full=True),
        )
        assert config.slope_url == (
            "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_slp.tif"
        )

    def test_from_catalog_slope_url(self):
        config = SiteConfig.from_catalog("connecting_ridge")
        assert "_slp.tif" in config.slope_url
        assert "Site01" in config.slope_url


class TestLoadSitesCatalogShorthand:
    def _write_yaml(self, data: dict, path: Path) -> Path:
        config_file = path / "sites.yaml"
        with open(config_file, "w") as f:
            yaml.dump(data, f)
        return config_file

    def test_catalog_shorthand(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{
                    "site": "connecting_ridge",
                    "extent": {"use_full": True},
                }]
            }, Path(tmpdir))
            sites = load_sites(config_file)
            assert len(sites) == 1
            assert sites[0].name == "connecting_ridge"
            assert "Site01" in sites[0].dem_url

    def test_catalog_shorthand_with_bbox(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{
                    "site": "shackleton_rim",
                    "extent": {
                        "use_full": False,
                        "bounding_box": {"lat": -86.5, "lon": -4.0, "width_km": 5.0},
                    },
                }]
            }, Path(tmpdir))
            sites = load_sites(config_file)
            assert sites[0].extent.bounding_box.width_km == 5.0
            assert "Site04" in sites[0].dem_url

    def test_mixed_catalog_and_explicit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [
                    {
                        "site": "connecting_ridge",
                        "extent": {"use_full": True},
                    },
                    {
                        "name": "custom",
                        "dem_url": "https://example.com/dem.tif",
                        "extent": {"use_full": True},
                    },
                ]
            }, Path(tmpdir))
            sites = load_sites(config_file)
            assert len(sites) == 2
            assert sites[0].name == "connecting_ridge"
            assert sites[1].name == "custom"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/generate_lunar_sdf/test/test_site_config.py::TestFromCatalog -v`
Expected: FAIL — `SiteConfig` has no `from_catalog` method

- [ ] **Step 3: Add from_catalog() and slope_url to SiteConfig**

In `src/generate_lunar_sdf/generate_lunar_sdf/utils/site_config_parser.py`, add
`from_catalog()` classmethod and `slope_url` property to SiteConfig:

```python
@dataclass
class SiteConfig:
    """Configuration for a single terrain generation site."""

    name: str
    dem_url: str
    extent: Extent = field(default_factory=Extent)
    description: str = ""

    @classmethod
    def from_catalog(cls, site_name: str, extent: Extent | None = None) -> SiteConfig:
        """Construct SiteConfig from the PGDA-78 site catalog."""
        from .site_catalog import get_site
        cat = get_site(site_name)
        return cls(
            name=cat.name,
            dem_url=cat.dem_url,
            extent=extent or Extent(use_full=True),
            description=cat.description,
        )

    @property
    def slope_url(self) -> str:
        """Derive slope GeoTIFF URL from DEM URL."""
        return self.dem_url.replace("_surf.tif", "_slp.tif")

    def validate(self) -> None:
        # ... existing validate unchanged ...
```

- [ ] **Step 4: Update load_sites() for catalog shorthand**

In `load_sites()`, add catalog resolution before the existing logic:

```python
def load_sites(config_path: Path) -> list[SiteConfig]:
    """Parse a YAML config file and return a list of validated SiteConfig objects."""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    sites = []
    for entry in data["sites"]:
        # Catalog shorthand: { site: "connecting_ridge", extent: {...} }
        if "site" in entry:
            extent_raw = entry.get("extent", {})
            use_full = bool(extent_raw.get("use_full", True))

            bounding_box = None
            bb_raw = extent_raw.get("bounding_box")
            if bb_raw is not None:
                bounding_box = BoundingBox(
                    lat=float(bb_raw["lat"]),
                    lon=float(bb_raw["lon"]),
                    width_km=float(bb_raw.get("width_km", 10.0)),
                    height_km=float(bb_raw.get("height_km", 10.0)),
                )

            extent = Extent(use_full=use_full, bounding_box=bounding_box)
            config = SiteConfig.from_catalog(entry["site"], extent=extent)
            config.validate()
            sites.append(config)
            continue

        # Legacy explicit URL format: { name: ..., dem_url: ..., extent: {...} }
        extent_raw = entry.get("extent", {})
        use_full = bool(extent_raw.get("use_full", False))

        bounding_box = None
        bb_raw = extent_raw.get("bounding_box")
        if bb_raw is not None:
            bounding_box = BoundingBox(
                lat=float(bb_raw["lat"]),
                lon=float(bb_raw["lon"]),
                width_km=float(bb_raw.get("width_km", 10.0)),
                height_km=float(bb_raw.get("height_km", 10.0)),
            )

        config = SiteConfig(
            name=entry["name"],
            dem_url=entry["dem_url"],
            extent=Extent(use_full=use_full, bounding_box=bounding_box),
            description=entry.get("description", ""),
        )
        config.validate()
        sites.append(config)
    return sites
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest src/generate_lunar_sdf/test/test_site_config.py -v`
Expected: All tests PASS (existing + 7 new)

- [ ] **Step 6: Commit**

```bash
git add src/generate_lunar_sdf/generate_lunar_sdf/utils/site_config_parser.py \
        src/generate_lunar_sdf/test/test_site_config.py
git commit -m "feat: add SiteConfig.from_catalog(), slope_url, and YAML catalog shorthand

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 5: Pipeline Update — Slope Download + Texture Generation

**Files:**
- Modify: `src/generate_lunar_sdf/generate_lunar_sdf/generate_lunar_sdf.py`
- Modify: `src/generate_lunar_sdf/test/test_integration.py`

- [ ] **Step 1: Update test_integration.py**

Update both pipeline tests to add slope download mock and diffuse assertions.

Replace `TestIntegrationPipeline` with:

```python
class TestIntegrationPipeline:
    """End-to-end pipeline with mocked external dependencies."""

    def test_terrain_generator_creates_output_structure(self, tmp_path):
        """Verify GenerateLunarSDF produces model dir with expected files."""
        config = SiteConfig(
            name="test_site",
            dem_url="https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif",
            extent=Extent(
                use_full=False,
                bounding_box=BoundingBox(lat=-86.5, lon=-4.0, width_km=2.0, height_km=2.0),
            ),
        )

        output_dir = tmp_path / "output"
        cache_dir = tmp_path / "cache"
        output_dir.mkdir()
        cache_dir.mkdir()

        size = 513
        fake_heightmap = np.random.rand(size, size).astype(np.float64)
        fake_diffuse = np.random.randint(60, 190, (size, size, 3), dtype=np.uint8)

        with patch("generate_lunar_sdf.generate_lunar_sdf.FileDownloader") as mock_dl_cls, \
             patch("generate_lunar_sdf.generate_lunar_sdf.HeightmapGenerator") as mock_hm, \
             patch("generate_lunar_sdf.generate_lunar_sdf.SlopeTextureGenerator") as mock_slope:

            mock_dl_instance = MagicMock()
            mock_dl_instance.download.return_value = tmp_path / "fake.tif"
            mock_dl_cls.return_value = mock_dl_instance

            mock_hm.from_dem.return_value = (fake_heightmap, -500.0, 2000.0)
            mock_slope.from_slope_geotiff_cropped.return_value = fake_diffuse

            generator = GenerateLunarSDF(output_dir=output_dir, cache_dir=cache_dir)
            result = generator.generate(config)

        # Downloader called for both DEM and slope
        assert mock_dl_instance.download.call_count == 2

        model_dir = output_dir / "test_site"
        assert model_dir.exists()
        assert result == model_dir

        assert (model_dir / "model.sdf").exists()
        assert (model_dir / "model.config").exists()

        textures_dir = model_dir / "materials" / "textures"
        assert textures_dir.exists()
        assert (textures_dir / "heightmap.png").exists()
        assert (textures_dir / "diffuse.png").exists()
        assert (textures_dir / "normal.png").exists()

        sdf_content = (model_dir / "model.sdf").read_text()
        assert "test_site" in sdf_content
        assert "diffuse.png" in sdf_content
```

Replace `TestIntegrationFullExtentPipeline` with:

```python
class TestIntegrationFullExtentPipeline:
    """Pipeline test with use_full extent."""

    def test_full_extent_pipeline(self, tmp_path):
        """Verify GenerateLunarSDF uses from_dem_full_extent when extent.use_full=True."""
        config = SiteConfig(
            name="test_full_extent",
            dem_url="https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif",
            extent=Extent(use_full=True),
        )

        output_dir = tmp_path / "output"
        cache_dir = tmp_path / "cache"
        output_dir.mkdir()
        cache_dir.mkdir()

        size = 513
        fake_heightmap = np.random.rand(size, size).astype(np.float64)
        fake_diffuse = np.random.randint(60, 190, (size, size, 3), dtype=np.uint8)
        bounds = {"center_lat": -89.5, "center_lon": -130.0, "width_km": 20.0, "height_km": 15.0}

        with patch("generate_lunar_sdf.generate_lunar_sdf.FileDownloader") as mock_dl_cls, \
             patch("generate_lunar_sdf.generate_lunar_sdf.HeightmapGenerator") as mock_hm, \
             patch("generate_lunar_sdf.generate_lunar_sdf.SlopeTextureGenerator") as mock_slope:

            mock_dl_instance = MagicMock()
            mock_dl_instance.download.return_value = tmp_path / "fake.tif"
            mock_dl_cls.return_value = mock_dl_instance

            mock_hm.from_dem_full_extent.return_value = (
                fake_heightmap, -500.0, 2000.0, bounds
            )
            mock_slope.from_slope_geotiff.return_value = fake_diffuse

            generator = GenerateLunarSDF(output_dir=output_dir, cache_dir=cache_dir)
            result = generator.generate(config)

        mock_hm.from_dem_full_extent.assert_called_once()
        mock_hm.from_dem.assert_not_called()
        mock_slope.from_slope_geotiff.assert_called_once()

        assert mock_dl_instance.download.call_count == 2

        model_dir = output_dir / "test_full_extent"
        assert model_dir.exists()
        assert result == model_dir
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/generate_lunar_sdf/test/test_integration.py::TestIntegrationPipeline -v`
Expected: FAIL — SlopeTextureGenerator not imported in generate_lunar_sdf

- [ ] **Step 3: Update generate_lunar_sdf.py pipeline**

Add SlopeTextureGenerator import:

```python
from .map_generators.slope_texture_generator import SlopeTextureGenerator
```

Update `generate()` method:

```python
    def generate(self, site: SiteConfig) -> Path:
        """Generate a complete Gazebo terrain model for a site."""
        print(f"\n=== Generating: {site.name} ===")

        dem_file = self._downloader.download(site.dem_url)
        slope_file = self._downloader.download(site.slope_url)

        if site.extent.use_full:
            heightmap, elev_min, elev_max, bounds = (
                HeightmapGenerator.from_dem_full_extent(dem_file)
            )
            diffuse = SlopeTextureGenerator.from_slope_geotiff(
                slope_file, heightmap.shape[0], heightmap.shape[1]
            )
            lat = bounds["center_lat"]
            lon = bounds["center_lon"]
            width_km = bounds["width_km"]
            height_km = bounds["height_km"]
            print(f"    Full extent: center=({lat:.4f}, {lon:.4f}), "
                  f"{width_km:.1f}x{height_km:.1f}km")
        else:
            bb = site.extent.bounding_box
            heightmap, elev_min, elev_max = HeightmapGenerator.from_dem(
                dem_file, bb.lat, bb.lon, bb.width_km, bb.height_km
            )
            diffuse = SlopeTextureGenerator.from_slope_geotiff_cropped(
                slope_file, bb.lat, bb.lon, bb.width_km, bb.height_km,
                heightmap.shape[0], heightmap.shape[1]
            )
            lat = bb.lat
            lon = bb.lon
            width_km = bb.width_km
            height_km = bb.height_km
            print(f"    Lat: {lat}, Lon: {lon}, "
                  f"Region: {width_km}x{height_km}km")

        normal_map = NormalMapGenerator.from_heightmap(heightmap)

        size_x_m = int(width_km * 1000)
        size_y_m = int(height_km * 1000)
        model_dir = self._output_dir / site.name
        writer = ModelWriter(model_dir)
        writer.write(
            site_id=site.name,
            display_name=site.name.replace("_", " ").title(),
            description=site.description or f"Lunar terrain at ({lat}, {lon})",
            heightmap=heightmap,
            diffuse_map=diffuse,
            normal_map=normal_map,
            size_x_m=size_x_m,
            size_y_m=size_y_m,
            elevation_min=elev_min,
            elevation_max=elev_max,
            lat=lat,
            lon=lon,
            source="nasa_pgda_78",
        )
        return model_dir
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest src/generate_lunar_sdf/test/test_integration.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/generate_lunar_sdf/generate_lunar_sdf/generate_lunar_sdf.py \
        src/generate_lunar_sdf/test/test_integration.py
git commit -m "feat: add slope texture generation to terrain pipeline

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 6: CLI Redesign — Site-Centric with Interactive Selection

**Files:**
- Modify: `src/generate_lunar_sdf/generate_lunar_sdf/generate_lunar_sdf.py`
- Modify: `src/generate_lunar_sdf/test/test_cli.py`

- [ ] **Step 1: Rewrite test_cli.py**

Replace the entire file with:

```python
"""Tests for the CLI argument parsing and interactive mode."""

import pytest
from unittest.mock import patch

from generate_lunar_sdf.generate_lunar_sdf import GenerateLunarSDF


class TestCLISiteMode:
    def test_site_mode_full_extent(self):
        parser = GenerateLunarSDF._build_parser()
        args = parser.parse_args([
            "--site", "connecting_ridge",
            "--output-dir", "/tmp/out",
        ])
        assert args.site == "connecting_ridge"
        assert args.output_dir == "/tmp/out"
        assert args.lat is None
        assert args.lon is None

    def test_site_mode_with_crop(self):
        parser = GenerateLunarSDF._build_parser()
        args = parser.parse_args([
            "--site", "shackleton_rim",
            "--lat", "-86.5",
            "--lon", "-4.0",
            "--width", "5.0",
            "--height", "5.0",
            "--output-dir", "/tmp/out",
        ])
        assert args.site == "shackleton_rim"
        assert args.lat == -86.5
        assert args.width == 5.0

    def test_site_mode_explicit_full_extent(self):
        parser = GenerateLunarSDF._build_parser()
        args = parser.parse_args([
            "--site", "peak_near_shackleton",
            "--use-full-extent",
            "--output-dir", "/tmp/out",
        ])
        assert args.site == "peak_near_shackleton"
        assert args.use_full_extent is True


class TestCLIConfigMode:
    def test_config_mode(self):
        parser = GenerateLunarSDF._build_parser()
        args = parser.parse_args([
            "--config", "sites.yaml",
            "--output-dir", "/tmp/out",
        ])
        assert args.config == "sites.yaml"
        assert args.output_dir == "/tmp/out"


class TestCLIMutualExclusion:
    def test_config_and_site_together_fails(self):
        parser = GenerateLunarSDF._build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([
                "--config", "sites.yaml",
                "--site", "bad",
                "--output-dir", "/tmp/out",
            ])


class TestCLIInteractiveMode:
    def test_no_mode_gives_interactive(self):
        """When neither --site nor --config given, args.site and args.config are both None."""
        parser = GenerateLunarSDF._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/out"])
        assert args.site is None
        assert args.config is None

    def test_interactive_list_sites(self):
        """_interactive_select should list all 27 sites and return a SiteConfig."""
        inputs = iter(["1", "1"])
        with patch("builtins.input", side_effect=inputs):
            config = GenerateLunarSDF._interactive_select()
        assert config.name == "connecting_ridge"
        assert config.extent.use_full is True

    def test_interactive_select_by_name(self):
        inputs = iter(["shackleton_rim", "1"])
        with patch("builtins.input", side_effect=inputs):
            config = GenerateLunarSDF._interactive_select()
        assert config.name == "shackleton_rim"

    def test_interactive_custom_bbox(self):
        inputs = iter(["1", "2", "-86.5", "-4.0", "5.0", "5.0"])
        with patch("builtins.input", side_effect=inputs):
            config = GenerateLunarSDF._interactive_select()
        assert config.extent.use_full is False
        assert config.extent.bounding_box.lat == -86.5
        assert config.extent.bounding_box.width_km == 5.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/generate_lunar_sdf/test/test_cli.py -v`
Expected: FAIL — parser structure changed, `_interactive_select` not found

- [ ] **Step 3: Rewrite CLI in generate_lunar_sdf.py**

Replace `_build_parser()` and `from_cli()` methods. Add `_interactive_select()`:

```python
    @classmethod
    def _build_parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Generate Gazebo SDF terrain models from PGDA Product 78 LOLA DEMs.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                "Site mode (single site from catalog):\n"
                "  generate_lunar_sdf --site connecting_ridge --output-dir ./models\n"
                "  generate_lunar_sdf --site shackleton_rim --lat -86.5 --lon -4.0 "
                "--width 5 --height 5 --output-dir ./models\n"
                "\n"
                "Config mode (batch from YAML):\n"
                "  generate_lunar_sdf --config sites.yaml --output-dir ./models\n"
                "\n"
                "Interactive mode (no --site or --config):\n"
                "  generate_lunar_sdf --output-dir ./models\n"
            ),
        )

        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--config", type=str, metavar="FILE",
            help="Path to YAML site configuration file (batch mode)",
        )
        mode.add_argument(
            "--site", type=str,
            help="Site name from PGDA-78 catalog (e.g., connecting_ridge)",
        )

        parser.add_argument(
            "--output-dir", type=str, required=True,
            help="Output directory for generated models",
        )
        parser.add_argument(
            "--cache-dir", type=str, default=None,
            help="Cache directory for downloaded data (default: <repo>/data/)",
        )

        # Extent options for --site mode
        parser.add_argument("--lat", type=float, help="Center latitude for crop")
        parser.add_argument("--lon", type=float, help="Center longitude for crop")
        parser.add_argument(
            "--width", type=float, default=10.0,
            help="Region width in km (default: 10)",
        )
        parser.add_argument(
            "--height", type=float, default=10.0,
            help="Region height in km (default: 10)",
        )
        parser.add_argument(
            "--use-full-extent", action="store_true", default=False,
            help="Use the entire DEM tile (default when --lat/--lon not given)",
        )

        return parser

    @staticmethod
    def _interactive_select() -> SiteConfig:
        """Interactively select a site and extent."""
        from .utils.site_catalog import list_sites as list_catalog_sites

        catalog = list_catalog_sites()
        print("\nAvailable PGDA-78 Sites:")
        for i, site in enumerate(catalog, 1):
            print(f"  {i:>2}. {site.name:<28} {site.pgda_id} – {site.display_name}")

        choice = input("\nSelect site (number or name): ").strip()
        selected = None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(catalog):
                selected = catalog[idx]
        except ValueError:
            for site in catalog:
                if site.name == choice:
                    selected = site
                    break
        if selected is None:
            raise ValueError(f"Invalid selection: {choice!r}")

        print(f"\nSelected: {selected.display_name} ({selected.pgda_id})")
        extent_choice = input(
            "\nExtent:\n  1. Full tile (recommended)\n  2. Custom bounding box\nSelect: "
        ).strip()

        if extent_choice == "2":
            lat = float(input("Center latitude: ").strip())
            lon = float(input("Center longitude: ").strip())
            width = float(input("Width (km): ").strip())
            height = float(input("Height (km): ").strip())
            extent = Extent(
                use_full=False,
                bounding_box=BoundingBox(lat=lat, lon=lon, width_km=width, height_km=height),
            )
        else:
            extent = Extent(use_full=True)

        return SiteConfig.from_catalog(selected.name, extent=extent)

    @classmethod
    def from_cli(cls, argv: list[str] | None = None) -> None:
        """Parse CLI arguments and run the terrain generation pipeline."""
        parser = cls._build_parser()
        args = parser.parse_args(argv)

        output_dir = Path(args.output_dir)
        cache_dir = Path(args.cache_dir) if args.cache_dir else cls._default_cache_dir()

        generator = cls(output_dir=output_dir, cache_dir=cache_dir)

        if args.config:
            config_path = Path(args.config)
            sites = load_sites(config_path)
            for site in sites:
                generator.generate(site)
        elif args.site:
            # Determine extent from flags
            if args.lat is not None and args.lon is not None:
                extent = Extent(
                    use_full=False,
                    bounding_box=BoundingBox(
                        lat=args.lat,
                        lon=args.lon,
                        width_km=args.width,
                        height_km=args.height,
                    ),
                )
            else:
                extent = Extent(use_full=True)
            site = SiteConfig.from_catalog(args.site, extent=extent)
            site.validate()
            generator.generate(site)
        else:
            # Interactive mode
            site = cls._interactive_select()
            site.validate()
            generator.generate(site)

        print("\nDone!")
```

Note: `--use-full-extent` defaults to `True` now and is implicit. The presence of
`--lat`/`--lon` triggers crop mode instead.

- [ ] **Step 4: Run tests**

Run: `python -m pytest src/generate_lunar_sdf/test/test_cli.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest src/generate_lunar_sdf/test/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/generate_lunar_sdf/generate_lunar_sdf/generate_lunar_sdf.py \
        src/generate_lunar_sdf/test/test_cli.py
git commit -m "feat: redesign CLI with site catalog selection and interactive mode

Three modes: --site <name> (catalog), --config <file> (batch YAML),
or interactive selection when neither is given. Removes --name and
--dem-url. URLs are now derived from the PGDA-78 site catalog.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 7: Config, README, Pre-built Models, and Final Verification

**Files:**
- Modify: `src/generate_lunar_sdf/config/artemis_sites.yaml`
- Modify: `src/generate_lunar_sdf/generate_lunar_sdf/__init__.py`
- Modify: `src/generate_lunar_sdf/README.md`
- Modify: 4 pre-built `model.sdf` files
- Modify: `src/generate_lunar_sdf/test/test_integration.py` (config load test)

- [ ] **Step 1: Update artemis_sites.yaml to catalog shorthand**

Replace `src/generate_lunar_sdf/config/artemis_sites.yaml` with:

```yaml
# Barker et al. (2021) Improved LOLA Elevation Maps for South Pole Landing Sites
# Paper: https://doi.org/10.1016/j.pss.2020.105119
# DEM data: NASA PGDA Product 78 – https://pgda.gsfc.nasa.gov/products/78
# 5 m/pix, south polar stereographic, track-adjusted (~2-4 cm vertical)

sites:
  - site: connecting_ridge
    extent:
      use_full: true

  - site: shackleton_rim
    extent:
      use_full: true

  - site: peak_near_shackleton
    extent:
      use_full: true

  - site: de_gerlache_rim
    extent:
      use_full: true
```

- [ ] **Step 2: Verify config loads correctly**

Run: `python -m pytest src/generate_lunar_sdf/test/test_integration.py::TestIntegrationConfigLoad -v`
Expected: All 3 config load tests PASS

- [ ] **Step 3: Update package __init__.py exports**

Replace `src/generate_lunar_sdf/generate_lunar_sdf/__init__.py` with:

```python
"""Lunar terrain generation tool for Gazebo Harmonic."""

from .utils.site_config_parser import BoundingBox, Extent, SiteConfig, load_sites, load_site
from .utils.site_catalog import CatalogSite, SITE_CATALOG, list_sites, get_site
from .generate_lunar_sdf import GenerateLunarSDF

__all__ = [
    "BoundingBox", "Extent", "SiteConfig", "load_sites", "load_site",
    "CatalogSite", "SITE_CATALOG", "list_sites", "get_site",
    "GenerateLunarSDF",
]
```

- [ ] **Step 4: Re-add `<diffuse>` to 4 pre-built model SDF files**

For each of these files, add the `<diffuse>` line before `<normal>`:
- `src/generate_lunar_sdf/models/connecting_ridge/model.sdf`
- `src/generate_lunar_sdf/models/shackleton_rim/model.sdf`
- `src/generate_lunar_sdf/models/peak_near_shackleton/model.sdf`
- `src/generate_lunar_sdf/models/de_gerlache_rim/model.sdf`

Change:
```xml
            <texture>
              <normal>model://SITE_NAME/materials/textures/normal.png</normal>
              <size>10</size>
            </texture>
```
to:
```xml
            <texture>
              <diffuse>model://SITE_NAME/materials/textures/diffuse.png</diffuse>
              <normal>model://SITE_NAME/materials/textures/normal.png</normal>
              <size>10</size>
            </texture>
```
(Replace `SITE_NAME` with the actual site name in each file.)

- [ ] **Step 5: Update README.md**

Rewrite `src/generate_lunar_sdf/README.md` to cover:
- New description: heightmap + slope-derived diffuse texture + normal map
- Three CLI modes (interactive, --site, --config)
- Catalog shorthand YAML format
- Site table (all 27 sites)
- Slope texture explanation
- Updated examples

- [ ] **Step 6: Run full test suite and grep for stale references**

```bash
python -m pytest src/generate_lunar_sdf/test/ -v
grep -rn "AlbedoGenerator\|--dem-url\|--name\|lroc\|pds3" src/generate_lunar_sdf/ --include="*.py"
```

Expected: All tests PASS, grep finds zero stale references.

- [ ] **Step 7: Commit**

```bash
git add src/generate_lunar_sdf/config/artemis_sites.yaml \
        src/generate_lunar_sdf/generate_lunar_sdf/__init__.py \
        src/generate_lunar_sdf/README.md \
        src/generate_lunar_sdf/models/
git commit -m "docs: update config, README, pre-built models for site catalog and slope texture

Convert artemis_sites.yaml to catalog shorthand. Add site catalog and
SlopeTextureGenerator exports. Re-add <diffuse> to pre-built model SDFs.
Rewrite README for site-centric workflow.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

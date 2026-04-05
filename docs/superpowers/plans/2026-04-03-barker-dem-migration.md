# Barker DEM Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded PDS3 DEM assumptions with metadata-driven rasterio reads, switch to Barker et al. (2021) per-site GeoTIFFs for 4 landing sites, and update all config/docs/tests.

**Architecture:** The `HeightmapGenerator` class gains a `from_dem_full_extent()` method and reads scale/nodata from rasterio metadata instead of hardcoding PDS3 values. `SiteConfig` adds a `use_full_extent` boolean that makes lat/lon optional. `TerrainGenerator` branches on this flag to either crop a region or use the full DEM extent, deriving albedo coordinates from the DEM bounds.

**Tech Stack:** Python 3.12, rasterio, numpy, pytest, ROS 2 ament_python

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py` | Modify | Add `stereo_to_latlon()`, `_read_elevations()`, `from_dem_full_extent()`; refactor `from_dem()` |
| `src/lunar_terrain_generator/lunar_terrain_generator/site_config.py` | Modify | Add `use_full_extent` field, make lat/lon optional |
| `src/lunar_terrain_generator/lunar_terrain_generator/terrain_generator.py` | Modify | Branch on `use_full_extent`, derive albedo coords from DEM bounds |
| `src/lunar_terrain_generator/lunar_terrain_generator/cli.py` | Modify | Add `--use-full-extent` flag, update epilog examples |
| `src/lunar_terrain_generator/config/artemis_sites.yaml` | Modify | Replace 13 sites with 4 Barker sites |
| `src/lunar_terrain_generator/test/test_heightmap.py` | Modify | Add tests for `stereo_to_latlon`, `_read_elevations`, `from_dem_full_extent` |
| `src/lunar_terrain_generator/test/test_site_config.py` | Modify | Add `use_full_extent` tests, update validation tests |
| `src/lunar_terrain_generator/test/test_cli.py` | Modify | Add `--use-full-extent` test, update example site names |
| `src/lunar_terrain_generator/test/test_integration.py` | Modify | Update site count/names, add `use_full_extent` pipeline test |
| `src/artemis_mission_launcher/launch/lunar_surface.launch.py` | Modify | Update default site and description |
| `src/lunar_terrain_generator/models/` | Modify | Remove old models, add/rename for new 4 sites |
| `README.md` | Modify | Update site table, examples, add citation |
| `src/lunar_terrain_generator/README.md` | Modify | Update DEM table, examples, add citation |

---

### Task 1: Add `stereo_to_latlon()` inverse projection to HeightmapGenerator

**Files:**
- Modify: `src/lunar_terrain_generator/test/test_heightmap.py`
- Modify: `src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py`

- [ ] **Step 1: Write failing tests for `stereo_to_latlon`**

Add this test class to `test_heightmap.py`, after the existing `TestPolarStereographicConversion` class:

```python
class TestInversePolarStereographic:
    """Test the polar stereographic (x, y) to lat/lon conversion."""

    def test_origin_maps_to_south_pole(self):
        """(0, 0) in stereo should map back to -90 lat."""
        lat, lon = HeightmapGenerator.stereo_to_latlon(0.0, 0.0)
        assert lat == pytest.approx(-90.0, abs=0.01)

    def test_roundtrip_known_point(self):
        """latlon_to_stereo then stereo_to_latlon should return the original coords."""
        orig_lat, orig_lon = -85.0, 45.0
        x, y = HeightmapGenerator.latlon_to_stereo(orig_lat, orig_lon)
        lat, lon = HeightmapGenerator.stereo_to_latlon(x, y)
        assert lat == pytest.approx(orig_lat, abs=0.01)
        assert lon == pytest.approx(orig_lon, abs=0.01)

    def test_roundtrip_near_pole(self):
        """Roundtrip for a point very near the south pole."""
        orig_lat, orig_lon = -89.5, -60.0
        x, y = HeightmapGenerator.latlon_to_stereo(orig_lat, orig_lon)
        lat, lon = HeightmapGenerator.stereo_to_latlon(x, y)
        assert lat == pytest.approx(orig_lat, abs=0.01)
        assert lon == pytest.approx(orig_lon, abs=0.1)

    def test_roundtrip_multiple_longitudes(self):
        """Roundtrip across different longitudes."""
        for orig_lon in [-180.0, -90.0, 0.0, 90.0, 130.0]:
            x, y = HeightmapGenerator.latlon_to_stereo(-87.0, orig_lon)
            lat, lon = HeightmapGenerator.stereo_to_latlon(x, y)
            assert lat == pytest.approx(-87.0, abs=0.01)
            # Normalize longitude comparison to [-180, 180]
            diff = (lon - orig_lon + 180) % 360 - 180
            assert abs(diff) < 0.1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_heightmap.py::TestInversePolarStereographic -v`
Expected: FAIL — `AttributeError: type object 'HeightmapGenerator' has no attribute 'stereo_to_latlon'`

- [ ] **Step 3: Implement `stereo_to_latlon`**

Add this staticmethod to `HeightmapGenerator` in `heightmap.py`, right after the existing `latlon_to_stereo` method:

```python
    @staticmethod
    def stereo_to_latlon(x: float, y: float) -> tuple[float, float]:
        """Convert lunar south pole stereographic (x, y) to geographic lat/lon.

        Inverse of latlon_to_stereo(). Returns (lat, lon) in degrees.
        """
        r = math.sqrt(x**2 + y**2)
        if r < 1e-10:
            return -90.0, 0.0
        colat = 2.0 * math.atan2(r, 2.0 * _LUNAR_RADIUS_M)
        lat = math.degrees(-(math.pi / 2 + colat))
        lon = math.degrees(math.atan2(x, y))
        return lat, lon
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_heightmap.py -v`
Expected: All tests PASS (existing + new)

- [ ] **Step 5: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py src/lunar_terrain_generator/test/test_heightmap.py
git commit -m "feat(heightmap): add stereo_to_latlon inverse projection

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: Add metadata-driven `_read_elevations()` to HeightmapGenerator

**Files:**
- Modify: `src/lunar_terrain_generator/test/test_heightmap.py`
- Modify: `src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py`

- [ ] **Step 1: Write failing tests for `_read_elevations`**

Add this test class to `test_heightmap.py`:

```python
class TestReadElevations:
    """Test metadata-driven elevation reading from rasterio datasets."""

    def test_float_data_no_scaling(self):
        """Float GeoTIFF data should be used as-is (no PDS3 scaling)."""
        raw = np.array([[100.5, 200.3], [150.7, -9999.0]], dtype=np.float32)
        elevations = HeightmapGenerator._read_elevations(raw, nodata=-9999.0, scale=1.0, offset=0.0)
        assert elevations[0, 0] == pytest.approx(100.5, abs=0.1)
        assert elevations[1, 0] == pytest.approx(150.7, abs=0.1)
        assert np.isnan(elevations[1, 1])

    def test_int16_with_scale(self):
        """int16 data with scale=0.5 should be equivalent to PDS3 scaling."""
        raw = np.array([[100, 200], [300, -32768]], dtype=np.int16)
        elevations = HeightmapGenerator._read_elevations(raw, nodata=-32768, scale=0.5, offset=0.0)
        assert elevations[0, 0] == pytest.approx(50.0)
        assert elevations[0, 1] == pytest.approx(100.0)
        assert np.isnan(elevations[1, 1])

    def test_scale_and_offset(self):
        """Scale and offset should both be applied: elevation = raw * scale + offset."""
        raw = np.array([[10, 20]], dtype=np.int16)
        elevations = HeightmapGenerator._read_elevations(raw, nodata=None, scale=2.0, offset=100.0)
        assert elevations[0, 0] == pytest.approx(120.0)
        assert elevations[0, 1] == pytest.approx(140.0)

    def test_no_nodata(self):
        """When nodata is None, no pixels should become NaN."""
        raw = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        elevations = HeightmapGenerator._read_elevations(raw, nodata=None, scale=1.0, offset=0.0)
        assert not np.any(np.isnan(elevations))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_heightmap.py::TestReadElevations -v`
Expected: FAIL — `AttributeError: type object 'HeightmapGenerator' has no attribute '_read_elevations'`

- [ ] **Step 3: Implement `_read_elevations`**

Add this staticmethod to `HeightmapGenerator` in `heightmap.py`, after the existing `apply_pds3_scaling` method:

```python
    @staticmethod
    def _read_elevations(
        raw: np.ndarray,
        nodata: float | int | None,
        scale: float = 1.0,
        offset: float = 0.0,
    ) -> np.ndarray:
        """Convert raw raster values to elevation in meters using dataset metadata.

        elevation_m = raw * scale + offset
        Pixels matching nodata become NaN.
        """
        result = raw.astype(np.float64) * scale + offset
        if nodata is not None:
            nodata_mask = np.isclose(raw.astype(np.float64), float(nodata))
            result[nodata_mask] = np.nan
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_heightmap.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py src/lunar_terrain_generator/test/test_heightmap.py
git commit -m "feat(heightmap): add metadata-driven _read_elevations method

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 3: Refactor `from_dem()` to use metadata-driven scaling

**Files:**
- Modify: `src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py`

- [ ] **Step 1: Refactor `from_dem` to use `_read_elevations`**

Replace the `from_dem` method body in `heightmap.py`. The method signature stays the same. Replace the entire method (lines 74-127) with:

```python
    @staticmethod
    def from_dem(
        dem_path: Path,
        lat: float,
        lon: float,
        region_size_km: float,
    ) -> tuple[np.ndarray, float, float]:
        """Crop a region from a polar DEM and return a heightmap.

        Reads nodata, scale, and offset from the dataset metadata rather
        than assuming a fixed format.  Works with both PDS3 .img files
        and GeoTIFF products.

        Args:
            dem_path: Local path to the DEM file.
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

            nodata = src.nodata
            scale = src.scales[0] if src.scales else 1.0
            offset = src.offsets[0] if src.offsets else 0.0

        elevations = HeightmapGenerator._read_elevations(raw, nodata, scale, offset)

        elev_min = float(np.nanmin(elevations))
        elev_max = float(np.nanmax(elevations))
        heightmap = HeightmapGenerator.normalize(elevations)

        return heightmap, elev_min, elev_max
```

- [ ] **Step 2: Run all tests to verify nothing is broken**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/ -v`
Expected: All 47+ tests PASS (the integration test mocks `HeightmapGenerator.from_dem` so the signature change is transparent)

- [ ] **Step 3: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py
git commit -m "refactor(heightmap): use metadata-driven scaling in from_dem

Read nodata, scale, offset from rasterio dataset metadata instead of
hardcoding PDS3 int16 assumptions. Works with both PDS3 and GeoTIFF.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: Add `from_dem_full_extent()` to HeightmapGenerator

**Files:**
- Modify: `src/lunar_terrain_generator/test/test_heightmap.py`
- Modify: `src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py`

- [ ] **Step 1: Write failing test for `from_dem_full_extent`**

This test creates a real in-memory GeoTIFF using rasterio to verify the full-extent read path. Add to `test_heightmap.py`:

```python
class TestFromDemFullExtent:
    """Test reading a full DEM tile without lat/lon cropping."""

    def _make_test_geotiff(self, tmp_path: Path, size: int = 64) -> Path:
        """Create a small GeoTIFF in south polar stereographic with known values."""
        import rasterio
        from rasterio.transform import from_bounds

        dem_path = tmp_path / "test_dem.tif"
        # 1km x 1km tile centered at stereo origin (south pole)
        transform = from_bounds(-500, -500, 500, 500, size, size)
        data = np.linspace(-100.0, 200.0, size * size, dtype=np.float32).reshape(size, size)

        with rasterio.open(
            dem_path, "w", driver="GTiff", height=size, width=size,
            count=1, dtype="float32",
            crs="EPSG:3031",  # Antarctic polar stereographic (close enough for test)
            transform=transform, nodata=-9999.0,
        ) as dst:
            dst.write(data, 1)
        return dem_path

    def test_returns_heightmap_and_bounds(self, tmp_path):
        """from_dem_full_extent should return heightmap, elevation range, and geographic bounds."""
        dem_path = self._make_test_geotiff(tmp_path)
        heightmap, elev_min, elev_max, bounds = HeightmapGenerator.from_dem_full_extent(dem_path)

        # Heightmap should be normalized [0, 1] and resized to 2^n+1
        assert heightmap.ndim == 2
        assert heightmap.shape[0] == heightmap.shape[1]
        assert heightmap.shape[0] in [3, 5, 9, 17, 33, 65, 129]  # 2^n+1
        assert heightmap.min() == pytest.approx(0.0, abs=0.01)
        assert heightmap.max() == pytest.approx(1.0, abs=0.01)

        # Elevation range should match the data we wrote
        assert elev_min == pytest.approx(-100.0, abs=1.0)
        assert elev_max == pytest.approx(200.0, abs=1.0)

        # Bounds should have center_lat, center_lon, size_km
        assert "center_lat" in bounds
        assert "center_lon" in bounds
        assert "size_km" in bounds
        assert bounds["size_km"] == pytest.approx(1.0, abs=0.1)
```

Add `from pathlib import Path` to the test file imports if not already present, and add `import pytest` if not already present.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_heightmap.py::TestFromDemFullExtent -v`
Expected: FAIL — `AttributeError: type object 'HeightmapGenerator' has no attribute 'from_dem_full_extent'`

- [ ] **Step 3: Implement `from_dem_full_extent`**

Add this staticmethod to `HeightmapGenerator` in `heightmap.py`, after the `from_dem` method:

```python
    @staticmethod
    def from_dem_full_extent(
        dem_path: Path,
    ) -> tuple[np.ndarray, float, float, dict]:
        """Read an entire DEM file and return a heightmap with geographic bounds.

        For use with pre-cropped per-site DEM tiles where lat/lon cropping
        is not needed.

        Returns:
            (heightmap_float64_01, elevation_min_m, elevation_max_m, bounds)
            bounds is a dict with keys: center_lat, center_lon, size_km
        """
        import rasterio
        from rasterio.enums import Resampling

        with rasterio.open(dem_path) as src:
            raw_size = max(src.width, src.height)
            target_size = HeightmapGenerator.nearest_gazebo_size(raw_size)

            raw = src.read(
                1,
                out_shape=(target_size, target_size),
                resampling=Resampling.bilinear,
            )

            nodata = src.nodata
            scale = src.scales[0] if src.scales else 1.0
            offset = src.offsets[0] if src.offsets else 0.0

            # Derive geographic bounds from the raster extent
            raster_bounds = src.bounds
            x_min, y_min = raster_bounds.left, raster_bounds.bottom
            x_max, y_max = raster_bounds.right, raster_bounds.top

        elevations = HeightmapGenerator._read_elevations(raw, nodata, scale, offset)

        elev_min = float(np.nanmin(elevations))
        elev_max = float(np.nanmax(elevations))
        heightmap = HeightmapGenerator.normalize(elevations)

        x_center = (x_min + x_max) / 2.0
        y_center = (y_min + y_max) / 2.0
        center_lat, center_lon = HeightmapGenerator.stereo_to_latlon(x_center, y_center)
        size_m = max(x_max - x_min, y_max - y_min)

        bounds = {
            "center_lat": center_lat,
            "center_lon": center_lon,
            "size_km": size_m / 1000.0,
        }

        return heightmap, elev_min, elev_max, bounds
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_heightmap.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py src/lunar_terrain_generator/test/test_heightmap.py
git commit -m "feat(heightmap): add from_dem_full_extent for pre-cropped tiles

Reads entire DEM tile, derives geographic bounds from raster extent
for use with Barker per-site GeoTIFFs.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 5: Update `SiteConfig` to support `use_full_extent`

**Files:**
- Modify: `src/lunar_terrain_generator/test/test_site_config.py`
- Modify: `src/lunar_terrain_generator/lunar_terrain_generator/site_config.py`

- [ ] **Step 1: Write failing tests for `use_full_extent` support**

Add these tests to `test_site_config.py` inside the existing `TestSiteConfig` class:

```python
    def test_create_with_use_full_extent(self):
        config = SiteConfig(
            name="test_site",
            dem_url="https://example.com/dem.tif",
            use_full_extent=True,
        )
        assert config.use_full_extent is True
        assert config.lat is None
        assert config.lon is None

    def test_validate_full_extent_without_latlon(self):
        """use_full_extent=True should not require lat/lon."""
        config = SiteConfig(
            name="test_site",
            dem_url="https://example.com/dem.tif",
            use_full_extent=True,
        )
        config.validate()  # Should not raise

    def test_validate_full_extent_ignores_region_size(self):
        """use_full_extent=True should skip region_size_km validation."""
        config = SiteConfig(
            name="test_site",
            dem_url="https://example.com/dem.tif",
            use_full_extent=True,
            region_size_km=0,
        )
        config.validate()  # Should not raise

    def test_validate_cropped_still_requires_latlon(self):
        """use_full_extent=False (default) must still require lat/lon."""
        with pytest.raises(ValueError, match="lat"):
            SiteConfig(
                name="test_site",
                dem_url="https://example.com/dem.tif",
            ).validate()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_site_config.py::TestSiteConfig::test_create_with_use_full_extent src/lunar_terrain_generator/test/test_site_config.py::TestSiteConfig::test_validate_full_extent_without_latlon src/lunar_terrain_generator/test/test_site_config.py::TestSiteConfig::test_validate_full_extent_ignores_region_size src/lunar_terrain_generator/test/test_site_config.py::TestSiteConfig::test_validate_cropped_still_requires_latlon -v`
Expected: FAIL — `TypeError: SiteConfig.__init__() missing required argument: 'lat'` (or similar)

- [ ] **Step 3: Update `SiteConfig` dataclass**

Replace the entire `SiteConfig` class and `validate` method in `site_config.py`:

```python
@dataclass
class SiteConfig:
    """Configuration for a single terrain generation site."""

    name: str
    dem_url: str
    lat: float | None = None
    lon: float | None = None
    region_size_km: float = 10.0
    lroc_url: str = field(default_factory=lambda: DEFAULT_LROC_WAC_URL)
    description: str = ""
    use_full_extent: bool = False

    def validate(self) -> None:
        """Validate configuration values. Raises ValueError on invalid data."""
        if not self.name or not _VALID_NAME_RE.match(self.name):
            raise ValueError(
                f"name must be non-empty and contain only alphanumeric, "
                f"hyphens, or underscores (got: {self.name!r})"
            )
        if not self.dem_url:
            raise ValueError("dem_url must be a non-empty string")

        if not self.use_full_extent:
            if self.lat is None:
                raise ValueError("lat is required when use_full_extent is False")
            if self.lon is None:
                raise ValueError("lon is required when use_full_extent is False")
            if self.lat > -80.0:
                raise ValueError(
                    f"lat must be <= -80.0 for south pole DEMs (got: {self.lat})"
                )
            if self.region_size_km <= 0:
                raise ValueError(
                    f"region_size_km must be > 0 (got: {self.region_size_km})"
                )
```

- [ ] **Step 4: Update `load_sites` to parse `use_full_extent`**

Replace the `load_sites` function in `site_config.py`:

```python
def load_sites(config_path: Path) -> list[SiteConfig]:
    """Parse a YAML config file and return a list of validated SiteConfig objects."""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    sites = []
    for entry in data["sites"]:
        lat_raw = entry.get("lat")
        lon_raw = entry.get("lon")
        config = SiteConfig(
            name=entry["name"],
            dem_url=entry["dem_url"],
            lat=float(lat_raw) if lat_raw is not None else None,
            lon=float(lon_raw) if lon_raw is not None else None,
            region_size_km=float(entry.get("region_size_km", 10.0)),
            lroc_url=entry.get("lroc_url", DEFAULT_LROC_WAC_URL),
            description=entry.get("description", ""),
            use_full_extent=bool(entry.get("use_full_extent", False)),
        )
        config.validate()
        sites.append(config)
    return sites
```

- [ ] **Step 5: Fix existing tests that pass `lat` as positional argument**

Several existing tests create `SiteConfig(name=..., lat=..., lon=..., dem_url=...)` with lat/lon as positional args. Since we changed the field order (lat/lon are now after dem_url), update these to use keyword arguments.

In `test_site_config.py`, update `test_create_with_required_fields`:

```python
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
        assert config.use_full_extent is False
```

The other tests in `TestSiteConfig` and `TestLoadSites` already use keyword arguments, so they should continue to work. Verify by running all tests.

- [ ] **Step 6: Run all tests**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_site_config.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add src/lunar_terrain_generator/lunar_terrain_generator/site_config.py src/lunar_terrain_generator/test/test_site_config.py
git commit -m "feat(site_config): add use_full_extent support

When use_full_extent=True, lat/lon are optional and region_size_km
validation is skipped. For use with pre-cropped per-site DEM tiles.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 6: Update `TerrainGenerator` to branch on `use_full_extent`

**Files:**
- Modify: `src/lunar_terrain_generator/test/test_integration.py`
- Modify: `src/lunar_terrain_generator/lunar_terrain_generator/terrain_generator.py`

- [ ] **Step 1: Write failing test for `use_full_extent` pipeline path**

Add this test to `TestIntegrationPipeline` class in `test_integration.py`:

```python
    def test_terrain_generator_full_extent_pipeline(self, tmp_path):
        """Verify TerrainGenerator works with use_full_extent=True."""
        config = SiteConfig(
            name="full_extent_test",
            dem_url="https://example.com/site01.tif",
            use_full_extent=True,
            description="Test full extent",
        )

        output_dir = tmp_path / "output"
        cache_dir = tmp_path / "cache"
        output_dir.mkdir()
        cache_dir.mkdir()

        size = 513
        fake_heightmap = np.random.rand(size, size).astype(np.float64)
        fake_albedo = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)
        fake_bounds = {"center_lat": -89.0, "center_lon": -60.0, "size_km": 20.0}

        with patch("lunar_terrain_generator.terrain_generator.FileDownloader") as mock_dl_cls, \
             patch("lunar_terrain_generator.terrain_generator.HeightmapGenerator") as mock_hm, \
             patch("lunar_terrain_generator.terrain_generator.AlbedoGenerator") as mock_alb:

            mock_dl_instance = MagicMock()
            mock_dl_instance.download.return_value = tmp_path / "fake.tif"
            mock_dl_cls.return_value = mock_dl_instance

            mock_hm.from_dem_full_extent.return_value = (fake_heightmap, -500.0, 2000.0, fake_bounds)
            mock_alb.from_geotiff.return_value = fake_albedo

            generator = TerrainGenerator(output_dir=output_dir, cache_dir=cache_dir)
            result = generator.generate(config)

        model_dir = output_dir / "full_extent_test"
        assert model_dir.exists()
        assert result == model_dir
        assert (model_dir / "model.sdf").exists()
        assert (model_dir / "materials" / "textures" / "heightmap.png").exists()

        # Verify from_dem_full_extent was called (not from_dem)
        mock_hm.from_dem_full_extent.assert_called_once()
        mock_hm.from_dem.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_integration.py::TestIntegrationPipeline::test_terrain_generator_full_extent_pipeline -v`
Expected: FAIL — `from_dem_full_extent` not called by the generator (it always calls `from_dem`)

- [ ] **Step 3: Update `TerrainGenerator.generate()`**

Replace the `generate` method in `terrain_generator.py`:

```python
    def generate(self, site: SiteConfig) -> Path:
        """Generate a complete Gazebo terrain model for a site.

        Returns the path to the generated model directory.
        """
        print(f"\n=== Generating: {site.name} ===")

        dem_file = self._downloader.download(site.dem_url)

        if site.use_full_extent:
            print(f"    Using full DEM extent")
            heightmap, elev_min, elev_max, bounds = HeightmapGenerator.from_dem_full_extent(
                dem_file
            )
            lat = bounds["center_lat"]
            lon = bounds["center_lon"]
            size_m = int(bounds["size_km"] * 1000)
        else:
            print(f"    Lat: {site.lat}, Lon: {site.lon}, "
                  f"Region: {site.region_size_km}km")
            heightmap, elev_min, elev_max = HeightmapGenerator.from_dem(
                dem_file, site.lat, site.lon, site.region_size_km
            )
            lat = site.lat
            lon = site.lon
            size_m = int(site.region_size_km * 1000)

        lroc_file = self._downloader.download(site.lroc_url)
        resolution = heightmap.shape[0]
        region_size_km = size_m / 1000.0
        albedo = AlbedoGenerator.from_geotiff(
            lroc_file, lat, lon, region_size_km, resolution
        )

        normal_map = NormalMapGenerator.from_heightmap(heightmap)

        model_dir = self._output_dir / site.name
        writer = ModelWriter(model_dir)
        writer.write(
            site_id=site.name,
            display_name=site.name.replace("_", " ").title(),
            description=site.description or f"Lunar terrain at ({lat}, {lon})",
            heightmap=heightmap,
            albedo=albedo,
            normal_map=normal_map,
            size_m=size_m,
            elevation_min=elev_min,
            elevation_max=elev_max,
            lat=lat,
            lon=lon,
            source="nasa_lola_lroc",
        )
        return model_dir
```

- [ ] **Step 4: Run all tests**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/ -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add src/lunar_terrain_generator/lunar_terrain_generator/terrain_generator.py src/lunar_terrain_generator/test/test_integration.py
git commit -m "feat(terrain_generator): support use_full_extent pipeline path

When use_full_extent is True, uses from_dem_full_extent() and derives
lat/lon/size from the DEM bounds for albedo generation.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 7: Update CLI to support `--use-full-extent`

**Files:**
- Modify: `src/lunar_terrain_generator/test/test_cli.py`
- Modify: `src/lunar_terrain_generator/lunar_terrain_generator/cli.py`

- [ ] **Step 1: Write failing tests for `--use-full-extent` CLI flag**

Add this test class to `test_cli.py`:

```python
class TestCLIFullExtentMode:
    def test_direct_mode_with_full_extent(self):
        parser = build_parser()
        args = parser.parse_args([
            "--name", "site01",
            "--dem-url", "https://example.com/site01.tif",
            "--use-full-extent",
            "--output-dir", "/tmp/out",
        ])
        assert args.name == "site01"
        assert args.use_full_extent is True
        assert args.dem_url == "https://example.com/site01.tif"

    def test_direct_mode_full_extent_no_latlon_needed(self):
        """With --use-full-extent, --lat and --lon should not be required."""
        parser = build_parser()
        args = parser.parse_args([
            "--name", "site01",
            "--dem-url", "https://example.com/site01.tif",
            "--use-full-extent",
            "--output-dir", "/tmp/out",
        ])
        assert args.lat is None
        assert args.lon is None
```

Also update `TestCLIConfigMode::test_config_mode_single_site` to use a valid new site name:

```python
    def test_config_mode_single_site(self):
        parser = build_parser()
        args = parser.parse_args([
            "--config", "sites.yaml",
            "--site", "connecting_ridge",
            "--output-dir", "/tmp/out",
        ])
        assert args.config == "sites.yaml"
        assert args.site == "connecting_ridge"
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_cli.py::TestCLIFullExtentMode -v`
Expected: FAIL — `error: unrecognized arguments: --use-full-extent`

- [ ] **Step 3: Update CLI parser and main function**

In `cli.py`, add the `--use-full-extent` argument. Add this after the `--lroc-url` argument (around line 69):

```python
    parser.add_argument(
        "--use-full-extent", action="store_true", default=False,
        help="Use the full DEM tile extent (no lat/lon cropping needed)",
    )
```

Update the epilog string (replace the existing epilog around lines 22-30):

```python
        epilog=(
            "Config mode (batch from YAML):\n"
            "  generate_lunar_sdf --config sites.yaml --output-dir ./models\n"
            "  generate_lunar_sdf --config sites.yaml --site connecting_ridge --output-dir ./models\n"
            "\n"
            "Direct mode (one-off with lat/lon crop):\n"
            "  generate_lunar_sdf --name my_site --lat -85.0 --lon 30.0 \\\n"
            "    --dem-url https://...ldem_85s_10m.img --output-dir ./models\n"
            "\n"
            "Direct mode (full DEM extent):\n"
            "  generate_lunar_sdf --name site01 --use-full-extent \\\n"
            "    --dem-url https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif \\\n"
            "    --output-dir ./models\n"
        ),
```

Update the direct-mode validation in the `main()` function. Replace the existing direct-mode block (from `else:` around line 93 to the end of `generator.generate(site)`):

```python
    else:
        # Direct mode — validate required args
        if not args.use_full_extent:
            if not all([args.lat is not None, args.lon is not None, args.dem_url]):
                parser.error("Direct mode requires --lat, --lon, and --dem-url (or use --use-full-extent)")
        elif not args.dem_url:
            parser.error("Direct mode with --use-full-extent requires --dem-url")

        site = SiteConfig(
            name=args.name,
            dem_url=args.dem_url,
            lat=args.lat,
            lon=args.lon,
            region_size_km=args.region_size,
            lroc_url=args.lroc_url,
            use_full_extent=args.use_full_extent,
        )
        site.validate()
        generator.generate(site)
```

- [ ] **Step 4: Run all CLI tests**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/test_cli.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add src/lunar_terrain_generator/lunar_terrain_generator/cli.py src/lunar_terrain_generator/test/test_cli.py
git commit -m "feat(cli): add --use-full-extent flag for pre-cropped DEM tiles

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 8: Update site config and pre-built models to 4 Barker sites

**Files:**
- Modify: `src/lunar_terrain_generator/config/artemis_sites.yaml`
- Modify: `src/lunar_terrain_generator/models/` (remove/add/rename directories)
- Modify: `src/lunar_terrain_generator/test/test_integration.py`

- [ ] **Step 1: Replace `artemis_sites.yaml` with 4 Barker sites**

Replace the entire contents of `config/artemis_sites.yaml`:

```yaml
# Barker et al. (2021) improved LOLA south pole landing sites
# Source: NASA PGDA Product 78 (https://pgda.gsfc.nasa.gov/products/78)
# DEM: 5 m/pix GeoTIFFs, track-adjusted, south polar stereographic, MOON_ME frame
#
# Reference: Barker et al., 2021, "Improved LOLA Elevation Maps for South Pole
# Landing Sites: Error Estimates and Their Impact on Illumination Conditions",
# Planetary & Space Science, Vol. 203, 105119.
# https://doi.org/10.1016/j.pss.2020.105119

sites:
  - name: connecting_ridge
    description: "Connecting ridge between Shackleton and de Gerlache craters (Barker Site 01)"
    dem_url: "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif"
    use_full_extent: true

  - name: shackleton_rim
    description: "Rim of Shackleton crater (Barker Site 04)"
    dem_url: "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site04/Site04_final_adj_5mpp_surf.tif"
    use_full_extent: true

  - name: peak_near_shackleton
    description: "Isolated peak near Shackleton crater (Barker Site 07)"
    dem_url: "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site07/Site07_final_adj_5mpp_surf.tif"
    use_full_extent: true

  - name: de_gerlache_rim
    description: "Rim of de Gerlache crater (Barker Site 11)"
    dem_url: "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site11/Site11_final_adj_5mpp_surf.tif"
    use_full_extent: true
```

- [ ] **Step 2: Remove old model directories and rename/create new ones**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator/src/lunar_terrain_generator/models

# Remove models for deleted sites
rm -rf nobile_rim_1 malapert_massif shackleton_crater

# Rename de_gerlache_rim_1 -> de_gerlache_rim
git mv de_gerlache_rim_1 de_gerlache_rim

# Create shackleton_rim directory from connecting_ridge as template
cp -r connecting_ridge shackleton_rim
```

- [ ] **Step 3: Update model files for renamed/new sites**

For `de_gerlache_rim` — update the SDF, config, and metadata files to use the new name. Replace occurrences of `de_gerlache_rim_1` with `de_gerlache_rim` in:

`models/de_gerlache_rim/model.sdf` — replace all `de_gerlache_rim_1` → `de_gerlache_rim`

`models/de_gerlache_rim/model.config` — update the display name and description:
```xml
<?xml version="1.0"?>
<model>
  <name>De Gerlache Rim</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <author>
    <name>Artemis Mission Simulator</name>
  </author>
  <description>Rim of de Gerlache crater (Barker Site 11)</description>
</model>
```

`models/de_gerlache_rim/metadata.yaml` — update site_id, display_name, description, source:
```yaml
site_id: de_gerlache_rim
display_name: De Gerlache Rim
description: Rim of de Gerlache crater (Barker Site 11)
coordinates:
  lat: -88.5
  lon: -70.0
size_m: 20000
resolution: 513
elevation_min_m: 0.0
elevation_max_m: 500.0
elevation_range_m: 500.0
source: barker_2021_pgda
```

For `shackleton_rim` — update all files similarly:

`models/shackleton_rim/model.sdf` — replace all `connecting_ridge` → `shackleton_rim`

`models/shackleton_rim/model.config`:
```xml
<?xml version="1.0"?>
<model>
  <name>Shackleton Rim</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <author>
    <name>Artemis Mission Simulator</name>
  </author>
  <description>Rim of Shackleton crater (Barker Site 04)</description>
</model>
```

`models/shackleton_rim/metadata.yaml`:
```yaml
site_id: shackleton_rim
display_name: Shackleton Rim
description: Rim of Shackleton crater (Barker Site 04)
coordinates:
  lat: -89.7
  lon: 130.0
size_m: 20000
resolution: 513
elevation_min_m: 0.0
elevation_max_m: 500.0
elevation_range_m: 500.0
source: barker_2021_pgda
```

Also update `connecting_ridge/metadata.yaml` to change `source: synthetic` to `source: barker_2021_pgda` and update description:
```yaml
site_id: connecting_ridge
display_name: Connecting Ridge
description: Connecting ridge between Shackleton and de Gerlache craters (Barker Site 01)
coordinates:
  lat: -88.5
  lon: -10.0
size_m: 20000
resolution: 513
elevation_min_m: 0.0
elevation_max_m: 500.0
elevation_range_m: 500.0
source: barker_2021_pgda
```

And `peak_near_shackleton/metadata.yaml`:
```yaml
site_id: peak_near_shackleton
display_name: Peak Near Shackleton
description: Isolated peak near Shackleton crater (Barker Site 07)
coordinates:
  lat: -89.5
  lon: 130.0
size_m: 20000
resolution: 513
elevation_min_m: 0.0
elevation_max_m: 500.0
elevation_range_m: 500.0
source: barker_2021_pgda
```

- [ ] **Step 4: Update integration tests**

Replace `TestIntegrationConfigLoad` in `test_integration.py`:

```python
class TestIntegrationConfigLoad:
    """Verify the preset Artemis sites config loads correctly."""

    def test_load_all_artemis_sites(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        assert len(sites) == 4
        names = [s.name for s in sites]
        assert "connecting_ridge" in names
        assert "shackleton_rim" in names
        assert "peak_near_shackleton" in names
        assert "de_gerlache_rim" in names

    def test_all_sites_use_full_extent(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        for site in sites:
            assert site.use_full_extent is True
            assert site.dem_url.startswith("https://pgda.gsfc.nasa.gov/")

    def test_all_sites_validate(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        for site in sites:
            site.validate()

    def test_all_site_names_are_unique(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        names = [s.name for s in sites]
        assert len(names) == len(set(names))
```

- [ ] **Step 5: Run all tests**

Run: `cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add -A src/lunar_terrain_generator/config/ src/lunar_terrain_generator/models/ src/lunar_terrain_generator/test/test_integration.py
git commit -m "feat: switch to 4 Barker et al. (2021) landing sites

Replace 13 PDS3-based sites with 4 track-adjusted PGDA Product 78
GeoTIFF sites: connecting_ridge, shackleton_rim, peak_near_shackleton,
de_gerlache_rim. All use use_full_extent: true.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 9: Update launch file default site

**Files:**
- Modify: `src/artemis_mission_launcher/launch/lunar_surface.launch.py`

- [ ] **Step 1: Update the launch file**

In `lunar_surface.launch.py`, update the default site and description. Change lines 6, 70, and 71.

Line 6 — update usage comment:
```python
    ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=connecting_ridge
```

Lines 68-74 — update the `DeclareLaunchArgument`:
```python
        DeclareLaunchArgument(
            "site",
            default_value="connecting_ridge",
            description="Lunar site to load (connecting_ridge, shackleton_rim, peak_near_shackleton, de_gerlache_rim)",
        ),
```

- [ ] **Step 2: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add src/artemis_mission_launcher/launch/lunar_surface.launch.py
git commit -m "chore(launch): update default site to connecting_ridge

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 10: Update READMEs with new sites and Barker citation

**Files:**
- Modify: `README.md`
- Modify: `src/lunar_terrain_generator/README.md`

- [ ] **Step 1: Update main `README.md`**

Replace the "Available Terrain Sites" table (lines 41-50):

```markdown
## Available Terrain Sites

| Site | Launch ID | Description |
|------|-----------|-------------|
| Connecting Ridge | `connecting_ridge` | Ridge between Shackleton and de Gerlache (Barker Site 01) |
| Shackleton Rim | `shackleton_rim` | Rim of Shackleton crater (Barker Site 04) |
| Peak Near Shackleton | `peak_near_shackleton` | Isolated peak near Shackleton crater (Barker Site 07) |
| de Gerlache Rim | `de_gerlache_rim` | Rim of de Gerlache crater (Barker Site 11) |

Terrain data: [Barker et al. (2021)](https://doi.org/10.1016/j.pss.2020.105119) improved LOLA 5 m/pix DEMs from [NASA PGDA](https://pgda.gsfc.nasa.gov/products/78).
```

Update the Quick Start launch example (line 27) — change `site:=shackleton_crater` to `site:=connecting_ridge`.

Update the Quick Start example (lines 26-28):
```bash
docker compose run sim bash -c "source /ws/install/setup.bash && \
  ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=connecting_ridge"
```

Update the "Quick Start" section launch mode example (line 55):
```bash
ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=shackleton_rim
```

Update the NVIDIA example (lines 37-38):
```bash
docker compose run sim-nvidia bash -c "source /ws/install/setup.bash && \
  ros2 launch artemis_mission_launcher lunar_surface.launch.py"
```
(This one doesn't specify a site, so no change needed.)

- [ ] **Step 2: Update `src/lunar_terrain_generator/README.md`**

Replace the entire file content with:

```markdown
# Lunar Terrain Generator

ROS 2 (ament_python) package that generates Gazebo SDF terrain models from NASA LOLA elevation data and LROC WAC albedo imagery.

## Features

- Generates 16-bit heightmap PNGs from LOLA DEM data (GeoTIFF or PDS3 format)
- Generates albedo textures from LROC WAC global mosaic
- Derives normal maps using Sobel gradients
- Outputs complete Gazebo SDF model directories
- Ships with preset configurations for 4 Barker et al. (2021) landing sites
- Supports custom site generation via YAML config or CLI arguments
- Supports full-extent DEM tiles (no lat/lon cropping needed)

## Usage

### Generate all default sites from preset config

```bash
generate_lunar_sdf --config config/artemis_sites.yaml --output-dir ./models
```

### Generate a single site from config

```bash
generate_lunar_sdf --config config/artemis_sites.yaml --site connecting_ridge --output-dir ./models
```

### Generate a custom site with lat/lon cropping

```bash
generate_lunar_sdf --name my_site --lat -89.7 --lon 0.0 \
  --dem-url "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/87S/ldem_87s_5mpp.tif" \
  --output-dir ./models
```

### Generate using a full DEM tile (no cropping)

```bash
generate_lunar_sdf --name site01 --use-full-extent \
  --dem-url "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif" \
  --output-dir ./models
```

## Site Configuration Format

Sites are defined in YAML files:

```yaml
sites:
  - name: connecting_ridge
    description: "Connecting ridge between Shackleton and de Gerlache craters"
    dem_url: "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif"
    use_full_extent: true
```

For custom regions that need lat/lon cropping:

```yaml
sites:
  - name: custom_site
    description: "Custom region"
    lat: -85.0
    lon: 30.0
    dem_url: "https://example.com/dem.tif"
    region_size_km: 10
```

## DEM Data Sources

### Default: Barker et al. (2021) improved LOLA DEMs

The default sites use track-adjusted 5 m/pix GeoTIFFs from NASA PGDA Product 78:

| Site | Barker ID | GeoTIFF |
|------|-----------|---------|
| Connecting Ridge | Site 01 | `Site01_final_adj_5mpp_surf.tif` |
| Shackleton Rim | Site 04 | `Site04_final_adj_5mpp_surf.tif` |
| Peak Near Shackleton | Site 07 | `Site07_final_adj_5mpp_surf.tif` |
| de Gerlache Rim | Site 11 | `Site11_final_adj_5mpp_surf.tif` |

Source: [NASA PGDA Product 78](https://pgda.gsfc.nasa.gov/products/78)

**Please cite when using these DEMs:**

> Barker et al., 2021, "Improved LOLA Elevation Maps for South Pole Landing Sites:
> Error Estimates and Their Impact on Illumination Conditions",
> *Planetary & Space Science*, Volume 203, 105119.
> https://doi.org/10.1016/j.pss.2020.105119

### Alternative: LOLA Polar Gridded Data Records (PDS)

Standard LOLA DEMs from the PDS Geosciences Node can also be used with lat/lon cropping:

| File | Coverage | Resolution |
|------|----------|------------|
| `ldem_80s_20m.img` | 80°S to pole | 20 m/px |
| `ldem_85s_10m.img` | 85°S to pole | 10 m/px |
| `ldem_875s_5m.img` | 87.5°S to pole | 5 m/px |
```

- [ ] **Step 3: Commit**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
git add README.md src/lunar_terrain_generator/README.md
git commit -m "docs: update READMEs for Barker DEM sites and citation

Update terrain site tables to 4 Barker sites, add PGDA citation,
update launch examples.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 11: Final test run and verification

**Files:** (none — verification only)

- [ ] **Step 1: Run the full test suite**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator && python -m pytest src/lunar_terrain_generator/test/ -v
```
Expected: All tests PASS

- [ ] **Step 2: Verify model directories are correct**

```bash
ls -la src/lunar_terrain_generator/models/
```
Expected: Exactly 4 directories: `connecting_ridge`, `shackleton_rim`, `peak_near_shackleton`, `de_gerlache_rim`

- [ ] **Step 3: Verify config loads correctly**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator && python -c "
from lunar_terrain_generator.site_config import load_sites
sites = load_sites('src/lunar_terrain_generator/config/artemis_sites.yaml')
for s in sites:
    s.validate()
    print(f'{s.name}: use_full_extent={s.use_full_extent}, dem_url={s.dem_url[:60]}...')
print(f'Total: {len(sites)} sites')
"
```
Expected: 4 sites, all with `use_full_extent=True` and PGDA URLs

- [ ] **Step 4: Verify no stale references to removed sites**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
grep -rn "shackleton_crater\|nobile_rim_1\|nobile_rim_2\|malapert_massif\|faustini_rim\|haworth\|amundsen_rim\|de_gerlache_rim_1\|de_gerlache_rim_2\|de_gerlache_kocher\|connecting_ridge_extension\|leibnitz_beta" \
  --include="*.py" --include="*.yaml" --include="*.launch.py" \
  src/ README.md
```
Expected: No matches (old site names completely removed from operational files)

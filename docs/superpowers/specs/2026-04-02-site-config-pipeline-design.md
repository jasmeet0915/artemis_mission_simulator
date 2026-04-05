# Site Config & Pipeline Fix Design

## Problem

The `lunar_terrain_generator` package has three critical bugs preventing real terrain generation from LOLA PDS data:

1. **Broken DEM URL** — The default URL points to `ldem_80s_20m_float.img`, which does not exist on PDS. Only the int16 version (`ldem_80s_20m.img`) is available for polar products.
2. **Wrong projection handling** — HeightmapGenerator assumes geographic (lat/lon) coordinates, but LOLA polar DEMs use polar stereographic projection with (x, y) coordinates in meters.
3. **Wrong data format** — The code assumes float elevation values, but the data is int16 with a scaling factor of 0.5 (`elevation_m = pixel × 0.5`).

Additionally, the package lacks a site config system for managing the 13 NASA Artemis III candidate landing regions, requiring users to manually specify coordinates and DEM URLs for each site.

## Approach

Introduce a YAML-based site configuration system and fix the terrain generation pipeline to correctly handle LOLA PDS3 polar stereographic DEMs. A single config file ships with all 13 Artemis III sites as presets; users can create their own configs for custom sites.

## Architecture

```
lunar_terrain_generator/
├── config/
│   └── artemis_sites.yaml          # Preset: 13 Artemis III candidate regions
├── lunar_terrain_generator/
│   ├── cli.py                      # Rewrite: --config mode + --lat/--lon mode
│   ├── site_config.py              # New: YAML parser → SiteConfig dataclass
│   ├── terrain_generator.py        # Modify: accept SiteConfig, remove broken default URL
│   ├── heightmap.py                # Rewrite: polar stereographic + int16 scaling
│   ├── albedo.py                   # Modify: CRS-aware windowed reads
│   ├── downloader.py               # Modify: cache by URL hash
│   ├── model_writer.py             # No change
│   └── normal_map.py               # No change
├── setup.py                        # Modify: add config to data_files, add pyproj dep
└── package.xml                     # Modify: add pyproj dependency
```

### Data Flow

1. CLI parses args → loads YAML → creates list of `SiteConfig` objects
2. For each site: `TerrainGenerator.generate(site_config, output_dir)`
3. `TerrainGenerator` delegates to `HeightmapGenerator`, `AlbedoGenerator`, `NormalMapGenerator`, `ModelWriter`

`SiteConfig` is the single input contract replacing scattered individual parameters.

## Config Format

### SiteConfig Dataclass

```python
@dataclass
class SiteConfig:
    name: str              # Output directory name, must be valid dir name
    lat: float             # Latitude in degrees (negative for south)
    lon: float             # Longitude in degrees (negative for west)
    dem_url: str           # Full URL to LOLA PDS3 DEM .img file
    region_size_km: float = 10.0   # Square region side length in km
    lroc_url: str = DEFAULT_LROC_WAC_URL  # Albedo texture source
    description: str = ""  # Human-readable site description
```

### Validation Rules

- `lat` must be ≤ -80.0 (LOLA south pole DEMs cover 80°S to pole)
- `name` must be a valid directory name (alphanumeric, hyphens, underscores)
- `dem_url` must be a non-empty string (URL format)
- `region_size_km` must be > 0

### YAML Format

```yaml
sites:
  - name: haworth
    description: "Northern rim of Haworth crater"
    lat: -86.5
    lon: -4.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_85s_10m.img"
    region_size_km: 10

  - name: malapert_massif
    description: "Malapert Massif, southwestern rim of Malapert crater"
    lat: -86.0
    lon: 0.0
    dem_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_85s_10m.img"
```

### Preset Sites: 13 Artemis III Candidate Regions

DEM base URL: `https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/`

Available south pole DEMs:
- `ldem_80s_20m.img` — 80°S to pole, 20 m/px, ~1.85 GB
- `ldem_85s_10m.img` — 85°S to pole, 10 m/px, ~1.84 GB
- `ldem_875s_5m.img` — 87.5°S to pole, 5 m/px, ~1.84 GB

Each site uses the highest-resolution DEM that covers its latitude.

| # | name | lat | lon | DEM file | Description |
|---|------|-----|-----|----------|-------------|
| 1 | faustini_rim_a | -87.0 | 77.0 | ldem_875s_5m | Rim of Faustini crater |
| 2 | peak_near_shackleton | -89.5 | 130.0 | ldem_875s_5m | Peak near Shackleton crater at south pole |
| 3 | connecting_ridge | -89.0 | -60.0 | ldem_875s_5m | Ridge connecting Shackleton to de Gerlache |
| 4 | connecting_ridge_extension | -88.5 | -50.0 | ldem_875s_5m | Extension of connecting ridge |
| 5 | de_gerlache_rim_1 | -88.2 | -80.0 | ldem_875s_5m | Northern rim of de Gerlache crater |
| 6 | de_gerlache_rim_2 | -88.5 | -70.0 | ldem_875s_5m | Eastern rim of de Gerlache crater |
| 7 | de_gerlache_kocher_massif | -86.0 | -110.0 | ldem_85s_10m | Highland between de Gerlache and Kocher |
| 8 | haworth | -86.5 | -4.0 | ldem_85s_10m | Northern rim of Haworth crater |
| 9 | malapert_massif | -86.0 | 0.0 | ldem_85s_10m | Malapert Mountain, SW rim of Malapert crater |
| 10 | leibnitz_beta_plateau | -84.6 | 31.0 | ldem_80s_20m | Mons Mouton flat-topped mountain plateau |
| 11 | nobile_rim_1 | -85.3 | 36.0 | ldem_85s_10m | Western rim of Nobile crater |
| 12 | nobile_rim_2 | -84.5 | 53.0 | ldem_80s_20m | Northern rim of Nobile crater |
| 13 | amundsen_rim | -83.5 | 83.0 | ldem_80s_20m | Northern rim of Amundsen crater |

**Note:** Coordinates for rim/peak/ridge/massif sites are estimated from parent crater geometry. NASA has not published exact landing zone center coordinates. These estimates place the crop window in the correct terrain area and can be refined later.

## CLI Interface

Two mutually exclusive modes via argparse:

### Config Mode

```bash
# Generate all 13 sites
generate-terrain --config artemis_sites.yaml --output-dir ./models

# Generate a single site from config
generate-terrain --config artemis_sites.yaml --site haworth --output-dir ./models
```

### Direct Mode

```bash
# One-off generation without a config file
generate-terrain --name custom_site --lat -85.0 --lon 30.0 \
  --dem-url "https://...ldem_85s_10m.img" --output-dir ./models
```

### Argument Groups

- Config group: `--config`, `--site` (optional filter), `--output-dir`
- Direct group: `--name`, `--lat`, `--lon`, `--dem-url`, `--output-dir`, `--region-size` (optional), `--lroc-url` (optional)

`--config` and `--name` are mutually exclusive. `--output-dir` is required in both modes.

## Pipeline Fixes

### HeightmapGenerator — Polar Stereographic Handling

**Problem:** LOLA polar DEMs use polar stereographic projection. Current code passes lat/lon degrees to rasterio's `from_bounds()`, which expects coordinates in the raster's native CRS (projected meters).

**Fix:**

1. Open the `.lbl` sidecar with rasterio (GDAL reads PDS3 labels natively)
2. Convert center (lat, lon) to polar stereographic (x, y) using pyproj:
   ```python
   from pyproj import Transformer
   # Lunar polar stereographic: centered on south pole, lunar radius
   lunar_stereo = "+proj=stere +lat_0=-90 +lon_0=0 +R=1737400 +units=m"
   transformer = Transformer.from_crs("EPSG:4326", lunar_stereo, always_xy=True)
   x_center, y_center = transformer.transform(lon, lat)
   ```
3. Compute bounding box in projected coordinates:
   ```python
   half_size = region_size_km * 1000 / 2
   x_min, x_max = x_center - half_size, x_center + half_size
   y_min, y_max = y_center - half_size, y_center + half_size
   ```
4. Use `rasterio.windows.from_bounds(x_min, y_min, x_max, y_max, transform=dataset.transform)` to get the pixel window
5. Read int16 data, apply scaling factor: `elevation_m = raw_pixels * 0.5`
6. Normalize elevation range to 0–65535 for 16-bit PNG
7. Resize to nearest 2^n+1 dimension (Gazebo heightmap requirement)

**New dependency:** `pyproj`

### AlbedoGenerator — CRS-Aware Reads

**Problem:** Same geographic coordinate math issue as HeightmapGenerator, but the LROC WAC mosaic uses simple cylindrical (equirectangular) projection.

**Fix:** Use rasterio's CRS-aware windowed read. The WAC GeoTIFF has proper geotransform metadata, so rasterio can handle the coordinate conversion. Near the poles, cylindrical projection causes E-W stretching in the texture, but this maps correctly onto the terrain mesh since both use the same spatial extent.

### Downloader — URL-Based Caching

**Problem:** Current cache uses filename only. Different DEM URLs could share the same base filename.

**Fix:** Cache key = `<sha256_of_url[:16]>_<filename>`. Example: `a1b2c3d4e5f6g7h8_ldem_85s_10m.img`.

### TerrainGenerator — Remove Broken Default

Remove `DEFAULT_LOLA_URL` constant (pointed to non-existent `_float.img`). DEM URL is now always provided by SiteConfig.

## Package Changes

### setup.py

Add to `data_files`:
```python
('share/lunar_terrain_generator/config', ['config/artemis_sites.yaml']),
```

### package.xml

Add dependency:
```xml
<exec_depend>python3-pyproj</exec_depend>
```

If `python3-pyproj` is not available as a system package, fall back to pip install in Dockerfile.

## Testing

### New Tests

- **test_site_config.py**: YAML parsing, validation (bad lat, missing fields, empty name, invalid dem_url), load_sites/load_site functions, SiteConfig defaults
- **test_heightmap.py**: Polar stereographic conversion math (known lat/lon → expected x,y), int16 scaling (raw value × 0.5), windowed read with mock rasterio dataset, resize to 2^n+1
- **test_cli.py**: Config mode argument parsing, direct mode argument parsing, mutual exclusion, error messages for missing required args
- **test_integration.py**: SiteConfig → TerrainGenerator → verify all output files created (heightmap PNG, albedo PNG, normal map PNG, model.sdf, model.config) using mocked downloads

### Existing Tests (Unchanged)

- test_normal_map.py (4 tests)
- test_model_writer.py (3 tests)

## Error Handling

- **Network errors**: Retry downloads up to 3 times with exponential backoff (existing behavior)
- **Invalid config**: Fail fast with clear error message listing which field(s) failed validation
- **DEM doesn't cover site**: If the lat/lon falls outside the DEM's spatial extent, raise a descriptive error
- **Missing .lbl file**: GDAL needs the `.lbl` sidecar to be co-located with `.img`. If HTTP range requests are supported, rasterio can read remotely; otherwise download the full file

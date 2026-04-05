# Design: Migrate to Barker et al. (2021) Improved LOLA DEMs

## Problem

The terrain generator hardcodes PDS3 format assumptions (int16 scaling factor 0.5, nodata -32768) in `heightmap.py`. This prevents using GeoTIFF-format DEMs. We want to switch to the higher-quality, track-adjusted Barker et al. (2021) per-site GeoTIFFs from NASA PGDA Product 78 and reduce the default site list to the 4 primary sites studied in the paper.

## Approach

Make the DEM reader format-agnostic by reading metadata from rasterio, add `use_full_extent` support for per-site tiles, update the site config to 4 Barker sites, and update documentation with proper citations.

## Data Source

**Barker et al., 2021**, "Improved LOLA Elevation Maps for South Pole Landing Sites: Error Estimates and Their Impact on Illumination Conditions", *Planetary & Space Science*, Vol. 203, 105119. https://doi.org/10.1016/j.pss.2020.105119

Individual per-site GeoTIFFs from NASA PGDA Product 78: https://pgda.gsfc.nasa.gov/products/78

- 5 m/pix resolution, south polar stereographic, MOON_ME frame (DE421)
- Track-adjusted with ~10-20 cm horizontal and ~2-4 cm vertical geolocation uncertainty
- RMS height error: 0.30-0.50 m (significantly better than standard LOLA GDRs)

## Changes

### 1. `heightmap.py` — Format-agnostic DEM reading

Remove hardcoded PDS3 assumptions. Read metadata from rasterio dataset:
- `src.nodata` for nodata value
- `src.scales` / `src.offsets` for value transforms
- Detect if raw data needs scaling or is already in meters

Add `from_dem_full_extent()` classmethod:
- Reads the entire DEM without lat/lon cropping
- Returns heightmap + elevation bounds + geographic bounds (for albedo derivation)

Add `stereo_to_latlon()` inverse projection:
- Converts south pole stereographic (x, y) back to geographic (lat, lon)
- Used to derive albedo crop region from DEM bounds

Keep `apply_pds3_scaling()` for backward compatibility but it will no longer be called by `from_dem()`. The read path uses rasterio metadata instead.

### 2. `site_config.py` — Add `use_full_extent` field

Add `use_full_extent: bool = False` to `SiteConfig` dataclass.

When `use_full_extent=True`:
- `lat` and `lon` become optional (`None`)
- `region_size_km` is ignored (full tile extent used)
- Validation skips lat/lon checks

When `use_full_extent=False`:
- Existing behavior preserved: lat, lon, region_size_km all required

Update `load_sites()` to read `use_full_extent` from YAML.

### 3. `terrain_generator.py` — Branch on `use_full_extent`

If `site.use_full_extent`:
- Call `HeightmapGenerator.from_dem_full_extent(dem_file)`
- Derive center lat/lon from returned DEM bounds
- Compute region size from DEM extent
- Pass derived values to albedo generator

Otherwise:
- Existing `from_dem()` path with metadata-aware scaling

### 4. `artemis_sites.yaml` — 4 Barker sites

Replace all 13 sites with these 4:

| Name | Barker Site | DEM GeoTIFF |
|------|-------------|-------------|
| `connecting_ridge` | Site 01 | `Site01_final_adj_5mpp_surf.tif` |
| `shackleton_rim` | Site 04 | `Site04_final_adj_5mpp_surf.tif` |
| `peak_near_shackleton` | Site 07 | `Site07_final_adj_5mpp_surf.tif` |
| `de_gerlache_rim` | Site 11 | `Site11_final_adj_5mpp_surf.tif` |

All use `use_full_extent: true`. Base URL: `https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/`

### 5. Pre-built models

- Remove models for sites no longer in the config: `nobile_rim_1`, `malapert_massif`, `shackleton_crater`
- Rename `de_gerlache_rim_1` → `de_gerlache_rim`
- Add `shackleton_rim` model directory
- Model content (heightmaps, textures) will be regenerated from new DEMs

Note: Since models contain generated binary data (PNGs), we will regenerate stub/placeholder SDF+config files. Actual heightmap/texture generation requires downloading the PGDA data, which is a runtime operation.

### 6. Launch file updates

In `lunar_surface.launch.py`:
- Change default site from `shackleton_crater` to `connecting_ridge`
- Update description to list the 4 available sites

### 7. README updates

**Main `README.md`:**
- Update "Available Terrain Sites" table to 4 sites
- Update launch examples
- Add DEM source citation

**`src/lunar_terrain_generator/README.md`:**
- Update "Available LOLA DEMs" table to reference PGDA Product 78
- Update CLI examples to use new site names
- Add Barker et al. 2021 citation
- Update site config YAML example

### 8. Test updates

**`test_heightmap.py`:**
- Keep `TestInt16Scaling` tests (method still exists for backward compat)
- Add tests for metadata-driven scaling path

**`test_site_config.py`:**
- Add tests for `use_full_extent=True` with optional lat/lon
- Update validation tests

**`test_integration.py`:**
- Update `test_load_all_artemis_sites` to expect 4 sites
- Update name assertions to match new sites
- Add test for `use_full_extent` pipeline path

**`test_cli.py`:**
- Update example site name from `haworth` to one of the 4 new sites

## Out of Scope

- Downloading or processing actual PGDA data (runtime operation)
- Changes to albedo.py, normal_map.py, model_writer.py (no changes needed)
- Cloud-Optimized GeoTIFF support
- Support for non-south-pole DEMs

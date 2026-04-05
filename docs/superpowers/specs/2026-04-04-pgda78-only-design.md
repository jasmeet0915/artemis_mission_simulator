# Design: Simplify Package to PGDA Product 78 Only

**Date:** 2026-04-04
**Status:** Draft
**Scope:** Remove all non-PGDA-78 data handling from `generate_lunar_sdf`

## Problem

The `generate_lunar_sdf` package currently supports two independent data sources:

1. **PGDA Product 78** (Barker et al.) — 5 m/pix south polar stereographic GeoTIFF DEMs from NASA PGDA. This is the authoritative high-accuracy dataset we actually use.
2. **LROC WAC mosaic** — A global equirectangular albedo texture from USGS. Used to generate diffuse textures for Gazebo models.
3. **Legacy LOLA PDS3 GDRs** — Older `.img` format DEMs from PDS Geosciences Node. Referenced in docs and supported via `apply_pds3_scaling()`.

Only (1) is needed. Items (2) and (3) add complexity, dependencies, and code paths that are never used in practice — all 4 preset Artemis sites use `use_full: true` with PGDA-78 GeoTIFFs.

## Decision

Simplify the entire package to work exclusively with PGDA Product 78 GeoTIFF DEMs. Remove everything else.

## What Gets Removed

### AlbedoGenerator (entire class and file)
- `map_generators/albedo_generator.py` — deleted entirely
- Import and re-export from `map_generators/__init__.py`
- LROC WAC download step in `GenerateLunarSDF.generate()`
- `--lroc-url` CLI argument
- `lroc_url` field from `SiteConfig` dataclass
- `DEFAULT_LROC_WAC_URL` constant from `site_config_parser.py`
- All test mocking of `AlbedoGenerator`

### PDS3 Format Support
- `HeightmapGenerator.apply_pds3_scaling()` static method — deleted
- Module docstring reference to "PDS3" in `heightmap_generator.py`
- Legacy LOLA GDR section from `README.md`
- PDS3-specific test cases (`test_int16_with_scale`, `test_nodata_handling` for int16 sentinel values)

### SDF Template Albedo Reference
- `<diffuse>` texture line removed from the SDF template in `model_writer.py`
- `albedo` parameter removed from `ModelWriter.write()`
- Albedo PNG no longer written to `materials/textures/`

### YAML Config
- `lroc_url` field removed from YAML format (and parser)

## What Stays

### HeightmapGenerator (core of the package)
- Polar stereographic projection (`latlon_to_stereo`, `stereo_to_latlon`)
- `from_dem()` — rectangular crop from GeoTIFF using rasterio
- `from_dem_full_extent()` — full-tile read for pre-cropped PGDA tiles
- `_read_elevations()` — reads nodata/scale/offset from GeoTIFF metadata (this is generic rasterio, not PDS3-specific)
- `normalize()`, `nearest_gazebo_size()`

### NormalMapGenerator
- Derives normal map purely from heightmap via Sobel gradients
- No dependency on albedo — stays as-is
- SDF `<normal>` texture reference stays in the template

### ModelWriter (simplified)
- Writes heightmap PNG (16-bit grayscale) and normal map PNG (RGB)
- SDF template with `<heightmap>` geometry + `<normal>` texture only
- `model.config`, `metadata.yaml`
- Parameters: remove `albedo`, keep everything else

### Config / CLI
- `BoundingBox`, `Extent`, `SiteConfig` — stay (minus `lroc_url`)
- CLI: `--config`, `--name`, `--lat`, `--lon`, `--width`, `--height`, `--dem-url`, `--use-full-extent`, `--output-dir`, `--cache-dir` all stay
- `artemis_sites.yaml` — unchanged (already PGDA-78 only)

### FileDownloader
- Unchanged — generic HTTP download with caching

## SDF Template (After)

```xml
<?xml version="1.0"?>
<sdf version="1.11">
  <model name="${site_id}">
    <static>true</static>
    <link name="terrain_link">
      <collision name="terrain_collision">
        <geometry>
          <heightmap>
            <uri>model://${site_id}/materials/textures/heightmap.png</uri>
            <size>${size_x} ${size_y} ${size_z}</size>
            <pos>0 0 ${z_offset}</pos>
          </heightmap>
        </geometry>
      </collision>
      <visual name="terrain_visual">
        <geometry>
          <heightmap>
            <uri>model://${site_id}/materials/textures/heightmap.png</uri>
            <size>${size_x} ${size_y} ${size_z}</size>
            <pos>0 0 ${z_offset}</pos>
            <texture>
              <normal>model://${site_id}/materials/textures/normal.png</normal>
              <size>10</size>
            </texture>
          </heightmap>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>
```

The `<diffuse>` line is removed. Gazebo will use its default gray diffuse, which is appropriate for lunar regolith.

## Updated Package Structure

```
generate_lunar_sdf/
  __init__.py            # Exports: BoundingBox, Extent, SiteConfig, load_sites, load_site, GenerateLunarSDF
  generate_lunar_sdf.py  # CLI + pipeline (no albedo step)
  map_generators/
    __init__.py           # Exports: HeightmapGenerator, NormalMapGenerator
    heightmap_generator.py  # Polar stereo + GeoTIFF (no PDS3)
    normal_map_generator.py # Unchanged
    (albedo_generator.py DELETED)
  utils/
    __init__.py           # Exports: BoundingBox, Extent, SiteConfig, ..., FileDownloader, ModelWriter
    site_config_parser.py # No lroc_url, no DEFAULT_LROC_WAC_URL
    file_downloader.py    # Unchanged
    model_writer.py       # No albedo param, no albedo PNG
```

## Test Impact

| Test File | Changes |
|-----------|---------|
| `test_site_config.py` | Remove any `lroc_url` references in YAML dicts |
| `test_cli.py` | Remove `--lroc-url` test; no `--region-size` (already done) |
| `test_integration.py` | Remove albedo mocking, remove `fake_albedo`, remove LROC download assertions |
| `test_terrain_processing.py` | Remove `_make_albedo()` helper, remove `albedo` param from ModelWriter calls, update metadata assertions |
| `test_heightmap.py` | Remove PDS3-specific tests (`TestInt16Scaling`); keep GeoTIFF-based tests |
| `test_downloader.py` | Unchanged |

Estimated net test count: ~55-58 (down from 70, removing ~12 albedo/PDS3 tests, adding none).

## Dependencies Removed

No Python dependencies are removed (rasterio, numpy, Pillow, PyYAML all still needed for heightmap/normal/SDF generation). The LROC WAC data dependency (a 24 GB GeoTIFF download) is eliminated.

## README Updates

- Remove "generates albedo textures from LROC WAC global mosaic" from features
- Remove Legacy LOLA Polar GDRs section
- Remove PDS3 format references
- Update CLI examples (no `--lroc-url`)
- Update YAML example (no `lroc_url`)
- Note that data source is exclusively PGDA Product 78

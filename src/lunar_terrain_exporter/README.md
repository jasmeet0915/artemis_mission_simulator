# lunar_terrain_exporter

Generates Gazebo Harmonic SDF terrain models from NASA PGDA Product 78 south-polar LOLA DEMs (5 m/pixel).

## Available Sites

All 27 sites from PGDA Product 78 are available. Run `lunar_terrain_exporter --output-dir ./models` interactively to see the full list.

## Usage

### Interactive mode (recommended)

```bash
lunar_terrain_exporter --output-dir ./models
```

Lists all 27 PGDA-78 sites and lets you pick one, then choose full-tile or custom bounding box.

### Site mode

```bash
# Full tile
lunar_terrain_exporter --site connecting_ridge --output-dir ./models

# Custom crop
lunar_terrain_exporter --site connecting_ridge \
  --lat -86.5 --lon -4.0 --width 5 --height 5 \
  --output-dir ./models
```

### Config mode (batch)

```bash
lunar_terrain_exporter --config config/artemis_sites.yaml --output-dir ./models
```

## Config File Format

```yaml
sites:
  - site: connecting_ridge
  - site: shackleton_rim
  - site: peak_near_shackleton
    roi:
      use_full: false
      bounding_box:
        lat: -86.5
        lon: -4.0
        width_km: 5.0
        height_km: 5.0
```

## Output Structure

Each site generates a complete Gazebo model:

```
models/<site_name>/
  model.sdf          # SDF with heightmap geometry
  model.config       # Gazebo model metadata
  metadata.yaml      # Generation parameters
  materials/textures/
    heightmap.png     # 16-bit grayscale DEM
    diffuse.png       # Slope-derived grayscale texture
    normal.png        # Sobel-gradient normal map
```

## Data Source

[NASA PGDA Product 78](https://pgda.gsfc.nasa.gov/products/78) — LOLA 5 m/pixel south-polar DEMs in GeoTIFF format (Moon ME reference frame, polar stereographic projection).

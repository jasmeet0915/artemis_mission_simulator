# Slope Texture + Site Catalog + CLI Simplification Design

## Problem

The package currently generates heightmap + normal map but no diffuse texture,
resulting in flat gray terrain in Gazebo. The user wants to add a
physically-meaningful diffuse texture derived from PGDA-78 data. They also
want a site-centric CLI that leverages the fact that all 27 PGDA-78 sites
have predictable URL patterns—eliminating the need to specify URLs manually.

### XYZI Correction

The user initially proposed using LOLA point cloud intensity from the XYZI
files. Investigation revealed the XYZI 4th column is **RDR ID** (track
identification), not intensity. The README confirms: "Data format: Binary
double precision floating point tables with 4 columns: X, Y, Z, RDRid."

### Chosen Approach: Slope Map as Diffuse Texture

PGDA-78 provides slope maps (`*_slp.tif`) — already-gridded 5 m/pix GeoTIFFs
in the same projection and extent as the DEMs. Slope values (degrees) map
naturally to surface appearance: flat regolith accumulation areas appear
lighter, steep exposed surfaces appear darker. This provides:
- Real, measured surface property variation
- Perfect spatial alignment with DEM (no interpolation needed)
- Non-uniform returns for drone LiDAR simulation (`gpu_lidar` in Gazebo)
- Small additional download (~same size as DEM)

### PBR Constraint

SDF `<heightmap>` geometry supports only `<texture>` layers with `<diffuse>`
and `<normal>` — NO `<pbr>` block (no roughness, metalness, emissive). The
slope-derived diffuse + Sobel normal map is the maximum we can provide for
heightmap terrain in Gazebo.

## Design

### A. Site Catalog — `utils/site_catalog.py`

A registry of all 27 PGDA-78 sites. URL patterns are deterministic:
- DEM: `https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/{pgda_id}/{pgda_id}_final_adj_5mpp_surf.tif`
- Slope: `https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/{pgda_id}/{pgda_id}_final_adj_5mpp_slp.tif`

```python
@dataclass(frozen=True)
class CatalogSite:
    pgda_id: str       # "Site01", "Haworth", "DM1", etc.
    name: str          # snake_case display name: "connecting_ridge"
    display_name: str  # "Connecting Ridge"
    description: str   # Brief description

    @property
    def dem_url(self) -> str: ...
    @property
    def slope_url(self) -> str: ...

SITE_CATALOG: dict[str, CatalogSite]  # keyed by name

def list_sites() -> list[CatalogSite]: ...
def get_site(name: str) -> CatalogSite: ...  # raises KeyError
```

Full catalog (27 sites from PGDA product page):

| name | pgda_id | display_name |
|------|---------|-------------|
| connecting_ridge | Site01 | Connecting Ridge |
| shackleton_rim | Site04 | Shackleton Rim |
| nobile_rim_1 | Site06 | Nobile Rim 1 |
| peak_near_shackleton | Site07 | Peak Near Shackleton |
| de_gerlache_rim | Site11 | de Gerlache Rim |
| leibnitz_beta | Site20 | Leibnitz Beta Plateau |
| leibnitz_beta_v2 | Site20v2 | Leibnitz Beta Plateau (Extended) |
| malapert_massif | Site23 | Malapert Massif |
| de_gerlache_kocher | Site42 | de Gerlache-Kocher Massif |
| haworth | Haworth | Haworth |
| shoemaker | Shoemaker | Shoemaker |
| amundsen_rim | DM1 | Amundsen Rim |
| nobile_rim_2 | DM2 | Nobile Rim 2 |
| de_gerlache_rim_2 | SL2 | de Gerlache Rim (SL2) |
| connecting_ridge_ext | SL3 | Connecting Ridge Extension |
| cabeus_wall | NPA | Cabeus Exterior Wall 1 |
| amundsen_1 | NPB | Amundsen 1 |
| idelson_l | NPC | Idel'son L Crater 1 |
| malapert_crater | NPD | Malapert Crater 1 |
| shackleton_rim_b | LM1 | Shackleton Rim B |
| shoemaker_rim_a | LM2 | Shoemaker Rim A |
| shoemaker_rim_b | LM3 | Shoemaker Rim B |
| shoemaker_rim_c | LM4 | Shoemaker Rim C |
| shoemaker_rim_d | LM5 | Shoemaker Rim D |
| shoemaker_rim_e | LM6 | Shoemaker Rim E |
| faustini_rim_a | LM7 | Faustini Rim A |
| shoemaker_rim_f | LM8 | Shoemaker Rim F |

### B. Slope Texture Generator — `map_generators/slope_texture_generator.py`

Reads slope GeoTIFF, resamples to match heightmap dimensions, and produces
a grayscale diffuse texture.

```python
class SlopeTextureGenerator:
    @staticmethod
    def from_slope_geotiff(
        slope_path: Path,
        target_height: int,
        target_width: int,
    ) -> np.ndarray:
        """Read full slope GeoTIFF and resample to target dimensions.

        Maps slope (degrees) to grayscale: flat=light, steep=dark.
        Returns uint8 RGB array (H, W, 3) for SDF diffuse compatibility.
        """

    @staticmethod
    def from_slope_geotiff_cropped(
        slope_path: Path,
        lat: float, lon: float,
        width_km: float, height_km: float,
        target_height: int, target_width: int,
    ) -> np.ndarray:
        """Crop slope GeoTIFF to bounding box and resample."""
```

**Slope-to-gray mapping:**
- Read slope values (0–90° typically, most <30°)
- Clamp to [0, max_slope] where max_slope = 45° (reasonable lunar max)
- Normalize to [0, 1]
- Map to grayscale: `gray = 190 - slope_norm * 130` → range [60, 190]
  - 60: steep slopes (dark gray, exposed rock)
  - 190: flat areas (light gray, accumulated regolith)
- Replicate to 3-channel RGB for PNG output

### C. Updated SDF Template — `utils/model_writer.py`

Re-add `<diffuse>` to the visual texture block:

```xml
<texture>
  <diffuse>model://${site_id}/materials/textures/diffuse.png</diffuse>
  <normal>model://${site_id}/materials/textures/normal.png</normal>
  <size>10</size>
</texture>
```

**ModelWriter.write()** gains a `diffuse_map: np.ndarray` parameter.
Saves as `diffuse.png` (uint8 RGB) in the textures directory.

### D. Updated SiteConfig — `utils/site_config_parser.py`

Add `from_catalog()` class method for catalog-based construction:

```python
@dataclass
class SiteConfig:
    name: str
    dem_url: str
    extent: Extent = field(default_factory=Extent)
    description: str = ""

    @classmethod
    def from_catalog(cls, site_name: str, extent: Extent | None = None) -> SiteConfig:
        """Construct SiteConfig from the PGDA-78 catalog."""
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
```

`dem_url` stays for backward compatibility — existing YAML configs still work.
The catalog shorthand is additive, not a replacement.

### E. Updated YAML Config Format

Support catalog-based shorthand alongside existing format:

```yaml
sites:
  # Catalog shorthand (recommended)
  - site: connecting_ridge
    extent:
      use_full: true

  # With custom bounding box
  - site: shackleton_rim
    extent:
      use_full: false
      bounding_box:
        lat: -86.5
        lon: -4.0
        width_km: 5.0
        height_km: 5.0

  # Legacy explicit URL (still supported)
  - name: custom_site
    dem_url: "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif"
    extent:
      use_full: true
```

`load_sites()` updated: if `site` key present, resolve via catalog.
If `name` + `dem_url` present, use directly (backward compat).

### F. CLI Redesign — `generate_lunar_sdf.py`

Three modes:

**1. Interactive mode** (no `--site`, no `--config`):
```
$ generate_lunar_sdf --output-dir ./models

Available PGDA-78 Sites:
  1. connecting_ridge      Site 01 – Connecting Ridge
  2. shackleton_rim        Site 04 – Shackleton Rim
  3. nobile_rim_1          Site 06 – Nobile Rim 1
  ...
  27. shoemaker_rim_f      LM8 – Shoemaker Rim F

Select site (number or name): 1

Extent:
  1. Full tile (recommended)
  2. Custom bounding box

Select: 1

Generating connecting_ridge (full extent)...
```

**2. Non-interactive mode** (flag-based):
```
$ generate_lunar_sdf --site connecting_ridge --output-dir ./models
$ generate_lunar_sdf --site connecting_ridge --crop --lat -86.5 --lon -4.0 \
    --width 5 --height 5 --output-dir ./models
```

**3. Batch mode** (YAML config):
```
$ generate_lunar_sdf --config sites.yaml --output-dir ./models
```

**Removed flags:**
- `--dem-url` (URLs derived from catalog)
- `--name` (replaced by `--site` which looks up catalog)
- Old `--site` filter for `--config` mode (use `--site <name>` directly instead)

**Parser structure:**
- `--output-dir` (required)
- `--cache-dir` (optional, default: `<repo>/data/`)
- Mode group (mutually exclusive):
  - `--config <file>` — batch mode
  - `--site <name>` — non-interactive single site
  - (neither) — interactive mode
- Extent options (for `--site` mode):
  - `--use-full-extent` (default if no crop args)
  - `--lat`, `--lon`, `--width`, `--height` — triggers crop mode

### G. Updated Pipeline — `generate_lunar_sdf.py`

```python
def generate(self, site: SiteConfig) -> Path:
    dem_file = self._downloader.download(site.dem_url)
    slope_file = self._downloader.download(site.slope_url)

    if site.extent.use_full:
        heightmap, elev_min, elev_max, bounds = (
            HeightmapGenerator.from_dem_full_extent(dem_file)
        )
        diffuse = SlopeTextureGenerator.from_slope_geotiff(
            slope_file, heightmap.shape[0], heightmap.shape[1]
        )
        ...
    else:
        bb = site.extent.bounding_box
        heightmap, elev_min, elev_max = HeightmapGenerator.from_dem(
            dem_file, bb.lat, bb.lon, bb.width_km, bb.height_km
        )
        diffuse = SlopeTextureGenerator.from_slope_geotiff_cropped(
            slope_file, bb.lat, bb.lon, bb.width_km, bb.height_km,
            heightmap.shape[0], heightmap.shape[1]
        )
        ...

    normal_map = NormalMapGenerator.from_heightmap(heightmap)
    writer.write(..., diffuse_map=diffuse, ...)
```

### H. Updated artemis_sites.yaml

Convert to catalog shorthand:

```yaml
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

## Test Strategy

- **test_site_catalog.py** (new): catalog lookup, URL generation, list_sites, get_site error
- **test_slope_texture.py** (new): from_slope_geotiff shape/dtype, grayscale range, flat slope → light gray
- **test_terrain_processing.py**: update ModelWriter calls with diffuse_map param
- **test_integration.py**: add slope download mock, diffuse texture assertion
- **test_cli.py**: update for new `--site` flag, test interactive mode prompts, remove `--name`/`--dem-url` tests
- **test_site_config.py**: test `from_catalog()`, `slope_url` property, catalog YAML shorthand

## Files Changed

### New files:
- `generate_lunar_sdf/utils/site_catalog.py`
- `generate_lunar_sdf/map_generators/slope_texture_generator.py`
- `test/test_site_catalog.py`
- `test/test_slope_texture.py`

### Modified files:
- `generate_lunar_sdf/utils/site_config_parser.py` — add from_catalog(), slope_url
- `generate_lunar_sdf/utils/model_writer.py` — add diffuse to SDF template + write()
- `generate_lunar_sdf/generate_lunar_sdf.py` — new pipeline + CLI redesign
- `generate_lunar_sdf/map_generators/__init__.py` — export SlopeTextureGenerator
- `generate_lunar_sdf/utils/__init__.py` — export site_catalog functions
- `generate_lunar_sdf/__init__.py` — update exports
- `config/artemis_sites.yaml` — catalog shorthand
- `test/test_terrain_processing.py` — update ModelWriter calls
- `test/test_integration.py` — add slope mock, diffuse assertions
- `test/test_cli.py` — new CLI structure tests
- `test/test_site_config.py` — from_catalog, slope_url, catalog YAML
- `README.md` — document new features

### Pre-built models:
- 4 model.sdf files — re-add `<diffuse>` line with diffuse.png

## Out of Scope

- PBR materials (not supported for SDF heightmaps)
- LOLA intensity/reflectance (not available in PGDA-78 XYZI files)
- Hillshade computation (would double-light with Gazebo's renderer)
- Non-PGDA-78 data sources (removed by design)

# Lunar Base Models Package — Design Spec

**Date:** 2026-04-02
**Status:** Approved (autonomous decision — user away)

## Problem

The Artemis Mission Simulator needs a library of 3D models to populate a demo lunar base world. Currently, the terrain models exist but there are no surface assets (habitats, equipment, astronauts, etc.) to create a compelling demo scene.

## Approach

Create a new ROS 2 ament_cmake package `lunar_base_models` containing:
1. SDF models wrapping NASA 3D Resources (GLB format, public domain)
2. SDF models built from primitives for simple equipment/props
3. LED plugin integration on models where appropriate
4. An env hook for `GZ_SIM_RESOURCE_PATH`

## Model Inventory

### Tier 1 — NASA 3D Resources (GLB → SDF)

| Model | Source | File | Size | Notes |
|-------|--------|------|------|-------|
| `astronaut` | NASA 3D | `Astronaut.glb` | 763 KB | EVA figure, static |
| `habitat_module` | NASA 3D | `Habitat Demonstration Unit (part 1).glb`, `(part 2).glb` | 1.2 MB | Two parts composed in single SDF |
| `rassor` | NASA 3D | `Regolith Advanced Surface Systems Operations Robot (RASSOR).glb` | 6.3 MB | Mining robot, static |

### Tier 2 — SDF Primitive Models

| Model | Description | Geometry |
|-------|-------------|----------|
| `solar_array` | Deployable solar panel array | Boxes (panels) + cylinder (mast) |
| `landing_pad` | Circular pad with markings | Cylinder (pad) + visual decals |
| `equipment_crate` | Storage container | Box with colored accents |
| `comm_antenna` | Dish antenna on mast | Cylinder (mast) + half-sphere (dish) |
| `lunar_flag` | US flag on pole | Cylinder (pole) + thin box (flag) |
| `lunar_rock_a` | Small irregular rock | Scaled box with rough material |
| `lunar_rock_b` | Medium rock | Larger scaled geometry |
| `lunar_rock_c` | Large boulder | Largest variant |
| `light_tower` | Area illumination mast | Cylinder (tower) + point light |
| `pathway_marker` | Ground-level guide bollard | Small cylinder + LED |

### Tier 3 — Fuel References (in demo world, not in package)

These are referenced via Fuel URI directly in the world SDF and are NOT stored locally:
- `https://fuel.gazebosim.org/1.0/OpenRobotics/models/antenna` (optional alternate comm antenna)

## LED Plugin Integration

Uses `jasmeet0915/gz_sim_led_plugin`. Each LED requires a visual element + light element in SDF, configured with named modes.

### Integration Points

| Model | LED Location | LED Group Name | Modes |
|-------|-------------|----------------|-------|
| `habitat_module` | Airlock surround (2 LEDs) | `habitat_airlock` | `safe` (green steady), `cycling` (amber blink), `emergency` (red fast blink) |
| `habitat_module` | Roof beacon (1 LED) | `habitat_beacon` | `idle` (white slow pulse), `emergency` (red fast strobe) |
| `rassor` | Front status bar (2 LEDs) | `rassor_status` | `idle` (blue steady), `operating` (green blink), `fault` (red blink) |
| `solar_array` | Base indicator (1 LED) | `solar_status` | `charging` (green blink), `full` (green steady), `critical` (red blink) |
| `comm_antenna` | Mast indicator (1 LED) | `antenna_link` | `idle` (off), `transmitting` (blue blink), `connected` (green steady) |
| `landing_pad` | Boundary corners (4 LEDs) | `pad_boundary` | `standby` (amber steady), `active` (white fast blink), `emergency` (red strobe) |
| `pathway_marker` | Top face (1 LED) | `marker_light` | `guide` (dim white steady), `active` (bright white), `emergency` (red blink) |
| `light_tower` | Top housing (1 LED) | `tower_light` | `off` (dark), `on` (bright white), `emergency` (red strobe) |

Models WITHOUT LEDs: `astronaut`, `lunar_flag`, `lunar_rock_*`, `equipment_crate`

## Package Structure

```
src/lunar_base_models/
├── CMakeLists.txt
├── package.xml
├── README.md
├── hooks/
│   └── environment/
│       └── lunar_base_models.dsv.in
├── scripts/
│   └── download_nasa_models.sh      # Downloads GLBs from NASA GitHub
├── models/
│   ├── astronaut/
│   │   ├── model.config
│   │   ├── model.sdf
│   │   └── meshes/
│   │       └── astronaut.glb
│   ├── habitat_module/
│   │   ├── model.config
│   │   ├── model.sdf
│   │   └── meshes/
│   │       ├── habitat_part1.glb
│   │       └── habitat_part2.glb
│   ├── rassor/
│   │   ├── model.config
│   │   ├── model.sdf
│   │   └── meshes/
│   │       └── rassor.glb
│   ├── solar_array/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── landing_pad/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── equipment_crate/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── comm_antenna/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── lunar_flag/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── lunar_rock_a/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── lunar_rock_b/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── lunar_rock_c/
│   │   ├── model.config
│   │   └── model.sdf
│   ├── light_tower/
│   │   ├── model.config
│   │   └── model.sdf
│   └── pathway_marker/
│       ├── model.config
│       └── model.sdf
```

## SDF Model Convention

Each model follows the Gazebo model database convention:

**model.config:**
```xml
<?xml version="1.0"?>
<model>
  <name>Model Name</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Brief description</description>
</model>
```

**model.sdf (GLB wrapper):**
```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="model_name">
    <static>true</static>
    <link name="body">
      <visual name="visual">
        <geometry>
          <mesh><uri>meshes/model.glb</uri></mesh>
        </geometry>
      </visual>
      <collision name="collision">
        <geometry>
          <!-- Simplified bounding geometry -->
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
```

**model.sdf (with LED plugin):**
```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="model_name">
    <static>true</static>
    <link name="body">
      <!-- Main visual -->
      <visual name="visual">...</visual>
      <!-- LED visual (small emissive sphere/box) -->
      <visual name="led_status_visual">
        <pose>...</pose>
        <geometry><sphere><radius>0.02</radius></sphere></geometry>
        <material>
          <ambient>0 0 0 1</ambient>
          <diffuse>0 0 0 1</diffuse>
          <emissive>0 1 0 1</emissive>
        </material>
      </visual>
      <!-- LED light (point light near the visual) -->
      <light name="led_status_light" type="point">
        <pose>...</pose>
        <diffuse>0 1 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <range>2</range>
        <attenuation>
          <range>2</range>
          <constant>1</constant>
          <linear>0.5</linear>
          <quadratic>0.2</quadratic>
        </attenuation>
      </light>
    </link>
    <!-- LED Plugin -->
    <plugin filename="LEDPlugin" name="gz::sim::systems::LEDPlugin">
      <led_group name="model_status">
        <led>
          <visual_name>body/led_status_visual</visual_name>
          <light_name>body/led_status_light</light_name>
          <default_state>true</default_state>
        </led>
        <mode name="idle">
          <step><color>0 0.5 1 1</color><intensity>0.5</intensity><always_on>true</always_on></step>
        </mode>
        <mode name="operating">
          <step><color>0 1 0 1</color><intensity>1.0</intensity><on_time>0.5</on_time></step>
          <step><color>0 0 0 1</color><intensity>0.0</intensity><on_time>0.5</on_time></step>
        </mode>
        <mode name="emergency">
          <step><color>1 0 0 1</color><intensity>1.0</intensity><on_time>0.2</on_time></step>
          <step><color>0 0 0 1</color><intensity>0.0</intensity><on_time>0.2</on_time></step>
        </mode>
      </led_group>
    </plugin>
  </model>
</sdf>
```

## NASA Model Download

A shell script `download_nasa_models.sh` downloads the 3 GLB files from `github.com/nasa/NASA-3D-Resources`:

```
Astronaut/Astronaut.glb → models/astronaut/meshes/astronaut.glb
Habitat Demonstration Unit (part 1).glb → models/habitat_module/meshes/habitat_part1.glb
Habitat Demonstration Unit (part 2).glb → models/habitat_module/meshes/habitat_part2.glb
RASSOR.glb → models/rassor/meshes/rassor.glb
```

Total download: ~8.5 MB. Models are public domain per NASA media guidelines.

The GLB files are `.gitignore`d and downloaded on first build or manually.

## Env Hook

```
prepend-non-duplicate;GZ_SIM_RESOURCE_PATH;share/lunar_base_models
```

This makes `models/` discoverable by Gazebo when the workspace is sourced.

## Demo World Update

Update `artemis_mission_launcher/worlds/lunar_surface.world` to include several of these models arranged in a plausible base layout, demonstrating:
- Habitat at center with LED status lights
- Solar arrays nearby
- Landing pad offset from habitat
- RASSOR in operating area
- Comm antenna on elevated position
- Rocks scattered for realism
- Pathway markers between key locations
- Light towers at base perimeter

## Licensing

- NASA 3D models: Public domain ([NASA Media Usage Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/))
- SDF primitive models: Created for this project, same license as repo
- LED plugin: MIT License (jasmeet0915/gz_sim_led_plugin)

## Out of Scope

- Articulated/movable models (rovers with joints, robot arms)
- High-fidelity custom meshes (Blender modeling)
- Starship HLS model (no official 3D model available)
- VIPER rover model (no official 3D model available)
- Interior models (habitat internals)

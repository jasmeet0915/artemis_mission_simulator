# Lunar Base Models

SDF models for the Artemis lunar base simulation. Includes habitats, equipment, rocks,
and LED-integrated infrastructure for use with Gazebo Harmonic.

## Models

### NASA 3D Resources (GLB)

| Model | Description | LED Groups |
|-------|-------------|------------|
| `astronaut` | EVA astronaut figure | — |
| `habitat_module` | Habitat Demonstration Unit | `habitat_airlock`, `habitat_beacon` |
| `rassor` | RASSOR mining robot | `rassor_status` |

### SDF Primitive Props

| Model | Description | LED Groups |
|-------|-------------|------------|
| `equipment_crate` | Storage container | — |
| `lunar_flag` | Flag on pole | — |
| `lunar_rock_a` | Small rock | — |
| `lunar_rock_b` | Medium rock | — |
| `lunar_rock_c` | Large boulder | — |

### LED-Equipped Infrastructure

| Model | Description | LED Groups |
|-------|-------------|------------|
| `solar_array` | Solar panel array | `solar_status` |
| `comm_antenna` | Communications dish | `antenna_link` |
| `landing_pad` | Landing pad with boundary lights | `pad_boundary` |
| `light_tower` | Area illumination tower | `tower_light` |
| `pathway_marker` | Ground-level guide marker | `marker_light` |

## Setup

### Download NASA Models

The astronaut, habitat module, and RASSOR models use GLB meshes from
[NASA 3D Resources](https://github.com/nasa/NASA-3D-Resources) (public domain).

```bash
bash src/lunar_base_models/scripts/download_nasa_models.sh
```

### Build

```bash
colcon build --packages-select lunar_base_models
source install/setup.bash
```

The env hook automatically adds models to `GZ_SIM_RESOURCE_PATH`.

## LED Plugin Integration

Models with LEDs require [gz_sim_led_plugin](https://github.com/jasmeet0915/gz_sim_led_plugin).
Install it in the same workspace:

```bash
git clone https://github.com/jasmeet0915/gz_sim_led_plugin.git src/gz_led_plugin
colcon build --packages-select gz_led_plugin
```

### Changing LED Modes at Runtime

```bash
# Habitat airlock: safe, cycling, emergency
gz topic -t /habitat_airlock/change_led_mode -m gz.msgs.StringMsg -p "data: 'emergency'"

# Landing pad boundary: standby, active, emergency
gz topic -t /pad_boundary/change_led_mode -m gz.msgs.StringMsg -p "data: 'active'"

# Light tower: on, emergency (or "off" to turn off)
gz topic -t /tower_light/change_led_mode -m gz.msgs.StringMsg -p "data: 'on'"
```

## Licensing

- NASA 3D models: Public domain per [NASA Media Usage Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)
- SDF primitive models: Same license as repository
- LED plugin: Apache License 2.0

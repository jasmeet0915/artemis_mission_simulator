# Lunar Base Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a ROS 2 package `lunar_base_models` containing 13 SDF models (3 NASA GLB-wrapped, 10 SDF primitives) with LED plugin integration for 8 models, and update the demo world.

**Architecture:** An ament_cmake package installs static SDF model directories to `share/lunar_base_models/models/`. An env hook adds this path to `GZ_SIM_RESOURCE_PATH`. NASA GLB files are downloaded via a shell script and committed. LED-equipped models use `libLedPlugin.so` from `gz_sim_led_plugin`.

**Tech Stack:** ROS 2 ament_cmake, Gazebo Harmonic SDF 1.9, gz_sim_led_plugin (libLedPlugin.so), curl for downloads

---

### Task 1: Package Scaffolding

**Files:**
- Create: `src/lunar_base_models/package.xml`
- Create: `src/lunar_base_models/CMakeLists.txt`
- Create: `src/lunar_base_models/hooks/environment/lunar_base_models.dsv.in`

- [ ] **Step 1: Create package directory structure**

```bash
mkdir -p src/lunar_base_models/hooks/environment
mkdir -p src/lunar_base_models/scripts
mkdir -p src/lunar_base_models/models
```

- [ ] **Step 2: Create package.xml**

Create `src/lunar_base_models/package.xml`:

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>lunar_base_models</name>
  <version>0.1.0</version>
  <description>SDF models for Artemis lunar base simulation including habitats, equipment, and LED-integrated infrastructure</description>
  <maintainer email="todo@example.com">Artemis Simulator Contributors</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

- [ ] **Step 3: Create CMakeLists.txt**

Create `src/lunar_base_models/CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.8)
project(lunar_base_models)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  models
  DESTINATION share/${PROJECT_NAME}
)

# Environment hook for GZ_SIM_RESOURCE_PATH
ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/hooks/environment/lunar_base_models.dsv.in"
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
```

- [ ] **Step 4: Create env hook**

Create `src/lunar_base_models/hooks/environment/lunar_base_models.dsv.in`:

```
prepend-non-duplicate;GZ_SIM_RESOURCE_PATH;share/lunar_base_models/models
```

- [ ] **Step 5: Verify build**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
colcon build --packages-select lunar_base_models
```

Expected: Build succeeds (empty models directory is fine).

- [ ] **Step 6: Commit**

```bash
git add src/lunar_base_models/
git commit -m "feat(lunar_base_models): scaffold ament_cmake package with env hook

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: NASA GLB Download Script & Model Directories

**Files:**
- Create: `src/lunar_base_models/scripts/download_nasa_models.sh`
- Create: `src/lunar_base_models/models/astronaut/meshes/.gitkeep`
- Create: `src/lunar_base_models/models/habitat_module/meshes/.gitkeep`
- Create: `src/lunar_base_models/models/rassor/meshes/.gitkeep`

- [ ] **Step 1: Create mesh directories with .gitkeep files**

```bash
mkdir -p src/lunar_base_models/models/astronaut/meshes
mkdir -p src/lunar_base_models/models/habitat_module/meshes
mkdir -p src/lunar_base_models/models/rassor/meshes
touch src/lunar_base_models/models/astronaut/meshes/.gitkeep
touch src/lunar_base_models/models/habitat_module/meshes/.gitkeep
touch src/lunar_base_models/models/rassor/meshes/.gitkeep
```

- [ ] **Step 2: Create download script**

Create `src/lunar_base_models/scripts/download_nasa_models.sh`:

```bash
#!/usr/bin/env bash
# Downloads NASA 3D Resources GLB models for lunar base simulation.
# Source: https://github.com/nasa/NASA-3D-Resources (public domain)
#
# Usage: ./download_nasa_models.sh [target_dir]
#   target_dir defaults to the models/ directory next to this script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-${SCRIPT_DIR}/../models}"

BASE_URL="https://raw.githubusercontent.com/nasa/NASA-3D-Resources/main/3D%20Models"

declare -A DOWNLOADS=(
  ["${TARGET_DIR}/astronaut/meshes/astronaut.glb"]="${BASE_URL}/Astronaut/Astronaut.glb"
  ["${TARGET_DIR}/habitat_module/meshes/habitat_part1.glb"]="${BASE_URL}/Habitat%20Demonstration%20Unit/Habitat%20Demonstration%20Unit%20(part%201).glb"
  ["${TARGET_DIR}/habitat_module/meshes/habitat_part2.glb"]="${BASE_URL}/Habitat%20Demonstration%20Unit/Habitat%20Demonstration%20Unit%20(part%202).glb"
  ["${TARGET_DIR}/rassor/meshes/rassor.glb"]="${BASE_URL}/Regolith%20Advanced%20Surface%20Systems%20Operations%20Robot%20(RASSOR)/Regolith%20Advanced%20Surface%20Systems%20Operations%20Robot%20(RASSOR).glb"
)

echo "Downloading NASA 3D models to ${TARGET_DIR}..."

for dest in "${!DOWNLOADS[@]}"; do
  url="${DOWNLOADS[$dest]}"
  filename="$(basename "$dest")"
  if [[ -f "$dest" ]]; then
    echo "  [SKIP] ${filename} already exists"
    continue
  fi
  mkdir -p "$(dirname "$dest")"
  echo "  [GET]  ${filename}..."
  curl -fSL -o "$dest" "$url"
  echo "  [OK]   ${filename} ($(du -h "$dest" | cut -f1))"
done

echo "Done. All NASA models downloaded."
```

- [ ] **Step 3: Make script executable**

```bash
chmod +x src/lunar_base_models/scripts/download_nasa_models.sh
```

- [ ] **Step 4: Run the download script**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
bash src/lunar_base_models/scripts/download_nasa_models.sh
```

Expected: 4 GLB files downloaded to the meshes directories. If curl fails (no internet), note this and continue — user will run it later.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_base_models/scripts/ src/lunar_base_models/models/*/meshes/
git commit -m "feat(lunar_base_models): add NASA model download script and mesh dirs

Downloads astronaut, habitat module, and RASSOR GLBs from
github.com/nasa/NASA-3D-Resources (public domain).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

If GLB files were downloaded successfully, include them in the commit. If not, commit just the script and .gitkeep files.

---

### Task 3: NASA GLB-Wrapped Models (astronaut, habitat_module, rassor)

**Files:**
- Create: `src/lunar_base_models/models/astronaut/model.config`
- Create: `src/lunar_base_models/models/astronaut/model.sdf`
- Create: `src/lunar_base_models/models/habitat_module/model.config`
- Create: `src/lunar_base_models/models/habitat_module/model.sdf`
- Create: `src/lunar_base_models/models/rassor/model.config`
- Create: `src/lunar_base_models/models/rassor/model.sdf`

- [ ] **Step 1: Create astronaut model.config**

Create `src/lunar_base_models/models/astronaut/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Astronaut</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <author>
    <name>NASA</name>
    <email>https://nasa3d.arc.nasa.gov</email>
  </author>
  <description>NASA astronaut EVA figure (from NASA 3D Resources, public domain)</description>
</model>
```

- [ ] **Step 2: Create astronaut model.sdf**

Create `src/lunar_base_models/models/astronaut/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="astronaut">
    <static>true</static>
    <link name="body">
      <visual name="visual">
        <geometry>
          <mesh>
            <uri>meshes/astronaut.glb</uri>
          </mesh>
        </geometry>
      </visual>
      <collision name="collision">
        <pose>0 0 0.9 0 0 0</pose>
        <geometry>
          <box>
            <size>0.5 0.5 1.8</size>
          </box>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
```

- [ ] **Step 3: Create habitat_module model.config**

Create `src/lunar_base_models/models/habitat_module/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Habitat Module</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <author>
    <name>NASA</name>
    <email>https://nasa3d.arc.nasa.gov</email>
  </author>
  <description>NASA Habitat Demonstration Unit with LED status lights (from NASA 3D Resources, public domain)</description>
</model>
```

- [ ] **Step 4: Create habitat_module model.sdf with LED plugin**

Create `src/lunar_base_models/models/habitat_module/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="habitat_module">
    <static>true</static>

    <link name="body">
      <!-- Main habitat mesh: part 1 -->
      <visual name="habitat_part1_visual">
        <geometry>
          <mesh>
            <uri>meshes/habitat_part1.glb</uri>
          </mesh>
        </geometry>
      </visual>

      <!-- Main habitat mesh: part 2 -->
      <visual name="habitat_part2_visual">
        <geometry>
          <mesh>
            <uri>meshes/habitat_part2.glb</uri>
          </mesh>
        </geometry>
      </visual>

      <collision name="collision">
        <pose>0 0 1.5 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>2.5</radius>
            <length>3.0</length>
          </cylinder>
        </geometry>
      </collision>

      <!-- Airlock LED 1 (left side) -->
      <visual name="airlock_led_left_visual">
        <pose>2.5 0.3 1.5 0 0 0</pose>
        <geometry>
          <sphere><radius>0.04</radius></sphere>
        </geometry>
        <material>
          <ambient>0 0.3 0 1</ambient>
          <diffuse>0 0.3 0 1</diffuse>
          <emissive>0 0.5 0 1</emissive>
        </material>
      </visual>
      <light name="airlock_led_left_light" type="point">
        <pose>2.55 0.3 1.5 0 0 0</pose>
        <diffuse>0 1 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>3</range>
          <constant>1.0</constant>
          <linear>0.5</linear>
          <quadratic>0.2</quadratic>
        </attenuation>
      </light>

      <!-- Airlock LED 2 (right side) -->
      <visual name="airlock_led_right_visual">
        <pose>2.5 -0.3 1.5 0 0 0</pose>
        <geometry>
          <sphere><radius>0.04</radius></sphere>
        </geometry>
        <material>
          <ambient>0 0.3 0 1</ambient>
          <diffuse>0 0.3 0 1</diffuse>
          <emissive>0 0.5 0 1</emissive>
        </material>
      </visual>
      <light name="airlock_led_right_light" type="point">
        <pose>2.55 -0.3 1.5 0 0 0</pose>
        <diffuse>0 1 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>3</range>
          <constant>1.0</constant>
          <linear>0.5</linear>
          <quadratic>0.2</quadratic>
        </attenuation>
      </light>

      <!-- Roof beacon LED -->
      <visual name="beacon_led_visual">
        <pose>0 0 3.1 0 0 0</pose>
        <geometry>
          <sphere><radius>0.06</radius></sphere>
        </geometry>
        <material>
          <ambient>0.3 0.3 0.3 1</ambient>
          <diffuse>0.3 0.3 0.3 1</diffuse>
          <emissive>0.5 0.5 0.5 1</emissive>
        </material>
      </visual>
      <light name="beacon_led_light" type="point">
        <pose>0 0 3.2 0 0 0</pose>
        <diffuse>1 1 1 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>10</range>
          <constant>1.0</constant>
          <linear>0.1</linear>
          <quadratic>0.05</quadratic>
        </attenuation>
      </light>
    </link>

    <!-- Airlock LED group -->
    <plugin name="airlock_leds" filename="libLedPlugin.so">
      <led_group_name>habitat_airlock</led_group_name>

      <led name="left_led">
        <visual_name>body/airlock_led_left_visual</visual_name>
        <light_name>body/airlock_led_left_light</light_name>
        <default_state>
          <color>0 0.3 0 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <led name="right_led">
        <visual_name>body/airlock_led_right_visual</visual_name>
        <light_name>body/airlock_led_right_light</light_name>
        <default_state>
          <color>0 0.3 0 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <startup_mode>safe</startup_mode>

      <mode name="safe">
        <step always_on="true">
          <color>0 1 0 1</color>
          <intensity>1.0</intensity>
        </step>
      </mode>

      <mode name="cycling">
        <step always_on="false">
          <color>1 0.7 0 1</color>
          <intensity>1.5</intensity>
          <on_time>0.8</on_time>
        </step>
        <step always_on="false">
          <color>0.3 0.2 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.4</on_time>
        </step>
      </mode>

      <mode name="emergency">
        <step always_on="false">
          <color>1 0 0 1</color>
          <intensity>2.0</intensity>
          <on_time>0.2</on_time>
        </step>
        <step always_on="false">
          <color>0.3 0 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.2</on_time>
        </step>
      </mode>
    </plugin>

    <!-- Beacon LED group -->
    <plugin name="beacon_led" filename="libLedPlugin.so">
      <led_group_name>habitat_beacon</led_group_name>

      <led name="beacon">
        <visual_name>body/beacon_led_visual</visual_name>
        <light_name>body/beacon_led_light</light_name>
        <default_state>
          <color>0.3 0.3 0.3 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <startup_mode>idle</startup_mode>

      <mode name="idle">
        <step always_on="false">
          <color>1 1 1 1</color>
          <intensity>1.0</intensity>
          <on_time>2.0</on_time>
        </step>
        <step always_on="false">
          <color>0.3 0.3 0.3 1</color>
          <intensity>0.0</intensity>
          <on_time>2.0</on_time>
        </step>
      </mode>

      <mode name="emergency">
        <step always_on="false">
          <color>1 0 0 1</color>
          <intensity>2.0</intensity>
          <on_time>0.15</on_time>
        </step>
        <step always_on="false">
          <color>0.3 0 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.15</on_time>
        </step>
      </mode>
    </plugin>
  </model>
</sdf>
```

- [ ] **Step 5: Create rassor model.config**

Create `src/lunar_base_models/models/rassor/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>RASSOR</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <author>
    <name>NASA</name>
    <email>https://nasa3d.arc.nasa.gov</email>
  </author>
  <description>NASA RASSOR regolith mining robot with LED status indicators (from NASA 3D Resources, public domain)</description>
</model>
```

- [ ] **Step 6: Create rassor model.sdf with LED plugin**

Create `src/lunar_base_models/models/rassor/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="rassor">
    <static>true</static>

    <link name="body">
      <visual name="visual">
        <geometry>
          <mesh>
            <uri>meshes/rassor.glb</uri>
          </mesh>
        </geometry>
      </visual>

      <collision name="collision">
        <pose>0 0 0.5 0 0 0</pose>
        <geometry>
          <box>
            <size>2.5 1.4 1.0</size>
          </box>
        </geometry>
      </collision>

      <!-- Status LED left -->
      <visual name="status_led_left_visual">
        <pose>1.2 0.4 0.8 0 0 0</pose>
        <geometry>
          <sphere><radius>0.03</radius></sphere>
        </geometry>
        <material>
          <ambient>0 0 0.3 1</ambient>
          <diffuse>0 0 0.3 1</diffuse>
          <emissive>0 0 0.5 1</emissive>
        </material>
      </visual>
      <light name="status_led_left_light" type="point">
        <pose>1.25 0.4 0.8 0 0 0</pose>
        <diffuse>0 0 1 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>2</range>
          <constant>1.0</constant>
          <linear>0.5</linear>
          <quadratic>0.3</quadratic>
        </attenuation>
      </light>

      <!-- Status LED right -->
      <visual name="status_led_right_visual">
        <pose>1.2 -0.4 0.8 0 0 0</pose>
        <geometry>
          <sphere><radius>0.03</radius></sphere>
        </geometry>
        <material>
          <ambient>0 0 0.3 1</ambient>
          <diffuse>0 0 0.3 1</diffuse>
          <emissive>0 0 0.5 1</emissive>
        </material>
      </visual>
      <light name="status_led_right_light" type="point">
        <pose>1.25 -0.4 0.8 0 0 0</pose>
        <diffuse>0 0 1 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>2</range>
          <constant>1.0</constant>
          <linear>0.5</linear>
          <quadratic>0.3</quadratic>
        </attenuation>
      </light>
    </link>

    <plugin name="status_leds" filename="libLedPlugin.so">
      <led_group_name>rassor_status</led_group_name>

      <led name="left_led">
        <visual_name>body/status_led_left_visual</visual_name>
        <light_name>body/status_led_left_light</light_name>
        <default_state>
          <color>0 0 0.3 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <led name="right_led">
        <visual_name>body/status_led_right_visual</visual_name>
        <light_name>body/status_led_right_light</light_name>
        <default_state>
          <color>0 0 0.3 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <startup_mode>idle</startup_mode>

      <mode name="idle">
        <step always_on="true">
          <color>0 0.3 1 1</color>
          <intensity>0.5</intensity>
        </step>
      </mode>

      <mode name="operating">
        <step always_on="false">
          <color>0 1 0 1</color>
          <intensity>1.5</intensity>
          <on_time>0.5</on_time>
        </step>
        <step always_on="false">
          <color>0 0.3 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.5</on_time>
        </step>
      </mode>

      <mode name="fault">
        <step always_on="false">
          <color>1 0 0 1</color>
          <intensity>2.0</intensity>
          <on_time>0.3</on_time>
        </step>
        <step always_on="false">
          <color>0.3 0 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.3</on_time>
        </step>
      </mode>
    </plugin>
  </model>
</sdf>
```

- [ ] **Step 7: Verify XML validity**

```bash
python3 -c "
import xml.etree.ElementTree as ET
for f in [
    'src/lunar_base_models/models/astronaut/model.config',
    'src/lunar_base_models/models/astronaut/model.sdf',
    'src/lunar_base_models/models/habitat_module/model.config',
    'src/lunar_base_models/models/habitat_module/model.sdf',
    'src/lunar_base_models/models/rassor/model.config',
    'src/lunar_base_models/models/rassor/model.sdf',
]:
    ET.parse(f)
    print(f'OK: {f}')
"
```

Expected: All 6 files parse successfully.

- [ ] **Step 8: Commit**

```bash
git add src/lunar_base_models/models/astronaut/ src/lunar_base_models/models/habitat_module/ src/lunar_base_models/models/rassor/
git commit -m "feat(lunar_base_models): add astronaut, habitat, and RASSOR models

Astronaut: static NASA GLB wrapper
Habitat Module: NASA GLB with airlock + beacon LED groups
RASSOR: NASA GLB with status LED group

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: Simple Prop Models (equipment_crate, lunar_flag, lunar_rock_a/b/c)

**Files:**
- Create: `src/lunar_base_models/models/equipment_crate/model.config`
- Create: `src/lunar_base_models/models/equipment_crate/model.sdf`
- Create: `src/lunar_base_models/models/lunar_flag/model.config`
- Create: `src/lunar_base_models/models/lunar_flag/model.sdf`
- Create: `src/lunar_base_models/models/lunar_rock_a/model.config`
- Create: `src/lunar_base_models/models/lunar_rock_a/model.sdf`
- Create: `src/lunar_base_models/models/lunar_rock_b/model.config`
- Create: `src/lunar_base_models/models/lunar_rock_b/model.sdf`
- Create: `src/lunar_base_models/models/lunar_rock_c/model.config`
- Create: `src/lunar_base_models/models/lunar_rock_c/model.sdf`

- [ ] **Step 1: Create equipment_crate model**

Create `src/lunar_base_models/models/equipment_crate/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Equipment Crate</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Lunar base equipment storage container</description>
</model>
```

Create `src/lunar_base_models/models/equipment_crate/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="equipment_crate">
    <static>true</static>
    <link name="body">
      <!-- Main crate body -->
      <visual name="crate_visual">
        <pose>0 0 0.25 0 0 0</pose>
        <geometry>
          <box><size>1.0 0.6 0.5</size></box>
        </geometry>
        <material>
          <ambient>0.45 0.45 0.42 1</ambient>
          <diffuse>0.45 0.45 0.42 1</diffuse>
          <specular>0.2 0.2 0.2 1</specular>
        </material>
      </visual>
      <!-- Yellow hazard stripe -->
      <visual name="stripe_visual">
        <pose>0 0 0.38 0 0 0</pose>
        <geometry>
          <box><size>1.01 0.61 0.06</size></box>
        </geometry>
        <material>
          <ambient>0.7 0.6 0.0 1</ambient>
          <diffuse>0.7 0.6 0.0 1</diffuse>
        </material>
      </visual>
      <collision name="collision">
        <pose>0 0 0.25 0 0 0</pose>
        <geometry>
          <box><size>1.0 0.6 0.5</size></box>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
```

- [ ] **Step 2: Create lunar_flag model**

Create `src/lunar_base_models/models/lunar_flag/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Lunar Flag</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Flag on pole for lunar surface marking</description>
</model>
```

Create `src/lunar_base_models/models/lunar_flag/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="lunar_flag">
    <static>true</static>
    <link name="body">
      <!-- Pole -->
      <visual name="pole_visual">
        <pose>0 0 1.25 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.015</radius>
            <length>2.5</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.7 0.7 0.7 1</ambient>
          <diffuse>0.7 0.7 0.7 1</diffuse>
          <specular>0.5 0.5 0.5 1</specular>
        </material>
      </visual>
      <!-- Flag (simplified as thin box) -->
      <visual name="flag_visual">
        <pose>0.32 0 2.2 0 0 0</pose>
        <geometry>
          <box><size>0.6 0.005 0.4</size></box>
        </geometry>
        <material>
          <ambient>0.8 0.8 0.8 1</ambient>
          <diffuse>0.8 0.8 0.8 1</diffuse>
        </material>
      </visual>
      <!-- Horizontal support rod -->
      <visual name="rod_visual">
        <pose>0.32 0 2.4 0 1.5708 0</pose>
        <geometry>
          <cylinder>
            <radius>0.008</radius>
            <length>0.6</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.7 0.7 0.7 1</ambient>
          <diffuse>0.7 0.7 0.7 1</diffuse>
          <specular>0.5 0.5 0.5 1</specular>
        </material>
      </visual>
      <collision name="collision">
        <pose>0 0 1.25 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.02</radius>
            <length>2.5</length>
          </cylinder>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
```

- [ ] **Step 3: Create lunar_rock_a model (small)**

Create `src/lunar_base_models/models/lunar_rock_a/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Lunar Rock A</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Small lunar surface rock</description>
</model>
```

Create `src/lunar_base_models/models/lunar_rock_a/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="lunar_rock_a">
    <static>true</static>
    <link name="body">
      <visual name="visual">
        <pose>0 0 0.1 0.2 0.15 0.3</pose>
        <geometry>
          <box><size>0.35 0.28 0.22</size></box>
        </geometry>
        <material>
          <ambient>0.30 0.28 0.26 1</ambient>
          <diffuse>0.35 0.33 0.31 1</diffuse>
          <specular>0.05 0.05 0.05 1</specular>
        </material>
      </visual>
      <collision name="collision">
        <pose>0 0 0.1 0 0 0</pose>
        <geometry>
          <box><size>0.35 0.28 0.22</size></box>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
```

- [ ] **Step 4: Create lunar_rock_b model (medium)**

Create `src/lunar_base_models/models/lunar_rock_b/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Lunar Rock B</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Medium lunar surface rock</description>
</model>
```

Create `src/lunar_base_models/models/lunar_rock_b/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="lunar_rock_b">
    <static>true</static>
    <link name="body">
      <visual name="visual">
        <pose>0 0 0.25 0.1 -0.2 0.4</pose>
        <geometry>
          <box><size>0.75 0.6 0.5</size></box>
        </geometry>
        <material>
          <ambient>0.28 0.26 0.24 1</ambient>
          <diffuse>0.33 0.31 0.29 1</diffuse>
          <specular>0.05 0.05 0.05 1</specular>
        </material>
      </visual>
      <collision name="collision">
        <pose>0 0 0.25 0 0 0</pose>
        <geometry>
          <box><size>0.75 0.6 0.5</size></box>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
```

- [ ] **Step 5: Create lunar_rock_c model (large boulder)**

Create `src/lunar_base_models/models/lunar_rock_c/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Lunar Rock C</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Large lunar boulder</description>
</model>
```

Create `src/lunar_base_models/models/lunar_rock_c/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="lunar_rock_c">
    <static>true</static>
    <link name="body">
      <visual name="visual">
        <pose>0 0 0.5 -0.15 0.1 0.25</pose>
        <geometry>
          <box><size>1.6 1.3 1.1</size></box>
        </geometry>
        <material>
          <ambient>0.25 0.24 0.22 1</ambient>
          <diffuse>0.30 0.29 0.27 1</diffuse>
          <specular>0.04 0.04 0.04 1</specular>
        </material>
      </visual>
      <collision name="collision">
        <pose>0 0 0.5 0 0 0</pose>
        <geometry>
          <box><size>1.6 1.3 1.1</size></box>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
```

- [ ] **Step 6: Verify XML validity**

```bash
python3 -c "
import xml.etree.ElementTree as ET
import glob
for f in sorted(glob.glob('src/lunar_base_models/models/equipment_crate/*')) + \
         sorted(glob.glob('src/lunar_base_models/models/lunar_flag/*')) + \
         sorted(glob.glob('src/lunar_base_models/models/lunar_rock_*/*')):
    if f.endswith(('.config', '.sdf')):
        ET.parse(f)
        print(f'OK: {f}')
"
```

Expected: All 10 files parse successfully.

- [ ] **Step 7: Commit**

```bash
git add src/lunar_base_models/models/equipment_crate/ src/lunar_base_models/models/lunar_flag/ src/lunar_base_models/models/lunar_rock_*/
git commit -m "feat(lunar_base_models): add equipment crate, flag, and rock models

Simple SDF primitive models for lunar base scene props.
Three rock size variants with regolith-gray coloring.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 5: LED-Equipped Infrastructure Models

**Files:**
- Create: `src/lunar_base_models/models/solar_array/model.config`
- Create: `src/lunar_base_models/models/solar_array/model.sdf`
- Create: `src/lunar_base_models/models/comm_antenna/model.config`
- Create: `src/lunar_base_models/models/comm_antenna/model.sdf`
- Create: `src/lunar_base_models/models/landing_pad/model.config`
- Create: `src/lunar_base_models/models/landing_pad/model.sdf`
- Create: `src/lunar_base_models/models/light_tower/model.config`
- Create: `src/lunar_base_models/models/light_tower/model.sdf`
- Create: `src/lunar_base_models/models/pathway_marker/model.config`
- Create: `src/lunar_base_models/models/pathway_marker/model.sdf`

- [ ] **Step 1: Create solar_array model**

Create `src/lunar_base_models/models/solar_array/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Solar Array</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Deployable solar panel array with charge status LED</description>
</model>
```

Create `src/lunar_base_models/models/solar_array/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="solar_array">
    <static>true</static>

    <link name="body">
      <!-- Mast -->
      <visual name="mast_visual">
        <pose>0 0 1.0 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.04</radius>
            <length>2.0</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.5 0.5 0.5 1</ambient>
          <diffuse>0.6 0.6 0.6 1</diffuse>
          <specular>0.3 0.3 0.3 1</specular>
        </material>
      </visual>

      <!-- Left panel -->
      <visual name="panel_left_visual">
        <pose>-0.55 0 2.0 0 0.15 0</pose>
        <geometry>
          <box><size>1.0 0.05 2.0</size></box>
        </geometry>
        <material>
          <ambient>0.02 0.04 0.12 1</ambient>
          <diffuse>0.05 0.08 0.2 1</diffuse>
          <specular>0.3 0.3 0.4 1</specular>
        </material>
      </visual>

      <!-- Right panel -->
      <visual name="panel_right_visual">
        <pose>0.55 0 2.0 0 -0.15 0</pose>
        <geometry>
          <box><size>1.0 0.05 2.0</size></box>
        </geometry>
        <material>
          <ambient>0.02 0.04 0.12 1</ambient>
          <diffuse>0.05 0.08 0.2 1</diffuse>
          <specular>0.3 0.3 0.4 1</specular>
        </material>
      </visual>

      <!-- Base plate -->
      <visual name="base_visual">
        <pose>0 0 0.02 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.3</radius>
            <length>0.04</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.4 0.4 0.4 1</ambient>
          <diffuse>0.5 0.5 0.5 1</diffuse>
        </material>
      </visual>

      <collision name="collision_mast">
        <pose>0 0 1.0 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.06</radius>
            <length>2.0</length>
          </cylinder>
        </geometry>
      </collision>
      <collision name="collision_panels">
        <pose>0 0 2.0 0 0 0</pose>
        <geometry>
          <box><size>2.2 0.1 2.0</size></box>
        </geometry>
      </collision>

      <!-- Status LED -->
      <visual name="status_led_visual">
        <pose>0.08 0 0.15 0 0 0</pose>
        <geometry>
          <sphere><radius>0.025</radius></sphere>
        </geometry>
        <material>
          <ambient>0 0.2 0 1</ambient>
          <diffuse>0 0.2 0 1</diffuse>
          <emissive>0 0.3 0 1</emissive>
        </material>
      </visual>
      <light name="status_led_light" type="point">
        <pose>0.1 0 0.15 0 0 0</pose>
        <diffuse>0 1 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>2</range>
          <constant>1.0</constant>
          <linear>0.5</linear>
          <quadratic>0.3</quadratic>
        </attenuation>
      </light>
    </link>

    <plugin name="status_led" filename="libLedPlugin.so">
      <led_group_name>solar_status</led_group_name>

      <led name="status">
        <visual_name>body/status_led_visual</visual_name>
        <light_name>body/status_led_light</light_name>
        <default_state>
          <color>0 0.2 0 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <startup_mode>charging</startup_mode>

      <mode name="charging">
        <step always_on="false">
          <color>0 1 0 1</color>
          <intensity>1.0</intensity>
          <on_time>1.0</on_time>
        </step>
        <step always_on="false">
          <color>0 0.2 0 1</color>
          <intensity>0.0</intensity>
          <on_time>1.0</on_time>
        </step>
      </mode>

      <mode name="full">
        <step always_on="true">
          <color>0 1 0 1</color>
          <intensity>1.0</intensity>
        </step>
      </mode>

      <mode name="critical">
        <step always_on="false">
          <color>1 0 0 1</color>
          <intensity>2.0</intensity>
          <on_time>0.3</on_time>
        </step>
        <step always_on="false">
          <color>0.3 0 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.3</on_time>
        </step>
      </mode>
    </plugin>
  </model>
</sdf>
```

- [ ] **Step 2: Create comm_antenna model**

Create `src/lunar_base_models/models/comm_antenna/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Communications Antenna</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Lunar base communications dish antenna with link status LED</description>
</model>
```

Create `src/lunar_base_models/models/comm_antenna/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="comm_antenna">
    <static>true</static>

    <link name="body">
      <!-- Mast -->
      <visual name="mast_visual">
        <pose>0 0 2.0 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.05</radius>
            <length>4.0</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.5 0.5 0.5 1</ambient>
          <diffuse>0.6 0.6 0.6 1</diffuse>
          <specular>0.3 0.3 0.3 1</specular>
        </material>
      </visual>

      <!-- Dish (simplified as wide short cylinder tilted) -->
      <visual name="dish_visual">
        <pose>0 0 4.0 0.4 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.5</radius>
            <length>0.08</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.7 0.7 0.7 1</ambient>
          <diffuse>0.8 0.8 0.8 1</diffuse>
          <specular>0.4 0.4 0.4 1</specular>
        </material>
      </visual>

      <!-- Feed horn (small cylinder in front of dish) -->
      <visual name="feed_visual">
        <pose>0 0.25 4.2 0.4 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.03</radius>
            <length>0.5</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.5 0.5 0.5 1</ambient>
          <diffuse>0.6 0.6 0.6 1</diffuse>
        </material>
      </visual>

      <!-- Base plate -->
      <visual name="base_visual">
        <pose>0 0 0.03 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.35</radius>
            <length>0.06</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.4 0.4 0.4 1</ambient>
          <diffuse>0.5 0.5 0.5 1</diffuse>
        </material>
      </visual>

      <collision name="collision_mast">
        <pose>0 0 2.0 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.08</radius>
            <length>4.0</length>
          </cylinder>
        </geometry>
      </collision>
      <collision name="collision_dish">
        <pose>0 0 4.0 0.4 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.5</radius>
            <length>0.1</length>
          </cylinder>
        </geometry>
      </collision>

      <!-- Link status LED -->
      <visual name="link_led_visual">
        <pose>0.08 0 0.5 0 0 0</pose>
        <geometry>
          <sphere><radius>0.025</radius></sphere>
        </geometry>
        <material>
          <ambient>0.1 0.1 0.1 1</ambient>
          <diffuse>0.1 0.1 0.1 1</diffuse>
          <emissive>0 0 0 1</emissive>
        </material>
      </visual>
      <light name="link_led_light" type="point">
        <pose>0.1 0 0.5 0 0 0</pose>
        <diffuse>0 0 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>2</range>
          <constant>1.0</constant>
          <linear>0.5</linear>
          <quadratic>0.3</quadratic>
        </attenuation>
      </light>
    </link>

    <plugin name="link_led" filename="libLedPlugin.so">
      <led_group_name>antenna_link</led_group_name>

      <led name="link">
        <visual_name>body/link_led_visual</visual_name>
        <light_name>body/link_led_light</light_name>
        <default_state>
          <color>0.1 0.1 0.1 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <mode name="transmitting">
        <step always_on="false">
          <color>0 0.5 1 1</color>
          <intensity>1.5</intensity>
          <on_time>0.3</on_time>
        </step>
        <step always_on="false">
          <color>0 0.1 0.3 1</color>
          <intensity>0.0</intensity>
          <on_time>0.3</on_time>
        </step>
      </mode>

      <mode name="connected">
        <step always_on="true">
          <color>0 1 0 1</color>
          <intensity>1.0</intensity>
        </step>
      </mode>
    </plugin>
  </model>
</sdf>
```

- [ ] **Step 3: Create landing_pad model**

Create `src/lunar_base_models/models/landing_pad/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Landing Pad</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Lunar landing pad with boundary LED lights</description>
</model>
```

Create `src/lunar_base_models/models/landing_pad/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="landing_pad">
    <static>true</static>

    <link name="body">
      <!-- Main pad surface -->
      <visual name="pad_visual">
        <pose>0 0 0.025 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>5.0</radius>
            <length>0.05</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.4 0.4 0.38 1</ambient>
          <diffuse>0.5 0.5 0.48 1</diffuse>
          <specular>0.15 0.15 0.15 1</specular>
        </material>
      </visual>

      <!-- Center marking circle -->
      <visual name="center_mark_visual">
        <pose>0 0 0.055 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>1.0</radius>
            <length>0.01</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.7 0.5 0 1</ambient>
          <diffuse>0.8 0.6 0 1</diffuse>
        </material>
      </visual>

      <collision name="collision">
        <pose>0 0 0.025 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>5.0</radius>
            <length>0.05</length>
          </cylinder>
        </geometry>
      </collision>

      <!-- Boundary LED NE -->
      <visual name="boundary_led_ne_visual">
        <pose>3.5 3.5 0.1 0 0 0</pose>
        <geometry>
          <sphere><radius>0.05</radius></sphere>
        </geometry>
        <material>
          <ambient>0.4 0.25 0 1</ambient>
          <diffuse>0.4 0.25 0 1</diffuse>
          <emissive>0.6 0.4 0 1</emissive>
        </material>
      </visual>
      <light name="boundary_led_ne_light" type="point">
        <pose>3.5 3.5 0.15 0 0 0</pose>
        <diffuse>1 0.7 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>5</range>
          <constant>1.0</constant>
          <linear>0.3</linear>
          <quadratic>0.1</quadratic>
        </attenuation>
      </light>

      <!-- Boundary LED NW -->
      <visual name="boundary_led_nw_visual">
        <pose>-3.5 3.5 0.1 0 0 0</pose>
        <geometry>
          <sphere><radius>0.05</radius></sphere>
        </geometry>
        <material>
          <ambient>0.4 0.25 0 1</ambient>
          <diffuse>0.4 0.25 0 1</diffuse>
          <emissive>0.6 0.4 0 1</emissive>
        </material>
      </visual>
      <light name="boundary_led_nw_light" type="point">
        <pose>-3.5 3.5 0.15 0 0 0</pose>
        <diffuse>1 0.7 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>5</range>
          <constant>1.0</constant>
          <linear>0.3</linear>
          <quadratic>0.1</quadratic>
        </attenuation>
      </light>

      <!-- Boundary LED SE -->
      <visual name="boundary_led_se_visual">
        <pose>3.5 -3.5 0.1 0 0 0</pose>
        <geometry>
          <sphere><radius>0.05</radius></sphere>
        </geometry>
        <material>
          <ambient>0.4 0.25 0 1</ambient>
          <diffuse>0.4 0.25 0 1</diffuse>
          <emissive>0.6 0.4 0 1</emissive>
        </material>
      </visual>
      <light name="boundary_led_se_light" type="point">
        <pose>3.5 -3.5 0.15 0 0 0</pose>
        <diffuse>1 0.7 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>5</range>
          <constant>1.0</constant>
          <linear>0.3</linear>
          <quadratic>0.1</quadratic>
        </attenuation>
      </light>

      <!-- Boundary LED SW -->
      <visual name="boundary_led_sw_visual">
        <pose>-3.5 -3.5 0.1 0 0 0</pose>
        <geometry>
          <sphere><radius>0.05</radius></sphere>
        </geometry>
        <material>
          <ambient>0.4 0.25 0 1</ambient>
          <diffuse>0.4 0.25 0 1</diffuse>
          <emissive>0.6 0.4 0 1</emissive>
        </material>
      </visual>
      <light name="boundary_led_sw_light" type="point">
        <pose>-3.5 -3.5 0.15 0 0 0</pose>
        <diffuse>1 0.7 0 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>5</range>
          <constant>1.0</constant>
          <linear>0.3</linear>
          <quadratic>0.1</quadratic>
        </attenuation>
      </light>
    </link>

    <plugin name="boundary_leds" filename="libLedPlugin.so">
      <led_group_name>pad_boundary</led_group_name>

      <led name="ne">
        <visual_name>body/boundary_led_ne_visual</visual_name>
        <light_name>body/boundary_led_ne_light</light_name>
        <default_state>
          <color>0.4 0.25 0 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>
      <led name="nw">
        <visual_name>body/boundary_led_nw_visual</visual_name>
        <light_name>body/boundary_led_nw_light</light_name>
        <default_state>
          <color>0.4 0.25 0 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>
      <led name="se">
        <visual_name>body/boundary_led_se_visual</visual_name>
        <light_name>body/boundary_led_se_light</light_name>
        <default_state>
          <color>0.4 0.25 0 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>
      <led name="sw">
        <visual_name>body/boundary_led_sw_visual</visual_name>
        <light_name>body/boundary_led_sw_light</light_name>
        <default_state>
          <color>0.4 0.25 0 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <startup_mode>standby</startup_mode>

      <mode name="standby">
        <step always_on="true">
          <color>1 0.7 0 1</color>
          <intensity>0.8</intensity>
        </step>
      </mode>

      <mode name="active">
        <step always_on="false">
          <color>1 1 1 1</color>
          <intensity>2.0</intensity>
          <on_time>0.25</on_time>
        </step>
        <step always_on="false">
          <color>0.3 0.3 0.3 1</color>
          <intensity>0.0</intensity>
          <on_time>0.25</on_time>
        </step>
      </mode>

      <mode name="emergency">
        <step always_on="false">
          <color>1 0 0 1</color>
          <intensity>2.0</intensity>
          <on_time>0.15</on_time>
        </step>
        <step always_on="false">
          <color>0.3 0 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.15</on_time>
        </step>
      </mode>
    </plugin>
  </model>
</sdf>
```

- [ ] **Step 4: Create light_tower model**

Create `src/lunar_base_models/models/light_tower/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Light Tower</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Lunar base area illumination tower with LED</description>
</model>
```

Create `src/lunar_base_models/models/light_tower/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="light_tower">
    <static>true</static>

    <link name="body">
      <!-- Tower mast -->
      <visual name="mast_visual">
        <pose>0 0 1.5 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.04</radius>
            <length>3.0</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.45 0.45 0.45 1</ambient>
          <diffuse>0.55 0.55 0.55 1</diffuse>
          <specular>0.3 0.3 0.3 1</specular>
        </material>
      </visual>

      <!-- Light housing -->
      <visual name="housing_visual">
        <pose>0 0 3.0 0 0 0</pose>
        <geometry>
          <box><size>0.2 0.2 0.12</size></box>
        </geometry>
        <material>
          <ambient>0.35 0.35 0.35 1</ambient>
          <diffuse>0.45 0.45 0.45 1</diffuse>
        </material>
      </visual>

      <!-- Base plate -->
      <visual name="base_visual">
        <pose>0 0 0.02 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.2</radius>
            <length>0.04</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.4 0.4 0.4 1</ambient>
          <diffuse>0.5 0.5 0.5 1</diffuse>
        </material>
      </visual>

      <collision name="collision">
        <pose>0 0 1.5 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.06</radius>
            <length>3.0</length>
          </cylinder>
        </geometry>
      </collision>

      <!-- Tower LED -->
      <visual name="tower_led_visual">
        <pose>0 0 2.95 0 0 0</pose>
        <geometry>
          <sphere><radius>0.06</radius></sphere>
        </geometry>
        <material>
          <ambient>0.2 0.2 0.2 1</ambient>
          <diffuse>0.2 0.2 0.2 1</diffuse>
          <emissive>0 0 0 1</emissive>
        </material>
      </visual>
      <light name="tower_led_light" type="point">
        <pose>0 0 3.05 0 0 0</pose>
        <diffuse>1 1 1 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>15</range>
          <constant>1.0</constant>
          <linear>0.05</linear>
          <quadratic>0.02</quadratic>
        </attenuation>
      </light>
    </link>

    <plugin name="tower_led" filename="libLedPlugin.so">
      <led_group_name>tower_light</led_group_name>

      <led name="main">
        <visual_name>body/tower_led_visual</visual_name>
        <light_name>body/tower_led_light</light_name>
        <default_state>
          <color>0.2 0.2 0.2 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <mode name="on">
        <step always_on="true">
          <color>1 1 0.95 1</color>
          <intensity>3.0</intensity>
        </step>
      </mode>

      <mode name="emergency">
        <step always_on="false">
          <color>1 0 0 1</color>
          <intensity>3.0</intensity>
          <on_time>0.5</on_time>
        </step>
        <step always_on="false">
          <color>0.2 0 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.5</on_time>
        </step>
      </mode>
    </plugin>
  </model>
</sdf>
```

- [ ] **Step 5: Create pathway_marker model**

Create `src/lunar_base_models/models/pathway_marker/model.config`:

```xml
<?xml version="1.0"?>
<model>
  <name>Pathway Marker</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>Ground-level pathway guide marker with LED</description>
</model>
```

Create `src/lunar_base_models/models/pathway_marker/model.sdf`:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="pathway_marker">
    <static>true</static>

    <link name="body">
      <!-- Bollard body -->
      <visual name="bollard_visual">
        <pose>0 0 0.2 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.06</radius>
            <length>0.4</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.35 0.33 0.31 1</ambient>
          <diffuse>0.4 0.38 0.36 1</diffuse>
          <specular>0.15 0.15 0.15 1</specular>
        </material>
      </visual>

      <!-- Reflective band -->
      <visual name="band_visual">
        <pose>0 0 0.35 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.065</radius>
            <length>0.04</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.6 0.6 0.6 1</ambient>
          <diffuse>0.7 0.7 0.7 1</diffuse>
          <specular>0.5 0.5 0.5 1</specular>
        </material>
      </visual>

      <collision name="collision">
        <pose>0 0 0.2 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.07</radius>
            <length>0.4</length>
          </cylinder>
        </geometry>
      </collision>

      <!-- Guide LED (top) -->
      <visual name="guide_led_visual">
        <pose>0 0 0.42 0 0 0</pose>
        <geometry>
          <sphere><radius>0.03</radius></sphere>
        </geometry>
        <material>
          <ambient>0.15 0.15 0.15 1</ambient>
          <diffuse>0.15 0.15 0.15 1</diffuse>
          <emissive>0.2 0.2 0.2 1</emissive>
        </material>
      </visual>
      <light name="guide_led_light" type="point">
        <pose>0 0 0.45 0 0 0</pose>
        <diffuse>1 1 1 1</diffuse>
        <specular>0 0 0 1</specular>
        <attenuation>
          <range>3</range>
          <constant>1.0</constant>
          <linear>0.4</linear>
          <quadratic>0.2</quadratic>
        </attenuation>
      </light>
    </link>

    <plugin name="guide_led" filename="libLedPlugin.so">
      <led_group_name>marker_light</led_group_name>

      <led name="guide">
        <visual_name>body/guide_led_visual</visual_name>
        <light_name>body/guide_led_light</light_name>
        <default_state>
          <color>0.15 0.15 0.15 1</color>
          <intensity>0.0</intensity>
        </default_state>
      </led>

      <startup_mode>guide</startup_mode>

      <mode name="guide">
        <step always_on="true">
          <color>0.6 0.6 0.55 1</color>
          <intensity>0.5</intensity>
        </step>
      </mode>

      <mode name="active">
        <step always_on="true">
          <color>1 1 0.95 1</color>
          <intensity>1.5</intensity>
        </step>
      </mode>

      <mode name="emergency">
        <step always_on="false">
          <color>1 0 0 1</color>
          <intensity>2.0</intensity>
          <on_time>0.3</on_time>
        </step>
        <step always_on="false">
          <color>0.2 0 0 1</color>
          <intensity>0.0</intensity>
          <on_time>0.3</on_time>
        </step>
      </mode>
    </plugin>
  </model>
</sdf>
```

- [ ] **Step 6: Verify XML validity**

```bash
python3 -c "
import xml.etree.ElementTree as ET
import glob
for d in ['solar_array', 'comm_antenna', 'landing_pad', 'light_tower', 'pathway_marker']:
    for f in sorted(glob.glob(f'src/lunar_base_models/models/{d}/*')):
        if f.endswith(('.config', '.sdf')):
            ET.parse(f)
            print(f'OK: {f}')
"
```

Expected: All 10 files parse successfully.

- [ ] **Step 7: Commit**

```bash
git add src/lunar_base_models/models/solar_array/ src/lunar_base_models/models/comm_antenna/ src/lunar_base_models/models/landing_pad/ src/lunar_base_models/models/light_tower/ src/lunar_base_models/models/pathway_marker/
git commit -m "feat(lunar_base_models): add LED-equipped infrastructure models

Solar array, comm antenna, landing pad, light tower, and pathway
marker. All include gz_sim_led_plugin integration with named modes.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 6: Demo World Layout

**Files:**
- Modify: `src/artemis_mission_launcher/worlds/lunar_surface.world`

- [ ] **Step 1: Update lunar_surface.world with model includes**

Replace the entire contents of `src/artemis_mission_launcher/worlds/lunar_surface.world` with:

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <world name="lunar_surface">

    <!-- Lunar gravity: 1.625 m/s² (≈ 1/6 Earth) -->
    <gravity>0 0 -1.625</gravity>

    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
    </physics>

    <!-- Black sky, no atmosphere -->
    <scene>
      <ambient>0.05 0.05 0.05 1.0</ambient>
      <background>0 0 0 1.0</background>
      <shadows>true</shadows>
    </scene>

    <!-- Sun: directional light approximating low-angle polar illumination -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 100 0 0 0</pose>
      <diffuse>1.0 1.0 0.98 1.0</diffuse>
      <specular>0.5 0.5 0.48 1.0</specular>
      <attenuation>
        <range>10000</range>
        <constant>0.9</constant>
        <linear>0.0</linear>
        <quadratic>0.0</quadratic>
      </attenuation>
      <!-- Low elevation angle typical for south pole -->
      <direction>0.5 0.2 -0.3</direction>
    </light>

    <!-- Required Gazebo Harmonic system plugins -->
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics">
      <engine>
        <filename>gz-physics-dartsim-plugin</filename>
      </engine>
    </plugin>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>

    <!-- ==================== LUNAR BASE LAYOUT ==================== -->

    <!-- Habitat Module (base center) -->
    <include>
      <uri>model://habitat_module</uri>
      <name>habitat</name>
      <pose>0 0 0 0 0 0</pose>
    </include>

    <!-- Landing Pad (offset from habitat) -->
    <include>
      <uri>model://landing_pad</uri>
      <name>landing_pad</name>
      <pose>30 0 0 0 0 0</pose>
    </include>

    <!-- Solar Arrays (near habitat) -->
    <include>
      <uri>model://solar_array</uri>
      <name>solar_array_1</name>
      <pose>-8 6 0 0 0 0</pose>
    </include>
    <include>
      <uri>model://solar_array</uri>
      <name>solar_array_2</name>
      <pose>-8 -6 0 0 0 0</pose>
    </include>

    <!-- Communications Antenna (elevated position) -->
    <include>
      <uri>model://comm_antenna</uri>
      <name>comm_antenna</name>
      <pose>-5 0 0 0 0 0</pose>
    </include>

    <!-- RASSOR mining robot (work area) -->
    <include>
      <uri>model://rassor</uri>
      <name>rassor</name>
      <pose>12 -8 0 0 0 0.3</pose>
    </include>

    <!-- Astronaut near habitat -->
    <include>
      <uri>model://astronaut</uri>
      <name>astronaut_1</name>
      <pose>4 1 0 0 0 -0.5</pose>
    </include>

    <!-- Equipment Crates -->
    <include>
      <uri>model://equipment_crate</uri>
      <name>crate_1</name>
      <pose>3 -3 0 0 0 0.2</pose>
    </include>
    <include>
      <uri>model://equipment_crate</uri>
      <name>crate_2</name>
      <pose>3 -4.2 0 0 0 -0.1</pose>
    </include>

    <!-- Lunar Flag -->
    <include>
      <uri>model://lunar_flag</uri>
      <name>flag</name>
      <pose>6 3 0 0 0 0</pose>
    </include>

    <!-- Light Towers (base perimeter) -->
    <include>
      <uri>model://light_tower</uri>
      <name>tower_north</name>
      <pose>0 12 0 0 0 0</pose>
    </include>
    <include>
      <uri>model://light_tower</uri>
      <name>tower_south</name>
      <pose>0 -12 0 0 0 0</pose>
    </include>
    <include>
      <uri>model://light_tower</uri>
      <name>tower_east</name>
      <pose>12 0 0 0 0 0</pose>
    </include>

    <!-- Pathway Markers (habitat to landing pad) -->
    <include>
      <uri>model://pathway_marker</uri>
      <name>marker_1</name>
      <pose>7 0 0 0 0 0</pose>
    </include>
    <include>
      <uri>model://pathway_marker</uri>
      <name>marker_2</name>
      <pose>13 0 0 0 0 0</pose>
    </include>
    <include>
      <uri>model://pathway_marker</uri>
      <name>marker_3</name>
      <pose>19 0 0 0 0 0</pose>
    </include>
    <include>
      <uri>model://pathway_marker</uri>
      <name>marker_4</name>
      <pose>25 0 0 0 0 0</pose>
    </include>

    <!-- Scattered Rocks -->
    <include>
      <uri>model://lunar_rock_a</uri>
      <name>rock_1</name>
      <pose>8 5 0 0 0 0.8</pose>
    </include>
    <include>
      <uri>model://lunar_rock_a</uri>
      <name>rock_2</name>
      <pose>-3 8 0 0 0 2.1</pose>
    </include>
    <include>
      <uri>model://lunar_rock_b</uri>
      <name>rock_3</name>
      <pose>15 6 0 0 0 1.2</pose>
    </include>
    <include>
      <uri>model://lunar_rock_b</uri>
      <name>rock_4</name>
      <pose>-6 -10 0 0 0 0.5</pose>
    </include>
    <include>
      <uri>model://lunar_rock_c</uri>
      <name>rock_5</name>
      <pose>-12 5 0 0 0 0.9</pose>
    </include>
    <include>
      <uri>model://lunar_rock_c</uri>
      <name>rock_6</name>
      <pose>20 -10 0 0 0 2.5</pose>
    </include>

  </world>
</sdf>
```

- [ ] **Step 2: Verify XML validity**

```bash
python3 -c "
import xml.etree.ElementTree as ET
ET.parse('src/artemis_mission_launcher/worlds/lunar_surface.world')
print('OK: world file is valid XML')
"
```

- [ ] **Step 3: Commit**

```bash
git add src/artemis_mission_launcher/worlds/lunar_surface.world
git commit -m "feat(artemis_mission_launcher): populate demo world with lunar base models

Layout includes habitat, landing pad, solar arrays, comm antenna,
RASSOR, astronaut, crates, flag, light towers, pathway markers,
and scattered rocks.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 7: README & Build Verification

**Files:**
- Create: `src/lunar_base_models/README.md`
- Verify: `colcon build` succeeds for all packages

- [ ] **Step 1: Create README**

Create `src/lunar_base_models/README.md`:

````markdown
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
````

- [ ] **Step 2: Add lunar_base_models dependency to artemis_mission_launcher**

Edit `src/artemis_mission_launcher/package.xml` to add:

```xml
<exec_depend>lunar_base_models</exec_depend>
```

Add this line after the existing `<exec_depend>lunar_terrain_generator</exec_depend>` line.

- [ ] **Step 3: Build all packages**

```bash
cd /home/singh/ros_workspaces/artemis_mission_simulator
colcon build
```

Expected: All 3 packages build successfully (lunar_terrain_generator, lunar_base_models, artemis_mission_launcher).

- [ ] **Step 4: Verify model count**

```bash
ls -d src/lunar_base_models/models/*/model.sdf | wc -l
```

Expected: 13 (astronaut, habitat_module, rassor, equipment_crate, lunar_flag, lunar_rock_a, lunar_rock_b, lunar_rock_c, solar_array, comm_antenna, landing_pad, light_tower, pathway_marker)

- [ ] **Step 5: Validate all XML files**

```bash
python3 -c "
import xml.etree.ElementTree as ET
import glob
count = 0
for f in sorted(glob.glob('src/lunar_base_models/models/*/*')):
    if f.endswith(('.config', '.sdf')):
        ET.parse(f)
        count += 1
ET.parse('src/artemis_mission_launcher/worlds/lunar_surface.world')
count += 1
print(f'All {count} XML files valid')
"
```

Expected: All 27 XML files valid (13 model.config + 13 model.sdf + 1 world).

- [ ] **Step 6: Commit**

```bash
git add src/lunar_base_models/README.md src/artemis_mission_launcher/package.xml
git commit -m "docs(lunar_base_models): add README with model catalog and LED usage guide

Also adds lunar_base_models as dependency of artemis_mission_launcher.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

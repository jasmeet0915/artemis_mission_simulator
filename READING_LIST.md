# Reading List — Theory & Background

Everything you need to understand the technologies and techniques used in the
Artemis Mission Simulator. Organized from foundational concepts to
project-specific details.

---

## 1. Heightmaps (Displacement Maps)

A heightmap is a 2D image where each pixel's brightness represents elevation.
This is how we turn satellite elevation data into 3D terrain without creating
heavy 3D mesh files.

- **What is a heightmap:**
  https://en.wikipedia.org/wiki/Heightmap

- **How game engines use heightmaps for terrain:**
  https://docs.unity3d.com/Manual/terrain-Heightmaps.html
  (Unity docs, but the concept is universal — Gazebo uses the same approach)

- **Why power-of-2+1 resolution (257, 513, 1025)?**
  Terrain engines subdivide the heightmap into a grid of quads. A 513×513
  image creates 512×512 quads. The +1 is because you need one more vertex
  than the number of quads in each direction (fence-post problem).

- **16-bit vs 8-bit heightmaps:**
  8-bit gives 256 height levels (staircase artifacts). 16-bit gives 65,536
  levels — smooth enough for realistic terrain. Gazebo Harmonic supports both.

---

## 2. Texture Mapping

How 2D images are painted onto 3D surfaces.

- **Diffuse / Albedo map:**
  The base color texture. For lunar terrain, this comes from LROC WAC
  reflectance data — it captures the actual surface color/brightness.
  https://en.wikipedia.org/wiki/Texture_mapping

- **Normal map:**
  A special RGB texture that encodes surface orientation per pixel. It makes
  flat geometry look bumpy by changing how light reflects. Each pixel stores
  a 3D normal vector: R=X, G=Y, B=Z, mapped from [-1,1] to [0,255].
  https://en.wikipedia.org/wiki/Normal_mapping

- **Learn OpenGL — Normal Mapping (excellent visual tutorial):**
  https://learnopengl.com/Advanced-Lighting/Normal-Mapping

- **PBR (Physically Based Rendering) basics:**
  Modern rendering uses PBR materials (albedo + normal + roughness + metallic).
  For lunar regolith we only need albedo + normal. Roughness is uniformly high
  (regolith is matte), metallic is 0.
  https://learnopengl.com/PBR/Theory

---

## 3. Sobel Filter — Normal Map Generation

We derive the normal map from the heightmap using the Sobel operator (an image
processing technique). No additional data download needed.

- **Sobel operator — how it works:**
  A 3×3 convolution kernel that computes the gradient (rate of change) of image
  intensity in the X and Y directions. Applied to a heightmap, it tells you the
  slope at each pixel.
  https://en.wikipedia.org/wiki/Sobel_operator

- **From heightmap to normal map (algorithm):**
  1. Apply Sobel in X direction → gradient_x (how fast height changes left-right)
  2. Apply Sobel in Y direction → gradient_y (how fast height changes up-down)
  3. Construct normal vector: N = normalize(-gradient_x, -gradient_y, 1.0)
  4. Map from [-1,1] range to [0,255] range for storage as an image

- **Image convolution (prerequisite to understanding Sobel):**
  https://en.wikipedia.org/wiki/Kernel_(image_processing)

- **scipy.ndimage.sobel documentation:**
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.sobel.html

---

## 4. NASA LOLA — Lunar Elevation Data

The **Lunar Orbiter Laser Altimeter (LOLA)** flew on the Lunar Reconnaissance
Orbiter (LRO). It fires laser pulses at the Moon's surface and measures the
return time to calculate elevation. This is where our heightmap data comes from.

- **LOLA instrument overview:**
  https://lunar.gsfc.nasa.gov/lola.html

- **How laser altimetry works:**
  https://en.wikipedia.org/wiki/Lidar#Spaceborne

- **LOLA data products (LDEM = Lunar Digital Elevation Model):**
  https://pds-geosciences.wustl.edu/missions/lro/lola.htm
  - LDEM products give gridded elevation in meters, available at various
    resolutions (20m, 60m, 118m per pixel)
  - South pole specific product: LDEM_80S — covers 80°S to pole

- **USGS Astropedia lunar maps (browse LOLA products):**
  https://astrogeology.usgs.gov/search?pmi-target=moon

---

## 5. NASA LROC WAC — Lunar Surface Imagery

The **Lunar Reconnaissance Orbiter Camera (LROC)** has two components:
- **NAC (Narrow Angle Camera):** Very high resolution (0.5 m/px) but small coverage
- **WAC (Wide Angle Camera):** Lower resolution (~100 m/px) but global coverage

We use WAC global mosaics for our albedo textures because they cover the entire
Moon uniformly.

- **LROC instrument overview:**
  https://www.lroc.asu.edu/about

- **WAC global mosaic products:**
  https://wms.lroc.asu.edu/lroc/view_rdr_product/WAC_GLOBAL

- **Difference between WAC and NAC:**
  https://www.lroc.asu.edu/about/specs
  NAC is for close-up detail, WAC is for regional/global context.

- **LROC data browsing (QuickMap):**
  https://quickmap.lroc.asu.edu/
  Interactive lunar map — zoom to any Artemis candidate site and see what
  NAC/WAC data looks like.

---

## 6. GeoTIFF and Geospatial Rasters

Satellite data is stored as **GeoTIFF** files — regular images (TIFF format)
with embedded geographic metadata (coordinate system, projection, extent).

- **What is GeoTIFF:**
  https://en.wikipedia.org/wiki/GeoTIFF

- **Coordinate Reference Systems (CRS):**
  Every geospatial dataset uses a CRS to map pixel coordinates to real-world
  positions. Lunar data uses selenographic coordinates (latitude/longitude on
  the Moon) or polar stereographic projections.
  https://en.wikipedia.org/wiki/Spatial_reference_system

- **Selenographic coordinates:**
  Latitude and longitude on the Moon. Similar to Earth, but centred on the
  Moon's equator and prime meridian.
  https://en.wikipedia.org/wiki/Selenographic_coordinates

- **Rasterio (Python library for reading GeoTIFFs):**
  https://rasterio.readthedocs.io/en/stable/quickstart.html

- **GDAL (the underlying engine rasterio uses):**
  https://gdal.org/en/stable/
  Handles format conversion, reprojection, resampling of geospatial rasters.

---

## 7. Gazebo SDF Format

**SDF (Simulation Description Format)** is the XML format Gazebo uses to
describe worlds, models, physics, and sensors.

- **SDF specification:**
  http://sdformat.org/spec

- **Heightmap element in SDF:**
  http://sdformat.org/spec?ver=1.9&elem=geometry#geometry_heightmap
  This is the specific SDF element we use — it tells Gazebo to create terrain
  geometry from a PNG heightmap at runtime.

- **Model structure (model.sdf + model.config):**
  https://gazebosim.org/api/sim/8/resources.html
  Every Gazebo model needs model.sdf (the geometry/physics) and model.config
  (metadata like name, author, description). The Resource Spawner reads
  model.config to display models in the GUI.

---

## 8. Gazebo Harmonic

Gazebo Harmonic is the LTS release of the Gazebo simulator (formerly Ignition
Gazebo). It uses OGRE2 for rendering and DART for physics.

- **Gazebo Harmonic overview:**
  https://gazebosim.org/docs/harmonic/getstarted/

- **Gazebo system plugins (Physics, Sensors, SceneBroadcaster, etc.):**
  https://gazebosim.org/api/sim/8/createsystemplugins.html
  Our world file loads these plugins to enable physics simulation, rendering,
  and user interaction.

- **Resource Spawner plugin:**
  https://gazebosim.org/api/sim/8/resources.html
  Discovers models from `GZ_SIM_RESOURCE_PATH` and lets users drag-and-drop
  them into the scene. This is what powers our world-builder mode.

- **Gazebo GUI configuration (gui.config):**
  https://gazebosim.org/api/gui/8/config.html
  XML file that defines which GUI plugins to load and their layout.

---

## 9. ROS 2 Jazzy + Gazebo Integration

- **ROS 2 Jazzy overview:**
  https://docs.ros.org/en/jazzy/

- **ros_gz (ROS-Gazebo integration packages):**
  https://github.com/gazebosim/ros_gz
  Provides `ros_gz_sim` (launch utilities), `ros_gz_bridge` (topic bridging),
  and `ros_gz_image` (camera bridging).

- **ROS 2 Launch system:**
  https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-Main.html
  Python-based launch files that start nodes, set parameters, and compose
  complex launch configurations.

- **ament_cmake build system:**
  https://docs.ros.org/en/jazzy/How-To-Guides/Ament-CMake-Documentation.html
  The build system for ROS 2 C++ and mixed packages. Our package uses it to
  install resource files (models, worlds, configs, launch files).

---

## 10. Artemis Programme — Mission Context

Understanding the mission helps you understand why we chose specific sites
and terrain parameters.

- **NASA Artemis programme overview:**
  https://www.nasa.gov/artemis/

- **Artemis III candidate landing regions (13 sites near South Pole):**
  https://www.nasa.gov/press-release/nasa-identifies-candidate-regions-for-landing-next-americans-on-moon
  All sites are within ~6° of the South Pole — chosen for near-permanent
  sunlight on crater rims (power) and permanently shadowed craters nearby
  (water ice).

- **Why the South Pole?**
  https://science.nasa.gov/lunar-science/nasas-lunar-exploration/artemis-iii/
  Water ice in shadowed craters, near-continuous sunlight on peaks,
  scientifically interesting geology.

- **Artemis Science Definition Team Report (2020):**
  https://www.nasa.gov/wp-content/uploads/2020/12/artemis-iii-science-definition-report.pdf
  Detailed rationale for site selection and science objectives.

---

## 11. Docker for Robotics Simulation

- **Docker basics:**
  https://docs.docker.com/get-started/

- **Docker Compose:**
  https://docs.docker.com/compose/

- **X11 forwarding in Docker (GUI applications):**
  https://wiki.ros.org/docker/Tutorials/GUI

- **NVIDIA Container Toolkit (GPU passthrough):**
  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
  Required for hardware-accelerated rendering in Gazebo inside Docker.

---

## Suggested Reading Order

For someone new to all of this:

1. Heightmaps (§1) — the core concept everything else builds on
2. Texture mapping + Normal maps (§2)
3. Sobel filter (§3) — how we make normal maps from heightmaps
4. SDF format (§7) — how Gazebo consumes our data
5. Gazebo Harmonic (§8) — the simulation platform
6. LOLA + LROC (§4, §5) — where our data comes from
7. GeoTIFF / rasterio (§6) — how we process the data
8. Artemis programme (§10) — mission context
9. ROS 2 (§9) — the robotics framework
10. Docker (§11) — the deployment mechanism
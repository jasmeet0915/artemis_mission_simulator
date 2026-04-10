FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace

# Install Gazebo Harmonic + ROS-Gazebo integration and Python dependencies.
# Keep this list in sync with exec_depend entries in
# src/lunar_terrain_exporter/package.xml.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    python3-pip \
    gdal-bin \
    python3-gdal \
    python3-numpy \
    python3-scipy \
    python3-pyproj \
    python3-yaml \
    python3-pil \
    python3-rasterio \
    python3-requests \
    python3-tqdm \
    && rm -rf /var/lib/apt/lists/*

# Source ROS on shell entry; workspace sourced if built
RUN echo 'source /opt/ros/jazzy/setup.bash' >> /root/.bashrc && \
    echo '[ -f /workspace/install/setup.bash ] && source /workspace/install/setup.bash' >> /root/.bashrc

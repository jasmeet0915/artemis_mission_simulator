FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

# Install Gazebo Harmonic + ROS-Gazebo integration
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    python3-pip \
    python3-numpy \
    python3-scipy \
    python3-yaml \
    python3-pil \
    gdal-bin \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python deps for terrain tool
RUN pip3 install --break-system-packages \
    requests>=2.28 \
    pytest>=7.0 \
    && pip3 install --break-system-packages --no-deps rasterio>=1.3

WORKDIR /workspace

# Source ROS on shell entry; workspace sourced if built
RUN echo 'source /opt/ros/jazzy/setup.bash' >> /root/.bashrc && \
    echo '[ -f /workspace/install/setup.bash ] && source /workspace/install/setup.bash' >> /root/.bashrc

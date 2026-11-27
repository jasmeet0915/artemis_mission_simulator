FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

ENV USERNAME=commander
ENV COLCON_DEFAULTS_FILE=/home/commander/src/colcon_defaults.yaml

# Rename the existing ubuntu user inside the container to commander to match the project theme
RUN groupmod -n ${USERNAME} ubuntu && \
    usermod -l ${USERNAME} -d /home/${USERNAME} -m ubuntu && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

# Heavy layer on its own: Gazebo Harmonic + ROS<->Gazebo integration (hundreds
# of MB). Kept isolated so it stays cached across rebuilds of later layers.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    && rm -rf /var/lib/apt/lists/*

# Ament lint / build tooling.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ament-lint-auto \
    ros-jazzy-ament-lint-common \
    ros-jazzy-ament-cmake-clang-format \
    ros-jazzy-ament-cmake-pytest \
    && rm -rf /var/lib/apt/lists/*

# Python + system dependencies, including the mission stack runtime
# (tmux/libtmux for the launcher, psutil/rich for the mission-control home).
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    wget \
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
    tmux \
    python3-libtmux \
    python3-psutil \
    python3-rich \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install spiceypy for SPICE toolkit support in Python
RUN pip3 install --no-cache-dir --break-system-packages \
    spiceypy

# Bake the required NASA SPICE kernels into the image
COPY fetch_spice_kernels.sh /usr/local/bin/fetch_spice_kernels.sh
RUN chmod +x /usr/local/bin/fetch_spice_kernels.sh \
    && /usr/local/bin/fetch_spice_kernels.sh /opt/spice_kernels

# Source ROS in every interactive shell. /etc/bash.bashrc applies to any user
RUN echo 'source /opt/ros/jazzy/setup.bash' >> /etc/bash.bashrc

USER ${USERNAME}
WORKDIR /home/${USERNAME}
# Creating build directories here as the commander user to ensure correct ownsherip when
# they are mounted as named volumes
RUN mkdir build install log

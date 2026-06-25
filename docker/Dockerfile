FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

ENV USERNAME=commander
ENV COLCON_DEFAULTS_FILE=/home/commander/src/colcon_defaults.yaml

# Rename the existing ubuntu user inside the container to commander to match the project theme
RUN groupmod -n ${USERNAME} ubuntu && \
    usermod -l ${USERNAME} -d /home/${USERNAME} -m ubuntu && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

# Install Gazebo Harmonic + ROS-Gazebo integration and Python dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    ros-jazzy-ament-lint-auto \
    ros-jazzy-ament-lint-common \
    ros-jazzy-ament-cmake-clang-format \
    ros-jazzy-ament-cmake-pytest \
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
    tmux \
    python3-libtmux \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Source ROS in every interactive shell. /etc/bash.bashrc applies to any user
RUN echo 'source /opt/ros/jazzy/setup.bash' >> /etc/bash.bashrc

USER ${USERNAME}
WORKDIR /home/${USERNAME}
# Creating build directories here as the commander user to ensure correct ownsherip when
# they are mounted as named volumes
RUN mkdir build install log

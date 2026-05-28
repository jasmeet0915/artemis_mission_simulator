FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

ARG HOST_USERNAME=commander
ARG HOST_UID=1000
ARG HOST_GID=1000
ENV USERNAME=commander_${HOST_USERNAME}

# By default, the ros image already has a default non-root user named "ubuntu"
# Here, we modify that user to match the host's UID and GID to avoid permission issues when mounting volumes.
# We also change the username to something more thematic :p
RUN groupmod -n ${USERNAME} -g ${HOST_GID} ubuntu && \
    usermod -l ${USERNAME} -u ${HOST_UID} -g ${HOST_GID} -d /home/${USERNAME} -m ubuntu && \
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
    && rm -rf /var/lib/apt/lists/*

# Source ROS in every interactive shell. /etc/bash.bashrc applies to any user
RUN echo 'source /opt/ros/jazzy/setup.bash' >> /etc/bash.bashrc

USER ${USERNAME}
WORKDIR /home/${USERNAME}/artemis_workspace

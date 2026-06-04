#!/bin/bash
set -e

# Entrypoint script for remapping the commander user's UID and GID inside the container
# to match the host user's UID and GID, allowing for proper mount volume permissions
CURRENT_UID=$(id -u commander)
CURRENT_GID=$(id -g commander)
TARGET_UID="${HOST_UID:-$CURRENT_UID}"
TARGET_GID="${HOST_GID:-$CURRENT_GID}"

if [ "$TARGET_GID" != "$CURRENT_GID" ]; then
    groupmod -og "$TARGET_GID" commander
fi

if [ "$TARGET_UID" != "$CURRENT_UID" ]; then
    usermod -ou "$TARGET_UID" commander
fi

exec gosu commander "$@"

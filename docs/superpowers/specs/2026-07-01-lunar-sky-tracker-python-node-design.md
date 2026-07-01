# lunar_sky_tracker Python Node Skeleton — Design Spec

**Date:** 2026-07-01
**Status:** Approved

## Overview

Add a minimal ROS2 Python node skeleton to the existing `lunar_sky_tracker` package, which currently contains only an empty C++ cmake scaffold. No ROS2 interfaces (topics, services, actions) are defined at this stage — the goal is a buildable, runnable starting point.

## Build System

- Keep `ament_cmake` as the build type (no change to `package.xml` `<export>`)
- Add `ament_cmake_python` as a buildtool dependency to enable Python package installation via `ament_python_install_package`
- Add `rclpy` as an exec dependency

## File Layout

```
lunar_sky_tracker/
├── CMakeLists.txt          ← updated
├── package.xml             ← updated
├── lunar_sky_tracker/      ← new Python package
│   ├── __init__.py
│   └── sky_tracker_node.py
├── bin/
│   └── sky_tracker_node    ← executable entry point (no .py extension)
├── include/                ← unchanged (empty C++ stub)
└── src/                    ← unchanged (empty C++ stub)
```

## Node Skeleton (`sky_tracker_node.py`)

- Class `SkyTrackerNode(Node)` with node name `sky_tracker_node`
- Constructor declares one parameter: `timer_period` (float, default `1.0`)
- Creates a timer using `timer_period` that calls `timer_callback`
- `timer_callback` logs a DEBUG-level tick message
- `main()` function: `rclpy.init` → instantiate node → `rclpy.spin` → `rclpy.shutdown`

## Entry Point (`bin/sky_tracker_node`)

Python script with `#!/usr/bin/env python3` shebang (no `.py` extension, ROS2 convention) that imports and calls `main()` from `lunar_sky_tracker.sky_tracker_node`. Installed via `install(PROGRAMS ...)` in CMakeLists.txt.

## CMakeLists.txt Changes

1. `find_package(ament_cmake_python REQUIRED)`
2. `ament_python_install_package(${PROJECT_NAME})`
3. `install(PROGRAMS bin/sky_tracker_node DESTINATION lib/${PROJECT_NAME})`

## Out of Scope

- ROS2 publishers, subscribers, services, or actions
- Custom message types
- Launch file
- Tests

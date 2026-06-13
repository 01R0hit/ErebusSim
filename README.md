# Stonefish Swarm Simulation Workspace

This repository contains a ROS 2 workspace for simulating a small swarm of underwater AUVs ("scanners") using the [Stonefish](https://github.com/patrykcieslak/stonefish) physics-based marine robotics simulator and its ROS 2 wrapper, [`stonefish_ros2`](https://github.com/patrykcieslak/stonefish_ros2).

The `sim_swarm` package defines a Stonefish scenario containing two torpedo-shaped AUVs (`scanner_1` and `scanner_2`), each equipped with twin thrusters, a variable buoyancy system (VBS), side-scan sonars, and odometry. A keyboard teleop node is included to drive either vehicle.

---

## 1. Prerequisites

### 1.1 Stonefish (core simulator)

Before anything else, build and install the Stonefish simulation library itself. This is a standalone (non-ROS) CMake project and is installed **system-wide**, independent of any ROS workspace.

```bash
cd ~
git clone https://github.com/patrykcieslak/stonefish.git
cd stonefish
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

This requires a few system dependencies (OpenGL ≥ 4.3, GLFW, Eigen3, SDL2, etc.) — see the [Stonefish repo](https://github.com/patrykcieslak/stonefish) for the full dependency list for your distro.

Make sure Stonefish builds and installs cleanly **before moving on** — `stonefish_ros2` depends on it being available system-wide.

### 1.2 ROS 2 (Jazzy)

This workspace targets **ROS 2 Jazzy**. Make sure ROS 2 Jazzy is installed and sourced:

```bash
source /opt/ros/jazzy/setup.bash
```

---

## 2. Create the Workspace

Create the workspace directory and its `src` folder:

```bash
mkdir -p ~/stonefish_ws/src
cd ~/stonefish_ws/src
```

All packages (`stonefish_ros2` and `sim_swarm`) live inside `~/stonefish_ws/src/`.

---

## 3. Install `stonefish_ros2`

`stonefish_ros2` is the ROS 2 wrapper around the Stonefish simulator (nodes, message/service definitions, sensors, and actuators). Clone it directly into `src/`:

```bash
cd ~/stonefish_ws/src
git clone https://github.com/patrykcieslak/stonefish_ros2.git
```

It will be built together with `sim_swarm` in the build step below. Stonefish itself (step 1.1) must already be installed system-wide for `stonefish_ros2` to compile.

---

## 4. Add the `sim_swarm` Package

Clone (or copy) this `sim_swarm` package into the same `src/` directory:

```bash
cd ~/stonefish_ws/src
git clone https://github.com/01R0hit/AUV.git sim_swarm
```

After this step, `~/stonefish_ws/src/` should contain two packages side by side: `stonefish_ros2/` and `sim_swarm/`.

---

## 5. Build the Workspace

From the root of the workspace:

```bash
cd ~/stonefish_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

> `--symlink-install` is recommended for `sim_swarm` since it's a Python package — edits to `auv_teleop.py` will take effect without rebuilding.

Add the workspace overlay to your shell startup so it's sourced automatically in new terminals:

```bash
echo "source ~/stonefish_ws/install/setup.bash" >> ~/.bashrc
```

---

## 6. Running the Simulation

Launch the Stonefish simulator with the swarm scenario:

```bash
ros2 launch sim_swarm sim_swarm.launch.py
```

This starts the `stonefish_simulator` node (from `stonefish_ros2`) with:
- The scenario file `scenarios/sim_swarm.xml`
- A render window of `800x600`
- Render quality set to `low`
- A target simulation rate of `50.0` Hz

You should see a 3D window open showing a seafloor plane and two cylindrical AUVs, `scanner_1` and `scanner_2`, hovering near the origin.

### Visualizing in RViz (optional)

A pre-configured RViz layout is provided:

```bash
rviz2 -d src/sim_swarm/rviz/sim_swarm.rviz
```

---

## 7. Controlling the AUVs (Teleop)

A dedicated keyboard teleop node lets you drive either AUV using a differential-thrust scheme:

```bash
ros2 run sim_swarm auv_teleop
```

### Controls

| Key       | Action                          |
|-----------|----------------------------------|
| `W` / `S` | Move forward / backward          |
| `A` / `D` | Turn left / right                |
| `I` / `K` | Surface / dive (VBS system)      |
| `TAB`     | Switch between `scanner_1` and `scanner_2` |
| `Ctrl+C`  | Quit (publishes zero to all actuators on exit) |

The node starts with `scanner_1` as the active vehicle. Pressing `TAB` toggles control to the other AUV. On exit, all thrusters and VBS commands are zeroed out for a safe stop.

---

## 8. Workspace Structure

```
stonefish_ws/
└── src/
    ├── sim_swarm/
    │   ├── data/
    │   │   └── meshes/
    │   │       ├── dummy_prop.obj
    │   │       ├── empty.mtl
    │   │       ├── empty.obj
    │   │       ├── full.mtl
    │   │       ├── full.obj
    │   │       ├── half.mtl
    │   │       └── half.obj
    │   ├── launch/
    │   │   └── sim_swarm.launch.py
    │   ├── package.xml
    │   ├── resource/
    │   │   └── sim_swarm
    │   ├── rviz/
    │   │   └── sim_swarm.rviz
    │   ├── scenarios/
    │   │   └── sim_swarm.xml
    │   ├── setup.cfg
    │   ├── setup.py
    │   ├── sim_swarm/
    │   │   ├── auv_teleop.py
    │   │   ├── __init__.py
    │   │   └── __pycache__/
    │   │       ├── auv_teleop.cpython-312.pyc
    │   │       └── __init__.cpython-312.pyc
    │   └── test/
    │       ├── test_copyright.py
    │       ├── test_flake8.py
    │       └── test_pep257.py
    └── stonefish_ros2/   (cloned from patrykcieslak/stonefish_ros2)
```
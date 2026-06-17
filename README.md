# Swarm Simulation

This repository contains a ROS 2 workspace for simulating a small swarm of underwater AUVs ("scanners") using the [Stonefish](https://github.com/patrykcieslak/stonefish) physics-based marine robotics simulator and its ROS 2 wrapper, [`stonefish_ros2`](https://github.com/patrykcieslak/stonefish_ros2). The swarm's underwater networking and inter-vehicle communication is handled by [UnetStack](https://unetstack.net/), bridged into ROS 2 via a dedicated `unet_api` node.

The `ErebusSim` package defines a Stonefish scenario containing two torpedo-shaped AUVs (`scanner_1` and `scanner_2`), each equipped with twin thrusters, a variable buoyancy system (VBS), side-scan sonars, and odometry. A keyboard teleop node is included to drive either vehicle, and a PID controller node manages the VBS.

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

### 1.3 UnetStack (Community Edition)

This workspace uses [UnetStack](https://unetstack.net/) to run the underwater networking/agent stack alongside the simulation.

**Requirements** (per the [UnetStack downloads page](https://unetstack.net/)):
- Java 8 runtime environment
- PortAudio (on Linux/macOS)
- A modern browser (Chrome 61+ / Firefox 60+ / Safari 10.1+) for the web-based shell/console

Install the prerequisites on Ubuntu:

```bash
sudo apt update
sudo apt install -y openjdk-8-jre portaudio19-dev
```

Download the **UnetStack 3 Community edition** for Linux from the [UnetStack downloads page](https://unetstack.net/) — it will land in `~/Downloads` as something like `unet-community-3.4.4.tgz`. Extract it directly into your home directory:

```bash
cd ~/Downloads
tar -xvzf unet-community-*.tgz -C ~/
```

This produces `~/unet-3.4.4/` (the version number in the folder name will match whatever release you downloaded). Set the `UNET_HOME` environment variable to point at it and save it to your shell startup so the launch file can find it automatically:

```bash
echo 'export UNET_HOME=~/unet-3.4.4' >> ~/.bashrc
source ~/.bashrc
```

> If `UNET_HOME` is not set, `ErebusSim.launch.py` falls back to this same default path. If you extract a different version, update the `UNET_HOME` export (and the fallback in the launch file, if you want it to stay in sync) to match the new folder name.

Finally, install the `unetpy` Python package (used by the `unet_api` node to talk to UnetStack):

```bash
python3 -m pip install unetpy
```

---

## 2. Create the Workspace

Create the workspace directory and its `src` folder:

```bash
mkdir -p ~/stonefish_ws/src
cd ~/stonefish_ws/src
```

All packages (`stonefish_ros2` and `ErebusSim`) live inside `~/stonefish_ws/src/`.

---

## 3. Install `stonefish_ros2`

`stonefish_ros2` is the ROS 2 wrapper around the Stonefish simulator (nodes, message/service definitions, sensors, and actuators). Clone it directly into `src/`:

```bash
cd ~/stonefish_ws/src
git clone https://github.com/patrykcieslak/stonefish_ros2.git
```

It will be built together with `ErebusSim` in the build step below. Stonefish itself (step 1.1) must already be installed system-wide for `stonefish_ros2` to compile.

---

## 4. Add the `ErebusSim` Package

Clone (or copy) this `ErebusSim` package into the same `src/` directory:

```bash
cd ~/stonefish_ws/src
git clone https://github.com/01R0hit/AUV.git ErebusSim
```

After this step, `~/stonefish_ws/src/` should contain two packages side by side: `stonefish_ros2/` and `ErebusSim/`.

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

> `--symlink-install` is recommended for `ErebusSim` since it's a Python package — edits to `auv_teleop.py`, `unet_api.py`, etc. will take effect without rebuilding.

Add the workspace overlay to your shell startup so it's sourced automatically in new terminals:

```bash
echo "source ~/stonefish_ws/install/setup.bash" >> ~/.bashrc
```

---

## 6. Running the Simulation

The launch file starts Stonefish, RViz, the VBS PID controller, and UnetStack together, so a single terminal is enough to bring up the simulation side:

**Terminal 1 — Simulation + UnetStack**

```bash
cd ~/stonefish_ws
source install/setup.bash
ros2 launch ErebusSim ErebusSim.launch.py
```

This starts:
- The `stonefish_simulator` node (from `stonefish_ros2`) with the scenario file `scenarios/ErebusSim.xml`, a render window of `800x600`, render quality `low`, and a target simulation rate of `50.0` Hz
- `rviz2` with the bundled `rviz/ErebusSim.rviz` config
- The `vbs_pid_controller` node
- UnetStack, launched via `bin/unet` from the directory pointed to by `UNET_HOME` (see [§1.3](#13-unetstack-community-edition)), running `config/ErebusSim.groovy`

You should see a 3D window open showing a seafloor plane and two cylindrical AUVs, `scanner_1` and `scanner_2`, hovering near the origin, along with UnetStack's startup log printing the `tcp://` / `http://` addresses for each node's shell/console.

**Terminal 2 — `unet_api` node**

```bash
cd ~/stonefish_ws
source install/setup.bash
ros2 run ErebusSim unet_api
```

This node bridges ROS 2 and UnetStack using `unetpy`. Since UnetStack is now brought up by the launch file in Terminal 1, just make sure that terminal has finished starting up before launching `unet_api` here.

---

## 7. Controlling the AUVs (Teleop)

A dedicated keyboard teleop node lets you drive either AUV using a differential-thrust scheme:

```bash
ros2 run ErebusSim auv_teleop
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
    ├── ErebusSim/
    │   ├── config/
    │   │   └── ErebusSim.groovy
    │   ├── data/
    │   │   └── meshes/
    │   │       ├── dummy_prop.obj
    │   │       ├── empty.mtl
    │   │       ├── empty.obj
    │   │       ├── full.mtl
    │   │       ├── full.obj
    │   │       ├── half.mtl
    │   │       ├── half.obj
    │   │       ├── mine.mtl
    │   │       └── mine.obj
    │   ├── ErebusSim/
    │   │   ├── auv_teleop.py
    │   │   ├── __init__.py
    │   │   ├── sonar_cropper.py
    │   │   ├── unet_api.py
    │   │   └── vbs_pid_controller.py
    │   ├── launch/
    │   │   └── ErebusSim.launch.py
    │   ├── package.xml
    │   ├── README.md
    │   ├── resource/
    │   │   └── ErebusSim
    │   ├── rviz/
    │   │   └── ErebusSim.rviz
    │   ├── scenarios/
    │   │   └── ErebusSim.xml
    │   ├── setup.cfg
    │   └── setup.py
    └── stonefish_ros2/   (cloned from patrykcieslak/stonefish_ros2)
```

> Note: `__pycache__/` directories (generated `.pyc` files under `ErebusSim/ErebusSim/`) are build artifacts and are intentionally excluded from this tree. Make sure they're listed in `.gitignore` so they don't get committed.

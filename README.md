# Sensor Platform for Cornell AgRobotics Lab

Sensor platform built on NVIDIA Jetson Orin NX. Designed to be modular and work with foxglove for visualization.

### Requirements

- Flashed Jetson Nano. Developed for Jetpack 6.2.2.
- Unitree L2 Lidar
- Lidar should be configured to serial connection, not ethernet.

### Setup Instructions

1. Install ros humble
2. Follow instructions on the [realsense_ros2](https://github.com/realsenseai/realsense-ros) github to setup the realsense camera.
3. Setup permissions. On NVIDIA Jetson platforms (at least on Jetpack 6.2 on Orin NX) realsense dev is not available. Instead run

```bash
git clone <git@github.com>:realsenseai/librealsense.git
cd librealsense
./scripts/setup_udev_rules.sh
sudo udevadm control --reload-rules
sudo udevadm trigger
```

1. Clone this repository and setup dependencies.

```
git clone <https://github.com/Princeden/sensorPlatform.git>
cd sensorPlatform
rosdep install --from-paths src --ignore-src -r -y
colcon build
```

1. Launch  `ros2 launch sensor_platform sensor_platform.launch.py``

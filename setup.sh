#!/usr/bin/env bash
set -euo pipefail

echo "Setting up docker"
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker "$USER"
echo "Configuring docker to use GPU"

sudo apt install -y jq
sudo jq '. + {"default-runtime": "nvidia"}' /etc/docker/daemon.json | \
    sudo tee /etc/docker/daemon.json.tmp && \
    sudo mv /etc/docker/daemon.json.tmp /etc/docker/daemon.json
echo "Done setting up docker"

echo "Setting up isaac ros environment"
mkdir -p ~/workspaces/isaac_ros-dev/src
cd ~/workspaces/isaac_ros-dev/src

echo "cloning isaac repo"
git clone -b release-3.2 https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common.git
chmod +x isaac_ros_common/scripts/run_dev.sh

echo "export ISAAC_ROS_WS=${HOME}/workspaces/isaac_ros-dev" >> ~/.bashrc

echo "Done. Run the following to start Isaac ROS:"
echo "  cd ~/workspaces/isaac_ros-dev/src/isaac_ros_common && ./scripts/run_dev.sh"

echo "Additional packages for realsense cameras must be installed within the isaac docker image"


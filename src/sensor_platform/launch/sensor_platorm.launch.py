import os
import re
import datetime
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
    FrontendLaunchDescriptionSource,
)
import subprocess
from launch.actions import (
    ExecuteProcess,
    IncludeLaunchDescription,
)


def get_serials():
    """Serial numbers of all connected RealSense cameras."""
    try:
        out = subprocess.run(
            ["rs-enumerate-devices", "-s"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    return re.findall(r"\d{8,}", out)


def realsense_node(serial, camera_name):
    """RealSense driver for a single camera."""
    return Node(
        package="realsense2_camera",
        executable="realsense2_camera_node",
        name="camera",
        namespace=camera_name,
        parameters=[
            {
                "serial_no": serial,
                # Disabled to avoid permission errors.
                # "enable_gyro": False,
                # "enable_accel": False,
                # May need to disable on limited USB bandwidth.
                # "enable_infra1": True,
                # "enable_infra2": True,
            }
        ],
    )


RECORDED_TOPIC_SUFFIXES = (
    "camera/color/image_raw/compressed",
    "camera/depth/image_rect_raw/compressedDepth",
    "camera/color/camera_info",
    "camera/depth/camera_info",
)


def bag_recorder(camera_names):
    """Record every camera's color+depth streams; returns (bag_name, action)."""
    topics = [
        f"/{name}/{suffix}"
        for name in camera_names
        for suffix in RECORDED_TOPIC_SUFFIXES
    ]

    lidar_topics = ["/unilidar/cloud"]

    topics.extend(lidar_topics)

    bag_name = f"sensor_data_{datetime.now():%Y%m%d_%H%M%S}"

    action = ExecuteProcess(
        cmd=[
            "ros2",
            "bag",
            "record",
            "-s",
            "mcap",
            "-o",
            bag_name,
            *topics,
        ],  # mcap is better for fox glove
        output="screen",
    )
    return bag_name, action


def generate_launch_description():
    nodes = []

    serials = get_serials()
    camera_names = [f"camera_{serial}" for serial in serials]
    for serial, camera_name in zip(serials, camera_names):
        nodes.append(realsense_node(serial, camera_name))

    lidar_package_share = get_package_share_directory("unitree_lidar_ros2")
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(lidar_package_share, "launch", "launch.py")
        )
    )
    nodes.append(lidar_launch)

    foxglove_package_share = get_package_share_directory("foxglove_bridge")
    foxglove_launch = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource(
            os.path.join(foxglove_package_share, "launch", "foxglove_bridge_launch.xml")
        ),
        launch_arguments={
            "port": "8765",
            "address": "0.0.0.0",
        }.items(),
    )
    nodes.append(foxglove_launch)
    return LaunchDescription(nodes)

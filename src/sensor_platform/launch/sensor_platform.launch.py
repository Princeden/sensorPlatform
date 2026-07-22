import os
import re
from datetime import datetime
import pyzed.sl as sl
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


def get_realsense_serials():
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


def realsense_node(serial, namespace):
    """RealSense driver for a single camera."""
    return Node(
        package="realsense2_camera",
        executable="realsense2_camera_node",
        name="camera",
        namespace=namespace,
        parameters=[
            {
                "serial_no": serial,
                # Disabled to avoid permission errors.
                "enable_gyro": False,
                "enable_accel": False,
                # May need to disable on limited USB bandwidth.
                # "enable_infra1": True,
                # "enable_infra2": True,
            }
        ],
    )


def get_zed_serials():
    try:
        devices = sl.Camera.get_device_list()
        return [dev.serial_number for dev in devices]
    except Exception as e:
        print(f"Failed to detect ZED cameras: {e}")
        return []


def zed_node(serial, namespace):
    zed_launch = os.path.join(
        get_package_share_directory("zed_wrapper"),
        "launch",
        "zed_camera.launch.py",
    )

    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(zed_launch),
        launch_arguments={
            "camera_model": "zed2i",
            "serial_number": str(serial),
            "camera_name": namespace,
        }.items(),
    )


def get_camera_nodes():
    cameras = []
    realsense_serials = get_realsense_serials()
    realsense_names = [f"realsense_{serial}" for serial in realsense_serials]
    for serial, name in zip(realsense_serials, realsense_names):
        cameras.append(realsense_node(serial, name))
    zed_serials = get_zed_serials()
    zed_names = [f"zed_{serial}" for serial in zed_serials]
    for serial, name in zip(zed_serials, zed_names):
        cameras.append(zed_node(serial, name))
    camera_names = {"realsense": realsense_names, "zed": zed_names}
    return cameras, camera_names


REALSENSE_TOPIC_SUFFIXES = (
    "camera/color/image_raw/compressed",
    "camera/depth/image_rect_raw/compressedDepth",
    "camera/color/camera_info",
    "camera/depth/camera_info",
)

ZED_TOPIC_SUFFIXES = (
    "left/image_rect_color/compressed",
    "right/image_rect_color/compressed",
    "depth/depth_registered/compressedDepth",
    "left/camera_info",
    "right/camera_info",
    "depth/camera_info",
    "imu/data",
    "pose",
    "odom",
)


def bag_recorder(camera_names):
    """Record every camera's color+depth streams; returns (bag_name, action)."""
    topics = ["/unilidar/cloud", "/tf", "/tf_static"]
    realsense_names = camera_names["realsense"]
    zed_names = camera_names["zed"]

    realsense_topics = [
        f"/{name}/{suffix}"
        for name in realsense_names
        for suffix in REALSENSE_TOPIC_SUFFIXES
    ]

    zed_topics = [
        f"/{name}/{suffix}" for name in zed_names for suffix in ZED_TOPIC_SUFFIXES
    ]

    topics.extend(realsense_topics)
    topics.extend(zed_topics)
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
    camera_nodes, camera_names = get_camera_nodes()
    nodes.extend(camera_nodes)
    lidar_package_share = get_package_share_directory("unitree_lidar_ros2")

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(lidar_package_share, "launch.py"))
    )

    nodes.append(lidar_launch)

    transform_node = Node(
        package="sensor_platform",
        executable="pointcloud_transformer",
        name="pointcloud_transformer_node",
        output="screen",
    )

    nodes.append(transform_node)

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

    bag_name, recorder_action = bag_recorder(camera_names)
    nodes.append(recorder_action)

    return LaunchDescription(nodes)

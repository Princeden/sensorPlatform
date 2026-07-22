import numpy as np
import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener
from tf_transformations import quaternion_matrix


class LidarCameraFusion(Node):
    def __init__(self):
        super().__init__("lidar_camera_fusion")

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.T_lidar_to_cam = None  # cached 4x4 matrix

        # poll until the static transform is available, then stop
        self.tf_timer = self.create_timer(0.5, self._try_cache_transform)

    def _try_cache_transform(self):
        try:
            t = self.tf_buffer.lookup_transform(
                "camera_optical_frame",  # target
                "lidar_frame",  # source
                rclpy.time.Time(),  # latest available
            )
        except Exception as e:
            self.get_logger().info(f"Waiting for TF: {e}")
            return

        trans = t.transform.translation
        rot = t.transform.rotation
        M = quaternion_matrix([rot.x, rot.y, rot.z, rot.w])
        M[0:3, 3] = [trans.x, trans.y, trans.z]

        self.T_lidar_to_cam = M
        self.get_logger().info("Cached lidar->camera transform, starting subscriptions")
        self.tf_timer.cancel()
        self._start_subscriptions()
    def _start_subscriptions(self):
        from sensor_msgs.msg import PointCloud2
        self.lidar_sub = self.create_subscription(
            PointCloud2, '/lidar/points', self.lidar_callback, 10
        )

    def lidar_callback(self, msg):
        if self.T_lidar_to_cam is None:
            return  # shouldn't happen, but guard anyway

        points = self.pointcloud2_to_xyz_array(msg)  # Nx3 numpy array
        points_h = np.hstack([points, np.ones((points.shape[0], 1))])  # Nx4
        points_cam = (self.T_lidar_to_cam @ points_h.T).T[:, :3]

        # points_cam is now in the camera optical frame, ready for
        # projection, fusion, publishing, etc.
        self.process(points_cam, msg.header.sta

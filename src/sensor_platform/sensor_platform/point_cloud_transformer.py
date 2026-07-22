import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from tf2_ros import Buffer, TransformListener, TransformException
import tf2_sensor_msgs.tf2_sensor_msgs as tf2_sm


class PointCloudTransformer(Node):
    def __init__(self):
        super().__init__("pointcloud_transformer")

        self.target_frame = "camera_link"

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.sub = self.create_subscription(
            PointCloud2, "/unilidar/cloud", self.cloud_callback, 10
        )
        self.pub = self.create_publisher(PointCloud2, "/cloud_in_camera_frame", 10)

    def cloud_callback(self, msg: PointCloud2):
        try:
            # Look up the transform from the point cloud's header frame to target camera frame
            transform = self.tf_buffer.lookup_transform(
                self.target_frame,
                msg.header.frame_id,  # Source frame (e.g., 'laser_frame')
                rclpy.time.Time(),  # Latest available transform
            )

            # Perform the mathematical transformation
            transformed_cloud = tf2_sm.do_transform_cloud(msg, transform)

            # Publish transformed point cloud
            self.pub.publish(transformed_cloud)

        except TransformException as ex:
            self.get_logger().warn(f"Could not transform point cloud: {ex}")


def main():
    rclpy.init()
    node = PointCloudTransformer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

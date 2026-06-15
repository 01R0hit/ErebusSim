import rclpy
from rclpy.node import Node
# Import all required QoS policies
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class SonarCropper(Node):
    def __init__(self):
        super().__init__('sonar_cropper_node')
        self.bridge = CvBridge()
        
        # EXACT MATCH to Stonefish's QoS Demands
        custom_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        self.subscription = self.create_subscription(
            Image,
            '/scanner_1/sss_port/image',
            self.image_callback,
            custom_qos)
            
        # We can publish out to Keshav/RViz with a standard profile
        self.publisher = self.create_publisher(
            Image, 
            '/scanner_1/sss_port/intensity_only', 
            10)
            
        self.get_logger().info("Sonar Cropper Booted! Waiting for Stonefish data...")

    def image_callback(self, msg):
        try:
            self.get_logger().info("Receiving Sonar Ping! Slicing...", throttle_duration_sec=2.0)
            
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            height, width = cv_image.shape[:2]
            
            half_width = int(width / 2)
            intensity_map = cv_image[0:height, 0:half_width]
            
            clean_msg = self.bridge.cv2_to_imgmsg(intensity_map, encoding=msg.encoding)
            clean_msg.header = msg.header 
            self.publisher.publish(clean_msg)
            
        except Exception as e:
            self.get_logger().error(f"OpenCV Error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = SonarCropper()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
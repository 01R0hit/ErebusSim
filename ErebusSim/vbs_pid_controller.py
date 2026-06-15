#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry

class VBSController(Node):
    def __init__(self):
        super().__init__('vbs_pid_controller')
        
        # Added 'prev_error' to track velocity for the Derivative term
        self.auvs = {
            'scanner_1': {'target': 0.0, 'current': 0.0, 'prev_error': 0.0},
            'scanner_2': {'target': 0.0, 'current': 0.0, 'prev_error': 0.0}
        }

        # PD Control Gains
        self.Kp = 0.8  # Pushes AUV toward target
        self.Kd = 0.5  # Applies the brakes as it gets close
        self.deadband = 0.15 

        self.vbs_pubs = {
            'scanner_1': self.create_publisher(Float64, '/scanner_1/vbs_system/command', 10),
            'scanner_2': self.create_publisher(Float64, '/scanner_2/vbs_system/command', 10)
        }

        self.create_subscription(Odometry, '/scanner_1/odom', self.odom_callback_1, 10)
        self.create_subscription(Odometry, '/scanner_2/odom', self.odom_callback_2, 10)
        self.create_subscription(Float64, '/scanner_1/vbs_system/target_depth', self.target_callback_1, 10)
        self.create_subscription(Float64, '/scanner_2/vbs_system/target_depth', self.target_callback_2, 10)

        self.create_timer(0.1, self.control_loop)
        self.get_logger().info("PD VBS Controller Booted. Anti-Float Brakes engaged.")

    def odom_callback_1(self, msg): self.auvs['scanner_1']['current'] = msg.pose.pose.position.z
    def odom_callback_2(self, msg): self.auvs['scanner_2']['current'] = msg.pose.pose.position.z
    def target_callback_1(self, msg): self.auvs['scanner_1']['target'] = msg.data
    def target_callback_2(self, msg): self.auvs['scanner_2']['target'] = msg.data

    def control_loop(self):
        for auv_name, state in self.auvs.items():
            error = state['target'] - state['current']
            
            # Calculate Rate of Change (Derivative)
            derivative = (error - state['prev_error']) / 0.1
            state['prev_error'] = error
            
            msg = Float64()
            msg.data = 0.0 
            
            if abs(error) > self.deadband:
                # Proportional + Derivative Math
                raw_command = (error * self.Kp) + (derivative * self.Kd)
                msg.data = max(min(raw_command, 1.0), -1.0)
                
            self.vbs_pubs[auv_name].publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = VBSController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
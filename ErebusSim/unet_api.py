#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from unetpy import UnetSocket, DatagramReq, Protocol

class UnetApi(Node):
    def __init__(self):
        super().__init__('unet_api')
        
        self.poses = {
            'Surface_Base': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'scanner_1': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'scanner_2': {'x': 0.0, 'y': 0.0, 'z': 0.0}
        }
        
        # Connect to UnetStack Gateways
        self.get_logger().info("Connecting to UnetStack instances...")
        try:
            self.base_sock = UnetSocket('localhost', 1101)
            self.scan1_sock = UnetSocket('localhost', 1102)
            self.scan2_sock = UnetSocket('localhost', 1103)
            
            # BEST PRACTICE: Bind the base socket to Protocol.DATA (0) 
            # so it only catches incoming data datagrams, not network control noise.
            self.base_sock.bind(Protocol.DATA)
            self.get_logger().info("Connected to all UnetStack nodes successfully!")
        except Exception as e:
            self.get_logger().error(f"UnetStack connection failed: {e}")
            return

        self.get_logger().info("Caching NODE_INFO agents...")
        self.node_base = self.base_sock.agentForService('org.arl.unet.Services.NODE_INFO')
        self.node_s1 = self.scan1_sock.agentForService('org.arl.unet.Services.NODE_INFO')
        self.node_s2 = self.scan2_sock.agentForService('org.arl.unet.Services.NODE_INFO')

        # Subscriptions
        self.sub_base = self.create_subscription(Odometry, '/stonefish/surface_base/pose', self.base_cb, 10)
        self.sub_s1 = self.create_subscription(Odometry, '/scanner_1/odom', self.s1_cb, 10)
        self.sub_s2 = self.create_subscription(Odometry, '/scanner_2/odom', self.s2_cb, 10)

        self.timer = self.create_timer(1.0, self.update_unetstack)
        
        # Toggle variable to alternate between S1 and S2 transmissions
        self.active_transmitter = 1 

    def base_cb(self, msg): self.update_pose('Surface_Base', msg)
    def s1_cb(self, msg): self.update_pose('scanner_1', msg)
    def s2_cb(self, msg): self.update_pose('scanner_2', msg)

    def update_pose(self, node_id, msg):
        self.poses[node_id]['x'] = msg.pose.pose.position.x
        self.poses[node_id]['y'] = msg.pose.pose.position.y
        self.poses[node_id]['z'] = -msg.pose.pose.position.z

    def update_unetstack(self):
        # 1. Inject locations using the CACHED agents (Fast and lightweight)
        try:
            if self.node_base: self.node_base.location = [self.poses['Surface_Base']['x'], self.poses['Surface_Base']['y'], self.poses['Surface_Base']['z']]
            if self.node_s1: self.node_s1.location = [self.poses['scanner_1']['x'], self.poses['scanner_1']['y'], self.poses['scanner_1']['z']]
            if self.node_s2: self.node_s2.location = [self.poses['scanner_2']['x'], self.poses['scanner_2']['y'], self.poses['scanner_2']['z']]
        except Exception as e:
            self.get_logger().warn(f"Failed to update simulation locations: {e}")

        if self.active_transmitter == 1:
            try:
                msg_string = f"S1_POS: X={self.poses['scanner_1']['x']:.1f}, Y={self.poses['scanner_1']['y']:.1f}, Z={self.poses['scanner_1']['z']:.1f}"
                tx_packet = DatagramReq(to=1, protocol=Protocol.DATA, data=list(msg_string.encode('utf-8')))
                self.scan1_sock.send(tx_packet)
            except Exception as e:
                self.get_logger().warn(f"Transmit S1 failed: {e}")
            
            # Switch turn to Scanner 2 for the next timer tick
            self.active_transmitter = 2 

        elif self.active_transmitter == 2:
            try:
                msg_string = f"S2_POS: X={self.poses['scanner_2']['x']:.1f}, Y={self.poses['scanner_2']['y']:.1f}, Z={self.poses['scanner_2']['z']:.1f}"
                tx_packet = DatagramReq(to=1, protocol=Protocol.DATA, data=list(msg_string.encode('utf-8')))
                self.scan2_sock.send(tx_packet)
            except Exception as e:
                self.get_logger().warn(f"Transmit S2 failed: {e}")
            
            # Switch turn back to Scanner 1 for the next timer tick
            self.active_transmitter = 1

        # 4. Read the receiver buffer cleanly
        try:
            while True:
                # Use a very short timeout so ROS 2 doesn't freeze
                ntf = self.base_sock.receive(0)
                if ntf is None:
                    break 
                
                # Check if it has data and a sender ID
                if hasattr(ntf, 'data') and hasattr(ntf, 'from_'):
                    # sender_id = ntf.from_
                    decoded_msg = "".join([chr(b) for b in ntf.data])
                    self.get_logger().info(f"BASE RECEIVED: {decoded_msg}")
                    
        except Exception as e:
            self.get_logger().warn(f"Error reading packets: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = UnetApi()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean shutdown to close sockets safely
        node.base_sock.close()
        node.scan1_sock.close()
        node.scan2_sock.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
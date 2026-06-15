#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import math
from unetpy import UnetSocket, DatagramReq

class UnetApi(Node):
    def __init__(self):
        super().__init__('unet_api')
        
        # Dictionary to store coordinates
        self.poses = {
            'Surface_Base': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'scanner_1': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'scanner_2': {'x': 0.0, 'y': 0.0, 'z': 0.0}
        }
        
        # Connect to UnetStack Gateways via unetpy
        self.get_logger().info("Connecting to UnetStack instances...")
        try:
            self.base_sock = UnetSocket('localhost', 1101)
            self.scan1_sock = UnetSocket('localhost', 1102)
            self.scan2_sock = UnetSocket('localhost', 1103)
            self.get_logger().info("Connected to all UnetStack nodes successfully!")
        except Exception as e:
            self.get_logger().error(f"UnetStack connection failed. Is the Groovy script running? Error: {e}")
            return

        # Subscriptions to Stonefish Odometry
        self.sub_base = self.create_subscription(Odometry, '/stonefish/surface_base/pose', self.base_cb, 10)
        self.sub_s1 = self.create_subscription(Odometry, '/scanner_1/odom', self.s1_cb, 10)
        self.sub_s2 = self.create_subscription(Odometry, '/scanner_2/odom', self.s2_cb, 10)

        # Timer to calculate distances and update UnetStack at 2 Hz
        self.timer = self.create_timer(0.5, self.update_unetstack)

    def base_cb(self, msg): self.update_pose('Surface_Base', msg)
    def s1_cb(self, msg): self.update_pose('scanner_1', msg)
    def s2_cb(self, msg): self.update_pose('scanner_2', msg)

    def update_pose(self, node_id, msg):
        self.poses[node_id]['x'] = msg.pose.pose.position.x
        self.poses[node_id]['y'] = msg.pose.pose.position.y
        self.poses[node_id]['z'] = msg.pose.pose.position.z

    def update_unetstack(self):
        # 1. Inject Surface_Base location into UnetStack
        try:
            node_base = self.base_sock.agentForService('org.arl.unet.Services.NODE_INFO')
            node_base.location = [self.poses['Surface_Base']['x'], self.poses['Surface_Base']['y'], self.poses['Surface_Base']['z']]
        except Exception:
            pass

        # 2. Inject Scanner_1 location into UnetStack
        try:
            node_s1 = self.scan1_sock.agentForService('org.arl.unet.Services.NODE_INFO')
            node_s1.location = [self.poses['scanner_1']['x'], self.poses['scanner_1']['y'], self.poses['scanner_1']['z']]
        except Exception:
            pass

        # 3. Inject Scanner_2 location into UnetStack
        try:
            node_s2 = self.scan2_sock.agentForService('org.arl.unet.Services.NODE_INFO')
            node_s2.location = [self.poses['scanner_2']['x'], self.poses['scanner_2']['y'], self.poses['scanner_2']['z']]
        except Exception:
            pass

        # --- Transmit Acoustic Telemetry S1---
        try:
            # Send the X coordinate from Scanner 1 (Node 2) to Surface Base (Node 1)
            msg_string = f"S1_POS: X={self.poses['scanner_1']['x']:.1f}, Y={self.poses['scanner_1']['y']:.1f}, Z={self.poses['scanner_1']['z']:.1f}"
            payload = list(msg_string.encode('utf-8'))

            # Create the packet and send it
            tx_packet = DatagramReq(to=1, protocol=0, data=payload)
            self.scan1_sock.send(tx_packet)
        except Exception as e:
            self.get_logger().warn(f"Failed to transmit acoustic data scan_1: {e}")

        # --- Transmit Acoustic Telemetry S2---
        try:
            # Send the X coordinate from Scanner 2 (Node 3) to Surface Base (Node 1)
            msg_string = f"S2_POS: X={self.poses['scanner_2']['x']:.1f}, Y={self.poses['scanner_2']['y']:.1f}, Z={self.poses['scanner_2']['z']:.1f}"
            payload = list(msg_string.encode('utf-8'))

            # Create the packet and send it
            tx_packet = DatagramReq(to=1, protocol=0, data=payload)
            self.scan2_sock.send(tx_packet)
        except Exception as e:
            self.get_logger().warn(f"Failed to transmit acoustic data scan_2: {e}")

        # --- 4. CHECK FOR RECEIVED PACKETS AT SURFACE BASE ---
        try:
            while True:
                ntf = self.base_sock.receive(10)
                
                if ntf is None:
                    break 
                
                sender_id = ntf.from_
                raw_bytes = ntf.data
                decoded_msg = "".join([chr(b) for b in raw_bytes])
                
                self.get_logger().info(f"BASE RECEIVED from Node {sender_id}: {decoded_msg}")
                
        except Exception as e:
            self.get_logger().warn(f"Error reading packets: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = UnetApi()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
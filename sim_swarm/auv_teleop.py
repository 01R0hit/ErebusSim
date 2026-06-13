#!/usr/bin/env python3
"""
Keyboard teleop for AUVs in Stonefish simulation.
  W / S     : AUV_1 forward / backward
  I / K     : AUV_2 forward / backward
  SPACE     : stop all
  Q         : quit
"""
import sys, tty, termios
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

MAX_RPM = 1500.0

BINDINGS = {
    'w': ('auv1', +MAX_RPM),
    's': ('auv1', -MAX_RPM),
    'i': ('auv2', +MAX_RPM),
    'k': ('auv2', -MAX_RPM),
}

def get_key(old_settings):
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    return key

class AUVTeleop(Node):
    def __init__(self):
        super().__init__('auv_teleop')
        self.pubs = {
            'auv1': self.create_publisher(Float64, '/stonefish/auv_1/thruster_0', 10),
            'auv2': self.create_publisher(Float64, '/stonefish/auv_2/thruster_0', 10),
        }
        self.get_logger().info(
            '\n--- AUV Teleop ---\n'
            '  W/S : AUV_1 fwd/back\n'
            '  I/K : AUV_2 fwd/back\n'
            '  SPACE : stop all | Q : quit\n'
        )

    def send(self, robot, rpm):
        msg = Float64()
        msg.data = float(rpm)
        self.pubs[robot].publish(msg)
        self.get_logger().info(f'{robot}: {rpm:.0f} RPM')

    def stop_all(self):
        for robot in self.pubs:
            self.send(robot, 0.0)

def main():
    rclpy.init()
    node = AUVTeleop()
    settings = termios.tcgetattr(sys.stdin)
    try:
        while rclpy.ok():
            key = get_key(settings)
            if key in BINDINGS:
                robot, rpm = BINDINGS[key]
                node.send(robot, rpm)
            elif key == ' ':
                node.stop_all()
            elif key == 'q':
                break
    finally:
        node.stop_all()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
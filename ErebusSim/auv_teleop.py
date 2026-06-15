#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import sys
import select
import termios
import tty

# Save the terminal settings
settings = termios.tcgetattr(sys.stdin)

def get_key(timeout=0.1):
    """Reads a single keypress from the terminal without echoing."""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

class SwarmTeleop(Node):
    def __init__(self):
        super().__init__('swarm_teleop')
        
        self.active_auv = 'scanner_1'

        self.pubs = {
            'scanner_1': {
                'port': self.create_publisher(Float64, '/scanner_1/thrusters/port/command', 10),
                'stbd': self.create_publisher(Float64, '/scanner_1/thrusters/starboard/command', 10),
                'vbs': self.create_publisher(Float64, '/scanner_1/vbs_system/command', 10)
            },
            'scanner_2': {
                'port': self.create_publisher(Float64, '/scanner_2/thrusters/port/command', 10),
                'stbd': self.create_publisher(Float64, '/scanner_2/thrusters/starboard/command', 10),
                'vbs': self.create_publisher(Float64, '/scanner_2/vbs_system/command', 10)
            }
        }

        self.get_logger().info("=========================================")
        self.get_logger().info("Swarm Teleop Active! (Wayland Safe)")
        self.get_logger().info("W/S : Move Forward/Backward")
        self.get_logger().info("A/D : Turn Left/Right")
        self.get_logger().info("I/K : Surface/Dive (VBS System)")
        self.get_logger().info("TAB : Switch Submarines")
        self.get_logger().info("CTRL+C to quit")
        self.get_logger().info("=========================================")
        self.get_logger().info(f"Currently Controlling: [ {self.active_auv.upper()} ]")

    def run_teleop(self):
        surge = 0.0
        yaw = 0.0
        vbs = 0.0
        
        try:
            while rclpy.ok():
                # Read key with a 10Hz timeout
                key = get_key(timeout=0.1)
                
                # Switch AUVs
                if key == '\t': 
                    self.active_auv = 'scanner_2' if self.active_auv == 'scanner_1' else 'scanner_1'
                    print(f"\r\n>>> Switched Control To: [ {self.active_auv.upper()} ] <<<\r\n")
                    continue
                
                # Controls Mapping
                if key == 'w':
                    surge = 1.0
                elif key == 's':
                    surge = -1.0
                elif key == 'a':
                    yaw = -1.0
                elif key == 'd':
                    yaw = 1.0
                elif key == 'i':
                    vbs = -0.05
                elif key == 'k':
                    vbs = 0.05
                elif key == '\x03':  # Ctrl+C
                    break
                else:
                    # If no valid key is held down, auto-stop
                    surge = 0.0
                    yaw = 0.0
                    vbs = 0.0

                # Differential Drive Math
                thrust_port = surge + yaw
                thrust_starboard = yaw - surge

                # Clamp values to valid limits
                thrust_port = max(min(thrust_port, 1.0), -1.0)
                thrust_starboard = max(min(thrust_starboard, 1.0), -1.0)

                msg_port = Float64()
                msg_port.data = float(thrust_port)
                
                msg_stbd = Float64()
                msg_stbd.data = float(thrust_starboard)
                
                msg_vbs = Float64()
                msg_vbs.data = float(vbs)

                self.pubs[self.active_auv]['port'].publish(msg_port)
                self.pubs[self.active_auv]['stbd'].publish(msg_stbd)
                self.pubs[self.active_auv]['vbs'].publish(msg_vbs)

        except Exception as e:
            self.get_logger().error(f"Error: {e}")
            
        finally:
            # Safe shutdown: Publish zero to everything before exiting
            zero_msg = Float64()
            zero_msg.data = 0.0
            for auv in ['scanner_1', 'scanner_2']:
                for pub in ['port', 'stbd', 'vbs']:
                    self.pubs[auv][pub].publish(zero_msg)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

def main(args=None):
    rclpy.init(args=args)
    teleop_node = SwarmTeleop()
    teleop_node.run_teleop()
    teleop_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
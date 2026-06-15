#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import sys
import select
import termios
import tty

settings = termios.tcgetattr(sys.stdin)

def get_key(timeout=0.1):
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
        self.input_buffer = ""

        # INITIALIZATION FIX: Start them in formation
        self.target_depths = {
            'scanner_1': 0.0,
            'scanner_2': 10.0
        }

        self.pubs = {
            'scanner_1': {
                'port': self.create_publisher(Float64, '/scanner_1/thrusters/port/command', 10),
                'stbd': self.create_publisher(Float64, '/scanner_1/thrusters/starboard/command', 10),
                'depth': self.create_publisher(Float64, '/scanner_1/vbs_system/target_depth', 10)
            },
            'scanner_2': {
                'port': self.create_publisher(Float64, '/scanner_2/thrusters/port/command', 10),
                'stbd': self.create_publisher(Float64, '/scanner_2/thrusters/starboard/command', 10),
                'depth': self.create_publisher(Float64, '/scanner_2/vbs_system/target_depth', 10)
            }
        }

        self.get_logger().info("=========================================")
        self.get_logger().info("Swarm Teleop Active! (Leader-Follower V-Stack)")
        self.get_logger().info("W/S : Move Forward/Backward")
        self.get_logger().info("A/D : Turn Left/Right")
        self.get_logger().info("Depth Control: Type <value>i or <value>k, then press ENTER")
        self.get_logger().info("   Example: '15k' + ENTER -> Dive 15 meters")
        self.get_logger().info("TAB : Switch Submarines")
        self.get_logger().info("=========================================")

    def run_teleop(self):
        try:
            while rclpy.ok():
                key = get_key(timeout=0.1)
                surge = 0.0
                yaw = 0.0

                if key == '\t': 
                    self.active_auv = 'scanner_2' if self.active_auv == 'scanner_1' else 'scanner_1'
                    self.input_buffer = ""
                    print(f"\r\n>>> Switched Control To: [ {self.active_auv.upper()} ] <<<\r\n")
                    continue
                
                # --- BUFFERED DEPTH LOGIC ---
                if key in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'i', 'k', '.']:
                    self.input_buffer += key
                    print(f"\r[Buffer]: {self.input_buffer} (Press ENTER to execute)      ", end="", flush=True)
                
                elif key == '\x08' or key == '\x7f':  # Backspace
                    self.input_buffer = self.input_buffer[:-1]
                    print(f"\r[Buffer]: {self.input_buffer} (Press ENTER to execute)      ", end="", flush=True)
                
                elif key == '\r' or key == '\n':  # Enter Key
                    if self.input_buffer:
                        try:
                            val = float(self.input_buffer[:-1]) if len(self.input_buffer) > 1 else 1.0
                            if self.input_buffer.endswith('i'):
                                self.target_depths[self.active_auv] = max(0.0, self.target_depths[self.active_auv] - val)
                            elif self.input_buffer.endswith('k'):
                                self.target_depths[self.active_auv] += val
                            else:
                                print(f"\r\n[!] Invalid format. End with 'i' (up) or 'k' (down).\r\n")
                                self.input_buffer = ""
                                continue

                            # --- THE SWARM FORMATION MATH ---
                            if self.active_auv == 'scanner_1':
                                # Scanner 2 is dragged exactly 10m below Scanner 1
                                self.target_depths['scanner_2'] = self.target_depths['scanner_1'] + 10.0
                            else:
                                # Scanner 1 is pushed 10m above Scanner 2, but clamped at the surface (0.0)
                                self.target_depths['scanner_1'] = max(0.0, self.target_depths['scanner_2'] - 10.0)
                                # Re-sync Scanner 2 in case Scanner 1 hit the surface boundary
                                self.target_depths['scanner_2'] = self.target_depths['scanner_1'] + 10.0
                            
                            print(f"\r\n[ SWARM FORMATION ] S1 Target: {self.target_depths['scanner_1']}m | S2 Target: {self.target_depths['scanner_2']}m\r\n")

                        except ValueError:
                            print(f"\r\n[!] Error parsing depth command.\r\n")
                        
                        self.input_buffer = ""
                        print(f"\r[Buffer]:                                     ", end="\r", flush=True)

                # --- REAL-TIME WASD LOGIC ---
                elif key == 'w': surge = 1.0
                elif key == 's': surge = -1.0
                elif key == 'a': yaw = -1.0
                elif key == 'd': yaw = 1.0
                elif key == '\x03': break  # Ctrl+C

                thrust_port = max(min(surge + yaw, 1.0), -1.0)
                thrust_starboard = max(min(yaw - surge, 1.0), -1.0)

                # --- SWARM BROADCAST ---
                for auv in ['scanner_1', 'scanner_2']:
                    m_port, m_stbd, m_depth = Float64(), Float64(), Float64()
                    
                    # Both AUVs constantly receive their rigid formation targets
                    m_depth.data = float(self.target_depths[auv])
                    
                    if auv == self.active_auv:
                        m_port.data = float(thrust_port)
                        m_stbd.data = float(thrust_starboard)
                    else:
                        m_port.data = 0.0
                        m_stbd.data = 0.0

                    self.pubs[auv]['port'].publish(m_port)
                    self.pubs[auv]['stbd'].publish(m_stbd)
                    self.pubs[auv]['depth'].publish(m_depth)

        except Exception as e:
            self.get_logger().error(f"Error: {e}")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

def main(args=None):
    rclpy.init(args=args)
    teleop_node = SwarmTeleop()
    teleop_node.run_teleop()
    teleop_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
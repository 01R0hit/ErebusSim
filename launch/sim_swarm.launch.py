import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_sim_swarm = get_package_share_directory('sim_swarm')
    pkg_stonefish_ros2 = get_package_share_directory('stonefish_ros2')

    data_path = pkg_stonefish_ros2
    
    scenario_path = os.path.join(pkg_sim_swarm, 'scenarios', 'sim_swarm.xml')

    stonefish_node = Node(
        package='stonefish_ros2',
        executable='stonefish_simulator',
        name='stonefish_simulator',
        output='screen',
        arguments=[
            data_path,
            scenario_path,
            '50.0',
            '800',
            '600',
            'low'
        ]
    )

    return LaunchDescription([
        stonefish_node
    ])
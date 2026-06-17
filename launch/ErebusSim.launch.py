import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

DEFAULT_UNET_HOME = os.path.expanduser('~/unet-3.4.4')

def generate_launch_description():
    pkg_ErebusSim = get_package_share_directory('ErebusSim')
    pkg_stonefish_ros2 = get_package_share_directory('stonefish_ros2')

    data_path = pkg_stonefish_ros2
    scenario_path = os.path.join(pkg_ErebusSim, 'scenarios', 'ErebusSim.xml')
    rviz_config_path = os.path.join(pkg_ErebusSim, 'rviz', 'ErebusSim.rviz')
    groovy_script_path = os.path.join(pkg_ErebusSim, 'config', 'ErebusSim.groovy')

    unet_home = os.environ.get('UNET_HOME', DEFAULT_UNET_HOME)

    stonefish_node = Node(
        package='stonefish_ros2',
        executable='stonefish_simulator',
        name='stonefish_simulator',
        output='screen',
        arguments=[data_path, scenario_path, '50.0', '800', '600', 'low']
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen'
    )

    vbs_pid_controller_node = Node(
        package='ErebusSim',
        executable='vbs_pid_controller',
        name='vbs_pid_controller',
        output='screen'
    )

    unetstack_process = ExecuteProcess(
        cmd=[
            'bash', '-c',
            'cd "{unet_home}" && bin/unet "{groovy_script}"'.format(
                unet_home=unet_home,
                groovy_script=groovy_script_path
            )
        ],
        name='unetstack',
        output='screen'
    )

    return LaunchDescription([
        stonefish_node,
        rviz_node,
        vbs_pid_controller_node,
        unetstack_process
    ])
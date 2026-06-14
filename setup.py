import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'sim_swarm'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'scenarios'), glob('scenarios/*.xml')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'data/meshes'), glob('data/meshes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your.email@example.com',
    description='Subsea swarm simulation and routing architecture',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'auv_teleop = sim_swarm.auv_teleop:main',
            'unet_api = sim_swarm.unet_api:main'
        ],
    },
)
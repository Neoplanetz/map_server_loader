import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_dir = get_package_share_directory('map_server_loader')
    default_map_path = os.path.join(package_dir, 'maps', 'map.yaml')

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=default_map_path,
        description='Full path to the map YAML file to load.',
    )
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true.',
    )
    declare_autostart = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically transition the lifecycle node to active on startup.',
    )
    declare_log_level = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Logging level (debug, info, warn, error, fatal).',
    )

    map_yaml = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    log_level = LaunchConfiguration('log_level')

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': map_yaml,
            'use_sim_time': use_sim_time,
        }],
        arguments=['--ros-args', '--log-level', log_level],
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map_server',
        output='screen',
        parameters=[{
            'autostart': autostart,
            'node_names': ['map_server'],
            'use_sim_time': use_sim_time,
            'bond_timeout': 0.0,
        }],
        arguments=['--ros-args', '--log-level', log_level],
    )

    return LaunchDescription([
        declare_map,
        declare_use_sim_time,
        declare_autostart,
        declare_log_level,
        map_server_node,
        lifecycle_manager_node,
    ])

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='barcode_detection',
            executable='two_webcam_node',
            name='two_webcam_node',
            output='screen',
            emulate_tty=True  # supaya print ke terminal tampil rapi
        ),
        # --- NANTI TAMBAH NODE LAIN DI SINI ---
        # Node(
        #     package='barcode_detection',
        #     executable='another_node',
        #     name='another_node',
        #     output='screen'
        # ),
    ])

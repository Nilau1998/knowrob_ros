#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash
ros2 run knowrob_ros knowrob_ros_node "$@"

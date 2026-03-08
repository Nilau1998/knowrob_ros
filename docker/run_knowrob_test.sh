#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash

cd /ros2_ws

colcon test --packages-select knowrob_ros --event-handlers console_direct+
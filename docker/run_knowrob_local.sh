#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash

if [ -z "${KNOWROB_SETTINGS}" ]; then
  KNOWROB_SETTINGS=/config/knowrob_config.json
fi

if [ -d /usr/local/share/knowrob ]; then
  export KNOWROB_HOME=/usr/local/share/knowrob
  cd /usr/local/share/knowrob
fi

ros2 run knowrob_ros knowrob_ros_node "$@" --knowrob-settings "${KNOWROB_SETTINGS}"

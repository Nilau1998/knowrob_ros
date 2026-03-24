#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash

cd /ros2_ws

set +e
colcon test --packages-select knowrob_ros \
	--event-handlers console_direct+ \
	--return-code-on-test-failure \
	--ctest-args -V --output-on-failure
test_exit_code=$?
set -e

colcon test-result --verbose

exit $test_exit_code
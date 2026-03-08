#!/bin/bash
set -e

docker build -f docker/Dockerfile -t knowrob/ros2 ..

FROM ros:jazzy-ros-core-noble
LABEL maintainer="Sascha Jongebloed <jongebloed@uni-bremen.de>"

# Use bash for shell commands (to source setup.bash)
SHELL ["/bin/bash", "-lc"]

# SWI-Prolog runtime location
ENV SWI_HOME_DIR=/usr/lib/swi-prolog
ENV LD_LIBRARY_PATH=/usr/lib/swi-prolog/lib/x86_64-linux:${LD_LIBRARY_PATH}

# Install OS & ROS 2 build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl gnupg2 lsb-release git software-properties-common \
      python3-colcon-common-extensions python3-rosdep python3-vcstool \
      gdb g++ clang cmake make \
      libeigen3-dev libspdlog-dev libraptor2-dev librdf0-dev \
      libgtest-dev libboost-all-dev libboost-python-dev libboost-serialization-dev \
      libboost-program-options-dev libfmt-dev \
      libmongoc-1.0-0 libmongoc-dev \
      doxygen graphviz \
      python3 python3-dev python3-pip python3-venv python-is-python3 \
      swi-prolog* && \
    rm -rf /var/lib/apt/lists/*

# Initialize rosdep for resolving ROS 2 package dependencies
RUN rosdep init && rosdep update

# Build KnowRob as a standalone CMake project (it only provides pkg-config, not CMake config)
WORKDIR /tmp/knowrob
RUN git clone https://github.com/knowrob/knowrob.git . && \
    mkdir build && cd build && \
    cmake .. -DCATKIN=OFF -DPYTHON_MODULE_LIBDIR="dist-packages" && \
    make -j"$(nproc)" && \
    make install && \
    ldconfig && \
    rm -rf /tmp/knowrob

# Prepare the ROS 2 workspace with knowrob_ros only
WORKDIR /ros2_ws/src
ADD . /ros2_ws/src/knowrob_ros

# Build knowrob_ros with colcon (knowrob is already installed system-wide)
WORKDIR /ros2_ws
RUN source /opt/ros/jazzy/setup.bash && \
    rosdep install --from-paths src --ignore-src -r -y --skip-keys="knowrob" && \
    colcon build --symlink-install

# Copy startup scripts into the image
COPY run_knowrob.sh /ros2_ws/run_knowrob.sh
COPY run_knowrob_local.sh /ros2_ws/run_knowrob_local.sh
COPY run_knowrob_test.sh /ros2_ws/run_knowrob_test.sh

ENTRYPOINT ["./run_knowrob_local.sh"]

cmake_minimum_required(VERSION 3.5)
project(knowrob_ros VERSION 0.1.0 LANGUAGES C CXX)

# ——— C++ Standard ————————————————————
if (NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wswitch -pthread -Wno-undef")

# ——— find dependencies —————————————————
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(std_msgs REQUIRED)
find_package(action_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(spdlog REQUIRED)
find_package(PkgConfig REQUIRED)
find_package(GTest REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Development)
find_package(Boost REQUIRED COMPONENTS python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR})
# KnowRob only provides a pkg-config file (no CMake config).
# NOTE: KnowRob's .pc file omits -lknowrob from its Libs: field, so we must also locate the shared library explicitly.
pkg_check_modules(KNOWROB REQUIRED IMPORTED_TARGET knowrob)
find_library(KNOWROB_LIBRARY knowrob HINTS ${KNOWROB_LIBRARY_DIRS})
if(NOT KNOWROB_LIBRARY)
  message(FATAL_ERROR "Could not find libknowrob.so – is KnowRob installed?")
endif()

# ——— Interface definition  ———————————
# Generate messages, services, and actions
rosidl_generate_interfaces(${PROJECT_NAME}
  # messages
  "msg/KeyValuePair.msg"
  "msg/ModalFrame.msg"
  "msg/Triple.msg"
  "msg/TellMessage.msg"
  "msg/GraphQueryMessage.msg"
  "msg/GraphAnswerMessage.msg"
  # services
  "srv/AskIncrementalFinish.srv"
  "srv/ExportTriples.srv"
  # actions
  "action/AskAll.action"
  "action/AskOne.action"
  "action/AskIncremental.action"
  "action/AskIncrementalNextSolution.action"
  "action/Tell.action"
  DEPENDENCIES std_msgs action_msgs
)
ament_export_dependencies(rosidl_default_runtime)

# ——— Include directories ————————————
include_directories(
  include
  ${rclcpp_INCLUDE_DIRS}
  ${std_msgs_INCLUDE_DIRS}
  ${KNOWROB_INCLUDE_DIRS}
)
link_directories(${KNOWROB_LIBRARY_DIRS})

# ——— C++ node ——————————————————————
add_executable(knowrob_ros_node src/ROSInterface.cpp)
ament_target_dependencies(knowrob_ros_node
  rclcpp
  rclcpp_action
  std_msgs
  spdlog
)
target_include_directories(knowrob_ros_node PRIVATE
  ${Python3_INCLUDE_DIRS}
  ${Boost_INCLUDE_DIRS}
)
target_link_libraries(knowrob_ros_node
  ${KNOWROB_LIBRARY}
  PkgConfig::KNOWROB
  Boost::python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}
  Python3::Python
)
# Link generated type support into your node:
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(knowrob_ros_node "${cpp_typesupport_target}")

install(
  TARGETS knowrob_ros_node
  DESTINATION lib/${PROJECT_NAME}
)

# ——— Testing (optional) ——————————————
if (BUILD_TESTING)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)

  if(DEFINED ENV{ROS_DISTRO} AND NOT "$ENV{ROS_DISTRO}" STREQUAL "")
    set(ROS_SETUP_SCRIPT "/opt/ros/$ENV{ROS_DISTRO}/setup.bash")
  else()
    set(ROS_SETUP_SCRIPT "/opt/ros/jazzy/setup.bash")
  endif()

  add_test(
    NAME test_knowrob_ros_lib
    COMMAND /usr/bin/env bash -lc "source ${ROS_SETUP_SCRIPT} && ${Python3_EXECUTABLE} -m pytest ${CMAKE_CURRENT_SOURCE_DIR}/test/test_knowrob_ros_lib.py"
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  )
  set_tests_properties(test_knowrob_ros_lib PROPERTIES TIMEOUT 120)
endif()

# ——— ament package macro —————————————
ament_package()

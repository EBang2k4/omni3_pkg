cmake_minimum_required(VERSION 2.8.3)
project(mo_hinh_robot)
find_package(catkin REQUIRED COMPONENTS
message_generation
roscpp
rospy
std_msgs
geometry_msgs
urdf
xacro
message_generation
)
catkin_package(
CATKIN_DEPENDS
geometry_msgs
roscpp
rospy
std_msgs
)
find_package(roslaunch)
foreach(dir config launch meshes urdf)
install(DIRECTORY ${dir}/
DESTINATION
${CATKIN_PACKAGE_SHARE_DESTINATION}/${dir})
endforeach(dir)

catkin_install_python(PROGRAMS
  scripts/omni_keyboard_control.py
  scripts/wheel_encoder_reader.py
  scripts/odom_publisher.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
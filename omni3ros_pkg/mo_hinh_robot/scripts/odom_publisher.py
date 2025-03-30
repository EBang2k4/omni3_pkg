#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point, Quaternion, Twist
import sys
import tty
import termios
import math
import tf

class OmniKeyboardControl:
    def __init__(self):
        # Khởi tạo node ROS
        rospy.init_node('omni_keyboard_control', anonymous=True)

        # Publisher cho các lệnh vận tốc bánh xe
        self.pub_left = rospy.Publisher('/left_wheel_joint_velocity_controller/command', Float64, queue_size=10)
        self.pub_right = rospy.Publisher('/right_wheel_joint_velocity_controller/command', Float64, queue_size=10)
        self.pub_front = rospy.Publisher('/front_wheel_joint_velocity_controller/command', Float64, queue_size=10)

        # Publisher cho odometry
        self.odom_pub = rospy.Publisher('/odom', Odometry, queue_size=10)

        # TF broadcaster để liên kết odom với base_link
        self.odom_broadcaster = tf.TransformBroadcaster()

        # Tốc độ tối đa (radian/s)
        self.max_speed = 10.0

        # Vận tốc hiện tại của từng bánh
        self.left_speed = 0.0
        self.right_speed = 0.0
        self.front_speed = 0.0

        # Thông số robot (điều chỉnh theo thực tế)
        self.wheel_radius = 0.05  # Bán kính bánh xe (m), cần đo thực tế
        self.L = 0.128  # Khoảng cách từ tâm robot đến bánh xe (m), dựa trên URDF

        # Biến odometry
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = rospy.Time.now()

    def get_key(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

    def compute_odometry(self):
        current_time = rospy.Time.now()
        dt = (current_time - self.last_time).to_sec()

        # Tính vận tốc robot trong khung tọa độ robot
        vx = (self.left_speed * self.wheel_radius * math.cos(math.pi / 6) -
              self.right_speed * self.wheel_radius * math.cos(math.pi / 6)) / 2.0
        vy = (-self.left_speed * self.wheel_radius * math.sin(math.pi / 6) -
              self.right_speed * self.wheel_radius * math.sin(math.pi / 6) +
              self.front_speed * self.wheel_radius) / 3.0
        vtheta = (-self.left_speed * self.wheel_radius -
                  self.right_speed * self.wheel_radius -
                  self.front_speed * self.wheel_radius) / (3.0 * self.L)

        # Cập nhật vị trí và hướng
        self.x += (vx * math.cos(self.theta) - vy * math.sin(self.theta)) * dt
        self.y += (vx * math.sin(self.theta) + vy * math.cos(self.theta)) * dt
        self.theta += vtheta * dt

        # Tạo quaternion từ theta
        odom_quat = tf.transformations.quaternion_from_euler(0, 0, self.theta)

        # Xuất bản transform odom -> base_link
        self.odom_broadcaster.sendTransform(
            (self.x, self.y, 0.0),
            odom_quat,
            current_time,
            "base_link",
            "odom"
        )

        # Tạo thông điệp Odometry
        odom = Odometry()
        odom.header.stamp = current_time
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position = Point(self.x, self.y, 0.0)
        odom.pose.pose.orientation = Quaternion(*odom_quat)
        odom.twist.twist.linear.x = vx
        odom.twist.twist.linear.y = vy
        odom.twist.twist.angular.z = vtheta

        # Xuất bản odometry
        self.odom_pub.publish(odom)

        self.last_time = current_time

    def run(self):
        rospy.loginfo("Điều khiển robot omni 3 bánh bằng bàn phím:")
        rospy.loginfo("w: Tiến, s: Lùi, a: Trái, d: Phải, q: Xoay trái, e: Xoay phải")
        rospy.loginfo("x: Dừng và thoát")

        while not rospy.is_shutdown():
            key = self.get_key()

            # Đặt lại vận tốc về 0 trước khi tính toán
            self.left_speed = 0.0
            self.right_speed = 0.0
            self.front_speed = 0.0

            # Điều khiển chuyển động
            if key == 'w':  # Tiến
                self.left_speed = self.max_speed
                self.right_speed = -self.max_speed
                self.front_speed = 0.0
            elif key == 's':  # Lùi
                self.left_speed = -self.max_speed
                self.right_speed = self.max_speed
                self.front_speed = 0.0
            elif key == 'a':  # Sang trái
                self.left_speed = self.max_speed
                self.right_speed = self.max_speed
                self.front_speed = -self.max_speed
            elif key == 'd':  # Sang phải
                self.left_speed = -self.max_speed
                self.right_speed = -self.max_speed
                self.front_speed = self.max_speed
            elif key == 'q':  # Xoay trái
                self.left_speed = -self.max_speed
                self.right_speed = -self.max_speed
                self.front_speed = -self.max_speed
            elif key == 'e':  # Xoay phải
                self.left_speed = self.max_speed
                self.right_speed = self.max_speed
                self.front_speed = self.max_speed
            elif key == 'x':  # Dừng và thoát
                self.left_speed = 0.0
                self.right_speed = 0.0
                self.front_speed = 0.0
                self.pub_left.publish(self.left_speed)
                self.pub_right.publish(self.right_speed)
                self.pub_front.publish(self.front_speed)
                rospy.loginfo("Dừng robot và thoát")
                break

            # Gửi lệnh vận tốc
            self.pub_left.publish(self.left_speed)
            self.pub_right.publish(self.right_speed)
            self.pub_front.publish(self.front_speed)

            # Tính toán và xuất bản odometry
            self.compute_odometry()

            # Hiển thị trạng thái
            rospy.loginfo(f"Left: {self.left_speed:.2f}, Right: {self.right_speed:.2f}, Front: {self.front_speed:.2f}")
            rospy.loginfo(f"Pose: x={self.x:.2f}, y={self.y:.2f}, theta={self.theta:.2f}")

            rospy.sleep(0.1)

if __name__ == '__main__':
    try:
        controller = OmniKeyboardControl()
        controller.run()
    except rospy.ROSInterruptException:
        pass
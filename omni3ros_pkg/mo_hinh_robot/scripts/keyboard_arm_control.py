#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float64
from sensor_msgs.msg import JointState
import sys
import tty
import termios

class KeyboardArmControl:
    def __init__(self):
        # Khởi tạo node ROS
        rospy.init_node('keyboard_arm_control', anonymous=True)

        # Biến lưu trữ góc hiện tại của các khớp
        self.joint1_pos = 0.0  # arm1_joint
        self.joint2_pos = 0.0  # arm2_joint

        # Publisher cho lệnh điều khiển khớp
        self.pub_joint1 = rospy.Publisher('/arm_1_joint_controller/command', Float64, queue_size=10)
        self.pub_joint2 = rospy.Publisher('/arm_2_joint_controller/command', Float64, queue_size=10)

        # Subscriber để nhận trạng thái khớp
        rospy.Subscriber('/joint_states', JointState, self.joint_state_callback)

        # Tốc độ thay đổi góc (radian mỗi lần nhấn)
        self.step = 0.1

        # Giới hạn góc khớp (theo URDF của bạn: -1.57 đến 1.57 rad)
        self.min_angle = -1.57
        self.max_angle = 1.57

    def joint_state_callback(self, msg):
        # Cập nhật trạng thái hiện tại của các khớp từ /joint_states
        try:
            idx1 = msg.name.index('arm1_joint')
            idx2 = msg.name.index('arm2_joint')
            self.joint1_pos = msg.position[idx1]
            self.joint2_pos = msg.position[idx2]
        except ValueError:
            pass

    def get_key(self):
        # Đọc phím từ bàn phím mà không cần nhấn Enter
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

    def run(self):
        rospy.loginfo("Điều khiển tay máy bằng bàn phím:")
        rospy.loginfo("q/a: Tăng/Giảm arm1_joint")
        rospy.loginfo("w/s: Tăng/Giảm arm2_joint")
        rospy.loginfo("x: Thoát")

        while not rospy.is_shutdown():
            key = self.get_key()

            # Điều khiển arm1_joint
            if key == 'q':
                self.joint1_pos = min(self.joint1_pos + self.step, self.max_angle)
            elif key == 'a':
                self.joint1_pos = max(self.joint1_pos - self.step, self.min_angle)

            # Điều khiển arm2_joint
            elif key == 'w':
                self.joint2_pos = min(self.joint2_pos + self.step, self.max_angle)
            elif key == 's':
                self.joint2_pos = max(self.joint2_pos - self.step, self.min_angle)

            # Thoát
            elif key == 'x':
                rospy.loginfo("Thoát chương trình")
                break

            # Gửi lệnh đến các khớp
            self.pub_joint1.publish(self.joint1_pos)
            self.pub_joint2.publish(self.joint2_pos)

            # Hiển thị trạng thái hiện tại
            rospy.loginfo(f"arm1_joint: {self.joint1_pos:.2f}, arm2_joint: {self.joint2_pos:.2f}")

            rospy.sleep(0.1)  # Tránh đọc phím quá nhanh

if __name__ == '__main__':
    try:
        controller = KeyboardArmControl()
        controller.run()
    except rospy.ROSInterruptException:
        pass
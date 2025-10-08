import rclpy
from rclpy.node import Node

from std_msgs.msg import String

class TalkerNode(Node):
    def __init__(self):
        super().__init__('talker_node')
        self.publisher = self.create_publisher(String, 'talker', 10)
        timer_period = 0.5 # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.count = 0

    def timer_callback(self):

        msg = String()
        msg.data = f'Hello everyone {self.count}'
        self.publisher.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.count += 1

    def main(args=None):
        rclpy.init(args=args)

        # Create the node
        talker_node = TalkerNode()

        # Spin the node so the callback function is called.
        rclpy.spin(talker_node)
        talkerNode.destroy_node()

        rclpy.shutdown()

    if __name__ == '__main__':
        main()
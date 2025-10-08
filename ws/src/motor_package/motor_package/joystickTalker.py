import pygame
import socket
import pickle
import numpy as np
import time
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy
from std_msgs.msg import String



class TalkerNode(Node):
    def __init__(self):
        super().__init__("joystick_node")
        qos_profile = QoSProfile(depth=10)
        qos_profile.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        self.publisher_ = self.create_publisher(String, 'manual_controller_input', qos_profile)
        timer_period = 0.1
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.count = 0
        
        # dutyCycleLeft, dutyCycleRight, triggerMult, b_x1, b_circle1, b_square1, b_triangle1, b_lbumper1, b_rbumper1, b_padUp1, b_padDown1, b_padLeft1

        self.joy_x = 0
        self.joy_y = 0
        
        self.triggerMult = 0

        self.b_x = 0
        self.b_circle = 0
        self.b_triangle = 0
        self.b_square = 0
        

    def timer_callback(self):
        msg = String()
        msg.data = f"{self.joy_x} {self.joy_y} {self.triggerMult} {self.b_x} {self.b_circle} {self.b_triangle} {self.b_square}\n"

        self.publisher_.publish(msg)
        self.count += 1
        self.get_logger().info(f"Publishing {msg.data}")
        
    def update_joystick_values(self, joy_x, joy_y, triggerMult, b_x, b_circle, b_triangle, b_square):
        self.joy_x = joy_x
        self.joy_y = joy_y
        self.triggerMult = triggerMult
        self.b_x = b_x
        self.b_circle = b_circle
        self.b_triangle = b_triangle
        self.b_square = b_square

def deadzone(button):
    c_deadzone = 0.05
    c_roundAxis = 4
    # applies deadzone and shortens to c_roundAxis number of decimal places

    if abs(button) < c_deadzone:
        return 0
    else:
        return round(button, c_roundAxis)

def valueMap(val):
    return int(val * 255)

def cart2pol(x, y):
    radius = min(math.sqrt(x**2 + y**2), 1)  # Normalize and ceiling to 1
    angle = math.atan2(y, x) * (180 / math.pi)  # Convert angle to degrees
    return (int(255 * radius), int((angle + 360) % 360))

def calcWheelSpeeds(magnitude, angle):
    magnitude = magnitude / 255

    # Normalize angle to range [0, 360)
    angle = angle % 360

    # Calculate left and right speeds based on angle and magnitude
    if 0 <= angle <= 90:  # Moving forward with right turn
        left_speed = magnitude
        right_speed = magnitude * (angle / 90)
    elif 90 < angle <= 180:  # Moving forward with left turn
        left_speed = magnitude * (1 - (angle - 90) / 90)
        right_speed = magnitude
    elif 180 < angle <= 270:  # Moving backward with left turn
        left_speed = -magnitude * ((angle - 180) / 90)
        right_speed = -magnitude
    else:  # 270 < angle < 360, Moving backward with right turn
        left_speed = -magnitude
        right_speed = -magnitude * (1 - (angle - 270) / 90)
        
    if 150 < angle < 210:			# slowdown conditions on left / right turns - swapping directions could be tough on motors
        right_speed = right_speed * max(0.3, abs(angle-180)/30)
    if angle > 330:
        left_speed = left_speed * max(0.3, abs(angle-360)/30)
    if angle < 30:
        left_speed = left_speed * max(0.3, angle/30)

    return valueMap(left_speed), valueMap(right_speed)


def run(joysticks, publisher, triggerMult, stopFlag):
    
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                joysticks[joy.get_instance_id()] = joy
                print(f"Joystick {joy.get_instance_id()} connencted")

            if event.type == pygame.JOYDEVICEREMOVED:
                del joysticks[event.instance_id]
                print(f"Joystick {event.instance_id} disconnected")

        # screen.fill((255, 255, 255))
        # text_print.reset()
        if not joysticks:
            print("No joystick connected. Waiting...")
            time.sleep(3)
            continue
        # joystick 1 sets joystick buttons / axis to values

        if 0 in joysticks:
            guid = joysticks[0].get_guid()

        a_lt1 = deadzone(joysticks[0].get_axis(5) + 1)
        a_rt1 = deadzone(joysticks[0].get_axis(4) + 1)
        
        b_lbumper1 = joysticks[0].get_button(9)
        b_rbumper1 = joysticks[0].get_button(10)

        a_leftx1 = deadzone(joysticks[0].get_axis(0))
        a_lefty1 =  deadzone(joysticks[0].get_axis(1) * -1)

        a_rightx1 = deadzone(joysticks[0].get_axis(2))
        a_righty1 =  deadzone(joysticks[0].get_axis(3) * -1)

        b_leftIn1 = joysticks[0].get_button(7)
        b_rightIn1 = joysticks[0].get_button(8)

        b_x1 = joysticks[0].get_button(0)
        b_circle1 = joysticks[0].get_button(1)
        b_square1 = joysticks[0].get_button(3)
        b_triangle1 = joysticks[0].get_button(2)

        b_padUp1 = joysticks[0].get_button(11)
        b_padDown1= joysticks[0].get_button(12)
        #b_padLeft1 = joysticks[0].get_button(13)
        # b_padRight1 = joysticks[0].get_button(14)
        # b_touchpad1 = joysticks[0].get_button(15)

        #joystick_data = [a_lt1, a_rt1, b_lbumper1, b_rbumper1, a_leftx1, a_lefty1, a_rightx1, a_righty1, b_leftIn1, b_rightIn1, b_x1, b_circle1, b_square1, b_triangle1, b_padUp1, b_padDown1, b_padLeft1, b_padRight1]
        mag, angle = cart2pol(a_leftx1, a_lefty1)
        dutyCycleLeft, dutyCycleRight = calcWheelSpeeds(mag, angle) # converts magnitude/angle into left and right speeds
        # if needed - new function for individual wheel control

        if a_rt1 > 0.1:
            triggerMult = round(triggerMult - 0.01, 5)	#adjust magnitude scalar with triggers (0-2), left decrease, right increase, cancel each other out
        triggerMult = max(0.1, min(triggerMult, 2))	#limit to 0.1x to 2x
        

        if b_padUp1 == 1:		# presets - will need sleep() after sending signals w/ time hyperparameter (5secs?)
            pass
        if b_padDown1 == 1:
            pass
        #if b_padLeft1 == 1:
        #    pass
        # if b_padRight1 == 1:
        #     pass
        
        
        if b_leftIn1 == 1 and stopFlag == False:
            stopFlag = True
            
        if stopFlag == True:
            # dutyCycleLeft, dutyCycleRight = 0, 0
            pass
            
        # ORDER OF SENDING DATA OVER SERIAL
        # dutyCycleLeft, dutyCycleRight, triggerMult, b_x1, b_circle1, b_square1, b_triangle1, b_lbumper1, b_rbumper1, b_padUp1, b_padDown1, b_padLeft1
        #
        #
        #
        publisher.update_joystick_values(int(dutyCycleLeft * 0.15), 
                                         int(dutyCycleRight * 0.15), 
                                         float(triggerMult), 
                                         int(b_x1), 
                                         int(b_circle1), 
                                         int(b_triangle1), 
                                         int(b_square1))
        # publisher.joy_x = int(dutyCycleLeft * 0.15)  
        # publisher.joy_y = int(dutyCycleRight * 0.15)
        # publisher.triggerMult = float(triggerMult)
        # publisher.b_x = int(b_x1)
        # publisher.b_circle = int(b_circle1)
        # publisher.b_triangle = int(b_triangle1)
        # publisher.b_square = int(b_square1)
        rclpy.spin_once(publisher)
        
        

def main():


    rclpy.init()
    #create nodes
    joystickNode = TalkerNode()

    pygame.init()
    pygame.joystick.init()

    joysticks = {}
    run(joysticks, joystickNode, 1, stopFlag=False)
    pygame.quit()

    joystickNode.destroy_node()
    #subscriberNode.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()

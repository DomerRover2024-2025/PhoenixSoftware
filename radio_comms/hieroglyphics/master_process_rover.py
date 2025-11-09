# This is the server side of a client-server model.
# This will be receiving requests from the base station.

###################
##### IMPORTS #####
###################

from serial import Serial
import cv2
import os
import struct
import numpy as np
import concurrent.futures
import atexit
import time
import traceback

from message import Message
from scheduler import Scheduler
from messageQueue import MessageQueue
from roverMessageProcessor import RoverMessageProcessor
from socketReaderWriter import SocketReaderWriter
from serialReaderWriter import SerialReaderWriter
from readerWriter import ReaderWriter

def main():
    port = "/dev/cu.usbserial-BG00HO5R"
    #port = "/dev/tty.usbserial-B001VC58"
    #port = "COM4"
    #port = "/dev/ttyTHS1"
    baud = 57600
    timeout = 0.1

    # respective 'int' identifiers for each topic
    topics = {
        "status": 3,
        "vid_feed": 10,
        "position": 1,
        "hdp": 1,
        "ldp": 1,
        "file": 1
    }

    messageQueue : MessageQueue = MessageQueue()
    # readerWriter : ReaderWriter = SerialReaderWriter(port, baud, timeout, messageQueue)
    readerWriter : ReaderWriter = SocketReaderWriter('localhost', 9999, messageQueue, rover=True)
    scheduler = Scheduler(readerWriter=readerWriter, topics=topics)

    executor = concurrent.futures.ThreadPoolExecutor(4)
    future_scheduler = executor.submit(scheduler.send_messages_via_scheduler, messageQueue)
    future_msg_process = executor.submit(process_messages, messageQueue, scheduler)
    # future_video = executor.submit(capture_video)

    atexit.register(exit_handler, executor, messageQueue)
    print("entering read loop")

    received_info_from_gnss_eh = False
    
    try:
        while True:
            message = readerWriter.readMessage()
            if message:
                messageQueue.append(message)

    except KeyboardInterrupt or Exception:
        exit(0)

# capture_video_eh = False

def process_messages(messageQueue : MessageQueue, scheduler : Scheduler) -> None:
 try:

    print("thread activated :)")

    # rclpy.init(args=None)
    # #create node
    # talkerNode = TalkerNode()

    # TODO: TODO TODO FIX THIS when connected to the jetson
    #arduino = serial.Serial('/dev/ttyACM0')

    MSG_LOG = "messages_rover.log"

    VID_WIDTH = 200
    CAM_PATHS = [
        "/dev/v4l/by-id/usb-046d_081b_32750F50-video-index0",
        "/dev/v4l/by-id/usb-Technologies__Inc._ZED_2i_OV0001-video-index0"
    ]
    CAM_PATH = CAM_PATHS[1]

    # messageProcessor = RoverMessageProcessor(MSG_LOG, scheduler, '/dev/ttyACM0')
    messageProcessor = RoverMessageProcessor(MSG_LOG, scheduler, None)

    while messageQueue.isRunning():
        if len(messageQueue) == 0:
            continue

        currentMessage = messageQueue.pop()
        Message.log_message(currentMessage, MSG_LOG)

        if currentMessage.purpose == Message.Purpose.ERROR:
            messageProcessor.handleDebugMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.MOVEMENT:
            messageProcessor.handleDrivingMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.VIDEO:
            messageProcessor.handleVideoToggleMessage(currentMessage) 
        
        elif currentMessage.purpose == Message.Purpose.HIGH_DEFINITION_PHOTO: 
            messageProcessor.handleHighDefPhotoRequestMessage(currentMessage)
        
        elif currentMessage.purpose == Message.Purpose.LOW_DEFINITION_PHOTO:
            messageProcessor.handleLowDefPhotoRequestMessage(currentMessage)
        
        elif currentMessage.purpose == Message.Purpose.FILE_CONTENTS:
            messageProcessor.handleFileContentsRequestMessage(currentMessage)
        
        else:
            print("--Error: message matched no known purposes.")
    messageProcessor.imageCapturer.stopTakingVideo()
 except Exception:
    print('--error(process messages): ', traceback.format_exc())

# import rclpy
# from rclpy.node import Node
# from std_msgs.msg import String
# #be able to write to the arduino serial port
# #create an instance of the serial, open up a serial.write, and then write whatever the message being published is
# class TalkerNode(Node):
#     def __init__(self):
#         super().__init__("talker_node")
#         # TODO change the topic here from 'motor_state'
#         self.publisher_ = self.create_publisher(String, 'motor_state', 10)
#         timer_period = 0.1
#         #self.timer = self.create_timer(timer_period, self.timer_callback)
#         self.count = 0
#         self.serialPort = serial.Serial('/dev/ttyACM0')
#     def listener_callback(self, msg):
#         #msg = String()
#         #msg.data = f"Hello everyone {self.count}"
#         # self.publisher_.publish(msg.data)
#         self.count += 1
#         self.get_logger().info(f"Recieving {msg.data}")
#         # self.write(msg.data)
#      #def write(x):
#         self.serialPort.write(msg.data.encode())

def exit_handler(executor : concurrent.futures.ThreadPoolExecutor, messageQueue):
    messageQueue.shutdown()
    executor.shutdown()

if __name__ == "__main__":
    main()

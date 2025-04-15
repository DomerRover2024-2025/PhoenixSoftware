# This is the server side of a client-server model.
# This will be receiving requests from the base station.

###################
##### IMPORTS #####
###################

import serial
import cv2
import sys
import struct
import numpy as np
import concurrent.futures
from message import Message
from scheduler import Scheduler
from collections import deque
from datetime import datetime
import atexit
import time
#np.set_printoptions(threshold=sys.maxsize)

MSG_LOG = "messages_rover.log"
VID_WIDTH = 200
CAM_PATHS = [
    "/dev/v4l/by-id/usb-046d_081b_32750F50-video-index0",
    "/dev/v4l/by-id/usb-Technologies__Inc._ZED_2i_OV0001-video-index0"
]
CAM_PATH = CAM_PATHS[1]
kill_threads = False
# !TODO to be replaced by a message manager
messages_to_process = deque()
scheduler = Scheduler(ser=None, topics=None)
cap = cv2.VideoCapture(0)
capture_video_eh = False

def main():
    port = "/dev/cu.usbserial-BG00HO5R"
    #port = "/dev/tty.usbserial-B001VC58"
    #port = "COM4"
    #port = "/dev/ttyTHS1"
    baud = 57600
    timeout = 0.1
    ser = serial.Serial(port=port, baudrate=baud, timeout=timeout)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # respective 'int' identifiers for each topic
    topics = {
        "status": 3,
        "vid_feed": 10,
        "position": 1,
        "hdp": 1,
        "ldp": 1
    }

    scheduler.ser = ser
    scheduler.set_topics(topics=topics)

    executor = concurrent.futures.ThreadPoolExecutor(4)
    future_scheduler = executor.submit(send_messages_via_scheduler)
    future_msg_process = executor.submit(process_messages)
    future_video = executor.submit(capture_video)

    atexit.register(exit_handler, executor)
    print("entering read loop")

    received_info_from_gnss_eh = False
    
    try:
        while True:

            ##### READ: SERIAL PORT #####
            b_input = ser.read(1)
            if len(b_input) != 0:
                pot_msg = Message(new=False)
                b_input += ser.read(1)
                pot_msg.set_msg_id(struct.unpack(">H", b_input)[0])
                b_input = ser.read(1)
                pot_msg.set_purpose(b_input)
                b_input = ser.read(1)
                pot_msg.number = struct.unpack(">B", b_input)[0]
                b_input = ser.read(struct.calcsize(">L"))
                pot_msg.set_size(b_input)
                payload = b''

                while len(payload) < pot_msg.size_of_payload:
                    payload += ser.read(pot_msg.size_of_payload - len(payload))
                    if kill_threads:
                        return

                pot_msg.set_payload(payload)
                checksum = ser.read(1)
                if not Message.test_checksum(bytestring=pot_msg.get_as_bytes()[:-1], checksum=checksum):
                    print("Checksum error")
                    continue

                # TODO replace with a message manager
                messages_to_process.append(pot_msg)
                print(f"Message added")

            if received_info_from_gnss_eh:
                coord_x = 1.2345
                coord_y = 9534.1234
                b_coord_x = struct.pack(">f", coord_x)
                b_coord_x = struct.pack(">f", coord_y)

            # ##### READ: CAMERA #####
            # should_capture_image = False
            # # If true, capture image, split it into smaller messages (if needed), and send it.
            # if should_capture_image:
            #     _, buffer = capture_image(90, resize_width=VID_WIDTH)
            #     if buffer == None:
            #         continue
            #     scheduler.add_list_of_messages("vid_feed", Message.message_split(big_payload=buffer, purpose_for_all=2))
    
    except KeyboardInterrupt or Exception:
        exit(0)

def capture_image(quality : int, resize_width : int=None) -> tuple[int, bytearray]:
    #cap = cv2.VideoCapture(0)
    ret, frame = cap.read() # ret is a boolean indicating if the frame was captured correctly

    if not ret:
        #print("Failed to capture image.")
        return 0, None

    # with open("temp2.txt", 'bw') as f:
    #     f.write(frame)

    if resize_width:
        resize_factor = resize_width / frame.shape[1]
        frame = cv2.resize(frame, (resize_width, int(resize_factor * frame.shape[0])))

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    # encoded: boolean indicating whether the image capture was successful, 
    # buffer contains compressed image data
    encoded, buffer = cv2.imencode('.jpg', frame, encode_param) 
    size_of_data = len(buffer)
    #size_packed = struct.pack(">L", size_of_data)
    return size_of_data, buffer

# capture_video_eh = False
def capture_video() -> None:
    while not kill_threads:
        try:
            if not capture_video_eh:
                continue
            _, frame = capture_image(30, resize_width=250)
            if frame is None:
                continue
            scheduler.add_list_of_messages("vid_feed", Message.message_split(big_payload=frame.tobytes(), purpose_for_all=3))
        except Exception as e:
            print(e)
        time.sleep(1)

def process_messages() -> None:

    print("thread activated :)")

    # rclpy.init(args=None)
    # #create node
    # talkerNode = TalkerNode()

    # TODO: TODO TODO FIX THIS when connected to the jetson
    #arduino = serial.Serial('/dev/ttyACM0')

    current_file = ''

    while not kill_threads:
        if len(messages_to_process) == 0:
            continue
        print("Processing message", len(messages_to_process))
        curr_msg : Message = messages_to_process.popleft()
        Message.log_message(curr_msg, MSG_LOG)

        if curr_msg.purpose == 1: # indicates DRIVING
            #print("driving message")
            payload = curr_msg.get_payload()
            print(len(payload))
            lspeed = struct.unpack(">h", payload[0:2])[0]
            rspeed = struct.unpack(">h", payload[2:4])[0]
            speed_scalar = struct.unpack(">f", payload[4:8])[0]
            cam_left = struct.unpack(">B", payload[8:9])[0]
            cam_right = struct.unpack(">B", payload[9:10])[0]
            button_x = struct.unpack(">B", payload[10:11])[0]
            button_y = struct.unpack(">B", payload[11:12])[0]
            # TODO TODO TODO TODO FIX THIS WHEN CONNECTED TO THE JETSON
            #arduino.write(f"{lspeed} {rspeed}\n".encode())

        #!TODO ACTUALLY PICK CAMERA TO SEE
        elif curr_msg.purpose == 3: # indicates video
            global capture_video_eh
            global cap
            cam_num = struct.unpack(">b", curr_msg.payload)[0]
            if cam_num == -1:    # indicates STOP VIDEO FEED, returns camera feed to the photo camera
                capture_video_eh = False
                continue
            capture_video_eh = True
            if cam_num <= len(CAM_PATHS):
                cap = cv2.VideoCapture(CAM_PATH[cam_num])
            else:
                print(f"Only {len(CAM_PATHS)} camera(s). camera {cam_num} DNE")
                
        # elif curr_msg.purpose == 3: # indicates START/STOP VIDEO FEED
        #     global capture_video_eh
        #     capture_video_eh = not capture_video_eh
        
        elif curr_msg.purpose == 4: # indicates TAKE ME A GOOD PHOTO
            length, buffer = capture_image(90)
            print("Image captured")
            if buffer is None:
                print("error no image could be grabbed")
                error_str = "Error: could not capture a high definition photo."
                scheduler.add_single_message("status", Message(purpose=0, payload=error_str.encode()))
            else:
                print("splitting messages")
                msgs =  Message.message_split(big_payload=buffer.tobytes(), purpose_for_all=4)
                print("messages split")
                scheduler.add_list_of_messages("hdp", msgs)
                print("Message added of length ", len(buffer.tobytes()))
        
        elif curr_msg.purpose == 6: # indicates TAKE ME A BAD PHOTO
            print("getting an ldp photo")
            try:
                length, buffer = capture_image(90, resize_width=VID_WIDTH)
            except Exception as e:
                print(e)
            if buffer is None:
                error_str = "Error: could not capture a high definition photo."
                print(error_str)
                scheduler.add_single_message("status", Message(purpose=0, payload=error_str.encode()))
            else:
                try:
                    msgs = Message.message_split(big_payload=buffer.tobytes(), purpose_for_all=6)
                    scheduler.add_list_of_messages("ldp", msgs)
                    print("Message added of length ", len(buffer.tobytes()))
                except Exception as e:
                    print(e)

        elif curr_msg.purpose == 10: # indicates FILE NAME
            if curr_msg.number == 1:
                current_file = curr_msg.get_payload().decode()
            elif curr_msg.number == 0:
                current_file = ''
            elif not current_file:
                error_str = "Error: file contents received, but no file name for said contents."
                print(error_str)
                scheduler.add_single_message("status", Message(purpose=0, payload=error_str.encode()))
            else:
                with open(current_file, 'ab') as f:
                    f.write(curr_msg.get_payload())

            #arduino_ser.write(msg.encode())
        elif curr_msg.purpose == 0: # indicates DEBUGGING to the rover
            print("debugging message")
            payload = curr_msg.get_payload()
            print(payload.decode())
            return_str = f"string {payload.decode()} received."
            scheduler.add_single_message("status", Message(purpose=0, payload=return_str.encode()))
        
        else:
            print("didn't match to anything")

# weighted round robin algorithm?
# implement with a thread, I think
def send_messages_via_scheduler():
    print("started up the wrr")
    while not kill_threads:
        for topic in scheduler.topics: # all the topic names
            c = 0 # packet counter
            if topic == 'vid_feed' and not capture_video_eh:
                scheduler.messages[topic].clear()
            while scheduler.messages[topic] and c < scheduler.topics[topic]:
                try:
                    curr_msg = scheduler.messages[topic].popleft()
                    scheduler.ser.write(curr_msg.get_as_bytes())
                    c += 1
                    #print(f"{curr_msg.get_as_bytes()[4:8]}")
                    #print(f"Message sent: {curr_msg} of length {curr_msg.size_of_payload}")
                except Exception as e:
                    print(e)
    # talkerNode.destroy_node()
    # rclpy.shutdown()
    # arduino.close()

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

def exit_handler(executor : concurrent.futures.ThreadPoolExecutor):
    global kill_threads
    kill_threads = True
    executor.shutdown()


if __name__ == "__main__":
    main()

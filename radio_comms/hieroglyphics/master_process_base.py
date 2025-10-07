#### This is going to be more of a user-interface
#### based program than the rover version, which
#### doesn't *have* a UI, so it will be completely covered
#### by the scheduler and message manager.

# This is the client side of a client-server model.
# This will be sending requests to the rover.

###################
##### IMPORTS #####
###################

import serial
import sys
import numpy as np
import cv2
import time
import os
import struct
import subprocess
from collections import deque
import concurrent.futures
from datetime import datetime
import atexit

import config
from message import Message
import capture_controls
from messagePurpose import Purpose
from readPort import Reader

#######################
##### GLOBAL VARS #####
#######################

################
##### MAIN #####
################

def main():
    port = "/dev/cu.usbserial-BG00HO5R"
    #port = "/dev/cu.usbserial-B001VC58"
    # port = "COM4"
    #port = "/dev/ttyUSB0"
    baud = 57600
    timeout = 0.1
    ser = serial.Serial(port=port, baudrate=baud, timeout=timeout)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # make sure the log file is empty
    open(MSG_LOG, 'w').close()

    reader = Reader()

    # 3 concurrent threads: one read from serial port, 
    # one for processing messages, one for writing messages
    executor = concurrent.futures.ThreadPoolExecutor(3)
    future = executor.submit(process_messages)
    future = executor.submit(reader.read_from_port, ser)
    atexit.register(exit_main, executor)

    try:
            
        # the main control
        while True:
            # Continuously display options and ask for user input
            print_options()
            request = input(">> ")
            
            if request == 'quit':
                return 0

            # this request is for debugging, and prints the remaining contents
            # of the buffer into a file
            if request == 'log':
                tail_output = subprocess.run(["tail", '-n', 10, MSG_LOG], capture_output=True, text=True)
                print(tail_output.stdout)

            elif request == "dr":
                    # connec to controller?
                capture_controls.pygame.init()
                capture_controls.pygame.joystick.init()
                # get joystick
                try: 
                    gen = capture_controls.run({}, 1, False)
                except:
                    print("No joystick found")
                    continue

                # get joystick values
                while True:
                    lspeed, rspeed, scalar, camleft, camright, button_x, button_y = next(gen) # get joystick values
                    b_lspeed = struct.pack(">h", int(lspeed))
                    b_rspeed = struct.pack(">h", int(rspeed))
                    b_scalar = struct.pack(">f", scalar)
                    b_camleft = struct.pack(">B", camleft)
                    b_camright = struct.pack(">B", camright)
                    b_button_x = struct.pack(">B", camright)
                    b_button_y = struct.pack(">B", camright)
                    payload = b_lspeed + b_rspeed + b_scalar + b_camleft + b_camright + b_button_x + b_button_y

                    # pack up the message
                    ctrls_msg = Message(new=True, purpose=1, payload=payload)
                    print(ctrls_msg.get_as_bytes())

                    ser.write(ctrls_msg.get_as_bytes())

            # Send test messages
            elif request == "test":
                while True:
                    hello = input("enter tester phrase, exit to exit >> ")
                    if hello == "exit":
                        break
                    msg = Message(purpose=0, payload=hello.encode())
                    ser.write(msg.get_as_bytes())

            elif request == "vid":
                try: 
                    stop_video_request = input("n to stop feed, else start feed? >> ")
                    if stop_video_request == 'n':
                        cam_num = request_camera()
                        if cam_num == -1:
                            print("returning to menu")
                            continue
                    else:
                        cam_num = -1
                    b_cam = struct.pack(">b", cam_num)
                    msg = Message(new=True, purpose=3, payload=b_cam)
                    ser.write(msg.get_as_bytes())
                except TypeError as e:
                    print(f"--Error: {e}")
                    print("Returning to menu.")
            
            elif request == "hdp":
                msg = Message(new=True, purpose=4, payload=bytes(1))
                ser.write(msg.get_as_bytes())
            
            elif request == "ldp":
                msg = Message(new=True, purpose=6, payload=bytes(1))
                ser.write(msg.get_as_bytes())

            elif request == 'f':
                print('Enter path to file:')
                path = input('>> ')
                if not os.path.exists(path):
                    print(f"Error: file {path} does not exist. Returning to menu.")
                    continue
                with open(path, 'rb') as f:
                    contents = f.read()
                # print(contents)
                msg_title = Message(new=True, purpose=10, number=1, payload=os.path.basename(path).encode())
                ser.write(msg_title.get_as_bytes())
                msgs : list[Message] = Message.message_split(purpose_for_all=10, big_payload=contents, index_offset=1)
                for msg in msgs:
                    print(msg)
                    ser.write(msg.get_as_bytes())
            
            elif request == 'cp':
                print('Enter path to file ON ROVER:')
                path = input(">> ")
                ser.write(Message(new=True, purpose=11, payload=path.encode()).get_as_bytes())
                
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        print(f"--Error (main loop): exception. {e}")
        exit(0)

#####################
##### FUNCTIONS #####
#####################

def request_camera():
    try:
        cam_num = int(input("Pick camera: (0-4) for cams 0-4"))
        if cam_num < 0 or cam_num > 4:
           return -1
        return cam_num
    except:
        return -1


##### THE BRAINS FOR DECODING IMPORTED MESSAGES FROM ROVER
def process_messages() -> None:
    print("thread activated :)")

    ldp_str = b''
    hdp_str = b''
    vid_feed_str = b''

    ldp_num = 0
    hdp_num = 0
    vid_feed_num = 0

    # Continuously check for messages, process them according to their purpose.
    while not kill_threads:
        if len(messages_from_rover) == 0:
            continue

        curr_msg : Message = messages_from_rover.popleft()

        if curr_msg.purpose == Purpose.ERROR: # indicates ERROR
            error_msg = curr_msg.get_payload().decode()
            print(error_msg)
            with open(ERR_LOG,  'a') as f:
                f.write(error_msg + '\n')

        elif curr_msg.purpose == Purpose.HEARTBEAT: # indicates "HEARTBEAT / position"
            pass
        
        elif curr_msg.purpose == Purpose.VIDEO: # indicates "VIDEO FEED"
            if vid_feed_num < curr_msg.number:
                vid_feed_str += curr_msg.get_payload()
                vid_feed_num += 1
            else:
                vid_feed_num = 0
                vid_feed_str += curr_msg.get_payload()
                try:
                    save_and_output_image(vid_feed_str, "vid_feed")
                except Exception as e:
                    print(e)
                vid_feed_str = b''
        
        elif curr_msg.purpose == Purpose.HIGH_DEFINITION_PHOTO: # indicates "HIGH DEFINITION PHOTO"
            if hdp_num < curr_msg.number:
                hdp_str += curr_msg.get_payload()
                hdp_num += 1
            else:
                hdp_num = 0
                hdp_str += curr_msg.get_payload()
                try:
                    save_and_output_image(hdp_str, "hdp")
                except Exception as e:
                    print(e)
                hdp_str = b''
        
        elif curr_msg.purpose == Purpose.LOW_DEFINITION_PHOTO: # indicates "LOW DEFINITION PHOTO"
            if ldp_num < curr_msg.number:
                ldp_str += curr_msg.get_payload()
                ldp_num += 1
            else:
                ldp_num = 0
                ldp_str += curr_msg.get_payload()
                try:
                    save_and_output_image(ldp_str, "ldp")
                except Exception as e:
                    print(e)
                ldp_str = b''
        
        elif curr_msg.purpose == Purpose.FILE_CONTENTS: # indicates receiving a file
            if curr_msg.number == 1:
                current_file = curr_msg.get_payload().decode()
                print(f'copying file {current_file}...')
            elif curr_msg.number == 0:
                with open(f'./{current_file}', 'ab') as f:
                    f.write(curr_msg.get_payload())
                print(f"file {current_file} received.")
                current_file = ''
            elif not current_file:
                error_str = "--Error: file contents received, but no file name for said contents."
                print(error_str, file=sys.stderr)
            else:
                print(f'writing to {current_file}.')
                with open(f'./{current_file}', 'ab') as f:
                    f.write(curr_msg.get_payload())


def save_and_output_image(buffer : bytearray, type : str) -> bool:
    try:
        #buffer = buffer.frombytes()
        # Convert the byte array to an integer numpy array 
        # (decoded image with ".imdecode", written to a file (".imwrite")
        # and displayed (".imshow"))
        image = np.frombuffer(buffer, dtype=np.uint8)
        frame = cv2.imdecode(image, 1)
        if not os.path.isdir(f"{type}"):
            os.mkdir(f"{type}")
        cv2.imwrite(f"{type}/{time.time()}.jpg", frame)
        cv2.imshow(f'{type}', frame)
        cv2.waitKey(0)
        return True
    except Exception as e:
        print(e)
        return False

# everything to do on shutdown
def exit_main(executor : concurrent.futures.ThreadPoolExecutor):
    global kill_threads
    kill_threads = True
    executor.shutdown(wait=False, cancel_futures=True)


def print_options() -> None:
    print("----------------")
    print("MENU OF CONTROLS")
    print("----------------")
    print("(quit) to quit THIS SIDE ONLY")
    print("(log) get most recent 10 msgs of the log")
    print('(vid) to turn on/off video feed')
    print("(ldp) for LD photo")
    print("(hdp) for HD photo")

    # following three may be merged together
    print("(dr) for driving")
    print("(arm) for arm control")
    print("(drl) operate the drill")

    print("(wrd) for sending word to arm to type out")
    print("(hbt) Heartbeat mode: Receive coordinates")
    print("(f) Copy file from base station to rover")
    print("(cp) Copy file from rover to base station")
    print("(test) Send over tester strings for debugging purposes")
    print("(literally anything else) See menu options again")

if __name__ == "__main__":
    main()

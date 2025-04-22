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
from collections import deque
from message import Message
import struct
import capture_controls
import subprocess
import concurrent.futures
from datetime import datetime
import atexit

#######################
##### GLOBAL VARS #####
#######################

messages_from_rover = deque()
MSG_LOG = "messages_base.log"
ERR_LOG = "errors_from_rover.log"
kill_threads = False

################
##### MAIN #####
################

def main():
    port = "/dev/cu.usbserial-BG00HO5R"
    #port = "/dev/cu.usbserial-B001VC58"
    port = "COM4"
    #port = "/dev/ttyUSB0"
    baud = 57600
    timeout = 0.1
    ser = serial.Serial(port=port, baudrate=baud, timeout=timeout)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # make sure the log file is empty
    open(MSG_LOG, 'w').close()

    # 3 concurrent threads: one read from serial port, 
    # one for processing messages, one for writing messages
    executor = concurrent.futures.ThreadPoolExecutor(3)
    future = executor.submit(process_messages)
    future = executor.submit(read_from_port, ser)
    atexit.register(exit_main, executor)

    try:
            
        # the main control
        while True:
            # Continuously display options and ask for user input
            print_options()
            request = input(">> ")
            
            if request == 'quit':
                exit_main(executor=executor)
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
                    hello = input("enter tester phrase, exit to exit: ")
                    if hello == "exit":
                        break
                    msg = Message(purpose=0, payload=hello.encode())
                    ser.write(msg.get_as_bytes())

            elif request == "vid":
                try: 
                    stop_video_request = input("n to stop feed, else start feed? >>")
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
                except TypeError:
                    print("Returning to menu.")
            
            elif request == "hdp":
                msg = Message(new=True, purpose=4, payload=bytes(1))
                ser.write(msg.get_as_bytes())
            
            elif request == "ldp":
                msg = Message(new=True, purpose=6, payload=bytes(1))
                ser.write(msg.get_as_bytes())

            elif request == 'f':
                path = input('Enter path to file: ')
                if not os.path.exists(path):
                    print(f"Error: file {path} does not exist. Returning to menu.")
                    continue
                with open(path, 'rb') as f:
                    contents = f.read()
                print(contents)
                msg_title = Message(new=True, purpose=10, number=1, payload=os.path.basename(path).encode())
                ser.write(msg_title.get_as_bytes())
                msgs : list[Message] = Message.message_split(purpose_for_all=10, big_payload=contents, index_offset=1)
                for msg in msgs:
                    print(msg)
                    ser.write(msg.get_as_bytes())
                
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        print(f"Error: exception. {e}")
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

##### READ FROM THE SERIAL PORT for incoming messages
def read_from_port(ser: serial.Serial):
    while not kill_threads:

        try:
            b_id = read_num_bytes(ser, 1)
            # ID, PURPOSE, NUMBER, SIZE, PAYLOAD, CHECKSUM
            if len(b_id) == 0:
                continue
            #print("Got a message")
            pot_msg = Message(new=False)
            b_id += read_num_bytes(ser, 1)
            pot_msg.set_msg_id(struct.unpack(">H", b_id)[0])
            #print("Got id")
            b_purpose = read_num_bytes(ser, 1)
            pot_msg.set_purpose(struct.unpack(">B", b_purpose)[0])
            #print("Got purpose")
            b_number = read_num_bytes(ser, 1)
            pot_msg.number = struct.unpack(">B", b_number)[0]
            #print("Got number")
            b_size = read_num_bytes(ser, 4)
            #print(struct.calcsize(">L"))
            pot_msg.set_size(b_size)
            #print(f"{b_id}{b_purpose}{b_number}{b_size}")
            print("Got size", pot_msg.size_of_payload)

            # print(pot_msg.size_of_payload)
            payload = read_num_bytes(ser, pot_msg.size_of_payload)
            # print(len(payload))
            pot_msg.set_payload(payload)
            #print("Got payload")
            checksum = read_num_bytes(ser, 1)
            #print("Got checksum")

            #print(checksum)
            if not Message.test_checksum(bytestring=pot_msg.get_as_bytes()[:-1], checksum=checksum):
                print("Checksum error")
                continue
            messages_from_rover.append(pot_msg)
            print(f"Message added {pot_msg}; len = {len(messages_from_rover)}")
        except Exception as e:
            print(e)

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

        if curr_msg.purpose == 0: # indicates ERROR
            error_msg = curr_msg.get_payload().decode()
            print(error_msg)
            with open(ERR_LOG,  'a') as f:
                f.write(error_msg + '\n')

        elif curr_msg.purpose == 2: # indicates "HEARTBEAT / position"
            pass
        
        elif curr_msg.purpose == 3: # indicates "VIDEO FEED"
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
        
        elif curr_msg.purpose == 4: # indicates "HIGH DEFINITION PHOTO"
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
        
        elif curr_msg.purpose == 6: # indicates "LOW DEFINITION PHOTO"
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
        
        elif curr_msg.purpose == 10: # indicates receiving a photo
            if curr_msg.number == 1:
                current_file = curr_msg.get_payload().decode()
                print(f'copying file {current_file}...')
            elif curr_msg.number == 0:
                with open(f'./{current_file}', 'ab') as f:
                    f.write(curr_msg.get_payload())
                print(f"file {current_file} received.")
                current_file = ''
            elif not current_file:
                error_str = "Error: file contents received, but no file name for said contents."
                print(error_str, file=sys.stdin)
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

def read_num_bytes(ser: serial.Serial, numbytes : int):
    read_bytes = b''
    while len(read_bytes) < numbytes:
        if kill_threads:
            return
        read_bytes += ser.read(numbytes - len(read_bytes))

    return read_bytes

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
    print("(f) Copy file as bytes")
    print("(test) Send over tester strings for debugging purposes")
    print("(literally anything else) See menu options again")

if __name__ == "__main__":
    main()

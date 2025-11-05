#!/usr/bin/env python3

import zmq
import struct

##### CONSTANTS ######
HOST = "10.12.134.205"
PORT = 12347

# create subscribe socket
context = zmq.Context()
socket = context.socket(zmq.SUB)

# connect to the video publish socket
socket.connect(f"tcp://{HOST}:{PORT}")
socket.subscribe("") # subscribe to everything

print(f"Connection open to {HOST}:{PORT}")
print("Waiting for control data...")

try:
    while True:
        # receive the message (an encoded image)
        payload = socket.recv()
        if not payload:
            break
        lspeed = struct.unpack(">h", payload[0:2])[0]
        rspeed = struct.unpack(">h", payload[2:4])[0]
        speed_scalar = struct.unpack(">f", payload[4:8])[0]
        cam_left = struct.unpack(">B", payload[8:9])[0]
        cam_right = struct.unpack(">B", payload[9:10])[0]
        button_x = struct.unpack(">B", payload[10:11])[0]
        button_y = struct.unpack(">B", payload[11:12])[0]

        msg = f"{lspeed} {rspeed}\n"
        
        # Instead of writing to Arduino, just print
        print(f"Would send to Arduino: {msg.strip()} | Scalar:{speed_scalar:.2f} | Cam L:{cam_left} R:{cam_right} | Btns X:{button_x} Y:{button_y}")

except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    socket.close()
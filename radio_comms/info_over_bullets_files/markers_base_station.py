#!/usr/bin/env python3

import zmq
import cv2
import numpy as np

##### CONSTANTS ######
HOST = "192.168.11.17"
PORT = 12345
NUM_CAMS = 1

sockets = []

# create subscribe socket
context = zmq.Context()

for i in range(0, NUM_CAMS):
    socket = context.socket(zmq.SUB)

    # connect to the video publish socket
    socket.connect(f"tcp://{HOST}:{PORT}")
    socket.subscribe(f"{i}/") # subscribe to only certain things
    sockets.append(socket)

print("connection established")

while True:
    # receive the message (an encoded image)
    for i in range(0, NUM_CAMS):
        message = sockets[i].recv()
        if not message:
            break
        print("received message")
        # decode the image and show it
        image = np.frombuffer(message[2:], dtype=np.uint8)
        frame = cv2.imdecode(image, 1)
        cv2.imshow(f'frame{i}',frame)
        cv2.waitKey(1)

cv2.destroyAllWindows()
for socket in sockets:
    socket.close()

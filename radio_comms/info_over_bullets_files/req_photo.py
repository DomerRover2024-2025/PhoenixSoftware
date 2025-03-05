import zmq
import cv2
import numpy as np


HOST = "192.168.11.17"
PORT = 12345
NUM_CAMS = 2

sockets = []


context = zmq.Context()

for i in range(0, NUM_CAMS):
    socket = context.socket(zmq.REQ)

    # connect to the video publish socket
    socket.connect(f"tcp://{HOST}:{PORT}")
    sockets.append(socket)


print("Connected")


while True: 
    for i in range(0, NUM_CAMS):
        socket.send_string("0")
        message = socket.recv()
        if not message:
            break
        print("received message")
        # decode the image and show it
        image = np.frombuffer(message[2:], dtype=np.uint8)
        frame = cv2.imdecode(image, 1)
        cv2.imshow(f'frame{i}',frame)
        cv2.waitKey(1)

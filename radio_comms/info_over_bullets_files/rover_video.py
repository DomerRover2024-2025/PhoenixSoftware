#!/usr/bin/env python3

import cv2
import zmq
import time

###### CONSTANTS ######
HOST = "0.0.0.0"
PORT = 12345
QUALITY = 80
TIME_BETWEEN_FRAMES = 0.05
CAM_PATHS = [
    '/dev/v4l/by-id/usb-046d_081b_32750F50-video-index0',
    '/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_Live_camera_SN0001-video-index0'
]
NUM_CAMS = len(CAM_PATHS)
# create publish socket and video capture object
context = zmq.Context()
socket = context.socket(zmq.PUB)
caps = [cv2.VideoCapture(path) for path in CAM_PATHS]


# bind the host and port
socket.bind(f"tcp://{HOST}:{PORT}")

while True:
    # capture frame; if successful encode it and publish it with quality QUALITY
    for i in range(0, NUM_CAMS):
        ret, frame = caps[i].read()
        if ret:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), QUALITY]
            encoded, buffer = cv2.imencode('.jpg', frame, encode_param)
            try:
                socket.send(f'{i}/'.encode() + buffer.tobytes())
            except Exception as e:
                print(e)
            #socket.send(b'adsfasdfasdf')
        time.sleep(TIME_BETWEEN_FRAMES)
for cap in caps:
    cap.release()
cv2.destroyAllWindows()
socket.close()

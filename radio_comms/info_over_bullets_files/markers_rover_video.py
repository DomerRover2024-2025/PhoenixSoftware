#!/usr/bin/env python3

import cv2
import zmq
import time
import numpy as np
import sys

###### CONSTANTS ######
HOST = "0.0.0.0"
PORT = 12345
QUALITY = 80
TIME_BETWEEN_FRAMES = 0.05
CAM_PATH = ["/dev/v4l/by-id/usb-Technologies__Inc._ZED_2i_OV0001-video-index0"]
NUM_CAMS = len(CAM_PATH)

# MARKER DETECTION CODE

ARUCO_DICT = {
        "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
        "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
        "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
        "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
        "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
        "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
        "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
        "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
        "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
        "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
        "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
        "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
        "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
        "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
        "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
        "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
        "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
        "DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
        "DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
        "DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
        "DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11
}

def aruco_display(corners, ids, rejected, image):
    if len(corners) > 0:
        ids = ids.flatten() #if theres a for loop for multiple markers

        for (markerCorner, markerID) in zip(corners, ids):

            #creating corners for lines
            corners = markerCorner.reshape((4, 2))
            (topLeft, topRight, bottomRight, bottomLeft) = corners

            topRight = (int(topRight[0]), int(topRight[1]))
            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
            topLeft = (int(topLeft[0]), int(topLeft[1]))
            bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))


            #draw the bounding box of the ArUCo detection
            cv2.line(image, topLeft, topRight, (0, 255, 0), 2)
            cv2.line(image, topRight, bottomRight, (0, 255, 0), 2)
            cv2.line(image, bottomRight, bottomLeft, (0, 255, 0), 2)
            cv2.line(image, bottomLeft, topLeft, (0, 255, 0), 2)

            center_x = int((topLeft[0] + bottomRight[0]) / 2.0)
            center_y = int((topLeft[1] + bottomRight[1]) / 2.0)
            cv2.circle(image, (center_x, center_y), 5, (0, 0, 255), -1)
            cv2.putText(image, str(markerID), (topLeft[0], topLeft[1] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            print("[INFO] ArUCo marker ID:'{}".format(markerID))

    return image


def video_feed():
    
    # select the ArUCo tag type and ID
    aruco_selection = "DICT_4X4_50"
    arucoDict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[aruco_selection])
    arucoParams = cv2.aruco.DetectorParameters()
    
    # capture frame; if successful encode it and publish it with quality QUALITY
    ret, frame = cap.read()

    if ret:

        # resizing image
        h, w, _ = frame.shape
        width = 1000
        height = int(width*(h/w))
        frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_CUBIC)

        # marker detection
        detected_markers = frame.copy()
        aruco_detector = cv2.aruco.ArucoDetector(arucoDict, arucoParams)
        corners, ids, rejected = aruco_detector.detectMarkers(frame)

        if len(detected_markers) > 0:
            detected_markers = aruco_display(corners, ids, rejected, frame)

        #cv2.imshow("Image", detected_markers)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            exit(1)
        
        return detected_markers

if __name__ == "__main__":
    # create publish socket
    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    # bind the host and port
    socket.bind(f"tcp://{HOST}:{PORT}")
    
    if len(sys.argv) == 1:
        cameraID = 0
    else:
        cameraID = sys.argv[1]
    
    #creates video capture object
    cap = cv2.VideoCapture(CAM_PATH[0])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    frame = video_feed(cameraID)

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), QUALITY]
    encoded, buffer = cv2.imencode('.jpg', frame, encode_param)

    try:
        socket.send("0/".encode() + buffer.tobytes())
    except Exception as e:
        print(e)
    #socket.send(b'adsfasdfasdf')
    time.sleep(TIME_BETWEEN_FRAMES)

    cap.release()
    cv2.destroyAllWindows()
    socket.close()

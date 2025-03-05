#!/usr/bin/env python3

import cv2

# Open 3 cameras
caps = []
cap1 = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(1)
#cap3 = cv2.VideoCapture(2)
caps.append(cap1)
caps.append(cap2)
#caps.append(cap3)


# Check if cameras are opened successfully or not cap2.isOpened() or not cap3.isOpened()
if not cap1.isOpened() :
    print("Error: Could not open one or more cameras.")
    exit()

# Create a window to display the video streams
#cv2.namedWindow("Camera Streams", cv2.WINDOW_NORMAL)
#cv2.resizeWindow("Camera Streams", 800, 600)

inputCam = 0

while True:
    ret, frame = caps[inputCam].read()
    if not ret:
        print(f"Error: Could not read from camera {inputCam}.")
        break
    cv2.imshow('Camera Feed', frame)
    key = cv2.waitKey(5)
    # Press 'q' to exit the loop
    if cv2.waitKey(5) == ord('0'):
        inputCam = 0
    if cv2.waitKey(5) == ord('1'):
        inputCam = 1
    #if cv2.waitKey(5) == ord('2'):
        #inputCam = 2

    


    
for cap in caps:
    cap.release()
cv2.destroyAllWindows()



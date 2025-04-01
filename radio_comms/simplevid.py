import cv2
import sys

cap = cv2.VideoCapture(sys.argv[1])
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if ret:
        cv2.imshow('frame', frame)
        cv2.waitKey(0)
    else:
        print("me no work")


import cv2

class ImageCapturer:

    def __init__(self, cameraPaths):
        self.cameraPaths = cameraPaths
        self.cap = cv2.VideoCapture(0)
        self.running = False

    def isTakingVideo(self):
        return self.running

    def stopTakingVideo(self):
        self.running = False

    def startTakingVideo(self):
        self.running = True

    def changeCamera(self, cameraIndex : int):
        self.cap = cv2.VideoCapture(self.cameraPaths[cameraIndex])

    def captureImage(self, quality : int, resize_width : int=None) -> tuple[int, bytearray]:
        ret, frame = self.cap.read() 

        if not ret:
            return 0, None

        if resize_width:
            resize_factor = resize_width / frame.shape[1]
            frame = cv2.resize(frame, (resize_width, int(resize_factor * frame.shape[0])))

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        encoded, buffer = cv2.imencode('.jpg', frame, encode_param) 

        size_of_data = len(buffer)
        return size_of_data, buffer


import cv2
import os
import time
import traceback
import numpy as np
from message import Message
from scheduler import Scheduler

class BaseStationMessageProcessor:
    class OngoingBytes:
        def __init__(self, name : str):
            self.name = name
            self.bytestring = b''
            self.count = 0

        def reset(self):
            self.bytestring = b''
            self.count = 0

    def __init__(self, log : str, scheduler : Scheduler):
        self.currentFile = ""
        self.counter = 0
        self.log = log
        open(self.log, 'w').close()
        self.scheduler = scheduler
        self.lowDefPhotoBytes = self.OngoingBytes('ldp')
        self.highDefPhotoBytes = self.OngoingBytes('hdp')
        self.videoFeedBytes = self.OngoingBytes('vid')

    def handleAcknowledgment(self, message : Message):
        messageID = int.from_bytes(message.get_payload(), 'big')
        self.scheduler.acknowledgmentReceived(messageID)

    def handleDebugMessage(self, message : Message):
        errorString = message.get_payload().decode()
        print('error received: ' + errorString)
        with open(self.log, 'a') as f:
            f.write(f'bahahaha {errorString}\n')

    def readFileOverPort(self, message : Message) -> None:
        if message.number == 1:
            self.currentFile = message.get_payload().decode()
            print(f'copying file {self.currentFile}...')

        elif message.number == 0:
            with open(f'./{self.currentFile}', 'ab') as f:
                f.write(message.get_payload())
            print(f"file {self.currentFile} received.")
            self.currentFile = ""

        elif not self.currentFile:
            error_str = "--Error: file contents received, but no file name for said contents."
            print(error_str, file=sys.stderr)

        else:
            print(f'writing to {self.currentFile}.')
            with open(f'./{self.currentFile}', 'ab') as f:
                f.write(message.get_payload())

    def handleOngoingMessage(self, message : Message, ongoingBytes : OngoingBytes):
        if ongoingBytes.count < message.number:
            ongoingBytes.bytestring += message.get_payload()
            ongoingBytes.count += 1
        else:
            ongoingBytes.bytestring += message.get_payload()
            buffer = ongoingBytes.bytestring
            ongoingBytes.reset()
            self.saveImage(buffer, ongoingBytes.name)

    def handleVideoMessage(self, message : Message) -> None:
        self.handleOngoingMessage(message, self.videoFeedBytes)

    def handleLowDefPhotoMessage(self, message : Message) -> None:
        self.handleOngoingMessage(message, self.lowDefPhotoBytes)

    def handleHighDefPhotoMessage(self, message : Message) -> None:
        self.handleOngoingMessage(message, self.highDefPhotoBytes)

    def saveImage(self, buffer : bytearray, folder : str) -> None:
        #buffer = buffer.frombytes()
        # Convert the byte array to an integer numpy array 
        # (decoded image with ".imdecode", written to a file (".imwrite")
        # and displayed (".imshow"))
        image = np.frombuffer(buffer, dtype=np.uint8)
        frame = cv2.imdecode(image, 1)
        if not os.path.isdir(f"{folder}"):
            os.mkdir(f"{folder}")
        cv2.imwrite(f"{folder}/{folder}_{self.counter}.jpg", frame)
        self.counter += 1
        # cv2.imshow(f'{folder}', frame)


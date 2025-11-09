#### This is going to be more of a user-interface
#### based program than the rover version, which
#### doesn't *have* a UI, so it will be completely covered
#### by the scheduler and message manager.

# This is the client side of a client-server model.
# This will be sending requests to the rover.

###################
##### IMPORTS #####
###################

import subprocess
import concurrent.futures
import traceback
import atexit
from serial import Serial

from message import Message
from messageQueue import MessageQueue
import capture_controls
from baseStationMessageProcessor import BaseStationMessageProcessor
from readerWriter import ReaderWriter
from serialReaderWriter import SerialReaderWriter
from socketReaderWriter import SocketReaderWriter
from userInterface import UserInterface

#######################
##### GLOBAL VARS #####
#######################

################
##### MAIN #####
################

def main():
    port = "/dev/cu.usbserial-BG00HO5R"
    #port = "/dev/cu.usbserial-B001VC58"
    # port = "COM4"
    #port = "/dev/ttyUSB0"
    baud = 57600
    timeout = 0.1

    ERR_LOG = "error.log"
    MSG_LOG = "base_station_messages.log"

    # make sure the log file is empty
    open(MSG_LOG, 'w').close()

    messageQueue : MessageQueue = MessageQueue()
    # readerWriter : ReaderWriter = SerialReaderWriter(port, baud, timeout, messageQueue)
    readerWriter : ReaderWriter = SocketReaderWriter('localhost', 9999, messageQueue, rover=False)
    userInterface : UserInterface = UserInterface(MSG_LOG, readerWriter)

    # 3 concurrent threads: one read from serial port, 
    # one for processing messages, one for writing messages
    executor = concurrent.futures.ThreadPoolExecutor(3)
    future = executor.submit(processMessages, messageQueue, ERR_LOG)
    future = executor.submit(readMessages, readerWriter, messageQueue)

    try:
        userInterface.inputLoop()
    except KeyboardInterrupt:
        exit_main(executor, messageQueue)
        exit(0)
    except Exception as e:
        exit_main(executor, messageQueue)
        exit(1)
    exit_main(executor, messageQueue)

#####################
##### FUNCTIONS #####
#####################

def readMessages(readerWriter : ReaderWriter, messageQueue : MessageQueue) -> None:
    while messageQueue.isRunning():
        message = readerWriter.readMessage()
        if message:
            messageQueue.append(message)
            print('message added', len(messageQueue))
    print('exited reading')

##### THE BRAINS FOR DECODING IMPORTED MESSAGES FROM ROVER
def processMessages(messageQueue : MessageQueue, ERR_LOG : str) -> None:
    messageProcessor = BaseStationMessageProcessor(ERR_LOG)
    print("starting message processing loop...")

    while messageQueue.isRunning():
        # TODO: fix spin waiting.
        if not messageQueue:
            continue

        print("popping message")
        current_message : Message = messageQueue.pop()
        print(f"message popped of purpose {current_message.purpose}")

        if current_message.purpose == Message.Purpose.ERROR: 
            messageProcessor.handleDebugMessage(current_message)

        elif current_message.purpose == Message.Purpose.HEARTBEAT: 
            pass

        elif current_message.purpose == Message.Purpose.VIDEO:
            messageProcessor.handleVideoMessage(current_message)

        elif current_message.purpose == Message.Purpose.HIGH_DEFINITION_PHOTO:
            messageProcessor.handleHighDefPhotoMessage(current_message)

        elif current_message.purpose == Message.Purpose.LOW_DEFINITION_PHOTO:
            messageProcessor.handleLowDefPhotoMessage(current_message)

        elif current_message.purpose == Message.Purpose.FILE_CONTENTS:
            messageProcessor.readFileOverPort(current_message) 

        else:
            print("unknown message purpose")
    print('Exiting processing messages')

# everything to do on shutdown
def exit_main(executor : concurrent.futures.ThreadPoolExecutor, messageQueue : MessageQueue):
    messageQueue.shutdown()
    print('shut down queue')
    executor.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()

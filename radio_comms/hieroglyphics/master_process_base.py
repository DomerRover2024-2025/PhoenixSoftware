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
from serial import Serial

from message import Message
from messageQueue import MessageQueue
import capture_controls
from baseStationMessageProcessor import BaseStationMessageProcessor
from readerWriter import ReaderWriter
from serialReaderWriter import SerialReaderWriter
from socketReaderWriter import SocketReaderWriter
from userInterface import UserInterface
from scheduler import Scheduler

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

    topics = {
        'all': 1
    } 

    scheduler : Scheduler = Scheduler(readerWriter, topics)
    userInterface : UserInterface = UserInterface(MSG_LOG, scheduler)

    # 3 concurrent threads: one read from serial port, 
    # one for processing messages, one for writing messages
    executor = concurrent.futures.ThreadPoolExecutor(4)
    future = executor.submit(processMessages, messageQueue, scheduler, ERR_LOG)
    future = executor.submit(readMessages, readerWriter, messageQueue)
    future = executor.submit(scheduler.sendMessages, messageQueue)

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
def processMessages(messageQueue : MessageQueue, scheduler : Scheduler, ERR_LOG : str) -> None:
    messageProcessor = BaseStationMessageProcessor(ERR_LOG, scheduler)
    while messageQueue.isRunning():
        # TODO: fix spin waiting.
        if len(messageQueue) == 0:
            continue

        print("popping message")
        currentMessage : Message = messageQueue.pop()
        print(f"message popped of purpose {currentMessage.purpose}")

        if currentMessage.purpose == Message.Purpose.ERROR: 
            messageProcessor.handleDebugMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.HEARTBEAT: 
            pass

        elif currentMessage.purpose == Message.Purpose.VIDEO:
            messageProcessor.handleVideoMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.HIGH_DEFINITION_PHOTO:
            messageProcessor.handleHighDefPhotoMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.LOW_DEFINITION_PHOTO:
            messageProcessor.handleLowDefPhotoMessage(currentMessage)

        elif currentMessage.purpose == Message.Purpose.FILE_CONTENTS:
            messageProcessor.readFileOverPort(currentMessage) 

        else:
            print("unknown message purpose")

# everything to do on shutdown
def exit_main(executor : concurrent.futures.ThreadPoolExecutor, messageQueue : MessageQueue):
    messageQueue.shutdown()
    print('shut down queue')
    executor.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()

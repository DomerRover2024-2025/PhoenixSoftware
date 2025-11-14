#### scheduler to handle OUTGOING MESSAGES to the base station

###################
##### IMPORTS #####
###################

import serial
from message import Message
from collections import deque
from readerWriter import ReaderWriter
from messageQueue import MessageQueue
import traceback

class Scheduler:

    # topics: dict[str (topic name), int (wrr value)]
    # messages: dict[str (topic name), deque[message]]
    def __init__(self, readerWriter : ReaderWriter, topics : dict[str, int]=None):
        self.readerWriter = readerWriter

        if not topics: 
            self.topics : dict[str, int] = {}
            self.messages : dict[str, deque[Message]] = {}
        else:
            self.topics : dict[str, int] = topics
            self.messages : dict[str, deque[Message]] = {topic : deque() for topic in self.topics}
        self.retransmission : MessageQueue = MessageQueue()
    def set_topics(self, topics) -> None:
        self.topics = topics
        self.messages = {topic : deque() for topic in self.topics}

    # wrr = weighted round robin value
    # aka: how many messages of THIS one to send
    #      for every wrr value of other topics
    def add_topic(self, topic_name, wrr_val) -> None:
        self.topics[topic_name] = wrr_val
        self.messages[topic_name] = deque()

    # add message to a given "topic"
    # I call this a "topic" but it's probably called a "server" for an actual wrr
    def addMessage(self, message: Message, topic : str='all') -> None:
        if topic not in self.messages:
            raise IndexError
        print("added message to scheduler")
        self.messages[topic].append(message)

    def addListOfMessages(self, messageList, topic : str='all') -> None:
        if topic not in self.messages:
            raise IndexError
        self.messages[topic].extend(messageList)

    def handleAcknowledgment(self, messageID : int):
        self.retransmission.remove(messageID)

    # weighted round robin algorithm?
    # implement with a thread, I think
    def sendMessages(self, messageQueue : MessageQueue):
     try:
        print("started up the wrr", self.topics)
        while messageQueue.isRunning():
            for topic in self.topics: # all the topic names
                c = 0 # packet counter
                '''
                if topic == 'vid_feed' and not capture_video_eh:
                    self.messages[topic].clear()
                '''
                while self.messages[topic] and c < self.topics[topic]:
                    try:
                        current_message = self.messages[topic].popleft()
                        print("writing message")
                        self.readerWriter.writeMessage(current_message)
                        c += 1
                        #print(f"{curr_msg.get_as_bytes()[4:8]}")
                        #print(f"Message sent: {curr_msg} of length {curr_msg.size_of_payload}")
                    except Exception as e:
                        print(f'--Error: in the scheduler loop: {e}')
            # pop a message
            '''
            failedMessage = self.retransmission.pop()
            self.readerWriter.writeMessage(failedMessage)
            self.retransmission.append(failedMessage)
            '''
     except:
        traceback.format_exc()
        # talkerNode.destroy_node()
        # rclpy.shutdown()
        # arduino.close()

    # print as a string
    def __str__(self) -> str:
        ret_str = ""
        for topic in self.topics:
            ret_str =f'{ret_str}:name={topic},wrr={self.topics[topic]},num_msg={len(self.messages[topic])}'
        return ret_str

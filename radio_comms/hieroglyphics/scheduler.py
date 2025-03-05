#### scheduler to handle OUTGOING MESSAGES to the base station

###################
##### IMPORTS #####
###################

import serial
import message
from collections import deque

class Scheduler:

    # topics: dict[str (topic name), int (wrr value)]
    # messages: dict[str (topic name), deque[message]]
    def __init__(self, ser : serial.Serial, topics : dict[str, int]=None):
        self.ser : serial.Serial = ser
        if not topics: 
            self.topics : dict[str, int] = {}
            self.messages : dict[str, deque[message.Message]] = {}
        elif type(topics) != dict:
            raise TypeError
        else:
            self.topics : dict[str, int] = topics
            self.messages : dict[str, deque[message.Message]] = {topic : deque() for topic in self.topics}
    
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
    def add_single_message(self, topic_name, msg : message.Message) -> None:
        if topic_name not in self.messages:
            raise IndexError
        self.messages[topic_name].append(msg)
    
    def add_list_of_messages(self, topic_name, lst_of_msgs : list[message.Message]) -> None:
        if topic_name not in self.messages:
            raise IndexError
        self.messages[topic_name].extend(lst_of_msgs)

    # print as a string
    def __str__(self) -> str:
        ret_str = ""
        for topic in self.topics:
            ret_str =f'{ret_str}:name={topic},wrr={self.topics[topic]},num_msg={len(self.messages[topic])}'
        return ret_str[1:]

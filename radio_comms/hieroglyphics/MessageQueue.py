# Author: Henry Jochaniewicz
# Date Modified: October 8, 2025
from collections import deque
from message import Message
import threading

class MessageQueue:

    def __init__(self):
        self.queue : list[Message] = deque()
        self.running : bool = True
        self.lock = threading.Lock()

    def append(self, message : Message):
        self.queue.append(message)

    def pop(self) -> Message:
        return self.queue.popleft()

    def isRunning(self) -> bool:
        isQueueRunning = self.running 
        with self.lock:
            isQueueRunning = self.running
        return isQueueRunning

    def remove(self, messageID : int) -> None:
        for message in self.queue:
            if message.msg_id == messageID:
                self.queue.remove(message)

    def shutdown(self) -> None:
        with self.lock:
            self.running = False

    def __len__(self):
        return len(self.queue)


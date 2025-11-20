# Author: Henry Jochaniewicz
# Date Modified: October 8, 2025
from collections import deque
from message import Message
import threading

class MessageQueue:

    def __init__(self):
        self.queue : list[Message] = deque()
        self.running : bool = True
        self.runningLock = threading.Lock()
        self.condition = threading.Condition()

    def append(self, message : Message):
        with self.condition:
            self.queue.append(message)
            self.condition.notify()

    # Blocking pop.
    def pop(self) -> Message:
        with self.condition:
            while len(self) == 0:
                self.condition.wait()
            return self.queue.popleft()

    def isRunning(self) -> bool:
        isQueueRunning = self.running 
        with self.runningLock:
            isQueueRunning = self.running
        return isQueueRunning

    def shutdown(self) -> None:
        with self.runningLock:
            self.running = False

    def __len__(self):
        length = 0
        with self.condition:
            length = len(self.queue)
        return length

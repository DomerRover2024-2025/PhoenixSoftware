# Author: Henry Jochaniewicz
# Date Modified: October 8, 2025
from collections import deque
from message import Message

class MessageQueue:

    def __init__(self):
        self.queue : list[Message] = deque()
        self.running : bool = True

    def append(self, message : Message):
        self.queue.append(message)

    def pop(self) -> Message:
        return self.queue.popleft()

    def isRunning(self) -> bool:
        return self.running

    def __len__(self):
        return len(self.queue)

    def __bool__(self):
        return len(self.queue) != 0

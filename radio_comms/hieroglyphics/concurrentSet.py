import threading

class ConcurrentSet:
    def __init__(self):
        self.Set : set[int] = set()
        self.lock = threading.Lock()

    def add(self, messageID : int) -> None:
        with self.lock:
            self.Set.add(messageID)

    def __contains__(self, messageID : int) -> bool:
        isContained = False
        with self.lock:
            isContained = messageID in self.Set
        return isContained

    def remove(self, messageID : int) -> None:
        with self.lock:
            self.Set.remove(messageID)

    def clear(self, messageID : int) -> None:
        with self.lock:
            self.Set.clear()

    def __len__(self) -> int:
        length = 0
        with self.lock:
            length = len(self.Set)
        return length

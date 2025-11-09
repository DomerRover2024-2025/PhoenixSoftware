from serial import Serial
from message import Message

class ReaderWriter: 

##### READ FROM THE SERIAL PORT for incoming messages
    def readMessage(self) -> Message:
        pass

    def writeMessage(self, message : Message) -> None:
        pass

import struct
import socket

from message import Message
from readerWriter import ReaderWriter
from messageQueue import MessageQueue

class SocketReaderWriter(ReaderWriter):
    
    def __init__(self, host, port, messageQueue : MessageQueue, rover : bool):
        self.messageQueue = messageQueue
        s = socket.socket()

        if rover:
            s.bind((host, port))
            s.listen(1)
            connection, address = s.accept()
            self.communicator = connection
        else:
            s.connect((host, port))
            self.communicator = s

    def writeMessage(self, message : Message):
        self.communicator.send(message.get_as_bytes())

    def readBytes(self, num_bytes : int):
        self.communicator.settimeout(1.0)
        read_bytes = b''
        while len(read_bytes) < num_bytes:
            read_bytes += self.communicator.recv(num_bytes - len(read_bytes))

        return read_bytes
    
    def readMessage(self) -> Message:
        potentialMessage = Message(new=False)

        try:
            b_id = self.readBytes(2)
        except TimeoutError:
            return None
        potentialMessage.set_msg_id(struct.unpack(">H", b_id)[0])

        b_purpose = self.readBytes(1)
        potentialMessage.set_purpose(struct.unpack(">B", b_purpose)[0])

        b_number = self.readBytes(1)
        potentialMessage.number = struct.unpack(">B", b_number)[0]

        b_size = self.readBytes(4)
        potentialMessage.set_size(struct.unpack(">L", b_size)[0])

        if potentialMessage.size_of_payload > 4096:
            print(f"--Error: buffer? ID: {potentialMessage.msg_id}, purpose: {potentialMessage.purpose}, num: {potentialMessage.number}, len_payload: {potentialMessage.size_of_payload}")

        payload = self.readBytes(potentialMessage.size_of_payload)
        potentialMessage.set_payload(payload)

        checksum = self.readBytes(1)
        same_checksums, calculated_checksum = Message.test_checksum(bytestring=potentialMessage.get_as_bytes()[:-1], checksum=checksum)

        if not same_checksums:    
            print(f"--Error: checksum. Received checksum: {checksum} | calculated checksum: {calculated_checksum}. {potentialMessage}")
            return None

        return potentialMessage

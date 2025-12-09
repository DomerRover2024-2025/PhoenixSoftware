from serial import Serial
import struct
from message import Message
from readerWriter import ReaderWriter
from messageQueue import MessageQueue

class SerialReaderWriter(ReaderWriter): 
    
    def __init__(self, port : str, baud : int, timeout : float, messageQueue : MessageQueue) -> None:
        self.ser : Serial = Serial(port=port, baudrate=baud, timeout=timeout)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.messageQueue = messageQueue

    def readBytes(self, num_bytes : int):
        read_bytes = b''
        while self.messageQueue.isRunning() and len(read_bytes) < num_bytes:
            read_bytes += self.ser.read(num_bytes - len(read_bytes))

        return read_bytes

    def writeMessage(self, message : Message):
        self.ser.write(message.get_as_bytes())
        

##### READ FROM THE SERIAL PORT for incoming messages
    def readMessage(self) -> Message:
        potentialMessage = Message(new=False)

        b_id = self.readBytes(2)
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


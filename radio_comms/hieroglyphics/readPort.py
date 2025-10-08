from serial import Serial
from message import Message

class Reader: 
    
    def __init__(self, ser : Serial, messageQueue : MessageQueue) -> None:
        self.ser : Serial = ser 
        self.messageQueue : MessageQueue = messageQueue

    def read_num_bytes(self, num_bytes : int):
        read_bytes = b''
        while self.messageQueue.isRunning() and len(read_bytes) < num_bytes:
            read_bytes += self.ser.read(num_bytes - len(read_bytes))

        return read_bytes

##### READ FROM THE SERIAL PORT for incoming messages
    def read_from_port(self):
        while self.messageQueue.isRunning()
            try:
                potential_message = Message(new=False)
                b_id = read_num_bytes(2)

                potential_message.set_msg_id(struct.unpack(">H", b_id)[0])
                b_purpose = read_num_bytes(1)

                potential_message.set_purpose(struct.unpack(">B", b_purpose)[0])
                b_number = read_num_bytes(1)

                potential_message.number = struct.unpack(">B", b_number)[0]
                b_size = read_num_bytes(4)

                potential_message.set_size(struct.unpack(">L", b_size)[0])

                if potential_message.size_of_payload > 4096:
                    print(f"--Error: buffer? ID: {potential_message.msg_id}, purpose: {potential_message.purpose}, num: {potential_message.number}, len_payload: {potential_message.size_of_payload}")

                payload = read_num_bytes(potential_message.size_of_payload)
                potential_message.set_payload(payload)

                checksum = read_num_bytes(1)
                same_checksums, calculated_checksum = Message.test_checksum(bytestring=potential_message.get_as_bytes()[:-1], checksum=checksum)

                if not same_checksums:    
                    print(f"--Error: checksum. Received checksum: {checksum} | calculated checksum: {calculated_checksum}. {potential_message}"
                    continue

                self.messageQueue.append(potential_message)
                print(f"Message added {potential_message}; len = {len(self.messageQueue)}")

            except Exception as e:
                print(f"Exception occured: {e}")


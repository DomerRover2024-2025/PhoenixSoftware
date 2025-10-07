import serial
from message import Message

class Reader: 
    def read_num_bytes(ser: serial.Serial, numbytes : int):
        read_bytes = b''
        while kill_threads and len(read_bytes) < numbytes:
            read_bytes += ser.read(numbytes - len(read_bytes))

        return read_bytes

##### READ FROM THE SERIAL PORT for incoming messages
    def read_from_port(ser: serial.Serial):
        while not kill_threads:
            try:
                b_id = read_num_bytes(ser, 1)

                if len(b_id) == 0:
                    continue

                pot_msg = Message(new=False)
                b_id += read_num_bytes(ser, 1)

                pot_msg.set_msg_id(struct.unpack(">H", b_id)[0])
                b_purpose = read_num_bytes(ser, 1)

                pot_msg.set_purpose(struct.unpack(">B", b_purpose)[0])
                b_number = read_num_bytes(ser, 1)

                pot_msg.number = struct.unpack(">B", b_number)[0]
                b_size = read_num_bytes(ser, 4)

                pot_msg.set_size(struct.unpack(">L", b_size)[0])

                if pot_msg.size_of_payload > 4096:
                    print(f"--Error: buffer? ID: {pot_msg.msg_id}, purpose: {pot_msg.purpose}, num: {pot_msg.number}, len_payload: {pot_msg.size_of_payload}")

                payload = read_num_bytes(ser, pot_msg.size_of_payload)
                pot_msg.set_payload(payload)

                checksum = read_num_bytes(ser, 1)
                the_same, calculated_checksum = Message.test_checksum(bytestring=pot_msg.get_as_bytes()[:-1], checksum=checksum)
                if not the_same:    
                    print(f"--Error: checksum. Received checksum: {checksum} | calculated checksum: {calculated_checksum}. {pot_msg}"
                else:
                    config.messages_from_rover.append(pot_msg)
                    print(f"Message added {pot_msg}; len = {len(messages_from_rover)}")
            except Exception as e:
                print(f"Exception occured: {e}")

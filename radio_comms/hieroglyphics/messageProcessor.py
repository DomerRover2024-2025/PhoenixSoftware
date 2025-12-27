import struct
from message import Message
from scheduler import Scheduler

class MessageProcessor:

    def __init__(self, log : str, scheduler : Scheduler): 
        self.scheduler = scheduler 
        self.log = log
        open(self.log, 'w').close()

    def handleAcknowledgment(self, message : Message):
        messageID = struct.unpack(">H", message.get_payload())[0]
        self.scheduler.handleAcknowledgment(messageID)
        print(f'acknowledgment for message with ID {messageID} received.')

    def generateAcknowledgment(self, message : Message) -> Message:
        return Message(new=True, purpose=Message.Purpose.ACK, payload=struct.pack(">H", message.msg_id))

    def handleDebugMessage(self, message : Message):
        errorString = message.get_payload().decode()
        print(f'Received debug message: {errorString}')
        with open(self.log, 'a') as f:
            f.write(f'{errorString}\n')
        # acknowledgment = Message(purpose=Message.Purpose.ERROR, payload=f'{errorString} received.'.encode())
        # self.scheduler.addMessage(acknowledgment, 'status')

    def addMessage(self, message : Message, topic : str='all'):
        self.scheduler.addMessage(message, topic)

    def addListOfMessages(self, messageList : list[Message], topic='all') -> None:
        self.scheduler.addListOfMessages(messageList, topic)

from messageQueue import MessageQueue
from readerWriter import ReaderWriter
from message import Message
from scheduler import Scheduler
import os
import capture_controls

class UserInterface:
    def __init__(self, messageLog : str, scheduler : Scheduler):
        self.log = messageLog
        self.scheduler = scheduler

    def printLog(self) -> None:
        tail_output = subprocess.run(["tail", '-n', 10, self.log], capture_output=True, text=True)
        print(tail_output.stdout)

    def createDrivingMessage(self, lspeed, rspeed, scalar, camleft, camright, x, y) -> Message:
        b_lspeed = struct.pack(">h", int(lspeed))
        b_rspeed = struct.pack(">h", int(rspeed))
        b_scalar = struct.pack(">f", scalar)
        b_camleft = struct.pack(">B", camleft)
        b_camright = struct.pack(">B", camright)
        b_button_x = struct.pack(">B", camright)
        b_button_y = struct.pack(">B", camright)
        payload = b_lspeed + b_rspeed + b_scalar + b_camleft + b_camright + b_button_x + b_button_y

        # pack up the message
        controls_message = Message(new=True, purpose=Message.Purpose.MOVEMENT, payload=payload)
        return controls_message
    

    def handleControlsFromController(self) -> None:
        capture_controls.pygame.init()
        capture_controls.pygame.joystick.init()

        try:
            gen = capture_controls.run({}, 1, False)
        except:
            print("No joystick found")
            return
        while True:
            controlsMessage = createDrivingMessage(*next(gen))
            self.scheduler.addMessage(controlsMessage)
        
    def sendTestMessages(self) -> None:
        while True:
            testString = input("Tester phrase (exit to exit) >> ")
            if testString == "exit":
                break
            message = Message(purpose=Message.Purpose.ERROR, payload=testString.encode())
            self.scheduler.addMessage(message)

    def sendRequestMessage(self, purpose : Message.Purpose):
        message = Message(new=True, purpose=purpose, payload=bytes(1))
        self.scheduler.addMessage(message)

    def request_camera(self) -> int:
        try:
            cam_num = int(input("Pick camera: (0-4) for cams 0-4"))
        except ValueError:
            return -1
        if cam_num < 0 or cam_num > 4:
           return -1
        return cam_num

    def sendVideoRequestMessage(self):
        stop_request = input("n to stop feed, else start: >> ")
        cam_num = -1
        if stop_request == 'n':
            cam_num = request_camera()
            if cam_num == -1:
                return
        b_cam = struct.pack(">b", cam_num)
        message = Message(new=True, purpose=Message.Purpose.VIDEO, payload=b_cam)
        self.scheduler.addMessage(message)

    def sendFileContents(self):
        print('Enter path to file:')
        path = input('>> ')
        if not os.path.exists(path):
            print(f"Error: file {path} does not exist. Returning to menu.")
            return 
        with open(path, 'rb') as f:
            contents = f.read()
        basename = os.path.basename(path)
        message_title = Message(new=True, purpose=Message.Purpose.FILE_CONTENTS, number=1, payload=basename.encode())
        messages = Message.message_split(purpose_for_all=Message.Purpose.FILE_CONTENTS, big_payload=contents, index_offset=1)

        self.scheduler.addMessage(message_title)
        self.scheduler.addListOfMessages(message)

    def print_options(self) -> None:
        print("----------------")
        print("MENU OF CONTROLS")
        print("----------------")
        print("(quit) to quit THIS SIDE ONLY")
        print("(log) get most recent 10 msgs of the log")
        print('(vid) to turn on/off video feed')
        print("(ldp) for LD photo")
        print("(hdp) for HD photo")

        # following three may be merged together
        print("(dr) for driving")
        print("(arm) for arm control")
        print("(drl) operate the drill")

        print("(wrd) for sending word to arm to type out")
        print("(hbt) Heartbeat mode: Receive coordinates")
        print("(f) Copy file from base station to rover")
        print("(cp) Copy file from rover to base station")
        print("(test) Send over tester strings for debugging purposes")
        print("(literally anything else) See menu options again")

    def inputLoop(self) -> None:
        while True:
            # Continuously display options and ask for user input
            self.print_options()
            request = input(">> ")
            
            if request == 'quit':
                return

            elif request == "test":
                self.sendTestMessages()

            elif request == 'log':
                self.printLog()

            elif request == "dr":
                self.handleControlsFromController()

            elif request == "vid":
                self.sendVideoRequestMessage()
            
            elif request == "hdp":
                self.sendRequestMessage(Message.Purpose.HIGH_DEFINITION_PHOTO)
            
            elif request == "ldp":
                self.sendRequestMessage(Message.Purpose.LOW_DEFINITION_PHOTO)

            elif request == 'f':
                self.sendFileContents()
            
            elif request == 'cp':
                print('Enter path to file ON ROVER:')
                path = input(">> ")
                message = Message(new=True, purpose=Message.Purpose.REQUEST_FILE, payload=path.encode())
                self.scheduler.addMessage(message)

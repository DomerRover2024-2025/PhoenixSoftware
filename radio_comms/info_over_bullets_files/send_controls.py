#!/usr/bin/env python3

import zmq
import time
import struct
import capture_controls

def main():
    ###### CONSTANTS ######
    HOST = "*"
    PORT = 12347

    # create publish socket and video capture object
    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    capture_controls.pygame.init()
    capture_controls.pygame.joystick.init()
    gen = capture_controls.run({}, 1, False)

    # bind the host and port
    socket.bind(f"tcp://{HOST}:{PORT}")

    print("connected to publisher")

    while True:
        lspeed, rspeed, scalar, camleft, camright, button_x, button_y = next(gen)
        b_lspeed = struct.pack(">h", lspeed)
        b_rspeed = struct.pack(">h", rspeed)
        b_scalar = struct.pack(">f", scalar)
        b_camleft = struct.pack(">B", camleft)
        b_camright = struct.pack(">B", camright)
        b_button_x = struct.pack(">B", button_x)
        b_button_y = struct.pack(">B", button_y)
        payload = b_lspeed + b_rspeed + b_scalar + b_camleft + b_camright + b_button_x + b_button_y

        print(lspeed, rspeed)

        socket.send(payload)
    socket.close()

if __name__ == "__main__":
    main()

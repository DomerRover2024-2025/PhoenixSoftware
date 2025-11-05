#!/usr/bin/env python3

import zmq
import time
import struct
import joystick

def main():
    ###### CONSTANTS ######
    HOST = "*"
    PORT = 12347

    # create publish socket and video capture object
    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    joystick.pygame.init()
    joystick.pygame.joystick.init()
    gen = joystick.run({}, 1, False)

    # bind the host and port
    socket.bind(f"tcp://{HOST}:{PORT}")

    print("connected to publisher")

    while True:
        try:
            lspeed, rspeed, scalar, camleft, camright, button_x, button_y = next(gen)
            
            # Clamp values to prevent overflow (joystick can output beyond ±255 with trigger_mult)
            lspeed = max(-255, min(255, lspeed))
            rspeed = max(-255, min(255, rspeed))
            
            # Scale from ±255 to ±100 for Arduino
            lspeed = int(lspeed * 100 / 255)
            rspeed = int(rspeed * 100 / 255)
            
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
        except (pygame.error, StopIteration) as e:
            print(f"Controller error: {e}. Reconnecting...")
            time.sleep(0.5)
            continue
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(0.5)
            continue
    socket.close()

if __name__ == "__main__":
    main()

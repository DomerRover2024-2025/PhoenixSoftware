#!/usr/bin/python3
import sys
import subprocess
import signal

def menu() -> str:
    print("What would you like to run?")
    print(" - (ctrl) send controls")
    print(" - (vid) start video feed")
    print(" - (kill <ctrl/vid>) kill a running process")
    print(" - (q) quit the process")
    return input(">> ")

def main() -> None:
    file_ctrls = 'ctrls_log.log'
    file_cvid = 'vid_log.log'
    ctrl = None
    vid = None
    while True:
        choice = menu()
        if choice == 'ctrl':
            ctrl = subprocess.Popen(['./send_controls.py'], stdout=subprocess.PIPE)
            print('ctrl opened')
        elif choice == 'vid':
            vid = subprocess.Popen(['./base_station_video.py'], stdout=subprocess.PIPE)
            print('vid opened')
        elif choice.startswith('kill'):
            choices = choice.split()
            if len(choices) != 2:
                continue
            if choices[1] == 'vid' and vid is not None:
                vid.kill()
                vid = None
                print('vid killed')
            elif choices[1] == 'ctrl' and ctrl is not None:
                ctrl.kill()
                ctrl = None
                print('ctrl killed')
        elif choice == 'q':
            if vid:
                vid.kill()
            if ctrl:
                ctrl.kill()
            break



if __name__ == "__main__":
    main()

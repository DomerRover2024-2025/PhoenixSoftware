import pygame
import serial
import time

def deadzone(val, threshold=0.05):
    return 0 if abs(val) < threshold else val

def map_axis(val):
    # Map -1..1 to -255..255 for PWM
    return int(val * 255)

def main():
    # Replace with your Arduino serial port
    arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    pygame.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    print("Started. Use left stick to drive the middle wheels. Ctrl+C to stop.")
    try:
        while True:
            pygame.event.pump()
            left_x = deadzone(joystick.get_axis(0))
            left_y = deadzone(-joystick.get_axis(1))  # Invert Y axis

            # For a tank-style drive using only the left stick's Y axis for forward/backward
            left_middle = map_axis(left_y)
            right_middle = map_axis(left_y)

            # If you want to allow turning with left/right stick:
            # left_middle = map_axis(left_y + left_x)
            # right_middle = map_axis(left_y - left_x)

            # Send as "left right\n"
            msg = f"{left_middle} {right_middle}\n"
            arduino.write(msg.encode('utf-8'))
            print(f"Sent: {msg.strip()}")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Exiting.")
    finally:
        arduino.close()
        pygame.quit()

if __name__ == "__main__":
    main()
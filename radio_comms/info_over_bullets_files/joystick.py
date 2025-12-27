#!/usr/bin/env python3
"""
joystick.py

Improved joystick handling with:
- normalized triggers
- responsive polling (small delay)
- tank-turn mode when both bumpers are held:
    diff = right_trigger - left_trigger
    left_power = diff * triggerMult
    right_power = -diff * triggerMult
- generator API unchanged: yields
  (dutyCycleLeft, dutyCycleRight, triggerMult, b_x1, b_circle1, b_triangle1, b_square1)

Optional ROS2 mode:
- Run with --ros to publish motor commands to /motor_commands topic
- Uses std_msgs/Float32MultiArray: [left_power, right_power] in -1..1 range
"""

from __future__ import annotations

import pygame
import time
import math
import argparse
from typing import Dict, Generator, Tuple

# Try importing ROS2 (optional)
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Float32MultiArray
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False
    Node = object  # type: ignore

# Constants - change these to match your controller if needed
POLL_DELAY = 0.04            # seconds between polls (responsive)
DEADZONE = 0.05
ROUND_AXIS = 4               # rounding precision for axes
TRIGGER_SENSITIVITY = 0.001  # how much triggers affect triggerMult per loop (kept similar to original)
TRIGGER_MIN = 0.1
TRIGGER_MAX = 2.0

# Button/axis indices used in original file (keep these if your controller matches)
AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_RIGHT_X = 2
AXIS_RIGHT_Y = 3
AXIS_RIGHT_TRIGGER = 4      # original code used get_axis(4) as right trigger
AXIS_LEFT_TRIGGER = 5       # original code used get_axis(5) as left trigger

BUTTON_X = 0
BUTTON_CIRCLE = 1
BUTTON_SQUARE = 2
BUTTON_TRIANGLE = 3

BUTTON_LEFT_IN = 7
BUTTON_RIGHT_IN = 8
BUTTON_LBUMPER = 9
BUTTON_RBUMPER = 10

BUTTON_PAD_UP = 11
BUTTON_PAD_DOWN = 12

def deadzone(value: float) -> float:
    """Apply deadzone and rounding to an axis value (-1..1 expected)."""
    if abs(value) < DEADZONE:
        return 0.0
    return round(value, ROUND_AXIS)

def normalize_trigger(axis_value: float) -> float:
    """
    Convert trigger axis (-1..1 typical) to normalized 0..1 range and apply deadzone.
    Original code added 1 to axis; this gives clearer semantics:
        raw axis: -1 (released) -> 0.0, +1 (fully pressed) -> 1.0
    """
    norm = (axis_value + 1.0) / 2.0
    if abs(norm) < DEADZONE:
        return 0.0
    return round(norm, ROUND_AXIS)

def value_map(val: float) -> int:
    """Map float in [-1..1] (or 0..1 where appropriate) to 0..255 duty cycle expected by sender."""
    # The original code did `int(val * 255)` for a 0..1 value; here we handle both negative and positive.
    # Clamp input to [-1, 1]
    clamped = max(-1.0, min(1.0, val))
    # If negative values should map to 0..255 differently, adjust here. We'll map -1..1 -> -255..255 (but send_controls packs >h)
    # To match original usage (which appears to assume 0..255), provide positive range for duty cycles:
    # We'll map -1..1 -> -255..255 and the publisher code can interpret appropriately.
    return int(clamped * 255)

def cart2pol(x: float, y: float) -> Tuple[float, float]:
    """Convert x,y in -1..1 cartesian to (magnitude_in_0_1, angle_degrees 0..360)."""
    radius = min(math.sqrt(x * x + y * y), 1.0)
    angle = math.degrees(math.atan2(y, x))  # -180..180
    return (radius, (angle + 360) % 360)

def calc_wheel_speeds(magnitude: float, angle: float) -> Tuple[float, float]:
    """
    Compute left and right wheel power in range -1..1 according to original algorithm,
    with the same slowdown heuristics kept.
    """
    magnitude = min(magnitude, 1.0)
    angle = angle % 360.0

    if 0 <= angle <= 90:
        left_speed = magnitude
        right_speed = magnitude * (angle / 90.0)
    elif 90 < angle <= 180:
        left_speed = magnitude * (1.0 - (angle - 90.0) / 90.0)
        right_speed = magnitude
    elif 180 < angle <= 270:
        left_speed = -magnitude * ((angle - 180.0) / 90.0)
        right_speed = -magnitude
    else:
        left_speed = -magnitude
        right_speed = -magnitude * (1.0 - (angle - 270.0) / 90.0)

    # slowdown heuristics preserved
    if 150 < angle < 210:
        right_speed = right_speed * max(0.3, abs(angle - 180.0) / 30.0)
    if angle > 330:
        left_speed = left_speed * max(0.3, abs(angle - 360.0) / 30.0)
    if angle < 30:
        left_speed = left_speed * max(0.3, angle / 30.0)

    # ensure range [-1, 1]
    left_speed = max(-1.0, min(1.0, left_speed))
    right_speed = max(-1.0, min(1.0, right_speed))

    return left_speed, right_speed

def send_drive_signals(left: float, right: float) -> Tuple[int, int]:
    """Map -1..1 floats to duty cycle ints (0..255 or signed depending on your protocol)."""
    # Keep same semantics as original `valueMap(val)` which was `int(val * 255)` (likely 0..255)
    # Here we return signed mapping to preserve direction info.
    return value_map(left), value_map(right)

def run(joysticks: Dict[int, pygame.joystick.Joystick], trigger_mult: float = 1.0, stop_flag: bool = False
       ) -> Generator[Tuple[int, int, float, int, int, int, int], None, None]:
    """
    Main generator that yields control packets:
     (dutyCycleLeft, dutyCycleRight, triggerMult, b_x1, b_circle1, b_triangle1, b_square1)

    Parameters:
    - joysticks: dict to be filled with joysticks (keyed by instance id)
    - trigger_mult: multiplier scalar for speed
    - stop_flag: if True, motors should be zeroed
    """
    pygame.init()
    pygame.joystick.init()

    # Initialize joystick objects already connected (if any)
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        joysticks[joy.get_instance_id()] = joy

    try:
        while True:
            # Process events (joystick connection/disconnection and other events)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.JOYDEVICEADDED:
                    try:
                        joy = pygame.joystick.Joystick(event.device_index)
                        joy.init()
                        joysticks[joy.get_instance_id()] = joy
                        print(f"Joystick {joy.get_instance_id()} connected")
                    except Exception as exc:
                        print("Joystick add error:", exc)
                if event.type == pygame.JOYDEVICEREMOVED:
                    # event.instance_id is joystick instance id in newer pygame
                    iid = getattr(event, "instance_id", None)
                    if iid is not None and iid in joysticks:
                        del joysticks[iid]
                        print(f"Joystick {iid} disconnected")

            if not joysticks:
                # No joystick; yield zeros periodically so caller isn't blocked indefinitely
                print("No joystick connected. Waiting...")
                time.sleep(1.0)
                yield (0, 0, trigger_mult, 0, 0, 0, 0)
                continue

            # Use first joystick (index 0 instance) if present
            if 0 not in joysticks:
                # fallback: pick an arbitrary joystick
                joy = next(iter(joysticks.values()))
            else:
                joy = joysticks[0]

            # Read axes and buttons
            try:
                raw_lt = joy.get_axis(AXIS_LEFT_TRIGGER)
                raw_rt = joy.get_axis(AXIS_RIGHT_TRIGGER)
            except Exception:
                # If triggers are not mapped to these axes on this controller, default to 0
                raw_lt = -1.0
                raw_rt = -1.0

            a_lt = normalize_trigger(raw_lt)   # 0..1
            a_rt = normalize_trigger(raw_rt)   # 0..1

            b_lbumper = joy.get_button(BUTTON_LBUMPER)
            b_rbumper = joy.get_button(BUTTON_RBUMPER)

            # Left stick / right stick axes for general movement
            a_leftx = deadzone(joy.get_axis(AXIS_LEFT_X))
            a_lefty = deadzone(joy.get_axis(AXIS_LEFT_Y) * -1.0)   # invert Y to match original
            a_rightx = deadzone(joy.get_axis(AXIS_RIGHT_X))
            a_righty = deadzone(joy.get_axis(AXIS_RIGHT_Y) * -1.0)

            # Other buttons
            b_left_in = joy.get_button(BUTTON_LEFT_IN)
            b_right_in = joy.get_button(BUTTON_RIGHT_IN)

            b_x = joy.get_button(BUTTON_X)
            b_circle = joy.get_button(BUTTON_CIRCLE)
            b_square = joy.get_button(BUTTON_SQUARE)
            b_triangle = joy.get_button(BUTTON_TRIANGLE)

            b_pad_up = joy.get_button(BUTTON_PAD_UP)
            b_pad_down = joy.get_button(BUTTON_PAD_DOWN)

            # Convert left stick into magnitude and angle
            mag, angle = cart2pol(a_leftx, a_lefty)

            # Adjust trigger multiplier by right trigger similar to original (kept small effect)
            trigger_mult = trigger_mult + a_rt * TRIGGER_SENSITIVITY
            trigger_mult = max(TRIGGER_MIN, min(TRIGGER_MAX, trigger_mult))

            # By default compute curved wheel speeds
            left_power, right_power = calc_wheel_speeds(mag, angle)

            # If both bumpers pressed, enter tank-turn mode: triggers control in-place rotation.
            # Behavior: diff = right_trigger - left_trigger
            # left_power = diff * trigger_mult
            # right_power = -left_power
            # This yields in-place rotation; pressing right trigger more spins one way, left trigger more the opposite.
            if b_lbumper and b_rbumper:
                diff = max(-1.0, min(1.0, a_rt - a_lt))
                left_power = diff * trigger_mult
                right_power = -diff * trigger_mult
                # Clamp to prevent trigger_mult from causing overflow
                left_power = max(-1.0, min(1.0, left_power))
                right_power = max(-1.0, min(1.0, right_power))

            # If 'inner' buttons indicate an emergency stop or toggle, replicate original stop behavior
            if b_left_in and not stop_flag:
                stop_flag = True
            if stop_flag:
                left_power, right_power = 0.0, 0.0

            # Convert to duty cycles / ints
            duty_left, duty_right = send_drive_signals(left_power, right_power)

            # Yield same tuple shape as original so `send_controls.py` remains compatible
            yield (duty_left, duty_right, trigger_mult, b_x, b_circle, b_triangle, b_square)

            time.sleep(POLL_DELAY)
    finally:
        pygame.quit()


# === Optional ROS2 Node ===
class JoystickNode(Node):
    """Simple ROS2 node that publishes motor commands from joystick."""
    
    def __init__(self):
        super().__init__('joystick_node')
        self.publisher = self.create_publisher(Float32MultiArray, 'motor_commands', 10)
        self.get_logger().info('Joystick node started, publishing to /motor_commands')
    
    def publish_motors(self, left_norm: float, right_norm: float):
        """Publish normalized motor values [-1..1] as Float32MultiArray."""
        msg = Float32MultiArray()
        msg.data = [float(left_norm), float(right_norm)]
        self.publisher.publish(msg)


def run_with_ros(joysticks: Dict[int, pygame.joystick.Joystick]):
    """Run joystick with ROS2 publishing."""
    if not ROS_AVAILABLE:
        print("ERROR: ROS2 not available. Install ROS2 to use --ros mode.")
        return
    
    rclpy.init()
    node = JoystickNode()
    gen = run(joysticks, trigger_mult=1.0, stop_flag=False)
    
    try:
        while rclpy.ok():
            try:
                duty_left, duty_right, trigger_mult, b_x, b_circle, b_triangle, b_square = next(gen)
            except StopIteration:
                break
            
            # Convert duty cycle back to normalized -1..1 for ROS message
            left_norm = max(-1.0, min(1.0, duty_left / 255.0))
            right_norm = max(-1.0, min(1.0, duty_right / 255.0))
            
            node.publish_motors(left_norm, right_norm)
            
            # Spin once to process callbacks
            rclpy.spin_once(node, timeout_sec=0.0)
            
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


def main():
    parser = argparse.ArgumentParser(description='Joystick driver with optional ROS2 support')
    parser.add_argument('--ros', action='store_true', help='Enable ROS2 publishing to /motor_commands')
    args = parser.parse_args()
    
    joysticks: Dict[int, pygame.joystick.Joystick] = {}
    
    if args.ros:
        run_with_ros(joysticks)
    else:
        # Standalone mode - just print packets
        gen = run(joysticks, trigger_mult=1.0, stop_flag=False)
        print("Running in standalone mode (no ROS). Press Ctrl+C to exit.")
        try:
            for packet in gen:
                duty_left, duty_right, trigger_mult, b_x, b_circle, b_triangle, b_square = packet
                print(f"Left: {duty_left:4d}, Right: {duty_right:4d}, Mult: {trigger_mult:.2f}, "
                      f"Buttons: X={b_x} O={b_circle} △={b_triangle} □={b_square}")
        except KeyboardInterrupt:
            print("\nExiting...")


if __name__ == "__main__":
    main()

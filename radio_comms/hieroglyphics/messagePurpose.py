# Authors: Henry Jochaniewicz
# Date last modified: September 28, 2025
# Notes:

from enum import Enum

class Purpose(Enum):
    ERROR=0
    MOVEMENT=1
    HEARTBEAT=2
    VIDEO=3
    HIGH_DEFINITION_PHOTO=4
    ARM_WORD=5
    LOW_DEFINITION_PHOTO=6
    CSV=8
    CAMERA_VISION=9
    FILE_CONTENTS=10
    REQUEST_FILE=11


RADIO_COMMS README

I recommend setting up a python virtual environment in the directory JUST OUTSIDE of the main repo.
- If you want to include it in the repo on your local you ***must*** add the name of the directory to the `.gitignore` file
  so that the folder is not pushed to this repo and cause unnecessary clutter.
- to avoid this set up the virtual environment just outside of the main Domer Rover repo

To set up a virtual environment:
- make a new directory with `mkdir .my_env_name`. 
  - You can call it something different, I recommend the `.` beforehand to make it hidden.
- `cd` into that directory.
- run `python3 -m venv .` if on a UNIX based system, or `python -m venv .` if on a windows.
  - virtual env made!

To use the virtual environment:
- To activate the virtual environment:
  - on UNIX, run `source bin/activate` while still in the virtual env directory you made
  - on Windows, run `Scripts\activate` while still in the virtual env directory you made
  - This should make a `(.my_env_name)` before the command prompt / username in the terminal.
- to deactivate the virtual environment, run `deactivate`
- to install a package, run `python3 -m pip install <package_name>` (use `python` instead of `python3` if on windows)

These are the Python modules we are currently using. 
If you want to run the code please install these to the virtual environment 
    or to your local if you don't want to make a virtual environment.
- `pyzmq` (Zero message queueing, for building sockets)
  - run `import zmq` to import
- `opencv-python` (for video feed and camera capture)
  - run `import cv2` to import
- `numpy` (for array math operations)
  - run `import numpy as np` to import (you don't have to write `as np` but it's conventional)

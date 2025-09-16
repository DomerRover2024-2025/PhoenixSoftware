# Radio and Communications

## Setup

### Python virtual environment

I recommend setting up a python virtual environment in the directory JUST OUTSIDE of the main repo.
- If you want to include it in the repo on your local you ***must*** add the name of the directory to the `.gitignore` file
  so that the folder is not pushed to this repo and cause unnecessary clutter.
- to avoid this, set up the virtual environment just outside of the main Domer Rover repo

To set up a virtual environment:
- run 

```sh
python3 -m venv [environment_name]
```

if on a UNIX based system (Mac, Linux), or

```sh
python -m venv [environment_name]
```

if on a Windows system.

To use the virtual environment:
- To activate the virtual environment:
  - on UNIX, run `source bin/activate` while still in the virtual env directory you made
  - on Windows, run `Scripts\activate` while still in the virtual env directory you made
  - This should make a `([environment_name])` before the command prompt / username in the terminal.
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

### IP addressing 

You must ensure that the rover and user have the correct IP addresses.

As a note, here are the addresses of relevant items:
- Bullet-1: 192.168.1.1
- Bullet-2: 192.168.11.20
- Jetson: 192.168.11.17
- User: 192.168.11.179

The rover should automatically update its IP address to the correct one
once the communications system is properly set up.
This is done via a cronjob, which you may see and edit
via `sudo crontab -e`.

If it isn't, you may need to run the following:

```sh
sudo ifconfig enP8p1s0 192.168.11.17 netmask 255.255.255.0 up
```

This opens the ethernet IP address to the following.
You can see the status of various IP addressing with

```sh
nmcli dev wifi list
```

in a very nice looking output.

## Usage

### 900MHz

On the client (user), run 

```sh
python3 hieroglyphics/master_process_base.py
```

if in the radio/comms directory. 
On the server (rover), run

```sh
python3 hieroglyphics/master_process_rover.py
```

### 2.4GHz

These scripts are currently split.

#### Video

On the client (user), run

```sh
python3 info_over_bullet_files/base_station_video.py
```

if in the radio/comms directory. 
On the server (rover), run

```sh
python3 info_over_bullet_files/rover_video.py
```

#### Movement Controls

You will need to conenct a Ps4 controller to your laptop
(client) via Bluetooth.

On the client (user), run

```sh
python3 info_over_bullet_files/send_controls.py
```

if in the radio/comms directory. 
On the server (rover), run

```sh
python3 info_over_bullet_files/recv_controls.py
```

## Code

There are two main directories here:

### Hieroglyphics

Code for the 900MHz frequency, intended to be sent over RFD900x-US transceivers.


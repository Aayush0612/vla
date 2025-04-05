# ROSbot Vision-Language-Action (VLA) Control System

## Overview

This repository contains a Vision-Language-Action (VLA) control system for ROSbot, enabling natural language command processing through visual inputs. The system uses a vision-language model to interpret camera images and user instructions, converting them into robot movement commands.

## System Architecture

The system consists of three main components:

1. **ROSbot Controller** - Controls the physical robot, captures images, and executes movement commands
2. **VLA Server** - Processes images and text prompts using a language model to generate robot commands
3. **GUI** - Provides a user interface to view robot camera feed and input commands

## Components

### ROSbot Controller (`rosbot.py`)

The robot controller interfaces with the ROSbot hardware:

- Manages motors, sensors, and camera
- Captures and saves images
- Executes movement commands (go ahead, turn left, etc.)
- Monitors for new commands from the VLA server


### VLA Server (`main.py`)

A Flask-based API server that:

- Processes images from the robot
- Takes user text prompts
- Uses the Ollama `gemma3:4b` model to generate appropriate robot commands
- Returns command sequences to the controller


### GUI Interface (`gui.py`)

A Tkinter-based GUI that:

- Displays the robot's camera feed
- Allows users to enter natural language commands
- Sends requests to the VLA server
- Shows command execution status


## Requirements

- Python 3.7+
- Flask
- Ollama (with gemma3:4b model installed)
- Tkinter
- PIL (Pillow)
- Requests
- ROSbot simulation environment(e.g. Webots) or physical robot


## Installation

1. Clone this repository
2. Install the required Python packages:

```
pip install flask ollama pillow requests
```

3. Ensure Ollama is installed and the gemma3:4b model is available(you could use other vision models as well):

```
ollama pull gemma3:4b
```


## Running the System

1. Start the VLA Server:

```
python main.py
```

2. In a separate terminal, start the GUI:

```
python gui.py
```

3. Open a new Webots project or add the Husarion Rosbot to your existing Webots project and attach the rosbot.py controller to it instead of the rosbot.c controller file which comes pre-attached then refresh.



## Usage

1. The GUI will display the latest image from the robot's camera
2. Enter a natural language command in the prompt box (e.g., "move forward and roll in circles")
3. Click "Send" or press Enter
4. The VLA server will process the image and prompt, generating robot commands
5. The ROSbot will execute the sequence of commands

## Available Robot Commands

The system supports the following commands:

- `go_ahead(distance_meters)` - Move forward by specified distance
- `go_back(distance_meters)` - Move backward by specified distance
- `turn_left(angle_degrees)` - Turn left by specified angle
- `turn_right(angle_degrees)` - Turn right by specified angle
- `change_speed(speed_percent)` - Change the robot's movement speed


##Limitations
The current system has several important limitations:

Distance Perception:
The language model cannot accurately estimate real-world distances from images
Commands require explicit distance parameters (e.g., go_ahead(1.5)) that may not correspond to actual spatial conditions
No depth perception algorithm to reliably measure distances to objects or obstacles

Memory System:
The system lacks persistent memory between commands
Each image processing is independent with no context from previous observations
Cannot remember or refer to previously identified objects or locations
No mapping capability to build environment representations in a semantic way over time

Other Limitations:
Limited understanding of complex spatial relationships
No obstacle detection or collision avoidance system like SLAM
Basic movement commands that may not handle complex navigation challenges
Processing latency between image capture and command execution
Limited environmental adaptation capabilities in changing conditions

# NAO Performance Demos

This folder contains scripts and modules for running various interactive performances and demos with the NAO robot using the SIC framework.

## Contents

### Main Scripts
- **`main.py`**: The central performance demo. It executes a continuous performance where NAO demonstrates "awareness", expresses emotions via LEDs, and speaks/gestures based on "intents" (neutral, enjoyment, angry, etc.). This is based on example sentences which it will play at a uniform time distribution (used to show how the tts could be combined with gestures and emotion).
- **`snowwhite_demo.py`**: A storytelling demo ("Snow White") that is 'based' on the first scene of our performance. This is just to demonstrate how the performance could look like if every part of the performance is combined.
- **`opening_script.py`**: An introductory script where NAO introduces itself and the upcoming performance (Snow White).
- **`end_script.py`**: A closing script where NAO thanks the audience and says goodbye.

### Helper Modules
- **`animations.py`**: Contains the database of animations categorized by intent (e.g., neutral, question, negation) and functions to select the best animation based on text analysis.
- **`leds.py`**: Manages the robot's eye and ear LEDs to express various emotions (neutral, enjoyment, anger, disgust, sadness, fear, surprise).
- **`tts_client.py`**: Client for generating speech audio files using an external TTS server.
- **`music_player.py`**: Handles background music playback using `pygame`.

## Usage

### Prerequisites
- **Python libraries**: Install the required dependencies using pip:
    ```bash
    pip install -r requirements.txt
    ```
- **SIC Framework**: The `social-interaction-cloud` package is included in the requirements.
- **Network**: The computer must be on the same network as the NAO robot.
- **Redis Server**: The system requires a Redis server running before you can communicate with the robot. 
  Navigate to the `conf/redis` directory in the project root and run:
  ```bash
  .\redis-server.exe .\redis.conf
  ```
- **TTS Server**: The `tts_client.py` expects a TTS server running at `http://tts.twin-tails.org:80/tts`.


### Running the Demos

1.  **Main Performance**:
    ```bash
    python main.py
    ```
    Press `q` to stop the loop.

2.  **Snow White Story**:
    ```bash
    python snowwhite_demo.py
    ```

3.  **Opening/Closing Scripts**:
    ```bash
    python opening_script.py
    python end_script.py
    ```
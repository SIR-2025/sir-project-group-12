# NAO Performance Demos

This folder contains scripts and modules for running various interactive performances and demos with the NAO robot using the SIC framework.

## Contents

### Main Scripts

- **`snowwhite_interactive.py`**: The primary interactive application. It uses Google Speech-to-Text to listen to the user, Dialogflow CX to manage the conversation, and triggers theatrical performances (gestures + TTS) when the story intent is detected.
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
- **Redis Server**: The system requires a Redis server running locally.
  Navigate to the `conf/redis` directory in the project root and run:
  ```bash
  .\redis-server.exe .\redis.conf
  ```
- **Google STT Service**: Open a separate terminal and run:
  ```bash
  run-google-stt
  ```
- **TTS Server**: The `tts_client.py` expects a TTS server running at `http://localhost:8000/tts` (internet connection required).

### Running the Interactive App

**This is the main demo.**

```bash
python snowwhite_interactive.py
```

_Note: Make sure your `conf/google/google-key.json` is present and valid._

### Running Other Demos

1.  **Snow White Story (Non-Interactive)**:

    ```bash
    python snowwhite_demo.py
    ```

2.  **Opening/Closing Scripts**:
    ```bash
    python opening_script.py
    python end_script.py
    ```


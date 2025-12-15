# Socially Intelligent Robotics - Project Group 12

This project is for the Socially Intelligent Robotics course at the University of Groningen. It contains a collection of scripts and demonstrations for interacting with a NAO robot and using various cloud services for speech recognition, text-to-speech, and dialog management.

# NAO Performance Demos

This folder contains scripts and modules for running various interactive performances and demos with the NAO robot using the SIC framework.

## Contents

### Main Scripts

- **`nao_performance/snowwhite_interactive.py`**: The primary interactive application. It uses Google Speech-to-Text to listen to the user, Dialogflow CX to manage the conversation, and triggers theatrical performances (gestures + TTS) when the story intent is detected.
- **`nao_performance/snowwhite_demo.py`**: A storytelling demo ("Snow White") that is 'based' on the first scene of our performance. This is just to demonstrate how the performance could look like if every part of the performance is combined.
- **`nao_performance/opening_script.py`**: An introductory script where NAO introduces itself and the upcoming performance (Snow White).
- **`nao_performance/end_script.py`**: A closing script where NAO thanks the audience and says goodbye.

### Helper Modules

- **`nao_performance/animations.py`**: Contains the database of animations categorized by intent (e.g., neutral, question, negation) and functions to select the best animation based on text analysis.
- **`nao_performance/leds.py`**: Manages the robot's eye and ear LEDs to express various emotions (neutral, enjoyment, anger, disgust, sadness, fear, surprise).
- **`nao_performance/tts_client.py`**: Client for generating speech audio files using an external TTS server.
- **`nao_performance/music_player.py`**: Handles background music playback using `pygame`.

## Dialogflow Flows

The `flows` directory contains exported Dialogflow CX flows used by the interactive storytelling scripts. Each JSON file (e.g., `SIR_exported_flow_cycle_1.json` through `SIR_exported_flow_cycle_4.json`) represents a full flow version. Import these into Dialogflow CX when you need to recreate or update the conversation design used by `snowwhite_interactive.py` and related demos.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

**SIC Framework**: The `social-interaction-cloud` package is included in the requirements.
**Network**: The computer must be on the same network as the NAO robot.
**Redis Server**: The system requires a Redis server running locally.
Navigate to the `conf/redis` directory in the project root and run:

```bash
.\redis-server.exe .\redis.conf
```

- **Google STT Service**: Open a separate terminal and run:
  ```bash
  run-google-stt
  ```

1.  **Install uv:**

    If you don't have `uv` installed, you can install it with:

    ```bash
    pip install uv
    ```

2.  **Create a virtual environment:**

    It is recommended to use a virtual environment to manage the project's dependencies.

    ```bash
    uv venv
    ```

3.  **Activate the virtual environment:**

    On Linux and macOS:

    ```bash
    source .venv/bin/activate
    ```

    On Windows:

    ```bash
    .venv\Scripts\activate
    ```

4.  **Install dependencies:**

    Install the required packages using `uv`:

    ```bash
    uv pip install -r requirenments.txt
    ```

## Configuration

Before running any of the scripts, you will need to configure the following:

1.  **NAO Robot IP Address:**

    In the script you want to run, change the `nao_ip` variable to your NAO robot's IP address.

2.  **Dialogflow Configuration:**

    In the script you want to run, you will need to set the following variables:
    - `dialogflow_project_id`: Your Dialogflow project ID.
    - `dialogflow_agent_id`: Your Dialogflow agent ID.
    - `dialogflow_language_code`: The language code for your Dialogflow agent (e.g., "en-US").

3.  **Google API Key:**

    Move your Google API key JSON file to `conf/google/google-key.json`. In the script you want to run, make sure the `google_credentials_path` variable is set to this path.

## Kokoro TTS Server

The `server` directory contains a Text-to-Speech (TTS) server that uses the Kokoro TTS model. The `snowwhite_interactive.py` script uses this server to generate the audio for the storytelling performance.

The `server` directory contains the following scripts:

- `server.py`: The FastAPI server that runs the TTS model.
- `client.py`: A script that shows how to interact with the server.

Before running the `snowwhite_interactive.py` script, you need to start the TTS server.

You also need to configure the IP address of the machine running the server in the `nao_performance/tts_client.py` file. Change the `url` variable to the IP address of the machine running the `server.py` script.

## How to Run

1.  **Start the TTS Server:**

    Open a new terminal, activate the virtual environment, and run the following command:

    ```bash
    uv run server/server.py
    ```

    or if you are using python directly:

    ```bash
    python server/server.py
    ```

2.  **Run the Snow White Interactive Script:**

    Open another terminal, activate the virtual environment, and run the following command:

    ```bash
    uv run nao_performance/snowwhite_interactive.py
    ```

    or if you are using python directly:

    ```bash
    python nao_performance/snowwhite_interactive.py
    ```

To run a demo on the NAO robot, you will need to have the NAO's IP address and be on the same network.

## Authors

- Group 12

## License

This project is licensed under the MIT License.

---

**MIT License**

Copyright (c) 2025 Group 12

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

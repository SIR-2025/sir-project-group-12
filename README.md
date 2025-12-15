# Socially Intelligent Robotics - Project Group 12

This project is for the Socially Intelligent Robotics course at the University of Groningen. It contains a collection of scripts and demonstrations for interacting with a NAO robot and using various cloud services for speech recognition, text-to-speech, and dialog management.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

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

## How to Run

The `nao_performance` directory contains the performance code to demonstrate the project's functionality. You can run them directly from your terminal.

For example, to run the `snowwhite_interactive.py` script:

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

import requests
import os

# Simple HTTP TTS client wrapper for the local/external TTS server.
# Usage: call `synthesize_to_file(text, voice, speed, output_filename)`

DEFAULT_URL = os.getenv("TTS_SERVER_URL", "http://tts.twin-tails.org:80/tts")


def synthesize_to_file(text: str, voice: str = "af_bella", speed: float = 1.0, output_filename: str = "output.wav") -> bool:
    """Send text to TTS server and save response to `output_filename`.

    Returns True on success, False otherwise.
    """
    payload = {
        "text": text,
        "voice": voice,
        "speed": speed,
    }

    try:
        resp = requests.post(DEFAULT_URL, json=payload, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"TTS request failed: {e}")
        return False

    if resp.status_code != 200:
        print(f"TTS server returned status {resp.status_code}: {resp.text}")
        return False

    try:
        with open(output_filename, "wb") as f:
            f.write(resp.content)
    except Exception as e:
        print(f"Failed to write output file '{output_filename}': {e}")
        return False

    return True


if __name__ == "__main__":
    # Simple CLI test when run directly
    sample = "Generating Story... It is Snow White!"
    ok = synthesize_to_file(sample, voice="af_bella", speed=1.0, output_filename="output_test.wav")
    print("Success:" if ok else "Failed")

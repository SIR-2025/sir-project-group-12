import requests
import os

def generate_audio(text, output_filename, voice="af_bella", speed=1.0):
    """
    Generates audio from text using the TTS server and saves it to a file.

    Args:
        text (str): The text to convert to speech.
        output_filename (str): The path to save the generated WAV file.
        voice (str): The voice to use (default: "af_bella").
        speed (float): The speed of speech (default: 1.0).

    Returns:
        bool: True if successful, False otherwise.
    """
    # Change the IP address here to the IP address of the machine running the server.py script.
    url = "http://localhost:8000/tts"
    
    payload = {
        "text": text,
        "voice": voice,
        "speed": speed
    }

    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"Error: Server returned status code {response.status_code}")
            print("Details:", response.text)
            return False

    except requests.exceptions.ConnectionError:
        print("Failed to connect. Is server.py running?")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

import requests

# The URL where your server is running
url = "http://localhost:8000/tts"

# The text you want to convert
payload = {
    "text": "Let's generate a story... It is, - Snow White'!",
    "voice": "af_bella",  # Options: af_heart, af_bella, am_adam, etc.
    "speed": 1.0
}

print(f"Sending request to {url}...")

try:
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        # Save the binary content (audio) to a file
        output_filename = "output_1.wav"
        with open(output_filename, "wb") as f:
            f.write(response.content)
        print(f"Success! Audio saved to '{output_filename}'")
    else:
        print(f"Error: Server returned status code {response.status_code}")
        print("Details:", response.text)

except requests.exceptions.ConnectionError:
    print("Failed to connect. Is server.py running?")

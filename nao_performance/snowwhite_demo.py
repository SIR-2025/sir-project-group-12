import time
import sys
import os
import threading
import queue
import wave
import re

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoBasicAwarenessRequest,
    NaoListeningMovementRequest,
    NaoSetAutonomousLifeRequest,
    NaoWakeUpRequest,
    NaoRestRequest,
    NaoBlinkingRequest,
)
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.core.message_python2 import AudioRequest

try:
    from tts_client import generate_audio
    from animations import get_best_animation
    from music_player import MusicPlayer
    from leds import NaoLEDS
except ImportError:
    from .tts_client import generate_audio
    from .animations import get_best_animation
    from .music_player import MusicPlayer
    from .leds import NaoLEDS


class SnowWhiteDemo(SICApplication):
    """
    A specific storytelling demo that narrates the story of Snow White.
    It utilizes a producer-consumer pattern to generate TTS audio asynchronously
    while the consumer loop plays the audio synchronized with gestures and background music.
    """
    def __init__(self):
        super().__init__()
        self.nao_ip = "10.0.0.181"
        self.nao = None
        self.audio_queue = queue.Queue()
        self.music_player = MusicPlayer()

        # Parse the scene into smaller text chunks
        full_text = "Once upon a time, there lived a princess called Snow White. Snow White was very beautiful. Then there was the Evil Queen who also was very beautiful. Every day she looked into her Magic Mirror. She asked: 'Mirror, Mirror, on the wall, who is the [Word 1] of them all?' The Mirror replied: 'Not you. It is Snow White. She has skin as white as [Word 2], and she has [Word 3] as big as a [Word 4].' The Queen was furious. “Snow White!” she hissed. “It cannot be!”. Then the Queen told the huntsman to find Snow White and kill her in the forest."
        text_chunks = re.split(r'(?<=[.!?]) +', full_text)
        self.script = text_chunks
        
        # Music cues: {line_index: "path/to/music.wav"}
        self.music_cues = {
            0: "music/intro.wav",
        }
        self.setup()

    def setup(self):
        self.logger.info("Connecting to NAO at %s...", self.nao_ip)
        self.nao = Nao(ip=self.nao_ip)
        self.emotions = NaoLEDS(self.nao)

        self.logger.info("Waking up and enabling Autonomous Life...")
        self.nao.autonomous.request(NaoWakeUpRequest())
        self.nao.autonomous.request(NaoSetAutonomousLifeRequest("interactive"))

        # Enable awareness to track faces (audience) and sound
        self.logger.info("Enabling Basic Awareness (Face and Sound Tracking)...")
        self.nao.autonomous.request(
            NaoBasicAwarenessRequest(
                True,
                stimulus_detection=[
                    ("People", True),
                    ("Touch", False),
                    ("Sound", True),
                    ("Movement", True),
                ],
                engagement_mode="FullyEngaged", # Choose from Unengaged, FullyEngaged or SemiEngaged
                tracking_mode="BodyRotation",  # Choose from Head, BodyRotation, WholeBody or MoveContextually
            )
        )
        self.nao.autonomous.request(NaoListeningMovementRequest(True))
        
        self.emotions.enable_eyes()
        self.nao.autonomous.request(NaoBlinkingRequest(True))

    def producer(self):
        """Generates audio files in the background and puts them in the queue."""
        self.logger.info("Producer thread started.")
        for i, text in enumerate(self.script):
            voice = "bm_lewis"
            music = self.music_cues.get(i)
            
            output_file = f"snowwhite_{i}.wav"
            
            # Select best gesture based on intent and text
            gesture = get_best_animation("neutral", text)
            
            self.logger.info(f"Generating audio for line {i}: '{text[:20]}...' with gesture: {gesture}")
            if generate_audio(text, output_file, voice):
                self.audio_queue.put((output_file, gesture, text, music))
            else:
                self.logger.error(f"Failed to generate audio for line {i}")
                # Put None to signal failure/skip, or handle gracefully
                self.audio_queue.put(None)
        
        # Signal end of script
        self.audio_queue.put("DONE")
        self.logger.info("Producer thread finished.")

    def run(self):
        self.logger.info("Starting Snow White demo...")

        # Start the producer thread
        producer_thread = threading.Thread(target=self.producer)
        producer_thread.start()

        try:
            while True:
                # Get the next item from the queue (blocking)
                item = self.audio_queue.get()
                
                if item == "DONE":
                    break
                
                if item is None:
                    continue

                output_file, gesture, text, music = item
                
                # Change music if specified
                if music:
                    # Use absolute path or relative to script? Assuming relative to project root or script.
                    # Let's assume relative to project root for now, or handle in MusicPlayer
                    self.music_player.change_track(music)

                self.logger.info(f"Playing line: '{text[:20]}...'")

                # Define audio playback function
                def play_audio():
                    try:
                        with wave.open(output_file, "rb") as wavefile:
                            samplerate = wavefile.getframerate()
                            sound = wavefile.readframes(wavefile.getnframes())
                            message = AudioRequest(sample_rate=samplerate, waveform=sound)
                            self.nao.speaker.request(message)
                    except Exception as e:
                        self.logger.error(f"Error playing audio: {e}")

                # Start audio in a separate thread
                audio_thread = threading.Thread(target=play_audio)
                audio_thread.start()

                # Small delay to ensure audio starts before or with gesture
                time.sleep(0.2)

                # Start gesture if available
                if gesture:
                    self.nao.motion.request(NaoqiAnimationRequest(gesture))
                
                # Wait for audio to finish
                audio_thread.join()

                # Cleanup file
                try:
                    os.remove(output_file)
                except OSError:
                    pass

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user.")
        finally:
            self.cleanup()
            producer_thread.join()

    def cleanup(self):
        self.logger.info("Resting NAO...")
        if hasattr(self, 'music_player'):
            self.music_player.stop()
            
        if self.nao:
            try:
                # Disable awareness and listening movement first
                self.nao.autonomous.request(NaoBasicAwarenessRequest(False))
                self.nao.autonomous.request(NaoListeningMovementRequest(False))
                self.nao.autonomous.request(NaoBlinkingRequest(False))
                
                if self.emotions:
                    self.emotions.reset()

                # Then rest
                self.nao.autonomous.request(NaoRestRequest())
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    demo = SnowWhiteDemo()
    demo.run()

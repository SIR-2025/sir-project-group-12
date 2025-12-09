import random
import time
import threading
import sys
import os
import msvcrt

# Add project root to sys.path to allow importing 'emotion' package
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
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.core.message_python2 import AudioRequest
import wave

try:
    from animations import get_best_animation
    from leds import NaoLEDS
    from tts_client import generate_audio
except ImportError:
    from .animations import get_best_animation
    from .leds import NaoLEDS
    from .tts_client import generate_audio


class NaoPerformanceDemo(SICApplication):
    """
    A demo where NAO acts like it is performing in front of an audience.
    It uses Autonomous Life for basic awareness and idle movements,
    and periodically plays gestures with synchronized LED emotions and tts example sentences.
    """

    # Timing parameters for each intent (seconds)
    INTENT_PARAMS = {
        "neutral": {"min_wait": 0.0, "max_wait": 0.01},
        "enjoyment": {"min_wait": 1.0, "max_wait": 3.0},
        "surprise": {"min_wait": 0.5, "max_wait": 1.5},
        "angry": {"min_wait": 2.0, "max_wait": 4.0},
        "disgust": {"min_wait": 2.0, "max_wait": 4.0},
        "sadness": {"min_wait": 5.0, "max_wait": 10.0},
        "fear": {"min_wait": 1.0, "max_wait": 3.0},
    }

    # Sample sentences to simulate speech and drive gesture selection
    SAMPLE_SENTENCES = {
        "neutral": [
            "I think we should consider the following options.",
            "First, we need to analyze the data. Second, we make a plan.",
            "Is there anyone who can answer this question?",
            "No, I don't think that is the right approach.",
            "The object is located over there, near the window.",
            "I am feeling quite calm and ready to work.",
            "What do you think about this idea?",
            "We must never forget the importance of safety.",
            "You and I can work together on this.",
            "It happened a long time ago, in a galaxy far away."
        ],
        "enjoyment": [
            "Wow, this is absolutely amazing!",
            "I am so happy to see you all here!",
            "This is the best day ever!",
            "Hooray! We did it!",
            "I really enjoy spending time with you."
        ],
        "angry": [
            "I am not happy about this situation.",
            "This is unacceptable!",
            "No, I will not do that.",
            "Stop it right now!",
            "I am very frustrated."
        ],
        "sadness": [
            "I am feeling a bit down today.",
            "It is so sad that we have to say goodbye.",
            "I don't know what to do anymore.",
            "This is a very difficult time for me.",
            "I miss my friends."
        ]
    }

    def __init__(self):
        super().__init__()
        self.nao_ip = "10.0.0.181"
        self.nao = None
        self.emotions = None
        self.current_intent = "neutral"  # Default intent
        self.setup()

    def set_intent(self, intent: str):
        if intent in self.INTENT_PARAMS:
            self.current_intent = intent
            self.logger.info(f"Intent set to: {intent}")
            # Enable blinking only for neutral intent (or as requested)
            if self.nao:
                self.nao.autonomous.request(NaoBlinkingRequest(intent == "neutral"))
        else:
            self.logger.warning(f"Invalid intent: {intent}. Keeping current intent: {self.current_intent}")

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
                tracking_mode="Head",  # Choose from Head, BodyRotation, WholeBody or MoveContextually
            )
        )
        self.nao.autonomous.request(NaoListeningMovementRequest(True))
        
        self.emotions.enable_eyes()
        self.nao.autonomous.request(NaoBlinkingRequest(True))

    def run(self):
        # Configuration: Set the initial intent here for testing
        INITIAL_INTENT = "neutral" 
        self.set_intent(INITIAL_INTENT)

        self.logger.info(f"NAO is moving with intent '{self.current_intent}'... Press 'q' to stop.")
        try:
            while True:
                # Check for exit key
                if msvcrt.kbhit():
                    if msvcrt.getch().lower() == b'q':
                        self.logger.info("Quit key pressed.")
                        break

                # Determine wait time based on intent
                params = self.INTENT_PARAMS.get(self.current_intent, {"min_wait": 2.0, "max_wait": 5.0})
                wait_time = random.uniform(params["min_wait"], params["max_wait"])
                
                end_time = time.time() + wait_time
                
                interrupted = False
                while time.time() < end_time:
                    if msvcrt.kbhit():
                        if msvcrt.getch().lower() == b'q':
                            self.logger.info("Quit key pressed.")
                            interrupted = True
                            break
                    time.sleep(0.1)
                
                if interrupted:
                    break

                # Select a sentence based on intent
                # If intent doesn't have specific sentences, fallback to neutral or generic
                sentences = self.SAMPLE_SENTENCES.get(self.current_intent, self.SAMPLE_SENTENCES["neutral"])
                text_to_say = random.choice(sentences)

                # Select best gesture based on intent and text
                anim_path = get_best_animation(self.current_intent, text_to_say)
                
                # If no animation found (shouldn't happen with fallback), just express emotion
                if not anim_path:
                    self.logger.warning(f"No animations found for intent: {self.current_intent}")
                    self.emotions.express(self.current_intent)
                    time.sleep(1)
                    continue

                self.logger.info(f"Saying: '{text_to_say}' with gesture: {anim_path}")

                # Trigger LED emotion in a separate thread
                threading.Thread(target=self.emotions.express, args=(self.current_intent,), daemon=True).start()

                # Perform motion and speech in a separate thread               
                def speak():
                    # Generate audio file
                    output_file = "temp_speech.wav"
                    if generate_audio(text_to_say, output_file):
                        try:
                            # Read the wav file
                            with wave.open(output_file, "rb") as wavefile:
                                samplerate = wavefile.getframerate()
                                sound = wavefile.readframes(wavefile.getnframes())
                                message = AudioRequest(sample_rate=samplerate, waveform=sound)
                                self.nao.speaker.request(message)
                        except Exception as e:
                            self.logger.error(f"Error playing audio: {e}")
                            # Fallback to default TTS if audio playback fails
                            self.nao.tts.request(NaoqiTextToSpeechRequest(text_to_say))
                    else:
                        self.logger.error("Failed to generate audio, falling back to default TTS")
                        self.nao.tts.request(NaoqiTextToSpeechRequest(text_to_say))

                speech_thread = threading.Thread(target=speak)
                speech_thread.start()

                # Small delay to let speech start
                time.sleep(0.2)

                self.nao.motion.request(NaoqiAnimationRequest(anim_path))
                
                # Wait for speech to finish if it's longer than gesture
                speech_thread.join()

        except Exception as exc:
            self.logger.error("Run loop error: %s", exc)
        finally:
            self.cleanup()
            self.shutdown()

    def cleanup(self):
        self.logger.info("Resting NAO...")
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
    demo = NaoPerformanceDemo()
    demo.run()

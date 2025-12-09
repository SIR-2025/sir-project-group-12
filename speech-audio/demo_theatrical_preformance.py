# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoWakeUpRequest, NaoRestRequest, NaoBasicAwarenessRequest, NaoBlinkingRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.core.message_python2 import AudioRequest

# Import the service(s) we will be using
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DialogflowCX,
    DialogflowCXConf,
    DetectIntentRequest,
)

# Import libraries necessary for the demo
from time import sleep
from pathlib import Path
import wave
import os
import json
from os.path import abspath, join
import numpy as np
from dotenv import load_dotenv
import threading
import random
import time

load_dotenv()

# Local HTTP TTS client
try:
    import client as tts_client
except Exception as e:
    print("Missing TTS client. Ensure 'speech-audio/client.py' exists and dependencies (requests) are installed.")
    raise e


class NaoSnowWhiteInteractive(SICApplication):
    """
    NAO Snow White Interactive Demo.
    
    Combines Dialogflow CX (for logic/interaction) with OpenAI TTS (for theatrical performance).
    
    Behavior:
    1. Listens to user input via Dialogflow.
    2. Uses standard NAO TTS for simple prompts ("Name a fruit").
    3. When a 'robot_command' payload is received, it performs the theatrical routine
       (OpenAI Onyx voice, colored LEDs, and dramatic gestures).
    """
    
    def __init__(self):
        super(NaoSnowWhiteInteractive, self).__init__()
        
        # --- Configuration ---
        self.nao_ip = "10.0.0.181" 
        self.dialogflow_keyfile_path = abspath(join("conf", "google", "google-key.json")) # Ensure this path is correct
        
        # Dialogflow Agent Details (From your provided logs)
        self.agent_id = "5079e43a-fec2-441d-bf10-f23f292fbf15"
        self.location_id = "europe-west4"
        self.session_id = str(np.random.randint(10000))
        
        # Audio
        self.speech_file_path = Path(__file__).parent / "temp_theatrical_speech.wav"
        
        # Components
        self.nao = None
        self.dialogflow_cx = None
        
        self.set_log_level(sic_logging.INFO)
        self.setup()
    
    def setup(self):
        """Initialize NAO robot, Dialogflow CX, and OpenAI."""
        self.logger.info("Initializing NAO Snow White Interactive...")
        
        # 1. Initialize NAO
        self.nao = Nao(ip=self.nao_ip)
        nao_mic = self.nao.mic
        
        # 2. Initialize Dialogflow CX
        self.logger.info("Loading Dialogflow configuration...")
        try:
            with open(self.dialogflow_keyfile_path) as f:
                keyfile_json = json.load(f)
            
            dialogflow_conf = DialogflowCXConf(
                keyfile_json=keyfile_json,
                agent_id=self.agent_id,
                location=self.location_id,
                sample_rate_hertz=16000,
                language="en"
            )
            
            self.dialogflow_cx = DialogflowCX(conf=dialogflow_conf, input_source=nao_mic)
            self.logger.info("Dialogflow CX initialized.")
            # Start autonomous movement thread so NAO doesn't remain perfectly still
            try:
                self._autonomous_thread = threading.Thread(
                    target=self._autonomous_movement_loop,
                    name="autonomous_movement",
                    daemon=True,
                )
                self._autonomous_thread.start()
                self.logger.info("Autonomous movement thread started.")
            except Exception:
                self.logger.warning("Failed to start autonomous movement thread.")
            
        except FileNotFoundError:
            self.logger.error(f"Google Keyfile not found at: {self.dialogflow_keyfile_path}")
            raise

    def generate_story_speech(self, text, mood="neutral"):
        """Generates theatrical story speech using the HTTP TTS client and saves to file.

        This function is intended ONLY for story narration. Standard prompts/questions
        should continue to use the NAO onboard TTS via `self.nao.tts.request(...)`.
        """
        try:
            self.logger.info(f"Generating theatrical story speech via HTTP TTS (Mood: {mood})...")

            # Map mood to a simple voice choice and speed adjustments
            voice = "af_bella"
            speed = 1.0
            if mood == "scary":
                voice = "bf_isabella"
                speed = 0.65
            elif mood == "happy":
                voice = "af_heart"
                speed = 1.05

            success = tts_client.synthesize_to_file(
                text=text,
                voice=voice,
                speed=speed,
                output_filename=str(self.speech_file_path),
            )

            if not success:
                self.logger.error("HTTP TTS client reported failure.")

            return success
        except Exception as e:
            self.logger.error(f"TTS client failed: {e}")
            return False

    def play_wav_file(self):
        """Plays the generated WAV file on NAO."""
        if not self.speech_file_path.exists():
            return
            
        try:
            with wave.open(str(self.speech_file_path), "rb") as wf:
                samplerate = wf.getframerate()
                sound = wf.readframes(wf.getnframes())
            
            self.nao.speaker.request(AudioRequest(sample_rate=samplerate, waveform=sound))
        except Exception as e:
            self.logger.error(f"Playback failed: {e}")

    def execute_theatrical_command(self, cmd):
        """
        Parses the JSON payload from Dialogflow and executes the performance.
        Payload format: {"led": "color", "motion": "tag", "text": "story..."}
        """
        self.logger.info("--- EXECUTING THEATRICAL PERFORMANCE ---")
        
        # 1. Set LED Color
        color_map = {
            "red": (1.0, 0.0, 0.0),
            "green": (0.0, 1.0, 0.0),
            "white": (1.0, 1.0, 1.0)
        }
        # target_color = color_map.get(cmd.get("led"), (1.0, 1.0, 1.0))
        # self.nao.leds.request(NaoFadeRGBRequest("FaceLeds", *target_color, 0.2))
        
        # 2. Trigger Gesture (Non-blocking so it starts while speaking)
        motion_tag = cmd.get("motion", "neutral")
        # if motion_tag == "scary":
        #     self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/No_9"), block=False)
        # elif motion_tag == "happy":
        #     self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/BowShort_1"), block=False)
        
        # 3. Generate & Play Theatrical Speech
        story_text = cmd.get("text", "")
        if story_text:
            # Ensure robot is awake and has basic awareness/blinking enabled for natural performance
            try:
                self.nao.autonomous.request(NaoWakeUpRequest())
                self.nao.autonomous.request(NaoBasicAwarenessRequest(True))
                self.nao.autonomous.request(NaoBlinkingRequest(True))
            except Exception:
                self.logger.debug("Failed to send autonomous wake/awareness/blinking requests before exec command story")

            success = self.generate_story_speech(story_text, mood=motion_tag)
            if success:
                self.play_wav_file()
            else:
                # Fallback to standard TTS if OpenAI fails
                self.nao.tts.request(NaoqiTextToSpeechRequest(story_text))
        
        # 4. Reset LEDs
        sleep(1.0)
        self.nao.leds.request(NaoFadeRGBRequest("FaceLeds", 1.0, 1.0, 1.0, 1.0))

    def run(self):
        """Main interaction loop."""
        try:
            self.nao.autonomous.request(NaoWakeUpRequest())
            
            # --- MANUAL INTRO (ROBOT SPEAKS FIRST) ---
            # The robot sets the stage and asks Question 1 manually.
            intro_text = (
                # "Hello all! I have accessed File 001. "
                # "This file contains a story about mirrors, poison, and sleeping. "
                # "I need you to provide new variables to make the story work again. "
                # "Please wait for the beep before speaking. "
                "Let us begin. Name an adjective a Queen would want to be."
            )
            self.logger.info(f"Speaking Manual Intro: {intro_text}")
            self.nao.tts.request(NaoqiTextToSpeechRequest(intro_text))

            # --- MAIN LOOP ---
            while not self.shutdown_event.is_set():
                self.logger.info("Listening for user input...")
                
                # 1. Get Response from Dialogflow
                reply = self.dialogflow_cx.request(DetectIntentRequest(self.session_id))
                
                if not reply:
                    continue

                # 2. Process The Response
                if reply.fulfillment_message:
                    text_received = reply.fulfillment_message
                    self.logger.info(f"Dialogflow Response: {text_received}")

                    # --- CHECK: IS THIS THE STORY? ---
                    if "Generating Story" in text_received:
                        self.logger.info("Story Trigger Detected! Switching to Theatrical Mode.")

                        # A. Set Theatrical LEDs (Red)
                        self.nao.leds.request(NaoFadeRGBRequest("FaceLeds", 1.0, 1.0, 1.0, 0.2))
                        
                        # B. Wake robot and enable awareness/blinking so performance looks alive
                        try:
                            self.nao.autonomous.request(NaoWakeUpRequest())
                            self.nao.autonomous.request(NaoBasicAwarenessRequest(True))
                            self.nao.autonomous.request(NaoBlinkingRequest(True))
                        except Exception:
                            self.logger.debug("Failed to send autonomous wake/awareness/blinking requests")

                        # C. Start Motion (Scary/Dramatic)
                        # Non-blocking so it moves while speaking
                        # self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/No_9"), block=False)

                        # D. Send text to HTTP TTS for theatrical narration
                        # This function generates the WAV and plays it
                        # Note: Ensure `generate_story_speech` is defined in your class (see below)
                        success = self.generate_story_speech(text_received, mood="scary")
                        
                        if success:
                            self.play_wav_file()
                        else:
                            # Fallback to Nao TTS if internet/OpenAI fails
                            self.nao.tts.request(NaoqiTextToSpeechRequest(text_received))

                        # D. Stop the loop after story
                        self.logger.info("Story finished. Ending session.")
                        break

                    # --- OTHERWISE: STANDARD QUESTION ---
                    else:
                        # Use standard Nao TTS for questions ("Name a fruit", etc.)
                        self.nao.tts.request(NaoqiTextToSpeechRequest(text_received))
                
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Runtime error: {e}")
        finally:
            self.cleanup_files()
            self.nao.autonomous.request(NaoRestRequest())
            self.shutdown()

    def cleanup_files(self):
        if self.speech_file_path.exists():
            try:
                os.remove(self.speech_file_path)
            except:
                pass

if __name__ == "__main__":
    app = NaoSnowWhiteInteractive()
    app.run()
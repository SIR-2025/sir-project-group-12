import time
import sys
import os
import threading
import queue
import wave
import re
import json
import numpy as np
from pathlib import Path
from os.path import abspath, join
from dotenv import load_dotenv

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
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.core import sic_logging

# Dialogflow
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DialogflowCX,
    DialogflowCXConf,
    DetectIntentRequest,
)

# Local imports
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

load_dotenv()

class NaoStoryInteractive(SICApplication):
    """
    Combined Application:
    1. Interactive Mode: Uses Dialogflow CX to talk to the user (filling slots).
    2. Performance Mode: Once the story is generated, switches to theatrical playback
       (custom TTS, music, gestures) using the producer-consumer pattern.
    """
    
    def __init__(self):
        super(NaoStoryInteractive, self).__init__()
        
        # --- Configuration ---
        self.nao_ip = "10.0.0.181"
        # Adjust path to where the keyfile is actually located relative to this script
        self.dialogflow_keyfile_path = abspath(join("conf", "google", "google-key.json"))
        
        self.agent_id = "5079e43a-fec2-441d-bf10-f23f292fbf15"
        self.location_id = "europe-west4"
        self.session_id = str(np.random.randint(10000))
        
        # Components
        self.nao = None
        self.dialogflow_cx = None
        self.emotions = None
        self.music_player = MusicPlayer()
        
        # Performance/Story State
        self.audio_queue = queue.Queue()
        self.story_script = [] # List of strings/sentences
        self.music_cues = {
            0: "music/intro.wav", 
        }

        self.set_log_level(sic_logging.INFO)
        self.setup()

    def setup(self):
        """Initialize NAO, Dialogflow, and modules."""
        self.logger.info("Initializing NaoStoryInteractive...")
        
        # 1. Initialize NAO
        self.nao = Nao(ip=self.nao_ip)
        self.emotions = NaoLEDS(self.nao)
        
        # 2. Autonomous Life & Awareness (Standard Setup)
        self.logger.info("Waking up and enabling Autonomous Life...")
        self.nao.autonomous.request(NaoWakeUpRequest())
        # "interactive" mode helps keep the robot alive but we control attention manually mostly
        self.nao.autonomous.request(NaoSetAutonomousLifeRequest("interactive")) 
        
        self.nao.autonomous.request(
             NaoBasicAwarenessRequest(
                True,
                stimulus_detection=[
                    ("People", True),
                    ("Touch", False),
                    ("Sound", True),
                    ("Movement", True),
                ],
                engagement_mode="FullyEngaged",
                tracking_mode="BodyRotation",
            )
        )
        self.nao.autonomous.request(NaoListeningMovementRequest(True))
        self.nao.autonomous.request(NaoBlinkingRequest(True))
        self.emotions.enable_eyes()
        
        # 3. Initialize Dialogflow CX
        self.logger.info("Loading Dialogflow configuration...")
        try:
            # We need to find the keyfile. Assuming the script is run from project root or 'nao_performance' needs adjustment
            # If running from nao_performance/, conf is one level up probably?
            # Let's check if the file exists, if not try ../conf
            if not os.path.exists(self.dialogflow_keyfile_path):
                alt_path = abspath(join("..", "conf", "google", "google-key.json"))
                if os.path.exists(alt_path):
                    self.dialogflow_keyfile_path = alt_path
            
            with open(self.dialogflow_keyfile_path) as f:
                keyfile_json = json.load(f)
            
            dialogflow_conf = DialogflowCXConf(
                keyfile_json=keyfile_json,
                agent_id=self.agent_id,
                location=self.location_id,
                sample_rate_hertz=16000,
                language="en"
            )
            
            self.dialogflow_cx = DialogflowCX(conf=dialogflow_conf, input_source=self.nao.mic)
            self.logger.info("Dialogflow CX initialized.")
            
        except FileNotFoundError:
            self.logger.error(f"Google Keyfile not found at: {self.dialogflow_keyfile_path}")
            raise

    # ---------------------------------------------------------
    # PART A: THEATRICAL PERFORMANCE LOGIC (Producer/Consumer)
    # ---------------------------------------------------------

    def producer_story(self, full_text):
        """
        Takes the full story text, breaks it down, and generates audio/gestures.
        Runs in a background thread.
        """
        self.logger.info("Starting Story Producer...")
        
        # 1. Split text into chunks
        # Basic split by sentence terminators
        chunks = re.split(r'(?<=[.!?:]) +', full_text)
        # Filter empty chunks
        chunks = [c.strip() for c in chunks if c.strip()]
        
        for i, text in enumerate(chunks):
            # Determine voice/mood based on simple heuristics or passed params
            # For now, we stick to a default story voice or check keywords
            voice = "bm_lewis"
            
            # Simple keyword check for mood (optional extension)
            # if "Queen" in text: voice = "bf_isabella"
            
            music = self.music_cues.get(i)
            output_file = f"temp_story_{i}.wav"
            
            # Get Gesture
            # We pass "neutral" as intent for broad matching, or infer via NLP if we had it
            gesture = get_best_animation("neutral", text)
            
            self.logger.info(f"Preparing line {i}: '{text[:15]}...' | Gesture: {gesture}")
            
            success = generate_audio(text, output_file, voice)
            if success:
                self.audio_queue.put((output_file, gesture, text, music))
            else:
                self.logger.error(f"Failed to generate TTS for line {i}")
                # We put None so the consumer knows to skip or handle it
                # Or we could just use NAO TTS as fallback in consumer?
                # For now let's just skip to avoid breaking the loop
                pass

        self.audio_queue.put("DONE")
        self.logger.info("Story Producer finished.")

    def run_theatrical_performance(self):
        """
        Consumer loop: Plays the queued audio/motion elements.
        Blocks until the story is finished.
        """
        self.logger.info("Starting Theatrical Performance Phase...")
        
        while True:
            # Check shutdown
            if self.shutdown_event.is_set():
                break

            item = self.audio_queue.get()
            
            if item == "DONE":
                break
            
            output_file, gesture, text, music = item
            
            # 1. Music
            if music:
                self.music_player.change_track(music)
            
            self.logger.info(f"Performing: '{text[:20]}...'")
            
            # 2. Audio Playback (Threaded)
            def play_audio():
                try:
                    with wave.open(output_file, "rb") as wf:
                        samplerate = wf.getframerate()
                        sound = wf.readframes(wf.getnframes())
                        self.nao.speaker.request(AudioRequest(sample_rate=samplerate, waveform=sound))
                except Exception as e:
                    self.logger.error(f"Playback error: {e}")

            # Start audio
            audio_thread = threading.Thread(target=play_audio)
            audio_thread.start()
            
            # 3. Gesture
            # Small delay to sync with speech start
            time.sleep(0.2)
            if gesture:
                self.nao.motion.request(NaoqiAnimationRequest(gesture))
            
            # Wait for audio
            audio_thread.join()
            
            # Cleanup
            try:
                os.remove(output_file)
            except:
                pass
            
            # Small pause between sentences
            time.sleep(0.5)

        self.logger.info("Theatrical Performance Complete.")

    # ---------------------------------------------------------
    # PART B: MAIN INTERACTION LOOP
    # ---------------------------------------------------------

    def run(self):
        """Main Loop: Dialogflow Listener -> Performance Trigger"""
        try:
            # Intro
            intro_text = "Hello! I am ready to tell a story. Please help me fill in the blanks."
            self.nao.tts.request(NaoqiTextToSpeechRequest(intro_text))
            
            while not self.shutdown_event.is_set():
                self.logger.info("Listening for user input (Dialogflow)...")
                
                # 1. Listen & Detect Intent
                reply = self.dialogflow_cx.request(DetectIntentRequest(self.session_id))
                
                if not reply or not reply.fulfillment_message:
                    continue

                text_received = reply.fulfillment_message
                self.logger.info(f"Dialogflow said: {text_received}")
                
                # 2. Check for Story Trigger
                # Depending on how the Agent is set up, it might send a specific flag or just the story.
                # Heuristic: If the text is very long (> 100 chars) OR contains specific keywords.
                # For now, let's look for known story markers or length.
                is_story = len(text_received) > 150 or "Once upon a time" in text_received
                
                if is_story:
                    self.logger.info("Story detected! Switching to performance mode.")
                    
                    # A. Start Producer in Background with the full text
                    producer_thread = threading.Thread(target=self.producer_story, args=(text_received,))
                    producer_thread.start()
                    
                    # B. Run Consumer (Blocking)
                    self.run_theatrical_performance()
                    
                    # C. Wait for producer to fully exit (it should be done if consumer got DONE)
                    producer_thread.join()
                    
                    # End interaction after story? Or loop back?
                    self.logger.info("Story finished. Resetting session.")
                    # break # Uncomment to exit after one story
                    
                else:
                    # Standard conversational response
                    # Use NAO TTS for quick interaction
                    self.nao.tts.request(NaoqiTextToSpeechRequest(text_received))
                    
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Runtime Exception: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        self.logger.info("Cleaning up...")
        if hasattr(self, 'music_player'):
            self.music_player.stop()
        
        if self.nao:
            self.nao.autonomous.request(NaoBasicAwarenessRequest(False))
            self.nao.autonomous.request(NaoListeningMovementRequest(False))
            self.nao.autonomous.request(NaoBlinkingRequest(False))
            self.nao.autonomous.request(NaoRestRequest())

if __name__ == "__main__":
    app = NaoStoryInteractive()
    app.run()

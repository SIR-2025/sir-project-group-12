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

class NaoStoryTeller(SICApplication):
    """
    Linear Storytelling Application.
    Structure: Intro -> Chapter 1 -> Chapter 2 -> Chapter 3 -> Chapter 4 -> Outro.
    Each Chapter:
      1. Interaction (Dialogflow): Robot asks questions, User answers, until Story Segment is returned.
      2. Performance (Producer/Consumer): Robot acts out the story segment with custom TTS, Gestures, Music.
    """
    
    def __init__(self):
        super(NaoStoryTeller, self).__init__()
        
        # --- Configuration ---
        self.nao_ip = "10.0.0.181"
        self.dialogflow_keyfile_path = abspath(join("conf", "google", "google-key.json"))
        
        self.agent_id = "5079e43a-fec2-441d-bf10-f23f292fbf15"
        self.location_id = "europe-west4"
        self.session_id = str(np.random.randint(10000))
        
        # Components
        self.nao = None
        self.dialogflow_cx = None
        self.emotions = None
        self.music_player = MusicPlayer()
        
        # Performance State
        self.audio_queue = queue.Queue()
        
        # Music map per chapter (0=Intro, 1=Chapter1, ..., 5=Outro)
        self.music_cues = {
            1: "music/chapter1.wav",
            2: "music/chapter2.wav",
            3: "music/chapter3.wav",
            4: "music/chapter4.wav",
        }

        self.set_log_level(sic_logging.INFO)
        self.setup()

    def setup(self):
        """Initialize NAO, Dialogflow, and modules."""
        self.logger.info("Initializing NaoStoryTeller...")
        
        # 1. Initialize NAO
        self.nao = Nao(ip=self.nao_ip)
        self.emotions = NaoLEDS(self.nao)
        
        # 2. Autonomous Life & Awareness
        self.logger.info("Setting up Autonomous Life...")
        self.nao.autonomous.request(NaoWakeUpRequest())
        self.nao.autonomous.request(NaoSetAutonomousLifeRequest("interactive"))
        self.nao.autonomous.request(
             NaoBasicAwarenessRequest(
                True,
                stimulus_detection=[("People", True), ("Touch", False), ("Sound", True), ("Movement", True)],
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
            if not os.path.exists(self.dialogflow_keyfile_path):
                # Fallback check
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
    # PART A: THEATRICAL PERFORMANCE (The "Consumer")
    # ---------------------------------------------------------

    def producer_story(self, full_text):
        """
        Background thread: Splits text, generates TTS, queues actions.
        """
        self.logger.info("Producer: Generating audio/gestures...")
        
        # Split text into sentences
        chunks = re.split(r'(?<=[.!?:]) +', full_text)
        chunks = [c.strip() for c in chunks if c.strip()]
        
        for i, text in enumerate(chunks):
            # Decide Voice
            voice = "bm_lewis" # Default narrator
            
            output_file = f"temp_chap_{i}.wav"
            
            # Decide Gesture
            gesture = get_best_animation("neutral", text)
            
            self.logger.info(f"Generating Line {i}: {text[:20]}...")
            success = generate_audio(text, output_file, voice)
            
            if success:
                # Add to queue: (AudioPath, GestureName, DebugText)
                self.audio_queue.put((output_file, gesture, text))
            else:
                self.logger.error(f"TTS failed for line {i}")

        self.audio_queue.put("DONE")
        self.logger.info("Producer: Finished.")

    def perform_story_segment(self, chapter_num=0):
        """
        Consumes the queue and acts out the scene.
        """
        self.logger.info(f"Starting Performance for Chapter {chapter_num}...")
        
        # 1. Start Background Music (if available)
        music_file = self.music_cues.get(chapter_num)
        if music_file:
            self.music_player.change_track(music_file)
        
        # 2. Consumption Loop
        while True:
            item = self.audio_queue.get()
            
            if item == "DONE":
                break
            
            output_file, gesture, text = item
            
            self.logger.info(f"Performing: {text[:30]}...")
            
            # Setup Audio Thread
            def play_audio():
                try:
                    with wave.open(output_file, "rb") as wf:
                        samplerate = wf.getframerate()
                        sound = wf.readframes(wf.getnframes())
                        self.nao.speaker.request(AudioRequest(sample_rate=samplerate, waveform=sound))
                except Exception as e:
                    self.logger.error(f"Playback error: {e}")

            t_audio = threading.Thread(target=play_audio)
            t_audio.start()
            
            # Sync Gesture
            time.sleep(0.2)
            if gesture:
                self.nao.motion.request(NaoqiAnimationRequest(gesture))
            
            t_audio.join()
            
            # Cleanup
            try:
                os.remove(output_file)
            except:
                pass
                
            time.sleep(0.5) # Natural pause between sentences

        self.logger.info("Performance Segment Complete.")

    # ---------------------------------------------------------
    # PART B: INTERACTION (The "Collector")
    # ---------------------------------------------------------

    def collect_story_segment_from_dialogflow(self):
        """
        Loops interaction until a story segment is returned.
        Returns: The full story text string.
        """
        self.logger.info("Waiting for Story Segment from Dialogflow...")
        
        while not self.shutdown_event.is_set():
            # 1. Listen
            reply = self.dialogflow_cx.request(DetectIntentRequest(self.session_id))
            
            if not reply or not reply.fulfillment_message:
                continue

            text = reply.fulfillment_message
            self.logger.info(f"Received: {text}")
            
            # 2. Check Termination Condition
            # Heuristic: Story segments are usually long (> 100 chars) OR explicit trigger
            # Adjust this logic based on your Agent's actual output!
            is_story = len(text) > 150 or "Once upon a time" in text or "Chapter" in text
            
            if is_story:
                self.logger.info("Story Segment Detected.")
                return text
            else:
                # 3. Not story yet -> Speak prompt and continue loop
                self.nao.tts.request(NaoqiTextToSpeechRequest(text))
        
        return ""

    # ---------------------------------------------------------
    # PART C: SEQUENTIAL LOGIC
    # ---------------------------------------------------------

    def play_chapter(self, chapter_num):
        """
        Executes one full chapter cycle:
        1. Context Prompt (Optional/Hardcoded here or handled by logic)
        2. Robot prompts are handled by the Dialogflow conversation flow itself.
        3. Collect inputs -> Get Story
        4. Perform Story
        """
        self.logger.info(f"=== STARTING CHAPTER {chapter_num} ===")
        
        # 1. Interaction Phase
        story_text = self.collect_story_segment_from_dialogflow()
        
        if not story_text:
            self.logger.warning("No story text received (Shutdown?).")
            return

        # 2. Preparation Phase (Producer)
        p_thread = threading.Thread(target=self.producer_story, args=(story_text,))
        p_thread.start()
        
        # 3. Performance Phase (Consumer)
        self.perform_story_segment(chapter_num)
        
        # 4. Wait for producer cleanup
        p_thread.join()

    def run(self):
        """
        Main Execution Flow
        """
        try:
            # OPTIONAL: Intro
            self.nao.tts.request(NaoqiTextToSpeechRequest("Hello! Let's tell a story together. Say 'Start' to begin."))
            
            # Chapter 1
            self.play_chapter(1)
            
            # Chapter 2
            self.play_chapter(2)
            
            # Chapter 3
            self.play_chapter(3)
            
            # Chapter 4 (Ending)
            self.play_chapter(4)
            
            # Outro
            self.music_player.stop() # Fade out
            self.nao.tts.request(NaoqiTextToSpeechRequest("And that is the end. Thank you!"))
            
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
    app = NaoStoryTeller()
    app.run()

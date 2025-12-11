"""
Interactive Snow White Performance with NAO and Dialogflow CX.

Overview:
    This application acts as a bridge between the user, the Dialogflow CX conversational agent,
    and the NAO robot (via SIC framework). It enables a natural conversation loop that can
    seamlessly transition into a theatrical storytelling performance involving:
    - Custom Text-to-Speech (via tts_client/OpenAI/etc)
    - Gestures (via animations.py)
    - Emotional LED feedback (via leds.py)

Prerequisites:
    1. SIC Framework infrastucture running:
       - Redis Server (`redis-server`)
       - Google STT Service (`run-google-stt`)
    2. Network:
       - Computer must be on the same network as the NAO.
    3. Configuration:
       - `conf/google/google-key.json` must exist.
       - Update `self.nao_ip` in `__init__` to match your robot.

Usage:
    python snowwhite_interactive.py
"""

import time
import sys
import os
import threading
import queue
import wave
import re
import json
import uuid

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

# Add request_dialogflow to sys.path to import the client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../request_dialogflow")))

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
from sic_framework.services.google_stt.google_stt import (
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
    GetStatementRequest,
)

# Import the existing Dialogflow client from the sibling directory
try:
    from dialogflow_cx_direct_request import DialogflowCXDirectClient
except ImportError:
    print("Error: Could not import dialogflow_cx_direct_request. Make sure the request_dialogflow directory is in sys.path.")
    sys.exit(1)

# Local imports for performance assets
try:
    from tts_client import generate_audio
    from animations import get_best_animation
    from leds import NaoLEDS
except ImportError:
    from .tts_client import generate_audio
    from .animations import get_best_animation
    from .leds import NaoLEDS
    from .leds import NaoLEDS


class SnowWhiteInteractive(SICApplication):
    """
    Interactive Snow White Application.
    Uses Dialogflow CX to control the conversation and triggers
    the Snow White storytelling performance based on robot_command payloads.
    """

    OPENING_SCRIPT = [
        {
            "text": "\\style=neutral\\ Hello \\pau=200\\ my name is \\emph=1\\ Nao \\eos=1\\",
            "gesture": "animations/Stand/Gestures/Hey_5"  # Wave
        },
        {
            "text": "\\style=neutral\\ Today I will be telling a well-known fairy-tale story; \\pau=400\\ \\emph=1\\ Snowwhite \\eos=1\\",
            "gesture": "animations/Stand/Gestures/Me_7"  # Automic/Resting
        },
        {
            "text": "\\style=neutral\\ We all know this childhood story, \\bound=W\\ but today we will tell it with a \\pau=200\\ \\emph=1\\ twist. \\eos=1\\",
            "gesture": "animations/Stand/Gestures/YouKnowWhat_5"  # Automic/Resting
        },
        {
            "text": "\\style=didactic\\ You guys will be helping me. \\eos=1\\",
            "gesture": "animations/Stand/Gestures/You_3"  # Pointing
        },
        {
            "text": "\\style=didactic\\ You will do so by giving me words to fill in the story. \\eos=1\\",
            "gesture": "animations/Stand/Gestures/Joy_1"  # Explaining
        },
        {
            "text": "\\style=neutral\\ I will ask certain question for \\emph=1\\ specific words \\eos=1\\",
            "gesture": "animations/Stand/Gestures/Me_2"  # Pointing to self
        },
        {
            "text": "\\style=neutral\\ and my \\emph=1\\ assistants \\bound=W\\ will come to you guys to say the answer. \\eos=1\\",
            "gesture": "animations/Stand/Gestures/Thinking_2"  # Pointing to us/audience
        },
        {
            "text": "\\style=neutral\\ \\vct=95\\ I don't want to be the boring one, \\bound=S\\ but please keep the words \\emph=1\\ family-friendly, \\bound=W\\ as I am not allowed to use offensive words. \\eos=1\\",
            "gesture": "animations/Stand/Gestures/Please_3"  # Excused stance / begging
        },
        {
            "text": "\\style=neutral\\ \\vct=110\\ Now that everything is clear, \\pau=500\\ Lets begin: \\eos=1\\",
            "gesture": "animations/Stand/Gestures/Enthusiastic_3"  # Begin gesture
        }
    ]

    CLOSING_SCRIPT = [
        {
            "text": "\\style=neutral\\ Well, that was it. \\pau=300\\ I thank you for listening \\bound=S\\ and I thank my assistants for helping. \\eos=1\\",
            "gesture": "animations/Stand/Gestures/You_3"
        },
        {
            "text": "\\style=neutral\\ I wish you guys a nice day further. \\eos=1\\",
            "gesture": "animations/Stand/Gestures/You_4"
        },
        {
            "text": "\\style=neutral\\ \\vct=105\\ Oh! \\pau=200\\ I almost forgot. \\emph=1\\ Merry Christmas in advance! \\eos=1\\",
            "gesture": "animations/Stand/Gestures/Me_2",
            "pre_delay": 1.0
        },
        {
            "text": "\\style=neutral\\ And... \\pau=300\\ have a \\emph=1\\ fantastic New Year as well! \\eos=1\\",
            "gesture": "animations/Stand/Emotions/Positive/Laugh_2",
            "pre_delay": 2.0
        },
        {
            "text": "\\style=neutral\\ Actually, \\pau=200\\ you know what? \\emph=1\\ Happy Easter too! \\eos=1\\",
            "gesture": "animations/Stand/Emotions/Positive/Laugh_2",
            "pre_delay": 2.0
        },
        {
            "text": "\\style=neutral\\ Oke, \\pau=400\\ that is \\emph=1\\ really it. \\eos=1\\ Bye.",
            "gesture": "animations/Stand/Gestures/Hey_6",
            "pre_delay": 2.0
        }
    ]
    
    def __init__(self):
        super(SnowWhiteInteractive, self).__init__()
        
        # ========== CONFIGURATION ==========
        self.nao_ip = "10.0.0.181"
        # Path to conf/google/google-key.json relative to this script
        self.dialogflow_keyfile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../conf/google/google-key.json"))
        
        # Update these with your specific Agent details if they differ
        self.agent_id = "5079e43a-fec2-441d-bf10-f23f292fbf15"
        self.location = "europe-west4"
        # Define the sequence of flows to execute
        self.flows = [
            "c5eacb8c-2410-47b0-a51a-02c96c998c08", # Cycle 1
            "35b11713-c8ba-4c88-968a-1acbd74a43a8", # Cycle 2
            "511ba425-a19b-48fc-83ae-31b6cd3f7fdb", # Cycle 3
            "d0fb63a8-bc82-4440-a7b0-2360c2a16723", # Cycle 4
        ]
        
        self.session_id = str(uuid.uuid4())
        
        # Components
        self.nao = None
        self.dialogflow_client = None
        self.speech_to_text = None
        self.emotions = None
        
        # Performance/Audio Queue (Producer-Consumer)
        self.audio_queue = queue.Queue()
        self.current_proc_thread = None
        
 

        self.set_log_level(sic_logging.INFO)
        self.setup()
    
    def setup(self):
        """Initialize NAO, STT, and Dialogflow."""
        self.logger.info("Initializing SnowWhiteInteractive...")
        
        # 1. Initialize NAO & LEDs
        self.nao = Nao(ip=self.nao_ip)
        self.emotions = NaoLEDS(self.nao)
        
        # 2. Autonomous Life & Awareness (Face Tracking)
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
        
        # 3. Initialize Speech-to-Text
        self.logger.info("Initializing Speech-to-Text...")
        try:
            with open(self.dialogflow_keyfile_path) as f:
                keyfile_json = json.load(f)
            
            stt_conf = GoogleSpeechToTextConf(
                keyfile_json=keyfile_json,
                sample_rate_hertz=16000,
                language="en-US",
                interim_results=False,
            )
            self.speech_to_text = GoogleSpeechToText(conf=stt_conf, input_source=self.nao.mic)
        except Exception as e:
            self.logger.error(f"Failed to init STT: {e}")
            raise

        # 4. Initialize Dialogflow Client
        self.logger.info("Initializing Dialogflow Client...")
        self.dialogflow_client = DialogflowCXDirectClient(
            keyfile_path=self.dialogflow_keyfile_path,
            agent_id=self.agent_id,
            location=self.location
        )
        self.logger.info("Setup complete.")

    # -------------------------------------------------------------
    # SCRIPTED PERFORMANCE ENGINE (Opening/Closing)
    # -------------------------------------------------------------

    def perform_script(self, script_lines, name="Script"):
        """
        Executes a pre-defined list of text/gesture dictionaries.
        """
        self.logger.info(f"Starting {name}...")
        
        for i, line in enumerate(script_lines):
            if self.shutdown_event.is_set():
                break

            text = line["text"]
            gesture = line.get("gesture")
            pre_delay = line.get("pre_delay", 0)

            if pre_delay > 0:
                time.sleep(pre_delay)
            
            self.logger.info(f"[{name} {i+1}] Saying: '{text[:20]}...' | Gesture: {gesture}")
            
            # Start speech in background thread to sync with motion
            def speak():
                self.nao.tts.request(NaoqiTextToSpeechRequest(text))
            
            t = threading.Thread(target=speak)
            t.start()
            
            # Small delay to let TTS start
            time.sleep(0.3)
            
            # Perform gesture
            if gesture:
                # Resolve gesture if it's just a keyword
                if "/" not in gesture:
                    gesture = get_best_animation(gesture) or gesture
                    
                self.nao.motion.request(NaoqiAnimationRequest(gesture))
            
            # Wait for speech to finish
            t.join()
            
            # Small pause between lines
            time.sleep(0.1)

        self.logger.info(f"Finished {name}.")

    # -------------------------------------------------------------
    # STORYTELLING ENGINE (Producer - Consumer)
    # -------------------------------------------------------------
    
    def producer_story(self, full_text):
        """
        Splits text into chunks, generates audio/gestures, and enqueues them.
        """
        self.logger.info("Producer: Generating story assets...")
        
        # Clean text
        full_text = full_text.replace("\n", " ")
        
        # Split by punctuation
        chunks = re.split(r'(?<=[.!?:]) +', full_text)
        chunks = [c.strip() for c in chunks if c.strip()]
        
        for i, text in enumerate(chunks):
            if self.shutdown_event.is_set():
                break
                
            voice = "bm_lewis" # Storyteller voice
            output_file = f"temp_story_{uuid.uuid4().hex[:8]}.wav"
            
            # Determine gesture (simple keyword matching)
            gesture = get_best_animation("neutral", text)
            
            self.logger.info(f"Generating [{i}]: {text[:20]}... -> {gesture}")
            
            success = generate_audio(text, output_file, voice)
            if success:
                self.audio_queue.put({
                    "type": "story_segment",
                    "audio_file": output_file,
                    "gesture": gesture,
                    "text": text
                })
            else:
                self.logger.error(f"TTS Failed for: {text}")

        self.audio_queue.put({"type": "DONE"})
        self.logger.info("Producer: Finished.")

    def perform_story(self):
        """
        Consumes the queue and plays audio/gestures on the robot.
        """
        self.logger.info("Performer: Starting playback...")
        
        while not self.shutdown_event.is_set():
            item = self.audio_queue.get()
            
            if item["type"] == "DONE":
                break
            
            if item["type"] == "story_segment":
                audio_path = item["audio_file"]
                gesture = item["gesture"]
                text = item["text"]
                
                self.logger.info(f"Performing: {text[:30]}...")
                
                # Play Audio Thread
                def play_worker():
                    try:
                        with wave.open(audio_path, "rb") as wf:
                            sr = wf.getframerate()
                            data = wf.readframes(wf.getnframes())
                            self.nao.speaker.request(AudioRequest(sample_rate=sr, waveform=data))
                    except Exception as e:
                        self.logger.error(f"Audio Playback Error: {e}")

                t_audio = threading.Thread(target=play_worker)
                t_audio.start()
                
                # Sync Gesture
                time.sleep(0.2)
                if gesture:
                    self.nao.motion.request(NaoqiAnimationRequest(gesture))
                
                t_audio.join()
                
                # Cleanup
                try:
                    os.remove(audio_path)
                except:
                    pass
                
                time.sleep(0.5) # Pause between sentences
        
        self.logger.info("Performer: Finished segment.")

    # -------------------------------------------------------------
    # DIALOGFLOW & INTERACTION LOOP
    # -------------------------------------------------------------

    def get_user_input(self):
        """Listen to user via STT."""
        self.logger.info("Listening...")
        print("\n[NAO is listening...]")
        try:
            res = self.speech_to_text.request(GetStatementRequest())
            if res and res.response and res.response.alternatives:
                transcript = res.response.alternatives[0].transcript.strip()
                self.logger.info(f"User said: {transcript}")
                return transcript
        except Exception as e:
            self.logger.error(f"STT Error: {e}")
        
        return ""

    def handle_payloads(self, payloads):
        """
        Handle custom payloads from Dialogflow.
        Looking for:
        {
            "robot_command": {
                "text": "Long story text...",
                "motion": "optional_gesture",
                "led": "optional_color"
            }
        }
        """
        story_content = ""
        
        for payload in payloads:
            if "robot_command" in payload:
                cmd = payload["robot_command"]
                
                if "led" in cmd and self.emotions:
                    # TODO: Map color string to LED function if needed
                    pass
                
                if "motion" in cmd and cmd["motion"]:
                    # Immediate motion without audio queue
                    motion_val = cmd["motion"]
                    
                    # If it's a simple keyword (no slashes), try to resolve it to a real path
                    if "/" not in motion_val:
                        resolved = get_best_animation(motion_val)
                        if resolved:
                            self.logger.info(f"Resolved motion intent '{motion_val}' to: {resolved}")
                            motion_val = resolved
                        else:
                            self.logger.warning(f"Could not resolve motion intent: {motion_val}")
                    
                    self.nao.motion.request(NaoqiAnimationRequest(motion_val))
                
                if "text" in cmd and cmd["text"]:
                    # This is story content to be performed
                    story_content += cmd["text"] + " "
        
        return story_content.strip()

    def run(self):
        """Main Loop."""
        try:
            # 1. Start - Perform Opening Script ONCE
            self.perform_script(self.OPENING_SCRIPT, name="Opening")

            # 2. Iterate through each Flow in sequence
            for i, flow_id in enumerate(self.flows):
                if self.shutdown_event.is_set():
                    break
                    
                self.logger.info(f"--- Starting Flow Cycle {i+1}/{len(self.flows)}: {flow_id} ---")
                
                # Start the specific flow
                response = self.dialogflow_client.execute_flow(flow_id, self.session_id)
                parsed = self.dialogflow_client.parse_response(response)
                
                # Speak initial greeting for this flow
                self.process_turn_response(parsed)

                # Interaction Loop for this Flow
                flow_active = True
                while flow_active and not self.shutdown_event.is_set():
                    # Listen
                    user_text = self.get_user_input()
                    if not user_text:
                        continue
                    
                    if user_text.lower() in ["quit", "exit", "stop"]:
                        self.nao_say("Goodbye!")
                        self.shutdown_event.set() # Stop everything
                        break
                    
                    # Send to Dialogflow
                    resp = self.dialogflow_client.detect_intent_text(user_text, self.session_id)
                    parsed = self.dialogflow_client.parse_response(resp)
                    
                    self.process_turn_response(parsed)
                    
                    if parsed['end_interaction']:
                        self.logger.info(f"End of Flow Cycle {i+1}.")
                        flow_active = False # Break inner loop, proceed to next flow
                        
                        # Small pause before next flow
                        time.sleep(2.0)
                        break

            # 3. Perform Closing Script at the very end
            if not self.shutdown_event.is_set():
                self.perform_script(self.CLOSING_SCRIPT, name="Closing")
                    
        except KeyboardInterrupt:
            self.logger.info("Interrupted.")
        except Exception as e:
            self.logger.error(f"Runtime Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
            
    def process_turn_response(self, parsed):
        """Decide whether to speak simply or perform a story."""
        
        # 1. Check for Payloads (Story Mode)
        story_text = self.handle_payloads(parsed['payload_messages'])
        
        # Log Generative Info if present
        if parsed.get('generative_info'):
            self.logger.info(f"Generative Info received: {parsed['generative_info']}")

        # 2. FALLBACK: Check for Text Payload (if Dialogflow config is missing Custom Payload)
        # If no payload commands found, check if the text response itself looks like the story.
        if not story_text:
            all_text = " ".join(parsed['fulfillment_messages'])
            # Trigger if we see specific story keywords
            if "Once upon a time" in all_text or "Generating Story" in all_text or "The huntsman" in all_text:
                 self.logger.info("Text Keyword Detected! Treating response as Story.")
                 story_text = all_text

        if story_text:
            self.logger.info("STORY DETECTED. Starting Performance...")
            # Start Producer
            p_thread = threading.Thread(target=self.producer_story, args=(story_text,))
            p_thread.start()
            
            # Start Consumer (blocks until done)
            self.perform_story()
            
            p_thread.join()
            return

        # 3. Normal Conversation Mode
        # If no story payload, just speak the fulfillment messages using built-in TTS
        
        for msg in parsed['fulfillment_messages']:
            if msg.strip():
                self.logger.info(f"Saying: {msg}")
                self.nao_say(msg)
    
    def nao_say(self, text):
        """Simple wrapper for Naoqi TTS."""
        self.nao.tts.request(NaoqiTextToSpeechRequest(text))

    def cleanup(self):
        self.logger.info("Cleanup...")
        if self.nao:
            self.nao.autonomous.request(NaoRestRequest())
            self.nao.autonomous.request(NaoBasicAwarenessRequest(False))
            self.nao.autonomous.request(NaoListeningMovementRequest(False))

if __name__ == "__main__":
    app = SnowWhiteInteractive()
    app.run()

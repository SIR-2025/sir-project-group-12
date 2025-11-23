# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.nao import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest

# Import the service(s) we will be using
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DialogflowCX,
    DialogflowCXConf,
    DetectIntentRequest,
    QueryResult,
    RecognitionResult,
)

# Import libraries necessary for the demo
import json
import time
from os.path import abspath, join
import numpy as np


class NaoDialogflowCXDemo(SICApplication):
    """
    NAO Dialogflow CX Co-Creator Storyteller Application.
    This script connects to Dialogflow CX and uses a custom payload
    to drive the Nao's performative actions.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoDialogflowCXDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "ip"
        self.dialogflow_keyfile_path = abspath(join("..", "..", "conf", "google", "google-key.json"))
        self.nao = None
        self.dialogflow_cx = None
        self.session_id = str(np.random.randint(10000)) # Use string for session ID

        self.set_log_level(sic_logging.INFO)
        
        # This map translates abstract names to existing Nao animations
        # TODO improve this mapping as needed
        self.animation_map = {
            "open_arms_welcoming": "animations/Stand/Gestures/Hey_1",
            "look_around_curious": "animations/Stand/Gestures/LookingAround_1",
            "lean_in_excited": "animations/Stand/Gestures/Excited_1",
            "thinking_pose_story": "animations/Stand/Gestures/Thinking_1",
            "excited_nod": "animations/Stand/Gestures/Yes_1",
            "happy_dance": "animations/Stand/Emotions/Positive/Happy_1",
        }
        
        self.setup()
    
    def on_recognition(self, message):
        """
        Callback function for Dialogflow CX recognition results.
        """
        if message.response:
            if hasattr(message.response, 'recognition_result') and message.response.recognition_result:
                rr = message.response.recognition_result
                if hasattr(rr, 'is_final') and rr.is_final:
                    if hasattr(rr, 'transcript'):
                        self.logger.info("Transcript: {transcript}".format(transcript=rr.transcript))
    
    def setup(self):
        """Initialize and configure NAO robot and Dialogflow CX."""
        try:
            self.logger.info("Initializing NAO robot...")
            self.nao = Nao(ip=self.nao_ip, dev_test=False)
            # Ensure Nao is in a good starting posture
            self.nao.motion.request(NaoPostureRequest("StandInit", 1.0), block=True)
            self.nao_mic = self.nao.mic
        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to connect to Nao robot at {self.nao_ip}. Exception: {e}")
            self.shutdown()
            return

        self.logger.info("Initializing Dialogflow CX...")
        
        try:
            with open(self.dialogflow_keyfile_path) as f:
                keyfile_json = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"CRITICAL: Dialogflow keyfile not found at {self.dialogflow_keyfile_path}")
            self.shutdown()
            return
        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to load keyfile. Exception: {e}")
            self.shutdown()
            return
        
        # Agent configuration
        agent_id = "agent_id"  # Your agent ID
        location = "europe-west4"  # Your agent location
        
        dialogflow_conf = DialogflowCXConf(
            keyfile_json=keyfile_json,
            agent_id=agent_id,
            location=location,
            sample_rate_hertz=16000,  # NAO's microphone sample rate
            language="en",
            # no_input_timeout_sec=1500,
        )
        
        # Initialize Dialogflow CX with NAO's microphone as input
        self.dialogflow_cx = DialogflowCX(conf=dialogflow_conf, input_source=self.nao_mic)
        
        self.logger.info("Initialized Dialogflow CX... registering callback function")
        self.dialogflow_cx.register_callback(callback=self.on_recognition)
    
    def run(self):
        """Main application loop."""
        
        try:
            self.logger.info(" -- Storyteller is Ready -- ")
            
           # --- This is the "instant" kick-off call ---
            self.logger.info(" ----- Sending 'start_story_kickoff' event to start the story...")
            reply = self.dialogflow_cx.request(DetectIntentRequest(self.session_id, 
                                                                 event_input="start_story_kickoff"))
            # The first 'reply' will be the generative kick-off from the 1_Story_Kickoff page.
            # We process it once *before* starting the main loop.
            self.process_dialogflow_reply(reply)

            # Main conversation loop
            while not self.shutdown_event.is_set():
                self.logger.info(" ----- Your turn to talk! (Listening...)")
                
                # This call waits for the user to speak.
                reply = self.dialogflow_cx.request(DetectIntentRequest(self.session_id))
                
                # Process the reply (speak, act, log)
                self.process_dialogflow_reply(reply)
                    
        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        except Exception as e:
            self.logger.error("Exception in main run loop: {}".format(e))
            import traceback
            traceback.print_exc()
        finally:
            self.logger.info("Shutting down...")
            if self.nao:
                # Go to a safe resting posture
                self.nao.motion.request(NaoPostureRequest("Crouch", 1.0), block=True)
            self.shutdown()

    def process_dialogflow_reply(self, reply: QueryResult):
        """
        Helper function to process the QueryResult from Dialogflow.
        This handles payload commands, TTS, and logging with error checking.
        """
        if not reply:
            self.logger.warning("Received an invalid (None) reply from Dialogflow.")
            return

        if hasattr(reply, 'payload') and reply.payload:
            self.logger.info(f"Received custom payload: {reply.payload}")
            try:
                payload_data = reply.payload 
                
                if "sicf_commands" in payload_data:
                    commands = payload_data["sicf_commands"]
                    
                    if "robot_animation" in commands and "name" in commands["robot_animation"]:
                        anim_name_from_gemini = commands["robot_animation"]["name"]
                        
                        if not anim_name_from_gemini:
                            self.logger.warning("Received empty animation name in payload.")
                        else:
                            # Clean the string from newlines (e.g., "happy_dance\n")
                            anim_name_clean = anim_name_from_gemini.strip()
                            
                            if anim_name_clean in self.animation_map:
                                nao_animation_path = self.animation_map[anim_name_clean]
                                self.logger.info(f"Executing animation: '{anim_name_clean}' -> '{nao_animation_path}'")
                                
                                self.nao.motion.request(NaoPostureRequest("Stand", 0.5), block=False)
                                self.nao.motion.request(NaoqiAnimationRequest(nao_animation_path), block=False)
                            else:
                                self.logger.warning(f"Animation '{anim_name_clean}' not in animation_map! Skipping.")
                            
            except Exception as e:
                self.logger.error(f"Failed to parse or execute custom payload: {e}")
        
        else:
            self.logger.info("No custom payload received in this turn.")

        # Log the transcript
        if reply.transcript:
            self.logger.info(f"User said: {reply.transcript}")
        
        # Robust TTS Handling
        if reply.fulfillment_message:
            text = reply.fulfillment_message.strip()
            if text:
                self.logger.info(f"NAO reply: {text}")
                self.nao.tts.request(NaoqiTextToSpeechRequest(text), volume=25)
            else:
                self.logger.info("Received empty fulfillment message. Nao will not speak.")
        else:
            self.logger.info("No fulfillment message from Dialogflow in this turn.")
        
        # Log any parameters
        if reply.parameters:
            self.logger.info(f"Parameters: {reply.parameters}")


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoDialogflowCXDemo()
    demo.run()
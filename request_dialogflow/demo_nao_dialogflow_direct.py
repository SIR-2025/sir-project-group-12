"""
NAO Robot with Dialogflow CX Direct HTTPS Integration (Voice-Enabled)

This script combines NAO robot capabilities with direct Dialogflow CX HTTPS requests
to execute conversation flows. NAO will:
- Listen to user voice input via its microphone
- Process responses through Dialogflow CX
- Speak the agent's responses naturally
- Execute robot commands (gestures, LEDs) from payloads

Requirements:
    pip install social-interaction-cloud[google-stt] google-auth requests

Setup:
    1. Start the Google Speech-to-Text service:
       run-google-stt
    
    2. Update NAO_IP with your robot's IP address
    
    3. Place google-key.json in the same directory
    
    4. Configure your agent and flow settings in __init__()
    
    5. Run: python demo_nao_dialogflow_direct.py

Note: NAO will speak agent responses naturally, removing technical labels
      like "Adjective:" and keeping only natural questions.
"""

# Import basic SIC framework
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import NAO device
from sic_framework.devices import Nao
from sic_framework.devices.nao import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoWakeUpRequest, NaoRestRequest

# Import Google Speech-to-Text service
from sic_framework.services.google_stt.google_stt import (
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
    GetStatementRequest,
)

# Import Dialogflow CX direct client
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import uuid
from time import sleep
import re


class DialogflowCXDirectClient:
    """Client for making direct HTTPS requests to Dialogflow CX."""
    
    def __init__(self, keyfile_path, agent_id, location):
        """Initialize the Dialogflow CX client."""
        self.agent_id = agent_id
        self.location = location
        
        # Load credentials
        with open(keyfile_path) as f:
            keyfile_json = json.load(f)
        
        self.project_id = keyfile_json.get("project_id")
        
        # Create credentials
        self.credentials = service_account.Credentials.from_service_account_info(
            keyfile_json,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        self.base_url = f"https://{location}-dialogflow.googleapis.com/v3"
    
    def _get_access_token(self):
        """Get a fresh access token."""
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token
    
    def detect_intent_text(self, text, session_id, language_code="en", current_page=None, parameters=None):
        """Send a text query to Dialogflow CX."""
        session_path = f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/agents/{self.agent_id}/sessions/{session_id}:detectIntent"
        
        request_body = {
            "queryInput": {
                "text": {
                    "text": text
                },
                "languageCode": language_code
            }
        }
        
        if current_page or parameters:
            request_body["queryParams"] = {}
            if current_page:
                request_body["queryParams"]["currentPage"] = current_page
            if parameters:
                request_body["queryParams"]["parameters"] = parameters
        
        access_token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(session_path, headers=headers, json=request_body)
        response.raise_for_status()
        
        return response.json()
    
    def parse_response(self, response):
        """Parse the Dialogflow CX response."""
        query_result = response.get("queryResult", {})
        
        parsed = {
            "transcript": query_result.get("transcript", ""),
            "parameters": query_result.get("parameters", {}),
            "intent": None,
            "intent_confidence": None,
            "fulfillment_messages": [],
            "payload_messages": [],
            "current_page_name": query_result.get("currentPage", {}).get("displayName", ""),
            "current_flow_name": query_result.get("currentFlow", {}).get("displayName", ""),
            "end_interaction": False
        }
        
        if "intent" in query_result and query_result["intent"]:
            parsed["intent"] = query_result["intent"].get("displayName", "")
        
        if "intentDetectionConfidence" in query_result:
            parsed["intent_confidence"] = query_result["intentDetectionConfidence"]
        
        response_messages = query_result.get("responseMessages", [])
        for msg in response_messages:
            if "text" in msg:
                texts = msg["text"].get("text", [])
                parsed["fulfillment_messages"].extend(texts)
            elif "payload" in msg:
                parsed["payload_messages"].append(msg["payload"])
            elif "endInteraction" in msg:
                parsed["end_interaction"] = True
        
        return parsed
    
    def execute_flow(self, flow_id, session_id, initial_text="hi", parameters=None):
        """Execute a flow from its START_PAGE."""
        if parameters is None:
            parameters = {}
        
        flow_start_page = f"projects/{self.project_id}/locations/{self.location}/agents/{self.agent_id}/flows/{flow_id}/pages/START_PAGE"
        
        return self.detect_intent_text(
            text=initial_text,
            session_id=session_id,
            current_page=flow_start_page,
            parameters=parameters
        )


class NaoDialogflowDirectDemo(SICApplication):
    """
    NAO robot with Dialogflow CX direct HTTPS integration.
    
    This demo executes a specific Dialogflow CX flow and makes NAO speak the responses.
    """
    
    def __init__(self):
        super(NaoDialogflowDirectDemo, self).__init__()
        
        # ========== CONFIGURATION ==========
        # NAO Robot
        self.nao_ip = "10.0.0.181"  # TODO: Update with your NAO's IP
        
        # Dialogflow CX
        self.keyfile_path = "google-key.json"
        self.agent_id = "5079e43a-fec2-441d-bf10-f23f292fbf15"
        self.location = "europe-west4"
        
        # Flow to execute
        self.flows = {
            "demo_cycle_1": "c5eacb8c-2410-47b0-a51a-02c96c998c08",
            "demo_cycle_2": "35b11713-c8ba-4c88-968a-1acbd74a43a8",
        }
        self.selected_flow = "demo_cycle_1"
        
        # Session
        self.session_id = str(uuid.uuid4())
        
        # Initialize
        self.nao = None
        self.dialogflow_client = None
        self.speech_to_text = None
        
        self.set_log_level(sic_logging.INFO)
        self.setup()
    
    def setup(self):
        """Initialize NAO, Speech-to-Text, and Dialogflow CX client."""
        self.logger.info("Initializing NAO robot...")
        self.nao = Nao(ip=self.nao_ip)
        nao_mic = self.nao.mic
        
        self.logger.info("Initializing Speech-to-Text...")
        # Load keyfile for Google Speech-to-Text
        with open(self.keyfile_path) as f:
            keyfile_json = json.load(f)
        
        # Configure Speech-to-Text for NAO (16000 Hz sample rate)
        stt_conf = GoogleSpeechToTextConf(
            keyfile_json=keyfile_json,
            sample_rate_hertz=16000,  # NAO's microphone sample rate
            language="en-US",
            interim_results=False,
        )
        
        # Initialize Speech-to-Text with NAO's microphone
        self.speech_to_text = GoogleSpeechToText(conf=stt_conf, input_source=nao_mic)
        
        self.logger.info("Initializing Dialogflow CX client...")
        self.dialogflow_client = DialogflowCXDirectClient(
            keyfile_path=self.keyfile_path,
            agent_id=self.agent_id,
            location=self.location
        )
        
        self.logger.info("Setup complete")
    
    def clean_speech_text(self, text):
        """
        Clean the text to make NAO's speech more natural.
        
        Removes technical terms and keeps only natural questions/prompts.
        Examples:
        - "Adjective: Name an adjective..." -> "Name an adjective..."
        - "Any Word: Tell me a word" -> "Tell me a word"
        """
        if not text:
            return text
        
        # Remove labels like "Adjective:", "Any Word:", etc. (pattern: Word/words followed by colon)
        text = re.sub(r'^[A-Za-z\s]+:\s*', '', text)
        
        # Replace "Name this..." patterns with more natural phrasing
        text = re.sub(r'Name this', 'Name a', text)
        text = re.sub(r'Name an', 'Tell me', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def nao_speak(self, text, animated=False, clean=True):
        """Make NAO speak the given text."""
        if text:
            if clean:
                text = self.clean_speech_text(text)
            
            if text:  # Check again after cleaning
                self.logger.info(f"NAO says: {text}")
                self.nao.tts.request(NaoqiTextToSpeechRequest(text, animated=animated))
    
    def handle_robot_commands(self, payload_messages):
        """
        Handle robot commands from Dialogflow CX payload.
        
        Expected payload format:
        {
            "robot_command": {
                "text": "Text to speak",
                "motion": "gesture_name",
                "led": "color"
            }
        }
        """
        for payload in payload_messages:
            if "robot_command" in payload:
                cmd = payload["robot_command"]
                
                # Handle motion/animation
                if "motion" in cmd:
                    motion = cmd["motion"]
                    self.logger.info(f"Executing motion: {motion}")
                    
                    if motion == "wave":
                        self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1"), block=False)
                    elif motion == "scary":
                        # You can add scary animation here
                        pass
                
                # Handle LED color
                if "led" in cmd:
                    led_color = cmd["led"]
                    self.logger.info(f"Setting LED color: {led_color}")
                    # Add LED control here if needed
                
                # Handle text in payload
                if "text" in cmd:
                    self.logger.info(f"Payload text: {cmd['text']}")
    
    def get_user_voice_input(self):
        """
        Get user input via speech recognition from NAO's microphone.
        
        Returns:
            str: The transcribed text from the user's speech
        """
        try:
            # Visual cue that NAO is listening
            self.logger.info("NAO is listening...")
            print("\n[NAO is listening... Speak now]")
            
            # Request speech recognition
            result = self.speech_to_text.request(GetStatementRequest())
            
            # Extract transcript
            if result and hasattr(result, 'response') and hasattr(result.response, 'alternatives'):
                if result.response.alternatives:
                    transcript = result.response.alternatives[0].transcript
                    self.logger.info(f"User said: {transcript}")
                    return transcript.strip()
            
            self.logger.warning("No speech recognized")
            return ""
            
        except Exception as e:
            self.logger.error(f"Speech recognition error: {e}")
            return ""
    
    def run(self):
        """Main conversation loop."""
        try:
            # Wake up NAO
            self.logger.info("Waking up NAO...")
            self.nao.autonomous.request(NaoWakeUpRequest())
            sleep(1)
            
            # Welcome message
            self.nao_speak("Hello, I am Nao. Let's start our conversation!", clean=False)
            sleep(1)
            
            # Execute the flow
            flow_id = self.flows[self.selected_flow]
            self.logger.info(f"Executing flow: {self.selected_flow} ({flow_id})")
            self.logger.info(f"Session ID: {self.session_id}")
            
            response = self.dialogflow_client.execute_flow(
                flow_id=flow_id,
                session_id=self.session_id
            )
            parsed = self.dialogflow_client.parse_response(response)
            
            # Display initial response
            self.display_state(parsed)
            
            # Speak the first message (naturally cleaned)
            if parsed['fulfillment_messages']:
                for msg in parsed['fulfillment_messages']:
                    self.nao_speak(msg, clean=True)
                    sleep(0.5)
            
            # Handle robot commands in payload
            if parsed['payload_messages']:
                self.handle_robot_commands(parsed['payload_messages'])
            
            # Conversation loop
            turn = 1
            while not self.shutdown_event.is_set():
                # Check if conversation ended
                if parsed['end_interaction'] or parsed['current_page_name'] == 'End Session':
                    self.logger.info("Conversation has ended")
                    self.nao_speak("Thank you for the conversation. Goodbye!", clean=False)
                    break
                
                self.logger.info(f"\n--- Turn {turn} ---")
                
                # Get user input via speech recognition
                user_text = self.get_user_voice_input()
                
                if user_text.lower() in ['quit', 'exit', 'stop']:
                    self.logger.info("User requested exit")
                    break
                
                if not user_text:
                    self.logger.warning("No input received, asking again...")
                    self.nao_speak("I didn't hear you. Please try again.", clean=False)
                    continue
                
                # Send to Dialogflow
                self.logger.info(f"User said: {user_text}")
                response = self.dialogflow_client.detect_intent_text(
                    text=user_text,
                    session_id=self.session_id
                )
                parsed = self.dialogflow_client.parse_response(response)
                
                # Display state
                self.display_state(parsed)
                
                # Make NAO speak the response (naturally cleaned)
                if parsed['fulfillment_messages']:
                    for msg in parsed['fulfillment_messages']:
                        self.nao_speak(msg, clean=True)
                        sleep(0.5)
                
                # Handle robot commands
                if parsed['payload_messages']:
                    self.handle_robot_commands(parsed['payload_messages'])
                
                turn += 1
            
            # Rest NAO
            self.logger.info("Putting NAO to rest...")
            self.nao.autonomous.request(NaoRestRequest())
            
        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        except Exception as e:
            self.logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()
    
    def display_state(self, parsed):
        """Display the current conversation state."""
        self.logger.info("-" * 60)
        self.logger.info(f"Flow: {parsed['current_flow_name']}")
        self.logger.info(f"Page: {parsed['current_page_name']}")
        
        if parsed['intent']:
            self.logger.info(f"Intent: {parsed['intent']} (confidence: {parsed['intent_confidence']})")
        
        if parsed['fulfillment_messages']:
            self.logger.info("Agent response:")
            for msg in parsed['fulfillment_messages']:
                self.logger.info(f"  {msg}")
        
        if parsed['parameters']:
            self.logger.info("Parameters:")
            for key, value in parsed['parameters'].items():
                self.logger.info(f"  {key}: {value}")
        
        self.logger.info("-" * 60)


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoDialogflowDirectDemo()
    demo.run()


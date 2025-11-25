# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoWakeUpRequest, 
    NaoRestRequest
    #NaoqiAutonomousLifeRequest
)
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest, NaoLEDRequest
from sic_framework.core.message_python2 import AudioRequest

# Import libraries necessary for the demo
from time import sleep
from pathlib import Path
import wave
import os
from dotenv import load_dotenv
import threading

load_dotenv()

# OpenAI imports
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError as e:
    print("Missing dependencies. Install with: pip install openai")
    raise e


class NaoTheatricalPerformance(SICApplication):
    """
    NAO Theatrical Performance Demo.
    
    A complete theatrical performance featuring:
    1. Introduction with welcoming gestures and white eyes
    2. Scary story narration with OpenAI TTS, red eyes, and dramatic gestures
    3. Ending with thanks, green eyes, and a bow
    """
    
    def __init__(self, nao_ip="10.0.0.181"):
        super(NaoTheatricalPerformance, self).__init__()
        
        self.nao_ip = nao_ip
        self.nao = None
        self.speech_file_path = Path(__file__).parent / "theatrical_speech.wav"
        
        # Story content
        self.introduction = "Good evening everyone! Welcome to my performance tonight. I have a chilling tale to share with you."
        
        self.scary_story = """
        It was a dark and stormy night in an abandoned mansion. 
        Sarah heard footsteps echoing through the empty halls, getting closer... and closer. 
        She turned around, but no one was there. 
        Then, a cold whisper brushed past her ear: "You should not have come here."
        The lights flickered and went out. In the darkness, she felt a hand on her shoulder.
        """
        
        self.ending = "Thank you all for listening to my story. I hope it gave you chills! Good night everyone."
        
        # Threading control for async speech generation
        self.speech_generation_thread = None
        self.speech_ready = False
        self.speech_generation_error = None
        
        self.set_log_level(sic_logging.INFO)
        self.setup()
    
    def setup(self):
        """Initialize NAO robot and start async speech generation."""
        self.logger.info("Initializing NAO Theatrical Performance...")
        
        # Start async speech generation immediately
        self.logger.info("Starting async OpenAI speech generation...")
        self.speech_generation_thread = threading.Thread(target=self._generate_speech_async)
        self.speech_generation_thread.start()
        
        # Initialize NAO while speech is being generated
        self.nao = Nao(ip=self.nao_ip)
        self.logger.info("NAO initialized successfully")
    
    def _generate_speech_async(self):
        """Background thread function to generate OpenAI speech."""
        try:
            scary_instructions = """
            Voice: Deep, hushed, and enigmatic, with a slow, deliberate cadence that draws the listener in.
            Phrasing: Sentences are short and rhythmic, building tension with pauses and carefully placed suspense.
            Punctuation: Dramatic pauses, ellipses, and abrupt stops enhance the feeling of unease and anticipation.
            """
            
            self.logger.info("Generating OpenAI speech in background...")
            success = self.generate_openai_speech(
                self.scary_story,
                voice="onyx",
                speed=1.0,
                instructions=scary_instructions
            )
            
            if success:
                self.speech_ready = True
                self.logger.info("Background speech generation completed successfully")
            else:
                self.speech_generation_error = "Failed to generate speech"
                self.logger.error("Background speech generation failed")
                
        except Exception as e:
            self.speech_generation_error = str(e)
            self.logger.error("Error in background speech generation: {}".format(e))
    
    def set_eye_color(self, red, green, blue, duration=1.0):
        """
        Set NAO's eye color.
        
        Args:
            red: Red intensity (0.0 to 1.0)
            green: Green intensity (0.0 to 1.0)
            blue: Blue intensity (0.0 to 1.0)
            duration: Fade duration in seconds
        """
        self.nao.leds.request(NaoFadeRGBRequest("FaceLeds", red, green, blue, duration))
    
    def wakeup(self):
        """Wake up NAO."""
        self.logger.info("Waking up NAO...")
        self.nao.autonomous.request(NaoWakeUpRequest())
    
    def rest(self):
        """Put NAO to rest."""
        self.logger.info("NAO going to rest...")
        self.nao.autonomous.request(NaoRestRequest())
    
    def say(self, text, animated=False):
        """Make NAO speak using built-in TTS."""
        self.nao.tts.request(NaoqiTextToSpeechRequest(text, animated=animated))
    
    def perform_gesture(self, animation_name, block=True):
        """
        Perform a gesture animation.
        
        Common animations:
        - animations/Stand/Gestures/Hey_1
        - animations/Stand/Gestures/Enthusiastic_4
        - animations/Stand/Gestures/Explain_1
        - animations/Stand/Gestures/BowShort_1
        - animations/Stand/Emotions/Negative/Afraid_1
        - animations/Stand/Emotions/Positive/Excited_1
        """
        self.nao.motion.request(NaoqiAnimationRequest(animation_name), block=block)
    
    def generate_openai_speech(self, text, voice="onyx", speed=1.0, instructions=None):
        """
        Generate speech using OpenAI TTS API.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse)
            speed: Speech speed (0.25 to 4.0)
            instructions: Voice style instructions
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Generating speech with OpenAI TTS...")
            self.logger.info("Voice: {}, Speed: {}".format(voice, speed))
            
            with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text,
                response_format="wav",
                instructions=instructions,
                speed=speed
            ) as response:
                response.stream_to_file(self.speech_file_path)
            
            self.logger.info("Speech generated successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to generate speech: {}".format(e))
            return False
    
    def enable_autonomous_life(self, state="solitary"):
        """
        Enable autonomous life for natural movements.
        
        Args:
            state: "disabled", "solitary", "interactive", "safeguard"
        """
        try:
            self.logger.info("Enabling autonomous life: {}".format(state))
            self.nao.autonomous_life.request(NaoqiAutonomousLifeRequest(state))
        except Exception as e:
            self.logger.warning("Failed to set autonomous life: {}".format(e))
    
    def disable_autonomous_life(self):
        """Disable autonomous life movements."""
        try:
            self.logger.info("Disabling autonomous life")
            self.nao.autonomous_life.request(NaoqiAutonomousLifeRequest("disabled"))
        except Exception as e:
            self.logger.warning("Failed to disable autonomous life: {}".format(e))
    
    def play_openai_speech(self):
        """Play the generated OpenAI speech through NAO's speakers with autonomous movement."""
        try:
            self.logger.info("Playing OpenAI generated speech...")
            
            # Load audio file
            with wave.open(str(self.speech_file_path), "rb") as wf:
                samplerate = wf.getframerate()
                sound = wf.readframes(wf.getnframes())
            
            # Enable autonomous movements before speech
            self.logger.info("Enabling autonomous movements during speech...")
            #self.enable_autonomous_life("solitary")
            sleep(0.5)
            
            # Play the speech
            message = AudioRequest(sample_rate=samplerate, waveform=sound)
            self.nao.speaker.request(message)
            
            # Disable autonomous movements after speech
            self.logger.info("Disabling autonomous movements...")
            #self.disable_autonomous_life()
            
            self.logger.info("Speech playback completed")
            return True
            
        except Exception as e:
            self.logger.error("Error playing speech: {}".format(e))
            # Make sure to disable autonomous life even on error
            self.disable_autonomous_life()
            return False
    
    def cleanup_files(self):
        """Clean up generated audio files."""
        try:
            if self.speech_file_path.exists():
                os.remove(self.speech_file_path)
                self.logger.info("Cleaned up audio files")
        except Exception as e:
            self.logger.warning("Failed to cleanup files: {}".format(e))
    
    def perform_introduction(self):
        """
        Act 1: Introduction
        - White eyes
        - Welcoming gestures
        - Introduce the performance
        """
        self.logger.info("=" * 60)
        self.logger.info("ACT 1: INTRODUCTION")
        self.logger.info("=" * 60)
        
        # Set white eyes
        self.set_eye_color(1.0, 1.0, 1.0, duration=1.0)
        sleep(1)
        
        # Welcoming gesture
        self.logger.info("Performing welcoming gesture...")
        self.perform_gesture("animations/Stand/Gestures/Hey_1", block=False)
        sleep(0.5)
        
        # Introduction speech
        self.logger.info("Speaking introduction...")
        self.say(self.introduction, animated=True)
        sleep(1)
    
    def perform_scary_story(self):
        """
        Act 2: Scary Story
        - Red eyes
        - OpenAI TTS with dramatic voice
        - Dramatic gestures
        """
        self.logger.info("=" * 60)
        self.logger.info("ACT 2: SCARY STORY")
        self.logger.info("=" * 60)
        
        # Set red eyes
        self.logger.info("Setting eyes to red...")
        self.set_eye_color(1.0, 0.0, 0.0, duration=1.5)
        sleep(2)
        
        # Wait for speech generation to complete (if not already done)
        if self.speech_generation_thread and self.speech_generation_thread.is_alive():
            self.logger.info("Waiting for speech generation to complete...")
            self.speech_generation_thread.join()
        
        # Check if speech was generated successfully
        if self.speech_ready and not self.speech_generation_error:
            # Perform afraid gesture while story plays
            self.logger.info("Performing dramatic gesture...")
            self.perform_gesture("animations/Stand/Gestures/No_9", block=False)
            sleep(1)
            
            # Play the scary story
            self.logger.info("Playing scary story...")
            self.play_openai_speech()
            self.perform_gesture("animations/Stand/Gestures/No_9", block=False)
            sleep(1)
        else:
            # Fallback to built-in TTS if OpenAI fails
            if self.speech_generation_error:
                self.logger.warning("Speech generation error: {}".format(self.speech_generation_error))
            self.logger.warning("Using fallback TTS for story")
            self.say(self.scary_story, animated=True)
    
    def perform_ending(self):
        """
        Act 3: Ending
        - Green eyes
        - Thank the audience
        - Bow
        """
        self.logger.info("=" * 60)
        self.logger.info("ACT 3: ENDING")
        self.logger.info("=" * 60)
        
        # Set green eyes
        self.logger.info("Setting eyes to green...")
        self.set_eye_color(0.0, 1.0, 0.0, duration=1.5)
        sleep(2)
        
        # Thank the audience
        self.logger.info("Thanking the audience...")
        self.say(self.ending, animated=True)
        sleep(1)
        
        # Bow
        self.logger.info("Performing bow...")
        self.perform_gesture("animations/Stand/Gestures/BowShort_1")
        sleep(1)
    
    def run(self):
        """Main performance sequence."""
        self.logger.info("Starting Theatrical Performance...")
        
        try:
            # Wake up NAO
            self.wakeup()
            sleep(2)
            
            # Act 1: Introduction
            self.perform_introduction()
            sleep(2)
            
            # Act 2: Scary Story
            self.perform_scary_story()
            sleep(2)
            
            # Act 3: Ending
            self.perform_ending()
            sleep(1)
            
            # Put NAO to rest
            self.rest()
            
            self.logger.info("=" * 60)
            self.logger.info("PERFORMANCE COMPLETED SUCCESSFULLY!")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error("Error during performance: {}".format(e))
        finally:
            self.cleanup_files()
            self.logger.info("Shutting down application")
            self.shutdown()


if __name__ == "__main__":
    # Configuration
    nao_ip = "10.0.0.181"
    
    # Create and run the performance
    performance = NaoTheatricalPerformance(nao_ip=nao_ip)
    performance.run()


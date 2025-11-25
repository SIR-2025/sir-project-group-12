# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao

# Import message types and requests
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoWakeUpRequest, NaoRestRequest

# Import libraries necessary for the demo
import wave
from time import sleep


class NaoSoundAndTalkDemo(SICApplication):
    """
    NAO background sound with speech demo.
    Demonstrates playing background audio while the robot talks using TTS.
    Combines functionality from demo_nao_speakers.py and demo_nao_talk.py.
    """
    
    def __init__(self, audio_file):
        # Call parent constructor (handles singleton initialization)
        super(NaoSoundAndTalkDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "10.0.0.181"
        self.audio_file = audio_file  # Relative path from scripts to nao folder
        self.nao = None
        self.sound = None
        self.samplerate = None

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/path/to/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the NAO robot and load audio file."""
        self.logger.info("Starting NAO Sound and Talk Demo...")
        
        # Load audio file once for background playback
        try:
            with wave.open(self.audio_file, "rb") as wf:
                self.samplerate = wf.getframerate()
                self.sound = wf.readframes(wf.getnframes())
            self.logger.info("Loaded audio file '{}' (sample rate: {})".format(
                self.audio_file, self.samplerate
            ))
        except Exception as e:
            self.logger.error("Failed to load audio file '{}': {}".format(self.audio_file, e))
        
        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip)
    
    def play_background_sound(self):
        """Start playing background audio (non-blocking)."""
        if self.sound is not None and self.samplerate is not None:
            self.logger.info("Starting background audio playback")
            message = AudioRequest(sample_rate=self.samplerate, waveform=self.sound)
            self.nao.speaker.request(message, block=False)
        else:
            self.logger.warning("No audio loaded, skipping background sound")
    
    def say(self, text):
        """Make NAO say text using TTS."""
        self.nao.tts.request(NaoqiTextToSpeechRequest(text))
    
    def say_animated(self, text):
        """Make NAO say text with animated gestures."""
        self.nao.tts.request(NaoqiTextToSpeechRequest(text, animated=True), block=False)
    
    def wakeup(self):
        """Wake up the NAO robot."""
        self.logger.info("Waking up NAO...")
        self.nao.autonomous.request(NaoWakeUpRequest())
    
    def rest(self):
        """Put the NAO robot to rest."""
        self.logger.info("NAO going to rest...")
        self.nao.autonomous.request(NaoRestRequest())
    
    def run(self):
        """Main application logic demonstrating background sound with speech."""
        try:
            # Wake up the robot
            self.wakeup()
            sleep(1)
            
            # Start background audio (non-blocking)
            self.play_background_sound()
            
            # Robot talks while background audio plays
            self.logger.info("NAO will now talk with background music")
            
            self.say("Hello! I am a Nao robot.")
            sleep(10)
            
            # Put robot to rest
            self.rest()
            
            self.logger.info("Demo completed successfully")
            
        except Exception as e:
            self.logger.error("Error in demo: {}".format(e))
        finally:
            self.logger.info("Shutting down application")
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    audio_file = "./ghost-audio.wav"
    demo = NaoSoundAndTalkDemo(audio_file)
    demo.run()


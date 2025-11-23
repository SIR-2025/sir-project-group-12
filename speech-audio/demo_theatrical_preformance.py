from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoWakeUpRequest, 
    NaoRestRequest
)
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest, NaoLEDRequest
from sic_framework.core.message_python2 import AudioRequest
from time import sleep
from pathlib import Path
import wave
import os
from dotenv import load_dotenv
import threading

load_dotenv()

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError as e:
    print("Missing dependencies. Install with: pip install openai")
    raise e


class NaoTheatricalPerformance(SICApplication):
    def __init__(self, nao_ip="10.0.0.181"):
        super(NaoTheatricalPerformance, self).__init__()
        
        self.nao_ip = nao_ip
        self.nao = None
        self.speech_file_path = Path(__file__).parent / "theatrical_speech.wav"
        
        self.introduction = "Good evening everyone! Welcome to my performance tonight. I have a chilling tale to share with you."
        
        self.scary_story = """
        It was a dark and stormy night in an abandoned mansion. 
        Sarah heard footsteps echoing through the empty halls, getting closer... and closer. 
        She turned around, but no one was there. 
        Then, a cold whisper brushed past her ear: "You should not have come here."
        The lights flickered and went out. In the darkness, she felt a hand on her shoulder.
        """
        
        self.ending = "Thank you all for listening to my story. I hope it gave you chills! Good night everyone."
        
        self.speech_generation_thread = None
        self.speech_ready = False
        self.speech_generation_error = None
        
        self.set_log_level(sic_logging.INFO)
        self.setup()
    
    def setup(self):
        self.speech_generation_thread = threading.Thread(target=self._generate_speech_async)
        self.speech_generation_thread.start()
        self.nao = Nao(ip=self.nao_ip)
    
    def _generate_speech_async(self):
        try:
            scary_instructions = """
            Voice: Deep, hushed, and enigmatic, with a slow, deliberate cadence that draws the listener in.
            Phrasing: Sentences are short and rhythmic, building tension with pauses and carefully placed suspense.
            Punctuation: Dramatic pauses, ellipses, and abrupt stops enhance the feeling of unease and anticipation.
            """
            
            success = self.generate_openai_speech(
                self.scary_story,
                voice="onyx",
                speed=1.0,
                instructions=scary_instructions
            )
            
            if success:
                self.speech_ready = True
            else:
                self.speech_generation_error = "Failed to generate speech"
                
        except Exception as e:
            self.speech_generation_error = str(e)
    
    def set_eye_color(self, red, green, blue, duration=1.0):
        self.nao.leds.request(NaoFadeRGBRequest("FaceLeds", red, green, blue, duration))
    
    def wakeup(self):
        self.nao.autonomous.request(NaoWakeUpRequest())
    
    def rest(self):
        self.nao.autonomous.request(NaoRestRequest())
    
    def say(self, text, animated=False):
        self.nao.tts.request(NaoqiTextToSpeechRequest(text, animated=animated))
    
    def perform_gesture(self, animation_name, block=True):
        self.nao.motion.request(NaoqiAnimationRequest(animation_name), block=block)
    
    def generate_openai_speech(self, text, voice="onyx", speed=1.0, instructions=None):
        try:
            with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text,
                response_format="wav",
                instructions=instructions,
                speed=speed
            ) as response:
                response.stream_to_file(self.speech_file_path)
            
            return True
            
        except Exception as e:
            return False
    
    def play_openai_speech(self):
        try:
            with wave.open(str(self.speech_file_path), "rb") as wf:
                samplerate = wf.getframerate()
                sound = wf.readframes(wf.getnframes())
            
            sleep(0.5)
            
            message = AudioRequest(sample_rate=samplerate, waveform=sound)
            self.nao.speaker.request(message)
            
            return True
            
        except Exception as e:
            return False
    
    def cleanup_files(self):
        try:
            if self.speech_file_path.exists():
                os.remove(self.speech_file_path)
        except Exception as e:
            pass
    
    def perform_introduction(self):
        self.set_eye_color(1.0, 1.0, 1.0, duration=1.0)
        sleep(1)
        
        self.perform_gesture("animations/Stand/Gestures/Hey_1", block=False)
        sleep(0.5)
        
        self.say(self.introduction, animated=True)
        sleep(1)
    
    def perform_scary_story(self):
        self.set_eye_color(1.0, 0.0, 0.0, duration=1.5)
        sleep(2)
        
        if self.speech_generation_thread and self.speech_generation_thread.is_alive():
            self.speech_generation_thread.join()
        
        if self.speech_ready and not self.speech_generation_error:
            self.perform_gesture("animations/Stand/Gestures/No_9", block=False)
            sleep(1)
            
            self.play_openai_speech()
            self.perform_gesture("animations/Stand/Gestures/No_9", block=False)
            sleep(1)
        else:
            self.say(self.scary_story, animated=True)
    
    def perform_ending(self):
        self.set_eye_color(0.0, 1.0, 0.0, duration=1.5)
        sleep(2)
        
        self.say(self.ending, animated=True)
        sleep(1)
        
        self.perform_gesture("animations/Stand/Gestures/BowShort_1")
        sleep(1)
    
    def run(self):
        try:
            self.wakeup()
            sleep(2)
            
            self.perform_introduction()
            sleep(2)
            
            self.perform_scary_story()
            sleep(2)
            
            self.perform_ending()
            sleep(1)
            
            self.rest()
            
        except Exception as e:
            pass
        finally:
            self.cleanup_files()
            self.shutdown()


if __name__ == "__main__":
    nao_ip = "10.0.0.181"
    performance = NaoTheatricalPerformance(nao_ip=nao_ip)
    performance.run()


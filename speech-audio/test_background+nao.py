from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging
from sic_framework.devices import Nao
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoWakeUpRequest, NaoRestRequest
import wave
from time import sleep


class NaoSoundAndTalkDemo(SICApplication):
    def __init__(self, audio_file):
        super(NaoSoundAndTalkDemo, self).__init__()
        
        self.nao_ip = "10.0.0.181"
        self.audio_file = audio_file
        self.nao = None
        self.sound = None
        self.samplerate = None

        self.set_log_level(sic_logging.INFO)
        self.setup()
    
    def setup(self):
        try:
            with wave.open(self.audio_file, "rb") as wf:
                self.samplerate = wf.getframerate()
                self.sound = wf.readframes(wf.getnframes())
        except Exception as e:
            pass
        
        self.nao = Nao(ip=self.nao_ip)
    
    def play_background_sound(self):
        if self.sound is not None and self.samplerate is not None:
            message = AudioRequest(sample_rate=self.samplerate, waveform=self.sound)
            self.nao.speaker.request(message, block=False)
    
    def say(self, text):
        self.nao.tts.request(NaoqiTextToSpeechRequest(text))
    
    def say_animated(self, text):
        self.nao.tts.request(NaoqiTextToSpeechRequest(text, animated=True), block=False)
    
    def wakeup(self):
        self.nao.autonomous.request(NaoWakeUpRequest())
    
    def rest(self):
        self.nao.autonomous.request(NaoRestRequest())
    
    def run(self):
        try:
            self.wakeup()
            sleep(1)
            
            self.play_background_sound()
            
            self.say("Hello! I am a Nao robot.")
            sleep(10)
            
            self.rest()
            
        except Exception as e:
            pass
        finally:
            self.shutdown()


if __name__ == "__main__":
    audio_file = "./ghost-audio.wav"
    demo = NaoSoundAndTalkDemo(audio_file)
    demo.run()


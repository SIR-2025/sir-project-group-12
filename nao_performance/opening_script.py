import time
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoWakeUpRequest,
    NaoRestRequest,
    NaoBasicAwarenessRequest,
    NaoBlinkingRequest,
)
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest

class OpeningScriptDemo(SICApplication):
    """
    The opening act for the performance.
    """
    def __init__(self):
        super().__init__()
        self.nao_ip = "10.0.0.181"
        self.nao = None
        self.setup()

    def setup(self):
        self.logger.info("Connecting to NAO at %s...", self.nao_ip)
        self.nao = Nao(ip=self.nao_ip)
        self.logger.info("Waking up...")
        self.nao.autonomous.request(NaoWakeUpRequest())
        self.nao.autonomous.request(NaoBasicAwarenessRequest(True))
        self.nao.autonomous.request(NaoBlinkingRequest(True))

    def run(self):
        self.logger.info("Starting opening script...")

        script = [
            {
                "text": "\\style=neutral\\ Hello \\pau=200\\ my name is \\emph=1\\ Nao \\eos=1\\",
                "gesture": "animations/Stand/Gestures/Hey_5" # Wave
            },
            {
                "text": "\\style=neutral\\ Today I will be telling a well-known fairy-tale story; \\pau=400\\ \\emph=1\\ Snowwhite \\eos=1\\",
                "gesture": "animations/Stand/Gestures/Me_7" # Automic/Resting
            },
            {
                "text": "\\style=joyful\\ We all know this childhood story, \\bound=W\\ but today we will tell it with a \\pau=200\\ \\emph=1\\ twist. \\eos=1\\",
                "gesture": "animations/Stand/Gestures/YouKnowWhat_5" # Automic/Resting
            },
            {
                "text": "\\style=didactic\\ You guys will be helping me. \\eos=1\\",
                "gesture": "animations/Stand/Gestures/You_3" # Pointing
            },
            {
                "text": "\\style=didactic\\ You will do so by giving me words to fill in the story. \\eos=1\\",
                "gesture": "animations/Stand/Gestures/Joy_1" # Explaining
            },
            {
                "text": "\\style=neutral\\ I will ask certain question for \\emph=1\\ specific words \\eos=1\\",
                "gesture": "animations/Stand/Gestures/Me_2" # Pointing to self
            },
            {
                "text": "\\style=neutral\\ and my \\emph=1\\ assistants \\bound=W\\ will come to you guys to say the answer. \\eos=1\\",
                "gesture": "animations/Stand/Gestures/Thinking_2" # Pointing to us/audience
            },
            {
                "text": "\\style=neutral\\ \\vct=95\\ I don't want to be the boring one, \\bound=S\\ but please keep the words \\emph=1\\ family-friendly, \\bound=W\\ as I am not allowed to use offensive words. \\eos=1\\",
                "gesture": "animations/Stand/Gestures/Please_3" # Excused stance / begging
            },
            {
                "text": "\\style=neutral\\ \\vct=110\\ Now that everything is clear, \\pau=500\\ Lets begin: \\eos=1\\",
                "gesture": "animations/Stand/Gestures/Enthusiastic_3" # Begin gesture
            }
        ]

        for line in script:
            text = line["text"]
            gesture = line["gesture"]
            
            self.logger.info(f"Saying: '{text}' with gesture: {gesture}")
            
            import threading
            def speak():
                self.nao.tts.request(NaoqiTextToSpeechRequest(text))
            
            t = threading.Thread(target=speak)
            t.start()
            
            # Small delay to sync
            time.sleep(0.3)
            
            # Perform gesture
            self.nao.motion.request(NaoqiAnimationRequest(gesture))
            
            # Wait for speech to finish
            t.join()
            
            # Small pause between lines
            time.sleep(0.1)

        self.logger.info("Script finished.")
        self.cleanup()

    def cleanup(self):
        if self.nao:
            self.nao.autonomous.request(NaoBasicAwarenessRequest(False))
            self.nao.autonomous.request(NaoBlinkingRequest(False))
            self.nao.autonomous.request(NaoRestRequest())

if __name__ == "__main__":
    demo = OpeningScriptDemo()
    demo.run()

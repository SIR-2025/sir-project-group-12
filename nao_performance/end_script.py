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

class EndScriptDemo(SICApplication):
    """
    The closing act for the performance.
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
        self.logger.info("Starting end script...")

        script = [
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

        for line in script:
            text = line["text"]
            gesture = line["gesture"]
            pre_delay = line.get("pre_delay", 0)

            if pre_delay > 0:
                self.logger.info(f"Pausing for {pre_delay} seconds...")
                time.sleep(pre_delay)
            
            self.logger.info(f"Saying: '{text}' with gesture: {gesture}")
            
            # Start speech
            import threading
            def speak():
                self.nao.tts.request(NaoqiTextToSpeechRequest(text))
            
            t = threading.Thread(target=speak)
            t.start()
            
            # Small delay to sync
            time.sleep(0.3)
            
            # Perform gesture if defined
            if gesture:
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
    demo = EndScriptDemo()
    demo.run()

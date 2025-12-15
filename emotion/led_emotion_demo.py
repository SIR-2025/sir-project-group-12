import random
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from emotion.eye_pulse_animator import EyePulseAnimator
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoBasicAwarenessRequest,
    NaoListeningMovementRequest,
    NaoRestRequest,
    NaoSetAutonomousLifeRequest,
    NaoWakeUpRequest,
)
from sic_framework.devices.common_naoqi.naoqi_leds import (
    NaoFadeRGBRequest,
    NaoSetIntensityRequest,
)


class EmotionScript:
    handler_names: Tuple[str, ...]
    weights: Optional[Tuple[float, ...]] = None


class NaoEmotionDemo(SICApplication):
    """
    Interactive NAO emotion demo focused on eye + ear color language.
    Provides multiple angry variants and placeholder mappings for other emotions.
    """

    EMOTIONS: Dict[str, EmotionScript] = {
        "angry": EmotionScript(
            ("_show_angry1", "_show_angry2"),
            (0.5, 0.5),
        ),
        "fear": EmotionScript(("_show_fear",)),
        "surprise": EmotionScript(("_show_surprise",)),
        "disgust": EmotionScript(("_show_disgust",)),
        "sadness": EmotionScript(("_show_sadness",)),
        "enjoyment": EmotionScript(("_show_enjoyment",)),
    }

    # Dictionary to map multiple input variants to emotions
    EMOTION_ALIASES = {
        "mad": "angry",
        "furious": "angry",
        "scared": "fear",
        "afraid": "fear",
        "wow": "surprise",
        "gross": "disgust",
        "sad": "sadness",
        "happy": "enjoyment",
        "joy": "enjoyment",
    }

    EXIT_WORDS = {"quit", "exit", "q", "stop"}

    def __init__(self):
        super(NaoEmotionDemo, self).__init__()
        self.nao_ip = "10.0.0.181"
        self.nao: Optional[Nao] = None
        self.eye_animator: Optional[EyePulseAnimator] = None
        self._listening_enabled = False
        self._basic_awareness_enabled = False
        self.set_log_level(sic_logging.INFO)
        self.setup()

    # ------------------------------------------------------------------ setup/run
    def setup(self):
        self.logger.info("Connecting to NAO...")
        self.nao = Nao(ip=self.nao_ip)
        self.eye_animator = EyePulseAnimator(self.nao)
        self._enable_face_leds()
        self._wake_and_enable_behaviors()
        self._set_basic_awareness(True)
        self._set_listening_movement(True)

    def run(self):
        available = ", ".join(sorted(self.EMOTIONS.keys()))
        self.logger.info("Emotion demo ready. Options: %s (type 'quit' to leave)", available)

        try:
            while True:
                try:
                    raw = input(f"Emotion ({available}, quit): ")
                except EOFError:
                    print()
                    break

                normalized = " ".join(raw.strip().lower().split())
                if not normalized:
                    continue
                if normalized in self.EXIT_WORDS:
                    break

                canonical = self.EMOTION_ALIASES.get(normalized, normalized)
                script = self.EMOTIONS.get(canonical)
                if not script:
                    print(f"Unknown emotion '{raw}'. Try one of: {available}")
                    continue

                self._express_emotion(canonical, script)
        finally:
            self._reset_all()
            self.shutdown()

    # ---------------------------------------------------------------- wake
    def _wake_and_enable_behaviors(self):
        if not self.nao:
            return
        try:
            self.nao.autonomous.request(NaoWakeUpRequest())
            self.nao.autonomous.request(NaoSetAutonomousLifeRequest("interactive"))
        except Exception as exc:
            self.logger.warning("Failed to wake up NAO: %s", exc)

    def _set_basic_awareness(self, enabled: bool):
        if not self.nao:
            return
        try:
            # Keep head attention focused on faces with standard tracking.
            self.nao.autonomous.request(
                NaoBasicAwarenessRequest(
                    enabled,
                    stimulus_detection=[
                        ("People", enabled),
                        ("Movement", enabled),
                        ("Sound", False),
                        ("Touch", False),
                    ],
                    engagement_mode="FullyEngaged" if enabled else None,
                    tracking_mode="WholeBody" if enabled else "Head",
                )
            )
            self._basic_awareness_enabled = enabled
        except Exception as exc:
            self.logger.warning("Failed to set basic awareness: %s", exc)

    def _set_listening_movement(self, enabled: bool):
        if not self.nao:
            return
        try:
            self.nao.autonomous.request(NaoListeningMovementRequest(enabled))
            self._listening_enabled = enabled
        except Exception as exc:
            self.logger.warning("Failed to set listening movement: %s", exc)

    # ------------------------------------------------------------------ helpers for LEDs
    def _enable_face_leds(self):
        if self.nao:
            self.nao.leds.request(NaoSetIntensityRequest("FaceLeds", 1.0))

    def _set_face(self, rgb, duration: float = 0.0):
        if not self.nao:
            return
        r, g, b = rgb
        self.nao.leds.request(NaoFadeRGBRequest("FaceLeds", r, g, b, duration))

    def _set_ears(self, intensity: float, *, enabled: bool = True):
        """Optional ear control; ignored unless explicitly enabled."""
        if not enabled or not self.nao:
            return
        value = max(0.0, min(1.0, intensity))
        for group in ("LeftEarLeds", "RightEarLeds"):
            self.nao.leds.request(NaoSetIntensityRequest(group, value))

    def _express_emotion(self, emotion: str, script: EmotionScript):
        handler_name = script.handler_names[0]
        if len(script.handler_names) > 1:
            if script.weights and len(script.weights) == len(script.handler_names):
                handler_name = random.choices(
                    script.handler_names, weights=script.weights, k=1
                )[0]
            else:
                handler_name = random.choice(script.handler_names)

        handler = getattr(self, handler_name, None)
        if not callable(handler):
            self.logger.warning("No handler for '%s'", emotion)
            return

        self.logger.info("Expressing %s", emotion)
        handler()

    # ---------------------------------------------------------------- reset/rest
    def _reset_all(self):
        if not self.nao:
            return
        if self.eye_animator:
            self.eye_animator.set_color((1.0, 1.0, 1.0))
        else:
            self._set_face((1.0, 1.0, 1.0))
        self._set_ears(0.0)
        if self._listening_enabled:
            self._set_listening_movement(False)
        self._set_basic_awareness(False)
        self._rest()

    def _rest(self):
        if not self.nao:
            return
        try:
            self.nao.autonomous.request(NaoRestRequest())
        except Exception as exc:
            self.logger.warning("Failed to rest NAO: %s", exc)

    # ------------------------------------------------------------------ emotions
    def _show_angry1(self):
        self.eye_animator.pulse(
            base_rgb=(0.35, 0.0, 0.0),
            peak_rgb=(1.0, 0.0, 0.0),
            cycles=6,
            period=0.4,
            settle_seconds=2.0,
            intensity=1.0,
        )

    def _show_angry2(self):
        self._set_face((0.9, 0.15, 0.0), duration=0.05)

    def _show_fear(self):
        self._set_face((0.15, 0.15, 0.15), duration=0.05)

    def _show_surprise(self):
        self._set_ears(0.3)

        self.eye_animator.pulse(
            base_rgb=(0.15, 0.6, 0.8),
            peak_rgb=(0.4, 0.9, 1.0),
            cycles=5,
            period=0.3,
            settle_seconds=0.5,
            intensity=1.0,
        )
        
        self._set_ears(0.0)

    def _show_disgust(self):
        self.eye_animator.pulse(
            base_rgb=(0.4, 0.05, 0.02),
            peak_rgb=(0.7, 0.2, 0.05),
            cycles=4,
            period=0.45,
            settle_seconds=0.5,
            intensity=0.8,
        )

    def _show_sadness(self):
        self.eye_animator.pulse(
            base_rgb=(0.02, 0.08, 0.6),
            peak_rgb=(0.08, 0.2, 0.9),
            cycles=3,
            period=1.5,
            settle_seconds=1.5,
            intensity=0.6,
        )        

    def _show_enjoyment(self):
        palette = [
            (1.0, 0.4, 0.0),   # warm orange
            (1.0, 0.6, 0.2),   # bright amber
            (0.9, 0.2, 0.6),   # magenta
            (0.3, 0.8, 0.5),   # teal
        ]
    
        for color in palette:
            self.eye_animator.set_color(color, duration=0.2)
            time.sleep(0.35)
        self.eye_animator.set_color((0.95, 0.5, 0.2))


if __name__ == "__main__":
    demo = NaoEmotionDemo()
    demo.run()

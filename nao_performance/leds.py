import random
from sic_framework.devices.common_naoqi.naoqi_leds import (
    NaoFadeRGBRequest,
    NaoSetIntensityRequest,
)
from emotion.eye_pulse_animator import EyePulseAnimator

class NaoLEDS:
    """
    Manages LED expressions for the NAO robot.
    Supports the following emotions/intents:
    - neutral
    - enjoyment
    - surprise
    - angry
    - disgust
    - sadness
    - fear
    """
    def __init__(self, nao):
        self.nao = nao
        self.eye_animator = EyePulseAnimator(self.nao)

    def enable_eyes(self):
        """Enables the face LEDs at full intensity."""
        if self.nao:
            self.nao.leds.request(NaoSetIntensityRequest("FaceLeds", 1.0))

    def express(self, emotion: str):
        """
        Expresses the given emotion using LED patterns.
        """
        if emotion == "neutral":
            self._show_neutral()
        elif emotion == "enjoyment":
            self._pick_random([self._show_enjoyment_1, self._show_enjoyment_2, self._show_enjoyment_3])
        elif emotion == "surprise":
            self._pick_random([self._show_surprise_1, self._show_surprise_2])
        elif emotion == "angry":
            self._pick_random([self._show_angry_1, self._show_angry_2, self._show_angry_3])
        elif emotion == "disgust":
            self._pick_random([self._show_disgust_1, self._show_disgust_2])
        elif emotion == "sadness":
            self._pick_random([self._show_sadness_1, self._show_sadness_2, self._show_sadness_3])
        elif emotion == "fear":
            self._pick_random([self._show_fear_1, self._show_fear_2])
        else:
            # Default to neutral for unknown emotions
            self._show_neutral()

    def _pick_random(self, methods):
        method = random.choice(methods)
        method()

    def reset(self):
        if self.eye_animator:
            self.eye_animator.set_color((1.0, 1.0, 1.0))
        self._set_ears(0.0)

    def _set_ears(self, intensity: float):
        if not self.nao:
            return
        value = max(0.0, min(1.0, intensity))
        for group in ("LeftEarLeds", "RightEarLeds"):
            self.nao.leds.request(NaoSetIntensityRequest(group, value))

    # --- Emotion Implementations ---

    def _show_neutral(self):
        # Soft/Inactive: Soft white
        self.eye_animator.set_color((0.8, 0.8, 0.8), duration=0.5)
        self._set_ears(0.0)

    # --- Enjoyment Variations (Turquoise) ---
    def _show_enjoyment_1(self):
        # Standard Turquoise
        self.eye_animator.set_color((0.25, 0.88, 0.82), duration=0.2)
        self._set_ears(0.5)

    def _show_enjoyment_2(self):
        # Brighter/Lighter Turquoise
        self.eye_animator.set_color((0.4, 1.0, 0.9), duration=0.2)
        self._set_ears(0.8)

    def _show_enjoyment_3(self):
        # Pulsing Turquoise (Excitement)
        self.eye_animator.pulse(
            base_rgb=(0.2, 0.7, 0.7),
            peak_rgb=(0.4, 1.0, 1.0),
            cycles=2,
            period=0.5,
            settle_seconds=1.0,
            intensity=1.0,
        )
        self._set_ears(1.0)

    # --- Surprise Variations (Turquoise) ---
    def _show_surprise_1(self):
        # Fast Pulse
        self.eye_animator.pulse(
            base_rgb=(0.0, 0.8, 0.8),
            peak_rgb=(0.5, 1.0, 1.0),
            cycles=3,
            period=0.2,
            settle_seconds=1.0,
            intensity=1.0,
        )
        self._set_ears(1.0)

    def _show_surprise_2(self):
        # Sudden Bright Flash then fade
        self.eye_animator.set_color((0.6, 1.0, 1.0), duration=0.1)
        self._set_ears(1.0)

    # --- Angry Variations (Red) ---
    def _show_angry_1(self):
        # Strong Pulse
        self.eye_animator.pulse(
            base_rgb=(0.5, 0.0, 0.0),
            peak_rgb=(1.0, 0.0, 0.0),
            cycles=5,
            period=0.3,
            settle_seconds=2.0,
            intensity=1.0,
        )
        self._set_ears(1.0)

    def _show_angry_2(self):
        # Solid Strong Red
        self.eye_animator.set_color((1.0, 0.0, 0.0), duration=0.1)
        self._set_ears(1.0)

    def _show_angry_3(self):
        # Slow Threatening Pulse
        self.eye_animator.pulse(
            base_rgb=(0.2, 0.0, 0.0),
            peak_rgb=(0.8, 0.0, 0.0),
            cycles=2,
            period=1.0,
            settle_seconds=2.0,
            intensity=1.0,
        )
        self._set_ears(0.8)

    # --- Disgust Variations (Red/Pinkish) ---
    def _show_disgust_1(self):
        # Softer Red
        self.eye_animator.set_color((0.6, 0.2, 0.2), duration=0.5)
        self._set_ears(0.2)

    def _show_disgust_2(self):
        # Pinkish Red
        self.eye_animator.set_color((0.7, 0.3, 0.3), duration=0.5)
        self._set_ears(0.1)

    # --- Sadness Variations (Blue) ---
    def _show_sadness_1(self):
        # Slow Pulse
        self.eye_animator.pulse(
            base_rgb=(0.0, 0.0, 0.4),
            peak_rgb=(0.0, 0.0, 0.7),
            cycles=3,
            period=1.5,
            settle_seconds=1.5,
            intensity=0.5,
        )
        self._set_ears(0.0)

    def _show_sadness_2(self):
        # Dim Static Blue
        self.eye_animator.set_color((0.0, 0.0, 0.3), duration=1.0)
        self._set_ears(0.0)

    def _show_sadness_3(self):
        # Very Deep Blue
        self.eye_animator.set_color((0.0, 0.0, 0.5), duration=1.5)
        self._set_ears(0.0)

    # --- Fear Variations (Black/Dim) ---
    def _show_fear_1(self):
        # Black (Off)
        self.eye_animator.set_color((0.0, 0.0, 0.0), duration=0.1)
        self._set_ears(0.0)

    def _show_fear_2(self):
        # Very Dim Grey (Trembling?)
        self.eye_animator.pulse(
            base_rgb=(0.0, 0.0, 0.0),
            peak_rgb=(0.1, 0.1, 0.1),
            cycles=5,
            period=0.1, # Fast tremble
            settle_seconds=0.5,
            intensity=0.1,
        )
        self._set_ears(0.0)

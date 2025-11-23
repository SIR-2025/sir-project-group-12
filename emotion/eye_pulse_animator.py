import time
from typing import Optional

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_leds import (
    NaoFadeRGBRequest,
    NaoSetIntensityRequest,
)


class EyePulseAnimator:
    """
    Reusable helper that drives NAO's eye LEDs through a color pulse.

    The default palette is deep red, but callers can pass any RGB tuples via
    `base_rgb` and `peak_rgb` to reuse the same timing/settle behavior for
    different emotions (e.g., blue for sadness, turquoise for surprise).
    """

    def __init__(self, nao: Nao):
        self.nao = nao

    def pulse(
        self,
        *,
        base_rgb=(0.35, 0.0, 0.0),
        peak_rgb=(1.0, 0.0, 0.0),
        cycles: int = 6,
        period: float = 0.3,
        settle_seconds: float = 2.0,
        intensity: float = 1.0,
    ):
        """Bring the eyes to red, pulse them, and leave them steady again."""
        self._set_intensity("FaceLeds", intensity)
        self._fade_group("FaceLeds", peak_rgb)
        self._pulse_color("FaceLeds", base_rgb, peak_rgb, cycles, period)
        self._fade_group("FaceLeds", peak_rgb)
        if settle_seconds > 0:
            time.sleep(settle_seconds)

    def set_color(self, rgb, duration: float = 0.0):
        """Expose a safe way for callers to set the face LEDs."""
        self._fade_group("FaceLeds", rgb, duration)

    # ---------------------------------------------------------------- helpers
    def _set_intensity(self, name: str, value: float):
        value = max(0.0, min(1.0, value))
        self.nao.leds.request(NaoSetIntensityRequest(name, value))

    def _fade_group(self, name: str, rgb, duration: float = 0.0):
        r, g, b = rgb
        self.nao.leds.request(NaoFadeRGBRequest(name, r, g, b, duration))

    def _pulse_color(self, name: str, low_rgb, high_rgb, cycles: int, period: float):
        if cycles <= 0:
            return

        half_period = max(period, 0.1) / 2.0
        for _ in range(cycles):
            self._fade_group(name, low_rgb, duration=half_period / 2.0)
            self._fade_group(name, high_rgb, duration=half_period / 2.0)

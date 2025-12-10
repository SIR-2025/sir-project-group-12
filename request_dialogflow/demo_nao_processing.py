# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoWakeUpRequest, NaoRestRequest
from sic_framework.devices.common_naoqi.naoqi_leds import (
    NaoFadeRGBRequest,
    NaoLEDRequest,
)
# Try to import NaoSetIntensityRequest if available
try:
    from sic_framework.devices.common_naoqi.naoqi_leds import NaoSetIntensityRequest
    HAS_INTENSITY = True
except ImportError:
    HAS_INTENSITY = False
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)

# Import libraries necessary for the demo
import time
import threading


class NaoProcessingDemo(SICApplication):
    """
    NAO processing act demo application.
    Demonstrates a "processing" act where the robot:
    - Says "processing... please wait" 3 times
    - Flashes eyes and ear LEDs white
    - Performs a thinking/processing gesture
    """

    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoProcessingDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "10.0.0.181"
        self.nao = None
        self.processing_count = 3

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the NAO robot."""
        self.logger.info("Starting NAO Processing Demo...")
        
        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip)
    
    def _set_intensity(self, name: str, value: float):
        """Set LED intensity for a given LED group."""
        value = max(0.0, min(1.0, value))
        if HAS_INTENSITY:
            try:
                self.nao.leds.request(NaoSetIntensityRequest(name, value))
            except:
                # If intensity control doesn't work, skip it
                pass
        # If intensity control is not available, we'll just use RGB values

    def _fade_group(self, name: str, rgb, duration: float = 0.0):
        """Fade LED group to specified RGB color."""
        r, g, b = rgb
        try:
            self.nao.leds.request(NaoFadeRGBRequest(name, r, g, b, duration))
        except Exception as e:
            self.logger.warning("Could not fade {} LEDs: {}".format(name, e))

    def _pulse_color(self, name: str, low_rgb, high_rgb, cycles: int, period: float):
        """Pulse LED color between low and high RGB values."""
        if cycles <= 0:
            return

        half_period = max(period, 0.1) / 2.0
        for _ in range(cycles):
            self._fade_group(name, low_rgb, duration=half_period)
            time.sleep(half_period)
            self._fade_group(name, high_rgb, duration=half_period)
            time.sleep(half_period)
    
    def _cycle_colors(self, name: str, colors: list, cycles: int, period: float):
        """Cycle LED through a list of colors."""
        if cycles <= 0 or len(colors) == 0:
            return
        
        # Calculate time per color transition
        transition_time = max(period, 0.1) / len(colors)
        
        for _ in range(cycles):
            for color in colors:
                self._fade_group(name, color, duration=transition_time)
                time.sleep(transition_time)

    def pulse(
        self,
        *,
        cycles: int = 6,
        period: float = 0.3,
        settle_seconds: float = 2.0,
        intensity: float = 1.0,
        led_groups=None
    ):
        """
        Cycle LEDs through red, green, blue, and white colors with smooth fade transitions.
        
        Args:
            cycles: Number of complete color cycles (red->green->blue->white)
            period: Period of each complete color cycle in seconds
            settle_seconds: Time to wait after cycling
            intensity: LED intensity (0.0 to 1.0)
            led_groups: List of LED group names to cycle (default: FaceLeds and ear LEDs)
        """
        if led_groups is None:
            led_groups = ["FaceLeds", "LeftEarLeds", "RightEarLeds"]
        
        # Define colors: red, green, blue, white
        colors = [
            (1.0, 0.0, 0.0),  # Red
            (0.0, 1.0, 0.0),  # Green
            (0.0, 0.0, 1.0),  # Blue
            (1.0, 1.0, 1.0),  # White
        ]
        
        for group in led_groups:
            try:
                self._set_intensity(group, intensity)
                # Start with first color
                self._fade_group(group, colors[0])
                # Cycle through colors
                self._cycle_colors(group, colors, cycles, period)
                # End with white
                self._fade_group(group, colors[-1])
            except Exception as e:
                # If a specific LED group doesn't work, try alternatives
                if group == "LeftEarLeds" or group == "RightEarLeds":
                    try:
                        # Try general EarLeds
                        if group not in ["FaceLeds"]:
                            self._set_intensity("EarLeds", intensity)
                            self._fade_group("EarLeds", colors[0])
                            self._cycle_colors("EarLeds", colors, cycles, period)
                            self._fade_group("EarLeds", colors[-1])
                    except:
                        self.logger.warning("Could not control {} LEDs, skipping".format(group))
                else:
                    self.logger.warning("Could not control {} LEDs: {}".format(group, e))
        
        if settle_seconds > 0:
            time.sleep(settle_seconds)
    
    def processing_act(self, iteration: int = 1):
        """
        Perform a single processing act:
        - Say "processing... please wait" (first 2 times) or "Processing done, story generated." (3rd time)
        - Cycle LEDs through colors
        - Perform thinking gesture
        
        Args:
            iteration: Which iteration this is (1, 2, or 3)
        """
        # Start LED color cycling in a separate thread
        led_thread = threading.Thread(
            target=self.pulse,
            kwargs={
                "cycles": 6,
                "period": 0.3,
                "settle_seconds": 0.0,  # Don't wait, let thread handle timing
                "intensity": 1.0
            }
        )
        led_thread.daemon = True
        led_thread.start()
        
        # Say different message based on iteration
        if iteration == 3:
            self.logger.info("Saying: Processing done, story generated.")
            self.nao.tts.request(NaoqiTextToSpeechRequest("Processing done, story generated."))
        else:
            self.logger.info("Saying: processing... please wait")
            self.nao.tts.request(NaoqiTextToSpeechRequest("Processing... please wait."))
        
        # Perform thinking/processing gesture (non-blocking so LEDs continue)
        # Common thinking gestures: Think_1, Think_2, or similar
        try:
            self.logger.info("Performing thinking gesture")
            self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Think_1"), block=False)
        except:
            # Fallback to a different gesture if Think_1 doesn't exist
            try:
                self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Think_2"), block=False)
            except:
                # If no thinking gesture available, use a simple gesture
                self.logger.warning("Thinking gesture not available, using alternative")
                try:
                    self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Explain_1"), block=False)
                except:
                    pass
        
        # Wait for LED thread to finish (pulse duration is approximately cycles * period)
        led_thread.join(timeout=3.0)
    
    def wakeup(self):
        """Wake up the NAO robot."""
        self.logger.info("Waking up NAO robot")
        self.nao.autonomous.request(NaoWakeUpRequest())
        time.sleep(1)
    
    def rest(self):
        """Put the NAO robot to rest and reset LEDs."""
        self.logger.info("Putting NAO robot to rest")
        # Reset LEDs to default (on)
        self.nao.leds.request(NaoLEDRequest("FaceLeds", True))
        try:
            self.nao.leds.request(NaoLEDRequest("LeftEarLeds", True))
            self.nao.leds.request(NaoLEDRequest("RightEarLeds", True))
        except:
            try:
                self.nao.leds.request(NaoLEDRequest("EarLeds", True))
            except:
                pass
        # Put robot to rest
        self.nao.autonomous.request(NaoRestRequest())
    
    def run(self):
        """Main application logic: perform processing act 3 times."""
        try:
            self.logger.info("Starting NAO Processing Demo...")
            
            # Wake up the robot
            self.wakeup()
            
            # Perform processing act multiple times
            for i in range(self.processing_count):
                iteration = i + 1
                self.logger.info("Processing act {} of {}".format(iteration, self.processing_count))
                self.processing_act(iteration=iteration)
                
                # Small pause between acts (except after the last one)
                if i < self.processing_count - 1:
                    time.sleep(0.5)
            
            self.logger.info("Processing demo completed successfully")
            
        except Exception as e:
            self.logger.error("Error in processing demo: {}".format(e))
        finally:
            self.rest()
            self.logger.info("Shutting down application")
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoProcessingDemo()
    demo.run()


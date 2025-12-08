import pygame
import time
import os

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_track = None

    def play(self, file_path, loop=True, fade_ms=1000):
        """
        Starts playing a track.
        
        Args:
            file_path (str): Path to the music file.
            loop (bool): Whether to loop the track.
            fade_ms (int): Fade-in duration in milliseconds.
        """
        if not os.path.exists(file_path):
            print(f"Error: Music file not found: {file_path}")
            return

        try:
            pygame.mixer.music.load(file_path)
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            self.current_track = file_path
            print(f"Playing music: {file_path}")
        except Exception as e:
            print(f"Error playing music: {e}")

    def stop(self, fade_ms=1000):
        """Stops playback with a fade-out."""
        pygame.mixer.music.fadeout(fade_ms)
        self.current_track = None

    def change_track(self, file_path, fade_ms=1000):
        """
        Smoothly transitions to a new track.
        
        Args:
            file_path (str): Path to the new music file.
            fade_ms (int): Fade-out/fade-in duration in milliseconds.
        """
        if self.current_track == file_path:
            return  # Already playing this track

        if pygame.mixer.music.get_busy():
            self.stop(fade_ms=fade_ms)
            # Wait for fadeout to finish (approximate)
            time.sleep(fade_ms / 1000.0)
        
        self.play(file_path, fade_ms=fade_ms)

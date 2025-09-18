"""
Audio system for the Kingdom-Pygame menu system.
Handles background music and sound effects with caching and volume control.
"""

import pygame as pg
from typing import Optional


class AudioManager:
    """Handles background music and sound effects."""
    
    def __init__(self):
        """Initialize the audio manager."""
        pg.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        pg.mixer.set_num_channels(16)  # Increase number of channels for better sound mixing
        self.current_music = None
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.music_paused = False
        self.sound_cache = {}  # Cache for sound effects
        self.burst_channel = pg.mixer.Channel(15)  # Dedicated channel for burst sounds
        
    def play_music(self, music_path: str, loop: bool = True):
        """Play background music."""
        if self.current_music != music_path:
            try:
                pg.mixer.music.load(music_path)
                pg.mixer.music.set_volume(self.music_volume)
                pg.mixer.music.play(-1 if loop else 0)
                self.current_music = music_path
                print(f"Playing music: {music_path}")
            except Exception as e:
                print(f"Could not load music {music_path}: {e}")
    
    def stop_music(self):
        """Stop background music."""
        pg.mixer.music.stop()
        self.current_music = None
    
    def pause_music(self):
        """Pause background music."""
        pg.mixer.music.pause()
        self.music_paused = True
    
    def resume_music(self):
        """Resume background music."""
        pg.mixer.music.unpause()
        self.music_paused = False
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        pg.mixer.music.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def load_sound(self, sound_path: str) -> Optional[pg.mixer.Sound]:
        """Load and cache a sound effect."""
        if sound_path in self.sound_cache:
            return self.sound_cache[sound_path]
        
        try:
            # Load sound and set initial volume
            sound = pg.mixer.Sound(sound_path)
            sound.set_volume(self.sfx_volume)
            self.sound_cache[sound_path] = sound
            return sound
        except Exception as e:
            print(f"Could not load sound {sound_path}: {e}")
            return None
    
    def play_sound(self, sound_path: str):
        """Play a sound effect."""
        sound = self.load_sound(sound_path)
        if sound:
            # Find an available channel and play
            channel = pg.mixer.find_channel()
            if channel:
                channel.play(sound)
    
    def play_burst_sound(self, character_name: str):
        """Play a character's burst sound using the dedicated channel."""
        burst_sound_path = f"assets/sounds/voices/{character_name.lower()}_burst.wav"
        sound = self.load_sound(burst_sound_path)
        if sound:
            # Use dedicated burst channel
            self.burst_channel.play(sound)
        else:
            print(f"Burst sound not found for {character_name}")
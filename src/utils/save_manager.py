"""
Game Save/Load System for S.A.C.K. BATTLE: A NIKKE FAN GAME
Handles save slots, player progress, settings persistence, and character unlocks.
"""

import json
import os
import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path

@dataclass
class PlayerStats:
    """Player statistics that are saved."""
    total_playtime: float = 0.0
    total_kills: int = 0
    highest_wave: int = 0
    highest_score: int = 0
    games_played: int = 0
    characters_unlocked: List[str] = None
    favorite_character: str = ""
    
    def __post_init__(self):
        if self.characters_unlocked is None:
            # Default unlocked characters (first 3)
            self.characters_unlocked = ["cecil", "commander", "crown"]

@dataclass 
class GameSettings:
    """Game settings that are saved."""
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    resolution: str = "1920x1080"
    fullscreen: bool = False
    key_bindings: Dict[str, int] = None
    
    def __post_init__(self):
        if self.key_bindings is None:
            import pygame as pg
            self.key_bindings = {
                "move_up": pg.K_w,
                "move_down": pg.K_s,
                "move_left": pg.K_a,
                "move_right": pg.K_d,
                "dash": pg.K_LSHIFT,
                "burst": pg.K_e,
                "pause": pg.K_p
            }

@dataclass
class SaveSlot:
    """Individual save slot data."""
    slot_id: int
    character_name: str = ""
    level: int = 1
    score: int = 0
    wave: int = 1
    playtime: float = 0.0
    save_date: str = ""
    is_empty: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SaveSlot':
        """Create from dictionary."""
        return cls(**data)

class GameSaveManager:
    """Manages game saves, settings, and player progress."""
    
    def __init__(self):
        """Initialize the save manager."""
        self.save_dir = Path("saves")
        self.settings_file = self.save_dir / "settings.json"
        self.stats_file = self.save_dir / "player_stats.json"
        self.save_slots_file = self.save_dir / "save_slots.json"
        
        # Ensure save directory exists
        self.save_dir.mkdir(exist_ok=True)
        
        # Initialize data
        self.settings = GameSettings()
        self.player_stats = PlayerStats()
        self.save_slots: Dict[int, SaveSlot] = {}
        
        # Initialize save slots (1-5)
        for i in range(1, 6):
            self.save_slots[i] = SaveSlot(slot_id=i)
        
        # Load existing data
        self.load_settings()
        self.load_player_stats()
        self.load_save_slots()
    
    def save_settings(self):
        """Save game settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(asdict(self.settings), f, indent=2)
            print("Settings saved successfully")
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def load_settings(self):
        """Load game settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.settings = GameSettings(**data)
                print("Settings loaded successfully")
        except Exception as e:
            print(f"Failed to load settings: {e}")
            self.settings = GameSettings()  # Use defaults
    
    def save_player_stats(self):
        """Save player statistics to file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(asdict(self.player_stats), f, indent=2)
            print("Player stats saved successfully")
        except Exception as e:
            print(f"Failed to save player stats: {e}")
    
    def load_player_stats(self):
        """Load player statistics from file."""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.player_stats = PlayerStats(**data)
                print("Player stats loaded successfully")
        except Exception as e:
            print(f"Failed to load player stats: {e}")
            self.player_stats = PlayerStats()  # Use defaults
    
    def save_save_slots(self):
        """Save all save slots to file."""
        try:
            slots_data = {str(k): v.to_dict() for k, v in self.save_slots.items()}
            with open(self.save_slots_file, 'w') as f:
                json.dump(slots_data, f, indent=2)
            print("Save slots saved successfully")
        except Exception as e:
            print(f"Failed to save save slots: {e}")
    
    def load_save_slots(self):
        """Load save slots from file."""
        try:
            if self.save_slots_file.exists():
                with open(self.save_slots_file, 'r') as f:
                    data = json.load(f)
                    for slot_id_str, slot_data in data.items():
                        slot_id = int(slot_id_str)
                        self.save_slots[slot_id] = SaveSlot.from_dict(slot_data)
                print("Save slots loaded successfully")
        except Exception as e:
            print(f"Failed to load save slots: {e}")
    
    def create_save(self, slot_id: int, character_name: str, score: int, wave: int, playtime: float):
        """Create a new save in the specified slot."""
        if slot_id not in self.save_slots:
            print(f"Invalid slot ID: {slot_id}")
            return False
        
        save_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        self.save_slots[slot_id] = SaveSlot(
            slot_id=slot_id,
            character_name=character_name,
            score=score,
            wave=wave,
            playtime=playtime,
            save_date=save_date,
            is_empty=False
        )
        
        self.save_save_slots()
        print(f"Game saved to slot {slot_id}")
        return True
    
    def load_save(self, slot_id: int) -> Optional[SaveSlot]:
        """Load a save from the specified slot."""
        if slot_id not in self.save_slots:
            print(f"Invalid slot ID: {slot_id}")
            return None
        
        slot = self.save_slots[slot_id]
        if slot.is_empty:
            print(f"Slot {slot_id} is empty")
            return None
        
        print(f"Loaded save from slot {slot_id}")
        return slot
    
    def delete_save(self, slot_id: int):
        """Delete a save from the specified slot."""
        if slot_id not in self.save_slots:
            print(f"Invalid slot ID: {slot_id}")
            return False
        
        self.save_slots[slot_id] = SaveSlot(slot_id=slot_id)  # Reset to empty
        self.save_save_slots()
        print(f"Deleted save from slot {slot_id}")
        return True
    
    def get_save_slots(self) -> Dict[int, SaveSlot]:
        """Get all save slots."""
        return self.save_slots.copy()
    
    def update_player_stats(self, score: int, wave: int, kills: int, playtime: float, character: str):
        """Update player statistics after a game."""
        self.player_stats.total_playtime += playtime
        self.player_stats.total_kills += kills
        self.player_stats.games_played += 1
        
        if wave > self.player_stats.highest_wave:
            self.player_stats.highest_wave = wave
        
        if score > self.player_stats.highest_score:
            self.player_stats.highest_score = score
        
        if character:
            self.player_stats.favorite_character = character
        
        self.save_player_stats()
    
    def unlock_character(self, character_id: str):
        """Unlock a character."""
        if character_id not in self.player_stats.characters_unlocked:
            self.player_stats.characters_unlocked.append(character_id)
            self.save_player_stats()
            print(f"Character unlocked: {character_id}")
            return True
        return False
    
    def is_character_unlocked(self, character_id: str) -> bool:
        """Check if a character is unlocked."""
        return character_id in self.player_stats.characters_unlocked
    
    def apply_settings(self, audio_manager, screen_manager=None):
        """Apply loaded settings to the game systems."""
        # Apply audio settings
        if audio_manager:
            audio_manager.set_music_volume(self.settings.music_volume)
            audio_manager.set_sfx_volume(self.settings.sfx_volume)
        
        # Note: Screen resolution changes would require game restart
        # This could be implemented with screen_manager if needed
        print("Settings applied to game systems")
    
    def update_settings(self, music_volume: float = None, sfx_volume: float = None, 
                       resolution: str = None, fullscreen: bool = None, 
                       key_bindings: Dict[str, int] = None):
        """Update game settings."""
        if music_volume is not None:
            self.settings.music_volume = music_volume
        if sfx_volume is not None:
            self.settings.sfx_volume = sfx_volume
        if resolution is not None:
            self.settings.resolution = resolution
        if fullscreen is not None:
            self.settings.fullscreen = fullscreen
        if key_bindings is not None:
            self.settings.key_bindings = key_bindings
        
        self.save_settings()
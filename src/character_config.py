"""
Character configuration system for loading character stats and data from JSON files.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CharacterStats:
    """Character statistics data class."""
    speed: int
    hp: int
    burst_multiplier: int

@dataclass
class SpriteInfo:
    """Sprite information data class."""
    filename: str
    frame_width: Optional[int]
    frame_height: Optional[int]
    animation_speed: float

@dataclass
class BurstAbility:
    """Burst ability data class."""
    name: str
    description: str
    damage_multiplier: float

@dataclass
class CharacterConfig:
    """Complete character configuration."""
    name: str
    display_name: str
    description: str
    weapon_name: str
    weapon_type: str
    stats: CharacterStats
    sprite_info: SpriteInfo
    burst_ability: BurstAbility

class CharacterConfigManager:
    """Manages character configuration loading and caching."""
    
    def __init__(self, characters_path: str = "assets/images/Characters"):
        """Initialize the character config manager."""
        self.characters_path = characters_path
        self.configs_cache: Dict[str, CharacterConfig] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all character configurations from their folders."""
        if not os.path.exists(self.characters_path):
            print(f"Warning: Characters path not found: {self.characters_path}")
            return
        
        try:
            # Scan for character folders
            for folder_name in os.listdir(self.characters_path):
                folder_path = os.path.join(self.characters_path, folder_name)
                
                if os.path.isdir(folder_path):
                    config_file = os.path.join(folder_path, "config.json")
                    
                    if os.path.exists(config_file):
                        config = self._load_character_config(config_file, folder_name)
                        if config:
                            self.configs_cache[folder_name] = config
                            print(f"Loaded config for: {config.display_name}")
                    else:
                        print(f"Warning: No config.json found for character: {folder_name}")
            
            print(f"Loaded {len(self.configs_cache)} character configurations")
            
        except Exception as e:
            print(f"Error scanning character configurations: {e}")
    
    def _load_character_config(self, config_path: str, folder_name: str) -> Optional[CharacterConfig]:
        """Load a single character configuration from JSON."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create CharacterStats
            stats_data = data['stats']
            stats = CharacterStats(
                speed=stats_data['speed'],
                hp=stats_data['hp'],
                burst_multiplier=stats_data['burst_multiplier']
            )
            
            # Create SpriteInfo
            sprite_data = data['sprite_info']
            sprite_info = SpriteInfo(
                filename=sprite_data['filename'],
                frame_width=sprite_data.get('frame_width'),
                frame_height=sprite_data.get('frame_height'),
                animation_speed=sprite_data['animation_speed']
            )
            
            # Create BurstAbility
            burst_data = data['burst_ability']
            burst_ability = BurstAbility(
                name=burst_data['name'],
                description=burst_data['description'],
                damage_multiplier=burst_data['damage_multiplier']
            )
            
            # Create complete configuration
            config = CharacterConfig(
                name=data['name'],
                display_name=data['display_name'],
                description=data['description'],
                weapon_name=data['weapon_name'],
                weapon_type=data['weapon_type'],
                stats=stats,
                sprite_info=sprite_info,
                burst_ability=burst_ability
            )
            
            return config
            
        except Exception as e:
            print(f"Error loading character config from {config_path}: {e}")
            return None
    
    def get_character_config(self, character_name: str) -> Optional[CharacterConfig]:
        """Get character configuration by name."""
        return self.configs_cache.get(character_name)
    
    def get_all_character_names(self) -> list[str]:
        """Get list of all available character names."""
        return list(self.configs_cache.keys())
    
    def get_character_sprite_path(self, character_name: str) -> Optional[str]:
        """Get the full path to a character's sprite file."""
        config = self.get_character_config(character_name)
        if config:
            return os.path.join(self.characters_path, character_name, config.sprite_info.filename)
        return None
    
    def get_character_display_names(self) -> Dict[str, str]:
        """Get mapping of character names to display names."""
        return {name: config.display_name for name, config in self.configs_cache.items()}

# Global instance for easy access
character_config_manager = CharacterConfigManager()
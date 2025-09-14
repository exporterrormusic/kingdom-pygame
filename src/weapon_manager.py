"""
Weapon system for the Kingdom-Pygame twin-stick shooter.
Handles loading and managing weapon configurations from weapons.json.
"""

import json
import os
from typing import Dict, Any, Optional

class WeaponManager:
    """Manages weapon configurations and properties."""
    
    def __init__(self):
        """Initialize the weapon manager."""
        self.weapon_data: Dict[str, Any] = {}
        self.load_weapons()
    
    def load_weapons(self):
        """Load weapon configurations from weapons.json."""
        weapons_path = "weapons.json"
        
        if not os.path.exists(weapons_path):
            print(f"Warning: weapons.json not found at {weapons_path}")
            return
        
        try:
            with open(weapons_path, 'r') as f:
                data = json.load(f)
                self.weapon_data = data.get('weapon_categories', {})
                print(f"Loaded {len(self.weapon_data)} weapon categories")
                
        except Exception as e:
            print(f"Error loading weapons.json: {e}")
            self.weapon_data = {}
    
    def get_weapon_config(self, weapon_type: str) -> Optional[Dict[str, Any]]:
        """Get weapon configuration by type."""
        return self.weapon_data.get(weapon_type)
    
    def get_weapon_property(self, weapon_type: str, category: str, property_name: str, default=None):
        """Get a specific weapon property by category and property name."""
        weapon_config = self.get_weapon_config(weapon_type)
        if weapon_config and category in weapon_config:
            return weapon_config[category].get(property_name, default)
        return default
    
    def get_fire_rate(self, weapon_type: str) -> float:
        """Get weapon fire rate."""
        return self.get_weapon_property(weapon_type, 'firing', 'fire_rate', 0.2)
    
    def get_magazine_size(self, weapon_type: str) -> int:
        """Get weapon magazine size."""
        return self.get_weapon_property(weapon_type, 'ammo', 'magazine_size', 30)
    
    def get_reload_time(self, weapon_type: str) -> float:
        """Get weapon reload time."""
        return self.get_weapon_property(weapon_type, 'ammo', 'reload_time', 2.0)
    
    def get_damage(self, weapon_type: str) -> int:
        """Get weapon damage."""
        return self.get_weapon_property(weapon_type, 'firing', 'damage', 25)
    
    def get_bullet_properties(self, weapon_type: str) -> Dict[str, Any]:
        """Get weapon bullet properties."""
        weapon_config = self.get_weapon_config(weapon_type)
        if weapon_config and 'bullet_properties' in weapon_config:
            bullet_props = weapon_config['bullet_properties'].copy()
            # Add range from firing properties
            if 'firing' in weapon_config and 'range' in weapon_config['firing']:
                bullet_props['range'] = weapon_config['firing']['range']
            return bullet_props
        
        # Default bullet properties
        return {
            "speed": 800,
            "size_multiplier": 1.0,
            "color": [255, 255, 255],
            "shape": "standard",
            "penetration": 1,
            "range": 800  # Default range
        }
    
    def get_weapon_range(self, weapon_type: str) -> float:
        """Get weapon range in pixels."""
        return self.get_weapon_property(weapon_type, 'firing', 'range', 800.0)
    
    def weapon_exists(self, weapon_type: str) -> bool:
        """Check if a weapon type exists in the loaded data."""
        return weapon_type in self.weapon_data
    
    def get_pellet_count(self, weapon_type: str) -> int:
        """Get number of pellets for shotgun-type weapons."""
        return self.get_weapon_property(weapon_type, 'special_mechanics', 'pellet_count', 1)
    
    def get_spread_angle(self, weapon_type: str) -> float:
        """Get spread angle for shotgun-type weapons."""
        return self.get_weapon_property(weapon_type, 'special_mechanics', 'spread_angle', 0.0)

# Global weapon manager instance
weapon_manager = WeaponManager()
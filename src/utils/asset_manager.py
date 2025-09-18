"""
Asset manager for caching and reusing game assets.
"""

import pygame as pg
from typing import Dict, Optional

class AssetManager:
    """Manages and caches game assets to prevent redundant loading."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one asset manager exists."""
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the asset manager."""
        if not AssetManager._initialized:
            self.sprite_sheets: Dict[str, pg.Surface] = {}
            self.cached_animations: Dict[str, tuple] = {}  # Cache animation frame data
            AssetManager._initialized = True
    
    def load_sprite_sheet(self, path: str) -> Optional[pg.Surface]:
        """Load and cache a sprite sheet."""
        if path in self.sprite_sheets:
            return self.sprite_sheets[path]
        
        try:
            sprite_sheet = pg.image.load(path).convert_alpha()
            self.sprite_sheets[path] = sprite_sheet
            print(f"Loaded and cached sprite sheet: {path}")
            return sprite_sheet
        except Exception as e:
            print(f"Failed to load sprite sheet {path}: {e}")
            return None
    
    def get_cached_sprite_sheet(self, path: str) -> Optional[pg.Surface]:
        """Get a cached sprite sheet without loading."""
        return self.sprite_sheets.get(path)
    
    def cache_animation_frames(self, path: str, frame_width: int, frame_height: int) -> Optional[Dict]:
        """Cache pre-sliced animation frames for better performance."""
        cache_key = f"{path}_{frame_width}_{frame_height}"
        
        # Debug: Cache hit
        if cache_key in self.cached_animations:
            return self.cached_animations[cache_key]
        
        sprite_sheet = self.load_sprite_sheet(path)
        if not sprite_sheet:
            return None
        
        # Animation states mapping
        animations = {
            'down': 0,   # Row 0
            'left': 1,   # Row 1  
            'right': 2,  # Row 2
            'up': 3      # Row 3
        }
        
        frames = {}
        for animation_name, row in animations.items():
            frame_list = []
            for col in range(3):  # 3 frames per animation
                # Calculate frame position
                x = col * frame_width
                y = row * frame_height
                
                # Extract frame
                frame_rect = pg.Rect(x, y, frame_width, frame_height)
                frame = sprite_sheet.subsurface(frame_rect).copy()
                frame_list.append(frame)
            
            frames[animation_name] = frame_list
        
        self.cached_animations[cache_key] = frames
        print(f"Cached animation frames for: {path}")
        print(f"Frame data: {len(frames)} animations, each with {len(frames.get('down', []))} frames")
        return frames
    
    def clear_cache(self):
        """Clear all cached assets."""
        self.sprite_sheets.clear()
        self.cached_animations.clear()
        print("Asset cache cleared")

# Global asset manager instance
asset_manager = AssetManager()
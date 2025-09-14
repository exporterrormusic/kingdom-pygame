"""
Sprite animation system with asset caching for optimal performance.
Supports 3x4 grid format with DOWN, LEFT, RIGHT, UP animations.
"""

import pygame as pg
from typing import Dict, List, Tuple
import os

try:
    from src.asset_manager import asset_manager
except ImportError:
    try:
        from asset_manager import asset_manager
    except ImportError:
        asset_manager = None

class SpriteAnimation:
    """Handles sprite sheet animations with automatic frame slicing."""
    
    def __init__(self, sprite_sheet_path: str, frame_width: int, frame_height: int, 
                 animation_speed: float = 0.15, scale_factor: float = 0.2):
        """
        Initialize sprite animation from a 3x4 grid sprite sheet.
        
        Args:
            sprite_sheet_path: Path to the sprite sheet image
            frame_width: Width of each frame in pixels
            frame_height: Height of each frame in pixels
            animation_speed: Time between frames in seconds
            scale_factor: Scale factor for rendering (default 0.2 = 1/5 size)
        """
        self.sprite_sheet_path = sprite_sheet_path
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.animation_speed = animation_speed
        self.scale_factor = scale_factor
        
        # Animation states mapping (needed by other methods)
        self.animations = {
            'down': 0,   # Row 0
            'left': 1,   # Row 1  
            'right': 2,  # Row 2
            'up': 3      # Row 3
        }
        
        # Try to use cached assets first
        if asset_manager:
            self.frames = asset_manager.cache_animation_frames(sprite_sheet_path, frame_width, frame_height)
            if self.frames is None:
                raise Exception(f"Failed to load sprite sheet: {sprite_sheet_path}")
        else:
            # Fallback to original loading method
            self.sprite_sheet = pg.image.load(sprite_sheet_path).convert_alpha()
            self.frames = self._slice_sprite_sheet()
        
        # Current animation state
        self.current_animation = 'down'
        self.current_frame = 0
        self.frame_timer = 0.0
        self.is_playing = False
        self.reverse_playback = False  # New: for reverse animation
    
    def _slice_sprite_sheet(self) -> Dict[str, List[pg.Surface]]:
        """Slice the sprite sheet into individual frames (fallback method)."""
        frames = {}
        
        # Animation states mapping
        animations = {
            'down': 0,   # Row 0
            'left': 1,   # Row 1  
            'right': 2,  # Row 2
            'up': 3      # Row 3
        }
        
        for animation_name, row in animations.items():
            frame_list = []
            for col in range(3):  # 3 frames per animation
                # Calculate frame position
                x = col * self.frame_width
                y = row * self.frame_height
                
                # Extract frame
                frame_rect = pg.Rect(x, y, self.frame_width, self.frame_height)
                frame = self.sprite_sheet.subsurface(frame_rect).copy()
                frame_list.append(frame)
            
            frames[animation_name] = frame_list
        
        return frames
    
    def play_animation(self, animation_name: str, reverse: bool = False):
        """Start playing a specific animation."""
        if animation_name in self.animations and (animation_name != self.current_animation or reverse != self.reverse_playback):
            self.current_animation = animation_name
            self.reverse_playback = reverse
            self.current_frame = 2 if reverse else 0  # Start from end if reverse
            self.frame_timer = 0.0
        self.is_playing = True
    
    def pause_animation(self):
        """Pause animation at current frame."""
        self.is_playing = False
    
    def show_first_frame(self, animation_name: str):
        """Show only the first frame of an animation (for idle states)."""
        if animation_name in self.animations:
            self.current_animation = animation_name
            self.current_frame = 0
            self.is_playing = False
            self.reverse_playback = False
    
    def stop_animation(self):
        """Stop the current animation."""
        self.is_playing = False
        self.current_frame = 0
        self.frame_timer = 0.0
    
    def update(self, dt: float):
        """Update animation frame based on time."""
        if not self.is_playing:
            return
        
        self.frame_timer += dt
        
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0.0
            
            if self.reverse_playback:
                # Play in reverse
                self.current_frame = (self.current_frame - 1) % 3
            else:
                # Play forward
                self.current_frame = (self.current_frame + 1) % 3
    
    def get_current_frame(self) -> pg.Surface:
        """Get the current animation frame."""
        return self.frames[self.current_animation][self.current_frame]
    
    def get_scaled_dimensions(self):
        """Get the scaled dimensions of frames."""
        return int(self.frame_width * self.scale_factor), int(self.frame_height * self.scale_factor)
    
    def render(self, screen: pg.Surface, x: int, y: int, offset=(0, 0)):
        """Render the current frame at the specified position."""
        frame = self.get_current_frame()
        
        if frame is None:
            print(f"Warning: No frame to render for animation '{self.current_animation}' frame {self.current_frame}")
            return
        
        # Scale frame using the configured scale factor
        scaled_width = int(self.frame_width * self.scale_factor)
        scaled_height = int(self.frame_height * self.scale_factor)
        scaled_frame = pg.transform.scale(frame, (scaled_width, scaled_height))
        
        render_x = x + offset[0] - scaled_width // 2
        render_y = y + offset[1] - scaled_height // 2
        
        screen.blit(scaled_frame, (render_x, render_y))

class AnimatedSprite:
    """A sprite with animation capabilities."""
    
    def __init__(self, sprite_sheet_path: str, x: float, y: float, 
                 frame_width: int, frame_height: int, animation_speed: float = 0.15, scale_factor: float = 0.2):
        """Initialize an animated sprite."""
        self.pos = pg.Vector2(x, y)
        self.animation = SpriteAnimation(sprite_sheet_path, frame_width, frame_height, animation_speed, scale_factor)
        self.last_direction = 'down'
        self.is_moving = False
    
    def update(self, dt: float, velocity: pg.Vector2 = None, facing_angle: float = None):
        """Update sprite position and animation."""
        # Update position if velocity is provided
        if velocity and velocity.length() > 0:
            self.pos += velocity * dt
            self.is_moving = True
        else:
            self.is_moving = False
        
        # Determine animation direction based on facing angle if provided
        if facing_angle is not None:
            import math
            # Convert angle to direction (angle is in radians)
            angle_degrees = math.degrees(facing_angle) % 360
            
            if angle_degrees >= 315 or angle_degrees < 45:
                facing_direction = 'right'
            elif angle_degrees >= 45 and angle_degrees < 135:
                facing_direction = 'down'  
            elif angle_degrees >= 135 and angle_degrees < 225:
                facing_direction = 'left'
            else:
                facing_direction = 'up'
            
            self.last_direction = facing_direction
            
            # Determine if moving in the same or opposite direction
            if self.is_moving and velocity:
                # Calculate movement direction
                if abs(velocity.x) > abs(velocity.y):
                    movement_direction = 'right' if velocity.x > 0 else 'left'
                else:
                    movement_direction = 'down' if velocity.y > 0 else 'up'
                
                # Check if moving backwards (opposite to facing direction)
                opposite_directions = {
                    'up': 'down', 'down': 'up',
                    'left': 'right', 'right': 'left'
                }
                
                is_moving_backwards = movement_direction == opposite_directions.get(facing_direction, '')
                
                # Play animation (forward or reverse)
                self.animation.play_animation(facing_direction, reverse=is_moving_backwards)
            else:
                # Not moving - show first frame of facing direction
                self.animation.show_first_frame(facing_direction)
        else:
            # Fallback: use movement direction if no facing angle provided
            if self.is_moving and velocity and velocity.length() > 0:
                if abs(velocity.x) > abs(velocity.y):
                    direction = 'right' if velocity.x > 0 else 'left'
                else:
                    direction = 'down' if velocity.y > 0 else 'up'
                
                self.last_direction = direction
                self.animation.play_animation(direction)
            else:
                # Show first frame of last direction
                self.animation.show_first_frame(self.last_direction)
        
        # Update animation
        self.animation.update(dt)
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render the animated sprite."""
        self.animation.render(screen, int(self.pos.x), int(self.pos.y), offset)
    
    def set_position(self, x: float, y: float):
        """Set sprite position."""
        self.pos.x = x
        self.pos.y = y
    
    def get_rect(self) -> pg.Rect:
        """Get sprite bounding rectangle for collision detection."""
        scaled_width, scaled_height = self.animation.get_scaled_dimensions()
        return pg.Rect(
            self.pos.x - scaled_width // 2,
            self.pos.y - scaled_height // 2,
            scaled_width,
            scaled_height
        )

# Utility function to create animated sprites
def create_animated_sprite(sprite_sheet_path: str, x: float, y: float, 
                          frame_width: int, frame_height: int, 
                          animation_speed: float = 0.15) -> AnimatedSprite:
    """
    Convenience function to create an animated sprite.
    
    Args:
        sprite_sheet_path: Path to sprite sheet (relative to assets/images/)
        x, y: Initial position
        frame_width, frame_height: Size of each frame
        animation_speed: Animation speed in seconds per frame
    
    Returns:
        AnimatedSprite instance
    """
    # Construct full path
    full_path = os.path.join("assets", "images", sprite_sheet_path)
    return AnimatedSprite(full_path, x, y, frame_width, frame_height, animation_speed)
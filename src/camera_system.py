"""
Camera system for the twin-stick shooter game.
Handles camera movement, zoom, shake effects, and world bounds.
"""

import pygame as pg
import random


class CameraSystem:
    """Manages camera position, zoom, shake effects and world bounds."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize the camera system."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Camera position (world coordinates)
        self.camera_x = 0.0
        self.camera_y = 0.0
        
        # Camera shake
        self.camera_shake_intensity = 0.0
        self.camera_shake_duration = 0.0
        self.camera_offset = pg.Vector2(0, 0)
        
        # Zoom system
        self.base_zoom = 1.0
        self.zoom_level = 1.0
        self.target_zoom = 1.0
        self.zoom_speed = 5.0
        
        # Delta time for smooth movements
        self.dt = 0.016  # Default 60fps
        
    def add_camera_shake(self, intensity: float, duration: float):
        """Add camera shake effect."""
        self.camera_shake_intensity = max(self.camera_shake_intensity, intensity)
        self.camera_shake_duration = max(self.camera_shake_duration, duration)
    
    def update_camera_shake(self, dt: float):
        """Update camera shake effect."""
        if self.camera_shake_duration > 0:
            self.camera_shake_duration -= dt
            
            # Calculate shake offset
            shake_amount = self.camera_shake_intensity * (self.camera_shake_duration / 0.5)
            self.camera_offset.x = random.uniform(-shake_amount, shake_amount)
            self.camera_offset.y = random.uniform(-shake_amount, shake_amount)
            
            if self.camera_shake_duration <= 0:
                self.camera_offset = pg.Vector2(0, 0)
        else:
            self.camera_offset = pg.Vector2(0, 0)
            
    def update_camera(self, player):
        """Update camera position to follow player with smooth interpolation and subtle lead."""
        if player:
            # Calculate target camera position with subtle lead
            lead_distance = 50.0  # How far ahead to look
            movement_velocity = player.velocity if hasattr(player, 'velocity') else pg.Vector2(0, 0)
            
            # Only apply lead if player is moving
            if movement_velocity.length() > 10:  # Minimum movement threshold
                lead_direction = movement_velocity.normalize()
                target_x = player.pos.x + lead_direction.x * lead_distance
                target_y = player.pos.y + lead_direction.y * lead_distance
            else:
                # No movement, center on player
                target_x = player.pos.x
                target_y = player.pos.y
            
            # Smooth camera interpolation (lerp)
            smooth_factor = 3.0  # Higher = more responsive, lower = smoother
            self.camera_x += (target_x - self.camera_x) * smooth_factor * self.dt
            self.camera_y += (target_y - self.camera_y) * smooth_factor * self.dt
            
            # Clamp camera to stay within world bounds considering screen size and zoom
            half_screen_width = (self.screen_width / self.base_zoom) / 2
            half_screen_height = (self.screen_height / self.base_zoom) / 2
            
            # Rectangular world bounds with 100-pixel visible border
            world_min_x, world_min_y = -1920, -1080
            world_max_x, world_max_y = 1920, 1080
            border_size = 100
            
            # Clamp camera position
            self.camera_x = max(world_min_x - border_size + half_screen_width, 
                              min(world_max_x + border_size - half_screen_width, self.camera_x))
            self.camera_y = max(world_min_y - border_size + half_screen_height, 
                              min(world_max_y + border_size - half_screen_height, self.camera_y))
    
    def handle_zoom_input(self, keys):
        """Handle zoom input from keyboard."""
        if keys[pg.K_EQUALS] or keys[pg.K_PLUS]:  # Zoom in
            self.target_zoom = min(3.0, self.target_zoom + 0.02)
        elif keys[pg.K_MINUS]:  # Zoom out
            self.target_zoom = max(0.5, self.target_zoom - 0.02)
            
        # Smooth zoom transition
        zoom_diff = self.target_zoom - self.zoom_level
        self.zoom_level += zoom_diff * self.zoom_speed * self.dt
    
    def get_world_camera_offset(self):
        """
        Get the camera offset for world coordinates.
        This is the offset to apply to world objects for screen positioning.
        """
        # Basic camera offset (world center to screen center)
        offset_x = self.screen_width // 2 - self.camera_x
        offset_y = self.screen_height // 2 - self.camera_y
        
        # Add shake offset
        offset_x += self.camera_offset.x
        offset_y += self.camera_offset.y
        
        return (offset_x, offset_y)
    
    def calculate_offset(self):
        """Legacy method for compatibility."""
        return self.get_world_camera_offset()
    
    def screen_to_world_pos(self, screen_pos):
        """Convert screen coordinates to world coordinates."""
        camera_offset = self.get_world_camera_offset()
        world_x = screen_pos[0] - camera_offset[0]
        world_y = screen_pos[1] - camera_offset[1]
        
        return (world_x + self.camera_x - self.screen_width // 2,
                world_y + self.camera_y - self.screen_height // 2)
    
    def world_to_screen_pos(self, world_pos):
        """Convert world coordinates to screen coordinates."""
        camera_offset = self.get_world_camera_offset()
        screen_x = world_pos[0] + camera_offset[0]
        screen_y = world_pos[1] + camera_offset[1]
        return (screen_x, screen_y)
    
    def update(self, dt: float, player):
        """Update camera system."""
        self.dt = dt
        self.update_camera_shake(dt)
        self.update_camera(player)
    
    def is_visible(self, world_x: float, world_y: float, size: float = 0) -> bool:
        """Check if a world position is visible on screen (with optional size margin)."""
        screen_pos = self.world_to_screen_pos((world_x, world_y))
        margin = size
        
        return (-margin <= screen_pos[0] <= self.screen_width + margin and 
                -margin <= screen_pos[1] <= self.screen_height + margin)
"""
Player class for the twin-stick shooter game.
Handles player movement, rotation, and rendering.
"""

import pygame as pg
import math
from typing import Tuple

class Player:
    """Player class with twi        # Dra        pg.draw.circle(screen, outline_color, (render_x, render_y), self.size, 2)
        
        # Draw V-shaped aiming arrow around the player sprite
        angle_rad = math.radians(self.angle)
        
        # Calculate distance from player center (circles around sprite)
        arrow_distance = self.size + 25  # Further out from sprite
        
        # Main arrow tip position
        tip_x = render_x + math.cos(angle_rad) * arrow_distance
        tip_y = render_y + math.sin(angle_rad) * arrow_distance
        
        # Calculate V-shape arrow points
        arrow_length = 20
        arrow_width = math.radians(25)  # 25 degree angle for V-shape
        
        # Left wing of the V
        left_angle = angle_rad + arrow_width
        left_x = tip_x - math.cos(left_angle) * arrow_length
        left_y = tip_y - math.sin(left_angle) * arrow_length
        
        # Right wing of the V
        right_angle = angle_rad - arrow_width
        right_x = tip_x - math.cos(right_angle) * arrow_length
        right_y = tip_y - math.sin(right_angle) * arrow_length
        
        # Arrow colors - more visually impressive
        arrow_color = (255, 255, 100) if self.is_dashing else (255, 200, 100)  # Golden/yellow
        arrow_outline = (255, 255, 255)
        
        # Draw V-shaped arrow with outline for better visibility
        # Outline (thicker, white)
        pg.draw.line(screen, arrow_outline, (tip_x, tip_y), (left_x, left_y), 5)
        pg.draw.line(screen, arrow_outline, (tip_x, tip_y), (right_x, right_y), 5)
        
        # Main arrow (thinner, colored)
        pg.draw.line(screen, arrow_color, (tip_x, tip_y), (left_x, left_y), 3)
        pg.draw.line(screen, arrow_color, (tip_x, tip_y), (right_x, right_y), 3)
        
        # Optional: Add a small circle at the arrow tip for better visibility
        pg.draw.circle(screen, arrow_color, (int(tip_x), int(tip_y)), 3)
        pg.draw.circle(screen, arrow_outline, (int(tip_x), int(tip_y)), 3, 1)
        
        # Draw health bar above player (scaled for larger resolution)ndicator (gun barrel)
        gun_length = self.size + 10
        angle_rad = math.radians(self.angle)
        
        end_x = render_x + math.cos(angle_rad) * gun_length
        end_y = render_y + math.sin(angle_rad) * gun_length
        
        barrel_color = (255, 255, 255) if self.is_dashing else (255, 255, 255)
        pg.draw.line(screen, barrel_color, (render_x, render_y), (end_x, end_y), 3)
        
        # Draw health bar above player (scaled for larger resolution)
        if self.health < self.max_health:
            bar_width = 60  # Increased from 40
            bar_height = 8   # Increased from 6
            bar_x = render_x - bar_width // 2
            bar_y = render_y - self.size - 15controls."""
    
    def __init__(self, x: float, y: float):
        """Initialize the player."""
        self.pos = pg.Vector2(x, y)
        self.velocity = pg.Vector2(0, 0)
        self.angle = 0.0  # Facing direction in degrees
        
        # Player stats
        self.speed = 200  # pixels per second
        self.size = 20
        self.max_health = 100
        self.health = self.max_health
        
        # Dash mechanics
        self.dash_distance = 150  # pixels to dash
        self.is_dashing = False
        self.dash_duration = 0.15  # seconds
        self.dash_timer = 0.0
        self.dash_velocity = pg.Vector2(0, 0)
        self.shift_pressed = False  # Track shift key state for single-press detection
        
        # Visual properties
        self.color = (100, 150, 255)  # Light blue
        self.body_color = (80, 120, 200)
        self.dash_color = (255, 255, 255)  # White when dashing
        
        # Hit flash effect
        self.hit_flash_duration = 0.0
        self.hit_flash_timer = 0.0
        self.flash_color = (255, 50, 50)  # Red flash color
        
        # Input state
        self.move_keys = {
            'up': False,
            'down': False,
            'left': False,
            'right': False
        }
    
    def handle_input(self, keys_pressed: dict, mouse_pos: Tuple[int, int], current_time: float, effects_manager=None, camera_shake_callback=None):
        """Handle player input for twin-stick controls."""
        # Movement input (WASD or arrow keys)
        self.move_keys['up'] = keys_pressed[pg.K_w] or keys_pressed[pg.K_UP]
        self.move_keys['down'] = keys_pressed[pg.K_s] or keys_pressed[pg.K_DOWN]
        self.move_keys['left'] = keys_pressed[pg.K_a] or keys_pressed[pg.K_LEFT]
        self.move_keys['right'] = keys_pressed[pg.K_d] or keys_pressed[pg.K_RIGHT]
        
        # Dash input (Shift key) - only trigger once per press
        shift_currently_pressed = keys_pressed[pg.K_LSHIFT] or keys_pressed[pg.K_RSHIFT]
        if shift_currently_pressed and not self.shift_pressed:
            # Shift was just pressed (not held)
            self.try_dash(current_time, effects_manager, camera_shake_callback)
        self.shift_pressed = shift_currently_pressed
        
        # Mouse aiming - calculate angle to mouse cursor
        if mouse_pos:
            dx = mouse_pos[0] - self.pos.x
            dy = mouse_pos[1] - self.pos.y
            self.angle = math.degrees(math.atan2(dy, dx))
    
    def try_dash(self, current_time: float, effects_manager=None, camera_shake_callback=None):
        """Attempt to dash if player is moving and not already dashing."""
        if not self.is_dashing and self.has_movement_input():
            # Calculate dash direction from current movement input
            dash_direction = pg.Vector2(0, 0)
            
            if self.move_keys['up']:
                dash_direction.y -= 1
            if self.move_keys['down']:
                dash_direction.y += 1
            if self.move_keys['left']:
                dash_direction.x -= 1
            if self.move_keys['right']:
                dash_direction.x += 1
            
            # Normalize for diagonal dashes
            if dash_direction.length() > 0:
                dash_direction = dash_direction.normalize()
                
                # Start dash
                self.is_dashing = True
                self.dash_timer = 0.0
                
                # Calculate dash velocity for smooth movement
                dash_speed = self.dash_distance / self.dash_duration
                self.dash_velocity = dash_direction * dash_speed
                
                # Add dash effect if effects manager is provided
                if effects_manager:
                    effects_manager.add_dash_effect(self.pos.x, self.pos.y, dash_direction)
                
                # Add slight camera shake for dash
                if camera_shake_callback:
                    camera_shake_callback(5.0, 0.2)  # Light shake for dash
    
    def has_movement_input(self) -> bool:
        """Check if player is pressing any movement keys."""
        return any(self.move_keys.values())
    
    def update(self, dt: float):
        """Update player state."""
        # Update hit flash effect
        self.update_hit_flash(dt)
        
        # Update dash state
        if self.is_dashing:
            self.dash_timer += dt
            if self.dash_timer >= self.dash_duration:
                # End dash
                self.is_dashing = False
                self.dash_timer = 0.0
                self.dash_velocity = pg.Vector2(0, 0)
        
        # Calculate movement vector
        if self.is_dashing:
            # Use dash velocity during dash
            self.velocity = self.dash_velocity
        else:
            # Normal movement
            movement = pg.Vector2(0, 0)
            
            if self.move_keys['up']:
                movement.y -= 1
            if self.move_keys['down']:
                movement.y += 1
            if self.move_keys['left']:
                movement.x -= 1
            if self.move_keys['right']:
                movement.x += 1
            
            # Normalize diagonal movement
            if movement.length() > 0:
                movement = movement.normalize()
            
            # Apply movement
            self.velocity = movement * self.speed
        
        # Update position
        self.pos += self.velocity * dt
        
        # Keep player on screen (using updated screen dimensions)
        self.pos.x = max(self.size, min(1920 - self.size, self.pos.x))
        self.pos.y = max(self.size, min(1080 - self.size, self.pos.y))
    
    def get_gun_tip_position(self) -> pg.Vector2:
        """Get the position where bullets should spawn from."""
        # Calculate the tip of the "gun" based on facing direction
        gun_length = self.size + 60  # Increased from 35 to 60 for better separation from sprite
        angle_rad = math.radians(self.angle)
        
        tip_x = self.pos.x + math.cos(angle_rad) * gun_length
        tip_y = self.pos.y + math.sin(angle_rad) * gun_length
        
        return pg.Vector2(tip_x, tip_y)
    
    def add_hit_flash(self):
        """Add red flash effect when player is hit."""
        self.hit_flash_duration = 0.3  # Flash duration in seconds
        self.hit_flash_timer = 0.0
    
    def update_hit_flash(self, dt: float):
        """Update hit flash effect."""
        if self.hit_flash_duration > 0:
            self.hit_flash_timer += dt
            if self.hit_flash_timer >= self.hit_flash_duration:
                self.hit_flash_duration = 0.0
                self.hit_flash_timer = 0.0
    
    def render(self, screen: pg.Surface, current_time: float = 0.0, offset=(0, 0)):
        """Render the player."""
        # Apply camera offset
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        # Choose colors based on state
        body_color = self.dash_color if self.is_dashing else self.body_color
        outline_color = (255, 255, 255) if self.is_dashing else self.color
        
        # Apply hit flash effect
        if self.hit_flash_duration > 0:
            # Flash red when hit
            flash_intensity = 1.0 - (self.hit_flash_timer / self.hit_flash_duration)
            body_color = (
                int(self.flash_color[0] * flash_intensity + body_color[0] * (1 - flash_intensity)),
                int(self.flash_color[1] * flash_intensity + body_color[1] * (1 - flash_intensity)),
                int(self.flash_color[2] * flash_intensity + body_color[2] * (1 - flash_intensity))
            )
        
        # Draw player body (circle)
        pg.draw.circle(screen, body_color, (render_x, render_y), self.size)
        pg.draw.circle(screen, outline_color, (render_x, render_y), self.size, 2)
        
        # Draw dash trail effect when dashing
        if self.is_dashing:
            # Create a trailing effect
            trail_alpha = 0.3
            for i in range(3):
                trail_size = self.size - (i * 3)
                if trail_size > 0:
                    trail_surface = pg.Surface((trail_size * 2, trail_size * 2), pg.SRCALPHA)
                    trail_color = (*outline_color, int(255 * trail_alpha * (1 - i * 0.3)))
                    pg.draw.circle(trail_surface, trail_color, (trail_size, trail_size), trail_size)
                    screen.blit(trail_surface, (render_x - trail_size, render_y - trail_size))
        
        # Draw direction indicator (gun barrel)
        gun_length = self.size + 10
        angle_rad = math.radians(self.angle)
        
        end_x = render_x + math.cos(angle_rad) * gun_length
        end_y = render_y + math.sin(angle_rad) * gun_length
        
        barrel_color = (255, 255, 255) if self.is_dashing else (255, 255, 255)
        pg.draw.line(screen, barrel_color, (render_x, render_y), (end_x, end_y), 3)
        
        # Draw health bar above player (scaled for larger resolution)
        if self.health < self.max_health:
            bar_width = 60  # Increased from 40
            bar_height = 8   # Increased from 6
            bar_x = render_x - bar_width // 2
            bar_y = render_y - self.size - 20  # Moved slightly further up
            
            # Background
            pg.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
            
            # Health bar
            health_width = (self.health / self.max_health) * bar_width
            health_color = (255, 0, 0) if self.health < 30 else (255, 255, 0) if self.health < 60 else (0, 255, 0)
            pg.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
    
    def take_damage(self, damage: int):
        """Apply damage to the player."""
        self.health = max(0, self.health - damage)
        
    def is_alive(self) -> bool:
        """Check if player is still alive."""
        return self.health > 0
    
    def get_rect(self) -> pg.Rect:
        """Get collision rectangle for the player."""
        return pg.Rect(self.pos.x - self.size, self.pos.y - self.size, 
                      self.size * 2, self.size * 2)
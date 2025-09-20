"""
Bullet system for the twin-stick shooter game.
Handles bullet physics, rendering, and lifecycle management.
"""

import pygame as pg
import math
from typing import List, Tuple
from enum import Enum

class BulletType(Enum):
    """Types of bullets."""
    PLAYER = "player"
    ENEMY_LASER = "enemy_laser"

class Bullet:
    """Individual bullet class."""
    
    def __init__(self, x: float, y: float, angle: float, bullet_type: BulletType = BulletType.PLAYER, speed: float = 800, damage: int = None, size_multiplier: float = 1.0, color: tuple = None, penetration: int = 1, shape: str = "standard", range_limit: float = None, weapon_type: str = None, special_attack: bool = False, bounce_enabled: bool = False, max_bounces: int = 0, bounce_range: float = None, enemy_targeting: bool = False, trail_enabled: bool = False, trail_duration: float = 0.0, target_pos: tuple = None):
        """Initialize a bullet."""
        self.pos = pg.Vector2(x, y)
        self.start_pos = pg.Vector2(x, y)  # Store starting position for range calculation
        self.angle = angle  # Direction in degrees
        self.type = bullet_type
        self.speed = speed  # pixels per second
        self.penetration = penetration  # How many enemies this bullet can go through
        self.hits_remaining = penetration  # Track remaining penetration
        self.shape = shape  # Bullet shape: "standard", "laser", "sniper", "tracer"
        self.range_limit = range_limit  # Maximum travel distance in pixels
        self.weapon_type = weapon_type  # Track weapon type for enhanced rendering
        self.special_attack = special_attack  # Mark if this is a special attack bullet
        
        # Bouncing properties
        self.bounce_enabled = bounce_enabled  # Can this bullet bounce?
        self.max_bounces = max_bounces  # Maximum number of bounces allowed
        self.bounces_remaining = max_bounces  # Track remaining bounces
        self.bounce_range = bounce_range  # Range within which to find bounce targets
        self.enemy_targeting = enemy_targeting  # Should bounces target enemies?
        self.has_bounced = False  # Track if bullet has bounced at least once
        
        # Trail properties for special sniper bullets
        self.trail_enabled = trail_enabled  # Can this bullet leave a burning trail?
        self.trail_duration = trail_duration  # How long the trail lasts
        self.trail_points = []  # List of positions where the bullet has been
        self.trail_segment_interval = 10  # Distance between trail segments (pixels)
        self.last_trail_pos = pg.Vector2(x, y)  # Last position where we added a trail point
        
        # Grenade targeting properties
        self.target_pos = target_pos  # Target position for grenade launcher
        self.is_grenade = (shape == "grenade")  # Flag for grenade behavior
        self.explode_at_target = False  # Flag for grenade explosions
        
        # Visual effect properties
        self.lifespan = None  # Optional lifespan for visual effects
        self.creation_time = None  # Time when bullet was created
        
        # Dissolving properties
        self.is_dissolving = False
        self.dissolve_start_time = 0.0
        self.dissolve_duration = 0.15  # 0.15 seconds to dissolve
        self.alpha = 255  # Full opacity initially
        
        # Calculate velocity from angle
        angle_rad = math.radians(angle)
        self.velocity = pg.Vector2(
            math.cos(angle_rad) * speed,
            math.sin(angle_rad) * speed
        )
        
        # Initialize stats based on type
        self._init_stats_by_type()
        
        # Disable individual bullet trails for minigun bullets
        if weapon_type == "Minigun" and shape == "tracer":
            self.max_trail_length = 0  # Disable individual bullet trails for minigun
        
        # Override damage if provided
        if damage is not None:
            self.damage = damage
            
        # Apply visual customizations for weapon types
        if bullet_type == BulletType.PLAYER:
            if size_multiplier != 1.0:
                self.size = int(self.size * size_multiplier)
            if color is not None:
                self.color = color
                # For special attacks with red color, use brighter trail and enhanced effects
                if special_attack and color == (255, 0, 0):  # Bright red special attack
                    self.trail_color = (255, 120, 120)  # Bright red-orange trail
                    # Make special attack bullets MUCH larger and more impressive
                    self.size = int(self.size * 2.0)  # Increased from 1.3x to 2.0x
                else:
                    # Adjust trail color to be slightly darker
                    self.trail_color = tuple(max(0, c - 50) for c in color)
        
        # Bullet properties
        self.age = 0.0
        
        # Trail effect
        self.trail_positions = []
    
    def _init_stats_by_type(self):
        """Initialize bullet stats based on type."""
        if self.type == BulletType.PLAYER:
            # Player bullets - ENHANCED ANIME-STYLE (much bigger and more powerful looking)
            self.size = 8  # Increased from 3 to 8 (2.6x bigger)
            self.color = (255, 255, 150)  # Brighter yellow with more white
            self.trail_color = (255, 220, 100)  # Brighter golden trail
            self.damage = 25
            self.lifetime = 3.0  # seconds
            self.max_trail_length = 12  # Longer trail for more dramatic effect
            
        elif self.type == BulletType.ENEMY_LASER:
            # Enemy laser bullets (red, long)
            self.size = 4
            self.color = (255, 50, 50)  # Bright red
            self.trail_color = (200, 30, 30)
            self.damage = 15
            self.lifetime = 4.0  # seconds (longer range)
            self.max_trail_length = 15  # Longer trail for lasers
            self.length = 25  # Length of the laser beam
            self.width = 3   # Width of the laser beam
    
    def update(self, dt: float, current_game_time: float = None, world_manager=None) -> bool:
        """Update bullet position and state. Returns True if bullet should be removed."""
        # Check if visual effect bullet should expire first
        if self.lifespan is not None and self.creation_time is not None and current_game_time is not None:
            if current_game_time - self.creation_time > self.lifespan:
                return True  # Visual effect expired
        
        # Update position
        self.pos += self.velocity * dt
        
        # Check grenade target proximity for explosion
        if self.is_grenade and self.target_pos is not None:
            target_distance = self.pos.distance_to(pg.Vector2(self.target_pos))
            if target_distance <= 30:  # Explode when within 30 pixels of target
                # Signal for explosion (will be handled by bullet manager)
                self.explode_at_target = True
                return True  # Remove grenade bullet to trigger explosion
        
        # Check map collision (blocks bullets or causes bounces)
        if world_manager is not None and hasattr(world_manager, 'is_position_blocked_by_map'):
            if world_manager.is_position_blocked_by_map(self.pos.x, self.pos.y):
                # Check if bullet can bounce
                if self.bounce_enabled and self.bounces_remaining > 0:
                    # Attempt to bounce
                    if self.bounce_off_surface(world_manager):
                        self.bounces_remaining -= 1
                        self.has_bounced = True
                        # Update starting position for range calculation from bounce point
                        self.start_pos = self.pos.copy()
                    else:
                        return True  # Couldn't bounce, remove bullet
                else:
                    return True  # Bullet blocked by map tile
        
        # Check range limit
        if self.range_limit is not None and not self.is_dissolving:
            distance_traveled = self.pos.distance_to(self.start_pos)
            if distance_traveled >= self.range_limit:
                # Start dissolving instead of immediately removing
                self.is_dissolving = True
                self.dissolve_start_time = self.age
                self.velocity = pg.Vector2(0, 0)  # Stop moving when dissolving
        
        # Handle dissolving effect
        if self.is_dissolving:
            dissolve_elapsed = self.age - self.dissolve_start_time
            if dissolve_elapsed >= self.dissolve_duration:
                return True  # Bullet fully dissolved, remove it
            else:
                # Calculate alpha based on dissolve progress
                progress = dissolve_elapsed / self.dissolve_duration
                self.alpha = int(255 * (1.0 - progress))  # Fade from 255 to 0
        
        # Update trail (but skip for minigun bullets)
        if not (self.weapon_type == "Minigun" and self.shape == "tracer"):
            self.trail_positions.append(self.pos.copy())
            if len(self.trail_positions) > self.max_trail_length:
                self.trail_positions.pop(0)
        
        # Update burning trail for special sniper bullets
        if self.trail_enabled and current_game_time is not None:
            # Record trail points more frequently for better coverage
            distance_from_last_trail = self.pos.distance_to(self.last_trail_pos)
            if distance_from_last_trail >= 5:  # Record every 5 pixels for complete coverage
                # Add current position to trail points with timestamp
                self.trail_points.append({
                    'pos': self.pos.copy(),
                    'timestamp': current_game_time
                })
                self.last_trail_pos = self.pos.copy()
        
        # Update bounce effects if any exist
        if hasattr(self, 'bounce_effects'):
            effects_to_remove = []
            for effect in self.bounce_effects:
                effect['age'] += dt
                
                # Update particles
                particles_to_remove = []
                for particle in effect['particles']:
                    particle['pos'] += particle['velocity'] * dt
                    particle['velocity'] *= 0.95  # Friction
                    particle['life'] -= dt * 3  # Fade over time
                    particle['size'] *= 0.98   # Shrink
                    
                    if particle['life'] <= 0 or particle['size'] <= 0.5:
                        particles_to_remove.append(particle)
                
                # Remove dead particles
                for particle in particles_to_remove:
                    effect['particles'].remove(particle)
                
                # Remove effect if too old or no particles left
                if effect['age'] >= effect['lifetime'] or not effect['particles']:
                    effects_to_remove.append(effect)
            
            # Remove dead effects
            for effect in effects_to_remove:
                self.bounce_effects.remove(effect)

        # Update age
        self.age += dt        # Check if bullet should be removed
        if self.age >= self.lifetime:
            return True
            
        # Check if bullet is extremely far from its starting position (avoid infinite bullets)
        # Use a much larger distance for infinite world gameplay
        max_travel_distance = 20000  # Allow bullets to travel very far in infinite world
        if self.pos.distance_to(self.start_pos) > max_travel_distance:
            return True
            
        return False
    
    def bounce_off_surface(self, world_manager) -> bool:
        """Attempt to bounce off a surface. Returns True if successful."""
        # Store old position for bounce effect
        bounce_pos = self.pos.copy()
        
        # Move bullet back to just before collision
        reverse_velocity = -self.velocity * 0.1  # Move back slightly
        self.pos += reverse_velocity
        
        # Check if we can find a valid bounce direction
        bounce_direction = self.calculate_bounce_direction(world_manager)
        if bounce_direction is not None:
            # Update velocity with new direction
            self.velocity = bounce_direction * self.speed
            self.angle = math.degrees(math.atan2(bounce_direction.y, bounce_direction.x))
            
            # Change bullet color to indicate bounce
            if hasattr(self, 'color'):
                # Make bullet more yellow/orange after bounce to show it bounced
                self.color = (255, 200, 100)  # Orange-yellow
                self.trail_color = (255, 150, 50)  # Orange trail
            
            # Mark bullet as bounced for visual changes
            self.has_bounced = True
            
            # Add visual bounce effect
            self.add_bounce_effect(bounce_pos)
            
            return True
        
        return False
    
    def add_bounce_effect(self, bounce_pos):
        """Add visual effect at bounce location."""
        # Store bounce effect data that can be rendered
        if not hasattr(self, 'bounce_effects'):
            self.bounce_effects = []
        
        # Add sparkle effect at bounce point
        bounce_effect = {
            'pos': bounce_pos.copy(),
            'age': 0.0,
            'lifetime': 0.3,
            'particles': []
        }
        
        # Create spark particles in all directions
        import random
        for i in range(8):
            angle = (i / 8.0) * 2 * math.pi
            speed = random.uniform(50, 150)
            bounce_effect['particles'].append({
                'pos': bounce_pos.copy(),
                'velocity': pg.Vector2(math.cos(angle) * speed, math.sin(angle) * speed),
                'size': random.uniform(2, 4),
                'color': (255, 255, 100),  # Yellow sparks
                'life': 1.0
            })
        
        self.bounce_effects.append(bounce_effect)
    
    def calculate_bounce_direction(self, world_manager) -> pg.Vector2:
        """Calculate bounce direction, preferring enemy targets if enabled."""
        if self.enemy_targeting and hasattr(world_manager, 'enemy_manager'):
            # Try to find nearest enemy within bounce range
            target_direction = self.find_enemy_target(world_manager.enemy_manager)
            if target_direction is not None:
                return target_direction
        
        # Fallback to surface normal reflection
        return self.calculate_surface_reflection(world_manager)
    
    def find_enemy_target(self, enemy_manager) -> pg.Vector2:
        """Find nearest enemy within bounce range and return direction."""
        if not self.bounce_range:
            return None
            
        nearest_enemy = None
        nearest_distance = float('inf')
        
        for enemy in enemy_manager.get_enemies():
            distance = self.pos.distance_to(enemy.pos)
            if distance <= self.bounce_range and distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy
        
        if nearest_enemy:
            direction = (nearest_enemy.pos - self.pos)
            if direction.length() > 0:
                return direction.normalize()
        
        return None
    
    def calculate_surface_reflection(self, world_manager) -> pg.Vector2:
        """Calculate reflection off surface using simple normal estimation."""
        # Sample points around bullet to estimate surface normal
        test_radius = 10
        normals = []
        
        # Test 8 directions around the bullet
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            angle_rad = math.radians(angle)
            test_x = self.pos.x + math.cos(angle_rad) * test_radius
            test_y = self.pos.y + math.sin(angle_rad) * test_radius
            
            if not world_manager.is_position_blocked_by_map(test_x, test_y):
                # This direction is free, so surface normal points this way
                normals.append(pg.Vector2(math.cos(angle_rad), math.sin(angle_rad)))
        
        if normals:
            # Average the normals to get surface direction
            avg_normal = pg.Vector2(0, 0)
            for normal in normals:
                avg_normal += normal
            avg_normal = avg_normal.normalize()
            
            # Check if velocity is zero or very small
            if self.velocity.length() < 0.1:
                # Use angle to create a velocity vector
                angle_rad = math.radians(self.angle)
                self.velocity = pg.Vector2(math.cos(angle_rad), math.sin(angle_rad)) * self.speed
            
            # Reflect velocity off the surface
            velocity_normalized = self.velocity.normalize()
            reflected = velocity_normalized - 2 * velocity_normalized.dot(avg_normal) * avg_normal
            return reflected
        
        # Fallback: reverse direction
        if self.velocity.length() < 0.1:
            # Use angle to create a velocity vector
            angle_rad = math.radians(self.angle)
            self.velocity = pg.Vector2(math.cos(angle_rad), math.sin(angle_rad)) * self.speed
        
        return -self.velocity.normalize()
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render the bullet with trail effect."""
        # Apply camera offset
        render_x = self.pos.x + offset[0]
        render_y = self.pos.y + offset[1]
        
        # Create a temporary surface for alpha blending if dissolving
        if self.is_dissolving and self.alpha < 255:
            # Create a temporary surface for alpha rendering
            temp_surface = pg.Surface((screen.get_width(), screen.get_height()), pg.SRCALPHA)
            temp_surface.set_alpha(self.alpha)
            self._render_bullet_content(temp_surface, offset)
            screen.blit(temp_surface, (0, 0))
        else:
            # Render normally
            self._render_bullet_content(screen, offset)
        
        # Render bounce effects
        if hasattr(self, 'bounce_effects'):
            for effect in self.bounce_effects:
                for particle in effect['particles']:
                    if particle['life'] > 0 and particle['size'] > 0.5:
                        particle_x = particle['pos'].x + offset[0]
                        particle_y = particle['pos'].y + offset[1]
                        
                        # Calculate alpha based on life
                        alpha = min(255, int(particle['life'] * 255))
                        size = int(particle['size'])
                        
                        if alpha > 0 and size > 0:
                            # Create particle surface with alpha
                            particle_surf = pg.Surface((size * 2, size * 2), pg.SRCALPHA)
                            color_with_alpha = (*particle['color'], alpha)
                            pg.draw.circle(particle_surf, color_with_alpha, (size, size), size)
                            screen.blit(particle_surf, (int(particle_x - size), int(particle_y - size)),
                                      special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _render_bullet_content(self, screen: pg.Surface, offset=(0, 0)):
        """Internal method to render bullet content to the given surface."""
        import math  # Import math at the beginning of the function
        
        # Apply camera offset
        render_x = self.pos.x + offset[0]
        render_y = self.pos.y + offset[1]
        
        if self.type == BulletType.ENEMY_LASER:
            # Render laser beam as a long line
            angle_rad = math.radians(self.angle)
            
            # Calculate laser beam endpoints
            start_x = render_x - math.cos(angle_rad) * (self.length // 2)
            start_y = render_y - math.sin(angle_rad) * (self.length // 2)
            end_x = render_x + math.cos(angle_rad) * (self.length // 2)
            end_y = render_y + math.sin(angle_rad) * (self.length // 2)
            
            # Draw laser beam with glow effect
            # Outer glow (thicker, semi-transparent)
            glow_color = (*self.trail_color, 100)  # Semi-transparent red
            pg.draw.line(screen, self.trail_color, (int(start_x), int(start_y)), (int(end_x), int(end_y)), self.width + 4)
            
            # Inner beam (bright core)
            pg.draw.line(screen, self.color, (int(start_x), int(start_y)), (int(end_x), int(end_y)), self.width)
            
            # Bright center line
            pg.draw.line(screen, (255, 255, 255), (int(start_x), int(start_y)), (int(end_x), int(end_y)), 1)
        else:
            # Regular bullet rendering
            # Draw trail - enhanced for pellets and tracers
            if self.shape == "pellet":
                # Enhanced energy trail for shotgun pellets
                for i, trail_pos in enumerate(self.trail_positions[:-1]):
                    alpha = (i + 1) / len(self.trail_positions) * 0.7
                    trail_size = max(2, int(self.size * alpha * 1.5))
                    
                    # Energy trail with multiple colors
                    trail_color_core = (
                        int(255 * alpha),  # Orange-red core
                        int(180 * alpha),
                        int(50 * alpha)
                    )
                    trail_color_glow = (
                        int(255 * alpha * 0.8),  # Yellow glow
                        int(220 * alpha * 0.8),
                        int(100 * alpha * 0.8)
                    )
                    
                    trail_render_x = trail_pos.x + offset[0]
                    trail_render_y = trail_pos.y + offset[1]
                    
                    # Draw glow layer first
                    pg.draw.circle(screen, trail_color_glow, (int(trail_render_x), int(trail_render_y)), trail_size + 2)
                    # Draw core trail
                    pg.draw.circle(screen, trail_color_core, (int(trail_render_x), int(trail_render_y)), trail_size)
            elif self.shape == "tracer":
                # Military-style contrail for anime tracer rounds (but skip minigun bullets)
                if self.weapon_type != "Minigun":  # Disable trails for minigun bullets
                    for i, trail_pos in enumerate(self.trail_positions[:-1]):
                        alpha = (i + 1) / len(self.trail_positions) * 0.8
                        trail_size = max(1, int(self.size * alpha * 1.2))
                        
                        # Military tracer trail colors
                        trail_color_hot = (
                            int(255 * alpha),  # Bright orange-yellow
                            int(200 * alpha), 
                            int(100 * alpha)
                        )
                        trail_color_smoke = (
                            int(200 * alpha * 0.7),  # Smoke trail
                            int(150 * alpha * 0.7),
                            int(100 * alpha * 0.7)
                        )
                        
                        trail_render_x = trail_pos.x + offset[0]
                        trail_render_y = trail_pos.y + offset[1]
                        
                        # Draw smoke contrail first (wider)
                        pg.draw.circle(screen, trail_color_smoke, (int(trail_render_x), int(trail_render_y)), trail_size + 1)
                        # Draw hot tracer core
                        pg.draw.circle(screen, trail_color_hot, (int(trail_render_x), int(trail_render_y)), trail_size)
            elif self.shape == "neon":
                # Cyberpunk holographic trail with digital artifacts
                for i, trail_pos in enumerate(self.trail_positions[:-1]):
                    alpha = (i + 1) / len(self.trail_positions) * 0.9
                    trail_size = max(1, int(self.size * alpha * 1.5))
                    
                    # Check if bullet has bounced to change colors
                    if hasattr(self, 'has_bounced') and self.has_bounced:
                        # Orange/yellow holographic trail after bounce
                        trail_color_glow = (
                            int(255 * alpha), # Orange red
                            int(200 * alpha), # Orange green  
                            int(0),           # No blue
                            int(150 * alpha)  # Alpha for holographic effect
                        )
                        trail_color_core = (
                            int(255 * alpha), # Full orange red
                            int(150 * alpha), # Reduced green for orange
                            int(50 * alpha)   # Slight blue
                        )
                    else:
                        # Original neon holographic trail colors (cyan-based)
                        trail_color_glow = (
                            int(0),           # No red
                            int(255 * alpha), # Bright cyan green
                            int(255 * alpha), # Bright cyan blue
                            int(150 * alpha)  # Alpha for holographic effect
                        )
                        trail_color_core = (
                            int(100 * alpha), # Slight red tint
                            int(255 * alpha), # Full green
                            int(255 * alpha)  # Full blue
                        )
                    
                    trail_render_x = trail_pos.x + offset[0]
                    trail_render_y = trail_pos.y + offset[1]
                    
                    # Draw holographic glow first (with alpha)
                    self._draw_pixel_artifact(screen, trail_render_x, trail_render_y, trail_size + 2, trail_color_glow)
                    # Draw solid core trail
                    pg.draw.circle(screen, trail_color_core, (int(trail_render_x), int(trail_render_y)), trail_size)
                    
                    # Add occasional digital glitch pixels
                    if i % 2 == 0:  # Every other trail position
                        import random
                        glitch_x = trail_render_x + random.uniform(-trail_size * 2, trail_size * 2)
                        glitch_y = trail_render_y + random.uniform(-trail_size * 2, trail_size * 2)
                        glitch_size = random.randint(1, 2)
                        glitch_alpha = int(alpha * 100)
                        if glitch_alpha > 0:
                            self._draw_pixel_artifact(screen, glitch_x, glitch_y, glitch_size, (0, 255, 255, glitch_alpha))
            elif self.shape == "slash":
                # Magical sword trail with sparkle remnants and energy wisps
                for i, trail_pos in enumerate(self.trail_positions[:-1]):
                    alpha = (i + 1) / len(self.trail_positions) * 0.8
                    trail_size = max(1, int(self.size * alpha * 2.0))  # Larger magical trail
                    
                    # Magical blade trail colors (mystical blue-white)
                    trail_color_glow = (
                        int(150 * alpha), # Soft blue glow
                        int(200 * alpha), # Magical blue
                        int(255 * alpha), # Bright magical white
                        int(120 * alpha)  # Alpha for magical effect
                    )
                    trail_color_core = (
                        int(200 * alpha), # Light blue core
                        int(200 * alpha), # Balanced magical
                        int(255 * alpha)  # Bright white magical
                    )
                    
                    trail_render_x = trail_pos.x + offset[0]
                    trail_render_y = trail_pos.y + offset[1]
                    
                    # Draw magical glow first (with alpha)
                    self._draw_magical_sparkle(screen, trail_render_x, trail_render_y, trail_size + 3, trail_color_glow)
                    # Draw solid core trail
                    pg.draw.circle(screen, trail_color_core, (int(trail_render_x), int(trail_render_y)), trail_size)
                    
                    # Add magical sparkle particles
                    if i % 3 == 0:  # Every third trail position
                        import random
                        sparkle_x = trail_render_x + random.uniform(-trail_size * 3, trail_size * 3)
                        sparkle_y = trail_render_y + random.uniform(-trail_size * 3, trail_size * 3)
                        sparkle_size = random.randint(2, 4)
                        sparkle_alpha = int(alpha * 150)
                        if sparkle_alpha > 0:
                            self._draw_magical_sparkle(screen, sparkle_x, sparkle_y, sparkle_size, (255, 255, 255, sparkle_alpha))
            else:
                # Standard trail for other bullets
                for i, trail_pos in enumerate(self.trail_positions[:-1]):
                    alpha = (i + 1) / len(self.trail_positions) * 0.5
                    trail_size = max(1, int(self.size * alpha))
                    trail_color = (
                        int(self.trail_color[0] * alpha),
                        int(self.trail_color[1] * alpha),
                        int(self.trail_color[2] * alpha)
                    )
                    trail_render_x = trail_pos.x + offset[0]
                    trail_render_y = trail_pos.y + offset[1]
                    pg.draw.circle(screen, trail_color, (int(trail_render_x), int(trail_render_y)), trail_size)
            
            # Draw main bullet based on shape
            if self.shape == "laser":
                # Draw sniper bullet - larger, elongated white projectile
                self.render_sniper_bullet(screen, render_x, render_y)
            elif self.shape == "pellet":
                # Draw shotgun pellet - glowing energy orb
                self.render_shotgun_pellet(screen, render_x, render_y)
            elif self.shape == "tracer":
                # Always use enhanced rendering for minigun bullets
                if self.weapon_type == "Minigun":
                    self.render_enhanced_minigun_bullet(screen, render_x, render_y)
                else:
                    # Draw anime military tracer round for other weapons
                    self.render_tracer_round(screen, render_x, render_y)
            elif self.shape == "neon":
                # Draw cyberpunk neon bullet
                self.render_neon_bullet(screen, render_x, render_y)
            elif self.shape == "slash":
                # Draw magical sword slash
                self.render_sword_slash(screen, render_x, render_y)
            elif self.shape == "grenade":
                # Draw simple, small grenade projectile (like rocket missiles)
                grenade_size = max(3, int(self.size))  # Much smaller - just like other bullets
                
                # Simple small grenade - minimal visual impact during flight
                # Dark metallic base
                pg.draw.circle(screen, (60, 45, 30), (int(render_x), int(render_y)), grenade_size)
                
                # Small highlight
                highlight_size = max(2, int(grenade_size * 0.7))
                pg.draw.circle(screen, (100, 80, 60), (int(render_x), int(render_y)), highlight_size)
                
                # Tiny center
                center_size = max(1, int(grenade_size * 0.4))
                pg.draw.circle(screen, (200, 150, 100), (int(render_x), int(render_y)), center_size)
            else:
                # Standard circular bullet - ENHANCED ANIME-STYLE RENDERING
                # Draw multiple layers for dramatic anime-style effect
                
                # Outer glow layer (reduced size for better balance)
                outer_glow_size = int(self.size * 1.4)  # Reduced from 2.5x
                outer_glow_color = (
                    min(255, self.color[0] + 30),
                    min(255, self.color[1] + 30), 
                    min(255, self.color[2] + 50)
                )
                pg.draw.circle(screen, outer_glow_color, (int(render_x), int(render_y)), outer_glow_size)
                
                # Mid glow layer
                mid_glow_size = int(self.size * 1.2)  # Reduced from 1.8x
                mid_glow_color = (
                    min(255, self.color[0] + 20),
                    min(255, self.color[1] + 20),
                    min(255, self.color[2] + 30)
                )
                pg.draw.circle(screen, mid_glow_color, (int(render_x), int(render_y)), mid_glow_size)
                
                # Main bullet body - slightly reduced
                main_size = int(self.size * 1.1)  # Reduced from 1.3x
                pg.draw.circle(screen, self.color, (int(render_x), int(render_y)), main_size)
                
                # Bright inner core
                inner_size = int(self.size * 0.8)
                inner_color = (
                    min(255, self.color[0] + 40),
                    min(255, self.color[1] + 40),
                    min(255, self.color[2] + 60)
                )
                pg.draw.circle(screen, inner_color, (int(render_x), int(render_y)), inner_size)
                
                # Ultra-bright center point for anime-style intensity
                center_size = max(2, int(self.size * 0.4))
                center_color = (255, 255, 255)  # Pure white center
                pg.draw.circle(screen, center_color, (int(render_x), int(render_y)), center_size)
                
                # Bright outline ring for definition
                outline_width = max(2, int(self.size * 0.2))
                pg.draw.circle(screen, (255, 255, 255), (int(render_x), int(render_y)), main_size, outline_width)
    
    def render_sniper_bullet(self, screen: pg.Surface, x: float, y: float):
        """Render a sci-fi laser beam with particle effects."""
        import math
        import random
        
        angle_rad = math.radians(self.angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Laser beam dimensions - absolutely massive sci-fi laser beam
        beam_length = self.size * 60  # Triple the length (was 20x)
        beam_width = max(self.size * 4, 24)  # Double the width (was 2x with 12px min)
        
        # Calculate beam endpoints - start from spawn point instead of centering
        # The beam should start from the bullet position (gun tip) and extend forward
        back_x = x  # Start from the bullet spawn position
        back_y = y
        front_x = x + cos_angle * beam_length  # Extend full length forward
        front_y = y + sin_angle * beam_length
        
        # Draw tapered laser beam with smooth ends
        self._draw_tapered_laser_beam(screen, back_x, back_y, front_x, front_y, beam_width)
        
        # Particle effects at the tip
        self._draw_laser_particles(screen, front_x, front_y, angle_rad)
        
        # Energy crackling effects along the beam
        self._draw_energy_crackling(screen, back_x, back_y, front_x, front_y, beam_width)
    
    def _draw_tapered_laser_beam(self, screen: pg.Surface, back_x: float, back_y: float, front_x: float, front_y: float, beam_width: float):
        """Draw a tapered laser beam with smooth, pointed ends."""
        import math
        
        # Calculate beam direction
        beam_dx = front_x - back_x
        beam_dy = front_y - back_y
        beam_length = math.sqrt(beam_dx**2 + beam_dy**2)
        
        if beam_length == 0:
            return
            
        # Normalize direction
        norm_dx = beam_dx / beam_length
        norm_dy = beam_dy / beam_length
        
        # Perpendicular vector for width
        perp_x = -norm_dy
        perp_y = norm_dx
        
        # Create tapered beam shape points
        taper_length = beam_width * 3  # How long the taper is
        
        # Back taper (starts at point, widens to full width)
        back_tip_x = back_x
        back_tip_y = back_y
        back_wide_x = back_x + norm_dx * taper_length
        back_wide_y = back_y + norm_dy * taper_length
        
        # Front taper (full width, narrows to point)
        front_wide_x = front_x - norm_dx * taper_length
        front_wide_y = front_y - norm_dy * taper_length
        front_tip_x = front_x
        front_tip_y = front_y
        
        # Calculate width points
        half_width = beam_width / 2
        
        # Outer glow (largest, most transparent)
        glow_width = beam_width * 3
        self._draw_tapered_beam_layer(screen, back_x, back_y, front_x, front_y, 
                                    glow_width, (100, 200, 255, 30), taper_length * 1.5)
        
        # Middle glow
        mid_glow_width = beam_width * 2
        self._draw_tapered_beam_layer(screen, back_x, back_y, front_x, front_y, 
                                    mid_glow_width, (150, 220, 255, 60), taper_length * 1.2)
        
        # Inner glow
        inner_glow_width = beam_width * 1.3
        self._draw_tapered_beam_layer(screen, back_x, back_y, front_x, front_y, 
                                    inner_glow_width, (200, 240, 255, 100), taper_length)
        
        # Core beam (solid white)
        self._draw_tapered_beam_core(screen, back_x, back_y, front_x, front_y, 
                                   beam_width, taper_length)
    
    def _draw_tapered_beam_layer(self, screen: pg.Surface, back_x: float, back_y: float, 
                               front_x: float, front_y: float, width: float, color: tuple, taper_len: float):
        """Draw a single tapered beam layer with alpha blending."""
        import math
        
        # Calculate beam properties
        beam_dx = front_x - back_x
        beam_dy = front_y - back_y
        beam_length = math.sqrt(beam_dx**2 + beam_dy**2)
        
        if beam_length == 0:
            return
            
        norm_dx = beam_dx / beam_length
        norm_dy = beam_dy / beam_length
        perp_x = -norm_dy * width / 2
        perp_y = norm_dx * width / 2
        
        # Create tapered polygon points
        points = []
        
        # Back point (sharp tip)
        points.append((back_x, back_y))
        
        # Back wide section
        back_wide_x = back_x + norm_dx * taper_len
        back_wide_y = back_y + norm_dy * taper_len
        points.append((back_wide_x + perp_x, back_wide_y + perp_y))
        
        # Middle section (full width)
        front_wide_x = front_x - norm_dx * taper_len
        front_wide_y = front_y - norm_dy * taper_len
        points.append((front_wide_x + perp_x, front_wide_y + perp_y))
        
        # Front point (sharp tip)
        points.append((front_x, front_y))
        
        # Front wide section (other side)
        points.append((front_wide_x - perp_x, front_wide_y - perp_y))
        
        # Back wide section (other side)
        points.append((back_wide_x - perp_x, back_wide_y - perp_y))
        
        # Draw with alpha blending
        if len(color) == 4:  # Has alpha
            # Create surface for alpha blending
            bounds = self._get_polygon_bounds(points)
            temp_surf = pg.Surface((int(bounds[2] - bounds[0]) + 10, int(bounds[3] - bounds[1]) + 10), pg.SRCALPHA)
            offset_points = [(p[0] - bounds[0] + 5, p[1] - bounds[1] + 5) for p in points]
            pg.draw.polygon(temp_surf, color, offset_points)
            screen.blit(temp_surf, (bounds[0] - 5, bounds[1] - 5), special_flags=pg.BLEND_ALPHA_SDL2)
        else:
            pg.draw.polygon(screen, color, points)
    
    def _draw_tapered_beam_core(self, screen: pg.Surface, back_x: float, back_y: float, 
                              front_x: float, front_y: float, width: float, taper_len: float):
        """Draw the solid white core of the tapered beam."""
        import math
        
        # Calculate beam properties
        beam_dx = front_x - back_x
        beam_dy = front_y - back_y
        beam_length = math.sqrt(beam_dx**2 + beam_dy**2)
        
        if beam_length == 0:
            return
            
        norm_dx = beam_dx / beam_length
        norm_dy = beam_dy / beam_length
        perp_x = -norm_dy * width / 2
        perp_y = norm_dx * width / 2
        
        # Core beam (full size)
        points = []
        points.append((back_x, back_y))
        
        back_wide_x = back_x + norm_dx * taper_len
        back_wide_y = back_y + norm_dy * taper_len
        points.append((back_wide_x + perp_x, back_wide_y + perp_y))
        
        front_wide_x = front_x - norm_dx * taper_len
        front_wide_y = front_y - norm_dy * taper_len
        points.append((front_wide_x + perp_x, front_wide_y + perp_y))
        points.append((front_x, front_y))
        points.append((front_wide_x - perp_x, front_wide_y - perp_y))
        points.append((back_wide_x - perp_x, back_wide_y - perp_y))
        
        pg.draw.polygon(screen, (255, 255, 255), points)
        
        # Inner core (smaller, brighter)
        inner_width = width * 0.6
        inner_perp_x = -norm_dy * inner_width / 2
        inner_perp_y = norm_dx * inner_width / 2
        
        inner_points = []
        inner_points.append((back_x, back_y))
        inner_points.append((back_wide_x + inner_perp_x, back_wide_y + inner_perp_y))
        inner_points.append((front_wide_x + inner_perp_x, front_wide_y + inner_perp_y))
        inner_points.append((front_x, front_y))
        inner_points.append((front_wide_x - inner_perp_x, front_wide_y - inner_perp_y))
        inner_points.append((back_wide_x - inner_perp_x, back_wide_y - inner_perp_y))
        
        pg.draw.polygon(screen, (255, 255, 255), inner_points)
        
        # Ultra-bright center line
        center_width = max(width * 0.2, 2)
        center_perp_x = -norm_dy * center_width / 2
        center_perp_y = norm_dx * center_width / 2
        
        center_points = []
        center_points.append((back_x, back_y))
        center_points.append((back_wide_x + center_perp_x, back_wide_y + center_perp_y))
        center_points.append((front_wide_x + center_perp_x, front_wide_y + center_perp_y))
        center_points.append((front_x, front_y))
        center_points.append((front_wide_x - center_perp_x, front_wide_y - center_perp_y))
        center_points.append((back_wide_x - center_perp_x, back_wide_y - center_perp_y))
        
        pg.draw.polygon(screen, (255, 255, 255), center_points)
    
    def render_shotgun_pellet(self, screen: pg.Surface, x: float, y: float):
        """Render small shotgun pellets with minimal glow effects."""
        import math
        
        # Check if this is a special attack for color
        is_special = hasattr(self, 'special_attack') and self.special_attack
        
        # Small pellet size - much smaller than before
        base_size = max(3, int(self.size))  # Base size without multipliers
        if is_special:
            base_size = int(base_size * 1.1)  # Tiny increase for special attacks
        
        # Create subtle pulsing effect
        pulse_time = pg.time.get_ticks() / 300
        pulse_factor = 1.0 + 0.1 * math.sin(pulse_time + hash((x, y)) % 100)
        current_size = int(base_size * pulse_factor)
        
        # Color scheme: Orange fire for normal, Red for special attacks
        if is_special:
            outer_color = (255, 50, 50, 40)    # Subtle red glow
            inner_color = (255, 100, 100, 80)  # Red core
            core_color = (255, 150, 150)       # Light red center
        else:
            outer_color = (255, 120, 60, 35)   # Subtle orange glow
            inner_color = (255, 160, 80, 70)   # Orange core  
            core_color = (255, 200, 120)       # Light orange center
        
        # Very small glow layers
        outer_size = current_size + 2  # Just 2 pixels larger
        inner_size = current_size + 1  # Just 1 pixel larger
        
        # Draw minimal glow layers
        self._draw_energy_orb_layer(screen, x, y, outer_size, outer_color)
        self._draw_energy_orb_layer(screen, x, y, inner_size, inner_color)
        
        # Small solid core
        pg.draw.circle(screen, core_color, (int(x), int(y)), current_size)
    
    def _draw_flame_layer(self, screen: pg.Surface, x: float, y: float, size: int, color: tuple, time_offset: float):
        """Draw a flickering flame layer with animated distortion."""
        import math
        import random
        
        # Create flame-like distorted circle
        points = []
        num_points = 16
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            # Add flame-like distortion
            distortion = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(angle * 3 + time_offset * 2))
            radius = size * distortion * (0.8 + 0.4 * math.sin(angle * 2 + time_offset))
            point_x = x + math.cos(angle) * radius
            point_y = y + math.sin(angle) * radius
            points.append((point_x, point_y))
        
        # Draw the flame shape if we have enough points
        if len(points) >= 3:
            try:
                # Create surface with per-pixel alpha for the flame effect
                flame_surf = pg.Surface((size * 3, size * 3), pg.SRCALPHA)
                adjusted_points = [(pt[0] - x + size * 1.5, pt[1] - y + size * 1.5) for pt in points]
                pg.draw.polygon(flame_surf, color, adjusted_points)
                screen.blit(flame_surf, (x - size * 1.5, y - size * 1.5), special_flags=pg.BLEND_ALPHA_SDL2)
            except:
                # Fallback to simple circle if polygon fails
                pg.draw.circle(screen, color[:3], (int(x), int(y)), size)
    
    def _draw_energy_orb_layer(self, screen: pg.Surface, x: float, y: float, size: int, color: tuple):
        """Draw a single energy orb layer with alpha blending."""
        if len(color) == 4:  # Has alpha
            # Create surface for alpha blending
            orb_surf = pg.Surface((size * 2 + 10, size * 2 + 10), pg.SRCALPHA)
            pg.draw.circle(orb_surf, color, (size + 5, size + 5), size)
            screen.blit(orb_surf, (x - size - 5, y - size - 5), special_flags=pg.BLEND_ALPHA_SDL2)
        else:
            # Regular drawing without alpha
            pg.draw.circle(screen, color, (int(x), int(y)), size)

    def render_tracer_round(self, screen: pg.Surface, x: float, y: float):
        """Render anime military-style tracer round."""
        import math
        
        # Calculate bullet length and orientation
        angle_rad = math.radians(self.angle)
        bullet_length = self.size * 3  # Elongated like real tracer rounds
        
        # Calculate front and back points of the tracer
        front_x = x + math.cos(angle_rad) * bullet_length / 2
        front_y = y + math.sin(angle_rad) * bullet_length / 2
        back_x = x - math.cos(angle_rad) * bullet_length / 2
        back_y = y - math.sin(angle_rad) * bullet_length / 2
        
        # Outer glow layer (reduced size)
        outer_glow_width = self.size * 1.5  # Reduced from 2.5x
        outer_color = (255, 150, 0, 60)  # Orange glow with alpha
        self._draw_tracer_line(screen, back_x, back_y, front_x, front_y, outer_glow_width, outer_color)
        
        # Middle glow layer
        mid_glow_width = self.size * 1.2  # Reduced from 1.8x
        mid_color = (255, 180, 50, 100)  # Brighter orange
        self._draw_tracer_line(screen, back_x, back_y, front_x, front_y, mid_glow_width, mid_color)
        
        # Inner core (solid tracer round)
        core_width = self.size * 1.2
        core_color = (255, 220, 100)  # Bright yellow-orange core
        pg.draw.line(screen, core_color, (int(back_x), int(back_y)), (int(front_x), int(front_y)), int(core_width))
        
        # Ultra-bright center line (anime-style intense brightness)
        center_color = (255, 255, 200)  # Near-white center
        center_width = max(int(self.size * 0.6), 2)
        pg.draw.line(screen, center_color, (int(back_x), int(back_y)), (int(front_x), int(front_y)), center_width)
        
        # Bright tip point (military tracer tip)
        tip_size = int(self.size * 0.8)
        pg.draw.circle(screen, (255, 255, 255), (int(front_x), int(front_y)), tip_size)
        
        # Hot center tip
        hot_tip_size = max(int(self.size * 0.4), 1)
        pg.draw.circle(screen, (255, 255, 255), (int(front_x), int(front_y)), hot_tip_size)
    
    def render_enhanced_minigun_bullet(self, screen: pg.Surface, x: float, y: float):
        """Render simple sci-fi plasma ball for minigun."""
        import math
        
        # Draw simple glowing energy ball instead of elongated bolt
        ball_size = max(6, int(self.size))  # Simple ball size
        
        # Sci-fi plasma colors
        outer_color = (0, 150, 255, 100)    # Cyan outer glow
        inner_color = (100, 220, 255, 180)  # Bright cyan inner
        core_color = (255, 255, 255)        # White core
        
        # Draw simple glowing ball layers
        # Outer glow
        outer_size = ball_size + 3
        self._draw_energy_orb_layer(screen, x, y, outer_size, outer_color)
        
        # Inner glow
        inner_size = ball_size + 1
        self._draw_energy_orb_layer(screen, x, y, inner_size, inner_color)
        
        # Bright core
        pg.draw.circle(screen, core_color, (int(x), int(y)), ball_size)

    def render_neon_bullet(self, screen: pg.Surface, x: float, y: float):
        """Render a cyberpunk neon bullet with holographic effects."""
        import math
        import random
        
        # Cyberpunk neon bullet - holographic projectile with digital effects
        angle_rad = math.radians(self.angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Neon bullet dimensions - sleek digital projectile
        bullet_length = self.size * 8  # Elongated neon projectile
        bullet_width = max(self.size * 2, 6)  # Slim but visible
        
        # Calculate bullet endpoints (elongated in direction of travel)
        back_x = x - cos_angle * bullet_length * 0.5
        back_y = y - sin_angle * bullet_length * 0.5
        front_x = x + cos_angle * bullet_length * 0.5
        front_y = y + sin_angle * bullet_length * 0.5
        
        # Cyberpunk neon colors - change based on bounce status
        if hasattr(self, 'has_bounced') and self.has_bounced:
            # Orange/amber colors after bounce
            neon_cyan = (255, 150, 0)      # Orange base
            neon_bright = (255, 255, 200)  # Bright yellow-white core
            neon_glow = (255, 200, 50)     # Bright orange glow  
            neon_dark = (200, 100, 0)      # Darker orange outline
        else:
            # Original cyan theme
            neon_cyan = self.color         # Base color [0, 255, 255]
            neon_bright = (255, 255, 255)  # Bright white core
            neon_glow = (0, 200, 255)      # Bright cyan glow
            neon_dark = (0, 150, 200)      # Darker cyan outline
        
        # Layer 1: Outer holographic glow
        glow_width = int(bullet_width * 2.5)
        self._draw_neon_line(screen, back_x, back_y, front_x, front_y, glow_width, (*neon_glow, 60))
        
        # Layer 2: Mid glow
        mid_width = int(bullet_width * 1.8)
        self._draw_neon_line(screen, back_x, back_y, front_x, front_y, mid_width, (*neon_cyan, 120))
        
        # Layer 3: Core projectile
        core_width = int(bullet_width * 1.2)
        self._draw_neon_line(screen, back_x, back_y, front_x, front_y, core_width, neon_bright)
        
        # Layer 4: Inner core
        inner_width = max(int(bullet_width * 0.6), 2)
        self._draw_neon_line(screen, back_x, back_y, front_x, front_y, inner_width, neon_cyan)
        
        # Digital artifacts - glitchy pixel effects around the bullet
        for _ in range(3):
            artifact_x = x + random.uniform(-bullet_length * 0.8, bullet_length * 0.8)
            artifact_y = y + random.uniform(-bullet_width * 2, bullet_width * 2)
            artifact_size = random.randint(1, 3)
            artifact_alpha = random.randint(80, 150)
            
            # Small glitch pixels
            if random.random() > 0.3:  # 70% chance
                self._draw_pixel_artifact(screen, artifact_x, artifact_y, artifact_size, (*neon_cyan, artifact_alpha))
        
        # Holographic tip effect - bright leading edge
        tip_size = int(bullet_width * 1.5)
        pg.draw.circle(screen, neon_bright, (int(front_x), int(front_y)), tip_size)
        pg.draw.circle(screen, neon_cyan, (int(front_x), int(front_y)), int(tip_size * 0.6))
        
        # Data stream tail - digital particle trail
        for i in range(3):
            trail_offset = (i + 1) * bullet_length * 0.15
            trail_x = back_x - cos_angle * trail_offset
            trail_y = back_y - sin_angle * trail_offset
            trail_alpha = 200 - (i * 60)
            trail_size = max(int(bullet_width * (0.8 - i * 0.2)), 1)
            
            if trail_alpha > 0:
                self._draw_pixel_artifact(screen, trail_x, trail_y, trail_size, (*neon_cyan, trail_alpha))
    
    def _draw_neon_line(self, screen: pg.Surface, x1: float, y1: float, x2: float, y2: float, width: float, color: tuple):
        """Draw a neon line with alpha blending for cyberpunk effects."""
        if len(color) == 4:  # Has alpha
            # Create surface for alpha blending
            line_length = max(abs(x2 - x1), abs(y2 - y1))
            temp_surf = pg.Surface((line_length + width * 2, width * 2), pg.SRCALPHA)
            
            # Draw on temp surface
            temp_x1 = width
            temp_y1 = width
            temp_x2 = temp_x1 + (x2 - x1)
            temp_y2 = temp_y1 + (y2 - y1)
            
            pg.draw.line(temp_surf, color, (int(temp_x1), int(temp_y1)), (int(temp_x2), int(temp_y2)), int(width))
            
            # Blit with alpha
            screen.blit(temp_surf, (int(x1 - width), int(y1 - width)), special_flags=pg.BLEND_ALPHA_SDL2)
        else:
            # Regular line without alpha
            pg.draw.line(screen, color, (int(x1), int(y1)), (int(x2), int(y2)), int(width))
    
    def _draw_pixel_artifact(self, screen: pg.Surface, x: float, y: float, size: int, color: tuple):
        """Draw digital glitch artifacts for cyberpunk effect."""
        if len(color) == 4:  # Has alpha
            # Create small surface for pixel artifact
            temp_surf = pg.Surface((size * 2, size * 2), pg.SRCALPHA)
            pg.draw.rect(temp_surf, color, (0, 0, size, size))
            screen.blit(temp_surf, (int(x - size/2), int(y - size/2)), special_flags=pg.BLEND_ALPHA_SDL2)
        else:
            # Regular pixel without alpha
            pg.draw.rect(screen, color, (int(x - size/2), int(y - size/2), size, size))
    
    def render_sword_slash(self, screen: pg.Surface, x: float, y: float):
        """Render a magical fantasy sword slash with energy crescents and sparkle effects."""
        import math
        import random
        
        # Magical sword slash - crescent-shaped energy wave
        angle_rad = math.radians(self.angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Sword slash dimensions - massive sweeping crescent
        slash_length = self.size * 12  # Long sweeping slash
        slash_width = max(self.size * 6, 20)  # Wide magical blade
        
        # Calculate crescent arc points for magical energy wave
        arc_points = []
        arc_segments = 16  # Smooth curved slash
        
        for i in range(arc_segments + 1):
            # Create curved crescent shape
            t = i / arc_segments
            curve_offset = math.sin(t * math.pi) * slash_width * 0.5  # Curved arc
            
            # Base position along slash length
            base_x = x + (t - 0.5) * slash_length * cos_angle
            base_y = y + (t - 0.5) * slash_length * sin_angle
            
            # Add perpendicular curve for crescent shape
            perp_x = base_x + curve_offset * (-sin_angle)
            perp_y = base_y + curve_offset * cos_angle
            
            arc_points.append((perp_x, perp_y))
        
        # Magical blade colors (mystical blue-white energy)
        blade_core = self.color  # Base sword color [200, 200, 255]
        blade_bright = (255, 255, 255)  # Brilliant white edge
        blade_glow = (150, 200, 255)  # Soft blue magical glow
        blade_energy = (100, 150, 255)  # Deep magical energy
        
        # Layer 1: Outer magical aura (largest)
        aura_width = int(slash_width * 2.5)
        self._draw_magical_crescent(screen, x, y, slash_length * 1.2, aura_width, (*blade_energy, 40))
        
        # Layer 2: Mid magical glow
        glow_width = int(slash_width * 1.8)
        self._draw_magical_crescent(screen, x, y, slash_length * 1.1, glow_width, (*blade_glow, 80))
        
        # Layer 3: Bright blade energy
        bright_width = int(slash_width * 1.3)
        self._draw_magical_crescent(screen, x, y, slash_length, bright_width, blade_bright)
        
        # Layer 4: Core blade
        core_width = max(int(slash_width * 0.8), 8)
        self._draw_magical_crescent(screen, x, y, slash_length * 0.9, core_width, blade_core)
        
        # Add magical sparkle particles around the slash
        sparkle_count = random.randint(8, 15)
        for _ in range(sparkle_count):
            sparkle_distance = random.uniform(slash_length * 0.3, slash_length * 0.7)
            sparkle_angle = self.angle + random.uniform(-30, 30)
            sparkle_angle_rad = math.radians(sparkle_angle)
            
            sparkle_x = x + math.cos(sparkle_angle_rad) * sparkle_distance
            sparkle_y = y + math.sin(sparkle_angle_rad) * sparkle_distance
            sparkle_size = random.randint(2, 5)
            sparkle_alpha = random.randint(120, 200)
            
            self._draw_magical_sparkle(screen, sparkle_x, sparkle_y, sparkle_size, (*blade_bright, sparkle_alpha))
        
        # Magical blade tip effect - concentrated energy point
        tip_x = x + cos_angle * slash_length * 0.5
        tip_y = y + sin_angle * slash_length * 0.5
        
        # Bright magical tip
        tip_size = int(slash_width * 0.8)
        pg.draw.circle(screen, blade_bright, (int(tip_x), int(tip_y)), tip_size)
        pg.draw.circle(screen, blade_core, (int(tip_x), int(tip_y)), int(tip_size * 0.6))
        
        # Energy trails from tip
        for i in range(3):
            trail_offset = (i + 1) * slash_length * 0.08
            trail_x = tip_x - cos_angle * trail_offset
            trail_y = tip_y - sin_angle * trail_offset
            trail_alpha = 180 - (i * 50)
            trail_size = max(int(slash_width * (0.6 - i * 0.15)), 2)
            
            if trail_alpha > 0:
                self._draw_magical_sparkle(screen, trail_x, trail_y, trail_size, (*blade_glow, trail_alpha))
    
    def _draw_magical_crescent(self, screen: pg.Surface, center_x: float, center_y: float, length: float, width: float, color: tuple):
        """Draw a curved magical crescent shape for sword slashes."""
        import math
        
        # Create points for curved crescent
        points = []
        segments = 12
        
        angle_rad = math.radians(self.angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Top curve of crescent
        for i in range(segments + 1):
            t = i / segments
            curve_strength = math.sin(t * math.pi) * width * 0.5
            
            base_x = center_x + (t - 0.5) * length * cos_angle
            base_y = center_y + (t - 0.5) * length * sin_angle
            
            curve_x = base_x + curve_strength * (-sin_angle)
            curve_y = base_y + curve_strength * cos_angle
            points.append((curve_x, curve_y))
        
        # Bottom curve of crescent (reverse direction)
        for i in range(segments, -1, -1):
            t = i / segments
            curve_strength = math.sin(t * math.pi) * width * 0.5
            
            base_x = center_x + (t - 0.5) * length * cos_angle
            base_y = center_y + (t - 0.5) * length * sin_angle
            
            curve_x = base_x - curve_strength * (-sin_angle)
            curve_y = base_y - curve_strength * cos_angle
            points.append((curve_x, curve_y))
        
        # Draw the crescent shape
        if len(color) == 4:  # Has alpha
            # Create surface for alpha blending
            bounds = self._get_polygon_bounds(points)
            if bounds[2] > bounds[0] and bounds[3] > bounds[1]:
                temp_surf = pg.Surface((int(bounds[2] - bounds[0] + 4), int(bounds[3] - bounds[1] + 4)), pg.SRCALPHA)
                adjusted_points = [(p[0] - bounds[0] + 2, p[1] - bounds[1] + 2) for p in points]
                
                if len(adjusted_points) >= 3:
                    pg.draw.polygon(temp_surf, color, adjusted_points)
                    screen.blit(temp_surf, (bounds[0] - 2, bounds[1] - 2), special_flags=pg.BLEND_ALPHA_SDL2)
        else:
            # Regular polygon without alpha
            if len(points) >= 3:
                pg.draw.polygon(screen, color, points)
    
    def _draw_magical_sparkle(self, screen: pg.Surface, x: float, y: float, size: int, color: tuple):
        """Draw magical sparkle effects for sword slashes."""
        if len(color) == 4:  # Has alpha
            # Create sparkle surface
            temp_surf = pg.Surface((size * 3, size * 3), pg.SRCALPHA)
            
            # Draw star-shaped sparkle
            center = (size * 1.5, size * 1.5)
            # Horizontal line
            pg.draw.line(temp_surf, color, (0, center[1]), (size * 3, center[1]), max(size // 2, 1))
            # Vertical line  
            pg.draw.line(temp_surf, color, (center[0], 0), (center[0], size * 3), max(size // 2, 1))
            # Diagonal lines for star effect
            pg.draw.line(temp_surf, color, (size // 2, size // 2), (size * 2.5, size * 2.5), max(size // 3, 1))
            pg.draw.line(temp_surf, color, (size * 2.5, size // 2), (size // 2, size * 2.5), max(size // 3, 1))
            
            screen.blit(temp_surf, (int(x - size * 1.5), int(y - size * 1.5)), special_flags=pg.BLEND_ALPHA_SDL2)
        else:
            # Simple circular sparkle without alpha
            pg.draw.circle(screen, color, (int(x), int(y)), size)
    
    def _draw_tracer_line(self, screen: pg.Surface, x1: float, y1: float, x2: float, y2: float, width: float, color: tuple):
        """Draw a tracer line with alpha blending for glow effects."""
        if len(color) == 4:  # Has alpha
            # Create surface for alpha blending
            import math
            line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            temp_surf = pg.Surface((int(line_length + width * 2), int(width * 2)), pg.SRCALPHA)
            
            # Draw line on temp surface
            start_point = (int(width), int(width))
            end_point = (int(line_length + width), int(width))
            pg.draw.line(temp_surf, color, start_point, end_point, int(width))
            
            # Rotate and blit the surface
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            rotated_surf = pg.transform.rotate(temp_surf, -angle)
            
            # Calculate position for rotated surface
            rect = rotated_surf.get_rect()
            rect.center = (int(x1 + (x2 - x1) / 2), int(y1 + (y2 - y1) / 2))
            screen.blit(rotated_surf, rect, special_flags=pg.BLEND_ALPHA_SDL2)
        else:
            # Regular line without alpha
            pg.draw.line(screen, color, (int(x1), int(y1)), (int(x2), int(y2)), int(width))

    def _get_polygon_bounds(self, points):
        """Get bounding box of polygon points."""
        if not points:
            return (0, 0, 0, 0)
        
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        return (min_x, min_y, max_x, max_y)
    
    def _draw_laser_line(self, screen: pg.Surface, x1: float, y1: float, x2: float, y2: float, width: float, color: tuple):
        """Draw a glowing laser line with alpha blending."""
        # Create a surface for alpha blending
        temp_surf = pg.Surface((abs(x2 - x1) + width * 2, abs(y2 - y1) + width * 2), pg.SRCALPHA)
        
        # Calculate relative positions
        rel_x1 = width
        rel_y1 = width
        rel_x2 = rel_x1 + (x2 - x1)
        rel_y2 = rel_y1 + (y2 - y1)
        
        # Draw the glowing line
        if width > 2:
            pg.draw.line(temp_surf, color, (int(rel_x1), int(rel_y1)), (int(rel_x2), int(rel_y2)), int(width))
        
        # Blit to main screen
        screen.blit(temp_surf, (min(x1, x2) - width, min(y1, y2) - width), special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _draw_laser_particles(self, screen: pg.Surface, tip_x: float, tip_y: float, angle_rad: float):
        """Draw optimized particle effects at the laser tip."""
        import math
        import random
        
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Create shorter streaming particle trail - reduced from 15 to 8
        for i in range(8):  # Reduced for performance
            trail_dist = i * 6  # Slightly increased spacing
            trail_x = tip_x - cos_angle * trail_dist
            trail_y = tip_y - sin_angle * trail_dist
            
            # Smaller random offset for better performance
            offset_x = random.uniform(-2, 2)  # Reduced spread
            offset_y = random.uniform(-2, 2)
            
            particle_size = max(1, 4 - i // 2)  # Smaller particles
            color = (255, min(255, 180 + i * 8), min(255, 120 + i * 12))
            
            pg.draw.circle(screen, color, (int(trail_x + offset_x), int(trail_y + offset_y)), particle_size)
        
        # Create fewer particle rings - reduced from 5 to 3
        for ring in range(3):  # Reduced rings for performance
            ring_radius = (ring + 1) * 6  # Slightly smaller radius
            particles = 8 + ring * 2  # Fewer particles per ring (was 12 + ring * 4)
            
            for i in range(particles):
                # Random particle position around the tip
                particle_angle = (i / particles) * 2 * math.pi + random.uniform(-0.3, 0.3)
                particle_dist = ring_radius + random.uniform(-3, 3)  # Reduced spread
                
                particle_x = tip_x + math.cos(particle_angle) * particle_dist
                particle_y = tip_y + math.sin(particle_angle) * particle_dist
                
                # Simplified particle colors with fewer conditionals
                if ring == 0:
                    color = (255, 255, 255)
                    size = 3  # Smaller center particles
                elif ring == 1:
                    color = (200, 230, 255)
                    size = 2
                else:  # ring == 2
                    color = (150, 200, 255)
                    size = 1
                
                # Reduced particle visibility check - 70% chance (was 80%)
                if random.random() > 0.3:
                    pg.draw.circle(screen, color, (int(particle_x), int(particle_y)), size)
        
        # Smaller center flash with less variation
        flash_size = 6 + int(random.uniform(-1, 1))  # Smaller flash
        pg.draw.circle(screen, (255, 255, 255), (int(tip_x), int(tip_y)), flash_size)
        pg.draw.circle(screen, (200, 240, 255), (int(tip_x), int(tip_y)), flash_size + 2, 1)  # Thinner ring
    
    def _draw_energy_crackling(self, screen: pg.Surface, back_x: float, back_y: float, front_x: float, front_y: float, beam_width: float):
        """Draw optimized energy crackling effects along the beam."""
        import math
        import random
        
        beam_length = math.sqrt((front_x - back_x)**2 + (front_y - back_y)**2)
        
        # Draw fewer energy crackles for performance
        num_crackles = max(int(beam_length / 25), 2)  # Fewer crackles (was /15)
        
        for i in range(num_crackles):
            # Position along the beam
            t = (i + 1) / (num_crackles + 1)
            base_x = back_x + (front_x - back_x) * t
            base_y = back_y + (front_y - back_y) * t
            
            # Smaller crackling offset for performance
            offset_dist = random.uniform(beam_width * 0.5, beam_width * 1.5)  # Reduced range
            offset_angle = random.uniform(0, 2 * math.pi)
            
            crack_x = base_x + math.cos(offset_angle) * offset_dist
            crack_y = base_y + math.sin(offset_angle) * offset_dist
            
            # Draw crackling line - simpler color logic
            color = (200, 230, 255) if random.random() > 0.5 else (255, 255, 255)
            pg.draw.line(screen, color, (int(base_x), int(base_y)), (int(crack_x), int(crack_y)), 1)
    
    def get_rect(self) -> pg.Rect:
        """Get collision rectangle for the bullet."""
        # Calculate effective collision size based on shape
        effective_size = self.size
        if hasattr(self, 'shape') and self.shape == "laser":
            # Laser bullets (sniper) have much larger visual beam width
            # Match the visual beam_width = max(size * 4, 24)
            effective_size = max(self.size * 4, 24) / 2  # Divide by 2 since we're using radius
        
        return pg.Rect(self.pos.x - effective_size, self.pos.y - effective_size,
                      effective_size * 2, effective_size * 2)

class BurningTrail:
    """A burning trail segment left behind by special sniper bullets."""
    
    def __init__(self, x: float, y: float, duration: float = 2.5, damage: float = 12):
        """Initialize a burning trail segment.
        
        Args:
            x, y: Position of the trail segment
            duration: How long the trail segment burns (seconds)
            damage: Damage per second to enemies touching this segment
        """
        self.pos = pg.Vector2(x, y)
        self.radius = 40  # Larger radius for better visibility
        self.damage_per_second = damage
        self.duration = duration
        self.age = 0.0
        self.damaged_enemies = set()  # Track recently damaged enemies
        self.damage_cooldown = 0.3  # Seconds between damage ticks per enemy
        self.last_damage_times = {}  # Track last damage time per enemy
        
        # Visual properties for trail fire animation
        self.flame_flicker_time = 0.0
        self._initialize_trail_particles()
    
    def _initialize_trail_particles(self):
        """Initialize trail fire particles for visual effects."""
        import random
        import math
        
        # Create fire particles for the trail segment
        self.fire_particles = []
        
        # Create more fire particles in a line-like pattern for better visibility
        particle_count = 20  # Increased count for trail segments
        for _ in range(particle_count):
            # Position particles in a small area around the trail point
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.radius * 0.9)
            x = self.pos.x + math.cos(angle) * distance
            y = self.pos.y + math.sin(angle) * distance
            self.fire_particles.append({
                'x': x, 'y': y,
                'base_x': x, 'base_y': y,
                'size': random.uniform(6, 14),  # Larger particles
                'intensity': random.uniform(0.9, 1.4),
                'flicker_speed': random.uniform(8, 15),
                'color_variant': random.uniform(0.9, 1.1)
            })
    
    def update(self, dt: float) -> bool:
        """Update the burning trail. Returns True if it should be removed."""
        self.age += dt
        self.flame_flicker_time += dt
        
        # Update particle animation
        import math
        for particle in self.fire_particles:
            flicker = math.sin(self.flame_flicker_time * particle['flicker_speed']) * 0.3
            particle['size'] = particle['size'] + flicker
            particle['intensity'] = max(0.5, particle['intensity'] + flicker * 0.2)
        
        return self.age >= self.duration
    
    def render(self, screen: pg.Surface, offset: pg.Vector2):
        """Render the burning trail segment."""
        if self.age >= self.duration:
            return
        
        # Calculate fade out effect near end of duration
        fade_start = self.duration * 0.7  # Start fading at 70% of duration
        alpha = 1.0
        if self.age > fade_start:
            fade_progress = (self.age - fade_start) / (self.duration - fade_start)
            alpha = max(0.0, 1.0 - fade_progress)
        
        # Render fire particles
        import random
        for particle in self.fire_particles:
            # Calculate screen position (add offset like ground fire does)
            screen_x = particle['x'] + offset.x
            screen_y = particle['y'] + offset.y
            
            # Skip if off screen
            if (screen_x < -50 or screen_x > screen.get_width() + 50 or
                screen_y < -50 or screen_y > screen.get_height() + 50):
                continue
            
            # Fire color gradient (blue flames for sniper special attack)
            base_intensity = particle['intensity'] * alpha * particle['color_variant']
            blue = min(255, int(255 * base_intensity))
            cyan = min(255, int(180 * base_intensity * 0.9))
            white = min(150, int(100 * base_intensity * 0.6))
            
            color = (white, cyan, blue)  # Blue fire effect
            size = max(1, int(particle['size'] * alpha))
            
            # Draw fire particle
            if size > 0:
                pg.draw.circle(screen, color, (int(screen_x), int(screen_y)), size)
                # Add glow effect with blue tones
                if size > 2:
                    glow_color = (min(255, white + 30), min(255, cyan + 50), min(255, blue + 30))
                    pg.draw.circle(screen, glow_color, (int(screen_x), int(screen_y)), size // 2)
    
    def can_damage_enemy(self, enemy, current_time: float) -> bool:
        """Check if this trail segment can damage the given enemy."""
        enemy_id = id(enemy)
        
        # Check if enemy is in damage radius
        enemy_pos = pg.Vector2(enemy.pos[0], enemy.pos[1]) if hasattr(enemy, 'pos') else pg.Vector2(enemy.x, enemy.y)
        distance = self.pos.distance_to(enemy_pos)
        
        if distance > self.radius:
            return False
        
        # Check damage cooldown
        if enemy_id in self.last_damage_times:
            time_since_last_damage = current_time - self.last_damage_times[enemy_id]
            if time_since_last_damage < self.damage_cooldown:
                return False
        
        # Update last damage time
        self.last_damage_times[enemy_id] = current_time
        return True


class BulletManager:
    """Manages all bullets in the game."""
    
    def __init__(self):
        """Initialize the bullet manager."""
        self.bullets: List[Bullet] = []
        
        # Shooting mechanics
        self.last_shot_time = 0.0
        self.fire_rate = 0.1  # Default seconds between shots (10 shots per second)
        
        # Minigun spin-up mechanics
        self.is_firing_continuously = False
        self.continuous_fire_start_time = 0.0
        self.base_fire_rate = 0.1  # Store the weapon's normal fire rate
        self.current_fire_rate = 0.1  # Dynamic fire rate that changes during spin-up
        self.minigun_reload_reset = False  # Flag to prevent spin-up restart until fire button released
        
        # Burning trail system for special sniper bullets
        self.burning_trails = []  # List of active burning trail segments
    
    def set_fire_rate(self, fire_rate: float):
        """Set the fire rate for bullets."""
        self.fire_rate = fire_rate
        self.base_fire_rate = fire_rate  # Store base rate for minigun spin-up calculations
        self.current_fire_rate = fire_rate
    
    def start_continuous_fire(self, current_time: float, weapon_type: str = None):
        """Start continuous firing (for minigun spin-up mechanics)."""
        # Don't start continuous fire if we just reset from reload and fire button is still held
        if self.minigun_reload_reset and weapon_type == "Minigun":
            return  # Wait for fire button to be released first
            
        # Don't start continuous fire if we're not already firing continuously
        if not self.is_firing_continuously:
            self.is_firing_continuously = True
            self.continuous_fire_start_time = current_time
            
            # Set initial fire rate for minigun
            if weapon_type == "Minigun":
                from src.weapons.weapon_manager import weapon_manager
                initial_rate = weapon_manager.get_weapon_property(weapon_type, 'special_mechanics', 'initial_fire_rate', self.base_fire_rate)
                self.current_fire_rate = initial_rate
    
    def stop_continuous_fire(self, weapon_type=None):
        """Stop continuous firing and reset fire rate."""
        was_firing = self.is_firing_continuously
        self.is_firing_continuously = False
        
        # For minigun, reset to initial slow rate, not base fast rate
        if weapon_type == "Minigun":
            from src.weapons.weapon_manager import weapon_manager
            initial_rate = weapon_manager.get_weapon_property(weapon_type, 'special_mechanics', 'initial_fire_rate', self.base_fire_rate)
            self.current_fire_rate = initial_rate
            # Clear the reload reset flag when fire button is released
            self.minigun_reload_reset = False
            if was_firing:  # Only print if we were actually firing continuously
                pass  # Spin-down complete
        else:
            self.current_fire_rate = self.base_fire_rate
            
        # Clear the reload reset flag when fire button is released for non-minigun weapons
        if weapon_type != "Minigun":
            self.minigun_reload_reset = False
    
    def update_minigun_fire_rate(self, current_time: float, weapon_type: str):
        """Update fire rate for minigun spin-up effect."""
        if weapon_type == "Minigun" and self.is_firing_continuously:
            from src.weapons.weapon_manager import weapon_manager
            
            spin_up_duration = weapon_manager.get_weapon_property(weapon_type, 'special_mechanics', 'spin_up_time', 1.5)
            initial_rate = weapon_manager.get_weapon_property(weapon_type, 'special_mechanics', 'initial_fire_rate', self.base_fire_rate)
            
            # Calculate how long we've been firing continuously
            fire_duration = current_time - self.continuous_fire_start_time
            
            # Interpolate between initial rate and full rate
            if fire_duration >= spin_up_duration:
                # Fully spun up
                self.current_fire_rate = self.base_fire_rate
            else:
                # Interpolate between initial (slow) and full (fast) rate
                progress = fire_duration / spin_up_duration
                # Use smooth interpolation (ease-out curve)
                progress = 1 - (1 - progress) ** 2
                self.current_fire_rate = initial_rate + (self.base_fire_rate - initial_rate) * progress
    
    def can_shoot(self, current_time: float) -> bool:
        """Check if enough time has passed since last shot."""
        # Clear any stuck reload reset flag after reasonable time
        if self.minigun_reload_reset:
            # Clear the flag after 0.1 seconds to prevent getting stuck
            if (current_time - self.last_shot_time) > 0.1:
                self.minigun_reload_reset = False
            
        return current_time - self.last_shot_time >= self.current_fire_rate
    
    def create_bullet(self, x: float, y: float, angle: float, bullet_type: BulletType = BulletType.PLAYER, damage: int = None, speed: float = 800, size_multiplier: float = 1.0, color: tuple = None, penetration: int = 1, shape: str = None, range_limit: float = None, weapon_type: str = None, lighting_system=None, special_attack: bool = False, bounce_enabled: bool = False, max_bounces: int = 0, bounce_range: float = None, enemy_targeting: bool = False, trail_enabled: bool = False, trail_duration: float = 0.0, target_pos: tuple = None):
        """Create a bullet without fire rate checking (used for multi-pellet weapons)."""
        from src.entities.bullet import Bullet
        
        # Add muzzle flash lighting effect for shotgun pellets (reduced intensity per pellet)
        if lighting_system and bullet_type == BulletType.PLAYER:
            print(f"Shotgun pellet - adding muzzle flash for weapon: {weapon_type}")
            lighting_system.add_muzzle_flash(x, y, intensity=0.5, weapon_type=weapon_type or "default")
        
        return Bullet(x, y, angle, bullet_type, speed=speed, damage=damage, size_multiplier=size_multiplier, color=color, penetration=penetration, shape=shape, range_limit=range_limit, weapon_type=weapon_type, special_attack=special_attack, bounce_enabled=bounce_enabled, max_bounces=max_bounces, bounce_range=bounce_range, enemy_targeting=enemy_targeting, trail_enabled=trail_enabled, trail_duration=trail_duration, target_pos=target_pos)
    
    def shoot(self, x: float, y: float, angle: float, current_time: float, bullet_type: BulletType = BulletType.PLAYER, damage: int = None, speed: float = 800, size_multiplier: float = 1.0, color: tuple = None, penetration: int = 1, shape: str = None, range_limit: float = None, weapon_type: str = None, lighting_system=None, special_attack: bool = False, bounce_enabled: bool = False, max_bounces: int = 0, bounce_range: float = None, enemy_targeting: bool = False, trail_enabled: bool = False, trail_duration: float = 0.0) -> bool:
        """Create a new bullet if fire rate allows. Returns True if bullet was fired."""
        if self.can_shoot(current_time):
            bullet = Bullet(x, y, angle, bullet_type, speed=speed, damage=damage, size_multiplier=size_multiplier, color=color, penetration=penetration, shape=shape, range_limit=range_limit, weapon_type=weapon_type, special_attack=special_attack, bounce_enabled=bounce_enabled, max_bounces=max_bounces, bounce_range=bounce_range, enemy_targeting=enemy_targeting, trail_enabled=trail_enabled, trail_duration=trail_duration)
            self.bullets.append(bullet)
            self.last_shot_time = current_time
            
            # Add muzzle flash lighting effect
            if lighting_system and bullet_type == BulletType.PLAYER:
                print(f"Bullet shot - adding muzzle flash for weapon: {weapon_type}")
                lighting_system.add_muzzle_flash(x, y, intensity=1.0, weapon_type=weapon_type or "default")
            elif not lighting_system:
                print("No lighting system provided to bullet shoot")
            
            return True
        return False
    
    def shoot_enemy_laser(self, x: float, y: float, angle: float, current_time: float):
        """Create an enemy laser bullet (no fire rate limit for enemies)."""
        bullet = Bullet(x, y, angle, BulletType.ENEMY_LASER, speed=300)  # Reduced speed for visibility
        self.bullets.append(bullet)
    
    def update(self, dt: float, current_game_time: float = None, world_manager=None, impact_sparks_manager=None):
        """Update all bullets and remove expired ones."""
        # Update bullets and mark for removal
        bullets_to_remove = []
        
        for bullet in self.bullets:
            # Store previous position for impact angle calculation
            old_pos = bullet.pos.copy()
            
            # Check if bullet should be removed due to wall collision or other reasons
            should_remove = bullet.update(dt, current_game_time, world_manager)
            
            # If bullet was removed due to wall collision, create impact sparks
            if should_remove and world_manager and impact_sparks_manager:
                # Check if removal was due to wall collision
                if (world_manager.is_position_blocked_by_map(bullet.pos.x, bullet.pos.y) and
                    not world_manager.is_position_blocked_by_map(old_pos.x, old_pos.y)):
                    # Bullet hit a wall - calculate impact angle
                    impact_angle = math.atan2(bullet.velocity.y, bullet.velocity.x) if bullet.velocity.length() > 0 else 0
                    impact_sparks_manager.add_impact_sparks(bullet.pos.x, bullet.pos.y, impact_angle)
            
            # Create burning trail segments for special sniper bullets
            if not should_remove and bullet.trail_enabled and current_game_time is not None:
                # Create trail segments for all recorded trail points that don't have segments yet
                if len(bullet.trail_points) > 1:  # Need at least 2 points
                    # Create segments for older trail points (not the most recent ones)
                    points_to_process = bullet.trail_points[:-2] if len(bullet.trail_points) > 2 else []
                    
                    for trail_data in points_to_process:
                        # Create a burning trail segment at this position
                        trail_segment = BurningTrail(
                            trail_data['pos'].x, trail_data['pos'].y,
                            duration=bullet.trail_duration,
                            damage=12
                        )
                        self.burning_trails.append(trail_segment)
                    
                    # Remove processed points to avoid duplicates
                    bullet.trail_points = bullet.trail_points[-(min(3, len(bullet.trail_points))):]
            
            # When bullet is removed, create final trail segments for any remaining trail points
            if should_remove and bullet.trail_enabled:
                for trail_data in bullet.trail_points:
                    trail_segment = BurningTrail(
                        trail_data['pos'].x, trail_data['pos'].y,
                        duration=bullet.trail_duration,
                        damage=12
                    )
                    self.burning_trails.append(trail_segment)
            
            if should_remove:
                bullets_to_remove.append(bullet)
                
                # Check if this is a grenade that should explode
                if hasattr(bullet, 'explode_at_target') and bullet.explode_at_target and hasattr(bullet, 'is_grenade') and bullet.is_grenade:
                    # Store grenade explosion data for main game to handle
                    bullet.create_explosion = True
                    bullet.explosion_pos = bullet.pos.copy()
        
        # Remove expired bullets (but keep grenades that need to explode for main game to handle)
        for bullet in bullets_to_remove:
            # If this is a grenade that should explode, don't remove it yet - let main game handle it
            if hasattr(bullet, 'create_explosion') and bullet.create_explosion:
                continue  # Skip removal, let main game handle explosion and removal
            self.bullets.remove(bullet)
        
        # Update burning trails
        trails_to_remove = []
        for trail in self.burning_trails:
            if trail.update(dt):
                trails_to_remove.append(trail)
        
        # Remove expired trails
        for trail in trails_to_remove:
            self.burning_trails.remove(trail)
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render all bullets and burning trails."""
        # Render burning trails first (behind bullets)
        offset_vector = pg.Vector2(offset) if isinstance(offset, (tuple, list)) else offset
        for trail in self.burning_trails:
            trail.render(screen, offset_vector)
        
        # Render bullets
        for bullet in self.bullets:
            bullet.render(screen, offset)
    
    def create_network_bullet(self, x: float, y: float, velocity_x: float, velocity_y: float, 
                             damage: int, weapon_type: str, special_attack: bool = False, 
                             owner_id: str = None, shape: str = "standard", 
                             size_multiplier: float = 1.0, color: tuple = None, 
                             penetration: int = 1, bounce_enabled: bool = False, 
                             max_bounces: int = 0, bounce_range: float = None, 
                             enemy_targeting: bool = False, trail_enabled: bool = False, 
                             trail_duration: float = 0.0, range_limit: float = None):
        """Create a network bullet from another player (visual only, no local collision)."""
        import math
        
        # Debug logging for network bullet creation
        # Only log special attacks to reduce spam
        if special_attack:
            print(f"[NETWORK_BULLET] Creating special attack: {weapon_type}")
        # Removed normal bullet logging to reduce debug spam
        
        # Calculate angle from velocity
        angle = math.degrees(math.atan2(velocity_y, velocity_x))
        speed = math.sqrt(velocity_x**2 + velocity_y**2)
        
        # Use transmitted color or determine bullet color from weapon properties
        bullet_color = color
        if bullet_color is None:
            if special_attack:
                bullet_color = (255, 0, 0)  # Bright red for special attack visual effects
            else:
                # Get weapon-specific color for normal bullets
                try:
                    from src.weapons.weapon_manager import weapon_manager
                    weapon_props = weapon_manager.get_bullet_properties(weapon_type)
                    weapon_color = weapon_props.get("color", [255, 255, 255])
                    # Convert list to tuple if needed
                    if isinstance(weapon_color, list):
                        bullet_color = tuple(weapon_color)
                    else:
                        bullet_color = weapon_color
                except:
                    bullet_color = (255, 255, 255)  # Fall back to default bullet color
        
        # Create bullet with all transmitted network properties - preserve full appearance
        bullet = Bullet(
            x, y, angle, 
            BulletType.PLAYER,  # Use player type to get proper appearance
            speed=speed, 
            damage=damage, 
            weapon_type=weapon_type, 
            special_attack=special_attack,
            color=bullet_color,
            size_multiplier=size_multiplier,
            shape=shape,
            penetration=penetration,
            bounce_enabled=bounce_enabled,
            max_bounces=max_bounces,
            bounce_range=bounce_range,
            enemy_targeting=enemy_targeting,
            trail_enabled=trail_enabled,
            trail_duration=trail_duration,
            range_limit=range_limit
        )
        
        # Mark as network bullet but preserve full appearance
        bullet.is_network_bullet = True
        bullet.owner_id = owner_id
        
        # Set velocity directly (don't recalculate from angle)
        bullet.velocity = pg.Vector2(velocity_x, velocity_y)
        
        self.bullets.append(bullet)
        return bullet

    def get_bullets(self) -> List[Bullet]:
        """Get list of all active bullets."""
        return self.bullets
    
    def remove_bullet(self, bullet: Bullet):
        """Remove a specific bullet (for collision handling)."""
        if bullet in self.bullets:
            self.bullets.remove(bullet)
    
    def clear(self):
        """Remove all bullets and burning trails."""
        self.bullets.clear()
        self.burning_trails.clear()
    
    def get_bullet_count(self) -> int:
        """Get the number of active bullets."""
        return len(self.bullets)
    
    def check_burning_trail_damage(self, enemies, current_time: float) -> list:
        """Check if enemies are taking damage from burning trails.
        
        Returns:
            list: List of tuples (enemy, damage) for enemies taking trail damage
        """
        damage_events = []
        
        for trail in self.burning_trails:
            for enemy in enemies:
                if trail.can_damage_enemy(enemy, current_time):
                    damage_events.append((enemy, trail.damage_per_second))
        
        return damage_events
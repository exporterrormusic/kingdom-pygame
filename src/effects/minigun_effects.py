"""
Minigun visual enhancement system.
Handles muzzle flames, barrel spin effects, and enhanced bullet rendering for minigun.
"""

import pygame as pg
import math
import random
from typing import Tuple
from .base_trail_renderer import MinigunTrailRenderer
from .base_particle_system import BaseParticleSystem
from .base_weapon_effects import BaseWeaponEffectsManager

class MinigunEffectsManager(BaseWeaponEffectsManager):
    """Manages visual effects for the minigun weapon."""
    
    def __init__(self, lighting_system=None):
        """Initialize the minigun effects manager."""
        super().__init__(lighting_system)
        
        # Legacy minigun-specific effects (keeping for compatibility)
        self.muzzle_flames = []  # Now handled by base class
        self.shell_casings = []  # Now handled by base class
        
        # Minigun-specific barrel effects
        self.barrel_rotation = 0.0  # Current barrel rotation angle
        self.spin_speed = 0.0  # Current barrel spin speed
        self.max_spin_speed = 720.0  # Maximum degrees per second
        self.spin_up_time = 3.0  # Time to reach full spin
        self.is_spinning = False
        
        # Initialize trail renderer
        self.trail_renderer = MinigunTrailRenderer(lighting_system)
        
        # Initialize particle system for impact sparks
        self.spark_system = BaseParticleSystem(lighting_system)
        
        # Whip trail system for full-speed effect
        self.whip_trail_active = False
        self.whip_segments = []  # Active damage whip segments (line segments between bullets)
        self.whip_damage_segments = []  # Track damage-dealing line segments
        
        # Effect timing (legacy, now handled by base class)
        self.last_flame_time = 0.0
        self.last_shell_time = 0.0
        self.flame_interval = 0.02  # Interval between flame spawns at full speed
        self.shell_interval = 0.05  # Interval between shell ejections
        
    def update(self, dt: float, is_firing: bool, fire_rate: float, gun_tip_pos: Tuple[float, float], gun_angle: float):
        """Update minigun effects with whip trail system."""
        # Update base weapon effects (muzzle flashes, shell casings)
        super().update(dt)
        
        # Update barrel spin
        self._update_barrel_spin(dt, is_firing, fire_rate)
        
        # Determine if at full speed (fire rate at minimum = full speed)
        at_full_speed = is_firing and fire_rate <= 0.03  # Full speed when fire rate is at minimum
        
        # Update whip trail system
        self.whip_trail_active = at_full_speed
        if at_full_speed:
            self._update_whip_trail(dt, gun_tip_pos, gun_angle)
        else:
            # Let existing whip effects fade
            self._fade_whip_trail(dt)
        
        # Legacy cleanup - now handled by base class
        self.muzzle_flames = []  # No more muzzle spark effects
        self.shell_casings = []  # No shell casings
        
        # Update spark system
        self.spark_system.update(dt)
        
        # Clear damage segments - they're rebuilt each frame
        self.whip_damage_segments = []
        
    def _update_barrel_spin(self, dt: float, is_firing: bool, fire_rate: float):
        """Update barrel rotation with dramatic anime-style spin effects."""
        if is_firing:
            # Anime-style dramatic spin up based on fire rate
            target_speed = self.max_spin_speed * (1.0 - fire_rate / 0.03)
            if self.spin_speed < target_speed:
                # Faster, more dramatic spin-up for anime effect
                spin_acceleration = (self.max_spin_speed / self.spin_up_time) * 2.5  # 2.5x faster spin-up
                self.spin_speed = min(target_speed, self.spin_speed + spin_acceleration * dt)
        else:
            # Slower, more dramatic spin-down for anime effect
            spin_deceleration = (self.max_spin_speed / (self.spin_up_time * 3))  # 3x slower spin-down
            self.spin_speed = max(0, self.spin_speed - spin_deceleration * dt)
        
        # Update rotation angle with overdramatic speed
        self.barrel_rotation += self.spin_speed * dt
        if self.barrel_rotation >= 360:
            self.barrel_rotation -= 360
            
    def _update_whip_trail(self, dt: float, gun_tip_pos: Tuple[float, float], gun_angle: float):
        """Update damage whip trail system."""
        # The particle system handles updating automatically
        pass
    
    def _fade_whip_trail(self, dt: float):
        """Fade out whip trail effects when not at full speed."""
        # The particle system handles fading automatically
        pass
            
    def update_whip_trail_with_bullets(self, bullets, offset=(0, 0)):
        """Update damage whip trail - create damage segments along curved bullet paths."""
        if not self.whip_trail_active or len(bullets) < 2:
            self.whip_damage_segments = []
            return
            
        # Use the shared trail renderer to generate damage segments
        self.whip_damage_segments = self.trail_renderer.generate_damage_segments(bullets, damage=6, width=12)
    
    def create_impact_spark(self, x: float, y: float):
        """Create a small impact spark when enemy hits the whip."""
        # Use the new particle system for impact sparks
        self.spark_system.add_particles(
            x, y, 
            particle_type="impact",
            count=1,
            velocity_x=random.uniform(-50, 50),
            velocity_y=random.uniform(-50, 50),
            color=random.choice([
                (100, 220, 255),  # Bright cyan to match bullet inner core
                (150, 240, 255),  # Electric cyan
                (200, 250, 255),  # Bright white-cyan
                (255, 255, 255)   # Pure white for brightness
            ]),
            size=random.uniform(2, 4),
            lifetime=random.uniform(0.15, 0.25)
        )
        
    def get_whip_damage_segments(self):
        """Get current damage segments for collision checking."""
        return self.whip_damage_segments
        
    def check_whip_collision(self, enemy_x: float, enemy_y: float, enemy_radius: float):
        """Check if an enemy collides with any whip damage segment.
        Returns (hit, damage, hit_x, hit_y) tuple."""
        if not self.whip_trail_active:
            return False, 0, 0, 0
            
        for segment in self.whip_damage_segments:
            # Check line-to-circle collision
            hit, hit_x, hit_y = self._line_circle_collision(
                segment['start_x'], segment['start_y'],
                segment['end_x'], segment['end_y'],
                enemy_x, enemy_y, enemy_radius + segment['width']
            )
            
            if hit:
                return True, segment['damage'], hit_x, hit_y
                
        return False, 0, 0, 0
    
    def _line_circle_collision(self, x1: float, y1: float, x2: float, y2: float, 
                             cx: float, cy: float, radius: float):
        """Check collision between line segment (x1,y1)-(x2,y2) and circle at (cx,cy) with radius.
        Returns (collision, closest_x, closest_y)."""
        
        # Vector from start to end of line
        dx = x2 - x1
        dy = y2 - y1
        
        # Vector from start of line to circle center
        fx = cx - x1
        fy = cy - y1
        
        # Handle zero-length line segment
        line_length_sq = dx * dx + dy * dy
        if line_length_sq == 0:
            # Line is a point, check distance to circle center
            dist_sq = fx * fx + fy * fy
            if dist_sq <= radius * radius:
                return True, x1, y1
            return False, x1, y1
        
        # Parameter t for closest point on line to circle center
        t = max(0, min(1, (fx * dx + fy * dy) / line_length_sq))
        
        # Closest point on line segment to circle center
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from circle center to closest point
        dist_x = cx - closest_x
        dist_y = cy - closest_y
        distance_sq = dist_x * dist_x + dist_y * dist_y
        
        # Check if collision occurs
        collision = distance_sq <= radius * radius
        return collision, closest_x, closest_y
                
    def render_muzzle_flames(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render impact sparks when enemies hit the damage whip."""
        # Use the new particle system to render impact sparks
        self.spark_system.render(screen, offset)
        
        # Also render base class muzzle flashes
        super().render_muzzle_flashes(screen, offset)
                    
    def render_whip_trail_lines(self, screen: pg.Surface, bullets, offset: Tuple[float, float] = (0, 0)):
        """Render thick, curved glowing lines connecting bullets when at full speed."""
        if not self.whip_trail_active or len(bullets) < 2:
            return
            
        # Use the shared trail renderer
        self.trail_renderer.render_bullet_trail_lines(screen, bullets, offset)
    def render_shell_casings(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render shell casings - now handled by base class but disabled for minigun."""
        # Base class handles shell casings but minigun has them disabled for clean look
        # super().render_shell_casings(screen, offset)  # Commented out for clean whip trail aesthetic
        pass
        
    def get_spin_intensity(self) -> float:
        """Get current spin intensity (0.0 to 1.0)."""
        return self.spin_speed / self.max_spin_speed
        
    def is_at_full_speed(self) -> bool:
        """Check if minigun is at full spinning speed."""
        return self.spin_speed >= self.max_spin_speed * 0.9
"""
Base weapon effects system for consolidating common weapon effect patterns.
Handles muzzle flashes, shell casings, and impact effects for all weapon types.
"""

import pygame as pg
import math
import random
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional


class BaseMuzzleFlash(ABC):
    """Abstract base class for muzzle flash effects."""
    
    def __init__(self, x: float, y: float, angle: float, weapon_type: str):
        self.x = x
        self.y = y
        self.angle = angle
        self.weapon_type = weapon_type
        self.age = 0.0
        self.max_lifetime = self._get_lifetime()
        self.particles = []
        self._generate_particles()
    
    @abstractmethod
    def _get_lifetime(self) -> float:
        """Get the lifetime for this muzzle flash type."""
        pass
    
    @abstractmethod
    def _get_particle_properties(self) -> Dict[str, Any]:
        """Get particle properties specific to this weapon type."""
        pass
    
    def _generate_particles(self):
        """Generate muzzle flash particles based on weapon type."""
        props = self._get_particle_properties()
        
        for _ in range(props['count']):
            # Calculate particle angle with spread
            spread_angle = random.uniform(-props['spread']/2, props['spread']/2)
            particle_angle = math.radians(self.angle + spread_angle)
            
            # Calculate velocity
            speed = random.uniform(props['min_speed'], props['max_speed'])
            velocity = pg.Vector2(
                math.cos(particle_angle) * speed,
                math.sin(particle_angle) * speed
            )
            
            particle = {
                'pos': pg.Vector2(self.x, self.y),
                'velocity': velocity,
                'color': props['color'],
                'size': random.uniform(props['min_size'], props['max_size']),
                'life': random.uniform(props['min_life'], props['max_life']),
                'initial_life': random.uniform(props['min_life'], props['max_life']),
                'fade_speed': props.get('fade_speed', 0.95)
            }
            self.particles.append(particle)
    
    def update(self, dt: float) -> bool:
        """Update muzzle flash. Returns True if should be removed."""
        self.age += dt
        
        particles_to_remove = []
        for particle in self.particles:
            particle['pos'] += particle['velocity'] * dt
            particle['life'] -= dt
            particle['velocity'] *= particle['fade_speed']
            
            if particle['life'] <= 0:
                particles_to_remove.append(particle)
        
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        return self.age >= self.max_lifetime or len(self.particles) == 0
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render muzzle flash particles."""
        for particle in self.particles:
            if particle['life'] > 0:
                # Calculate alpha based on remaining life
                life_ratio = particle['life'] / particle['initial_life']
                alpha = max(0, min(255, int(255 * life_ratio)))
                
                # Render position
                render_x = int(particle['pos'].x + offset[0])
                render_y = int(particle['pos'].y + offset[1])
                
                # Create color with alpha
                color = (*particle['color'], alpha)
                size = max(1, int(particle['size'] * life_ratio))
                
                try:
                    pg.draw.circle(screen, color[:3], (render_x, render_y), size)
                except (ValueError, OverflowError):
                    pass


class AssaultRifleMuzzleFlash(BaseMuzzleFlash):
    """Muzzle flash effect for assault rifles."""
    
    def _get_lifetime(self) -> float:
        return 0.15
    
    def _get_particle_properties(self) -> Dict[str, Any]:
        return {
            'count': 12,
            'spread': 45,
            'min_speed': 200,
            'max_speed': 400,
            'color': (255, 220, 180),
            'min_size': 2,
            'max_size': 5,
            'min_life': 0.08,
            'max_life': 0.12,
            'fade_speed': 0.92
        }


class ShotgunMuzzleFlash(BaseMuzzleFlash):
    """Muzzle flash effect for shotguns."""
    
    def _get_lifetime(self) -> float:
        return 0.2
    
    def _get_particle_properties(self) -> Dict[str, Any]:
        return {
            'count': 18,
            'spread': 60,
            'min_speed': 150,
            'max_speed': 350,
            'color': (255, 200, 100),
            'min_size': 3,
            'max_size': 7,
            'min_life': 0.1,
            'max_life': 0.18,
            'fade_speed': 0.88
        }


class SMGMuzzleFlash(BaseMuzzleFlash):
    """Muzzle flash effect for SMGs."""
    
    def _get_lifetime(self) -> float:
        return 0.12
    
    def _get_particle_properties(self) -> Dict[str, Any]:
        return {
            'count': 8,
            'spread': 30,
            'min_speed': 250,
            'max_speed': 450,
            'color': (200, 220, 255),
            'min_size': 1,
            'max_size': 4,
            'min_life': 0.06,
            'max_life': 0.1,
            'fade_speed': 0.95
        }


class MinigunMuzzleFlash(BaseMuzzleFlash):
    """Muzzle flash effect for miniguns."""
    
    def _get_lifetime(self) -> float:
        return 0.08
    
    def _get_particle_properties(self) -> Dict[str, Any]:
        return {
            'count': 6,
            'spread': 25,
            'min_speed': 300,
            'max_speed': 500,
            'color': (100, 220, 255),
            'min_size': 1,
            'max_size': 3,
            'min_life': 0.04,
            'max_life': 0.08,
            'fade_speed': 0.98
        }


class BaseShellCasing:
    """Base class for shell casing effects."""
    
    def __init__(self, x: float, y: float, angle: float, weapon_type: str):
        self.pos = pg.Vector2(x, y)
        self.weapon_type = weapon_type
        self.age = 0.0
        self.max_lifetime = 3.0
        
        # Calculate ejection properties
        eject_angle = math.radians(angle + random.uniform(70, 110))  # Perpendicular to barrel
        eject_speed = random.uniform(80, 150)
        
        self.velocity = pg.Vector2(
            math.cos(eject_angle) * eject_speed,
            math.sin(eject_angle) * eject_speed
        )
        
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-720, 720)  # degrees per second
        
        # Visual properties based on weapon type
        self.size, self.color = self._get_visual_properties()
        
        # Physics properties
        self.bounce_factor = 0.3
        self.friction = 0.85
        self.gravity = 400
        self.bounced = False
    
    def _get_visual_properties(self) -> Tuple[int, Tuple[int, int, int]]:
        """Get size and color based on weapon type."""
        if self.weapon_type == "Assault Rifle":
            return (6, (255, 215, 100))  # Medium brass
        elif self.weapon_type == "Shotgun":
            return (8, (255, 200, 80))   # Large red shell
        elif self.weapon_type == "SMG":
            return (4, (220, 220, 180))  # Small brass
        elif self.weapon_type == "Minigun":
            return (5, (200, 200, 150))  # Medium steel
        else:
            return (5, (255, 215, 100))  # Default brass
    
    def update(self, dt: float) -> bool:
        """Update shell casing physics. Returns True if should be removed."""
        self.age += dt
        
        # Apply gravity
        self.velocity.y += self.gravity * dt
        
        # Update position
        self.pos += self.velocity * dt
        
        # Update rotation
        self.rotation += self.rotation_speed * dt
        
        # Simple ground collision (assuming ground at y > some value)
        # This is a simplified version - could be improved with actual ground detection
        if not self.bounced and self.velocity.y > 0 and self.pos.y > 500:  # Rough ground level
            self.velocity.y *= -self.bounce_factor
            self.velocity.x *= self.friction
            self.rotation_speed *= 0.5
            self.bounced = True
        
        # Fade out over time
        return self.age >= self.max_lifetime
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render shell casing."""
        if self.age >= self.max_lifetime:
            return
        
        # Calculate alpha based on age
        if self.age > 2.0:
            alpha_factor = 1.0 - ((self.age - 2.0) / 1.0)  # Fade in last second
        else:
            alpha_factor = 1.0
        
        alpha = max(0, min(255, int(255 * alpha_factor)))
        
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        # Simple rectangle representing shell casing
        color = (*self.color, alpha)
        
        try:
            # Create a small rotated rectangle for the shell
            points = []
            for dx, dy in [(-self.size//2, -2), (self.size//2, -2), 
                          (self.size//2, 2), (-self.size//2, 2)]:
                # Rotate point
                angle_rad = math.radians(self.rotation)
                rotated_x = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
                rotated_y = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
                points.append((render_x + rotated_x, render_y + rotated_y))
            
            pg.draw.polygon(screen, color[:3], points)
        except (ValueError, OverflowError):
            # Fallback to simple circle
            pg.draw.circle(screen, color[:3], (render_x, render_y), self.size//2)


class BaseWeaponEffectsManager:
    """Base class for managing weapon-specific visual effects."""
    
    def __init__(self, lighting_system=None):
        self.lighting_system = lighting_system
        self.muzzle_flashes = []
        self.shell_casings = []
        
        # Muzzle flash factory
        self.muzzle_flash_types = {
            "Assault Rifle": AssaultRifleMuzzleFlash,
            "Shotgun": ShotgunMuzzleFlash,
            "SMG": SMGMuzzleFlash,
            "Minigun": MinigunMuzzleFlash,
        }
    
    def create_muzzle_flash(self, x: float, y: float, angle: float, weapon_type: str):
        """Create a muzzle flash effect for the specified weapon type."""
        flash_class = self.muzzle_flash_types.get(weapon_type, AssaultRifleMuzzleFlash)
        muzzle_flash = flash_class(x, y, angle, weapon_type)
        self.muzzle_flashes.append(muzzle_flash)
        
        # Add lighting effect if system available
        if self.lighting_system and hasattr(self.lighting_system, 'add_muzzle_flash'):
            intensity = self._get_muzzle_flash_intensity(weapon_type)
            self.lighting_system.add_muzzle_flash(x, y, intensity=intensity, weapon_type=weapon_type)
    
    def create_shell_casing(self, x: float, y: float, angle: float, weapon_type: str):
        """Create a shell casing effect for the specified weapon type."""
        # Skip shell casings for certain weapon types
        if weapon_type in ["Minigun"]:  # Minigun disabled for clean look
            return
            
        shell_casing = BaseShellCasing(x, y, angle, weapon_type)
        self.shell_casings.append(shell_casing)
    
    def _get_muzzle_flash_intensity(self, weapon_type: str) -> float:
        """Get lighting intensity for muzzle flash based on weapon type."""
        intensity_map = {
            "Assault Rifle": 0.8,
            "Shotgun": 1.0,
            "SMG": 0.6,
            "Minigun": 0.4,
            "Rocket Launcher": 1.2,
        }
        return intensity_map.get(weapon_type, 0.7)
    
    def update(self, dt: float):
        """Update all weapon effects."""
        # Update muzzle flashes
        self.muzzle_flashes = [flash for flash in self.muzzle_flashes 
                              if not flash.update(dt)]
        
        # Update shell casings
        self.shell_casings = [casing for casing in self.shell_casings 
                             if not casing.update(dt)]
    
    def render_muzzle_flashes(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render all muzzle flash effects."""
        for flash in self.muzzle_flashes:
            flash.render(screen, offset)
    
    def render_shell_casings(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render all shell casing effects."""
        for casing in self.shell_casings:
            casing.render(screen, offset)
    
    def clear_effects(self):
        """Clear all active effects."""
        self.muzzle_flashes.clear()
        self.shell_casings.clear()


class BaseImpactEffect:
    """Base class for weapon impact effects."""
    
    def __init__(self, x: float, y: float, weapon_type: str, target_type: str = "enemy"):
        self.x = x
        self.y = y
        self.weapon_type = weapon_type
        self.target_type = target_type
        self.age = 0.0
        self.particles = []
        
        # Get impact properties based on weapon and target type
        props = self._get_impact_properties()
        self.max_lifetime = props['lifetime']
        self.color = props['color']
        
        # Generate impact particles
        self._generate_impact_particles(props)
    
    def _get_impact_properties(self) -> Dict[str, Any]:
        """Get impact properties based on weapon and target type."""
        # Base properties
        base_props = {
            'lifetime': 0.5,
            'particle_count': 8,
            'color': (255, 255, 255),
            'speed': 100,
            'size_range': (2, 4)
        }
        
        # Weapon-specific modifications
        weapon_mods = {
            "Assault Rifle": {'color': (255, 255, 220), 'particle_count': 6},
            "Shotgun": {'color': (255, 200, 100), 'particle_count': 12, 'speed': 80},
            "SMG": {'color': (0, 255, 255), 'particle_count': 4, 'speed': 120},
            "Minigun": {'color': (100, 220, 255), 'particle_count': 3, 'speed': 150},
            "Sniper Rifle": {'color': (255, 255, 255), 'particle_count': 10, 'speed': 200},
        }
        
        # Apply weapon modifications
        if self.weapon_type in weapon_mods:
            base_props.update(weapon_mods[self.weapon_type])
        
        # Target-specific modifications
        if self.target_type == "armor":
            base_props['color'] = (255, 150, 50)  # Sparks for armor
            base_props['particle_count'] *= 2
        elif self.target_type == "flesh":
            base_props['color'] = (200, 50, 50)   # Blood-like for flesh
        
        return base_props
    
    def _generate_impact_particles(self, props: Dict[str, Any]):
        """Generate impact particles."""
        for _ in range(props['particle_count']):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(props['speed'] * 0.5, props['speed'] * 1.5)
            
            particle = {
                'pos': pg.Vector2(self.x, self.y),
                'velocity': pg.Vector2(
                    math.cos(angle) * speed,
                    math.sin(angle) * speed
                ),
                'size': random.uniform(*props['size_range']),
                'life': random.uniform(0.2, 0.6),
                'initial_life': random.uniform(0.2, 0.6)
            }
            self.particles.append(particle)
    
    def update(self, dt: float) -> bool:
        """Update impact effect. Returns True if should be removed."""
        self.age += dt
        
        particles_to_remove = []
        for particle in self.particles:
            particle['pos'] += particle['velocity'] * dt
            particle['life'] -= dt
            particle['velocity'] *= 0.9  # Friction
            
            if particle['life'] <= 0:
                particles_to_remove.append(particle)
        
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        return self.age >= self.max_lifetime or len(self.particles) == 0
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render impact effect."""
        for particle in self.particles:
            if particle['life'] > 0:
                life_ratio = particle['life'] / particle['initial_life']
                alpha = max(0, min(255, int(255 * life_ratio)))
                
                render_x = int(particle['pos'].x + offset[0])
                render_y = int(particle['pos'].y + offset[1])
                
                color = (*self.color, alpha)
                size = max(1, int(particle['size'] * life_ratio))
                
                try:
                    pg.draw.circle(screen, color[:3], (render_x, render_y), size)
                except (ValueError, OverflowError):
                    pass


class WeaponImpactEffectsManager:
    """Manager for weapon impact effects."""
    
    def __init__(self):
        self.impact_effects = []
    
    def create_impact_effect(self, x: float, y: float, weapon_type: str, target_type: str = "enemy"):
        """Create an impact effect."""
        effect = BaseImpactEffect(x, y, weapon_type, target_type)
        self.impact_effects.append(effect)
    
    def update(self, dt: float):
        """Update all impact effects."""
        self.impact_effects = [effect for effect in self.impact_effects 
                              if not effect.update(dt)]
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render all impact effects."""
        for effect in self.impact_effects:
            effect.render(screen, offset)
    
    def clear_effects(self):
        """Clear all active impact effects."""
        self.impact_effects.clear()
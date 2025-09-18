"""
Base explosion system for consolidating all explosion effects.
Handles simple particle explosions, complex multi-phase explosions, and weapon-specific blast effects.
"""

import pygame as pg
import math
import random
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any, Optional
from enum import Enum


class ExplosionPhase(Enum):
    """Phases of a complex explosion."""
    FLASH = "flash"
    EXPANSION = "expansion" 
    PEAK = "peak"
    FADE = "fade"
    COMPLETE = "complete"


class BaseExplosion(ABC):
    """Abstract base class for all explosion effects."""
    
    def __init__(self, x: float, y: float, explosion_type: str):
        self.x = x
        self.y = y
        self.explosion_type = explosion_type
        self.age = 0.0
        self.max_lifetime = self._get_lifetime()
        self.particles = []
        self.is_alive = True
        
        # Generate initial particles
        self._generate_particles()
    
    @abstractmethod
    def _get_lifetime(self) -> float:
        """Get the total lifetime for this explosion type."""
        pass
    
    @abstractmethod
    def _generate_particles(self):
        """Generate explosion particles based on type."""
        pass
    
    @abstractmethod
    def update(self, dt: float) -> bool:
        """Update explosion. Returns True if should be removed."""
        pass
    
    @abstractmethod
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render explosion effect."""
        pass


class SimpleExplosion(BaseExplosion):
    """Simple particle-based explosion for basic effects."""
    
    def __init__(self, x: float, y: float, explosion_type: str = "basic",
                 color: Tuple[int, int, int] = (255, 200, 100),
                 particle_count: int = 15, speed: float = 200):
        self.color = color
        self.particle_count = particle_count
        self.speed = speed
        super().__init__(x, y, explosion_type)
    
    def _get_lifetime(self) -> float:
        type_lifetimes = {
            "basic": 1.0,
            "muzzle_flash": 0.15,
            "bullet_impact": 0.3,
            "small": 0.5,
            "sparks": 0.4,
        }
        return type_lifetimes.get(self.explosion_type, 0.8)
    
    def _generate_particles(self):
        """Generate simple explosion particles."""
        for _ in range(self.particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed_variation = random.uniform(0.5, 1.5)
            velocity = pg.Vector2(
                math.cos(angle) * self.speed * speed_variation,
                math.sin(angle) * self.speed * speed_variation
            )
            
            particle = {
                'pos': pg.Vector2(self.x, self.y),
                'velocity': velocity,
                'size': random.uniform(2, 6),
                'initial_size': random.uniform(2, 6),
                'life': random.uniform(0.3, 0.8),
                'initial_life': random.uniform(0.3, 0.8),
                'color': self.color
            }
            self.particles.append(particle)
    
    def update(self, dt: float) -> bool:
        """Update simple explosion particles."""
        self.age += dt
        
        particles_to_remove = []
        for particle in self.particles:
            particle['pos'] += particle['velocity'] * dt
            particle['life'] -= dt
            particle['velocity'] *= 0.95  # Friction
            
            if particle['life'] <= 0:
                particles_to_remove.append(particle)
        
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        # Remove explosion when all particles are gone or max lifetime reached
        self.is_alive = len(self.particles) > 0 and self.age < self.max_lifetime
        return not self.is_alive
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render simple explosion particles."""
        for particle in self.particles:
            if particle['life'] > 0:
                life_ratio = particle['life'] / particle['initial_life']
                alpha = max(0, min(255, int(255 * life_ratio)))
                size = max(1, int(particle['size'] * life_ratio))
                
                render_x = int(particle['pos'].x + offset[0])
                render_y = int(particle['pos'].y + offset[1])
                
                # Vary color based on life
                if life_ratio > 0.7:
                    color = (255, 255, 255)  # White hot
                elif life_ratio > 0.3:
                    color = particle['color']  # Base color
                else:
                    # Fade to darker
                    color = tuple(int(c * 0.5) for c in particle['color'])
                
                try:
                    pg.draw.circle(screen, color, (render_x, render_y), size)
                except (ValueError, OverflowError):
                    pass


class ComplexExplosion(BaseExplosion):
    """Multi-phase explosion with flash, expansion, peak, and fade phases."""
    
    def __init__(self, x: float, y: float, explosion_type: str = "normal",
                 radius: float = 100, damage: int = 50):
        self.radius = radius
        self.damage = damage
        self.current_phase = ExplosionPhase.FLASH
        self.phase_progress = 0.0
        
        # Phase timings (as ratios of total lifetime)
        self.phase_timings = {
            ExplosionPhase.FLASH: 0.1,      # 10% of lifetime
            ExplosionPhase.EXPANSION: 0.3,   # 30% of lifetime
            ExplosionPhase.PEAK: 0.3,        # 30% of lifetime
            ExplosionPhase.FADE: 0.3         # 30% of lifetime
        }
        
        super().__init__(x, y, explosion_type)
    
    def _get_lifetime(self) -> float:
        type_lifetimes = {
            "normal": 0.8,
            "large": 1.2,
            "rocket": 1.0,
            "grenade": 0.9,
            "tactical": 1.1,
        }
        return type_lifetimes.get(self.explosion_type, 1.0)
    
    def _generate_particles(self):
        """Generate particles for complex explosion (debris, sparks, etc.)."""
        particle_count = int(self.radius / 3)  # Scale with explosion size
        
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.radius * 1.5)
            speed = random.uniform(50, 200)
            
            particle = {
                'pos': pg.Vector2(self.x, self.y),
                'velocity': pg.Vector2(
                    math.cos(angle) * speed,
                    math.sin(angle) * speed
                ),
                'size': random.uniform(1, 4),
                'life': random.uniform(0.5, 1.0),
                'initial_life': random.uniform(0.5, 1.0),
                'color': random.choice([
                    (255, 255, 150), (255, 200, 100), (255, 150, 50), (255, 100, 0)
                ])
            }
            self.particles.append(particle)
    
    def update(self, dt: float) -> bool:
        """Update complex explosion phases."""
        self.age += dt
        
        # Update current phase
        progress = self.age / self.max_lifetime
        
        if progress < self.phase_timings[ExplosionPhase.FLASH]:
            self.current_phase = ExplosionPhase.FLASH
            self.phase_progress = progress / self.phase_timings[ExplosionPhase.FLASH]
        elif progress < (self.phase_timings[ExplosionPhase.FLASH] + self.phase_timings[ExplosionPhase.EXPANSION]):
            self.current_phase = ExplosionPhase.EXPANSION
            start = self.phase_timings[ExplosionPhase.FLASH]
            self.phase_progress = (progress - start) / self.phase_timings[ExplosionPhase.EXPANSION]
        elif progress < (sum([self.phase_timings[ExplosionPhase.FLASH], 
                             self.phase_timings[ExplosionPhase.EXPANSION], 
                             self.phase_timings[ExplosionPhase.PEAK]])):
            self.current_phase = ExplosionPhase.PEAK
            start = self.phase_timings[ExplosionPhase.FLASH] + self.phase_timings[ExplosionPhase.EXPANSION]
            self.phase_progress = (progress - start) / self.phase_timings[ExplosionPhase.PEAK]
        elif progress < 1.0:
            self.current_phase = ExplosionPhase.FADE
            start = sum([self.phase_timings[ExplosionPhase.FLASH], 
                        self.phase_timings[ExplosionPhase.EXPANSION], 
                        self.phase_timings[ExplosionPhase.PEAK]])
            self.phase_progress = (progress - start) / self.phase_timings[ExplosionPhase.FADE]
        else:
            self.current_phase = ExplosionPhase.COMPLETE
        
        # Update particles
        particles_to_remove = []
        for particle in self.particles:
            particle['pos'] += particle['velocity'] * dt
            particle['life'] -= dt
            particle['velocity'] *= 0.98  # Light friction
            
            if particle['life'] <= 0:
                particles_to_remove.append(particle)
        
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        self.is_alive = self.current_phase != ExplosionPhase.COMPLETE
        return not self.is_alive
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render complex explosion based on current phase."""
        render_x = int(self.x + offset[0])
        render_y = int(self.y + offset[1])
        
        if self.current_phase == ExplosionPhase.FLASH:
            self._render_flash_phase(screen, render_x, render_y)
        elif self.current_phase == ExplosionPhase.EXPANSION:
            self._render_expansion_phase(screen, render_x, render_y)
        elif self.current_phase == ExplosionPhase.PEAK:
            self._render_peak_phase(screen, render_x, render_y)
        elif self.current_phase == ExplosionPhase.FADE:
            self._render_fade_phase(screen, render_x, render_y)
        
        # Render particles
        for particle in self.particles:
            if particle['life'] > 0:
                life_ratio = particle['life'] / particle['initial_life']
                size = max(1, int(particle['size'] * life_ratio))
                
                particle_x = int(particle['pos'].x + offset[0])
                particle_y = int(particle['pos'].y + offset[1])
                
                try:
                    pg.draw.circle(screen, particle['color'], (particle_x, particle_y), size)
                except (ValueError, OverflowError):
                    pass
    
    def _render_flash_phase(self, screen: pg.Surface, x: int, y: int):
        """Render initial bright flash."""
        flash_radius = int(self.radius * 0.5 * (1.0 + self.phase_progress))
        alpha_factor = 1.0 - self.phase_progress
        
        # Multiple glow layers
        colors = [
            (255, 255, 255, int(255 * alpha_factor)),  # Bright white core
            (255, 255, 150, int(200 * alpha_factor)),  # Yellow glow
            (255, 200, 100, int(150 * alpha_factor)),  # Orange outer
        ]
        
        for i, color in enumerate(colors):
            radius = flash_radius + i * 5
            if radius > 0:
                pg.draw.circle(screen, color[:3], (x, y), radius)
    
    def _render_expansion_phase(self, screen: pg.Surface, x: int, y: int):
        """Render rapid expansion with shockwave."""
        explosion_radius = int(self.radius * self.phase_progress)
        alpha_factor = 1.0 - self.phase_progress * 0.3
        
        # Main explosion layers
        layers = [
            {'radius_mult': 1.2, 'color': (255, 80, 0), 'alpha': alpha_factor * 0.7},
            {'radius_mult': 1.0, 'color': (255, 120, 20), 'alpha': alpha_factor * 0.8},
            {'radius_mult': 0.8, 'color': (255, 150, 50), 'alpha': alpha_factor * 0.9},
            {'radius_mult': 0.6, 'color': (255, 200, 100), 'alpha': alpha_factor * 1.0},
            {'radius_mult': 0.4, 'color': (255, 255, 150), 'alpha': alpha_factor * 1.0},
        ]
        
        for layer in layers:
            layer_radius = int(explosion_radius * layer['radius_mult'])
            if layer_radius > 0:
                pg.draw.circle(screen, layer['color'], (x, y), layer_radius)
        
        # Shockwave ring
        if self.phase_progress > 0.3:
            shockwave_radius = int(explosion_radius * 1.3)
            shockwave_thickness = max(2, int(5 * (1 - self.phase_progress)))
            pg.draw.circle(screen, (255, 200, 100), (x, y), shockwave_radius, shockwave_thickness)
    
    def _render_peak_phase(self, screen: pg.Surface, x: int, y: int):
        """Render peak explosion with maximum intensity."""
        explosion_radius = int(self.radius)
        alpha_factor = 1.0 - self.phase_progress * 0.2
        
        # Peak explosion layers
        layers = [
            {'radius_mult': 1.0, 'color': (255, 80, 0), 'alpha': alpha_factor * 0.8},
            {'radius_mult': 0.8, 'color': (255, 120, 40), 'alpha': alpha_factor * 0.9},
            {'radius_mult': 0.6, 'color': (255, 160, 80), 'alpha': alpha_factor * 1.0},
            {'radius_mult': 0.4, 'color': (255, 200, 120), 'alpha': alpha_factor * 1.0},
            {'radius_mult': 0.2, 'color': (255, 240, 160), 'alpha': alpha_factor * 1.0}
        ]
        
        for layer in layers:
            layer_radius = int(explosion_radius * layer['radius_mult'])
            if layer_radius > 0:
                pg.draw.circle(screen, layer['color'], (x, y), layer_radius)
    
    def _render_fade_phase(self, screen: pg.Surface, x: int, y: int):
        """Render fading explosion with smoke."""
        explosion_radius = int(self.radius * (1.0 - self.phase_progress * 0.3))
        alpha_factor = 1.0 - self.phase_progress
        
        # Fading colors (more smoke-like)
        layers = [
            {'radius_mult': 1.0, 'color': (120, 80, 60), 'alpha': alpha_factor * 0.6},
            {'radius_mult': 0.7, 'color': (150, 100, 80), 'alpha': alpha_factor * 0.7},
            {'radius_mult': 0.4, 'color': (180, 120, 100), 'alpha': alpha_factor * 0.8},
        ]
        
        for layer in layers:
            layer_radius = int(explosion_radius * layer['radius_mult'])
            if layer_radius > 0:
                pg.draw.circle(screen, layer['color'], (x, y), layer_radius)


class WeaponSpecificExplosion(SimpleExplosion):
    """Explosion effects tailored for specific weapon types."""
    
    def __init__(self, x: float, y: float, weapon_type: str):
        self.weapon_type = weapon_type
        
        # Get weapon-specific properties
        props = self._get_weapon_explosion_properties()
        
        super().__init__(x, y, weapon_type, 
                        color=props['color'],
                        particle_count=props['particle_count'],
                        speed=props['speed'])
    
    def _get_weapon_explosion_properties(self) -> Dict[str, Any]:
        """Get explosion properties based on weapon type."""
        weapon_properties = {
            "Assault Rifle": {
                'color': (255, 255, 220),
                'particle_count': 8,
                'speed': 150
            },
            "Shotgun": {
                'color': (255, 200, 100),
                'particle_count': 15,
                'speed': 120
            },
            "SMG": {
                'color': (0, 255, 255),
                'particle_count': 6,
                'speed': 180
            },
            "Minigun": {
                'color': (100, 220, 255),
                'particle_count': 4,
                'speed': 200
            },
            "Sniper Rifle": {
                'color': (255, 255, 255),
                'particle_count': 12,
                'speed': 250
            },
            "Rocket Launcher": {
                'color': (255, 150, 0),
                'particle_count': 25,
                'speed': 300
            }
        }
        
        return weapon_properties.get(self.weapon_type, {
            'color': (255, 200, 100),
            'particle_count': 10,
            'speed': 150
        })


class ExplosionManager:
    """Manager for all explosion effects in the game."""
    
    def __init__(self):
        self.explosions = []
    
    def create_simple_explosion(self, x: float, y: float, explosion_type: str = "basic",
                               color: Tuple[int, int, int] = (255, 200, 100),
                               particle_count: int = 15, speed: float = 200):
        """Create a simple particle explosion."""
        explosion = SimpleExplosion(x, y, explosion_type, color, particle_count, speed)
        self.explosions.append(explosion)
        return explosion
    
    def create_complex_explosion(self, x: float, y: float, explosion_type: str = "normal",
                                radius: float = 100, damage: int = 50):
        """Create a complex multi-phase explosion."""
        explosion = ComplexExplosion(x, y, explosion_type, radius, damage)
        self.explosions.append(explosion)
        return explosion
    
    def create_weapon_explosion(self, x: float, y: float, weapon_type: str):
        """Create a weapon-specific explosion effect."""
        explosion = WeaponSpecificExplosion(x, y, weapon_type)
        self.explosions.append(explosion)
        return explosion
    
    def update(self, dt: float):
        """Update all explosions."""
        self.explosions = [explosion for explosion in self.explosions 
                          if not explosion.update(dt)]
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render all explosions."""
        for explosion in self.explosions:
            explosion.render(screen, offset)
    
    def clear_explosions(self):
        """Clear all active explosions."""
        self.explosions.clear()
    
    def get_explosion_count(self) -> int:
        """Get the number of active explosions."""
        return len(self.explosions)
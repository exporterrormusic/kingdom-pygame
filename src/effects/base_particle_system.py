"""
Base particle system for consolidating spark and particle effects.
Provides a unified interface for different types of particles (sparks, debris, etc.)
"""

import pygame as pg
import math
import random
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any


class Particle:
    """Individual particle with physics and rendering."""
    
    def __init__(self, x: float, y: float, velocity_x: float = 0, velocity_y: float = 0, 
                 color: Tuple[int, int, int] = (255, 255, 255), size: float = 3.0, 
                 lifetime: float = 1.0, particle_type: str = "spark"):
        """Initialize a particle."""
        self.pos = pg.Vector2(x, y)
        self.velocity = pg.Vector2(velocity_x, velocity_y)
        self.color = color
        self.initial_color = color
        self.size = size
        self.initial_size = size
        self.age = 0.0
        self.lifetime = lifetime
        self.particle_type = particle_type
        self.alpha = 255
        self.expired = False
        
        # Physics properties
        self.gravity = 0.0
        self.air_resistance = 1.0
        self.bounce = 0.0
        
    def update(self, dt: float) -> bool:
        """Update particle. Returns True if should be removed."""
        if self.expired:
            return True
            
        self.age += dt
        
        # Update position
        self.pos += self.velocity * dt
        
        # Apply gravity
        if self.gravity > 0:
            self.velocity.y += self.gravity * dt
            
        # Apply air resistance
        if self.air_resistance < 1.0:
            self.velocity *= self.air_resistance
            
        # Fade over time
        progress = self.age / self.lifetime
        if progress >= 1.0:
            self.expired = True
            return True
            
        # Update visual properties
        fade_factor = 1.0 - progress
        self.alpha = int(255 * fade_factor)
        self.size = max(0.5, self.initial_size * fade_factor)
        
        # Fade color
        self.color = (
            int(self.initial_color[0] * fade_factor),
            int(self.initial_color[1] * fade_factor),
            int(self.initial_color[2] * fade_factor)
        )
        
        return False
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render the particle."""
        if self.expired or self.alpha <= 0:
            return
            
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        # Only render if on screen (with small buffer)
        if (-20 <= render_x <= screen.get_width() + 20 and 
            -20 <= render_y <= screen.get_height() + 20):
            
            particle_size = max(1, int(self.size))
            
            if self.particle_type == "spark":
                # Draw spark as bright circle
                pg.draw.circle(screen, (*self.color, min(self.alpha, 255)), 
                             (render_x, render_y), particle_size)
            elif self.particle_type == "fire":
                # Draw fire particle with glow
                self._draw_fire_particle(screen, render_x, render_y, particle_size)
            elif self.particle_type == "impact":
                # Draw impact spark with additive blending
                self._draw_impact_spark(screen, render_x, render_y, particle_size)
            else:
                # Default circular particle
                pg.draw.circle(screen, self.color, (render_x, render_y), particle_size)
    
    def _draw_fire_particle(self, screen: pg.Surface, x: int, y: int, size: int):
        """Draw a fire-themed particle with glow."""
        if size <= 0:
            return
            
        # Create surface for glow effect
        glow_size = size * 3
        fire_surface = pg.Surface((glow_size, glow_size), pg.SRCALPHA)
        center = glow_size // 2
        
        # Outer glow
        outer_alpha = min(self.alpha // 3, 80)
        if outer_alpha > 0:
            pg.draw.circle(fire_surface, (*self.color, outer_alpha), (center, center), size + 2)
        
        # Inner core
        core_alpha = min(self.alpha, 255)
        if core_alpha > 0:
            pg.draw.circle(fire_surface, (*self.color, core_alpha), (center, center), size)
        
        # Blit with alpha blending
        screen.blit(fire_surface, (x - center, y - center), special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _draw_impact_spark(self, screen: pg.Surface, x: int, y: int, size: int):
        """Draw an impact spark with bright center."""
        if size <= 0:
            return
            
        # Outer glow
        if self.alpha > 50:
            pg.draw.circle(screen, (*self.color, min(self.alpha // 2, 100)), 
                         (x, y), size + 1)
        
        # Bright center
        pg.draw.circle(screen, (*self.color, min(self.alpha, 255)), (x, y), size)
        
        # Bright white center point
        if size > 1:
            pg.draw.circle(screen, (255, 255, 255), (x, y), max(1, size // 2))


class BaseParticleSystem:
    """Base particle system for managing collections of particles."""
    
    def __init__(self, lighting_system=None):
        """Initialize particle system."""
        self.particles: List[Particle] = []
        self.lighting_system = lighting_system
    
    def add_particles(self, x: float, y: float, particle_type: str = "spark", 
                     count: int = 5, **kwargs):
        """Add particles at the specified location."""
        for _ in range(count):
            particle = self._create_particle(x, y, particle_type, **kwargs)
            if particle:
                self.particles.append(particle)
    
    def _create_particle(self, x: float, y: float, particle_type: str, **kwargs) -> Particle:
        """Create a single particle. Override in subclasses for custom behavior."""
        # Default particle properties
        velocity_x = kwargs.get('velocity_x', random.uniform(-100, 100))
        velocity_y = kwargs.get('velocity_y', random.uniform(-100, 100))
        color = kwargs.get('color', (255, 255, 255))
        size = kwargs.get('size', random.uniform(2, 4))
        lifetime = kwargs.get('lifetime', random.uniform(0.3, 0.8))
        
        # Add position variation
        pos_x = x + random.uniform(-2, 2)
        pos_y = y + random.uniform(-2, 2)
        
        particle = Particle(pos_x, pos_y, velocity_x, velocity_y, color, size, lifetime, particle_type)
        
        # Set physics properties based on type
        if particle_type == "spark":
            particle.gravity = 200.0
            particle.air_resistance = 0.95
        elif particle_type == "fire":
            particle.gravity = -50.0  # Fire rises
            particle.air_resistance = 0.98
        elif particle_type == "impact":
            particle.gravity = 150.0
            particle.air_resistance = 0.97
            
        return particle
    
    def update(self, dt: float):
        """Update all particles and remove expired ones."""
        # Update particles and collect expired ones
        particles_to_remove = []
        for particle in self.particles:
            if particle.update(dt):
                particles_to_remove.append(particle)
        
        # Remove expired particles
        for particle in particles_to_remove:
            self.particles.remove(particle)
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render all particles."""
        for particle in self.particles:
            particle.render(screen, offset)
    
    def clear(self):
        """Clear all particles."""
        self.particles.clear()
    
    def get_particle_count(self) -> int:
        """Get current particle count."""
        return len(self.particles)


class ImpactSparksSystem(BaseParticleSystem):
    """Specialized system for impact sparks (bullet-wall collisions)."""
    
    def add_impact_sparks(self, x: float, y: float, impact_angle: float = None, 
                         surface_type: str = "wall"):
        """Create impact sparks at the specified position."""
        # Determine colors based on surface type
        if surface_type == "wall":
            colors = [(255, 255, 255), (255, 255, 200), (255, 200, 100)]
        elif surface_type == "metal":
            colors = [(255, 255, 255), (200, 200, 255), (150, 150, 255)]
        elif surface_type == "dirt":
            colors = [(139, 69, 19), (160, 82, 45), (210, 180, 140)]
        else:
            colors = [(255, 255, 255), (255, 255, 200), (255, 200, 100)]
        
        # Create 3-5 sparks per impact
        count = random.randint(3, 5)
        
        for _ in range(count):
            # Calculate direction based on impact angle
            if impact_angle is not None:
                base_angle = impact_angle + math.pi  # Opposite to impact direction
                angle_variation = random.uniform(-math.pi/3, math.pi/3)
                spark_angle = base_angle + angle_variation
            else:
                spark_angle = random.uniform(0, 2 * math.pi)
            
            # Convert to velocity
            speed = random.uniform(50, 150)
            velocity_x = math.cos(spark_angle) * speed
            velocity_y = math.sin(spark_angle) * speed
            
            # Create particle
            particle = self._create_particle(
                x, y, "impact",
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                color=random.choice(colors),
                size=random.uniform(2, 4),
                lifetime=random.uniform(0.2, 0.5)
            )
            
            if particle:
                self.particles.append(particle)


class TrailSparksSystem(BaseParticleSystem):
    """Specialized system for trail sparks (along bullet trails)."""
    
    def add_trail_sparks(self, bullets, offset: Tuple[float, float] = (0, 0), 
                        spark_type: str = "fire"):
        """Add sparks along bullet trails."""
        if len(bullets) < 2:
            return
            
        # Add sparks between bullets occasionally
        for i in range(len(bullets) - 1):
            if random.random() < 0.3:  # 30% chance per frame
                bullet1 = bullets[i]
                bullet2 = bullets[i + 1]
                
                # Position spark between bullets
                t = random.uniform(0.2, 0.8)
                spark_x = bullet1.pos.x + t * (bullet2.pos.x - bullet1.pos.x) + offset[0]
                spark_y = bullet1.pos.y + t * (bullet2.pos.y - bullet1.pos.y) + offset[1]
                
                # Different colors based on spark type
                if spark_type == "fire":
                    colors = [(255, 200, 0), (255, 150, 0), (255, 100, 0), (255, 255, 100)]
                elif spark_type == "electric":
                    colors = [(100, 220, 255), (150, 240, 255), (200, 250, 255), (255, 255, 255)]
                else:
                    colors = [(255, 255, 255), (255, 255, 200), (255, 200, 100)]
                
                particle = self._create_particle(
                    spark_x, spark_y, spark_type,
                    velocity_x=random.uniform(-30, 30),
                    velocity_y=random.uniform(-30, 30),
                    color=random.choice(colors),
                    size=random.uniform(2, 5),
                    lifetime=random.uniform(0.5, 1.2)
                )
                
                if particle:
                    self.particles.append(particle)
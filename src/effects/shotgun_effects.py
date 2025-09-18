"""
Shotgun fire trail enhancement system.
Handles fire-themed connecting lines between shotgun pellets.
"""

import pygame as pg
import math
import random
from typing import Tuple, List
from .base_trail_renderer import ShotgunTrailRenderer
from .base_particle_system import TrailSparksSystem
from .base_weapon_effects import BaseWeaponEffectsManager

class ShotgunEffectsManager(BaseWeaponEffectsManager):
    """Manages fire trail effects for shotgun pellets."""
    
    def __init__(self, lighting_system=None):
        """Initialize the shotgun effects manager."""
        super().__init__(lighting_system)
        
        # Shotgun-specific trail effects
        self.fire_trails = []  # Active fire trail segments
        self.trail_active = True  # Always active for shotgun
        
        # Initialize trail renderer
        self.trail_renderer = ShotgunTrailRenderer(lighting_system)
        
        # Initialize particle system
        self.spark_system = TrailSparksSystem(lighting_system)
        
    def update(self, dt: float):
        """Update fire trail effects."""
        # Update base weapon effects (muzzle flashes, shell casings)
        super().update(dt)
        
        # Update particle system
        self.spark_system.update(dt)
            
    def render_fire_trail_lines(self, screen: pg.Surface, bullets, offset: Tuple[float, float] = (0, 0)):
        """Render fire-themed glowing lines connecting shotgun pellets."""
        if len(bullets) < 2:
            return
            
        # Use the shared trail renderer
        self.trail_renderer.render_bullet_trail_lines(screen, bullets, offset)
                
        # Add and render fire sparks along the trails using particle system
        self.spark_system.add_trail_sparks(bullets, offset, spark_type="fire")
        self.spark_system.render(screen, offset)
                

"""
This module defines the AtmosphericEffects class, which manages 
environmental effects like rain, snow, and cherry blossoms.
"""

import pygame as pg
import random
import time
from typing import List, Tuple

class AtmosphericEffects:
    """Manages atmospheric effects like rain, snow, and cherry blossoms."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize atmospheric effects manager."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles: List[pg.Rect] = []
        self.particle_colors: List[Tuple[int, int, int]] = []
        self.particle_speeds: List[int] = []
        self.current_atmosphere: str = "none"
        
        # Footprint tracking
        self.footprints: List[dict] = []
        self.last_footprint_time = 0
    
    def set_atmosphere(self, atmosphere_type: str):
        """Set the current atmospheric effect (rain, snow, cherry_blossom)."""
        if self.current_atmosphere == atmosphere_type:
            return
            
        self.current_atmosphere = atmosphere_type
        self.particles.clear()
        self.particle_colors.clear()
        self.particle_speeds.clear()
        
        if atmosphere_type == "rain":
            self._create_rain_particles(200)
        elif atmosphere_type == "snow":
            self._create_snow_particles(150)
        elif atmosphere_type == "cherry_blossom":
            self._create_cherry_blossom_particles(100)
    
    def set_random_atmosphere(self):
        """Set a random atmospheric effect."""
        atmosphere_options = ["none", "rain", "snow", "cherry_blossom"]
        random_atmosphere = random.choice(atmosphere_options)
        self.set_atmosphere(random_atmosphere)
    
    def _create_rain_particles(self, num_particles: int):
        """Create particles for rain effect."""
        for _ in range(num_particles):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)
            self.particles.append(pg.Rect(x, y, 1, 15))
            self.particle_colors.append((173, 216, 230))
            self.particle_speeds.append(random.randint(10, 20))
    
    def _create_snow_particles(self, num_particles: int):
        """Create particles for snow effect."""
        for _ in range(num_particles):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)
            size = random.randint(2, 5)
            self.particles.append(pg.Rect(x, y, size, size))
            self.particle_colors.append((255, 255, 255))
            self.particle_speeds.append(random.randint(1, 3))
    
    def _create_cherry_blossom_particles(self, num_particles: int):
        """Create particles for cherry blossom effect."""
        for _ in range(num_particles):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)
            size = random.randint(4, 8)
            self.particles.append(pg.Rect(x, y, size, size))
            self.particle_colors.append(random.choice([(255, 182, 193), (255, 192, 203), (221, 160, 221)]))
            self.particle_speeds.append(random.randint(1, 2))
    
    def update(self, dt: float):
        """Update atmospheric particles."""
        if self.current_atmosphere == "rain":
            self._update_rain(dt)
        elif self.current_atmosphere == "snow":
            self._update_snow(dt)
        elif self.current_atmosphere == "cherry_blossom":
            self._update_cherry_blossom(dt)
    
    def _update_rain(self, dt: float):
        """Update rain particles."""
        for i, particle in enumerate(self.particles):
            particle.y += self.particle_speeds[i]
            if particle.y > self.screen_height:
                particle.y = random.randint(-20, 0)
                particle.x = random.randint(0, self.screen_width)
    
    def _update_snow(self, dt: float):
        """Update snow particles."""
        for i, particle in enumerate(self.particles):
            particle.y += self.particle_speeds[i]
            particle.x += random.randint(-1, 1)
            if particle.y > self.screen_height:
                particle.y = random.randint(-20, 0)
                particle.x = random.randint(0, self.screen_width)
    
    def _update_cherry_blossom(self, dt: float):
        """Update cherry blossom particles."""
        for i, particle in enumerate(self.particles):
            particle.y += self.particle_speeds[i]
            particle.x += random.randint(-2, 2)
            if particle.y > self.screen_height:
                particle.y = random.randint(-20, 0)
                particle.x = random.randint(0, self.screen_width)
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render atmospheric particles."""
        if self.current_atmosphere != "none":
            for i, particle in enumerate(self.particles):
                # Apply offset to particle position if needed
                render_pos = (particle.x + offset[0], particle.y + offset[1], particle.width, particle.height)
                render_rect = pg.Rect(render_pos)
                pg.draw.rect(screen, self.particle_colors[i], render_rect)
    
    def add_footprint(self, x: float, y: float):
        """Add a footprint at the given position."""
        current_time = time.time()
        
        # Only add footprints at a reasonable interval
        if current_time - self.last_footprint_time > 0.2:  # Every 200ms
            footprint = {
                'x': x,
                'y': y,
                'timestamp': current_time,
                'fade_time': 3.0  # Fade over 3 seconds
            }
            self.footprints.append(footprint)
            self.last_footprint_time = current_time
            
            # Limit the number of footprints to prevent memory issues
            if len(self.footprints) > 50:
                self.footprints.pop(0)
    
    def render_footprints(self, screen: pg.Surface, camera_offset=(0, 0)):
        """Render player footprints."""
        current_time = time.time()
        
        # Remove old footprints and render the rest
        self.footprints = [fp for fp in self.footprints 
                          if current_time - fp['timestamp'] < fp['fade_time']]
        
        for fp in self.footprints:
            # Calculate alpha based on age (fade out over time)
            age = current_time - fp['timestamp']
            alpha = max(0, int(255 * (1 - age / fp['fade_time'])))
            
            if alpha > 0:
                world_pos = (fp['x'], fp['y'])
                screen_pos = (int(world_pos[0] - camera_offset[0]), 
                            int(world_pos[1] - camera_offset[1]))
                
                # Simple footprint as a small semi-transparent circle
                footprint_color = (100, 100, 100, alpha)
                pg.draw.circle(screen, footprint_color[:3], screen_pos, 3)
    
    def render_screen_overlays(self, screen: pg.Surface):
        """Render screen-wide atmospheric overlays."""
        if self.current_atmosphere == "rain":
            # Add a slight blue overlay for rain
            overlay = pg.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(20)
            overlay.fill((100, 150, 200))  # Light blue
            screen.blit(overlay, (0, 0))
        elif self.current_atmosphere == "snow":
            # Add a slight white/blue overlay for snow
            overlay = pg.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(15)
            overlay.fill((200, 220, 255))  # Light blue-white
            screen.blit(overlay, (0, 0))
        elif self.current_atmosphere == "cherry_blossom":
            # Add a slight pink overlay for cherry blossoms
            overlay = pg.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(10)
            overlay.fill((255, 200, 220))  # Light pink
            screen.blit(overlay, (0, 0))

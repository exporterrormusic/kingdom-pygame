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
        # Use separate coordinate system for true screen-space particles
        self.atmospheric_particles: List[dict] = []  # [{'x': float, 'y': float, 'size': int, 'color': tuple, 'speed': float}]
        self.current_atmosphere: str = "none"
        
        # Footprint tracking (these DO use world coordinates)
        self.footprints: List[dict] = []
        self.last_footprint_time = 0
    
    def set_atmosphere(self, atmosphere_type: str):
        """Set the current atmospheric effect (rain, snow, cherry_blossom)."""
        if self.current_atmosphere == atmosphere_type:
            return
            
        self.current_atmosphere = atmosphere_type
        self.atmospheric_particles.clear()
        
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
            y = random.randint(-100, self.screen_height)  # Start some above screen
            self.particles.append(pg.Rect(x, y, 1, 15))
            self.particle_colors.append((173, 216, 230))
            self.particle_speeds.append(random.randint(10, 20))
    
    def _create_snow_particles(self, num_particles: int):
        """Create particles for snow effect."""
        for _ in range(num_particles):
            x = random.randint(0, self.screen_width)
            y = random.randint(-100, self.screen_height)  # Start some above screen
            size = random.randint(2, 5)
            self.particles.append(pg.Rect(x, y, size, size))
            self.particle_colors.append((255, 255, 255))
            self.particle_speeds.append(random.randint(1, 3))
    
    def _create_cherry_blossom_particles(self, num_particles: int):
        """Create particles for cherry blossom effect."""
        for _ in range(num_particles):
            x = random.randint(0, self.screen_width)
            y = random.randint(-100, self.screen_height)  # Start some above screen
            size = random.randint(4, 7)  # Smaller size range for reasonably sized flowers
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
            particle.y += self.particle_speeds[i] * dt * 60  # Frame-rate independent movement
            if particle.y > self.screen_height:
                particle.y = random.randint(-20, 0)
                particle.x = random.randint(0, self.screen_width)
    
    def _update_snow(self, dt: float):
        """Update snow particles."""
        for i, particle in enumerate(self.particles):
            particle.y += self.particle_speeds[i] * dt * 60  # Frame-rate independent movement
            particle.x += random.randint(-1, 1) * dt * 60  # Frame-rate independent horizontal drift
            if particle.y > self.screen_height:
                particle.y = random.randint(-20, 0)
                particle.x = random.randint(0, self.screen_width)
    
    def _update_cherry_blossom(self, dt: float):
        """Update cherry blossom particles."""
        for i, particle in enumerate(self.particles):
            particle.y += self.particle_speeds[i] * dt * 60  # Frame-rate independent movement
            particle.x += random.randint(-2, 2) * dt * 60  # Frame-rate independent horizontal drift
            if particle.y > self.screen_height:
                particle.y = random.randint(-20, 0)
                particle.x = random.randint(0, self.screen_width)
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render atmospheric particles in absolute screen coordinates."""
        if self.current_atmosphere != "none":
            for i, particle in enumerate(self.particles):
                # Render particles in absolute screen coordinates - completely ignore any offset
                render_x = int(particle.x)
                render_y = int(particle.y)
                
                # Only render if particle is visible on screen
                if (0 <= render_x <= self.screen_width and 
                    0 <= render_y <= self.screen_height):
                    
                    if self.current_atmosphere == "rain":
                        # Render rain as thin vertical lines
                        pg.draw.rect(screen, self.particle_colors[i], 
                                   (render_x, render_y, particle.width, particle.height))
                    elif self.current_atmosphere == "snow":
                        # Render snow as white circles
                        pg.draw.circle(screen, self.particle_colors[i], 
                                     (render_x + particle.width//2, render_y + particle.height//2), 
                                     particle.width//2)
                    elif self.current_atmosphere == "cherry_blossom":
                        # Render cherry blossoms as flower petals
                        self._render_cherry_blossom(screen, render_x, render_y, particle.width, self.particle_colors[i])
    
    def _render_cherry_blossom(self, screen: pg.Surface, x: int, y: int, size: int, color: tuple):
        """Render cherry blossom as a flower with petals."""
        import math
        
        center_x, center_y = x + size//2, y + size//2
        petal_size = max(3, size)  # Smaller petals - back to reasonable size
        
        # Draw 5 petals in a flower pattern
        for i in range(5):
            angle = (i / 5) * 2 * math.pi
            petal_x = center_x + int(math.cos(angle) * (petal_size // 2))
            petal_y = center_y + int(math.sin(angle) * (petal_size // 2))
            
            # Draw petal as smaller circle
            pg.draw.circle(screen, color, (petal_x, petal_y), max(2, petal_size//3))  # Smaller petals
        
        # Draw center
        pg.draw.circle(screen, (255, 255, 200), (center_x, center_y), max(1, size//3))  # Smaller center
    
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

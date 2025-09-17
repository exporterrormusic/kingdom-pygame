"""
This module defines the AtmosphericEffects class, which manages 
environmental effects like rain, snow, and cherry blossoms.
"""

import pygame as pg
import random
import time
import math
from typing import List, Tuple

class AtmosphericEffects:
    """Manages atmospheric effects like rain, snow, and cherry blossoms."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize atmospheric effects manager."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        # World-based atmospheric effects
        self.world_width = 3840
        self.world_height = 2160  
        self.particles: List[dict] = []
        self.current_atmosphere: str = "none"
        
        # Lightning system for rain effects
        self.lightning_timer = 0.0
        self.lightning_flash = False
        self.lightning_duration = 0.0
        self.next_lightning = random.uniform(3.0, 8.0)  # Random time until next lightning
        
        # Footprint tracking (these DO use world coordinates)
        self.footprints: List[dict] = []
        self.last_footprint_time = 0
    
    def set_atmosphere(self, atmosphere_type: str):
        """Set the current atmospheric effect (rain, snow, cherry_blossom)."""
        if self.current_atmosphere == atmosphere_type:
            return
            
        self.current_atmosphere = atmosphere_type
        self.particles.clear()
        
        if atmosphere_type == "rain":
            self._create_rain_particles(800)  # Increased for better coverage
        elif atmosphere_type == "snow":
            self._create_snow_particles(600)  # Increased for better coverage
        elif atmosphere_type == "cherry_blossom":
            self._create_cherry_blossom_particles(400)  # Increased for better coverage
    
    def set_random_atmosphere(self):
        """Set a random atmospheric effect."""
        atmosphere_options = ["none", "rain", "snow", "cherry_blossom"]
        random_atmosphere = random.choice(atmosphere_options)
        print(f"DEBUG: Setting atmosphere to: {random_atmosphere}")
        self.set_atmosphere(random_atmosphere)
    
    def _create_rain_particles(self, num_particles: int):
        """Create particles for rain effect in world coordinates."""
        print(f"DEBUG: Creating {num_particles} rain particles in world space")
        for _ in range(num_particles):
            particle = {
                'x': random.uniform(0, self.world_width),
                'y': random.uniform(0, self.world_height),
                'speed': random.uniform(300, 600),  # Pixels per second
                'width': 3,
                'height': random.randint(15, 30),
                'color': random.choice([(200, 200, 255), (180, 180, 255), (160, 160, 255)])
            }
            self.particles.append(particle)
    
    def _create_snow_particles(self, num_particles: int):
        """Create particles for snow effect in world coordinates."""
        print(f"DEBUG: Creating {num_particles} snow particles in world space")
        for _ in range(num_particles):
            particle = {
                'x': random.uniform(0, self.world_width),
                'y': random.uniform(0, self.world_height),
                'speed': random.uniform(50, 150),  # Pixels per second
                'drift': random.uniform(-30, 30),  # Horizontal drift pixels per second
                'size': random.randint(2, 5),
                'color': random.choice([(255, 255, 255), (240, 240, 255), (220, 220, 240)])
            }
            self.particles.append(particle)
    
    def _create_cherry_blossom_particles(self, num_particles: int):
        """Create particles for cherry blossom effect in world coordinates."""
        print(f"DEBUG: Creating {num_particles} cherry_blossom particles in world space")
        for _ in range(num_particles):
            particle = {
                'x': random.uniform(0, self.world_width),
                'y': random.uniform(0, self.world_height),
                'speed': random.uniform(80, 200),  # Pixels per second
                'drift': random.uniform(-100, 100),  # Horizontal drift pixels per second
                'size': random.randint(4, 7),
                'color': random.choice([(255, 182, 193), (255, 192, 203), (221, 160, 221)])
            }
            self.particles.append(particle)
    
    def update(self, dt: float):
        """Update atmospheric particles in world space - particles move and wrap within world bounds."""
        if self.current_atmosphere == "rain":
            self._update_rain(dt)
            self._update_lightning(dt)
        elif self.current_atmosphere == "snow":
            self._update_snow(dt)
        elif self.current_atmosphere == "cherry_blossom":
            self._update_cherry_blossom(dt)
    
    def _update_rain(self, dt: float):
        """Update rain particles in world coordinates."""
        for particle in self.particles:
            particle['y'] += particle['speed'] * dt
            if particle['y'] > self.world_height + 50:
                particle['y'] = -50
                particle['x'] = random.uniform(0, self.world_width)
    
    def _update_snow(self, dt: float):
        """Update snow particles in world coordinates."""
        for particle in self.particles:
            particle['y'] += particle['speed'] * dt
            particle['x'] += particle['drift'] * dt
            if particle['y'] > self.world_height + 50:
                particle['y'] = -50
                particle['x'] = random.uniform(0, self.world_width)
            # Keep particles within world bounds
            if particle['x'] < -50:
                particle['x'] = self.world_width + 50
            elif particle['x'] > self.world_width + 50:
                particle['x'] = -50
    
    def _update_cherry_blossom(self, dt: float):
        """Update cherry blossom particles in world coordinates."""
        for particle in self.particles:
            particle['y'] += particle['speed'] * dt
            particle['x'] += particle['drift'] * dt
            if particle['y'] > self.world_height + 50:
                particle['y'] = -50
                particle['x'] = random.uniform(0, self.world_width)
            # Keep particles within world bounds
            if particle['x'] < -50:
                particle['x'] = self.world_width + 50
            elif particle['x'] > self.world_width + 50:
                particle['x'] = -50
    
    def _update_lightning(self, dt: float):
        """Update lightning effects for rain."""
        self.lightning_timer += dt
        
        # Check if lightning should flash
        if self.lightning_timer >= self.next_lightning and not self.lightning_flash:
            self.lightning_flash = True
            self.lightning_duration = 0.15  # Flash for 150ms
            print("DEBUG: Lightning flash!")
            
        # Update lightning flash duration
        if self.lightning_flash:
            self.lightning_duration -= dt
            if self.lightning_duration <= 0:
                self.lightning_flash = False
                self.lightning_timer = 0.0
                self.next_lightning = random.uniform(4.0, 10.0)  # Next lightning in 4-10 seconds
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render atmospheric particles using world coordinates with camera offset like enemies."""
        if self.current_atmosphere != "none":
            visible_count = 0
            sample_particle = None
            for particle in self.particles:
                # Convert world coordinates to screen coordinates using camera offset
                screen_x = int(particle['x'] - offset[0])
                screen_y = int(particle['y'] - offset[1])
                
                # Store a sample particle for debugging
                if sample_particle is None:
                    sample_particle = particle
                
                # Only render if particle is visible on screen
                if (-50 <= screen_x <= self.screen_width + 50 and 
                    -50 <= screen_y <= self.screen_height + 50):
                    visible_count += 1
                    
                    if self.current_atmosphere == "rain":
                        # Render rain as vertical rectangles
                        pg.draw.rect(screen, particle['color'], 
                                   (screen_x, screen_y, particle['width'], particle['height']))
                    elif self.current_atmosphere == "snow":
                        # Render snow as circles
                        if particle['size'] > 0:
                            pg.draw.circle(screen, particle['color'], 
                                         (screen_x, screen_y), particle['size']//2 + 1)
                    elif self.current_atmosphere == "cherry_blossom":
                        # Render cherry blossoms as flowers
                        self._render_cherry_blossom(screen, screen_x, screen_y, particle['size'], particle['color'])
            
            # Only print debug info every 60 frames (once per second at 60 FPS)
            if hasattr(self, 'debug_counter'):
                self.debug_counter += 1
            else:
                self.debug_counter = 0
                
            if visible_count > 0 and sample_particle and self.debug_counter % 60 == 0:
                print(f"DEBUG: {visible_count}/{len(self.particles)} {self.current_atmosphere} particles visible. Sample world pos: ({sample_particle['x']:.1f}, {sample_particle['y']:.1f}), camera offset: ({offset[0]:.1f}, {offset[1]:.1f})")
    
    def _render_cherry_blossom(self, screen: pg.Surface, x: int, y: int, size: int, color: tuple):
        """Render cherry blossom as a flower with petals."""
        center_x, center_y = x, y
        petal_size = max(3, size)
        
        # Draw 5 petals in a flower pattern
        for i in range(5):
            angle = (i / 5) * 2 * math.pi
            petal_x = center_x + int(math.cos(angle) * (petal_size // 2))
            petal_y = center_y + int(math.sin(angle) * (petal_size // 2))
            
            # Draw petal as smaller circle
            pg.draw.circle(screen, color, (petal_x, petal_y), max(2, petal_size//3))
        
        # Draw center
        pg.draw.circle(screen, (255, 255, 200), (center_x, center_y), max(1, size//3))
    
    def add_footprint(self, x: float, y: float):
        """Add a footprint at the given position."""
        current_time = time.time()
        if current_time - self.last_footprint_time > 0.2:  # Limit footprint frequency
            self.footprints.append({
                'x': x,
                'y': y,
                'time': current_time,
                'alpha': 128
            })
            self.last_footprint_time = current_time
            
            # Limit footprints to prevent memory issues
            if len(self.footprints) > 50:
                self.footprints = self.footprints[-25:]  # Keep only the most recent 25
    
    def render_footprints(self, surface: pg.Surface, offset: Tuple[int, int]):
        """Render footprints on the world surface."""
        current_time = time.time()
        footprints_to_remove = []
        
        for i, footprint in enumerate(self.footprints):
            # Fade footprints over time
            age = current_time - footprint['time']
            if age > 5.0:  # Remove after 5 seconds
                footprints_to_remove.append(i)
                continue
                
            # Calculate alpha based on age
            alpha = max(0, int(128 * (1 - age / 5.0)))
            if alpha > 0:
                # Render footprint with world coordinates
                screen_x = int(footprint['x'] - offset[0])
                screen_y = int(footprint['y'] - offset[1])
                
                # Only render if visible on screen
                if (-20 <= screen_x <= surface.get_width() + 20 and 
                    -20 <= screen_y <= surface.get_height() + 20):
                    # Draw a simple footprint
                    pg.draw.circle(surface, (139, 69, 19, alpha), (screen_x, screen_y), 3)
        
        # Remove old footprints
        for i in reversed(footprints_to_remove):
            self.footprints.pop(i)
    
    def render_screen_overlays(self, screen: pg.Surface):
        """Render screen-wide atmospheric overlays."""
        if self.current_atmosphere == "rain":
            # Add lightning flash overlay
            if self.lightning_flash:
                flash_overlay = pg.Surface((self.screen_width, self.screen_height))
                flash_overlay.set_alpha(80)
                flash_overlay.fill((255, 255, 255))  # Bright white flash
                screen.blit(flash_overlay, (0, 0))
            else:
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
"""
Completely rewritten atmospheric effects system.
This system creates particles that exist at fixed world coordinates,
similar to how enemies work in the game.
"""

import pygame as pg
import random
import math
from typing import List, Tuple, Dict, Any

class Particle:
    """A single atmospheric particle with fixed world coordinates."""
    
    def __init__(self, world_x: float, world_y: float, particle_type: str):
        self.world_x = world_x
        self.world_y = world_y
        self.type = particle_type
        self.created_time = pg.time.get_ticks() / 1000.0
        
        if particle_type == "rain":
            self.speed_y = random.uniform(400, 800)  # Pixels per second downward
            self.speed_x = random.uniform(-50, 50)   # Slight horizontal drift
            self.width = random.randint(2, 4)
            self.height = random.randint(15, 25)
            self.color = random.choice([
                (180, 200, 255),
                (160, 180, 255),
                (200, 220, 255)
            ])
            
        elif particle_type == "snow":
            self.speed_y = random.uniform(60, 120)   # Slower falling
            self.speed_x = random.uniform(-80, 80)   # More horizontal drift
            self.size = random.randint(3, 8)
            self.color = random.choice([
                (255, 255, 255),
                (240, 240, 255),
                (220, 220, 240)
            ])
            
        elif particle_type == "cherry_blossom":
            self.speed_y = random.uniform(40, 100)   # Slow falling
            self.speed_x = random.uniform(-120, 120) # Wide drift
            self.size = random.randint(5, 11)  # Increased by 25% (was 4-9, now 5-11)
            self.color = random.choice([
                (255, 182, 193),  # Light pink
                (255, 192, 203),  # Pink
                (255, 174, 185),  # Rose pink
                (255, 160, 180),  # Deeper pink
                (240, 170, 190)   # Soft pink
            ])
            self.rotation = random.uniform(0, 2 * math.pi)
            self.rotation_speed = random.uniform(-2, 2)  # Radians per second
    
    def update(self, dt: float, world_bounds: Tuple[int, int], player_pos=None):
        """Update particle position in world space - they should fall naturally."""
        # Particles fall down in world space (like rain/snow should)
        self.world_y += self.speed_y * dt
        self.world_x += self.speed_x * dt
        
        if self.type == "cherry_blossom":
            self.rotation += self.rotation_speed * dt
        
        # Get world bounds (same as player system: -1920 to +1920, -1080 to +1080)
        # world_bounds parameter is (world_width, world_height), convert to actual bounds
        world_width, world_height = world_bounds
        min_x, min_y = -world_width//2, -world_height//2
        max_x, max_y = world_width//2, world_height//2
        
        # If particle falls below world, reset to top with random X position across entire world
        if self.world_y > max_y + 100:
            # Respawn at top of world with random X position across entire world width
            self.world_x = random.uniform(min_x, max_x)
            self.world_y = random.uniform(min_y - 200, min_y - 100)  # Spawn above world with variation
            
            # Debug: Print respawn info occasionally (reduced frequency for performance)
            if random.random() < 0.002:  # 0.2% chance (reduced from 0.5%)
                print(f"Particle respawned: ({self.world_x:.0f}, {self.world_y:.0f}), type: {self.type}")
            
        # Keep particles within world bounds - don't wrap, just constrain
        # World bounds are -1920 to +1920 (X) and -1080 to +1080 (Y)
        if self.world_x < min_x - 100:  # Allow small margin outside bounds
            self.world_x = max_x + 100   # Move to opposite side with margin
        elif self.world_x > max_x + 100:
            self.world_x = min_x - 100   # Move to opposite side with margin
    
    def render(self, screen: pg.Surface, camera_offset: Tuple[float, float]):
        """Render particle on screen using world-to-screen coordinate conversion like enemies."""
        # Convert world coordinates to screen coordinates - ADD the offset like enemies do
        screen_x = int(self.world_x + camera_offset[0])
        screen_y = int(self.world_y + camera_offset[1])
        
        # For atmospheric effects, render all particles within a very generous area
        # Use fast integer operations and pre-calculate screen bounds
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Pre-calculate screen bounds with margin for efficiency
        margin = 1000  # Reduced from 2000 for better performance while maintaining coverage
        min_screen_x = -margin
        max_screen_x = screen_width + margin
        min_screen_y = -margin
        max_screen_y = screen_height + margin
        
        # Fast bounds check using pre-calculated values
        if (min_screen_x <= screen_x <= max_screen_x and 
            min_screen_y <= screen_y <= max_screen_y):
            
            if self.type == "rain":
                pg.draw.rect(screen, self.color, 
                           (screen_x, screen_y, self.width, self.height))
                           
            elif self.type == "snow":
                if self.size > 0:
                    pg.draw.circle(screen, self.color, 
                                 (screen_x, screen_y), self.size // 2 + 1)
                                 
            elif self.type == "cherry_blossom":
                self._render_cherry_blossom(screen, screen_x, screen_y)
                
            return True  # Particle was rendered
        return False  # Particle was off-screen
    
    def _render_cherry_blossom(self, screen: pg.Surface, screen_x: int, screen_y: int):
        """Render a detailed but optimized cherry blossom flower."""
        # Pre-calculate values once per particle
        petal_length = max(3, int(self.size * 0.8))
        petal_width = max(2, int(self.size * 0.6))
        base_angle = 1.256637  # 2π/5 pre-calculated
        
        # Draw 5 petals with optimized rendering
        for i in range(5):
            angle = i * base_angle + self.rotation
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)
            
            # Calculate petal position once
            petal_offset_x = int(cos_angle * petal_length * 0.6)
            petal_offset_y = int(sin_angle * petal_length * 0.6)
            petal_center_x = screen_x + petal_offset_x
            petal_center_y = screen_y + petal_offset_y
            
            # Draw main petal as ellipse (single draw call per petal)
            petal_rect = pg.Rect(petal_center_x - petal_width//2, petal_center_y - petal_length//2, 
                                petal_width, petal_length)
            pg.draw.ellipse(screen, self.color, petal_rect)
            
            # Optional: Add single tip highlight only for larger particles (performance gate)
            if self.size >= 7:
                tip_x = screen_x + int(cos_angle * petal_length)
                tip_y = screen_y + int(sin_angle * petal_length)
                tip_color = (min(255, self.color[0] + 25), 
                            min(255, self.color[1] + 25), 
                            min(255, self.color[2] + 25))
                pg.draw.circle(screen, tip_color, (tip_x, tip_y), 1)
        
        # Simplified center (2 draw calls instead of 5+)
        center_size = max(2, self.size // 3)
        pg.draw.circle(screen, (200, 255, 200), (screen_x, screen_y), center_size)
        if center_size > 1:
            pg.draw.circle(screen, (255, 255, 150), (screen_x, screen_y), max(1, center_size // 2))


class AtmosphericEffects:
    """Manages atmospheric effects with particles at fixed world coordinates."""
    
    def __init__(self, world_width: int, world_height: int):
        self.world_width = world_width
        self.world_height = world_height
        self.particles: List[Particle] = []
        self.current_atmosphere = "none"
        # Use same coordinate system as player/enemies: center at (0,0)
        self.world_bounds = (-world_width//2, -world_height//2, world_width//2, world_height//2)  # (-1920, -1080, 1920, 1080)
        self.player_pos = (0, 0)  # Track player position for respawning
        
        # Lightning system
        self.lightning_timer = 0.0
        self.lightning_active = False
        self.lightning_duration = 0.0
        self.next_lightning_time = 0.0
        
        # Debug info
        self.debug_counter = 0
        
    def set_atmosphere(self, atmosphere_type: str, player_pos=None):
        """Set atmospheric effect type and generate particles around player."""
        if self.current_atmosphere == atmosphere_type:
            return
            
        print(f"Setting atmosphere to: {atmosphere_type}")
        self.current_atmosphere = atmosphere_type
        self.particles.clear()
        
        if atmosphere_type == "rain":
            self._generate_particles("rain", 600, player_pos)  # Reduced from 1000
        elif atmosphere_type == "snow":
            self._generate_particles("snow", 400, player_pos)  # Reduced from 800
        elif atmosphere_type == "cherry_blossom":
            self._generate_particles("cherry_blossom", 300, player_pos)  # Reduced from 500
    
    def _generate_particles(self, particle_type: str, count: int, player_pos=None):
        """Generate particles distributed across the entire world space, independent of player position."""
        print(f"Generating {count} {particle_type} particles across entire world ({self.world_width}x{self.world_height})")
        
        # Generate particles across the ENTIRE world, not around player
        min_x, min_y, max_x, max_y = self.world_bounds  # (-1920, -1080, 1920, 1080)
        
        for _ in range(count):
            # Distribute particles randomly across the entire world
            world_x = random.uniform(min_x, max_x)
            world_y = random.uniform(min_y, max_y)
            
            particle = Particle(world_x, world_y, particle_type)
            self.particles.append(particle)
    
    def update(self, dt: float, player_pos=None):
        """Update all particles and effects."""
        if player_pos:
            self.player_pos = player_pos
            # Debug: Print player position occasionally
            if hasattr(self, 'debug_counter'):
                self.debug_counter = (self.debug_counter + 1) % 300  # Every 5 seconds at 60fps
                if self.debug_counter == 0:
                    print(f"Player position update: ({player_pos[0]:.1f}, {player_pos[1]:.1f})")
            else:
                self.debug_counter = 0
            
        if self.current_atmosphere != "none":
            # Update all particles with player position for respawning
            for particle in self.particles:
                particle.update(dt, (self.world_width, self.world_height), self.player_pos)
            
            # Update lightning for rain
            if self.current_atmosphere == "rain":
                self._update_lightning(dt)
    
    def _update_lightning(self, dt: float):
        """Handle lightning flashes during rain."""
        self.lightning_timer += dt
        
        # Start lightning flash
        if self.lightning_timer >= self.next_lightning_time and not self.lightning_active:
            self.lightning_active = True
            self.lightning_duration = random.uniform(0.1, 0.2)  # Flash duration
            self.next_lightning_time = self.lightning_timer + random.uniform(5.0, 12.0)
            print("Lightning flash!")
        
        # End lightning flash
        if self.lightning_active:
            self.lightning_duration -= dt
            if self.lightning_duration <= 0:
                self.lightning_active = False
    
    def render(self, screen: pg.Surface, camera_offset: Tuple[float, float]):
        """Render all visible particles."""
        if self.current_atmosphere == "none":
            return
            
        visible_particles = 0
        sample_particle = None
        left_particles = 0
        right_particles = 0
        left_visible = 0
        right_visible = 0
        
        for particle in self.particles:
            # Count particles by side
            if particle.world_x < 0:
                left_particles += 1
            else:
                right_particles += 1
                
            if particle.render(screen, camera_offset):
                visible_particles += 1
                if particle.world_x < 0:
                    left_visible += 1
                else:
                    right_visible += 1
                if sample_particle is None:
                    sample_particle = particle
        
        # Debug output (occasional) - reduced frequency for performance
        self.debug_counter += 1
        if self.debug_counter % 1200 == 0 and sample_particle:  # Every 20 seconds at 60 FPS
            print(f"Atmospheric effects: {visible_particles}/{len(self.particles)} {self.current_atmosphere} particles")
    
    def render_screen_effects(self, screen: pg.Surface):
        """Render screen-wide atmospheric effects (tints, lightning)."""
        if self.current_atmosphere == "none":
            return
            
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        if self.current_atmosphere == "rain":
            if self.lightning_active:
                # Lightning flash - bright white overlay
                flash_surface = pg.Surface((screen_width, screen_height))
                flash_surface.fill((255, 255, 255))
                flash_surface.set_alpha(100)
                screen.blit(flash_surface, (0, 0))
            else:
                # Rain tint - subtle blue
                tint_surface = pg.Surface((screen_width, screen_height))
                tint_surface.fill((100, 150, 200))
                tint_surface.set_alpha(25)
                screen.blit(tint_surface, (0, 0))
                
        elif self.current_atmosphere == "snow":
            # Snow tint - subtle blue-white
            tint_surface = pg.Surface((screen_width, screen_height))
            tint_surface.fill((200, 220, 255))
            tint_surface.set_alpha(20)
            screen.blit(tint_surface, (0, 0))
            
        elif self.current_atmosphere == "cherry_blossom":
            # Cherry blossom tint - subtle pink
            tint_surface = pg.Surface((screen_width, screen_height))
            tint_surface.fill((255, 200, 220))
            tint_surface.set_alpha(15)
            screen.blit(tint_surface, (0, 0))
    
    def set_random_atmosphere(self, player_pos=None):
        """Set a random atmospheric effect."""
        atmosphere_types = ["none", "rain", "snow", "cherry_blossom"]
        selected = random.choice(atmosphere_types)
        self.set_atmosphere(selected, player_pos)
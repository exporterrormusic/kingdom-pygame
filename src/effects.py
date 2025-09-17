"""
This module contains the definitions for various visual effects used in the game.
These classes are instantiated and managed by the EffectsManager.
"""

import pygame as pg
import math
import random
from typing import List, Tuple

class ComicDashLine:
    """Comic book/anime style dash line effect that follows the player with tapered styling."""
    
    def __init__(self, relative_start_x: float, relative_start_y: float, 
                 relative_end_x: float, relative_end_y: float, 
                 thickness: int = 4, color: Tuple[int, int, int, int] = (255, 255, 255, 100)):
        """Initialize a simple dash line with relative positions from player."""
        self.relative_start = pg.Vector2(relative_start_x, relative_start_y)
        self.relative_end = pg.Vector2(relative_end_x, relative_end_y)
        self.start_thickness = thickness
        self.color = color[:3]  # RGB only
        self.base_alpha = color[3] if len(color) > 3 else 100  # More transparent base
        self.alpha = self.base_alpha
        self.max_life = 0.5  # Shorter duration for better performance
        self.life = self.max_life
        
        # Calculate line properties for tapered effect
        self.length = (self.relative_end - self.relative_start).length()
        if self.length > 0:
            self.direction = (self.relative_end - self.relative_start).normalize()
        else:
            self.direction = pg.Vector2(1, 0)
    
    def update(self, dt: float, player_pos: pg.Vector2) -> bool:
        """Update the dash line with player position. Returns True if should be removed."""
        self.life -= dt
        
        # Update absolute positions based on current player position
        self.start_pos = player_pos + self.relative_start
        self.end_pos = player_pos + self.relative_end
        
        # Fade out over time with slower fade at the beginning
        fade_progress = 1.0 - (self.life / self.max_life)
        if fade_progress < 0.2:
            # Stay at base alpha for the first 20% of lifetime
            self.alpha = self.base_alpha
        else:
            # Then fade out smoothly
            remaining_fade = (fade_progress - 0.2) / 0.8
            self.alpha = max(0, int(self.base_alpha * (1.0 - remaining_fade)))
        
        return self.life <= 0
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render a simple, performance-optimized dash line with enhanced glow."""
        if self.alpha <= 0 or not hasattr(self, 'start_pos'):
            return
            
        # Calculate render positions
        start_render = (int(self.start_pos.x + offset[0]), int(self.start_pos.y + offset[1]))
        end_render = (int(self.end_pos.x + offset[0]), int(self.end_pos.y + offset[1]))
        
        if start_render == end_render:
            return
            
        # Enhanced multi-layer glow for better visual impact
        glow_alpha = max(0, int(self.alpha * 0.4))  # Stronger glow
        if glow_alpha > 20:  # Draw glow if visible enough
            # Outer glow layer - soft and wide
            outer_glow_color = (*self.color, max(10, int(glow_alpha * 0.6)))
            outer_glow_thickness = self.start_thickness + 6
            pg.draw.line(screen, outer_glow_color, start_render, end_render, outer_glow_thickness)
            
            # Inner glow layer - brighter and narrower
            inner_glow_color = (*self.color, glow_alpha)
            inner_glow_thickness = self.start_thickness + 3
            pg.draw.line(screen, inner_glow_color, start_render, end_render, inner_glow_thickness)
        
        # Draw main line with good visibility
        main_alpha = max(0, int(self.alpha * 0.95))  # Very visible main line
        color_with_alpha = (*self.color, main_alpha)
        
        # Draw main line
        pg.draw.line(screen, color_with_alpha, start_render, end_render, self.start_thickness)

class ParticleEffect:
    """Simple particle effect for collisions and explosions."""
    
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], 
                 particle_count: int = 8, speed: float = 100):
        """Initialize a particle effect."""
        self.particles = []
        self.lifetime = 1.0
        self.age = 0.0
        
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed_variation = random.uniform(0.5, 1.5)
            particle = {
                'pos': pg.Vector2(x, y),
                'velocity': pg.Vector2(
                    math.cos(angle) * speed * speed_variation,
                    math.sin(angle) * speed * speed_variation
                ),
                'color': color,
                'size': random.randint(2, 4),
                'life': random.uniform(0.5, 1.0)
            }
            self.particles.append(particle)
    
    def update(self, dt: float) -> bool:
        """Update particles. Returns True if effect should be removed."""
        self.age += dt
        
        particles_to_remove = []
        
        for particle in self.particles:
            particle['pos'] += particle['velocity'] * dt
            particle['life'] -= dt
            
            # Apply gravity/friction
            particle['velocity'] *= 0.98
            
            if particle['life'] <= 0:
                particles_to_remove.append(particle)
        
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        return len(self.particles) == 0
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render all particles."""
        for particle in self.particles:
            alpha = max(0, particle['life'])
            color = tuple(int(c * alpha) for c in particle['color'])
            render_x = int(particle['pos'].x + offset[0])
            render_y = int(particle['pos'].y + offset[1])
            pg.draw.circle(screen, color, (render_x, render_y), particle['size'])

class EnhancedExplosionEffect:
    """Enhanced fiery explosion effect with multiple particle types."""
    
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], 
                 particle_count: int = 20, speed: float = 150, 
                 size_range: Tuple[int, int] = (3, 6), explosion_type: str = "normal",
                 direction_angle: float = None, spread_angle: float = 360):
        """Initialize enhanced explosion effect."""
        self.particles = []
        self.explosion_type = explosion_type
        self.age = 0.0
        
        # Different explosion types have different behaviors
        if explosion_type == "core":
            self.lifetime = 0.6
            gravity_factor = 0.95
        elif explosion_type == "fire":
            self.lifetime = 1.0
            gravity_factor = 0.92
        elif explosion_type == "smoke":
            self.lifetime = 1.2
            gravity_factor = 0.88
        elif explosion_type == "sparks":
            self.lifetime = 0.4
            gravity_factor = 0.98
        elif explosion_type == "muzzle_flash":
            self.lifetime = 0.3
            gravity_factor = 1.0
        elif explosion_type == "energy_wisps":
            self.lifetime = 0.8
            gravity_factor = 0.98
        elif explosion_type == "pellet_core":
            self.lifetime = 0.4
            gravity_factor = 0.96
        elif explosion_type == "pellet_sparks":
            self.lifetime = 0.3
            gravity_factor = 0.99
        elif explosion_type == "energy_residue":
            self.lifetime = 0.6
            gravity_factor = 0.92
        elif explosion_type == "tactical_flash":
            self.lifetime = 0.25
            gravity_factor = 1.0
        elif explosion_type == "anime_flash":
            self.lifetime = 0.2
            gravity_factor = 1.0
        elif explosion_type == "tactical_smoke":
            self.lifetime = 0.8
            gravity_factor = 0.90
        elif explosion_type == "tactical_sparks":
            self.lifetime = 0.35
            gravity_factor = 0.95
        elif explosion_type == "impact_flash":
            self.lifetime = 0.15
            gravity_factor = 1.0
        elif explosion_type == "tactical_debris":
            self.lifetime = 0.6
            gravity_factor = 0.85
        elif explosion_type == "neon_burst":
            self.lifetime = 0.15
            gravity_factor = 1.0
        elif explosion_type == "digital_fragments":
            self.lifetime = 0.12
            gravity_factor = 1.0
        elif explosion_type == "holographic_glow":
            self.lifetime = 0.1
            gravity_factor = 1.0
        elif explosion_type == "anime_energy_burst":
            self.lifetime = 0.2
            gravity_factor = 1.0
        elif explosion_type == "skid_mark":
            self.lifetime = 1.0
            gravity_factor = 0.8
        else:
            self.lifetime = 0.8
            gravity_factor = 0.95
        
        for _ in range(particle_count):
            if direction_angle is not None:
                spread_rad = math.radians(spread_angle)
                angle = math.radians(direction_angle) + random.uniform(-spread_rad/2, spread_rad/2)
            else:
                angle = random.uniform(0, 2 * math.pi)
                
            speed_variation = random.uniform(0.3, 1.8)
            
            if explosion_type == "sparks":
                velocity_magnitude = speed * speed_variation
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.2, 0.8)
            elif explosion_type == "smoke":
                velocity_magnitude = speed * speed_variation * 0.6
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.8, 1.4)
            else:
                velocity_magnitude = speed * speed_variation
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.5, 1.5)
            
            particle = {
                'pos': pg.Vector2(x, y),
                'velocity': pg.Vector2(
                    math.cos(angle) * velocity_magnitude,
                    math.sin(angle) * velocity_magnitude
                ),
                'base_color': color,
                'size': size,
                'initial_size': size,
                'life': life_duration,
                'initial_life': life_duration,
                'gravity_factor': gravity_factor
            }
            self.particles.append(particle)
    
    def update(self, dt: float) -> bool:
        """Update particles with enhanced effects."""
        self.age += dt
        particles_to_remove = []
        
        for particle in self.particles:
            particle['pos'] += particle['velocity'] * dt
            particle['life'] -= dt
            
            if self.explosion_type == "smoke":
                particle['velocity'] *= 0.85
                particle['size'] = min(particle['initial_size'] * 2, 
                                     particle['initial_size'] + (self.age * 8))
            elif self.explosion_type == "sparks":
                particle['velocity'] *= 0.99
                particle['velocity'].x += random.uniform(-10, 10)
                particle['velocity'].y += random.uniform(-10, 10)
            else:
                particle['velocity'] *= particle['gravity_factor']
            
            if particle['life'] <= 0:
                particles_to_remove.append(particle)
        
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        return len(self.particles) == 0
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render enhanced explosion particles."""
        for particle in self.particles:
            life_ratio = particle['life'] / particle['initial_life']
            render_x = int(particle['pos'].x + offset[0])
            render_y = int(particle['pos'].y + offset[1])
            
            base_r, base_g, base_b = particle['base_color']
            
            if self.explosion_type == "core":
                if life_ratio > 0.7: color = (255, 255, 255)
                elif life_ratio > 0.3: color = (255, 255, 100)
                else: color = (255, 150, 0)
            elif self.explosion_type == "fire":
                if life_ratio > 0.6: color = (255, 200, 0)
                elif life_ratio > 0.3: color = (255, 100, 0)
                else: color = (150, 50, 0)
            elif self.explosion_type == "smoke":
                if life_ratio > 0.3:
                    gray_value = int(120 * life_ratio)
                    color = (gray_value, gray_value//2, gray_value//3)
                else:
                    fade_factor = life_ratio / 0.3
                    gray_value = int(60 * fade_factor)
                    color = (gray_value, gray_value//2, gray_value//4)
            elif self.explosion_type == "sparks":
                if random.random() > 0.3: color = (255, 255, 200)
                else: color = (255, 255, 255)
            else:
                color = particle['base_color']
            
            if self.explosion_type == "smoke" and life_ratio < 0.3:
                alpha_factor = life_ratio / 0.3
            else:
                alpha_factor = max(0.05, life_ratio)
            
            final_color = tuple(int(c * alpha_factor) for c in color)
            
            if self.explosion_type in ["core", "fire", "sparks"]:
                glow_size = particle['size'] + 2
                glow_color = tuple(int(c * 0.3) for c in final_color)
                if glow_size > 0:
                    pg.draw.circle(screen, glow_color, (render_x, render_y), glow_size)
            
            if particle['size'] > 0:
                pg.draw.circle(screen, final_color, (render_x, render_y), int(particle['size']))

class MysticalBeamEffect:
    """A mystical beam effect for sword thrust attacks that follows the player."""
    
    def __init__(self, player_ref, relative_angle: float, beam_range: float, 
                 width: float, duration: float, color: list, damage: float):
        """Initialize mystical beam effect that follows the player."""
        self.player_ref = player_ref
        self.relative_angle = relative_angle
        self.beam_range = beam_range
        self.width = width
        self.max_duration = duration
        self.duration = duration
        self.color = color
        self.damage = damage
        self.alive = True
        self.damaged_enemies = set()
        
        self.particles = []
        self.update_particles()
    
    def get_current_position(self):
        """Get current position of the beam (follows player)."""
        if self.player_ref:
            gun_tip = self.player_ref.get_gun_tip_position()
            return (gun_tip.x, gun_tip.y)
        return (0, 0)
    
    def get_current_angle(self):
        """Get current angle of the beam (follows player rotation)."""
        if self.player_ref:
            return self.player_ref.angle + self.relative_angle
        return self.relative_angle
    
    def get_beam_endpoints(self):
        """Get current start and end positions of the beam."""
        current_pos = self.get_current_position()
        current_angle = self.get_current_angle()
        angle_rad = math.radians(current_angle)
        
        start_x, start_y = current_pos
        end_x = start_x + self.beam_range * math.cos(angle_rad)
        end_y = start_y + self.beam_range * math.sin(angle_rad)
        
        return (start_x, start_y, end_x, end_y)
    
    def update_particles(self):
        """Update particle positions to follow the beam."""
        start_x, start_y, end_x, end_y = self.get_beam_endpoints()
        
        self.particles = []
        
        beam_dx = end_x - start_x
        beam_dy = end_y - start_y
        beam_length = math.sqrt(beam_dx**2 + beam_dy**2)
        
        if beam_length > 0:
            num_particles = int(beam_length / 15)
            for i in range(num_particles):
                t = i / max(1, num_particles - 1)
                particle_x = start_x + t * beam_dx + random.uniform(-self.width/4, self.width/4)
                particle_y = start_y + t * beam_dy + random.uniform(-self.width/4, self.width/4)
                
                self.particles.append({
                    'x': particle_x,
                    'y': particle_y,
                    'size': random.uniform(2, 5),
                    'alpha': random.uniform(0.7, 1.0),
                    'pulse_speed': random.uniform(2, 4)
                })
    
    def update(self, dt: float):
        """Update beam effect."""
        self.duration -= dt
        if self.duration <= 0:
            self.alive = False
            return True
        
        self.update_particles()
        
        for particle in self.particles:
            particle['alpha'] = 0.5 + 0.5 * math.sin(particle['pulse_speed'] * (self.max_duration - self.duration))
        
        return False
    
    def check_enemy_collision(self, enemy) -> bool:
        """Check if enemy is currently being hit by this beam effect."""
        if not self.alive or not self.player_ref or id(enemy) in self.damaged_enemies:
            return False
            
        start_x, start_y, end_x, end_y = self.get_beam_endpoints()
        
        beam_dx = end_x - start_x
        beam_dy = end_y - start_y
        beam_length = math.sqrt(beam_dx**2 + beam_dy**2)
        
        if beam_length == 0:
            return False
        
        beam_dx /= beam_length
        beam_dy /= beam_length
        
        to_enemy_x = enemy.pos.x - start_x
        to_enemy_y = enemy.pos.y - start_y
        
        projection = to_enemy_x * beam_dx + to_enemy_y * beam_dy
        
        fade_progress = min(1.0, (self.max_duration - self.duration) / (self.max_duration * 0.3))
        current_beam_length = beam_length * fade_progress
        
        if 0 <= projection <= current_beam_length:
            closest_x = start_x + projection * beam_dx
            closest_y = start_y + projection * beam_dy
            perpendicular_distance = math.sqrt((enemy.pos.x - closest_x)**2 + (enemy.pos.y - closest_y)**2)
            
            enemy_radius = getattr(enemy, 'size', 20) / 2
            beam_radius = self.width / 2
            
            if perpendicular_distance <= (beam_radius + enemy_radius):
                self.damaged_enemies.add(id(enemy))
                return True
                
        return False
    
    def render(self, screen, offset):
        """Render mystical beam effect."""
        if not self.alive:
            return
        
        alpha_factor = max(0.5, self.duration / self.max_duration)
        
        start_x, start_y, end_x, end_y = self.get_beam_endpoints()
        
        start_pos = (int(start_x + offset[0]), int(start_y + offset[1]))
        end_pos = (int(end_x + offset[0]), int(end_y + offset[1]))
        
        beam_colors = [
            (120, 60, 180), (160, 100, 220), (200, 140, 255),
            (230, 180, 255), (255, 220, 255)
        ]
        
        beam_length = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        for i, color in enumerate(beam_colors):
            base_width = max(3, int(self.width * (6 - i) * 0.6))
            layer_alpha = max(0.4, alpha_factor * (0.6 + i * 0.15))
            
            if base_width > 0:
                beam_color = [min(255, max(60, int(c * layer_alpha))) for c in color]
                
                num_segments = 25
                for segment in range(num_segments):
                    t = segment / (num_segments - 1)
                    
                    if t < 0.1: taper_factor = t / 0.1
                    elif t > 0.9: taper_factor = (1.0 - t) / 0.1
                    else: taper_factor = 1.0
                    
                    taper_factor = max(0.05, taper_factor)
                    
                    fade_progress = min(1.0, (self.max_duration - self.duration) / (self.max_duration * 0.3))
                    
                    segment_alpha = 1.0 if t <= fade_progress else 0.0
                    
                    segment_width = max(1, int(base_width * taper_factor))
                    
                    final_layer_alpha = layer_alpha * segment_alpha
                    
                    if final_layer_alpha > 0.1:
                        seg_start_x = start_x + t * (end_x - start_x)
                        seg_start_y = start_y + t * (end_y - start_y)
                        
                        if segment < num_segments - 1:
                            t_next = (segment + 1) / (num_segments - 1)
                            seg_end_x = start_x + t_next * (end_x - start_x)
                            seg_end_y = start_y + t_next * (end_y - start_y)
                        else:
                            seg_end_x = end_x
                            seg_end_y = end_y
                        
                        seg_start_pos = (int(seg_start_x + offset[0]), int(seg_start_y + offset[1]))
                        seg_end_pos = (int(seg_end_x + offset[0]), int(seg_end_y + offset[1]))
                        
                        final_beam_color = [min(255, max(60, int(c * final_layer_alpha))) for c in color]
                        
                        try:
                            if segment_width > 0:
                                pg.draw.line(screen, final_beam_color, seg_start_pos, seg_end_pos, segment_width)
                        except (ValueError, OverflowError):
                            pass
        
        for particle in self.particles:
            particle_alpha = max(0.3, particle['alpha'] * alpha_factor)
            if particle_alpha > 0.1:
                particle_color = [int(255 * particle_alpha)] * 3
                particle_pos = (int(particle['x'] + offset[0]), int(particle['y'] + offset[1]))
                particle_size = max(2, int(particle['size'] * alpha_factor))
                try:
                    pg.draw.circle(screen, particle_color, particle_pos, particle_size)
                except (ValueError, OverflowError):
                    pass

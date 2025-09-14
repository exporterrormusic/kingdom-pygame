"""
Missile system for rocket launcher weapons.
Handles missile projectiles with targeting, explosions, and visual effects.
"""

import pygame as pg
import math
from typing import Tuple, Optional
from enum import Enum

class MissileState(Enum):
    """States for missile lifecycle."""
    FLYING = "flying"
    EXPLODING = "exploding"
    FINISHED = "finished"

class Missile:
    """Individual missile projectile with targeting and explosion capabilities."""
    
    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float, 
                 damage: int = 120, explosion_radius: float = 150, speed: float = 800):
        """Initialize a missile.
        
        Args:
            start_x, start_y: Starting position
            target_x, target_y: Target position to fly toward
            damage: Explosion damage
            explosion_radius: AOE explosion radius
            speed: Missile flight speed (doubled for more impact)
        """
        self.pos = pg.Vector2(start_x, start_y)
        self.target = pg.Vector2(target_x, target_y)
        self.damage = damage
        self.explosion_radius = explosion_radius
        self.speed = speed
        self.state = MissileState.FLYING
        
        # Calculate flight direction
        direction = self.target - self.pos
        distance = direction.length()
        if distance > 0:
            self.velocity = direction.normalize() * speed
        else:
            self.velocity = pg.Vector2(0, 0)
        
        # Visual properties (doubled for more impact)
        self.length = 50  # Length of missile body (doubled from 25)
        self.width = 16   # Width of missile body (doubled from 8)
        self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        
        # Trail effect
        self.trail_positions = []
        self.max_trail_length = 12
        
        # Animation properties for flickering flame
        self.flame_flicker_time = 0.0
        self.flame_intensity_base = 1.0
        self.flame_intensity_variance = 0.3
        
        # Visual-based damage tracking (like sword system)
        self.damaged_enemies = set()  # Track enemies already damaged
        
        # Explosion properties
        self.explosion_age = 0.0
        self.explosion_duration = 0.6  # How long explosion effect lasts
        self.explosion_max_radius = explosion_radius
        
        # Flight properties
        self.age = 0.0
        self.max_flight_time = 5.0  # Max seconds before auto-detonation
        
    def update(self, dt: float, enemies: list = None) -> bool:
        """Update missile state. Returns True if missile should be removed."""
        self.age += dt
        
        # Update flame animation time for flickering effect
        self.flame_flicker_time += dt
        
        if self.state == MissileState.FLYING:
            return self._update_flight(dt, enemies)
        elif self.state == MissileState.EXPLODING:
            return self._update_explosion(dt)
        else:
            return True
    
    def _update_flight(self, dt: float, enemies: list = None) -> bool:
        """Update missile during flight phase."""
        # Move missile
        old_pos = self.pos.copy()
        self.pos += self.velocity * dt
        
        # Update trail
        self.trail_positions.append(old_pos)
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)
        
        # Update angle based on velocity
        if self.velocity.length() > 0:
            self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        
        # Check if reached target or close enough
        distance_to_target = (self.target - self.pos).length()
        if distance_to_target < 10 or self.age >= self.max_flight_time:
            self._detonate()
            return False
        
        # Check collision with enemies
        if enemies:
            for enemy in enemies:
                enemy_distance = (enemy.pos - self.pos).length()
                if enemy_distance < 30:  # Close enough to trigger explosion
                    self._detonate()
                    return False
        
        return False
    
    def _update_explosion(self, dt: float) -> bool:
        """Update missile during explosion phase."""
        self.explosion_age += dt
        return self.explosion_age >= self.explosion_duration
    
    def _detonate(self):
        """Trigger missile detonation."""
        self.state = MissileState.EXPLODING
        self.explosion_age = 0.0
        
    def check_visual_damage(self, enemies) -> list:
        """Check for visual-based damage from missile body and explosion.
        Returns list of damage events for enemies hit by visual effects."""
        damage_events = []
        
        if self.state == MissileState.FLYING:
            # Check missile body collision
            for enemy in enemies:
                if self._check_missile_body_collision(enemy):
                    damage_events.append({
                        'enemy': enemy,
                        'damage': self.damage // 4,  # Reduced damage for body hits
                        'type': 'missile_body'
                    })
        
        elif self.state == MissileState.EXPLODING:
            # Check explosion visual collision
            for enemy in enemies:
                if self._check_explosion_collision(enemy):
                    damage_events.append({
                        'enemy': enemy,
                        'damage': self.damage,  # Full damage for explosion
                        'type': 'explosion'
                    })
        
        return damage_events
    
    def _check_missile_body_collision(self, enemy) -> bool:
        """Check if enemy is visually hit by missile body."""
        if id(enemy) in self.damaged_enemies:
            return False  # Already damaged
            
        # Calculate distance from missile to enemy
        dx = enemy.pos.x - self.pos.x
        dy = enemy.pos.y - self.pos.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Check if enemy is within missile body hitbox (doubled size)
        missile_radius = max(self.length, self.width) / 2
        if distance <= missile_radius + enemy.size / 2:
            self.damaged_enemies.add(id(enemy))
            return True
        
        return False
    
    def _check_explosion_collision(self, enemy) -> bool:
        """Check if enemy is visually hit by explosion effects."""
        if id(enemy) in self.damaged_enemies:
            return False  # Already damaged
            
        # Calculate distance from explosion center to enemy
        dx = enemy.pos.x - self.pos.x
        dy = enemy.pos.y - self.pos.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Calculate current explosion visual radius based on age
        progress = min(self.explosion_age / self.explosion_duration, 1.0)
        
        # Visual explosion grows during first 70% of duration
        if progress < 0.7:
            current_radius = self.explosion_max_radius * (progress / 0.7)
        else:
            current_radius = self.explosion_max_radius  # Keep full size during fade
        
        # Check if enemy is within current explosion visual radius
        if distance <= current_radius + enemy.size / 2:
            self.damaged_enemies.add(id(enemy))
            return True
        
        return False
        
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render the missile based on its current state."""
        if self.state == MissileState.FLYING:
            self._render_missile(screen, offset)
        elif self.state == MissileState.EXPLODING:
            self._render_explosion(screen, offset)
    
    def _render_missile(self, screen: pg.Surface, offset: Tuple[float, float]):
        """Render the enhanced flying missile with detailed sprite and effects."""
        render_x = self.pos.x + offset[0]
        render_y = self.pos.y + offset[1]
        
        # Enhanced exhaust trail with multiple layers
        self._render_enhanced_exhaust_trail(screen, offset)
        
        # Calculate missile orientation
        angle_rad = math.radians(self.angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Enhanced missile body - doubled for more impact
        missile_length = 70  # Doubled from 35
        missile_width = 20   # Doubled from 10
        
        # Missile tip (front)
        tip_x = render_x + cos_angle * (missile_length / 2)
        tip_y = render_y + sin_angle * (missile_length / 2)
        
        # Missile back
        back_x = render_x - cos_angle * (missile_length / 2)
        back_y = render_y - sin_angle * (missile_length / 2)
        
        # Side points for missile body
        perpendicular_x = -sin_angle * (missile_width / 2)
        perpendicular_y = cos_angle * (missile_width / 2)
        
        # Draw missile body with multiple segments for detail
        self._render_detailed_missile_body(screen, render_x, render_y, cos_angle, sin_angle, 
                                         missile_length, missile_width, perpendicular_x, perpendicular_y)
        
        # Enhanced exhaust flame
        self._render_enhanced_exhaust_flame(screen, back_x, back_y, cos_angle, sin_angle, perpendicular_x, perpendicular_y)
    
    def _render_enhanced_exhaust_trail(self, screen: pg.Surface, offset: Tuple[float, float]):
        """Render enhanced exhaust trail with layered effects."""
        for i, trail_pos in enumerate(self.trail_positions):
            alpha_factor = (i + 1) / len(self.trail_positions)
            trail_render_x = trail_pos.x + offset[0]
            trail_render_y = trail_pos.y + offset[1]
            
            # Multiple trail layers for depth
            trail_sizes = [8, 6, 4]  # Different sizes for layering
            trail_colors = [
                (255, 100, 0),    # Bright orange outer
                (255, 150, 50),   # Orange middle  
                (255, 255, 100),  # Yellow inner
            ]
            
            for size, color in zip(trail_sizes, trail_colors):
                adjusted_size = max(1, int(size * alpha_factor * 0.7))
                adjusted_color = (
                    int(color[0] * alpha_factor),
                    int(color[1] * alpha_factor),
                    int(color[2] * alpha_factor)
                )
                pg.draw.circle(screen, adjusted_color, (int(trail_render_x), int(trail_render_y)), adjusted_size)
    
    def _render_detailed_missile_body(self, screen: pg.Surface, render_x: float, render_y: float,
                                    cos_angle: float, sin_angle: float, missile_length: float, 
                                    missile_width: float, perpendicular_x: float, perpendicular_y: float):
        """Render detailed missile body with segments and markings."""
        # Main body segments
        segments = 3
        segment_length = missile_length / segments
        
        for i in range(segments):
            segment_start = (i - segments/2 + 0.5) * segment_length
            segment_end = segment_start + segment_length * 0.8
            
            # Segment colors - darker at back, brighter at front
            color_intensity = 0.6 + 0.4 * (i / (segments - 1))
            segment_color = (
                int(180 * color_intensity),
                int(180 * color_intensity), 
                int(200 * color_intensity)
            )
            
            # Segment positions
            seg_front_x = render_x + cos_angle * segment_end
            seg_front_y = render_y + sin_angle * segment_end
            seg_back_x = render_x + cos_angle * segment_start  
            seg_back_y = render_y + sin_angle * segment_start
            
            # Draw segment
            segment_points = [
                (seg_front_x + perpendicular_x, seg_front_y + perpendicular_y),
                (seg_front_x - perpendicular_x, seg_front_y - perpendicular_y),
                (seg_back_x - perpendicular_x, seg_back_y - perpendicular_y),
                (seg_back_x + perpendicular_x, seg_back_y + perpendicular_y)
            ]
            pg.draw.polygon(screen, segment_color, segment_points)
        
        # Missile tip (warhead)
        tip_x = render_x + cos_angle * (missile_length / 2)
        tip_y = render_y + sin_angle * (missile_length / 2)
        tip_back_x = render_x + cos_angle * (missile_length / 2 - 8)
        tip_back_y = render_y + sin_angle * (missile_length / 2 - 8)
        
        tip_points = [
            (tip_x, tip_y),  # Sharp tip
            (tip_back_x + perpendicular_x, tip_back_y + perpendicular_y),
            (tip_back_x - perpendicular_x, tip_back_y - perpendicular_y)
        ]
        pg.draw.polygon(screen, (255, 200, 100), tip_points)  # Golden tip
        
        # Enhanced fins
        fin_length = missile_width * 1.2
        fin_back_x = render_x - cos_angle * (missile_length / 2 - 5)
        fin_back_y = render_y - sin_angle * (missile_length / 2 - 5)
        
        # Four fins for more detail
        for fin_angle in [0.7, -0.7, 2.4, -2.4]:  # Radians offset
            fin_perp_x = -sin_angle * math.cos(fin_angle) * fin_length - cos_angle * math.sin(fin_angle) * fin_length
            fin_perp_y = cos_angle * math.cos(fin_angle) * fin_length - sin_angle * math.sin(fin_angle) * fin_length
            
            fin_points = [
                (fin_back_x, fin_back_y),
                (fin_back_x + fin_perp_x, fin_back_y + fin_perp_y),
                (fin_back_x - cos_angle * 8 + fin_perp_x * 0.6, fin_back_y - sin_angle * 8 + fin_perp_y * 0.6)
            ]
            pg.draw.polygon(screen, (150, 100, 100), fin_points)
    
    def _render_enhanced_exhaust_flame(self, screen: pg.Surface, back_x: float, back_y: float,
                                     cos_angle: float, sin_angle: float, perpendicular_x: float, perpendicular_y: float):
        """Render enhanced exhaust flame with multiple layers and flickering animation."""
        flame_length = 50  # Doubled from 25 to match bigger missile
        
        # Calculate flickering intensity based on time
        flicker_speed = 12.0  # Flicker frequency
        flicker_1 = math.sin(self.flame_flicker_time * flicker_speed) * 0.15
        flicker_2 = math.sin(self.flame_flicker_time * flicker_speed * 1.3) * 0.1
        flicker_3 = math.sin(self.flame_flicker_time * flicker_speed * 0.7) * 0.12
        
        # Calculate dynamic flame intensity
        flame_intensity = self.flame_intensity_base + flicker_1 + flicker_2 + flicker_3
        flame_intensity = max(0.6, min(1.3, flame_intensity))  # Clamp between 60% and 130%
        
        # Multiple flame layers for realistic effect with flickering
        base_colors = [
            (255, 100, 0),    # Outer orange
            (255, 150, 50),   # Middle 
            (255, 200, 100),  # Inner
            (255, 255, 150)   # Core
        ]
        
        # Apply flickering to colors and dimensions
        flame_layers = []
        for i, base_color in enumerate(base_colors):
            layer_flicker = 1.0 + (flicker_1 if i == 0 else flicker_2 if i == 1 else flicker_3) * 0.5
            layer_intensity = flame_intensity * layer_flicker
            
            # Scale layer properties with flickering
            layer_length_scale = 1.0 - i * 0.2  # Each layer shorter
            layer_width_scale = 1.0 - i * 0.2   # Each layer narrower
            
            flame_layers.append({
                'length': flame_length * layer_length_scale * layer_intensity,
                'width': 0.8 * layer_width_scale * layer_intensity,
                'color': tuple(max(0, min(255, int(c * min(layer_intensity, 1.2)))) for c in base_color)
            })
        
        for layer in flame_layers:
            self._render_soft_flame_layer(screen, back_x, back_y, cos_angle, sin_angle, perpendicular_x, perpendicular_y, layer)

    def _render_soft_flame_layer(self, screen: pg.Surface, base_x: float, base_y: float,
                                cos_angle: float, sin_angle: float, perpendicular_x: float, perpendicular_y: float, layer: dict):
        """Render a soft flame layer with particles and proper shape."""
        import random
        
        flame_length = layer['length']
        max_width = layer['width'] * (self.width / 4)  # Further reduced max width
        
        # Create smooth flame shape using ordered points
        flame_segments = 6  # Reduced for smoother shape
        left_points = []
        right_points = []
        
        # Start with narrow base at missile
        base_width = max_width * 0.15  # Very narrow start
        
        # Create flame outline points
        for i in range(flame_segments + 1):
            # Progress along flame length (0 to 1)
            progress = i / flame_segments
            
            # Distance from missile base
            segment_x = base_x - cos_angle * flame_length * progress
            segment_y = base_y - sin_angle * flame_length * progress
            
            # Width expands smoothly, then tapers at the end
            if progress < 0.7:
                width_expansion = 0.15 + (progress * 1.2)  # Expand to 135%
            else:
                # Taper to point at the end
                taper_progress = (progress - 0.7) / 0.3
                width_expansion = 1.35 * (1.0 - taper_progress)
            
            segment_width = max_width * width_expansion
            
            # Add soft wave effect
            wave_1 = math.sin(self.flame_flicker_time * 6 + progress * 3) * 0.08
            wave_2 = math.sin(self.flame_flicker_time * 9 + progress * 5) * 0.05
            total_wave = (wave_1 + wave_2) * segment_width
            
            if i == flame_segments:  # Flame tip
                # Single point at the tip with slight offset
                tip_offset = math.sin(self.flame_flicker_time * 8) * (flame_length * 0.05)
                tip_x = segment_x - cos_angle * tip_offset
                tip_y = segment_y - sin_angle * tip_offset
                left_points.append((tip_x, tip_y))
            else:
                # Add points for both sides
                left_points.append((segment_x + perpendicular_x * (segment_width + total_wave), 
                                  segment_y + perpendicular_y * (segment_width + total_wave)))
                right_points.append((segment_x - perpendicular_x * (segment_width - total_wave * 0.7), 
                                   segment_y - perpendicular_y * (segment_width - total_wave * 0.7)))
        
        # Combine points in proper order for polygon
        flame_points = left_points + list(reversed(right_points))
        
        # Draw the main flame shape with transparency
        if len(flame_points) >= 3:
            # Create flame surface for soft rendering
            flame_surface = pg.Surface((flame_length * 2 + 40, max_width * 3 + 40), pg.SRCALPHA)
            
            # Offset points to flame surface coordinates
            surface_center_x = flame_length + 20
            surface_center_y = max_width * 1.5 + 20
            offset_points = []
            for px, py in flame_points:
                offset_x = surface_center_x + (px - base_x)
                offset_y = surface_center_y + (py - base_y)
                offset_points.append((offset_x, offset_y))
            
            # Draw flame with slight transparency
            flame_color = (*layer['color'][:3], int(layer['color'][0] * 0.8 if len(layer['color']) == 4 else 200))
            pg.draw.polygon(flame_surface, flame_color, offset_points)
            
            # Add soft glow around flame
            glow_points = []
            for px, py in offset_points:
                glow_points.append((px, py))
            
            # Slightly larger glow version
            if len(glow_points) >= 3:
                glow_color = (*layer['color'][:3], 40)
                for gx, gy in glow_points:
                    pg.draw.circle(flame_surface, glow_color, (int(gx), int(gy)), 3)
            
            # Blit flame surface to screen
            screen.blit(flame_surface, 
                       (int(base_x - surface_center_x), int(base_y - surface_center_y)), 
                       special_flags=pg.BLEND_ALPHA_SDL2)
        
        # Add flame particles
        self._add_flame_particles(screen, base_x, base_y, cos_angle, sin_angle, flame_length, layer['color'])
    
    def _add_flame_particles(self, screen: pg.Surface, base_x: float, base_y: float, 
                           cos_angle: float, sin_angle: float, flame_length: float, flame_color: tuple):
        """Add particle effects to the flame."""
        import random
        
        # Particle count based on flame intensity
        particle_count = random.randint(3, 8)
        
        for _ in range(particle_count):
            # Random position along flame length
            particle_progress = random.uniform(0.1, 0.9)
            particle_distance = flame_length * particle_progress
            
            # Base position along flame
            particle_x = base_x - cos_angle * particle_distance
            particle_y = base_y - sin_angle * particle_distance
            
            # Add random spread perpendicular to flame
            spread = random.uniform(-15, 15)
            particle_x += -sin_angle * spread * cos_angle
            particle_y += cos_angle * spread * sin_angle
            
            # Particle size varies with position (smaller towards tip)
            particle_size = int(random.uniform(1, 4) * (1.0 - particle_progress * 0.5))
            
            # Particle color - brighter variants of flame color
            base_r, base_g, base_b = flame_color[:3]
            particle_r = min(255, base_r + random.randint(-30, 50))
            particle_g = min(255, base_g + random.randint(-20, 30))  
            particle_b = max(0, base_b + random.randint(-10, 20))
            particle_alpha = random.randint(120, 200)
            
            # Draw particle with slight transparency
            particle_surface = pg.Surface((particle_size * 2, particle_size * 2), pg.SRCALPHA)
            pg.draw.circle(particle_surface, (particle_r, particle_g, particle_b, particle_alpha), 
                          (particle_size, particle_size), particle_size)
            
            screen.blit(particle_surface, 
                       (int(particle_x - particle_size), int(particle_y - particle_size)), 
                       special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _render_explosion(self, screen: pg.Surface, offset: Tuple[float, float]):
        """Render spectacular multi-layered explosion effect."""
        render_x = self.pos.x + offset[0]
        render_y = self.pos.y + offset[1]
        
        # Calculate explosion progress with different phases
        progress = self.explosion_age / self.explosion_duration
        
        # Phase 1: Initial flash (0-0.1)
        # Phase 2: Rapid expansion (0.1-0.4) 
        # Phase 3: Peak explosion (0.4-0.7)
        # Phase 4: Fade out (0.7-1.0)
        
        if progress < 0.1:
            # Initial bright flash
            self._render_explosion_flash(screen, render_x, render_y, progress)
        elif progress < 0.4:
            # Rapid expansion with shockwave
            self._render_explosion_expansion(screen, render_x, render_y, progress)
        elif progress < 0.7:
            # Peak explosion with debris
            self._render_explosion_peak(screen, render_x, render_y, progress)
        else:
            # Smoke and fade
            self._render_explosion_fade(screen, render_x, render_y, progress)
    
    def _render_explosion_flash(self, screen: pg.Surface, x: float, y: float, progress: float):
        """Render initial bright explosion flash with glow effects."""
        flash_progress = progress / 0.1
        
        # Create glow surface with transparency
        glow_surface = pg.Surface((self.explosion_max_radius * 2, self.explosion_max_radius * 2), pg.SRCALPHA)
        center_x = self.explosion_max_radius
        center_y = self.explosion_max_radius
        
        # Multiple glow layers for realistic effect
        flash_radius = int(self.explosion_max_radius * 0.5)
        
        # Outer glow (very transparent)
        outer_glow_radius = int(flash_radius * 2.0)
        outer_glow_color = (*[255, 255, 200], int(60 * (1.0 - flash_progress)))
        pg.draw.circle(glow_surface, outer_glow_color, (center_x, center_y), outer_glow_radius)
        
        # Middle glow
        mid_glow_radius = int(flash_radius * 1.4)
        mid_glow_color = (*[255, 255, 150], int(120 * (1.0 - flash_progress)))
        pg.draw.circle(glow_surface, mid_glow_color, (center_x, center_y), mid_glow_radius)
        
        # Inner bright flash
        inner_color = (*[255, 255, 255], int(200 * (1.0 - flash_progress)))
        pg.draw.circle(glow_surface, inner_color, (center_x, center_y), flash_radius)
        
        # Colored core
        core_radius = int(flash_radius * 0.6)
        core_color = (*[255, 255, 100], int(255 * (1.0 - flash_progress)))
        pg.draw.circle(glow_surface, core_color, (center_x, center_y), core_radius)
        
        # Blit glow surface to screen
        screen.blit(glow_surface, (int(x - self.explosion_max_radius), int(y - self.explosion_max_radius)), special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _render_explosion_expansion(self, screen: pg.Surface, x: float, y: float, progress: float):
        """Render rapid expansion phase with transparent glowing shockwave."""
        expansion_progress = (progress - 0.1) / 0.3  # 0.1 to 0.4 mapped to 0-1
        
        # Create explosion surface with transparency
        explosion_surface = pg.Surface((self.explosion_max_radius * 3, self.explosion_max_radius * 3), pg.SRCALPHA)
        center_x = self.explosion_max_radius * 1.5
        center_y = self.explosion_max_radius * 1.5
        
        # Main explosion ball
        explosion_radius = int(self.explosion_max_radius * expansion_progress)
        
        # Multiple explosion layers with transparency and glow
        explosion_layers = [
            {'radius_mult': 1.2, 'color': (255, 80, 0), 'alpha': int(140 * (1.0 - expansion_progress * 0.3))},     # Outer orange glow
            {'radius_mult': 1.0, 'color': (255, 120, 20), 'alpha': int(180 * (1.0 - expansion_progress * 0.2))},   # Outer orange
            {'radius_mult': 0.8, 'color': (255, 150, 50), 'alpha': int(200 * (1.0 - expansion_progress * 0.1))},   # Middle
            {'radius_mult': 0.6, 'color': (255, 200, 100), 'alpha': int(220)},  # Inner yellow
            {'radius_mult': 0.4, 'color': (255, 255, 150), 'alpha': int(240)},  # Core white-yellow
            {'radius_mult': 0.2, 'color': (255, 255, 255), 'alpha': int(255)}   # Bright core
        ]
        
        for layer in explosion_layers:
            layer_radius = int(explosion_radius * layer['radius_mult'])
            if layer_radius > 0:
                layer_color = (*layer['color'], layer['alpha'])
                pg.draw.circle(explosion_surface, layer_color, (int(center_x), int(center_y)), layer_radius)
        
        # Add particle effects around the explosion
        import random
        particle_count = int(20 * expansion_progress)
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(explosion_radius * 0.8, explosion_radius * 1.3)
            particle_x = center_x + math.cos(angle) * distance
            particle_y = center_y + math.sin(angle) * distance
            particle_size = random.randint(2, 6)
            particle_color = (*[255, random.randint(150, 255), random.randint(0, 100)], random.randint(120, 200))
            pg.draw.circle(explosion_surface, particle_color, (int(particle_x), int(particle_y)), particle_size)
        
        # Shockwave ring with transparency
        shockwave_radius = int(explosion_radius * 1.4)
        if shockwave_radius > 5:
            shockwave_alpha = int(100 * (1.0 - expansion_progress))
            shockwave_color = (*[255, 200, 150], shockwave_alpha)
            pg.draw.circle(explosion_surface, shockwave_color, (int(center_x), int(center_y)), shockwave_radius, 4)
        
        # Blit explosion surface to screen
        screen.blit(explosion_surface, (int(x - self.explosion_max_radius * 1.5), int(y - self.explosion_max_radius * 1.5)), special_flags=pg.BLEND_ALPHA_SDL2)
        
        # Shockwave ring
        if expansion_progress > 0.3:
            shockwave_radius = int(explosion_radius * 1.3)
            shockwave_thickness = max(2, int(5 * (1 - expansion_progress)))
            shockwave_alpha = int(100 * (1 - expansion_progress))
            shockwave_color = (255, 200, 100)
            
            # Draw shockwave ring
            pg.draw.circle(screen, shockwave_color, (int(x), int(y)), shockwave_radius, shockwave_thickness)
    
    def _render_explosion_peak(self, screen: pg.Surface, x: float, y: float, progress: float):
        """Render peak explosion with debris and particles."""
        peak_progress = (progress - 0.4) / 0.3  # 0.4 to 0.7 mapped to 0-1
        
        # Main explosion - now at full size but starting to fade
        explosion_radius = self.explosion_max_radius
        alpha_factor = 1.0 - peak_progress * 0.5  # Gradual fade
        
        # Multiple explosion layers with fading
        explosion_layers = [
            {'radius_mult': 1.0, 'color': (255, 80, 0), 'alpha': alpha_factor * 0.7},
            {'radius_mult': 0.8, 'color': (255, 120, 40), 'alpha': alpha_factor * 0.8},
            {'radius_mult': 0.6, 'color': (255, 160, 80), 'alpha': alpha_factor * 0.9},
            {'radius_mult': 0.4, 'color': (255, 200, 120), 'alpha': alpha_factor * 1.0},
            {'radius_mult': 0.2, 'color': (255, 240, 160), 'alpha': alpha_factor * 1.0}
        ]
        
        for layer in explosion_layers:
            layer_radius = int(explosion_radius * layer['radius_mult'])
            if layer_radius > 0:
                color = layer['color']
                pg.draw.circle(screen, color, (int(x), int(y)), layer_radius)
        
        # Add debris particles flying outward
        import random
        debris_count = 12
        for i in range(debris_count):
            angle = (i / debris_count) * 2 * math.pi
            debris_distance = explosion_radius * (0.8 + peak_progress * 0.4)
            debris_x = x + math.cos(angle) * debris_distance
            debris_y = y + math.sin(angle) * debris_distance
            
            debris_size = random.randint(2, 6)
            debris_color = (255, random.randint(100, 200), 0)
            pg.draw.circle(screen, debris_color, (int(debris_x), int(debris_y)), debris_size)
    
    def _render_explosion_fade(self, screen: pg.Surface, x: float, y: float, progress: float):
        """Render explosion fade with smoke."""
        fade_progress = (progress - 0.7) / 0.3  # 0.7 to 1.0 mapped to 0-1
        
        # Smoke clouds
        smoke_radius = int(self.explosion_max_radius * (1.1 + fade_progress * 0.3))
        smoke_alpha = int(150 * (1 - fade_progress))
        
        # Multiple smoke layers
        smoke_layers = [
            {'radius_mult': 1.0, 'color': (80, 80, 80)},   # Dark smoke outer
            {'radius_mult': 0.8, 'color': (100, 100, 100)}, # Medium smoke
            {'radius_mult': 0.6, 'color': (120, 120, 120)}, # Light smoke
        ]
        
        for layer in smoke_layers:
            layer_radius = int(smoke_radius * layer['radius_mult'])
            if layer_radius > 0 and smoke_alpha > 0:
                # Draw smoke with transparency effect
                smoke_color = layer['color']
                pg.draw.circle(screen, smoke_color, (int(x), int(y)), layer_radius)
        
        # Remaining embers
        if fade_progress < 0.7:
            import random
            ember_count = 8
            for i in range(ember_count):
                angle = random.random() * 2 * math.pi
                ember_distance = smoke_radius * random.uniform(0.3, 0.8)
                ember_x = x + math.cos(angle) * ember_distance
                ember_y = y + math.sin(angle) * ember_distance
                
                ember_size = random.randint(1, 3)
                ember_color = (255, random.randint(150, 255), random.randint(0, 100))
                pg.draw.circle(screen, ember_color, (int(ember_x), int(ember_y)), ember_size)
    
    def get_explosion_damage_area(self) -> Tuple[pg.Vector2, float]:
        """Get the position and radius for explosion damage calculation."""
        if self.state == MissileState.EXPLODING:
            return self.pos, self.explosion_radius
        return self.pos, 0
    
    def is_exploding(self) -> bool:
        """Check if missile is currently exploding."""
        return self.state == MissileState.EXPLODING
    
    def get_rect(self) -> pg.Rect:
        """Get collision rectangle for the missile."""
        return pg.Rect(self.pos.x - self.length/2, self.pos.y - self.width/2,
                      self.length, self.width)

class MissileManager:
    """Manages all active missiles in the game."""
    
    def __init__(self):
        """Initialize the missile manager."""
        self.missiles = []
    
    def fire_missile(self, start_x: float, start_y: float, target_x: float, target_y: float,
                    damage: int = 120, explosion_radius: float = 150):
        """Fire a new missile."""
        missile = Missile(start_x, start_y, target_x, target_y, damage, explosion_radius)
        self.missiles.append(missile)
        return missile
    
    def update(self, dt: float, enemies: list = None):
        """Update all missiles and remove finished ones."""
        missiles_to_remove = []
        
        for missile in self.missiles:
            if missile.update(dt, enemies):
                missiles_to_remove.append(missile)
        
        for missile in missiles_to_remove:
            self.missiles.remove(missile)
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render all missiles."""
        for missile in self.missiles:
            missile.render(screen, offset)
    
    def check_visual_damage(self, enemies) -> list:
        """Check for visual-based damage from all active missiles.
        Returns list of damage events for enemies hit by visual effects."""
        all_damage_events = []
        
        for missile in self.missiles:
            damage_events = missile.check_visual_damage(enemies)
            all_damage_events.extend(damage_events)
        
        return all_damage_events
    
    def get_exploding_missiles(self) -> list:
        """Get all currently exploding missiles for damage calculation."""
        return [missile for missile in self.missiles if missile.is_exploding()]
    
    def clear(self):
        """Clear all missiles."""
        self.missiles.clear()
    
    def get_missile_count(self) -> int:
        """Get the number of active missiles."""
        return len(self.missiles)
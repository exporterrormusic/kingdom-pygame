"""
Missile system for rocket launcher weapons.
Handles missile projectiles with targeting, explosions, visual effects, and ground fire.
"""

import pygame as pg
import math
from typing import Tuple, Optional, List
from enum import Enum

class MissileState(Enum):
    """States for missile lifecycle."""
    FLYING = "flying"
    EXPLODING = "exploding"
    FINISHED = "finished"

class GroundFire:
    """Persistent ground fire that damages enemies after missile explosions."""
    
    def __init__(self, x: float, y: float, radius: float, damage: float, duration: float = 5.0):
        """Initialize ground fire area.
        
        Args:
            x, y: Center position of fire area
            radius: Damage radius
            damage: Damage per second to enemies in the area
            duration: How long the fire persists (seconds)
        """
        self.pos = pg.Vector2(x, y)
        self.radius = radius
        self.damage_per_second = damage
        self.duration = duration
        self.age = 0.0
        self.damaged_enemies = set()  # Track recently damaged enemies
        self.damage_cooldown = 0.5  # Seconds between damage ticks per enemy
        self.last_damage_times = {}  # Track last damage time per enemy
        
        # Visual properties for fire animation
        self.flame_flicker_time = 0.0
        self.particle_positions = []
        self._initialize_fire_particles()
    
    def _initialize_fire_particles(self):
        """Initialize fire particle positions for visual effects."""
        import random
        base_particle_count = int(self.radius / 4)  # More particles for visibility
        
        # Create multiple layers of fire particles for depth
        self.fire_layers = {
            'base_flames': [],      # Large base fire layer
            'dancing_flames': [],   # Medium dancing flames  
            'sparks': [],          # Small spark particles
            'smoke': []            # Smoke particles
        }
        
        # Base flame layer - large stationary flames
        for _ in range(base_particle_count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.radius * 0.9)
            x = self.pos.x + math.cos(angle) * distance
            y = self.pos.y + math.sin(angle) * distance
            self.fire_layers['base_flames'].append({
                'x': x, 'y': y,
                'base_x': x, 'base_y': y,
                'size': random.uniform(8, 16),
                'intensity': random.uniform(0.8, 1.2),
                'flicker_speed': random.uniform(6, 10),
                'color_variant': random.uniform(0.8, 1.2)
            })
        
        # Dancing flame layer - moving flames
        for _ in range(base_particle_count // 2):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.radius * 0.7)
            x = self.pos.x + math.cos(angle) * distance
            y = self.pos.y + math.sin(angle) * distance
            self.fire_layers['dancing_flames'].append({
                'x': x, 'y': y,
                'base_x': x, 'base_y': y,
                'size': random.uniform(6, 12),
                'intensity': random.uniform(0.9, 1.4),
                'flicker_speed': random.uniform(12, 18),
                'dance_radius': random.uniform(8, 15),
                'dance_speed': random.uniform(2, 4),
                'color_variant': random.uniform(0.9, 1.1)
            })
        
        # Spark layer - small bright particles
        for _ in range(base_particle_count * 2):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.radius * 0.8)
            x = self.pos.x + math.cos(angle) * distance
            y = self.pos.y + math.sin(angle) * distance
            self.fire_layers['sparks'].append({
                'x': x, 'y': y,
                'base_x': x, 'base_y': y,
                'size': random.uniform(2, 5),
                'intensity': random.uniform(1.0, 1.5),
                'flicker_speed': random.uniform(15, 25),
                'pop_interval': random.uniform(0.5, 2.0),
                'last_pop': 0,
                'color_variant': random.uniform(1.0, 1.3)
            })
        
        # Smoke layer - darker particles for realism
        for _ in range(base_particle_count // 3):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(self.radius * 0.3, self.radius * 1.1)
            x = self.pos.x + math.cos(angle) * distance
            y = self.pos.y + math.sin(angle) * distance
            self.fire_layers['smoke'].append({
                'x': x, 'y': y,
                'base_x': x, 'base_y': y,
                'size': random.uniform(10, 20),
                'intensity': random.uniform(0.3, 0.7),
                'drift_speed': random.uniform(1, 3),
                'drift_direction': random.uniform(0, 2 * math.pi)
            })
    
    def update(self, dt: float) -> bool:
        """Update ground fire. Returns True if fire should be removed."""
        self.age += dt
        self.flame_flicker_time += dt
        
        # Update multi-layer fire particle animations
        import random
        
        # Update base flames - gentle flickering
        for particle in self.fire_layers['base_flames']:
            flicker = math.sin(self.flame_flicker_time * particle['flicker_speed']) * 2
            particle['x'] = particle['base_x'] + random.uniform(-1, 1) + flicker
            particle['y'] = particle['base_y'] + random.uniform(-1, 1) + flicker * 0.5
        
        # Update dancing flames - more movement
        for particle in self.fire_layers['dancing_flames']:
            dance_angle = self.flame_flicker_time * particle['dance_speed']
            dance_x = math.cos(dance_angle) * particle['dance_radius']
            dance_y = math.sin(dance_angle) * particle['dance_radius'] * 0.5
            flicker = math.sin(self.flame_flicker_time * particle['flicker_speed']) * 3
            
            particle['x'] = particle['base_x'] + dance_x + random.uniform(-2, 2) + flicker
            particle['y'] = particle['base_y'] + dance_y + random.uniform(-1, 1) + flicker * 0.3
        
        # Update sparks - rapid flickering with occasional pops
        for particle in self.fire_layers['sparks']:
            # Check for spark pop (bright flash)
            if self.flame_flicker_time - particle['last_pop'] > particle['pop_interval']:
                particle['last_pop'] = self.flame_flicker_time
                particle['pop_interval'] = random.uniform(0.5, 2.0)
                particle['intensity'] = random.uniform(1.5, 2.0)
            else:
                particle['intensity'] = max(0.8, particle['intensity'] - dt * 2)
            
            flicker = math.sin(self.flame_flicker_time * particle['flicker_speed']) * 4
            particle['x'] = particle['base_x'] + random.uniform(-3, 3) + flicker
            particle['y'] = particle['base_y'] + random.uniform(-2, 2) + flicker * 0.4
        
        # Update smoke - slow upward drift
        for particle in self.fire_layers['smoke']:
            drift_x = math.cos(particle['drift_direction']) * particle['drift_speed'] * dt
            drift_y = math.sin(particle['drift_direction']) * particle['drift_speed'] * dt - dt * 10  # Upward drift
            particle['x'] += drift_x
            particle['y'] += drift_y
        
        return self.age >= self.duration
    
    def check_enemy_damage(self, enemies, current_time: float) -> List[dict]:
        """Check for enemies in fire area and apply damage.
        Returns list of damage events."""
        damage_events = []
        
        for enemy in enemies:
            enemy_id = id(enemy)
            distance = (enemy.pos - self.pos).length()
            
            # Check if enemy is in fire area
            if distance <= self.radius + enemy.size / 2:
                # Check damage cooldown
                last_damage_time = self.last_damage_times.get(enemy_id, 0)
                if current_time - last_damage_time >= self.damage_cooldown:
                    damage = self.damage_per_second * self.damage_cooldown
                    damage_events.append({
                        'enemy': enemy,
                        'damage': damage,
                        'type': 'ground_fire'
                    })
                    self.last_damage_times[enemy_id] = current_time
        
        return damage_events
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render enhanced ground fire effects with multiple visual layers."""
        render_x = self.pos.x + offset[0]
        render_y = self.pos.y + offset[1]
        
        # Calculate fade factor as fire ages (less aggressive fade)
        fade_factor = 1.0 - (self.age / self.duration) * 0.4  # Fade to 60% by end
        
        # Render fire area background glow first
        self._render_fire_base_glow(screen, render_x, render_y, fade_factor)
        
        # Render smoke layer (behind flames)
        self._render_smoke_layer(screen, offset, fade_factor)
        
        # Render base flame layer (large background flames)
        self._render_base_flames(screen, offset, fade_factor)
        
        # Render dancing flame layer (medium animated flames)
        self._render_dancing_flames(screen, offset, fade_factor)
        
        # Render spark layer (bright small particles on top)
        self._render_spark_layer(screen, offset, fade_factor)
        
        # Render fire area danger indicator
        self._render_danger_indicator(screen, render_x, render_y, fade_factor)
    
    def _render_fire_base_glow(self, screen: pg.Surface, center_x: float, center_y: float, fade_factor: float):
        """Render base orange glow for the entire fire area."""
        glow_radius = int(self.radius * 1.2)
        glow_alpha = max(0, min(255, int(40 * fade_factor)))
        
        # Create glow surface
        glow_surf = pg.Surface((glow_radius * 2, glow_radius * 2), pg.SRCALPHA)
        glow_center = (glow_radius, glow_radius)
        
        # Multiple glow layers for depth
        pg.draw.circle(glow_surf, (255, 80, 0, glow_alpha), glow_center, glow_radius)
        pg.draw.circle(glow_surf, (255, 120, 20, max(0, min(255, int(glow_alpha * 1.2)))), glow_center, int(glow_radius * 0.8))
        pg.draw.circle(glow_surf, (255, 150, 50, max(0, min(255, int(glow_alpha * 1.4)))), glow_center, int(glow_radius * 0.6))
        
        screen.blit(glow_surf, (int(center_x - glow_radius), int(center_y - glow_radius)),
                   special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _render_smoke_layer(self, screen: pg.Surface, offset: Tuple[float, float], fade_factor: float):
        """Render smoke particles for atmospheric effect."""
        for particle in self.fire_layers['smoke']:
            particle_x = particle['x'] + offset[0]
            particle_y = particle['y'] + offset[1]
            
            size = int(particle['size'] * particle['intensity'] * fade_factor)
            if size > 0:
                # Smoke colors (dark gray to light gray)
                gray_value = max(0, min(255, int(80 + 40 * particle['intensity'])))
                smoke_color = (gray_value, gray_value, gray_value)
                alpha = max(0, min(255, int(120 * particle['intensity'] * fade_factor)))
                
                # Draw smoke particle with transparency
                smoke_surf = pg.Surface((size * 2, size * 2), pg.SRCALPHA)
                pg.draw.circle(smoke_surf, (*smoke_color, alpha), (size, size), size)
                screen.blit(smoke_surf, (int(particle_x - size), int(particle_y - size)),
                           special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _render_base_flames(self, screen: pg.Surface, offset: Tuple[float, float], fade_factor: float):
        """Render large base flame particles."""
        for particle in self.fire_layers['base_flames']:
            particle_x = particle['x'] + offset[0]
            particle_y = particle['y'] + offset[1]
            
            size = int(particle['size'] * particle['intensity'] * fade_factor)
            if size > 0:
                # Base flame colors (red-orange) - ensure valid values
                red = max(0, min(255, int(255 * fade_factor * particle['color_variant'])))
                green = max(0, min(255, int(120 * fade_factor * particle['color_variant'])))
                blue = 0
                
                # Draw main flame particle
                flame_color = (red, green, blue)
                pg.draw.circle(screen, flame_color, (int(particle_x), int(particle_y)), size)
                
                # Add bright glow around flame
                if size > 3:
                    glow_size = size + 3
                    glow_alpha = max(0, min(255, int(80 * fade_factor * particle['intensity'])))
                    glow_surf = pg.Surface((glow_size * 2, glow_size * 2), pg.SRCALPHA)
                    glow_color = (red, green, blue, glow_alpha)
                    pg.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                    screen.blit(glow_surf, (int(particle_x - glow_size), int(particle_y - glow_size)),
                               special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _render_dancing_flames(self, screen: pg.Surface, offset: Tuple[float, float], fade_factor: float):
        """Render medium animated flame particles."""
        for particle in self.fire_layers['dancing_flames']:
            particle_x = particle['x'] + offset[0]
            particle_y = particle['y'] + offset[1]
            
            size = int(particle['size'] * particle['intensity'] * fade_factor)
            if size > 0:
                # Dancing flame colors (orange-yellow) - ensure valid values
                red = max(0, min(255, int(255 * fade_factor)))
                green = max(0, min(255, int(160 * fade_factor * particle['color_variant'])))
                blue = max(0, min(255, int(20 * fade_factor * particle['color_variant'])))
                
                # Draw dancing flame with flicker effect
                flame_color = (red, green, blue)
                pg.draw.circle(screen, flame_color, (int(particle_x), int(particle_y)), size)
                
                # Add animated glow
                if size > 2:
                    glow_size = size + 2
                    glow_alpha = max(0, min(255, int(100 * fade_factor * particle['intensity'])))
                    glow_surf = pg.Surface((glow_size * 2, glow_size * 2), pg.SRCALPHA)
                    glow_color = (red, green, blue, glow_alpha)
                    pg.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                    screen.blit(glow_surf, (int(particle_x - glow_size), int(particle_y - glow_size)),
                               special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _render_spark_layer(self, screen: pg.Surface, offset: Tuple[float, float], fade_factor: float):
        """Render bright spark particles on top."""
        for particle in self.fire_layers['sparks']:
            particle_x = particle['x'] + offset[0]
            particle_y = particle['y'] + offset[1]
            
            size = int(particle['size'] * particle['intensity'] * fade_factor)
            if size > 0:
                # Bright spark colors (yellow-white) - ensure valid color values
                intensity_boost = particle['intensity'] * particle['color_variant']
                red = max(0, min(255, int(255 * fade_factor * intensity_boost)))
                green = max(0, min(255, int(200 * fade_factor * intensity_boost)))
                blue = max(0, min(255, int(100 * fade_factor * intensity_boost)))
                
                # Draw bright spark
                spark_color = (red, green, blue)
                pg.draw.circle(screen, spark_color, (int(particle_x), int(particle_y)), size)
                
                # Add intense glow for sparks
                if size > 1:
                    glow_size = size + 1
                    glow_alpha = max(0, min(255, int(150 * fade_factor * particle['intensity'])))
                    glow_surf = pg.Surface((glow_size * 2, glow_size * 2), pg.SRCALPHA)
                    glow_color = (red, green, blue, glow_alpha)
                    pg.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                    screen.blit(glow_surf, (int(particle_x - glow_size), int(particle_y - glow_size)),
                               special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _render_danger_indicator(self, screen: pg.Surface, center_x: float, center_y: float, fade_factor: float):
        """Render subtle danger zone indicator."""
        # Pulsing red circle at the edge of damage area
        pulse = 0.8 + 0.2 * math.sin(self.flame_flicker_time * 4)
        indicator_alpha = max(0, min(255, int(60 * fade_factor * pulse)))
        
        if indicator_alpha > 10:
            pg.draw.circle(screen, (255, 0, 0), (int(center_x), int(center_y)), int(self.radius), 2)

class MissileState(Enum):
    """States for missile lifecycle."""
    FLYING = "flying"
    EXPLODING = "exploding"
    FINISHED = "finished"

class Missile:
    """Individual missile projectile with targeting and explosion capabilities."""
    
    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float, 
                 damage: int = 120, explosion_radius: float = 150, speed: float = 800, special_attack: bool = False, audio_manager=None, is_grenade: bool = False):
        """Initialize a missile.
        
        Args:
            start_x, start_y: Starting position
            target_x, target_y: Target position to fly toward
            damage: Explosion damage
            explosion_radius: AOE explosion radius
            speed: Missile flight speed (doubled for more impact)
            special_attack: Whether this is a special attack missile
            audio_manager: Audio manager for playing rocket sounds
            is_grenade: Whether this is a grenade (affects audio behavior)
        """
        self.pos = pg.Vector2(start_x, start_y)
        self.target = pg.Vector2(target_x, target_y)
        self.damage = damage
        self.explosion_radius = explosion_radius
        self.speed = speed
        self.state = MissileState.FLYING
        self.special_attack = special_attack
        self.audio_manager = audio_manager
        self.is_grenade = is_grenade
        
        # Start rocket flight sound only for rockets (not grenades)
        self.flight_sound_playing = False
        self.flight_sound_channel = None
        if self.audio_manager and not self.is_grenade:
            # Start rocket flight sound in loop only for rockets
            self.flight_sound_channel = self.audio_manager.play_rocket_flight_sound()
            if self.flight_sound_channel:
                self.flight_sound_playing = True
        
        # Calculate flight direction
        direction = self.target - self.pos
        distance = direction.length()
        if distance > 0:
            self.velocity = direction.normalize() * speed
        else:
            self.velocity = pg.Vector2(0, 0)
        
        # Visual properties - enhanced for special attacks
        if special_attack:
            self.length = 80  # Bigger special missile
            self.width = 24   # Wider special missile
        else:
            self.length = 60  # Standard missile size
            self.width = 18   # Standard width
        
        self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        
        # Trail effect - optimized length for performance
        self.trail_positions = []
        if getattr(self, 'is_grenade', False):
            self.max_trail_length = 0  # No trail for grenades
        else:
            self.max_trail_length = 10 if special_attack else 8  # Reduced from 15/12 for performance
        
        # Animation properties for flickering flame - more intense for special
        self.flame_flicker_time = 0.0
        self.flame_intensity_base = 1.2 if special_attack else 1.0
        self.flame_intensity_variance = 0.4 if special_attack else 0.3
        
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
        
        # Update trail (but skip for grenades)
        if not getattr(self, 'is_grenade', False):
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
        
        # Stop flight sound if it was playing
        if self.audio_manager and self.flight_sound_playing and self.flight_sound_channel:
            self.audio_manager.stop_rocket_flight_sound(self.flight_sound_channel)
            self.flight_sound_playing = False
            self.flight_sound_channel = None
        
        # Always play explosion sound for both missiles and grenades
        if self.audio_manager:
            self.audio_manager.play_rocket_explosion_sound()
        
        # Create ground fire for special attacks
        if self.special_attack and hasattr(self, 'ground_fire_callback') and self.ground_fire_callback:
            # Create larger ground fire area for special attacks
            fire_radius = self.explosion_radius * 0.8  # Ground fire slightly smaller than explosion
            fire_damage = 15  # Damage per second
            fire_duration = 5.0  # 5 seconds of ground fire
            self.ground_fire_callback(self.pos.x, self.pos.y, fire_radius, fire_damage, fire_duration)
        
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
        """Render missile or grenade projectile."""
        render_x = self.pos.x + offset[0]
        render_y = self.pos.y + offset[1]
        
        # Grenades render as simple bullets (no trails, no rocket shape)
        if getattr(self, 'is_grenade', False):
            self._render_grenade_bullet(screen, render_x, render_y)
        else:
            # Regular missile - impressive missile with spectacular effects
            # Enhanced exhaust trail with multiple layers
            self._render_spectacular_exhaust_trail(screen, offset)
            
            # Calculate missile orientation
            angle_rad = math.radians(self.angle)
            cos_angle = math.cos(angle_rad)
            sin_angle = math.sin(angle_rad)
            
            # Enhanced missile body - larger for more impact
            missile_length = self.length * 1.3  # Even bigger than original
            missile_width = self.width * 1.2    # Wider for presence
            
            # Missile tip (front)
            tip_x = render_x + cos_angle * (missile_length / 2)
            tip_y = render_y + sin_angle * (missile_length / 2)
            
            # Missile back
            back_x = render_x - cos_angle * (missile_length / 2)
            back_y = render_y - sin_angle * (missile_length / 2)
            
            # Side points for missile body
            perpendicular_x = -sin_angle * (missile_width / 2)
            perpendicular_y = cos_angle * (missile_width / 2)
            
            # Draw detailed missile body with segments
            self._render_spectacular_missile_body(screen, render_x, render_y, cos_angle, sin_angle, 
                                                missile_length, missile_width, perpendicular_x, perpendicular_y)

    def _render_grenade_bullet(self, screen: pg.Surface, render_x: float, render_y: float):
        """Render grenade with proper grenade appearance - not a bullet placeholder."""
        # Make it look like an actual grenade, not a bullet
        grenade_size = 12  # Bigger than bullets to look like a real grenade
        
        # Dark olive green grenade body (military grenade color)
        pg.draw.circle(screen, (80, 90, 60), (int(render_x), int(render_y)), grenade_size)
        
        # Darker military green outline
        pg.draw.circle(screen, (60, 70, 45), (int(render_x), int(render_y)), grenade_size, 2)
        
        # Metal pin/spoon highlight on top
        pin_offset_y = int(grenade_size * 0.6)
        pg.draw.circle(screen, (150, 150, 150), (int(render_x), int(render_y - pin_offset_y)), 3)
        
        # Segmented grenade pattern (cross-hatch lines)
        line_color = (50, 60, 35)
        # Horizontal line
        pg.draw.line(screen, line_color, 
                    (int(render_x - grenade_size * 0.7), int(render_y)), 
                    (int(render_x + grenade_size * 0.7), int(render_y)), 2)
        # Vertical line  
        pg.draw.line(screen, line_color,
                    (int(render_x), int(render_y - grenade_size * 0.7)),
                    (int(render_x), int(render_y + grenade_size * 0.7)), 2)
    
    def _render_spectacular_exhaust_trail(self, screen: pg.Surface, offset: Tuple[float, float]):
        """Render spectacular multi-layered exhaust trail."""
        # Performance optimization: reduce trail detail for distant positions
        trail_positions_to_render = self.trail_positions[::2] if len(self.trail_positions) > 8 else self.trail_positions
        
        for i, trail_pos in enumerate(trail_positions_to_render):
            alpha_factor = (i + 1) / len(trail_positions_to_render)
            trail_render_x = trail_pos.x + offset[0]
            trail_render_y = trail_pos.y + offset[1]
            
            # Enhanced trail with different colors for special attacks
            if self.special_attack:
                # Red-orange trail for special attack missiles (reduced layers for performance)
                trail_layers = [
                    {'size': 16, 'color': (255, 60, 0)},     # Large red outer
                    {'size': 9, 'color': (255, 140, 50)},   # Orange middle (skip one layer)
                    {'size': 4, 'color': (255, 220, 120)},  # Yellow-orange (skip one layer)
                    {'size': 2, 'color': (255, 255, 150)},  # White-yellow core
                ]
            else:
                # Standard trail colors (reduced layers for performance)
                trail_layers = [
                    {'size': 12, 'color': (255, 80, 0)},    # Large orange outer
                    {'size': 6, 'color': (255, 180, 50)},   # Yellow-orange (skip middle layer)
                    {'size': 3, 'color': (255, 220, 100)},  # Bright yellow (smaller)
                    {'size': 2, 'color': (255, 255, 150)},  # White-yellow core
                ]
            
            for layer in trail_layers:
                adjusted_size = max(1, int(layer['size'] * alpha_factor))
                adjusted_color = (
                    int(layer['color'][0] * alpha_factor),
                    int(layer['color'][1] * alpha_factor),
                    int(layer['color'][2] * alpha_factor)
                )
                pg.draw.circle(screen, adjusted_color, (int(trail_render_x), int(trail_render_y)), adjusted_size)
                
                # Add enhanced glow effect for special attacks
                if adjusted_size > 2:
                    glow_size = adjusted_size + (3 if self.special_attack else 2)
                    glow_alpha = max(20, int((80 if self.special_attack else 60) * alpha_factor))
                    glow_color = (*layer['color'][:3], glow_alpha)
                    # Create glow surface for transparency
                    glow_surf = pg.Surface((glow_size*2, glow_size*2), pg.SRCALPHA)
                    pg.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                    screen.blit(glow_surf, (int(trail_render_x - glow_size), int(trail_render_y - glow_size)), 
                              special_flags=pg.BLEND_ALPHA_SDL2)

    def _render_spectacular_missile_body(self, screen: pg.Surface, render_x: float, render_y: float,
                                       cos_angle: float, sin_angle: float, missile_length: float, 
                                       missile_width: float, perpendicular_x: float, perpendicular_y: float):
        """Render spectacular detailed missile body with multiple segments and effects."""
        # Enhanced body segments with metallic appearance (red-tinted for special attacks)
        segments = 4
        segment_length = missile_length / segments
        
        for i in range(segments):
            segment_start = (i - segments/2 + 0.5) * segment_length
            segment_end = segment_start + segment_length * 0.9
            
            # Segment colors - gradient from dark to bright metallic
            color_intensity = 0.5 + 0.5 * (i / (segments - 1))
            
            if self.special_attack:
                # Special attack missiles have red-tinted metallic appearance
                segment_color = (
                    int(180 + 60 * color_intensity),  # More red
                    int(120 + 30 * color_intensity),  # Less green
                    int(120 + 30 * color_intensity)   # Less blue
                )
            else:
                # Standard metallic appearance
                segment_color = (
                    int(160 + 40 * color_intensity),
                    int(160 + 40 * color_intensity), 
                    int(180 + 40 * color_intensity)
                )
            
            # Segment positions
            seg_front_x = render_x + cos_angle * segment_end
            seg_front_y = render_y + sin_angle * segment_end
            seg_back_x = render_x + cos_angle * segment_start  
            seg_back_y = render_y + sin_angle * segment_start
            
            # Draw main segment
            segment_points = [
                (seg_front_x + perpendicular_x, seg_front_y + perpendicular_y),
                (seg_front_x - perpendicular_x, seg_front_y - perpendicular_y),
                (seg_back_x - perpendicular_x, seg_back_y - perpendicular_y),
                (seg_back_x + perpendicular_x, seg_back_y + perpendicular_y)
            ]
            pg.draw.polygon(screen, segment_color, segment_points)
            
            # Add metallic highlights
            highlight_color = (min(255, segment_color[0] + 60), 
                             min(255, segment_color[1] + 60), 
                             min(255, segment_color[2] + 60))
            highlight_width = max(1, int(missile_width * 0.2))
            highlight_points = [
                (seg_front_x + perpendicular_x * 0.7, seg_front_y + perpendicular_y * 0.7),
                (seg_front_x + perpendicular_x * 0.3, seg_front_y + perpendicular_y * 0.3),
                (seg_back_x + perpendicular_x * 0.3, seg_back_y + perpendicular_y * 0.3),
                (seg_back_x + perpendicular_x * 0.7, seg_back_y + perpendicular_y * 0.7)
            ]
            if len(highlight_points) >= 3:
                pg.draw.polygon(screen, highlight_color, highlight_points)
        
        # Enhanced warhead tip with glow (brighter red for special attacks)
        tip_x = render_x + cos_angle * (missile_length / 2)
        tip_y = render_y + sin_angle * (missile_length / 2)
        tip_back_x = render_x + cos_angle * (missile_length / 2 - 12)
        tip_back_y = render_y + sin_angle * (missile_length / 2 - 12)
        
        # Warhead with glow effect
        tip_points = [
            (tip_x, tip_y),
            (tip_back_x + perpendicular_x, tip_back_y + perpendicular_y),
            (tip_back_x - perpendicular_x, tip_back_y - perpendicular_y)
        ]
        
        # Outer glow for warhead
        glow_surf = pg.Surface((int(missile_width*2), int(missile_width*2)), pg.SRCALPHA)
        glow_center = (int(missile_width), int(missile_width))
        
        if self.special_attack:
            # Red glow for special attack
            pg.draw.circle(glow_surf, (255, 100, 100, 100), glow_center, int(missile_width))
        else:
            # Standard golden glow
            pg.draw.circle(glow_surf, (255, 200, 100, 80), glow_center, int(missile_width))
        
        screen.blit(glow_surf, (int(tip_x - missile_width), int(tip_y - missile_width)), 
                   special_flags=pg.BLEND_ALPHA_SDL2)
        
        # Main warhead
        if self.special_attack:
            warhead_color = (255, 180, 120)  # Red-orange warhead
        else:
            warhead_color = (255, 220, 120)  # Standard golden warhead
        
        pg.draw.polygon(screen, warhead_color, tip_points)
        
        # Inner warhead highlight
        inner_tip_points = [
            (tip_x, tip_y),
            (tip_back_x + perpendicular_x * 0.6, tip_back_y + perpendicular_y * 0.6),
            (tip_back_x - perpendicular_x * 0.6, tip_back_y - perpendicular_y * 0.6)
        ]
        
        if self.special_attack:
            highlight_color = (255, 255, 180)  # Bright red-white highlight
        else:
            highlight_color = (255, 255, 200)  # Standard bright highlight
        
        pg.draw.polygon(screen, highlight_color, inner_tip_points)
        
        # Enhanced stabilizer fins with glow (more fins for special attacks)
        fin_length = missile_width * 1.5
        fin_back_x = render_x - cos_angle * (missile_length / 2 - 8)
        fin_back_y = render_y - sin_angle * (missile_length / 2 - 8)
        
        # More fins for special attack missiles
        fin_angles = [0.8, -0.8, 2.1, -2.1, 0, 3.14] if self.special_attack else [0.8, -0.8, 2.1, -2.1]
        
        for fin_angle in fin_angles:
            fin_perp_x = -sin_angle * math.cos(fin_angle) * fin_length - cos_angle * math.sin(fin_angle) * fin_length
            fin_perp_y = cos_angle * math.cos(fin_angle) * fin_length - sin_angle * math.sin(fin_angle) * fin_length
            
            # Main fin
            fin_points = [
                (fin_back_x, fin_back_y),
                (fin_back_x + fin_perp_x, fin_back_y + fin_perp_y),
                (fin_back_x - cos_angle * 12 + fin_perp_x * 0.7, fin_back_y - sin_angle * 12 + fin_perp_y * 0.7)
            ]
            
            if self.special_attack:
                fin_color = (200, 100, 100)  # Red-tinted fins
            else:
                fin_color = (180, 120, 120)  # Standard fins
                
            pg.draw.polygon(screen, fin_color, fin_points)
            
            # Fin highlight
            fin_highlight_points = [
                (fin_back_x, fin_back_y),
                (fin_back_x + fin_perp_x * 0.8, fin_back_y + fin_perp_y * 0.8),
                (fin_back_x - cos_angle * 8 + fin_perp_x * 0.6, fin_back_y - sin_angle * 8 + fin_perp_y * 0.6)
            ]
            
            if self.special_attack:
                highlight_color = (240, 120, 120)  # Brighter red highlight
            else:
                highlight_color = (220, 150, 150)  # Standard highlight
                
            pg.draw.polygon(screen, highlight_color, fin_highlight_points)

    def _render_simple_flame(self, screen: pg.Surface, back_x: float, back_y: float,
                           cos_angle: float, sin_angle: float, perpendicular_x: float, perpendicular_y: float):
        """Render simple exhaust flame."""
        flame_length = 20  # Reasonable flame size
        
        # Simple flickering intensity
        flicker = math.sin(self.flame_flicker_time * 8) * 0.2
        flame_intensity = 1.0 + flicker
        flame_intensity = max(0.8, min(1.2, flame_intensity))
        
        # Simple flame shape
        current_flame_length = flame_length * flame_intensity
        flame_width = self.width / 3 * flame_intensity
        
        # Flame points
        flame_tip_x = back_x - cos_angle * current_flame_length
        flame_tip_y = back_y - sin_angle * current_flame_length
        
        flame_left_x = back_x + perpendicular_x * flame_width
        flame_left_y = back_y + perpendicular_y * flame_width
        
        flame_right_x = back_x - perpendicular_x * flame_width
        flame_right_y = back_y - perpendicular_y * flame_width
        
        # Draw flame as triangle
        flame_points = [
            (flame_tip_x, flame_tip_y),
            (flame_left_x, flame_left_y),
            (flame_right_x, flame_right_y)
        ]
        
        # Outer flame (orange)
        pg.draw.polygon(screen, (255, 100, 0), flame_points)
        
        # Inner flame (yellow) - smaller
        inner_flame_length = current_flame_length * 0.7
        inner_flame_width = flame_width * 0.6
        
        inner_tip_x = back_x - cos_angle * inner_flame_length
        inner_tip_y = back_y - sin_angle * inner_flame_length
        
        inner_left_x = back_x + perpendicular_x * inner_flame_width
        inner_left_y = back_y + perpendicular_y * inner_flame_width
        
        inner_right_x = back_x - perpendicular_x * inner_flame_width
        inner_right_y = back_y - perpendicular_y * inner_flame_width
        
        inner_points = [
            (inner_tip_x, inner_tip_y),
            (inner_left_x, inner_left_y),
            (inner_right_x, inner_right_y)
        ]
        
        pg.draw.polygon(screen, (255, 200, 50), inner_points)

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
        
        # Particle count based on flame intensity (reduced for performance)
        particle_count = random.randint(2, 5)  # Reduced from 3-8
        
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
    """Manages all active missiles and ground fire effects in the game."""
    
    def __init__(self, audio_manager=None):
        """Initialize the missile manager."""
        self.missiles = []
        self.ground_fires = []
        self.audio_manager = audio_manager
    
    def fire_missile(self, start_x: float, start_y: float, target_x: float, target_y: float,
                    damage: int = 120, explosion_radius: float = 150, special_attack: bool = False):
        """Fire a new missile."""
        missile = Missile(start_x, start_y, target_x, target_y, damage, explosion_radius, special_attack=special_attack, audio_manager=self.audio_manager)
        
        # Set ground fire callback for special attacks
        if special_attack:
            missile.ground_fire_callback = self._create_ground_fire
        
        self.missiles.append(missile)
        return missile

    def fire_grenade(self, start_x: float, start_y: float, target_x: float, target_y: float,
                    damage: int = 45, explosion_radius: float = 150, speed: float = 600):
        """Fire a grenade using missile system but with grenade appearance."""
        missile = Missile(start_x, start_y, target_x, target_y, damage, explosion_radius, speed, 
                         audio_manager=self.audio_manager, is_grenade=True)
        
        # Disable trail for grenades - they should be simple bullets
        missile.max_trail_length = 0
        missile.trail_positions = []
        
        self.missiles.append(missile)
        return missile
    
    def _create_ground_fire(self, x: float, y: float, radius: float, damage: float, duration: float):
        """Create a new ground fire area."""
        ground_fire = GroundFire(x, y, radius, damage, duration)
        self.ground_fires.append(ground_fire)
    
    def update(self, dt: float, enemies: list = None):
        """Update all missiles and ground fires, remove finished ones."""
        # Update missiles
        missiles_to_remove = []
        for missile in self.missiles:
            if missile.update(dt, enemies):
                missiles_to_remove.append(missile)
        
        # Clean up audio for removed missiles
        for missile in missiles_to_remove:
            if missile.flight_sound_playing and missile.flight_sound_channel:
                if missile.audio_manager:
                    missile.audio_manager.stop_rocket_flight_sound(missile.flight_sound_channel)
            self.missiles.remove(missile)
        
        # Update ground fires
        fires_to_remove = []
        for ground_fire in self.ground_fires:
            if ground_fire.update(dt):
                fires_to_remove.append(ground_fire)
        
        for fire in fires_to_remove:
            self.ground_fires.remove(fire)
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render all missiles and ground fires."""
        # Render ground fires first (behind missiles)
        for ground_fire in self.ground_fires:
            ground_fire.render(screen, offset)
        
        # Render missiles on top
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
    
    def check_ground_fire_damage(self, enemies, current_time: float) -> list:
        """Check for ground fire damage to enemies.
        Returns list of damage events for enemies in fire areas."""
        all_damage_events = []
        
        for ground_fire in self.ground_fires:
            damage_events = ground_fire.check_enemy_damage(enemies, current_time)
            all_damage_events.extend(damage_events)
        
        return all_damage_events
    
    def get_exploding_missiles(self) -> list:
        """Get all currently exploding missiles for damage calculation."""
        return [missile for missile in self.missiles if missile.is_exploding()]
    
    def clear(self):
        """Clear all missiles and ground fires."""
        self.missiles.clear()
        self.ground_fires.clear()
    
    def get_missile_count(self) -> int:
        """Get the number of active missiles."""
        return len(self.missiles)
    
    def get_ground_fire_count(self) -> int:
        """Get the number of active ground fires."""
        return len(self.ground_fires)
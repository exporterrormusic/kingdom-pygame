"""
Collision detection system for the twin-stick shooter game.
Handles all collision detection and response between game objects.
"""

import pygame as pg
import math
from typing import List, Tuple
from src.player import Player
from src.bullet import Bullet, BulletManager
from src.enemy import Enemy, EnemyManager

class CollisionManager:
    """Handles all collision detection in the game."""
    
    def __init__(self):
        """Initialize the collision manager."""
        pass
    
    def check_bullet_enemy_collisions(self, bullet_manager: BulletManager, 
                                    enemy_manager: EnemyManager, player=None, effects_manager=None) -> int:
        """
        Check collisions between bullets and enemies.
        Returns the number of enemies killed this frame.
        """
        kills = 0
        bullets_to_remove = []
        enemies_to_remove = []
        enemy_death_positions = []  # Store positions for explosion effects
        
        for bullet in bullet_manager.get_bullets():
            # Skip enemy bullets - they shouldn't hit enemies (friendly fire)
            from src.bullet import BulletType
            if bullet.type == BulletType.ENEMY_LASER:
                continue  # Enemy bullets don't hurt enemies
                
            bullet_rect = bullet.get_rect()
            
            for enemy in enemy_manager.get_enemies():
                enemy_rect = enemy.get_rect()
                
                if bullet_rect.colliderect(enemy_rect):
                    # Check if actually colliding using distance (more accurate for circles)
                    distance = (bullet.pos - enemy.pos).length()
                    
                    # Calculate effective bullet collision size based on shape
                    effective_bullet_size = bullet.size
                    if hasattr(bullet, 'shape') and bullet.shape == "laser":
                        # Laser bullets (sniper) have much larger visual beam width
                        # Match the visual beam_width = max(size * 4, 24)
                        effective_bullet_size = max(bullet.size * 4, 24) / 2  # Divide by 2 since we're using radius
                    
                    if distance <= effective_bullet_size + enemy.size:
                        # Collision detected
                        enemy.take_damage(bullet.damage)
                        
                        # Add BURST charge to player when hitting enemy
                        if player and hasattr(player, 'add_burst_charge'):
                            player.add_burst_charge()
                        
                        # Handle bullet penetration
                        if hasattr(bullet, 'hits_remaining'):
                            bullet.hits_remaining -= 1
                            # Only remove bullet if it has no penetration left
                            if bullet.hits_remaining <= 0 and bullet not in bullets_to_remove:
                                bullets_to_remove.append(bullet)
                                
                                # Add pellet impact effect for shotgun energy balls
                                if effects_manager and hasattr(bullet, 'shape') and bullet.shape == "pellet":
                                    effects_manager.add_pellet_impact_effect(bullet.pos.x, bullet.pos.y)
                                # Add tracer impact effect for assault rifle rounds
                                elif effects_manager and hasattr(bullet, 'shape') and bullet.shape == "tracer":
                                    effects_manager.add_tracer_impact_effect(bullet.pos.x, bullet.pos.y)
                                # Add neon impact effect for SMG cyberpunk rounds
                                elif effects_manager and hasattr(bullet, 'shape') and bullet.shape == "neon":
                                    effects_manager.add_neon_impact_effect(bullet.pos.x, bullet.pos.y)
                                # Add sword impact effect for magical blade slashes
                                elif effects_manager and hasattr(bullet, 'shape') and bullet.shape == "slash":
                                    effects_manager.add_sword_impact_effect(bullet.pos.x, bullet.pos.y)
                        else:
                            # Default behavior for bullets without penetration system
                            if bullet not in bullets_to_remove:
                                bullets_to_remove.append(bullet)
                                
                                # Add pellet impact effect for shotgun energy balls
                                if effects_manager and hasattr(bullet, 'shape') and bullet.shape == "pellet":
                                    effects_manager.add_pellet_impact_effect(bullet.pos.x, bullet.pos.y)
                                # Add tracer impact effect for assault rifle rounds
                                elif effects_manager and hasattr(bullet, 'shape') and bullet.shape == "tracer":
                                    effects_manager.add_tracer_impact_effect(bullet.pos.x, bullet.pos.y)
                                # Add neon impact effect for SMG cyberpunk rounds
                                elif effects_manager and hasattr(bullet, 'shape') and bullet.shape == "neon":
                                    effects_manager.add_neon_impact_effect(bullet.pos.x, bullet.pos.y)
                                # Add sword impact effect for magical blade slashes
                                elif effects_manager and hasattr(bullet, 'shape') and bullet.shape == "slash":
                                    effects_manager.add_sword_impact_effect(bullet.pos.x, bullet.pos.y)
                        
                        if not enemy.is_alive() and enemy not in enemies_to_remove:
                            enemies_to_remove.append(enemy)
                            enemy_death_positions.append((enemy.pos.x, enemy.pos.y))  # Store position for explosion
                            kills += 1
        
        # Remove bullets and enemies that collided
        for bullet in bullets_to_remove:
            bullet_manager.remove_bullet(bullet)
        
        # Create explosion effects for dead enemies before removing them
        if effects_manager:
            for pos_x, pos_y in enemy_death_positions:
                effects_manager.add_explosion(pos_x, pos_y)
        
        for enemy in enemies_to_remove:
            enemy_manager.remove_enemy(enemy)
        
        return kills
    
    def check_player_enemy_collisions(self, player: Player, 
                                    enemy_manager: EnemyManager) -> bool:
        """
        Check collisions between player and enemies.
        Returns True if player took damage.
        """
        player_rect = player.get_rect()
        player_took_damage = False
        
        for enemy in enemy_manager.get_enemies():
            enemy_rect = enemy.get_rect()
            
            if player_rect.colliderect(enemy_rect):
                # Check if actually colliding using distance
                distance = (player.pos - enemy.pos).length()
                if distance <= player.size + enemy.size:
                    # Collision detected - player takes damage
                    player.take_damage(enemy.damage)
                    player_took_damage = True
                    
                    # Push player away from enemy (gentle push)
                    push_direction = (player.pos - enemy.pos)
                    if push_direction.length() > 0:
                        push_direction = push_direction.normalize()
                        push_force = 25  # Much smaller push - was 100
                        new_pos = player.pos + push_direction * push_force
                        
                        # Keep player on screen (use current resolution)
                        screen_width = 1920  # Current game resolution
                        screen_height = 1080
                        new_pos.x = max(player.size, min(screen_width - player.size, new_pos.x))
                        new_pos.y = max(player.size, min(screen_height - player.size, new_pos.y))
                        player.pos = new_pos
        
        return player_took_damage
    
    def check_enemy_bullet_player_collisions(self, bullet_manager: BulletManager, player: Player) -> bool:
        """
        Check collisions between enemy bullets and player.
        Returns True if player took damage.
        """
        from src.bullet import BulletType
        bullets_to_remove = []
        player_took_damage = False
        
        for bullet in bullet_manager.get_bullets():
            # Only check enemy bullets
            if bullet.type != BulletType.ENEMY_LASER:
                continue
            
            # Check shield collision first if shield is active
            if hasattr(player, 'shield_active') and player.shield_active:
                if self.check_bullet_shield_collision(bullet, player):
                    bullets_to_remove.append(bullet)
                    continue  # Shield blocked the bullet, skip player collision
                
            # Check collision with player
            distance = (bullet.pos - player.pos).length()
            if distance <= bullet.size + player.size:
                # Player takes damage from enemy bullet
                player.take_damage(bullet.damage)
                player_took_damage = True
                bullets_to_remove.append(bullet)
        
        # Remove bullets that hit the player or shield
        for bullet in bullets_to_remove:
            bullet_manager.remove_bullet(bullet)
            
        return player_took_damage
    
    def check_bullet_shield_collision(self, bullet, player) -> bool:
        """Check if a bullet collides with the player's curved shield."""
        if not hasattr(player, 'shield_active') or not player.shield_active:
            return False
        
        # Use circular collision detection for more accurate curved shield collision
        # Calculate distance from bullet to shield center
        distance_to_shield = (bullet.pos - player.shield_pos).length()
        
        # Shield collision radius accounts for curve and height
        shield_collision_radius = max(player.shield_height // 2, player.shield_curve_radius + player.shield_width)
        
        # Check if bullet is within shield collision area
        if distance_to_shield <= (shield_collision_radius + bullet.size):
            # Additional check: make sure bullet is in front of player (not behind shield)
            # Calculate vector from player to bullet
            player_to_bullet = bullet.pos - player.pos
            player_facing = pg.Vector2(math.cos(math.radians(player.angle)), 
                                     math.sin(math.radians(player.angle)))
            
            # Dot product tells us if bullet is in the forward direction
            dot_product = player_to_bullet.dot(player_facing)
            
            # Only block if bullet is coming from the front (positive dot product)
            return dot_product > 0
            
        return False
    
    def get_shield_collision_rect(self, player) -> pg.Rect:
        """Get the collision rectangle for the player's shield."""
        # Create a larger rectangle representing the curved shield area
        # The shield is now taller and farther from the player
        shield_half_width = player.shield_width + player.shield_curve_radius
        shield_half_height = player.shield_height // 2
        
        return pg.Rect(
            player.shield_pos.x - shield_half_width,
            player.shield_pos.y - shield_half_height,
            (shield_half_width * 2),
            player.shield_height
        )
    
    def check_point_in_circle(self, point: pg.Vector2, center: pg.Vector2, 
                            radius: float) -> bool:
        """Check if a point is inside a circle."""
        return (point - center).length() <= radius
    
    def check_circle_collision(self, pos1: pg.Vector2, radius1: float,
                             pos2: pg.Vector2, radius2: float) -> bool:
        """Check collision between two circles."""
        return (pos1 - pos2).length() <= (radius1 + radius2)
    
    def get_collision_response(self, obj1_pos: pg.Vector2, obj1_size: float,
                             obj2_pos: pg.Vector2, obj2_size: float) -> Tuple[pg.Vector2, pg.Vector2]:
        """
        Calculate collision response vectors for two circular objects.
        Returns (response_for_obj1, response_for_obj2).
        """
        # Calculate collision normal
        collision_vector = obj2_pos - obj1_pos
        distance = collision_vector.length()
        
        if distance == 0:
            # Objects are exactly on top of each other
            collision_vector = pg.Vector2(1, 0)
            distance = 1
        
        collision_normal = collision_vector / distance
        
        # Calculate overlap
        overlap = (obj1_size + obj2_size) - distance
        
        if overlap > 0:
            # Separate objects
            separation = collision_normal * (overlap / 2)
            response1 = -separation  # Move obj1 away
            response2 = separation    # Move obj2 away
            
            return response1, response2
        
        return pg.Vector2(0, 0), pg.Vector2(0, 0)

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
        
        import random
        import math
        
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
        
        import random
        import math
        
        # Different explosion types have different behaviors
        if explosion_type == "core":
            self.lifetime = 0.6  # Reduced from 0.8
            gravity_factor = 0.95
        elif explosion_type == "fire":
            self.lifetime = 1.0  # Reduced from 1.2
            gravity_factor = 0.92
        elif explosion_type == "smoke":
            self.lifetime = 1.2  # Reduced from 2.0
            gravity_factor = 0.88
        elif explosion_type == "sparks":
            self.lifetime = 0.4  # Reduced from 0.6
            gravity_factor = 0.98
        elif explosion_type == "muzzle_flash":
            self.lifetime = 0.3
            gravity_factor = 1.0  # No gravity for muzzle flash
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
            gravity_factor = 1.0  # No gravity for muzzle flash
        elif explosion_type == "anime_flash":
            self.lifetime = 0.2
            gravity_factor = 1.0  # No gravity
        elif explosion_type == "tactical_smoke":
            self.lifetime = 0.8
            gravity_factor = 0.90
        elif explosion_type == "tactical_sparks":
            self.lifetime = 0.35
            gravity_factor = 0.95
        elif explosion_type == "impact_flash":
            self.lifetime = 0.15
            gravity_factor = 1.0  # No gravity for flash
        elif explosion_type == "tactical_debris":
            self.lifetime = 0.6
            gravity_factor = 0.85
        elif explosion_type == "neon_burst":
            self.lifetime = 0.15  # Very short duration
            gravity_factor = 1.0  # No gravity for cyberpunk effects
        elif explosion_type == "digital_fragments":
            self.lifetime = 0.12  # Even shorter duration
            gravity_factor = 1.0  # No gravity
        elif explosion_type == "holographic_glow":
            self.lifetime = 0.1  # Shortest duration
            gravity_factor = 1.0  # No gravity
        elif explosion_type == "anime_energy_burst":
            self.lifetime = 0.2  # Quick energy burst
            gravity_factor = 1.0  # No gravity
        elif explosion_type == "skid_mark":
            self.lifetime = 1.0  # Longer lasting skid marks
            gravity_factor = 0.8  # Slight settling effect
        else:
            self.lifetime = 0.8  # Reduced from 1.0
            gravity_factor = 0.95
        
        for _ in range(particle_count):
            # Calculate angle based on direction_angle and spread_angle
            if direction_angle is not None:
                # Directional explosion (like muzzle flash)
                spread_rad = math.radians(spread_angle)
                angle = math.radians(direction_angle) + random.uniform(-spread_rad/2, spread_rad/2)
            else:
                # Omnidirectional explosion
                angle = random.uniform(0, 2 * math.pi)
                
            speed_variation = random.uniform(0.3, 1.8)
            
            # Create different particle behaviors based on type
            if explosion_type == "sparks":
                # Sparks fly further and faster
                velocity_magnitude = speed * speed_variation
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.2, 0.8)
            elif explosion_type == "smoke":
                # Smoke moves slower and gets bigger over time
                velocity_magnitude = speed * speed_variation * 0.6
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.8, 1.4)  # Reduced from 1.5-2.5
            elif explosion_type == "muzzle_flash":
                # Muzzle flash particles are fast and bright
                velocity_magnitude = speed * speed_variation
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.1, 0.3)
            elif explosion_type == "energy_wisps":
                # Energy wisps are smaller and faster
                velocity_magnitude = speed * speed_variation * 1.2
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.3, 0.8)
            elif explosion_type == "pellet_core":
                # Pellet core impact - small intense burst
                velocity_magnitude = speed * speed_variation * 1.1
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.2, 0.4)
            elif explosion_type == "pellet_sparks":
                # Pellet sparks - fast small particles
                velocity_magnitude = speed * speed_variation * 1.3
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.1, 0.3)
            elif explosion_type == "energy_residue":
                # Energy residue - slower drifting particles
                velocity_magnitude = speed * speed_variation * 0.8
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.3, 0.6)
            elif explosion_type == "tactical_flash":
                # Tactical muzzle flash - sharp, fast particles
                velocity_magnitude = speed * speed_variation * 1.2
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.1, 0.25)
            elif explosion_type == "anime_flash":
                # Anime-style intense flash - very fast and bright
                velocity_magnitude = speed * speed_variation * 1.4
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.08, 0.2)
            elif explosion_type == "tactical_smoke":
                # Tactical smoke - moderate speed, longer lasting
                velocity_magnitude = speed * speed_variation * 0.9
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.4, 0.8)
            elif explosion_type == "tactical_sparks":
                # Tactical sparks - precise, fast particles
                velocity_magnitude = speed * speed_variation * 1.3
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.2, 0.35)
            elif explosion_type == "impact_flash":
                # Impact flash - very fast, brief particles
                velocity_magnitude = speed * speed_variation * 1.5
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.08, 0.15)
            elif explosion_type == "tactical_debris":
                # Tactical debris - moderate speed with gravity
                velocity_magnitude = speed * speed_variation * 1.0
                size = random.randint(size_range[0], size_range[1])
                life_duration = random.uniform(0.3, 0.6)
            elif explosion_type == "neon_burst":
                # Cyberpunk neon burst - bright, fast, small particles
                velocity_magnitude = speed * speed_variation * 1.5
                size = random.randint(1, 3)  # Smaller particles
                life_duration = random.uniform(0.08, 0.15)
            elif explosion_type == "digital_fragments":
                # Digital fragments - medium speed, tiny particles
                velocity_magnitude = speed * speed_variation * 1.2
                size = random.randint(1, 2)  # Very small particles
                life_duration = random.uniform(0.06, 0.12)
            elif explosion_type == "holographic_glow":
                # Holographic afterglow - slow, small, fading particles
                velocity_magnitude = speed * speed_variation * 0.8
                size = random.randint(2, 4)  # Small glowing particles
                life_duration = random.uniform(0.05, 0.1)
            elif explosion_type == "anime_energy_burst":
                # Anime energy burst - bright, fast expanding particles
                velocity_magnitude = speed * speed_variation * 1.3
                size = random.randint(2, 4)  # Medium bright particles
                life_duration = random.uniform(0.1, 0.2)
            elif explosion_type == "skid_mark":
                # Skid mark particles - slow, settling dust/debris
                velocity_magnitude = speed * speed_variation * 0.5
                size = random.randint(2, 5)  # Larger dust particles
                life_duration = random.uniform(0.8, 1.0)
            else:
                # Fire and core particles
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
        
        import random
        
        for particle in self.particles:
            particle['pos'] += particle['velocity'] * dt
            particle['life'] -= dt
            
            # Apply different physics based on explosion type
            if self.explosion_type == "smoke":
                # Smoke expands and slows down
                particle['velocity'] *= 0.85
                particle['size'] = min(particle['initial_size'] * 2, 
                                     particle['initial_size'] + (self.age * 8))
            elif self.explosion_type == "sparks":
                # Sparks maintain speed but fade quickly
                particle['velocity'] *= 0.99
                # Add slight random movement for flickering effect
                particle['velocity'].x += random.uniform(-10, 10)
                particle['velocity'].y += random.uniform(-10, 10)
            else:
                # Fire and core particles slow down gradually
                particle['velocity'] *= particle['gravity_factor']
            
            if particle['life'] <= 0:
                particles_to_remove.append(particle)
        
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        return len(self.particles) == 0
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render enhanced explosion particles."""
        import random
        
        for particle in self.particles:
            life_ratio = particle['life'] / particle['initial_life']
            render_x = int(particle['pos'].x + offset[0])
            render_y = int(particle['pos'].y + offset[1])
            
            # Calculate dynamic color based on explosion type and life
            base_r, base_g, base_b = particle['base_color']
            
            if self.explosion_type == "core":
                # Core fades from white to yellow to red
                if life_ratio > 0.7:
                    color = (255, 255, 255)  # Bright white
                elif life_ratio > 0.3:
                    color = (255, 255, 100)  # Bright yellow
                else:
                    color = (255, 150, 0)    # Orange
            elif self.explosion_type == "fire":
                # Fire cycles through fire colors
                if life_ratio > 0.6:
                    color = (255, 200, 0)    # Bright orange
                elif life_ratio > 0.3:
                    color = (255, 100, 0)    # Orange
                else:
                    color = (150, 50, 0)     # Dark red
            elif self.explosion_type == "smoke":
                # Smoke gets lighter and more transparent (avoid dark spots)
                if life_ratio > 0.3:
                    gray_value = int(120 * life_ratio)  # Lighter smoke
                    color = (gray_value, gray_value//2, gray_value//3)
                else:
                    # Fade to invisible instead of getting darker
                    fade_factor = life_ratio / 0.3  # 0-1 range for final fade
                    gray_value = int(60 * fade_factor)  # Much lighter
                    color = (gray_value, gray_value//2, gray_value//4)
            elif self.explosion_type == "sparks":
                # Sparks flicker between bright yellow and white
                if random.random() > 0.3:
                    color = (255, 255, 200)
                else:
                    color = (255, 255, 255)
            else:
                color = particle['base_color']
            
            # Apply life-based alpha with faster fade-out
            if self.explosion_type == "smoke" and life_ratio < 0.3:
                # Smoke fades out completely in final 30% of life
                alpha_factor = life_ratio / 0.3
            else:
                alpha_factor = max(0.05, life_ratio)  # Reduced minimum from 0.1
            
            final_color = tuple(int(c * alpha_factor) for c in color)
            
            # Draw particle with glow effect for fire/core
            if self.explosion_type in ["core", "fire", "sparks"]:
                # Draw outer glow
                glow_size = particle['size'] + 2
                glow_color = tuple(int(c * 0.3) for c in final_color)
                if glow_size > 0:
                    pg.draw.circle(screen, glow_color, (render_x, render_y), glow_size)
            
            # Draw main particle
            if particle['size'] > 0:
                pg.draw.circle(screen, final_color, (render_x, render_y), int(particle['size']))


class EffectsManager:
    """Manages particle effects and visual feedback."""
    
    def __init__(self):
        """Initialize the effects manager."""
        self.effects = []
        self.dash_lines = []  # Comic book style dash lines
        
        # Anime environmental effects
        self.environmental_effects = []
        self.cherry_blossoms = []
        self.spirit_wisps = []
    
    def add_explosion(self, x: float, y: float, color: Tuple[int, int, int] = (255, 100, 0)):
        """Add an enhanced fiery explosion effect."""
        # Create multiple explosion layers for more impressive effect
        
        # Core explosion - bright white/yellow center
        core_effect = EnhancedExplosionEffect(x, y, 
                                            color=(255, 255, 255), 
                                            particle_count=15, 
                                            speed=200,
                                            size_range=(4, 8),
                                            explosion_type="core")
        self.effects.append(core_effect)
        
        # Fire layer - orange/red flames
        fire_effect = EnhancedExplosionEffect(x, y, 
                                            color=(255, 150, 0), 
                                            particle_count=25, 
                                            speed=150,
                                            size_range=(6, 12),
                                            explosion_type="fire")
        self.effects.append(fire_effect)
        
        # Smoke layer - lighter particles that fade cleanly
        smoke_effect = EnhancedExplosionEffect(x, y, 
                                             color=(100, 60, 40), 
                                             particle_count=15,  # Reduced from 20
                                             speed=80,
                                             size_range=(6, 12),  # Smaller smoke particles
                                             explosion_type="smoke")
        self.effects.append(smoke_effect)
        
        # Sparks - small fast bright particles
        spark_effect = EnhancedExplosionEffect(x, y, 
                                             color=(255, 255, 100), 
                                             particle_count=30, 
                                             speed=300,
                                             size_range=(1, 3),
                                             explosion_type="sparks")
        self.effects.append(spark_effect)
    
    def add_hit_effect(self, x: float, y: float, color: Tuple[int, int, int] = (255, 255, 0)):
        """Add a hit effect."""
        effect = ParticleEffect(x, y, color, particle_count=6, speed=80)
        self.effects.append(effect)
    
    def add_shotgun_muzzle_flash(self, x: float, y: float, angle: float):
        """Add a balanced anime-style fire muzzle flash for shotgun firing."""
        import math
        
        # Convert angle to radians
        angle_rad = math.radians(angle)
        
        # Scaled-down fire burst - fewer layers for balance
        for i in range(3):  # Reduced from 5 layers
            spread = 25 * (i + 1)  # Smaller spread
            fire_colors = [
                (255, 80, 0),    # Deep red-orange
                (255, 120, 0),   # Orange  
                (255, 180, 20),  # Yellow-orange
            ]
            flash_effect = EnhancedExplosionEffect(
                x, y,
                color=fire_colors[i],
                particle_count=15 + (i * 4),  # Fewer particles
                speed=120 + (i * 40),  # Moderate speed
                size_range=(2, 6 + i),  # Smaller particles
                explosion_type="muzzle_flash",
                direction_angle=angle,
                spread_angle=spread
            )
            self.effects.append(flash_effect)
        
        # Reduced fire sparks
        for i in range(2):  # Reduced from 3
            spark_angle = angle + (i - 0.5) * 10  # Smaller spread
            spark_effect = EnhancedExplosionEffect(
                x, y,
                color=(255, 200, 0) if i % 2 == 0 else (255, 255, 200),
                particle_count=8,  # Fewer sparks
                speed=150,  # Moderate speed
                size_range=(1, 4),  # Smaller sparks
                explosion_type="energy_wisps",
                direction_angle=spark_angle,
                spread_angle=20
            )
            self.effects.append(spark_effect)
        
        # Moderate fire plume
        plume_effect = EnhancedExplosionEffect(
            x, y,
            color=(255, 100, 0),  # Deep fire red
            particle_count=20,  # Reduced particles
            speed=100,  # Moderate speed
            size_range=(3, 8),  # Smaller particles
            explosion_type="muzzle_flash",
            direction_angle=angle,
            spread_angle=40  # Smaller spread
        )
        self.effects.append(plume_effect)
    
    def add_pellet_impact_effect(self, x: float, y: float):
        """Add a balanced anime-style fire explosion when shotgun pellets hit enemies."""
        # Scaled-down fiery explosion core
        fire_core = EnhancedExplosionEffect(
            x, y,
            color=(255, 80, 0),  # Deep fire red
            particle_count=12,  # Fewer particles
            speed=120,  # Moderate explosion speed
            size_range=(2, 5),  # Smaller particles
            explosion_type="pellet_core"
        )
        self.effects.append(fire_core)
        
        # Moderate fire burst
        fire_burst = EnhancedExplosionEffect(
            x, y,
            color=(255, 150, 0),  # Bright orange
            particle_count=10,  # Fewer particles
            speed=150,  # Moderate speed
            size_range=(2, 4),  # Smaller particles
            explosion_type="pellet_sparks"
        )
        self.effects.append(fire_burst)
        
        # Balanced fire sparks
        spark_burst = EnhancedExplosionEffect(
            x, y,
            color=(255, 220, 50),  # Golden yellow sparks
            particle_count=15,  # Moderate sparks
            speed=180,  # Good speed
            size_range=(1, 2),  # Small sparks
            explosion_type="pellet_sparks"
        )
        self.effects.append(spark_burst)
        
        # Residual energy wisps
        residue_effect = EnhancedExplosionEffect(
            x, y,
            color=(255, 180, 100),  # Orange-yellow residue
            particle_count=6,
            speed=60,
            size_range=(1, 3),
            explosion_type="energy_residue"
        )
        self.effects.append(residue_effect)
    
    def add_assault_rifle_muzzle_flash(self, x: float, y: float, angle: float):
        """Add anime-style tactical muzzle flash for assault rifle."""
        import math
        
        # Convert angle to radians  
        angle_rad = math.radians(angle)
        
        # Main tactical flash - sharp, angular burst
        tactical_flash = EnhancedExplosionEffect(
            x, y,
            color=(255, 220, 100),  # Bright tactical yellow-orange
            particle_count=12,
            speed=150,
            size_range=(3, 6),
            explosion_type="tactical_flash",
            direction_angle=angle,
            spread_angle=25  # Narrow, focused burst
        )
        self.effects.append(tactical_flash)
        
        # Secondary flash burst - anime-style intensity
        intense_flash = EnhancedExplosionEffect(
            x, y,
            color=(255, 255, 200),  # Near-white intensity
            particle_count=8,
            speed=200,
            size_range=(2, 4),
            explosion_type="anime_flash",
            direction_angle=angle,
            spread_angle=20
        )
        self.effects.append(intense_flash)
        
        # Tactical smoke wisps - brief professional residue
        smoke_wisps = EnhancedExplosionEffect(
            x, y,
            color=(150, 120, 80),  # Military smoke color
            particle_count=6,
            speed=70,
            size_range=(2, 4),
            explosion_type="tactical_smoke",
            direction_angle=angle,
            spread_angle=30
        )
        self.effects.append(smoke_wisps)
    
    def add_tracer_impact_effect(self, x: float, y: float):
        """Add anime military-style impact effect for tracer rounds."""
        # Tactical spark shower - anime-style precision sparks
        spark_shower = EnhancedExplosionEffect(
            x, y,
            color=(255, 220, 100),  # Bright military sparks
            particle_count=12,
            speed=180,
            size_range=(1, 3),
            explosion_type="tactical_sparks"
        )
        self.effects.append(spark_shower)
        
        # Impact flash - brief intense brightness
        impact_flash = EnhancedExplosionEffect(
            x, y,
            color=(255, 255, 200),  # Near-white flash
            particle_count=6,
            speed=120,
            size_range=(2, 4),
            explosion_type="impact_flash"
        )
        self.effects.append(impact_flash)
        
        # Tactical debris - professional military impact
        debris_effect = EnhancedExplosionEffect(
            x, y,
            color=(180, 140, 100),  # Debris color
            particle_count=8,
            speed=100,
            size_range=(1, 2),
            explosion_type="tactical_debris"
        )
        self.effects.append(debris_effect)
    
    def add_smg_muzzle_flash(self, x: float, y: float, angle: float):
        """Add cyberpunk neon muzzle flash for SMG."""
        import math
        
        # Calculate directional offset for muzzle
        angle_rad = math.radians(angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Primary neon burst - bright cyan core
        neon_burst = EnhancedExplosionEffect(
            x, y,
            color=(0, 255, 255),  # Bright cyan
            particle_count=8,  # Reduced from 15
            speed=250,
            size_range=(2, 5),
            explosion_type="neon_burst",
            direction_angle=angle,
            spread_angle=25
        )
        self.effects.append(neon_burst)
        
        # Digital particles - holographic fragments
        digital_fragments = EnhancedExplosionEffect(
            x, y,
            color=(100, 255, 255),  # Lighter cyan
            particle_count=6,  # Reduced from 10
            speed=180,
            size_range=(1, 3),
            explosion_type="digital_fragments",
            direction_angle=angle,
            spread_angle=35
        )
        self.effects.append(digital_fragments)
        
        # Holographic afterglow - lingering neon effect
        afterglow = EnhancedExplosionEffect(
            x, y,
            color=(0, 200, 255),  # Deep cyber blue
            particle_count=4,  # Reduced from 8
            speed=120,
            size_range=(3, 6),
            explosion_type="holographic_glow",
            direction_angle=angle,
            spread_angle=15
        )
        self.effects.append(afterglow)
        
        # Data stream wisps - digital exhaust
        data_wisps = EnhancedExplosionEffect(
            x, y,
            color=(50, 255, 200),  # Aqua data stream
            particle_count=12,
            speed=90,
            size_range=(1, 2),
            explosion_type="data_stream",
            direction_angle=angle + 180,  # Opposite direction
            spread_angle=40
        )
        self.effects.append(data_wisps)
    
    def add_neon_impact_effect(self, x: float, y: float):
        """Add cyberpunk digital impact effect for neon bullets."""
        # Data corruption explosion - digital breakdown
        data_corruption = EnhancedExplosionEffect(
            x, y,
            color=(0, 255, 255),  # Bright cyan
            particle_count=18,
            speed=200,
            size_range=(2, 4),
            explosion_type="data_corruption"
        )
        self.effects.append(data_corruption)
        
        # Holographic shatter - digital fragmentation
        holo_shatter = EnhancedExplosionEffect(
            x, y,
            color=(150, 255, 255),  # Light cyan
            particle_count=12,
            speed=160,
            size_range=(1, 3),
            explosion_type="holographic_shatter"
        )
        self.effects.append(holo_shatter)
        
        # Digital static burst - interference effect
        static_burst = EnhancedExplosionEffect(
            x, y,
            color=(0, 200, 255),  # Deep cyber blue
            particle_count=25,
            speed=250,
            size_range=(1, 2),
            explosion_type="digital_static"
        )
        self.effects.append(static_burst)
        
        # System error fragments - corrupted data particles
        error_fragments = EnhancedExplosionEffect(
            x, y,
            color=(255, 100, 255),  # Pink error color
            particle_count=8,
            speed=100,
            size_range=(2, 3),
            explosion_type="system_error"
        )
        self.effects.append(error_fragments)
    
    def add_sword_activation_flash(self, x: float, y: float, angle: float):
        """Add magical sword activation effect for blade attacks."""
        import math
        
        # Calculate directional offset for sword activation
        angle_rad = math.radians(angle)
        
        # Primary magical burst - mystical energy explosion
        magical_burst = EnhancedExplosionEffect(
            x, y,
            color=(200, 200, 255),  # Mystical blue-white
            particle_count=20,
            speed=300,
            size_range=(3, 8),
            explosion_type="magical_burst",
            direction_angle=angle,
            spread_angle=45
        )
        self.effects.append(magical_burst)
        
        # Blade sparkles - magical energy fragments
        blade_sparkles = EnhancedExplosionEffect(
            x, y,
            color=(255, 255, 255),  # Pure white sparkles
            particle_count=15,
            speed=200,
            size_range=(2, 5),
            explosion_type="blade_sparkles",
            direction_angle=angle,
            spread_angle=60
        )
        self.effects.append(blade_sparkles)
        
        # Mystical energy wave - expanding magical aura
        energy_wave = EnhancedExplosionEffect(
            x, y,
            color=(150, 180, 255),  # Soft magical blue
            particle_count=12,
            speed=150,
            size_range=(4, 10),
            explosion_type="mystical_wave",
            direction_angle=angle,
            spread_angle=30
        )
        self.effects.append(energy_wave)
        
        # Magical essence wisps - floating mystical particles
        essence_wisps = EnhancedExplosionEffect(
            x, y,
            color=(180, 200, 255),  # Light mystical essence
            particle_count=18,
            speed=80,
            size_range=(2, 4),
            explosion_type="mystical_essence",
            direction_angle=angle + 90,  # Perpendicular to slash
            spread_angle=120
        )
        self.effects.append(essence_wisps)
    
    def add_sword_impact_effect(self, x: float, y: float):
        """Add magical sword impact effect for blade hits."""
        # Magical energy explosion - mystical blade impact
        magical_explosion = EnhancedExplosionEffect(
            x, y,
            color=(200, 200, 255),  # Mystical blue-white
            particle_count=25,
            speed=250,
            size_range=(3, 6),
            explosion_type="magical_explosion"
        )
        self.effects.append(magical_explosion)
        
        # Blade sparks shower - magical energy fragments
        spark_shower = EnhancedExplosionEffect(
            x, y,
            color=(255, 255, 255),  # Bright white sparks
            particle_count=18,
            speed=220,
            size_range=(2, 4),
            explosion_type="blade_sparks"
        )
        self.effects.append(spark_shower)
        
        # Mystical shatter - magical energy breakdown
        mystical_shatter = EnhancedExplosionEffect(
            x, y,
            color=(180, 220, 255),  # Light mystical blue
            particle_count=30,
            speed=180,
            size_range=(1, 3),
            explosion_type="mystical_shatter"
        )
        self.effects.append(mystical_shatter)
        
        # Magical essence burst - concentrated mystical energy
        essence_burst = EnhancedExplosionEffect(
            x, y,
            color=(220, 200, 255),  # Purple-tinted mystical
            particle_count=12,
            speed=120,
            size_range=(4, 7),
            explosion_type="mystical_burst"
        )
        self.effects.append(essence_burst)
    
    def update(self, dt: float, player_pos: pg.Vector2 = None):
        """Update all effects."""
        effects_to_remove = []
        
        for effect in self.effects:
            if effect.update(dt):
                effects_to_remove.append(effect)
        
        for effect in effects_to_remove:
            self.effects.remove(effect)
        
        # Update dash lines with player position
        dash_lines_to_remove = []
        
        for dash_line in self.dash_lines:
            if player_pos is not None:
                if dash_line.update(dt, player_pos):
                    dash_lines_to_remove.append(dash_line)
            else:
                if dash_line.update(dt, pg.Vector2(0, 0)):  # Fallback
                    dash_lines_to_remove.append(dash_line)
        
        for dash_line in dash_lines_to_remove:
            self.dash_lines.remove(dash_line)
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render all effects."""
        # Render regular effects
        for effect in self.effects:
            effect.render(screen, offset)
        
        # Render dash lines on top for visibility
        for dash_line in self.dash_lines:
            dash_line.render(screen, offset)
    
    def add_dash_effect(self, x: float, y: float, direction: pg.Vector2):
        """Add an anime-style dash trail effect with speed lines and skid marks."""
        import math
        import random
        
        # Comic Book Style Dash Lines - the classic "whoosh" effect
        # Fix directional issues by ensuring we have a proper direction vector
        if direction.length() == 0:
            direction = pg.Vector2(1, 0)  # Default to right if no direction
        direction = direction.normalize()
        
        angle = math.atan2(direction.y, direction.x)
        dash_angle_degrees = math.degrees(angle)
        
        # Create multiple dash lines at different lengths and positions
        # All positions are relative to player (0, 0)
        
        # Main central dash lines - simple and clean
        # Create simple, character-height dash lines - positioned well behind the player
        character_height = 40  # Approximate character sprite height
        
        # Main central lines - positioned much further back to avoid sprite overlap
        for i in range(3):  # 3 main lines for better visibility
            line_length = int((character_height - (i * 6)) * 1.3)  # 30% longer: 52px, 44px, 36px
            start_distance = 55 + (i * 8)  # Much further back: 55, 63, 71 pixels behind player
            
            # Calculate RELATIVE positions (from player center)
            relative_start_x = -math.cos(angle) * start_distance
            relative_start_y = -math.sin(angle) * start_distance
            
            # Simple straight lines - no angle variation for better performance
            relative_end_x = relative_start_x - math.cos(angle) * line_length
            relative_end_y = relative_start_y - math.sin(angle) * line_length
            
            # More visible thickness and alpha
            thickness = 5 - i  # 5px, 4px, 3px
            alpha = 200 - (i * 30)  # 200, 170, 140 - much more visible
            
            dash_line = ComicDashLine(relative_start_x, relative_start_y, 
                                    relative_end_x, relative_end_y, thickness, (255, 255, 255, alpha))
            self.dash_lines.append(dash_line)
        
        # Add 2 side lines for width - also positioned much further back
        perpendicular_angle = angle + math.pi/2
        for side in [-1, 1]:  # One on each side
            line_length = int(25 * 1.3)  # 30% longer: 32px side lines
            start_distance = 50  # Much further back
            
            # Offset to the sides
            side_offset = 12 * side
            offset_x = math.cos(perpendicular_angle) * side_offset
            offset_y = math.sin(perpendicular_angle) * side_offset
            
            relative_start_x = -math.cos(angle) * start_distance + offset_x
            relative_start_y = -math.sin(angle) * start_distance + offset_y
            
            relative_end_x = relative_start_x - math.cos(angle) * line_length
            relative_end_y = relative_start_y - math.sin(angle) * line_length
            
            # Smaller side lines
            thickness = 3
            alpha = 150
            
            dash_line = ComicDashLine(relative_start_x, relative_start_y, 
                                    relative_end_x, relative_end_y, thickness, (255, 255, 255, alpha))
            self.dash_lines.append(dash_line)
        
        # Small energy puff for dash start
        energy_puff = EnhancedExplosionEffect(
            x, y,
            color=(200, 220, 255),  # Light blue energy
            particle_count=4,  # Small burst
            speed=120,
            size_range=(1, 2),
            explosion_type="anime_energy_burst",
            direction_angle=dash_angle_degrees + 180,
            spread_angle=20
        )
        self.effects.append(energy_puff)
    
    def clear(self):
        """Remove all effects."""
        self.effects.clear()
        self.dash_lines.clear()
        self.environmental_effects.clear()
        self.cherry_blossoms.clear()
        self.spirit_wisps.clear()


class AtmosphericEffects:
    """Manages random atmospheric effects for levels including rain, snow, and cherry blossoms."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize atmospheric effects system."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Current atmosphere state
        self.current_atmosphere = None  # "rain", "snow", "cherry_blossom", or None
        
        # Rain effect
        self.rain_drops = []
        self.rain_tint_alpha = 0
        self.vignette_alpha = 0
        
        # Snow effect  
        self.snow_flakes = []
        self.footprints = []
        
        # Cherry blossom effect
        self.cherry_petals = []
        
        # Timing
        self.effect_timer = 0.0
        
    def set_random_atmosphere(self):
        """Randomly select an atmospheric effect for the level with equal probability."""
        import random
        # Use random.randint for perfectly equal distribution
        random_num = random.randint(1, 3)  # 1, 2, or 3 with equal probability
        
        if random_num == 1:
            self.current_atmosphere = "rain"
            self._init_rain()
            print(f"Selected atmosphere: RAIN (intense storm) - {len(self.rain_drops)} drops created")
        elif random_num == 2:
            self.current_atmosphere = "snow"
            self._init_snow()
            print(f"Selected atmosphere: SNOW (winter wonderland)")
        else:  # random_num == 3
            self.current_atmosphere = "cherry_blossom"
            self._init_cherry_blossoms()
            print(f"Selected atmosphere: CHERRY BLOSSOM (peaceful spring)")
    
    def _init_rain(self):
        """Initialize rain atmospheric effect in world space."""
        import random
        # Create MANY more rain drops for intense storm effect
        map_margin = 500  # Extra area around map for seamless coverage
        for _ in range(800):  # Much more rain for intense storm
            # Varied rain colors for more realistic storm effect
            color_variants = [
                (160, 180, 255),  # Light blue
                (180, 200, 255),  # Lighter blue
                (200, 220, 255),  # Very light blue
                (220, 230, 255),  # Almost white-blue
                (255, 255, 255),  # Pure white
                (140, 160, 240),  # Deeper blue
                (190, 210, 250),  # Pale blue
            ]
            
            self.rain_drops.append({
                'x': random.uniform(-1920 - map_margin, 1920 + map_margin),
                'y': random.uniform(-1080 - map_margin, 1080 + map_margin),
                'speed': random.uniform(400, 700),  # Faster for intense storm
                'length': random.randint(15, 25),   # Longer rain lines
                'color': random.choice(color_variants),  # Varied colors
                'wind_drift': random.uniform(-50, 50),  # More wind variation
                'thickness': random.choice([1, 1, 1, 2])  # Mostly thin, some thicker drops
            })
        self.rain_tint_alpha = 80  # Stronger storm tint
        self.lightning_timer = 0.0
        self.lightning_flash = 0.0
    
    def _init_snow(self):
        """Initialize snow atmospheric effect in world space."""
        import random
        # Create snowflakes to cover the map area with good coverage
        map_margin = 500
        for _ in range(400):  # Significantly increased for better snow coverage
            self.snow_flakes.append({
                'x': random.uniform(-1920 - map_margin, 1920 + map_margin),
                'y': random.uniform(-1080 - map_margin, 1080 + map_margin),
                'speed': random.uniform(50, 120),
                'drift': random.uniform(-20, 20),
                'size': random.randint(2, 6),
                'opacity': random.randint(200, 255)  # 80% opacity
            })
        self.snow_tint_alpha = 30
    
    def _init_cherry_blossoms(self):
        """Initialize cherry blossom atmospheric effect in world space."""
        import random
        # Create cherry blossom petals to cover the map area
        map_margin = 500
        for _ in range(200):  # Increased for better coverage
            self.cherry_petals.append({
                'x': random.uniform(-1920 - map_margin, 1920 + map_margin),
                'y': random.uniform(-1080 - map_margin, 1080 + map_margin),
                'speed': random.uniform(30, 80),
                'drift': random.uniform(-50, 50),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-90, 90),
                'size': random.randint(8, 15),  # Increased size for better visibility
                'color': random.choice([(255, 182, 193, 204), (255, 192, 203, 204), (255, 160, 180, 204)])  # 80% opacity
            })
    
    def add_footprint(self, x: float, y: float):
        """Add a footprint when walking in snow."""
        if self.current_atmosphere == "snow":
            import time
            import random
            
            # Add slight offset for more natural footprint pattern
            offset_x = random.uniform(-5, 5)
            offset_y = random.uniform(-5, 5)
            
            self.footprints.append({
                'x': x + offset_x,
                'y': y + offset_y,
                'timestamp': time.time(),
                'fade_time': 3.0,  # Footprints last 3 seconds
                'size': random.randint(6, 10)  # Varying footprint sizes
            })
            
            # Limit footprints to prevent memory issues
            if len(self.footprints) > 200:
                self.footprints = self.footprints[-100:]
    
    def update(self, dt: float):
        """Update atmospheric effects (screen-space only, no camera offset)."""
        if not self.current_atmosphere:
            return
            
        self.effect_timer += dt
        
        if self.current_atmosphere == "rain":
            self._update_rain(dt)
        elif self.current_atmosphere == "snow":
            self._update_snow(dt)
        elif self.current_atmosphere == "cherry_blossom":
            self._update_cherry_blossoms(dt)
    
    def _update_rain(self, dt: float):
        """Update rain effects in world space."""
        import random
        
        # Update lightning timer and flash
        self.lightning_timer += dt
        if self.lightning_timer > random.uniform(8, 15):
            self.lightning_flash = 1.0
            self.lightning_timer = 0.0
        
        # Fade lightning flash
        if self.lightning_flash > 0:
            self.lightning_flash = max(0, self.lightning_flash - dt * 4)
        
        # Update rain drops in world space - they continue falling regardless of camera
        for drop in self.rain_drops:
            # Move rain in world coordinates (independent of camera)
            drop['y'] += drop['speed'] * dt
            drop['x'] += drop['wind_drift'] * dt
            
            # Reset drop when it goes too far down (world wrap to map boundaries)
            if drop['y'] > 1080 + 500:  # Bottom of map + margin
                drop['y'] = random.uniform(-1080 - 500, -1080 - 200)  # Respawn at top of map area
                drop['x'] = random.uniform(-1920 - 500, 1920 + 500)   # Random x position across map
    
    def _update_snow(self, dt: float):
        """Update snow effects in world space."""
        import random
        import time
        
        # Update snowflakes in world space
        for flake in self.snow_flakes:
            flake['y'] += flake['speed'] * dt
            flake['x'] += flake['drift'] * dt
            
            # Reset flake when it goes too far down (world wrap to map boundaries)
            if flake['y'] > 1080 + 500:
                flake['y'] = random.uniform(-1080 - 500, -1080 - 200)
                flake['x'] = random.uniform(-1920 - 500, 1920 + 500)
        
        # Update footprints (fade over time)
        current_time = time.time()
        self.footprints = [fp for fp in self.footprints 
                          if current_time - fp['timestamp'] < fp['fade_time']]
    
    def _update_cherry_blossoms(self, dt: float):
        """Update cherry blossom effects in world space."""
        import random
        
        # Update cherry petals in world space
        for petal in self.cherry_petals:
            petal['y'] += petal['speed'] * dt
            petal['x'] += petal['drift'] * dt
            petal['rotation'] += petal['rotation_speed'] * dt
            
            # Reset petal when it goes too far down (world wrap to map boundaries)
            if petal['y'] > 1080 + 500:
                petal['y'] = random.uniform(-1080 - 500, -1080 - 200)
                petal['x'] = random.uniform(-1920 - 500, 1920 + 500)
                petal['rotation'] = random.uniform(0, 360)
    
    def render(self, screen: pg.Surface, camera_offset: tuple = (0, 0)):
        """Render atmospheric effects in world space (uses camera offset like all world objects)."""
        if not self.current_atmosphere:
            return
            
        if self.current_atmosphere == "rain":
            self._render_rain(screen, camera_offset)
        elif self.current_atmosphere == "snow":
            self._render_snow(screen, camera_offset)
        elif self.current_atmosphere == "cherry_blossom":
            self._render_cherry_blossoms(screen, camera_offset)
    
    def _render_rain(self, screen: pg.Surface, camera_offset: tuple):
        """Render rain effect in world space with camera offset - intense storm."""
        # Debug: Count visible drops
        visible_count = 0
        
        # Render rain drops in world space - diagonal rain from top-left to bottom-right
        for drop in self.rain_drops:
            # Convert world position to screen position (same as snow/cherry blossoms)
            screen_x = drop['x'] + camera_offset[0]
            screen_y = drop['y'] + camera_offset[1]
            
            # Only render if visible on screen (with margin for performance)
            if (-100 <= screen_x <= screen.get_width() + 100 and 
                -100 <= screen_y <= screen.get_height() + 100):
                
                visible_count += 1
                
                # Diagonal rain: moves from top-left to bottom-right
                start_pos = (int(screen_x), int(screen_y))
                end_pos = (int(screen_x + drop['length']), int(screen_y + drop['length'] * 1.5))  # Diagonal movement
                
                # Use the varied color assigned to this drop
                color = drop['color']
                
                # Draw rain lines with varied thickness for more realistic storm
                pg.draw.line(screen, color, start_pos, end_pos, drop['thickness'])
        
        # Debug output every few seconds
        if hasattr(self, '_rain_debug_timer'):
            self._rain_debug_timer += 0.016  # Approximate frame time
            if self._rain_debug_timer > 3.0:  # Every 3 seconds
                print(f"Rain debug: {visible_count}/{len(self.rain_drops)} drops visible")
                self._rain_debug_timer = 0.0
        else:
            self._rain_debug_timer = 0.0
    
    def _render_snow(self, screen: pg.Surface, camera_offset: tuple):
        """Render snow effect in world space with camera offset."""
        # Render snowflakes in world space
        for flake in self.snow_flakes:
            # Convert world position to screen position
            screen_x = flake['x'] + camera_offset[0]
            screen_y = flake['y'] + camera_offset[1]
            
            # Only render if visible on screen
            if (-20 <= screen_x <= screen.get_width() + 20 and 
                -20 <= screen_y <= screen.get_height() + 20):
                
                pos = (int(screen_x), int(screen_y))
                color = (255, 255, 255, 204)  # 80% opacity
                snowflake_surface = pg.Surface((flake['size']*2, flake['size']*2), pg.SRCALPHA)
                pg.draw.circle(snowflake_surface, color, (flake['size'], flake['size']), flake['size'])
                screen.blit(snowflake_surface, (pos[0] - flake['size'], pos[1] - flake['size']))
    
    def _render_cherry_blossoms(self, screen: pg.Surface, camera_offset: tuple):
        """Render cherry blossom effect in world space with camera offset."""
        import math
        
        for petal in self.cherry_petals:
            # Convert world position to screen position
            screen_x = petal['x'] + camera_offset[0]
            screen_y = petal['y'] + camera_offset[1]
            
            # Only render if visible on screen
            if (-30 <= screen_x <= screen.get_width() + 30 and 
                -30 <= screen_y <= screen.get_height() + 30):
                
                pos = (int(screen_x), int(screen_y))
                color = petal['color']
                size = petal['size']
                
                # Create sakura blossom shape (5 petals)
                blossom_surface = pg.Surface((size*3, size*3), pg.SRCALPHA)
                center_x, center_y = size*3//2, size*3//2
                
                # Draw 5 petals in a star pattern
                for i in range(5):
                    angle = (i * 72 + petal['rotation']) * math.pi / 180  # 72 degrees between petals
                    petal_x = center_x + int(size * 0.8 * math.cos(angle))
                    petal_y = center_y + int(size * 0.8 * math.sin(angle))
                    
                    # Draw individual petal as small oval/ellipse
                    petal_size = max(2, size // 3)
                    pg.draw.ellipse(blossom_surface, color, 
                                   (petal_x - petal_size//2, petal_y - petal_size, 
                                    petal_size, petal_size*2))
                
                # Draw center of blossom
                pg.draw.circle(blossom_surface, (255, 255, 200, 180), 
                              (center_x, center_y), max(1, size // 4))
                
                screen.blit(blossom_surface, (pos[0] - center_x, pos[1] - center_y))
    
    def render_screen_overlays(self, screen: pg.Surface):
        """Render atmospheric screen overlays (storm tint, lightning, snow ground overlay)."""
        if not self.current_atmosphere:
            return
            
        if self.current_atmosphere == "rain":
            # Apply blue storm tint with brightness lowering
            storm_overlay = pg.Surface((screen.get_width(), screen.get_height()), pg.SRCALPHA)
            storm_overlay.fill((20, 30, 60, self.rain_tint_alpha))
            screen.blit(storm_overlay, (0, 0))
            
            # Apply lightning flash if active
            if self.lightning_flash > 0:
                flash_overlay = pg.Surface((screen.get_width(), screen.get_height()), pg.SRCALPHA)
                flash_intensity = int(self.lightning_flash * 150)
                flash_overlay.fill((255, 255, 255, flash_intensity))
                screen.blit(flash_overlay, (0, 0))
                
        elif self.current_atmosphere == "snow":
            # Add white/frosted ground overlay for snow
            ground_overlay = pg.Surface((screen.get_width(), screen.get_height()), pg.SRCALPHA)
            ground_overlay.fill((255, 255, 255, 40))  # 80% of 50 = 40
            screen.blit(ground_overlay, (0, 0))
    
    def render_footprints(self, screen: pg.Surface, camera_offset: tuple):
        """Render footprints in world space (uses camera offset since they're world objects)."""
        if self.current_atmosphere != "snow":
            return
            
        import time
        current_time = time.time()
        
        for fp in self.footprints:
            # Calculate alpha based on age (fade out over time)
            age = current_time - fp['timestamp']
            alpha = max(0, int(255 * (1 - age / fp['fade_time'])))
            
            if alpha > 0:
                world_pos = (fp['x'], fp['y'])
                screen_pos = (int(world_pos[0] - camera_offset[0]), 
                            int(world_pos[1] - camera_offset[1]))
                
                # Only render if on screen
                if (-50 <= screen_pos[0] <= screen.get_width() + 50 and 
                    -50 <= screen_pos[1] <= screen.get_height() + 50):
                    color = (100, 100, 120, alpha)  # Darker than snow
                    footprint_surface = pg.Surface((fp['size']*2, fp['size']*2), pg.SRCALPHA)
                    pg.draw.circle(footprint_surface, color, (fp['size'], fp['size']), fp['size'])
                    screen.blit(footprint_surface, (screen_pos[0] - fp['size'], screen_pos[1] - fp['size']))
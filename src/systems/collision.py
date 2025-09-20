"""
Collision detection system for the twin-stick shooter game.
Handles all collision detection and response between game objects.
"""

import pygame as pg
import math
from typing import List, Tuple
from src.entities.player import Player
from src.entities.bullet import Bullet, BulletManager
from src.entities.enemy import Enemy, EnemyManager

class CollisionManager:
    """Handles all collision detection in the game."""
    
    def __init__(self):
        """Initialize the collision manager."""
        pass
    
    def check_bullet_enemy_collisions(self, bullet_manager: BulletManager, 
                                    enemy_manager: EnemyManager, player=None, effects_manager=None, world_manager=None, bullet_hit_callback=None) -> int:
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
            from src.entities.bullet import BulletType
            if bullet.type == BulletType.ENEMY_LASER:
                continue  # Enemy bullets don't hurt enemies
                
            # Skip network bullets - they are visual only for local player
            if hasattr(bullet, 'is_network_bullet') and bullet.is_network_bullet:
                continue  # Network bullets don't collide with local enemies
                
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
                        
                        # Add BURST points to player when hitting enemy
                        if player and hasattr(player, 'add_burst_points'):
                            player.add_burst_points(1)
                        
                        # Check for SMG bouncing bullets first
                        should_remove_bullet = True
                        if (hasattr(bullet, 'bounce_enabled') and bullet.bounce_enabled and 
                            hasattr(bullet, 'bounces_remaining') and bullet.bounces_remaining > 0):
                            # Try to bounce off enemy toward another target
                            if self.handle_enemy_bounce(bullet, enemy, enemy_manager, world_manager):
                                should_remove_bullet = False  # Bullet bounced successfully
                                bullet.bounces_remaining -= 1
                                bullet.has_bounced = True
                                # Add visual bounce effect at the enemy position (impact point)
                                bullet.add_bounce_effect(enemy.pos)
                                # Move bullet to enemy position for accurate bounce start point
                                bullet.pos = enemy.pos.copy()
                        
                        # Handle bullet penetration
                        if hasattr(bullet, 'hits_remaining'):
                            bullet.hits_remaining -= 1
                            # Only remove bullet if it has no penetration left and didn't bounce
                            if bullet.hits_remaining <= 0 and should_remove_bullet and bullet not in bullets_to_remove:
                                # Grenades now use missile system, so no special handling needed for bullets
                                # All bullets get removed normally
                                bullets_to_remove.append(bullet)
                                    
                                # Check for special attack V-shaped blast (shotgun)
                                if (hasattr(bullet, 'special_attack') and bullet.special_attack and 
                                      hasattr(bullet, 'weapon_type') and bullet.weapon_type == "Shotgun"):
                                    self.trigger_v_shaped_blast(bullet, enemy, enemy_manager, effects_manager)
                                
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
                                
                                # Send bullet hit event for network synchronization
                                if bullet_hit_callback:
                                    bullet_hit_callback(bullet.pos.x, bullet.pos.y)
                        else:
                            # Default behavior for bullets without penetration system
                            if should_remove_bullet and bullet not in bullets_to_remove:
                                bullets_to_remove.append(bullet)
                                
                                # Check for special attack V-shaped blast (shotgun)
                                if (hasattr(bullet, 'special_attack') and bullet.special_attack and 
                                    hasattr(bullet, 'weapon_type') and bullet.weapon_type == "Shotgun"):
                                    self.trigger_v_shaped_blast(bullet, enemy, enemy_manager, effects_manager)
                                
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
                                
                                # Send bullet hit event for network synchronization
                                if bullet_hit_callback:
                                    bullet_hit_callback(bullet.pos.x, bullet.pos.y)
                        
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
    
    def trigger_v_shaped_blast(self, bullet, hit_enemy, enemy_manager, effects_manager):
        """Trigger V-shaped blast behind the hit enemy for shotgun special attacks."""
        import math
        
        print(f"=== V-SHAPED BLAST TRIGGERED ===")
        print(f"Original enemy hit at: {hit_enemy.pos}")
        
        # Use bullet's velocity direction (the direction it was traveling)
        bullet_velocity = getattr(bullet, 'velocity', None)
        if bullet_velocity and hasattr(bullet_velocity, 'x') and hasattr(bullet_velocity, 'y'):
            # Calculate angle from bullet's velocity direction
            impact_angle = math.degrees(math.atan2(bullet_velocity.y, bullet_velocity.x))
        else:
            # Fallback to bullet angle if velocity not available
            impact_angle = getattr(bullet, 'angle', 0)
        
        # V-shaped blast emanates from behind the enemy (opposite to bullet travel direction)
        blast_origin_angle = impact_angle + 180  # Opposite direction from bullet travel
        blast_origin_distance = 30  # Much closer to the enemy for visibility
        
        blast_origin_x = hit_enemy.pos.x + math.cos(math.radians(blast_origin_angle)) * blast_origin_distance
        blast_origin_y = hit_enemy.pos.y + math.sin(math.radians(blast_origin_angle)) * blast_origin_distance
        
        # V-shaped blast properties from weapon config
        blast_angle = 45  # degrees for each side of the V
        blast_range = 400  # pixels (increased to match visual effect range)
        blast_damage = int(bullet.damage * 0.67)  # 2/3 damage as requested
        
        # The V-blast opens in the direction the bullet was traveling (impact_angle)
        # NOT from the blast origin direction (blast_origin_angle)
        v_direction_angle = impact_angle  # Direction the V opens toward
        
        # Create V-shaped damage area
        left_angle = v_direction_angle - blast_angle / 2
        right_angle = v_direction_angle + blast_angle / 2
        
        enemies_hit = 0
        total_damage_dealt = 0
        
        # Check for enemies in the V-shaped blast area
        print(f"🔍 DEBUG: Checking {len(enemy_manager.get_enemies())} enemies for V-blast damage")
        print(f"🔍 Blast center angle: {v_direction_angle:.1f}°, blast_angle: {blast_angle}° (±{blast_angle/2:.1f}°)")
        
        for enemy in enemy_manager.get_enemies():
            if enemy == hit_enemy:
                continue  # Don't damage the originally hit enemy again
            
            # Calculate distance and angle to potential target
            to_enemy = enemy.pos - pg.Vector2(blast_origin_x, blast_origin_y)
            distance = to_enemy.length()
            
            print(f"🔍 Enemy at {enemy.pos} -> Distance: {distance:.1f} (max: {blast_range})")
            
            if distance > blast_range:
                print(f"  ❌ Too far ({distance:.1f} > {blast_range})")
                continue  # Too far away
            
            if distance == 0:
                print(f"  ❌ Zero distance")
                continue  # Avoid division by zero
            
            # Calculate angle to this enemy
            enemy_angle = math.degrees(math.atan2(to_enemy.y, to_enemy.x))
            
            # Normalize angles to handle wrapping around 360°
            def normalize_angle(angle):
                while angle > 180:
                    angle -= 360
                while angle < -180:
                    angle += 360
                return angle
            
            blast_center = normalize_angle(v_direction_angle)  # Use V direction, not origin direction
            enemy_relative = normalize_angle(enemy_angle - blast_center)
            
            print(f"  🎯 Enemy angle: {enemy_angle:.1f}°, relative to blast: {enemy_relative:.1f}°")
            print(f"  🎯 Checking if |{enemy_relative:.1f}°| <= {blast_angle/2:.1f}°")
            
            # Check if enemy is within the V-shaped blast angle
            if abs(enemy_relative) <= blast_angle / 2:
                # Damage enemy
                enemy.take_damage(blast_damage)
                enemies_hit += 1
                total_damage_dealt += blast_damage
                print(f"  ✅ V-BLAST HIT! Enemy took {blast_damage} damage (distance: {distance:.1f})")
            else:
                print(f"  ❌ Outside V-angle ({abs(enemy_relative):.1f}° > {blast_angle/2:.1f}°)")
        
        print(f"🔍 V-Blast Summary: {enemies_hit} enemies hit, {total_damage_dealt} total damage dealt!")
        print(f"🔍 Blast origin: ({blast_origin_x:.1f}, {blast_origin_y:.1f})")
        print(f"🔍 Blast range: {blast_range}, damage per hit: {blast_damage}")
        print("=" * 40)
        
        # Add visual effect for V-shaped blast
        # The V should open AWAY from the bullet's origin (opposite to bullet travel direction)
        # Since impact_angle is the bullet travel direction, we want the V to open in that same direction
        # BUT from the blast origin point which is already positioned behind the enemy
        v_opening_angle = impact_angle  # V opens away from bullet origin
        
        if effects_manager and hasattr(effects_manager, 'add_v_shaped_blast'):
            effects_manager.add_v_shaped_blast(blast_origin_x, blast_origin_y, v_opening_angle)
            print(f"🔥 MASSIVE RED V-BLAST EFFECT ADDED at ({blast_origin_x:.1f}, {blast_origin_y:.1f}) with angle {v_opening_angle}°")
        else:
            print(f"❌ Effects manager issue: {effects_manager}")
    
    def handle_enemy_bounce(self, bullet, hit_enemy, enemy_manager, world_manager=None):
        """Handle bullet bouncing off enemies toward nearest target."""
        import math
        
        # Get bullet's bounce range for finding targets
        bounce_range = getattr(bullet, 'bounce_range', 200)  # Default bounce range
        
        # Find nearest enemy within bounce range (excluding the one we just hit)
        # Use the hit enemy's position as the bounce origin point
        bounce_origin = hit_enemy.pos
        nearest_enemy = None
        min_distance = float('inf')
        
        for enemy in enemy_manager.get_enemies():
            if enemy == hit_enemy:
                continue  # Skip the enemy we just hit
                
            distance = bounce_origin.distance_to(enemy.pos)
            if distance <= bounce_range and distance < min_distance:
                min_distance = distance
                nearest_enemy = enemy
        
        if nearest_enemy:
            # Calculate bounce direction from impact point toward nearest enemy
            bounce_direction = (nearest_enemy.pos - bounce_origin)
            if bounce_direction.length() > 0:
                bounce_direction = bounce_direction.normalize()
                
                # Update bullet velocity and angle
                bullet.velocity = bounce_direction * bullet.speed
                bullet.angle = math.degrees(math.atan2(bounce_direction.y, bounce_direction.x))
                
                # Update starting position for range calculation from bounce point
                bullet.start_pos = bounce_origin.copy()
                
                return True  # Bounce successful
        
        # No enemy target found, skip surface bounce if no world_manager
        if world_manager and hasattr(bullet, 'bounce_off_surface'):
            # For surface bouncing, also use the impact point
            bullet.pos = bounce_origin.copy()
            bullet.start_pos = bounce_origin.copy()
            return bullet.bounce_off_surface(world_manager)
        else:
            return False  # Can't bounce without world manager
    
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
                        
                        # Let the player's movement system handle world bounds
                        player.pos = new_pos
        
        return player_took_damage
    
    def check_enemy_bullet_player_collisions(self, bullet_manager: BulletManager, player: Player) -> bool:
        """
        Check collisions between enemy bullets and player.
        Returns True if player took damage.
        """
        from src.entities.bullet import BulletType
        bullets_to_remove = []
        player_took_damage = False
        
        for bullet in bullet_manager.get_bullets():
            # Only check enemy bullets
            if bullet.type != BulletType.ENEMY_LASER:
                continue
            
            # Check collision with player
            distance = (bullet.pos - player.pos).length()
            if distance <= bullet.size + player.size:
                # Player takes damage from enemy bullet
                player.take_damage(bullet.damage)
                player_took_damage = True
                bullets_to_remove.append(bullet)
        
        # Remove bullets that hit the player
        for bullet in bullets_to_remove:
            bullet_manager.remove_bullet(bullet)
            
        return player_took_damage
    
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
    
    def check_bullet_enemy_collisions_network_client(self, bullet_manager, enemy_manager, player=None, 
                                                    effects_manager=None, world_manager=None, game_synchronizer=None, bullet_hit_callback=None):
        """
        Network client collision detection - detects hits and sends damage to host instead of applying locally.
        Returns 0 kills (since host handles the actual enemy deaths).
        """
        from src.networking.network_manager import MessageType
        
        bullets_to_remove = []
        damage_messages = []
        
        for bullet in bullet_manager.get_bullets():
            # Only check player bullets hitting enemies
            if bullet.type.value != "player":
                continue
                
            bullet_pos = pg.Vector2(bullet.pos)
            
            for enemy in enemy_manager.get_enemies():
                if not enemy.is_alive():
                    continue
                    
                enemy_pos = pg.Vector2(enemy.pos)
                distance = bullet_pos.distance_to(enemy_pos)
                
                # Calculate effective bullet collision size based on shape
                effective_bullet_size = bullet.size
                if hasattr(bullet, 'shape') and bullet.shape == "laser":
                    # Laser bullets (sniper) have much larger visual beam width
                    effective_bullet_size = max(bullet.size * 4, 24) / 2  # Divide by 2 since we're using radius
                
                if distance <= effective_bullet_size + enemy.size:
                    # Collision detected - send damage to host instead of applying locally
                    # Rate-limited debug to reduce spam
                    import time
                    if not hasattr(self, '_collision_debug_time'):
                        self._collision_debug_time = 0
                    current_time = time.time()
                    if current_time - self._collision_debug_time > 3.0:
                        self._collision_debug_time = current_time
                        # Reduce client collision debug spam
                        if hasattr(self, '_client_collision_count'):
                            self._client_collision_count += 1
                        else:
                            self._client_collision_count = 1
                            
                        # Only log every 10th collision to reduce spam
                        if self._client_collision_count % 10 == 1:
                            print(f"[CLIENT_COLLISION] Client hit detected, sending to host")
                    
                    if game_synchronizer and game_synchronizer.network_manager:
                        # Send damage message to host
                        damage_data = {
                            'enemy_id': enemy.enemy_id,
                            'damage': bullet.damage,
                            'player_id': game_synchronizer.local_player_id,
                            'bullet_id': getattr(bullet, 'bullet_id', 'unknown'),
                            'position': (enemy.pos.x, enemy.pos.y)
                        }
                        
                        # Only log every 10th damage message to reduce spam
                        if self._client_collision_count % 10 == 1:
                            print(f"[CLIENT_DAMAGE] Sending damage message: {bullet.damage} to enemy {enemy.enemy_id}")
                        game_synchronizer.network_manager.send_message(
                            MessageType.ENEMY_DAMAGE,
                            damage_data
                        )
                        # Remove excessive success message spam
                        pass
                    
                    # Add BURST points to player when hitting enemy (client can do this locally)
                    if player and hasattr(player, 'add_burst_points'):
                        player.add_burst_points(1)
                    
                    # Send bullet hit event for network synchronization
                    if bullet_hit_callback:
                        bullet_hit_callback(bullet.pos.x, bullet.pos.y)
                    
                    # Handle visual effects locally (impacts, sparks, etc.)
                    # Note: Skip impact sparks for now to avoid method call issues
                    # if effects_manager:
                    #     effects_manager.add_impact_sparks(bullet.pos.x, bullet.pos.y, bullet.angle)
                    
                    # Check if bullet should be removed (most bullets are removed on hit)
                    should_remove_bullet = True
                    
                    # Handle bullet penetration
                    if hasattr(bullet, 'hits_remaining'):
                        bullet.hits_remaining -= 1
                        if bullet.hits_remaining > 0:
                            should_remove_bullet = False
                    
                    if should_remove_bullet:
                        bullets_to_remove.append(bullet)
                    
                    break  # Bullet can only hit one enemy per frame
        
        # Remove bullets that hit targets
        for bullet in bullets_to_remove:
            bullet_manager.remove_bullet(bullet)
        
        return 0  # Client doesn't kill enemies directly
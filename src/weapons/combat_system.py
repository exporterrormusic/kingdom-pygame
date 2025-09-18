"""
Combat System for Kingdom-Pygame

Handles all weapon-related combat mechanics including:
- Sword slash damage and effects
- Missile collision and explosion damage
- Minigun whip trail damage
- Combat scoring and screen shake effects

Extracted from main.py to improve modularity and maintainability.
"""

import pygame as pg


class CombatSystem:
    """Manages all weapon combat mechanics and damage calculations."""
    
    def __init__(self, game):
        """Initialize combat system with reference to main game instance."""
        self.game = game
    
    def check_slash_damage(self):
        """Check for continuous damage from active sword slash effects."""
        if not self.game.slash_effect_manager.effects:
            return
            
        # Get damage events from all active slash effects
        damage_events = self.game.slash_effect_manager.check_enemy_collisions(
            self.game.enemy_manager.enemies, 
            self.game.player
        )
        
        kills = 0
        enemies_hit = []
        
        # Process each damage event
        for event in damage_events:
            enemy = event['enemy']
            damage = event['damage']
            
            # Deal damage to the enemy
            enemy.take_damage(damage)
            enemies_hit.append(enemy)
            
            # Add BURST points to player when hitting enemy
            if hasattr(self.game.player, 'add_burst_points'):
                self.game.player.add_burst_points(1)
            
            # Check if enemy died and remove
            if not enemy.is_alive():
                # Add explosion/death particles at enemy position BEFORE removal
                self.game.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 100))  # Purple-ish explosion
                self.game.effects_manager.add_sword_impact_effect(enemy.pos.x, enemy.pos.y)  # Sword-specific death effect
                
                # Explosion lighting disabled - lighting system removed
                # if self.game.enable_dynamic_lighting:
                #     self.game.dynamic_lighting.add_explosion_light(enemy.pos.x, enemy.pos.y, intensity=1.5)
                
                self.game.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.game.score += 100
        
        # Add screen shake for sword impacts
        if enemies_hit:
            self.game.add_camera_shake(0.4, 0.2)
    
    def check_missile_visual_damage(self):
        """Check for continuous damage from missile bodies and explosions based on visual effects."""
        if not self.game.missile_manager.missiles:
            return
            
        # Get damage events from all active missiles
        damage_events = self.game.missile_manager.check_visual_damage(
            self.game.enemy_manager.enemies
        )
        
        kills = 0
        enemies_hit = []
        
        # Process each damage event
        for event in damage_events:
            enemy = event['enemy']
            damage = event['damage']
            damage_type = event['type']
            
            # Deal damage to the enemy
            enemy.take_damage(damage)
            enemies_hit.append(enemy)
            
            # Add BURST points to player when hitting enemy
            if hasattr(self.game.player, 'add_burst_points'):
                self.game.player.add_burst_points(1)
            
            # Check if enemy died and remove
            if not enemy.is_alive():
                # Add appropriate explosion/death particles at enemy position BEFORE removal
                if damage_type == 'missile_body':
                    self.game.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 150, 0))  # Orange explosion for missile hit
                else:  # explosion damage
                    self.game.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 50))  # Red-orange explosion for missile explosion
                
                # Explosion lighting disabled - lighting system removed
                # if self.game.enable_dynamic_lighting:
                #     self.game.dynamic_lighting.add_explosion_light(enemy.pos.x, enemy.pos.y, intensity=2.0)
                
                self.game.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.game.score += 100
        
        # Add screen shake for missile impacts
        if enemies_hit:
            impact_intensity = 0.6 if any(event['type'] == 'explosion' for event in damage_events) else 0.3
            self.game.add_camera_shake(impact_intensity, 0.3)
    
    def create_slash_effect(self, sword_range, slash_arc, damage):
        """Create a visual slash effect for the sword attack."""
        # Pass player reference and damage so slash follows player movement and deals damage
        self.game.slash_effect_manager.create_slash(
            self.game.player,  # Pass player reference
            0,  # Relative angle offset (0 = follows player direction exactly)
            sword_range,
            damage  # Pass damage value to the slash effect
        )
    
    def check_missile_enemy_collisions(self):
        """Check for missile collisions with enemies and handle explosions."""
        from src.effects.missile_system import MissileState  # Import here to avoid circular imports
        
        kills = 0
        for missile in self.game.missile_manager.missiles[:]:  # Use slice copy for safe iteration
            if missile.state == MissileState.FLYING:
                # Check direct hit with enemies
                for enemy in self.game.enemy_manager.get_enemies():
                    distance = (missile.pos - enemy.pos).length()
                    if distance < enemy.size:
                        # Direct hit - explode missile
                        missile.explode()
                        break
                        
            elif missile.state == MissileState.EXPLODING:
                # Check AOE damage during explosion
                explosion_radius = 150  # Match the radius from weapons.json
                for enemy in self.game.enemy_manager.get_enemies():
                    distance = (missile.pos - enemy.pos).length()
                    if distance <= explosion_radius:
                        # Store enemy position before applying damage
                        enemy_pos = (enemy.pos.x, enemy.pos.y)
                        was_alive = enemy.is_alive()
                        
                        # Apply explosion damage
                        enemy.take_damage(missile.damage)
                        if was_alive and not enemy.is_alive():
                            kills += 1
                            # Add explosion effect for each enemy killed
                            self.game.effects_manager.add_explosion(enemy_pos[0], enemy_pos[1])
                            
                            # Add explosion lighting (disabled - lighting system removed)
                            # if self.game.enable_dynamic_lighting:
                            #     self.game.dynamic_lighting.add_explosion_light(enemy_pos[0], enemy_pos[1], intensity=1.8)
                
                # Add screen shake for explosion
                self.game.add_camera_shake(0.4, 0.4)
                
        return kills
    
    def check_whip_damage(self):
        """Check for minigun whip trail damage to enemies."""
        if not hasattr(self.game, 'minigun_effects_manager'):
            return 0
            
        kills = 0
        
        for enemy in self.game.enemy_manager.get_enemies():
            # Check if enemy collides with whip trail
            hit, damage, hit_x, hit_y = self.game.minigun_effects_manager.check_whip_collision(
                enemy.pos.x, enemy.pos.y, enemy.size
            )
            
            if hit:
                # Store enemy state before damage
                was_alive = enemy.is_alive()
                
                # Apply whip damage
                enemy.take_damage(damage)
                
                # Create impact spark at hit location
                self.game.minigun_effects_manager.create_impact_spark(hit_x, hit_y)
                
                # Check if enemy was killed
                if was_alive and not enemy.is_alive():
                    kills += 1
                    # Add small explosion effect
                    self.game.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y)
                    
                    # Add explosion lighting for minigun kills (disabled - lighting system removed)
                    # if self.game.enable_dynamic_lighting:
                    #     self.game.dynamic_lighting.add_explosion_light(enemy.pos.x, enemy.pos.y, intensity=1.2)
                    
        return kills
"""
Enemy system for the twin-stick shooter game.
Handles enemy AI, movement, and behavior.
"""

import pygame as pg
import math
import random
import os
from typing import List, Tuple, Optional
from enum import Enum

# Handle imports for sprite animation
try:
    from src.sprite_animation import AnimatedSprite
except ImportError:
    try:
        from sprite_animation import AnimatedSprite
    except ImportError:
        # If neither works, we'll create a dummy class
        AnimatedSprite = None

# Handle asset manager import
try:
    from src.asset_manager import AssetManager
    asset_manager = AssetManager()
except ImportError:
    try:
        from asset_manager import AssetManager
        asset_manager = AssetManager()
    except ImportError:
        asset_manager = None

class EnemyType(Enum):
    """Types of enemies."""
    BASIC = "basic"
    FAST = "fast"
    TANK = "tank"

class Enemy:
    """Base enemy class."""
    
    def __init__(self, x: float, y: float, enemy_type: EnemyType = EnemyType.BASIC, sprite_sheet_path: Optional[str] = None, wave: int = 1):
        """Initialize an enemy."""
        self.pos = pg.Vector2(x, y)
        self.velocity = pg.Vector2(0, 0)
        self.target_pos = pg.Vector2(0, 0)
        self.type = enemy_type
        self.wave = wave  # Store wave for scaling
        
        # Initialize stats based on type FIRST
        self._init_stats_by_type()
        
        # Apply wave scaling to speed (small increase per wave)
        wave_speed_multiplier = 1.0 + (wave - 1) * 0.1  # 10% increase per wave
        self.speed = int(self.speed * wave_speed_multiplier)
        
        # Current health
        self.health = self.max_health
        
        # AI state
        self.last_direction_change = 0.0
        self.wander_angle = random.uniform(0, 360)
        self.state = "seeking"  # seeking, wandering, attacking
        
        # Movement tracking for animation
        self.facing_angle = 0.0  # Direction enemy is facing
        self.last_direction = 'down'  # Track last animation direction
        self.direction_change_cooldown = 0.0  # Cooldown for direction changes
        self.direction_change_delay = 0.5  # 0.5 second delay between direction changes
        
        # Laser shooting
        self.last_laser_shot = 0.0
        self.laser_cooldown = random.uniform(0.3, 0.8)  # Much more frequent shooting
        self.can_shoot_lasers = random.random() < 0.9  # 90% of enemies can shoot
        
        # Store original size before sprite loading
        self.original_size = self.size
        
        # Sprite animation (optional)
        self.animated_sprite = None
        self.use_sprites = False
        
        if sprite_sheet_path and os.path.exists(sprite_sheet_path) and AnimatedSprite is not None:
            try:
                # Use the cached sprite sheet from AssetManager to avoid disk I/O
                sprite_sheet = None
                if asset_manager:
                    sprite_sheet = asset_manager.get_cached_sprite_sheet(sprite_sheet_path)
                    if sprite_sheet is None:
                        # Only load if not cached (first time)
                        sprite_sheet = asset_manager.load_sprite_sheet(sprite_sheet_path)
                else:
                    # Fallback to direct loading if no asset manager
                    sprite_sheet = pg.image.load(sprite_sheet_path)
                
                if sprite_sheet:
                    # Calculate frame dimensions exactly like player sprites
                    frame_w = sprite_sheet.get_width() // 3
                    frame_h = sprite_sheet.get_height() // 4
                    
                    # Create animated sprite smaller than player sprites (2/3 size)
                    enemy_scale_factor = 0.2 * (2/3)  # 2/3 the size of player sprites
                    self.animated_sprite = AnimatedSprite(
                        sprite_sheet_path, x, y, frame_w, frame_h, 0.15, enemy_scale_factor
                    )
                    self.use_sprites = True
                    
                    # Adjust collision size for scaled sprites 
                    scaled_frame_size = max(frame_w, frame_h) * enemy_scale_factor
                    self.size = int(scaled_frame_size // 3)  # Make collision smaller than sprite
                else:
                    raise Exception("Could not load sprite sheet")
            except Exception as e:
                print(f"Warning: Could not load enemy sprite sheet {sprite_sheet_path}: {e}")
                self.use_sprites = False
                self.size = self.original_size  # Restore original size on failure
        elif AnimatedSprite is None:
            self.use_sprites = False
        
        # Visual effects
        self.hurt_timer = 0.0
        self.hurt_duration = 0.2
    
    def _init_stats_by_type(self):
        """Initialize enemy stats based on type."""
        if self.type == EnemyType.BASIC:
            self.max_health = 50
            self.speed = 80  # Reduced further from 120 for more manageable gameplay
            self.size = 15
            self.color = (255, 100, 100)  # Red
            self.damage = 20
            
        elif self.type == EnemyType.FAST:
            self.max_health = 25
            self.speed = 120  # Reduced from 180 - still fast but not overwhelming
            self.size = 10
            self.color = (255, 150, 100)  # Orange
            self.damage = 15
            
        elif self.type == EnemyType.TANK:
            self.max_health = 150
            self.speed = 50  # Reduced from 80 - tanks should be slow and steady
            self.size = 25
            self.color = (150, 100, 255)  # Purple
            self.damage = 35
    
    def update(self, dt: float, player_pos: pg.Vector2, current_time: float):
        """Update enemy AI and movement."""
        # Update hurt effect
        if self.hurt_timer > 0:
            self.hurt_timer -= dt
        
        # Calculate distance to player
        to_player = player_pos - self.pos
        distance_to_player = to_player.length()
        
        # AI behavior - Make enemies much more aggressive and always swarm the player
        if distance_to_player < 800:  # Much larger detection range (increased from 300)
            self.state = "seeking"
            # Always move toward player aggressively
            if distance_to_player > 0:
                direction = to_player.normalize()
                
                # Add slight randomness for swarming behavior (prevents perfect stacking)
                swarm_offset = pg.Vector2(
                    random.uniform(-0.3, 0.3), 
                    random.uniform(-0.3, 0.3)
                )
                direction += swarm_offset
                if direction.length() > 0:
                    direction = direction.normalize()
                
                # Increase speed when close for more aggressive swarming
                speed_multiplier = 1.5 if distance_to_player < 150 else 1.0
                self.velocity = direction * self.speed * speed_multiplier
        else:
            # Still seek the player even at long range (no more wandering)
            self.state = "seeking"
            if distance_to_player > 0:
                direction = to_player.normalize()
                self.velocity = direction * (self.speed * 0.8)  # Slightly slower at long range
        
        # Apply movement
        self.pos += self.velocity * dt
        
        # Update facing direction based on movement (with cooldown to prevent glitching)
        if self.velocity.length() > 0:
            new_facing_angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
            
            # Determine new direction based on angle
            if new_facing_angle >= -45 and new_facing_angle < 45:
                new_direction = 'right'
            elif new_facing_angle >= 45 and new_facing_angle < 135:
                new_direction = 'down'
            elif new_facing_angle >= 135 or new_facing_angle < -135:
                new_direction = 'left'
            else:
                new_direction = 'up'
            
            # Only update direction if cooldown has passed
            if (new_direction != self.last_direction and 
                current_time - self.direction_change_cooldown > self.direction_change_delay):
                self.last_direction = new_direction
                self.facing_angle = new_facing_angle
                self.direction_change_cooldown = current_time
            elif new_direction == self.last_direction:
                # Same direction, update angle immediately
                self.facing_angle = new_facing_angle
        
        # Update sprite animation if using sprites
        if self.use_sprites and self.animated_sprite:
            self.animated_sprite.set_position(self.pos.x, self.pos.y)
            # Pass the smoothed facing angle (converted to radians) 
            facing_angle_rad = math.radians(self.facing_angle)
            self.animated_sprite.update(dt, self.velocity, facing_angle_rad)
        
        # Laser shooting logic
        if (self.can_shoot_lasers and 
            distance_to_player < 400 and  # Increased range for more aggressive shooting
            current_time - self.last_laser_shot > self.laser_cooldown):
            
            # Calculate angle to player for accurate shooting
            angle_to_player = math.degrees(math.atan2(to_player.y, to_player.x))
            
            # Signal that this enemy wants to shoot (will be handled by EnemyManager)
            self.should_shoot_laser = True
            self.laser_angle = angle_to_player
            self.last_laser_shot = current_time
            self.laser_cooldown = random.uniform(0.2, 0.6)  # Much more aggressive shooting
        else:
            self.should_shoot_laser = False
        
        # Keep enemy roughly on screen (with some buffer for spawning)
        self.pos.x = max(-50, min(1970, self.pos.x))
        self.pos.y = max(-50, min(1130, self.pos.y))
    
    def take_damage(self, damage: int):
        """Apply damage to the enemy."""
        self.health = max(0, self.health - damage)
        self.hurt_timer = self.hurt_duration
    
    def is_alive(self) -> bool:
        """Check if enemy is still alive."""
        return self.health > 0
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render the enemy."""
        # Apply camera offset
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        if self.use_sprites and self.animated_sprite:
            # Render sprite animation
            self.animated_sprite.render(screen, offset)
            
            # Apply hurt flash effect by drawing a white overlay (if hurt)
            if self.hurt_timer > 0:
                # Create a white tinted surface overlay
                sprite_size = int(32 * 0.8)  # Match the enemy scale factor
                sprite_rect = pg.Rect(render_x - sprite_size//2, render_y - sprite_size//2, sprite_size, sprite_size)
                white_overlay = pg.Surface((sprite_size, sprite_size), pg.SRCALPHA)
                white_overlay.fill((255, 255, 255, 128))  # Semi-transparent white
                screen.blit(white_overlay, sprite_rect)
        else:
            # Fallback to geometric rendering
            # Choose color based on state and hurt effect
            render_color = self.color
            if self.hurt_timer > 0:
                # Flash white when hurt
                render_color = (255, 255, 255)
            
            # Draw enemy body
            pg.draw.circle(screen, render_color, (render_x, render_y), self.size)
            
            # Draw darker outline
            outline_color = tuple(max(0, c - 50) for c in self.color)
            pg.draw.circle(screen, outline_color, (render_x, render_y), self.size, 2)
        
        # Draw health bar if damaged (scaled for larger resolution)
        if self.health < self.max_health:
            bar_width = int(self.size * 3)  # Scale with enemy size
            bar_height = 6  # Increased from 4
            bar_x = render_x - bar_width // 2
            bar_y = render_y - self.size - 12  # Moved slightly further up
            
            # Background
            pg.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
            
            # Health bar
            health_ratio = self.health / self.max_health
            health_width = health_ratio * bar_width
            health_color = (255, 0, 0) if health_ratio < 0.3 else (255, 255, 0) if health_ratio < 0.6 else (0, 255, 0)
            pg.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Draw type indicator (small shape)
        if self.type == EnemyType.FAST:
            # Triangle for fast enemies
            points = [
                (self.pos.x, self.pos.y - 5),
                (self.pos.x - 4, self.pos.y + 3),
                (self.pos.x + 4, self.pos.y + 3)
            ]
            pg.draw.polygon(screen, (255, 255, 255), points)
            
        elif self.type == EnemyType.TANK:
            # Square for tank enemies
            pg.draw.rect(screen, (255, 255, 255), 
                        (self.pos.x - 4, self.pos.y - 4, 8, 8))
    
    def get_rect(self) -> pg.Rect:
        """Get collision rectangle for the enemy."""
        return pg.Rect(self.pos.x - self.size, self.pos.y - self.size,
                      self.size * 2, self.size * 2)

class EnemyManager:
    """Manages all enemies in the game."""
    
    def __init__(self):
        """Initialize the enemy manager."""
        self.enemies: List[Enemy] = []
        
        # Spawning mechanics
        self.spawn_timer = 0.0
        self.spawn_interval = 1.5  # Much slower initial spawning (was 0.25)
        self.max_enemies = 15  # Reduced max enemies (was 35)
        
        # Wave system
        self.wave = 1
        self.enemies_killed = 0
        
        # Sprite sheet caching to prevent stuttering
        self.cached_sprite_path = "assets/images/Enemies/rapture1-sprite.png"
        
        # Pre-load and verify sprite sheet exists
        if not os.path.exists(self.cached_sprite_path):
            print(f"Warning: Enemy sprite sheet not found: {self.cached_sprite_path}")
            self.cached_sprite_path = None
    
    def spawn_enemy(self, screen_width: int = 1920, screen_height: int = 1080):
        """Spawn a new enemy at the edge of the screen."""
        if len(self.enemies) >= self.max_enemies:
            return
        
        # Choose spawn location (edge of screen with buffer)
        side = random.randint(0, 3)
        buffer = 50
        
        if side == 0:  # Top
            x = random.randint(-buffer, screen_width + buffer)
            y = -buffer
        elif side == 1:  # Right
            x = screen_width + buffer
            y = random.randint(-buffer, screen_height + buffer)
        elif side == 2:  # Bottom
            x = random.randint(-buffer, screen_width + buffer)
            y = screen_height + buffer
        else:  # Left
            x = -buffer
            y = random.randint(-buffer, screen_height + buffer)
        
        # Choose enemy type based on wave
        enemy_types = [EnemyType.BASIC]
        if self.wave >= 2:
            enemy_types.append(EnemyType.FAST)
        if self.wave >= 3:
            enemy_types.append(EnemyType.TANK)
        
        enemy_type = random.choice(enemy_types)
        
        # Use cached sprite path to prevent loading delays
        enemy = Enemy(x, y, enemy_type, self.cached_sprite_path, self.wave)
        self.enemies.append(enemy)
    
    def update(self, dt: float, player_pos: pg.Vector2, current_time: float, bullet_manager=None):
        """Update all enemies and handle spawning."""
        # Update spawn timer
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_enemy()
            self.spawn_timer = 0.0

        # Update all enemies
        enemies_to_remove = []

        for enemy in self.enemies:
            enemy.update(dt, player_pos, current_time)
            
            # Handle enemy laser shooting
            if (bullet_manager is not None and 
                hasattr(enemy, 'should_shoot_laser') and 
                enemy.should_shoot_laser):
                
                bullet_manager.shoot_enemy_laser(
                    enemy.pos.x, 
                    enemy.pos.y, 
                    enemy.laser_angle, 
                    current_time
                )

            if not enemy.is_alive():
                enemies_to_remove.append(enemy)
                self.enemies_killed += 1
        
        # Handle enemy-to-enemy collision to prevent overlapping
        self._handle_enemy_collisions()

        # Remove dead enemies
        for enemy in enemies_to_remove:
            self.enemies.remove(enemy)        # Update wave if enough enemies killed
        if self.enemies_killed >= self.wave * 10:
            self.wave += 1
            # Gradually increase difficulty each wave
            self.spawn_interval = max(0.8, self.spawn_interval * 0.95)  # Slower reduction
            self.max_enemies = min(25, self.max_enemies + 1)  # Smaller increases
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render all enemies."""
        for enemy in self.enemies:
            enemy.render(screen, offset)
    
    def get_enemies(self) -> List[Enemy]:
        """Get list of all active enemies."""
        return self.enemies
    
    def remove_enemy(self, enemy: Enemy):
        """Remove a specific enemy."""
        if enemy in self.enemies:
            self.enemies.remove(enemy)
    
    def _handle_enemy_collisions(self):
        """Handle collision detection between enemies with smooth bubble physics."""
        for i, enemy1 in enumerate(self.enemies):
            for j, enemy2 in enumerate(self.enemies[i+1:], i+1):
                # Calculate distance between enemies
                distance_vector = enemy1.pos - enemy2.pos
                distance = distance_vector.length()
                
                # Define bubble radius (larger than sprite for smooth separation)
                bubble_radius1 = enemy1.size + 15  # Larger bubble around enemy
                bubble_radius2 = enemy2.size + 15
                min_distance = bubble_radius1 + bubble_radius2
                
                if distance < min_distance and distance > 0.1:  # Avoid division by zero
                    # Calculate separation direction
                    separation_direction = distance_vector.normalize()
                    
                    # Calculate how much they're overlapping
                    overlap = min_distance - distance
                    
                    # Apply gentle push force (reduced strength to avoid glitching)
                    push_strength = overlap * 0.3  # Gentler push
                    
                    # Apply separation with damping to prevent oscillation
                    push_vector = separation_direction * push_strength
                    
                    # Move each enemy away from the other (split the push)
                    enemy1.pos += push_vector * 0.5
                    enemy2.pos -= push_vector * 0.5
                    
                    # Add slight velocity dampening to prevent jittery behavior
                    if hasattr(enemy1, 'velocity'):
                        enemy1.velocity *= 0.9
                    if hasattr(enemy2, 'velocity'):
                        enemy2.velocity *= 0.9
    
    def clear(self):
        """Remove all enemies."""
        self.enemies.clear()
        
    def get_enemy_count(self) -> int:
        """Get the number of active enemies."""
        return len(self.enemies)
    
    def get_wave(self) -> int:
        """Get current wave number."""
        return self.wave
    
    def get_kills(self) -> int:
        """Get total enemies killed."""
        return self.enemies_killed
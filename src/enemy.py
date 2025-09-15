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
    
    def __init__(self, x: float, y: float, enemy_type: EnemyType = EnemyType.BASIC, sprite_sheet_path: Optional[str] = None, wave: int = 1, wave_danger_level: int = 1, distance_from_spawn: float = 0.0):
        """Initialize an enemy."""
        self.pos = pg.Vector2(x, y)
        self.velocity = pg.Vector2(0, 0)
        self.target_pos = pg.Vector2(0, 0)
        self.type = enemy_type
        self.wave = wave  # Store wave for scaling
        self.wave_danger_level = wave_danger_level
        self.distance_from_spawn = distance_from_spawn
        
        # Initialize base stats based on type FIRST
        self._init_stats_by_type()
        
        # Apply wave-based scaling (1.0x to 2.0x multiplier based on danger level)
        wave_multiplier = 1.0 + (wave_danger_level - 1) * 0.25  # 25% increase per danger level
        
        # Apply distance-based scaling (increases with distance from spawn)
        # Every 2048 pixels (one chunk) adds 10% difficulty
        distance_chunks = distance_from_spawn / 2048.0
        distance_multiplier = 1.0 + (distance_chunks * 0.1)
        
        # Apply wave scaling to speed (small increase per wave)
        wave_speed_multiplier = 1.0 + (wave - 1) * 0.1  # 10% increase per wave
        
        # Combine all scaling factors
        total_multiplier = wave_multiplier * distance_multiplier * wave_speed_multiplier
        
        # Scale stats
        self.max_health = int(self.max_health * total_multiplier)
        self.speed = int(self.speed * wave_speed_multiplier)  # Speed only scales with wave, not biome
        self.damage = int(self.damage * wave_multiplier)  # Damage scales with wave danger
        
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
        
        # Debug timer for movement
        self._last_debug_wave_check = 0.0
        
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
    
    def take_damage(self, damage: int):
        """Apply damage to the enemy."""
        self.health = max(0, self.health - damage)
        self.hurt_timer = self.hurt_duration
    
    def _apply_hurt_tinting(self, surface: pg.Surface, intensity: float):
        """Apply hurt flash tinting to a surface while respecting alpha channel - OPTIMIZED."""
        # Use pygame's built-in color blending for better performance
        if intensity <= 0:
            return
        
        # Create a temporary surface for blending
        overlay = pg.Surface(surface.get_size(), pg.SRCALPHA)
        overlay.fill((255, 255, 255, int(128 * intensity)))  # Semi-transparent white
        
        # Use pygame's optimized blend modes
        surface.blit(overlay, (0, 0), special_flags=pg.BLEND_ALPHA_SDL2)
    
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
            
            # Apply hurt flash effect with alpha-respecting tinting
            if self.hurt_timer > 0:
                # Get current sprite surface
                sprite_surface = self.animated_sprite.animation.get_current_frame()
                if sprite_surface:
                    # Create a copy to apply tinting
                    tinted_sprite = sprite_surface.copy()
                    
                    # Apply per-pixel tinting that respects alpha
                    flash_intensity = min(1.0, self.hurt_timer / self.hurt_duration)
                    self._apply_hurt_tinting(tinted_sprite, flash_intensity)
                    
                    # Scale sprite to match enemy scale
                    sprite_size = int(32 * 0.8)
                    tinted_sprite = pg.transform.scale(tinted_sprite, (sprite_size, sprite_size))
                    
                    # Render the tinted sprite
                    sprite_rect = pg.Rect(render_x - sprite_size//2, render_y - sprite_size//2, sprite_size, sprite_size)
                    screen.blit(tinted_sprite, sprite_rect.topleft)
                else:
                    # Fallback to overlay method
                    sprite_size = int(32 * 0.8)
                    sprite_rect = pg.Rect(render_x - sprite_size//2, render_y - sprite_size//2, sprite_size, sprite_size)
                    white_overlay = pg.Surface((sprite_size, sprite_size), pg.SRCALPHA)
                    white_overlay.fill((255, 255, 255, 128))
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
    
    def __init__(self, world_manager=None, spawn_point=(0, 0)):
        """Initialize the enemy manager."""
        self.enemies: List[Enemy] = []
        self.world_manager = world_manager
        self.spawn_point = pg.Vector2(spawn_point)  # Player's starting position
        
        # Spawning mechanics
        self.spawn_timer = 0.0
        self.base_spawn_interval = 1.5  # Base spawn time
        self.spawn_interval = self.base_spawn_interval
        # Remove max_enemies for infinite spawning (performance-limited only)
        
        # Time-based progression system
        self.game_time = 0.0  # Total time elapsed since game start
        self.time_spawn_multiplier = 1.0  # Spawn rate multiplier based on time
        
        # Wave system
        self.wave = 1
        self.enemies_killed = 0
        
        # Removed biome system - using wave system instead
        self.initial_spawn_grace_period = 3.0  # Prevent spawning for first 3 seconds
        self.last_player_chunk = None  # Track player's current world chunk for pre-population
        
        # Sprite sheet caching to prevent stuttering
        self.cached_sprite_path = "assets/images/Enemies/rapture1-sprite.png"
        
        # Pre-load and verify sprite sheet exists
        if not os.path.exists(self.cached_sprite_path):
            print(f"Warning: Enemy sprite sheet not found: {self.cached_sprite_path}")
            self.cached_sprite_path = None
    
    def pre_populate_area(self, player_pos: pg.Vector2, zoom_level: float = 1.0, screen_width: int = 1920, screen_height: int = 1080):
        """Pre-populate the level with a reasonable number of enemies."""
        if self.initial_spawn_grace_period > 0:
            return  # Don't pre-populate during grace period
        
        # Simple population based on level/wave (performance-limited for infinite spawning)
        target_population = min(5 + self.wave * 2, 50)  # Cap at 50 for performance
        
        # Only populate if we're significantly under target
        if len(self.enemies) < target_population // 2:
            enemies_to_spawn = target_population - len(self.enemies)
            
            for _ in range(enemies_to_spawn):
                # Simply call spawn_enemy to handle proper positioning
                self.spawn_enemy(screen_width, screen_height, player_pos, zoom_level)

    def spawn_enemy(self, screen_width: int = 1920, screen_height: int = 1080, player_pos: pg.Vector2 = None, zoom_level: float = 1.0):
        """Spawn a new enemy at world borders, moving inward toward the center."""
        if player_pos is None:
            player_pos = pg.Vector2(0, 0)
            
        # Remove max enemy limit for infinite spawning
        # (Max enemies will be controlled by performance/gameplay balance)
            
        # Get world manager boundaries
        if not self.world_manager:
            return  # Can't spawn without world manager
            
        world_bounds = self.world_manager.world_bounds  # (-1920, -1080, 1920, 1080)
        
        # Calculate camera view area to avoid on-screen spawning
        virtual_width = screen_width / zoom_level
        virtual_height = screen_height / zoom_level
        camera_left = player_pos.x - virtual_width / 2
        camera_right = player_pos.x + virtual_width / 2
        camera_top = player_pos.y - virtual_height / 2
        camera_bottom = player_pos.y + virtual_height / 2
        
        # Choose a spawn side (border) randomly: 0=left, 1=right, 2=top, 3=bottom
        spawn_side = random.randint(0, 3)
        
        # Spawn exactly at world borders (guaranteed spawning)
        spawn_x = 0
        spawn_y = 0
        
        if spawn_side == 0:  # Left border
            spawn_x = world_bounds[0] + random.uniform(50, 150)  # Near left border
            spawn_y = random.uniform(world_bounds[1], world_bounds[3])
                
        elif spawn_side == 1:  # Right border  
            spawn_x = world_bounds[2] - random.uniform(50, 150)  # Near right border
            spawn_y = random.uniform(world_bounds[1], world_bounds[3])
                
        elif spawn_side == 2:  # Top border
            spawn_x = random.uniform(world_bounds[0], world_bounds[2])
            spawn_y = world_bounds[1] + random.uniform(50, 150)  # Near top border
                
        elif spawn_side == 3:  # Bottom border
            spawn_x = random.uniform(world_bounds[0], world_bounds[2])
            spawn_y = world_bounds[3] - random.uniform(50, 150)  # Near bottom border
        
        # Additional check: ensure we're actually near the borders, not in the middle areas
        min_distance_from_edge = min(
            abs(spawn_x - world_bounds[0]),  # Distance from left edge
            abs(spawn_x - world_bounds[2]),  # Distance from right edge  
            abs(spawn_y - world_bounds[1]),  # Distance from top edge
            abs(spawn_y - world_bounds[3])   # Distance from bottom edge
        )
        if min_distance_from_edge > 200:  # If not close to any edge, skip
            return  # Ensure spawning only at actual borders
        
        # Create the enemy at border position
        # Use wave system instead of biome danger level
        wave_danger_level = min(5, self.wave)  # Cap at 5 for balance
        
        # Determine enemy type based on wave level
        enemy_types = [EnemyType.BASIC]
        if self.wave >= 2 or wave_danger_level >= 3:
            enemy_types.append(EnemyType.FAST)
        if self.wave >= 3 or wave_danger_level >= 4:
            enemy_types.append(EnemyType.TANK)
        
        enemy_type = random.choice(enemy_types)
        distance_from_center = math.sqrt(spawn_x**2 + spawn_y**2)
        
        enemy = Enemy(spawn_x, spawn_y, enemy_type, self.cached_sprite_path, 
                    self.wave, wave_danger_level, distance_from_center)
        self.enemies.append(enemy)
    
    def populate_enemies_on_start(self, screen_width: int = 1920, screen_height: int = 1080, 
                                player_pos: pg.Vector2 = None, zoom_level: float = 1.0, initial_count: int = None):
        """Pre-populate enemies at world borders when level starts."""
        if player_pos is None:
            player_pos = pg.Vector2(0, 0)
            
        # Determine how many enemies to pre-populate
        if initial_count is None:
            # Base count increases with wave level and world size
            base_count = min(15 + self.wave * 3, 35)  # 15-35 enemies based on wave
            initial_count = base_count
        
        # Clear existing enemies for fresh start
        self.enemies.clear()
        
        # Get world manager boundaries
        if not self.world_manager:
            return
            
        world_bounds = self.world_manager.world_bounds  # (-1920, -1080, 1920, 1080)
        
        # Calculate camera view area to ensure no on-screen spawning
        virtual_width = screen_width / zoom_level
        virtual_height = screen_height / zoom_level
        camera_left = player_pos.x - virtual_width / 2
        camera_right = player_pos.x + virtual_width / 2
        camera_top = player_pos.y - virtual_height / 2
        camera_bottom = player_pos.y + virtual_height / 2
        
        spawn_attempts = 0
        max_attempts = initial_count * 10  # Prevent infinite loops
        
        while len(self.enemies) < initial_count and spawn_attempts < max_attempts:
            spawn_attempts += 1
            
            # Choose spawn side randomly: 0=left, 1=right, 2=top, 3=bottom
            spawn_side = random.randint(0, 3)
            
            spawn_x = 0
            spawn_y = 0
            valid_spawn = True
            
            if spawn_side == 0:  # Left border
                spawn_x = world_bounds[0] + random.uniform(0, 300)
                spawn_y = random.uniform(world_bounds[1], world_bounds[3])
                
            elif spawn_side == 1:  # Right border  
                spawn_x = world_bounds[2] - random.uniform(0, 300)
                spawn_y = random.uniform(world_bounds[1], world_bounds[3])
                
            elif spawn_side == 2:  # Top border
                spawn_x = random.uniform(world_bounds[0], world_bounds[2])
                spawn_y = world_bounds[1] + random.uniform(0, 300)
                
            elif spawn_side == 3:  # Bottom border
                spawn_x = random.uniform(world_bounds[0], world_bounds[2])
                spawn_y = world_bounds[3] - random.uniform(0, 300)
            
            # Validate spawn position
            # 1. Not on camera (less strict for pre-population)
            if (camera_left - 200 <= spawn_x <= camera_right + 200 and 
                camera_top - 200 <= spawn_y <= camera_bottom + 200):
                continue
            
            # 3. Not too close to other enemies
            too_close = False
            for existing_enemy in self.enemies:
                distance = math.sqrt((spawn_x - existing_enemy.pos.x)**2 + (spawn_y - existing_enemy.pos.y)**2)
                if distance < 150:  # Minimum distance between enemies
                    too_close = True
                    break
            
            if too_close:
                continue
            
            # Create the enemy using wave system
            wave_danger_level = min(5, self.wave)  # Cap at 5 for balance
            
            # Determine enemy type based on wave and danger level
            enemy_types = [EnemyType.BASIC]
            if self.wave >= 2 or wave_danger_level >= 3:
                enemy_types.append(EnemyType.FAST)
            if self.wave >= 3 or wave_danger_level >= 4:
                enemy_types.append(EnemyType.TANK)
            
            enemy_type = random.choice(enemy_types)
            distance_from_center = math.sqrt(spawn_x**2 + spawn_y**2)
            
            enemy = Enemy(spawn_x, spawn_y, enemy_type, self.cached_sprite_path, 
                        self.wave, wave_danger_level, distance_from_center)
            self.enemies.append(enemy)
        
        print(f"Pre-populated {len(self.enemies)} enemies at world borders")
    
    def update(self, dt: float, player_pos: pg.Vector2, current_time: float, bullet_manager=None, 
               zoom_level: float = 1.0, screen_width: int = 1920, screen_height: int = 1080):
        """Update all enemies and handle spawning with performance optimizations."""
        # Performance limiting: Cap maximum enemy count based on hardware capability
        max_enemies = min(50, 20 + self.wave * 2)  # Gradually increase limit, cap at 50
        
        # Update game time for progression
        self.game_time += dt
        
        # Calculate time-based spawn rate multiplier (increases over time)
        # Every 30 seconds, spawn rate doubles (spawn interval halves)
        time_minutes = self.game_time / 60.0
        self.time_spawn_multiplier = 2.0 ** (time_minutes / 0.5)  # Exponential increase
        
        # Update initial spawn grace period
        if self.initial_spawn_grace_period > 0:
            self.initial_spawn_grace_period -= dt
        
        # Use wave-based danger level instead of biome
        wave_danger_level = min(5, self.wave)  # Cap at 5 for balance
        
        # Simplified spawning without biome changes - just focus on wave progression
        # Check if player has moved to a significantly new area (pre-population)
        current_chunk = (int(player_pos.x // 2000), int(player_pos.y // 2000))  # 2000x2000 pixel chunks
        if self.last_player_chunk != current_chunk:
            self.last_player_chunk = current_chunk
            # Pre-populate the new area with enemies if we've moved significantly
            if self.initial_spawn_grace_period <= 0:
                self.pre_populate_area(player_pos, zoom_level, screen_width, screen_height)
        
        # Performance optimization: Only spawn if under enemy limit
        if len(self.enemies) >= max_enemies:
            # Skip spawning entirely when at capacity
            self.spawn_timer = 0.0  # Reset spawn timer to prevent immediate spawn when enemies die
        else:
            # Wave-based spawning (simpler than biome system) with time progression
            wave_spawn_multiplier = 1.0 / (1.0 + (wave_danger_level - 1) * 0.3)  # Faster spawning in higher waves
            
            # Distance-based spawn rate scaling
            distance_from_world_spawn = player_pos.distance_to(pg.Vector2(0, 0))
            # Exponential scaling: closer to borders = exponentially faster spawning
            distance_normalized = min(distance_from_world_spawn / 3000.0, 1.0)  # Normalize to 0-1 (smaller world)
            distance_multiplier = 1.0 / (0.1 + 0.9 * (1.0 - distance_normalized) ** 2)  # Exponential curve
            
            # Combine all multipliers including time-based progression
            combined_multiplier = wave_spawn_multiplier * distance_multiplier * (1.0 / self.time_spawn_multiplier)
            self.spawn_interval = self.base_spawn_interval * max(0.01, combined_multiplier)  # Never slower than 100x normal rate
            
            # Update spawn timer (but don't spawn during grace period)
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval and self.initial_spawn_grace_period <= 0:
                self.spawn_enemy(screen_width, screen_height, player_pos, zoom_level)
                self.spawn_timer = 0.0

        # Update all enemies with performance optimizations
        enemies_to_remove = []
        collision_check_frequency = 10  # Only check collision every N frames for performance
        
        for i, enemy in enumerate(self.enemies):
            enemy.update(dt, player_pos, current_time)
            
            # Keep enemies within world bounds (with some buffer for natural movement)
            if self.world_manager:
                world_bounds = self.world_manager.world_bounds  # (-1920, -1080, 1920, 1080)
                buffer = 100  # Allow some movement beyond strict bounds
                enemy.pos.x = max(world_bounds[0] - buffer, min(world_bounds[2] + buffer, enemy.pos.x))
                enemy.pos.y = max(world_bounds[1] - buffer, min(world_bounds[3] + buffer, enemy.pos.y))
                
                # Always check if enemy is stuck in an obstacle (every frame for accuracy)
                if self.world_manager.is_position_blocked_by_map(enemy.pos.x, enemy.pos.y):
                    # Immediate extraction if stuck in obstacle
                    for radius in [30, 50]:
                        extraction_successful = False
                        for angle in [0, 90, 180, 270]:  # Only try cardinal directions
                            angle_rad = math.radians(angle)
                            test_x = enemy.pos.x + math.cos(angle_rad) * radius
                            test_y = enemy.pos.y + math.sin(angle_rad) * radius
                            
                            if not self.world_manager.is_position_blocked_by_map(test_x, test_y):
                                # Calculate direction before moving
                                direction = pg.Vector2(test_x - enemy.pos.x, test_y - enemy.pos.y)
                                enemy.pos.x = test_x
                                enemy.pos.y = test_y
                                # Simple bounce using the direction we calculated
                                if direction.length() > 0:
                                    enemy.velocity = direction.normalize() * enemy.speed
                                else:
                                    # Fallback: random direction
                                    angle = math.radians(random.uniform(0, 360))
                                    enemy.velocity = pg.Vector2(math.cos(angle), math.sin(angle)) * enemy.speed
                                extraction_successful = True
                                break
                        
                        if extraction_successful:
                            break
                
                # Performance optimization: Only do expensive obstacle avoidance for some enemies per frame
                elif i % collision_check_frequency == (int(current_time * 10) % collision_check_frequency):
                    # Simplified obstacle avoidance - less frequent and simpler
                    if enemy.velocity.length() > 0:
                        # Only check immediate ahead
                        look_ahead_distance = 35
                        velocity_normalized = enemy.velocity.normalize()
                        future_x = enemy.pos.x + velocity_normalized.x * look_ahead_distance
                        future_y = enemy.pos.y + velocity_normalized.y * look_ahead_distance
                        
                        if self.world_manager.is_position_blocked_by_map(future_x, future_y):
                            # Simple steering - try left or right turn
                            current_angle = math.atan2(enemy.velocity.y, enemy.velocity.x)
                            for turn_angle in [math.pi/2, -math.pi/2]:  # Only 90 degree turns
                                test_angle = current_angle + turn_angle
                                test_x = enemy.pos.x + math.cos(test_angle) * look_ahead_distance
                                test_y = enemy.pos.y + math.sin(test_angle) * look_ahead_distance
                                
                                if not self.world_manager.is_position_blocked_by_map(test_x, test_y):
                                    enemy.velocity.x = math.cos(test_angle) * enemy.speed
                                    enemy.velocity.y = math.sin(test_angle) * enemy.speed
                                    break
            
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

        # Remove dead enemies and drop cores
        for enemy in enemies_to_remove:
            # Drop cores when enemy dies (if world manager and core system available)
            if self.world_manager and hasattr(self.world_manager, 'core_manager'):
                # Calculate enemy type multiplier for drop rates
                type_multiplier = 1.0
                if enemy.type == EnemyType.FAST:
                    type_multiplier = 1.2
                elif enemy.type == EnemyType.TANK:
                    type_multiplier = 1.5
                    
                self.world_manager.core_manager.drop_core_from_enemy(
                    enemy.pos, enemy.wave_danger_level, type_multiplier
                )
            
            self.enemies.remove(enemy)
            
        # Update wave if enough enemies killed
        if self.enemies_killed >= self.wave * 10:
            self.wave += 1
            # Gradually increase difficulty each wave (spawn interval only - no enemy limits)
            self.base_spawn_interval = max(0.8, self.base_spawn_interval * 0.95)  # Slower reduction
        
        # Performance optimization: Cull enemies that are too far from player
        cull_distance = 4000  # Remove enemies beyond this distance
        enemies_to_cull = []
        for enemy in self.enemies:
            distance_to_player = player_pos.distance_to(enemy.pos)
            if distance_to_player > cull_distance:
                enemies_to_cull.append(enemy)
        
        # Remove culled enemies (without dropping cores to maintain balance)
        for enemy in enemies_to_cull:
            self.enemies.remove(enemy)
    
    def render(self, screen: pg.Surface, offset=(0, 0)):
        """Render all enemies."""
        for enemy in self.enemies:
            enemy.render(screen, offset)
    
    def get_enemies(self) -> List[Enemy]:
        """Get list of all active enemies."""
        return self.enemies
    
    def remove_enemy(self, enemy: Enemy):
        """Remove a specific enemy and drop cores."""
        if enemy in self.enemies:
            # Drop cores when enemy dies (if world manager and core system available)
            if self.world_manager and hasattr(self.world_manager, 'core_manager'):
                # Calculate enemy type multiplier for drop rates
                type_multiplier = 1.0
                if enemy.type == EnemyType.FAST:
                    type_multiplier = 1.2
                elif enemy.type == EnemyType.TANK:
                    type_multiplier = 1.5
                    
                self.world_manager.core_manager.drop_core_from_enemy(
                    enemy.pos, enemy.wave_danger_level, type_multiplier
                )
            
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
"""
Enhanced player class with sprite animation support.
Maintains backward compatibility with geometric rendering.
"""

import pygame as pg
import math
from typing import Tuple, Optional
import os

# Handle imports for both direct execution and module import
try:
    from src.sprite_animation import AnimatedSprite
    from src.character_config import CharacterConfig
    from src.weapon_manager import weapon_manager
except ImportError:
    try:
        from sprite_animation import AnimatedSprite
        from character_config import CharacterConfig
        from weapon_manager import weapon_manager
    except ImportError:
        # If neither works, we'll create a dummy class
        AnimatedSprite = None
        CharacterConfig = None

class AnimatedPlayer:
    """Enhanced Player class with sprite animation support."""
    
    def __init__(self, x: float, y: float, sprite_sheet_path: Optional[str] = None, 
                 frame_width: int = 32, frame_height: int = 32, audio_manager=None, 
                 character_id: str = "", character_display_name: str = "", character_config=None):
        """Initialize the player with optional sprite animation and character stats."""
        self.pos = pg.Vector2(x, y)
        self.velocity = pg.Vector2(0, 0)
        self.angle = 0.0  # Facing direction in degrees
        self.audio_manager = audio_manager
        self.character_id = character_id  # For burst sound loading
        self.character_display_name = character_display_name  # For UI display
        self.character_config = character_config  # Store config for reference
        
        # Player stats - use config if available, otherwise defaults
        if character_config and character_config.stats:
            # Apply character-specific stats from JSON config
            self.speed = character_config.stats.speed * 2.2  # Scale speed for gameplay (90 -> ~200 pixels/sec)
            self.max_health = character_config.stats.hp
            # Get weapon damage from weapon system instead of character config
            self.burst_multiplier = character_config.stats.burst_multiplier  # Points per enemy kill
            self.weapon_type = character_config.weapon_type  # Get weapon type from config
            print(f"Applied {character_display_name} stats: SPD={self.speed:.1f}, HP={self.max_health}, Burst Multiplier={self.burst_multiplier}x, Weapon={self.weapon_type}")
        else:
            # Default stats for fallback
            self.speed = 200  # pixels per second
            self.max_health = 100
            self.weapon_damage = 25  # Default bullet damage
            self.burst_multiplier = 5  # Default burst multiplier
            self.weapon_type = 'Assault Rifle'
            print(f"Using default stats for {character_display_name}")
        
        # Weapon properties - use weapon manager for weapon-specific stats
        if weapon_manager.weapon_exists(self.weapon_type):
            self.weapon_fire_rate = weapon_manager.get_fire_rate(self.weapon_type)
            self.max_ammo = weapon_manager.get_magazine_size(self.weapon_type)
            self.reload_duration = weapon_manager.get_reload_time(self.weapon_type)
            self.weapon_damage = weapon_manager.get_damage(self.weapon_type)
            print(f"Using weapon stats for {self.weapon_type}: Fire Rate={self.weapon_fire_rate}, Mag={self.max_ammo}, Reload={self.reload_duration}s, Damage={self.weapon_damage}")
        else:
            # Use default weapon values if weapon type not found
            self.weapon_fire_rate = 0.2
            print(f"No weapon data found, using default fire rate: {self.weapon_fire_rate}")
            self.max_ammo = 30
            self.reload_duration = 2.0
            self.weapon_damage = 25  # Default damage
        
        self.health = self.max_health  # Current health starts at max
        self.size = 20
        
        # BURST gauge system - now point-based (no cooldown)
        self.burst_gauge = 0.0
        self.max_burst_gauge = 100.0
        self.burst_ready = False
        
        # Burst visual overlay system
        self.burst_overlay_active = False
        self.burst_overlay_duration = 2.0  # seconds
        self.burst_overlay_timer = 0.0
        self.burst_portrait = None
        
        # Special attack system
        self.special_attack_cooldowns = {}  # Cooldowns per weapon type
        self.special_attack_active = False
        self.using_special_attack = False  # Flag for special attack bullets
        self.fire_special_attack_shot = False  # Flag to trigger immediate firing
        
        # Ammo and reload system - initialize with weapon manager values
        self.current_ammo = self.max_ammo  # Start with full magazine
        
        # Grenade launcher ammo (for weapons that support it)
        if weapon_manager.has_grenade_launcher(self.weapon_type):
            self.max_grenade_rounds = weapon_manager.get_grenade_rounds(self.weapon_type)
            self.current_grenade_rounds = self.max_grenade_rounds
            self.grenade_reload_duration = weapon_manager.get_grenade_reload_time(self.weapon_type)
        else:
            self.max_grenade_rounds = 0
            self.current_grenade_rounds = 0
            self.grenade_reload_duration = 0.0
        self.is_reloading = False
        self.reload_timer = 0.0
        self.last_reload_input = False  # Track R key state for manual reload
        self.burst_effect_particles = []
        
        # Load burst portrait if character has one
        if character_id:
            burst_path = f"assets/images/Characters/{character_id}/burst.png"
            if os.path.exists(burst_path):
                try:
                    self.burst_portrait = pg.image.load(burst_path).convert_alpha()
                    # Scale to reasonable size for overlay
                    original_size = self.burst_portrait.get_size()
                    scale_factor = min(200 / original_size[0], 200 / original_size[1])
                    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                    self.burst_portrait = pg.transform.scale(self.burst_portrait, new_size)
                except:
                    self.burst_portrait = None
        
        # Dash mechanics
        self.dash_distance = 225  # pixels to dash (increased from 150 to 1.5x range)
        self.is_dashing = False
        self.dash_duration = 0.15  # seconds
        self.dash_timer = 0.0
        self.dash_velocity = pg.Vector2(0, 0)
        self.shift_pressed = False  # Track shift key state for single-press detection
        self.e_pressed = False  # Track E key state for single-press detection
        
        # Visual properties
        self.color = (100, 150, 255)  # Light blue
        self.body_color = (80, 120, 200)
        self.dash_color = (255, 255, 255)  # White when dashing
        
        # Hit flash effect
        self.hit_flash_duration = 0.0
        self.hit_flash_timer = 0.0
        self.flash_color = (255, 50, 50)  # Red flash color
        
        # Sprite animation (optional)
        self.animated_sprite = None
        self.use_sprites = False
        
        if sprite_sheet_path and os.path.exists(sprite_sheet_path) and AnimatedSprite is not None:
            try:
                self.animated_sprite = AnimatedSprite(
                    sprite_sheet_path, x, y, frame_width, frame_height
                )
                self.use_sprites = True
                
                # Adjust collision size for scaled sprites (1/5 scale = 0.2)
                scaled_frame_size = max(frame_width, frame_height) * 0.2  # Apply same scaling
                self.size = int(scaled_frame_size // 3)  # Make collision smaller than sprite
                
                print(f"Successfully loaded character sprite: {sprite_sheet_path}")
                print(f"Collision size adjusted to: {self.size} (scaled from {scaled_frame_size})")
            except Exception as e:
                print(f"Warning: Could not load sprite sheet {sprite_sheet_path}: {e}")
                self.use_sprites = False
        elif AnimatedSprite is None:
            print("Warning: AnimatedSprite not available, using geometric rendering")
            self.use_sprites = False
        
        # Input state
        self.move_keys = {
            'up': False,
            'down': False,
            'left': False,
            'right': False
        }
    
    def get_bullet_properties(self):
        """Get bullet properties based on weapon type from weapon manager."""
        if weapon_manager.weapon_exists(self.weapon_type):
            return weapon_manager.get_bullet_properties(self.weapon_type)
        
        # Fallback properties for unknown weapon types
        weapon_props = {
            "Handgun": {"speed": 900, "size_multiplier": 0.8, "color": (255, 255, 150)},  # Fast, small, yellow
            "Assault Rifle": {"speed": 1000, "size_multiplier": 1.0, "color": (255, 200, 100)},  # Very fast, standard, orange
            "Holy Sword": {"speed": 700, "size_multiplier": 1.5, "color": (200, 200, 255)},  # Slow, large, holy blue
            "Rifle": {"speed": 800, "size_multiplier": 1.0, "color": (255, 255, 100)},  # Default values
        }
        
        return weapon_props.get(self.weapon_type, weapon_props["Rifle"])
    
    def start_reload(self, bullet_manager=None):
        """Start the reload process."""
        if not self.is_reloading:
            self.is_reloading = True
            self.reload_timer = 0.0
            print(f"Reloading... ({self.current_ammo}/{self.max_ammo})")
            
            # Reset minigun spin-up during reload - this should override any continuous fire
            if bullet_manager and self.weapon_type == "Minigun":
                bullet_manager.stop_continuous_fire(self.weapon_type)
                # Force the minigun to not be in continuous fire state during reload
                bullet_manager.is_firing_continuously = False
    
    def update_reload(self, dt: float, bullet_manager=None):
        """Update reload progress."""
        if self.is_reloading:
            self.reload_timer += dt
            if self.reload_timer >= self.reload_duration:
                # Reload complete - reload both primary and grenade ammo
                self.current_ammo = self.max_ammo
                if weapon_manager.has_grenade_launcher(self.weapon_type):
                    self.current_grenade_rounds = self.max_grenade_rounds
                self.is_reloading = False
                self.reload_timer = 0.0
                if weapon_manager.has_grenade_launcher(self.weapon_type):
                    print(f"Reload complete! Ammo: ({self.current_ammo}/{self.max_ammo}) Grenades: ({self.current_grenade_rounds}/{self.max_grenade_rounds})")
                else:
                    print(f"Reload complete! ({self.current_ammo}/{self.max_ammo})")
                
                # Clear the minigun reload reset flag when reload completes
                if bullet_manager and self.weapon_type == "Minigun":
                    bullet_manager.minigun_reload_reset = False
    
    def can_shoot(self) -> bool:
        """Check if player can shoot (has ammo and not reloading)."""
        return self.current_ammo > 0 and not self.is_reloading
    
    def use_ammo(self, bullet_manager=None):
        """Use one bullet from current ammo."""
        if self.current_ammo > 0:
            self.current_ammo -= 1
            # Auto-reload when out of ammo
            if self.current_ammo <= 0:
                self.start_reload(bullet_manager)
    
    def can_fire_grenade(self) -> bool:
        """Check if player can fire grenade (has grenade rounds and not reloading)."""
        return self.current_grenade_rounds > 0 and not self.is_reloading and weapon_manager.has_grenade_launcher(self.weapon_type)
    
    def use_grenade_round(self):
        """Use one grenade round from current grenade ammo."""
        if self.current_grenade_rounds > 0:
            self.current_grenade_rounds -= 1
            # Auto-reload when out of grenades (but not if we still have regular ammo)
            if self.current_grenade_rounds <= 0 and self.current_ammo <= 0:
                self.start_reload()
        else:
            print(f"No grenades available! Current: {self.current_grenade_rounds}/{self.max_grenade_rounds}")
    
    def handle_input(self, keys_pressed: dict, mouse_pos: Tuple[int, int], current_time: float, 
                    effects_manager=None, camera_shake_callback=None, mouse_buttons=None, bullet_manager=None):
        """Handle player input for twin-stick controls."""
        # Movement input (WASD or arrow keys)
        self.move_keys['up'] = keys_pressed[pg.K_w] or keys_pressed[pg.K_UP]
        self.move_keys['down'] = keys_pressed[pg.K_s] or keys_pressed[pg.K_DOWN]
        self.move_keys['left'] = keys_pressed[pg.K_a] or keys_pressed[pg.K_LEFT]
        self.move_keys['right'] = keys_pressed[pg.K_d] or keys_pressed[pg.K_RIGHT]
        
        # Dash input (Shift key) - only trigger once per press
        shift_currently_pressed = keys_pressed[pg.K_LSHIFT] or keys_pressed[pg.K_RSHIFT]
        if shift_currently_pressed and not self.shift_pressed:
            # Shift was just pressed (not held)
            self.try_dash(current_time, effects_manager, camera_shake_callback)
        self.shift_pressed = shift_currently_pressed
        
        # BURST skill input (E key) - only trigger once per press
        e_currently_pressed = keys_pressed[pg.K_e]
        if e_currently_pressed and not getattr(self, 'e_pressed', False):
            # E was just pressed (not held)
            if self.can_use_burst():
                self.activate_burst(effects_manager)
        self.e_pressed = e_currently_pressed
        
        # Reload input (R key) - manual reload
        r_currently_pressed = keys_pressed[pg.K_r]
        if r_currently_pressed and not self.last_reload_input:
            # R was just pressed - start manual reload if not already reloading and not full ammo
            if not self.is_reloading and self.current_ammo < self.max_ammo:
                self.start_reload(bullet_manager)
        self.last_reload_input = r_currently_pressed
        
        # Mouse aiming - calculate angle to mouse cursor
        if mouse_pos:
            dx = mouse_pos[0] - self.pos.x
            dy = mouse_pos[1] - self.pos.y
            self.angle = math.degrees(math.atan2(dy, dx))
            
        # Special attack input (Right mouse button)
        if mouse_buttons and len(mouse_buttons) > 2:
            right_mouse_pressed = mouse_buttons[2]  # Right mouse button (index 2)
            
            # SMG and Sword special attacks support continuous firing
            if self.weapon_type in ["SMG", "Sword"]:
                if right_mouse_pressed:
                    # Continuous firing for SMG and Sword special attacks
                    if self.try_special_attack(current_time):
                        self.fire_special_attack_shot = True
                else:
                    # Reset flags when right mouse is released
                    self.fire_special_attack_shot = False
                    self.using_special_attack = False  # Clear special attack mode
            else:
                # Handle special attack trigger (single press, not held) for other weapons
                if right_mouse_pressed and not getattr(self, 'right_mouse_was_pressed', False):
                    self.try_special_attack(current_time)
            
            self.right_mouse_was_pressed = right_mouse_pressed
    
    def try_special_attack(self, current_time: float):
        """Attempt to use weapon-specific special attack."""
        weapon_type = getattr(self, 'weapon_type', 'Assault Rifle')
        
        # Check cooldown for this weapon type
        if weapon_type in self.special_attack_cooldowns:
            if current_time < self.special_attack_cooldowns[weapon_type]:
                return False  # Still on cooldown
        
        # Activate special attack
        self.perform_special_attack(weapon_type, current_time)
        return True
    
    def perform_special_attack(self, weapon_type: str, current_time: float):
        """Perform weapon-specific special attack."""
        # Set cooldown based on weapon type
        from src.weapon_manager import weapon_manager
        
        # Get weapon special attack config
        weapon_config = weapon_manager.get_weapon_config(weapon_type)
        if weapon_config and 'special_attack' in weapon_config:
            cooldown = weapon_config['special_attack'].get('cooldown', 3.0)
        else:
            cooldown = self.get_special_attack_cooldown(weapon_type)
        
        self.special_attack_cooldowns[weapon_type] = current_time + cooldown
        
        # Activate special attack mode and fire immediately
        if weapon_type == "Shotgun":
            self.using_special_attack = True
            # Force a shot to be fired immediately with special attack flag
            self.fire_special_attack_shot = True
            print(f"Shotgun special attack activated - firing V-blast shots!")
        else:
            print(f"Special attack activated for {weapon_type}!")
            self.using_special_attack = True
            self.fire_special_attack_shot = True
    
    def get_special_attack_cooldown(self, weapon_type: str) -> float:
        """Get cooldown duration for weapon special attacks."""
        cooldowns = {
            'Assault Rifle': 3.0,    # Burst fire mode
            'SMG': 2.5,              # Overcharge mode
            'Sniper': 5.0,           # Piercing shot
            'Shotgun': 4.0,          # Explosive shells
            'Rocket Launcher': 6.0,  # Cluster rockets
            'Minigun': 8.0,          # Overdrive mode
            'Sword': 3.5             # Whirlwind attack
        }
        return cooldowns.get(weapon_type, 3.0)
    
    def try_dash(self, current_time: float, effects_manager=None, camera_shake_callback=None):
        """Attempt to dash if player is moving and not already dashing."""
        if not self.is_dashing and self.has_movement_input():
            # Calculate dash direction from current movement input
            dash_direction = pg.Vector2(0, 0)
            
            if self.move_keys['up']:
                dash_direction.y -= 1
            if self.move_keys['down']:
                dash_direction.y += 1
            if self.move_keys['left']:
                dash_direction.x -= 1
            if self.move_keys['right']:
                dash_direction.x += 1
            
            # Normalize for diagonal dashes
            if dash_direction.length() > 0:
                dash_direction = dash_direction.normalize()
                
                # Start dash
                self.is_dashing = True
                self.dash_timer = 0.0
                
                # Calculate dash velocity for smooth movement
                dash_speed = self.dash_distance / self.dash_duration
                self.dash_velocity = dash_direction * dash_speed
                
                # Add dash effect if effects manager is provided
                if effects_manager:
                    effects_manager.add_dash_effect(self.pos.x, self.pos.y, dash_direction)
                
                # Add slight camera shake for dash
                if camera_shake_callback:
                    camera_shake_callback(5.0, 0.2)  # Light shake for dash
    
    def has_movement_input(self) -> bool:
        """Check if player is pressing any movement keys."""
        return any(self.move_keys.values())
    
    def add_hit_flash(self):
        """Add red flash effect when player is hit - DISABLED (using screen border instead)."""
        # Disabled to prevent white flash issues - using red screen border in main.py instead
        pass
    
    def update_burst_system(self, dt: float):
        """Update the BURST gauge system."""
        # Check if gauge is full and ready
        if self.burst_gauge >= self.max_burst_gauge:
            self.burst_ready = True
    
    def add_burst_points(self, points: int = 1):
        """Add points to the BURST gauge when killing an enemy."""
        if self.burst_gauge < self.max_burst_gauge:
            # Calculate actual points based on multiplier
            actual_points = points * self.burst_multiplier
            self.burst_gauge = min(self.max_burst_gauge, self.burst_gauge + actual_points)
            
    def add_burst_charge(self):
        """Legacy method for compatibility - adds 1 point."""
        self.add_burst_points(1)
    
    def can_use_burst(self) -> bool:
        """Check if BURST ability can be used."""
        return self.burst_ready and self.burst_gauge >= self.max_burst_gauge
    
    def use_burst(self) -> bool:
        """Use BURST ability if available."""
        if self.can_use_burst():
            self.burst_gauge = 0.0
            self.burst_ready = False
            return True
        return False
    
    def activate_burst(self, effects_manager=None):
        """Activate the BURST ability with visual effects and portrait overlay."""
        if self.use_burst():
            print(f"BURST ACTIVATED! Dealing massive damage!")
            
            # Play burst sound if available
            if self.audio_manager and self.character_id:
                self.audio_manager.play_burst_sound(self.character_id)
            
            # Activate burst visual overlay
            self.burst_overlay_active = True
            self.burst_overlay_timer = 0.0
            
            # Create burst effect particles
            self.burst_effect_particles = []
            for i in range(20):  # Create 20 particles
                angle = i * (360 / 20)
                speed = 100 + (i % 3) * 50  # Varying speeds
                self.burst_effect_particles.append({
                    'angle': angle,
                    'speed': speed,
                    'life': 1.5,
                    'max_life': 1.5,
                    'size': 8 + (i % 4) * 2
                })
            
            # Add visual effect if effects manager is available
            if effects_manager:
                # Create a large explosion effect at player position with bright yellow color
                effects_manager.add_explosion(self.pos.x, self.pos.y, color=(255, 255, 0))
            
            # TODO: Add actual BURST ability effects based on character
            # For now, this is just a placeholder that resets the gauge
            return True
        return False
    
    def update_hit_flash(self, dt: float):
        """Update hit flash effect."""
        if self.hit_flash_duration > 0:
            self.hit_flash_timer += dt
            if self.hit_flash_timer >= self.hit_flash_duration:
                self.hit_flash_duration = 0.0
                self.hit_flash_timer = 0.0
    
    def _apply_hit_flash_tinting(self, surface: pg.Surface, intensity: float):
        """Apply hit flash tinting to a surface while respecting alpha channel - OPTIMIZED."""
        # Use pygame's built-in color blending for better performance
        if intensity <= 0:
            return
        
        # Create a temporary surface for blending
        overlay = pg.Surface(surface.get_size(), pg.SRCALPHA)
        overlay.fill((*self.flash_color, int(128 * intensity)))  # Semi-transparent red
        
        # Use pygame's optimized blend modes
        surface.blit(overlay, (0, 0), special_flags=pg.BLEND_ALPHA_SDL2)
    
    def update_burst_overlay(self, dt: float):
        """Update burst visual overlay and particles."""
        if self.burst_overlay_active:
            self.burst_overlay_timer += dt
            
            # Update burst particles
            for particle in self.burst_effect_particles[:]:  # Copy list for safe removal
                particle['life'] -= dt
                if particle['life'] <= 0:
                    self.burst_effect_particles.remove(particle)
            
            # Deactivate overlay after duration
            if self.burst_overlay_timer >= self.burst_overlay_duration:
                self.burst_overlay_active = False
                self.burst_overlay_timer = 0.0
                self.burst_effect_particles = []
    
    def update(self, dt: float, bullet_manager=None, world_manager=None):
        """Update player state."""
        # Update hit flash effect
        self.update_hit_flash(dt)
        
        # Update BURST system
        self.update_burst_system(dt)
        
        # Update burst overlay
        self.update_burst_overlay(dt)
        
        # Update reload system
        self.update_reload(dt, bullet_manager)
        
        # Update dash state
        if self.is_dashing:
            self.dash_timer += dt
            if self.dash_timer >= self.dash_duration:
                # End dash
                self.is_dashing = False
                self.dash_timer = 0.0
                self.dash_velocity = pg.Vector2(0, 0)
        
        # Calculate movement vector
        if self.is_dashing:
            # Use dash velocity during dash
            self.velocity = self.dash_velocity
        else:
            # Normal movement
            movement = pg.Vector2(0, 0)
            
            if self.move_keys['up']:
                movement.y -= 1
            if self.move_keys['down']:
                movement.y += 1
            if self.move_keys['left']:
                movement.x -= 1
            if self.move_keys['right']:
                movement.x += 1
            
            # Normalize diagonal movement
            if movement.length() > 0:
                movement = movement.normalize()
                # Apply speed
                effective_speed = self.speed
                self.velocity = movement * effective_speed
            else:
                self.velocity = pg.Vector2(0, 0)
        
        # Calculate potential new position
        potential_pos = self.pos + self.velocity * dt
        
        # Check for map collisions and handle them
        if world_manager:
            # Try to move to the new position
            # Check X movement first - check multiple points around the player's perimeter
            temp_pos = pg.Vector2(potential_pos.x, self.pos.y)
            can_move_x = True
            
            # Check collision at multiple points around the player's circle
            for angle in [0, 90, 180, 270]:  # Check cardinal directions
                check_angle = math.radians(angle)
                check_x = temp_pos.x + math.cos(check_angle) * self.size
                check_y = temp_pos.y + math.sin(check_angle) * self.size
                if world_manager.is_position_blocked_by_map(check_x, check_y):
                    can_move_x = False
                    break
            
            if can_move_x:
                self.pos.x = temp_pos.x
            
            # Then check Y movement
            temp_pos = pg.Vector2(self.pos.x, potential_pos.y)
            can_move_y = True
            
            # Check collision at multiple points around the player's circle
            for angle in [0, 90, 180, 270]:  # Check cardinal directions
                check_angle = math.radians(angle)
                check_x = temp_pos.x + math.cos(check_angle) * self.size
                check_y = temp_pos.y + math.sin(check_angle) * self.size
                if world_manager.is_position_blocked_by_map(check_x, check_y):
                    can_move_y = False
                    break
            
            if can_move_y:
                self.pos.y = temp_pos.y
        else:
            # No collision checking, just update position
            self.pos = potential_pos
        
        # Keep player within world boundaries (3840x2160 rectangular world: -1920 to +1920 width, -1080 to +1080 height)
        world_min_x, world_max_x = -1920, 1920
        world_min_y, world_max_y = -1080, 1080
        self.pos.x = max(world_min_x + self.size, min(world_max_x - self.size, self.pos.x))
        self.pos.y = max(world_min_y + self.size, min(world_max_y - self.size, self.pos.y))
        
        # Update sprite animation if using sprites
        if self.use_sprites and self.animated_sprite:
            self.animated_sprite.set_position(self.pos.x, self.pos.y)
            # Pass the facing angle (converted to radians) instead of using movement direction
            facing_angle_rad = math.radians(self.angle)
            self.animated_sprite.update(dt, self.velocity if not self.is_dashing else None, facing_angle_rad)
    
    def get_gun_tip_position(self) -> pg.Vector2:
        """Get the position where bullets should spawn from."""
        # Calculate the tip of the "gun" based on facing direction
        gun_length = self.size + 60  # Increased from 35 to 60 for better muzzle flash separation
        angle_rad = math.radians(self.angle)
        
        tip_x = self.pos.x + math.cos(angle_rad) * gun_length
        tip_y = self.pos.y + math.sin(angle_rad) * gun_length
        
        return pg.Vector2(tip_x, tip_y)
    
    def get_gun_tip_position_at_angle(self, angle: float) -> pg.Vector2:
        """Get the position where bullets should spawn from at a specific angle."""
        # Calculate the tip of the "gun" based on specified angle
        gun_length = self.size + 60  # Same as regular gun tip calculation
        angle_rad = math.radians(angle)
        
        tip_x = self.pos.x + math.cos(angle_rad) * gun_length
        tip_y = self.pos.y + math.sin(angle_rad) * gun_length
        
        return pg.Vector2(tip_x, tip_y)
    
    def render(self, screen: pg.Surface, current_time: float = 0.0, offset=(0, 0)):
        """Render the player."""
        # Apply camera offset
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        if self.use_sprites and self.animated_sprite:
            # Render sprite animation
            self.animated_sprite.render(screen, offset)
            
            # Apply hit flash effect by tinting the sprite while respecting alpha
            if self.hit_flash_duration > 0:
                flash_intensity = 1.0 - (self.hit_flash_timer / self.hit_flash_duration)
                if flash_intensity > 0:
                    # Get the current sprite surface from the animation
                    sprite_surface = self.animated_sprite.animation.get_current_frame()
                    if sprite_surface:
                        # Get scaled dimensions
                        scaled_width, scaled_height = self.animated_sprite.animation.get_scaled_dimensions()
                        
                        # Create a copy of the sprite surface to apply tinting
                        tinted_sprite = sprite_surface.copy()
                        
                        # Apply per-pixel tinting that respects alpha
                        self._apply_hit_flash_tinting(tinted_sprite, flash_intensity)
                        
                        # Scale if necessary
                        if (scaled_width != tinted_sprite.get_width() or 
                            scaled_height != tinted_sprite.get_height()):
                            tinted_sprite = pg.transform.scale(tinted_sprite, (scaled_width, scaled_height))
                        
                        overlay_x = render_x - scaled_width // 2
                        overlay_y = render_y - scaled_height // 2
                        screen.blit(tinted_sprite, (overlay_x, overlay_y))
                    else:
                        # Fallback to old method if can't get sprite surface
                        scaled_width, scaled_height = self.animated_sprite.animation.get_scaled_dimensions()
                        overlay = pg.Surface((scaled_width, scaled_height), pg.SRCALPHA)
                        overlay.set_alpha(int(100 * flash_intensity))
                        overlay.fill(self.flash_color)
                        
                        overlay_x = render_x - scaled_width // 2
                        overlay_y = render_y - scaled_height // 2
                        screen.blit(overlay, (overlay_x, overlay_y))
        else:
            # Fallback to geometric rendering
            self._render_geometric(screen, render_x, render_y)
        
        # Draw health bar
        self._render_health_bar(screen, render_x, render_y)
        
        # Draw ammo bar
        self._render_ammo_bar(screen, render_x, render_y)
        
        # Draw character name above health bar
        self._render_character_name(screen, render_x, render_y)
        
        # Draw BURST gauge
        self._render_burst_gauge(screen, render_x, render_y)
        
        # Draw burst overlay if active
        if self.burst_overlay_active:
            self._render_burst_overlay(screen)
    
    def _render_geometric(self, screen: pg.Surface, render_x: int, render_y: int):
        """Render player using geometric shapes (fallback)."""
        # Choose colors based on state
        body_color = self.dash_color if self.is_dashing else self.body_color
        outline_color = (255, 255, 255) if self.is_dashing else self.color
        
        # Apply hit flash effect
        if self.hit_flash_duration > 0:
            # Flash red when hit
            flash_intensity = 1.0 - (self.hit_flash_timer / self.hit_flash_duration)
            body_color = (
                int(self.flash_color[0] * flash_intensity + body_color[0] * (1 - flash_intensity)),
                int(self.flash_color[1] * flash_intensity + body_color[1] * (1 - flash_intensity)),
                int(self.flash_color[2] * flash_intensity + body_color[2] * (1 - flash_intensity))
            )
        
        # Draw player body (circle)
        pg.draw.circle(screen, body_color, (render_x, render_y), self.size)
        pg.draw.circle(screen, outline_color, (render_x, render_y), self.size, 2)
        
        # Draw dash trail effect when dashing
        if self.is_dashing:
            # Create a trailing effect
            trail_alpha = 0.3
            for i in range(3):
                trail_size = self.size - (i * 3)
                if trail_size > 0:
                    trail_surface = pg.Surface((trail_size * 2, trail_size * 2), pg.SRCALPHA)
                    trail_color = (*outline_color, int(255 * trail_alpha * (1 - i * 0.3)))
                    pg.draw.circle(trail_surface, trail_color, (trail_size, trail_size), trail_size)
                    screen.blit(trail_surface, (render_x - trail_size, render_y - trail_size))
    
    def _render_gun_barrel(self, screen: pg.Surface, render_x: int, render_y: int):
        """Render a V-shaped aiming arrow around the player sprite."""
        angle_rad = math.radians(self.angle)
        
        # Calculate distance from player center (circles around sprite)
        arrow_distance = self.size + 25  # Further out from sprite
        
        # Main arrow tip position
        tip_x = render_x + math.cos(angle_rad) * arrow_distance
        tip_y = render_y + math.sin(angle_rad) * arrow_distance
        
        # Calculate V-shape arrow points
        arrow_length = 20
        arrow_width = math.radians(25)  # 25 degree angle for V-shape
        
        # Left wing of the V
        left_angle = angle_rad + arrow_width
        left_x = tip_x - math.cos(left_angle) * arrow_length
        left_y = tip_y - math.sin(left_angle) * arrow_length
        
        # Right wing of the V
        right_angle = angle_rad - arrow_width
        right_x = tip_x - math.cos(right_angle) * arrow_length
        right_y = tip_y - math.sin(right_angle) * arrow_length
        
        # Arrow colors - more visually impressive
        arrow_color = (255, 255, 100) if self.is_dashing else (255, 200, 100)  # Golden/yellow
        arrow_outline = (255, 255, 255)
        
        # Draw V-shaped arrow with outline for better visibility
        # Outline (thicker, white)
        pg.draw.line(screen, arrow_outline, (tip_x, tip_y), (left_x, left_y), 5)
        pg.draw.line(screen, arrow_outline, (tip_x, tip_y), (right_x, right_y), 5)
        
        # Main arrow (thinner, colored)
        pg.draw.line(screen, arrow_color, (tip_x, tip_y), (left_x, left_y), 3)
        pg.draw.line(screen, arrow_color, (tip_x, tip_y), (right_x, right_y), 3)
        
        # Optional: Add a small circle at the arrow tip for better visibility
        pg.draw.circle(screen, arrow_color, (int(tip_x), int(tip_y)), 3)
        pg.draw.circle(screen, arrow_outline, (int(tip_x), int(tip_y)), 3, 1)
    
    def _render_health_bar(self, screen: pg.Surface, render_x: int, render_y: int):
        """Render the health bar above the player - always visible."""
        bar_width = 70  # Slightly wider
        bar_height = 10  # Taller than BURST gauge
        bar_x = render_x - bar_width // 2
        bar_y = render_y - self.size - 40  # Higher up to avoid overlapping sprite
        
        # Background
        pg.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        
        # Health bar - always green as requested
        health_width = (self.health / self.max_health) * bar_width
        health_color = (0, 255, 0)  # Always green
        pg.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Border
        pg.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def _render_ammo_bar(self, screen: pg.Surface, render_x: int, render_y: int):
        """Render the ammo bar under the player sprite showing current bullets and reload progress."""
        bar_width = 60
        bar_height = 8
        bar_x = render_x - bar_width // 2
        bar_y = render_y + self.size + 10  # Below the player sprite
        
        # Special handling for sniper rifle (special ammo)
        is_sniper = hasattr(self, 'weapon_type') and self.weapon_type == "Sniper"
        
        # Background
        bg_color = (60, 60, 80) if is_sniper else (40, 40, 40)
        pg.draw.rect(screen, bg_color, (bar_x, bar_y, bar_width, bar_height))
        
        if self.is_reloading:
            # Show reload progress
            reload_progress = min(1.0, self.reload_timer / self.reload_duration)
            reload_width = reload_progress * bar_width
            
            if is_sniper:
                # Blue reload color for sniper
                import math
                pulse = abs(math.sin(self.reload_timer * 8)) * 50
                reload_color = (int(pulse), 150, 255)
                pg.draw.rect(screen, reload_color, (bar_x, bar_y, reload_width, bar_height))
                # Add glow effect for sniper reload
                glow_color = (50, 100, 200, 128)
                glow_rect = pg.Rect(bar_x - 2, bar_y - 2, reload_width + 4, bar_height + 4)
                pg.draw.rect(screen, glow_color[:3], glow_rect, 2)
            else:
                # Yellow color during reload for other weapons
                import math
                pulse = abs(math.sin(self.reload_timer * 8)) * 50
                reload_color = (255, 255, int(pulse))
                pg.draw.rect(screen, reload_color, (bar_x, bar_y, reload_width, bar_height))
        else:
            # Show current ammo
            ammo_ratio = self.current_ammo / self.max_ammo if self.max_ammo > 0 else 0
            ammo_width = ammo_ratio * bar_width
            
            if is_sniper:
                # Blue ammo bar for sniper (special ammo)
                import math, time
                glow_pulse = abs(math.sin(time.time() * 3)) * 0.3 + 0.7  # Gentle glow pulse
                base_blue = int(255 * glow_pulse)
                base_cyan = int(150 * glow_pulse)
                
                if ammo_ratio > 0.6:
                    ammo_color = (base_cyan, base_cyan, base_blue)    # Bright blue - plenty of special ammo
                elif ammo_ratio > 0.3:
                    ammo_color = (base_cyan // 2, base_cyan, base_blue)  # Medium blue
                else:
                    ammo_color = (100, base_cyan // 2, base_blue)    # Darker blue - low special ammo
                
                pg.draw.rect(screen, ammo_color, (bar_x, bar_y, ammo_width, bar_height))
                
                # Add outer glow effect for sniper
                glow_intensity = int(100 * glow_pulse)
                glow_color = (30, 50, glow_intensity)
                glow_rect = pg.Rect(bar_x - 1, bar_y - 1, ammo_width + 2, bar_height + 2)
                pg.draw.rect(screen, glow_color, glow_rect, 1)
            else:
                # Normal color progression for other weapons
                if ammo_ratio > 0.6:
                    ammo_color = (0, 255, 0)    # Green - plenty of ammo
                elif ammo_ratio > 0.3:
                    ammo_color = (255, 255, 0)  # Yellow - medium ammo
                else:
                    ammo_color = (255, 0, 0)    # Red - low ammo
                
                pg.draw.rect(screen, ammo_color, (bar_x, bar_y, ammo_width, bar_height))
        
        # Border
        border_color = (120, 150, 200) if is_sniper else (100, 100, 100)
        pg.draw.rect(screen, border_color, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Ammo text
        font = pg.font.Font(None, 20)
        if self.is_reloading:
            text_content = "RELOADING"
            text_color = (150, 200, 255) if is_sniper else (255, 255, 255)
        else:
            if is_sniper:
                text_content = f"{self.current_ammo}/{self.max_ammo} SPECIAL"
                text_color = (150, 200, 255)
            else:
                text_content = f"{self.current_ammo}/{self.max_ammo}"
                text_color = (255, 255, 255)
        
        ammo_text = font.render(text_content, True, text_color)
        
        text_rect = ammo_text.get_rect()
        text_x = render_x - text_rect.width // 2
        text_y = bar_y + bar_height + 2
        screen.blit(ammo_text, (text_x, text_y))
        
        # Display grenade ammo if this weapon has grenade launcher
        if (hasattr(self, 'max_grenade_rounds') and self.max_grenade_rounds > 0 and 
            hasattr(self, 'weapon_type') and weapon_manager.has_grenade_launcher(self.weapon_type)):
            
            # Grenade ammo bar (smaller, positioned below regular ammo)
            grenade_bar_width = 40
            grenade_bar_height = 6
            grenade_bar_x = render_x - grenade_bar_width // 2
            grenade_bar_y = text_y + text_rect.height + 5
            
            # Background
            pg.draw.rect(screen, (40, 30, 20), (grenade_bar_x, grenade_bar_y, grenade_bar_width, grenade_bar_height))
            
            # Grenade ammo fill
            if self.max_grenade_rounds > 0:
                grenade_ratio = self.current_grenade_rounds / self.max_grenade_rounds
                grenade_width = grenade_ratio * grenade_bar_width
                
                # Color based on grenade ammo level
                if grenade_ratio > 0.6:
                    grenade_color = (255, 165, 0)   # Orange - plenty of grenades
                elif grenade_ratio > 0.3:
                    grenade_color = (255, 100, 0)   # Dark orange - medium grenades
                else:
                    grenade_color = (200, 60, 0)    # Red-orange - low grenades
                
                pg.draw.rect(screen, grenade_color, (grenade_bar_x, grenade_bar_y, grenade_width, grenade_bar_height))
            
            # Border
            pg.draw.rect(screen, (150, 100, 50), (grenade_bar_x, grenade_bar_y, grenade_bar_width, grenade_bar_height), 1)
            
            # Grenade text
            grenade_font = pg.font.Font(None, 16)  # Smaller font
            grenade_text_content = f"G: {self.current_grenade_rounds}/{self.max_grenade_rounds}"
            grenade_text_color = (255, 180, 100)
            
            grenade_text = grenade_font.render(grenade_text_content, True, grenade_text_color)
            grenade_text_rect = grenade_text.get_rect()
            grenade_text_x = render_x - grenade_text_rect.width // 2
            grenade_text_y = grenade_bar_y + grenade_bar_height + 2
            screen.blit(grenade_text, (grenade_text_x, grenade_text_y))
    
    def _render_burst_gauge(self, screen: pg.Surface, render_x: int, render_y: int):
        """Render the BURST gauge below the health bar."""
        bar_width = 70  # Wider than before, same as health bar
        bar_height = 8   # Taller than before but shorter than health bar
        bar_x = render_x - bar_width // 2
        bar_y = render_y - self.size - 25   # Below health bar with proper spacing
        
        # Background
        pg.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # BURST gauge fill
        burst_width = (self.burst_gauge / self.max_burst_gauge) * bar_width
        
        # Color changes based on readiness
        if self.burst_ready and self.can_use_burst():
            # Ready to use - bright pulsing yellow/gold
            import time
            pulse = (math.sin(time.time() * 8) + 1) * 0.5  # Pulse between 0 and 1
            burst_color = (255, int(255 * pulse + 200 * (1 - pulse)), 0)  # Pulsing yellow-gold
        else:
            # Filling up - yellow
            burst_color = (255, 255, 0)
        
        if burst_width > 0:
            pg.draw.rect(screen, burst_color, (bar_x, bar_y, burst_width, bar_height))
        
        # Border
        pg.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def _render_character_name(self, screen: pg.Surface, render_x: int, render_y: int):
        """Render character name above the health bar."""
        if hasattr(self, 'character_display_name') and self.character_display_name:
            font = pg.font.Font(None, 24)
            name_text = font.render(self.character_display_name, True, (255, 255, 255))
            text_rect = name_text.get_rect()
            text_x = render_x - text_rect.width // 2
            text_y = render_y - self.size - 65  # Above health bar
            
            # Background for better readability
            bg_rect = text_rect.copy()
            bg_rect.x = text_x - 2
            bg_rect.y = text_y - 2
            bg_rect.width += 4
            bg_rect.height += 4
            pg.draw.rect(screen, (0, 0, 0, 128), bg_rect)
            
            screen.blit(name_text, (text_x, text_y))
    
    def _render_burst_overlay(self, screen: pg.Surface):
        """Render burst visual overlay with character portrait and effects."""
        if not self.burst_overlay_active:
            return
            
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Calculate overlay progress (0.0 to 1.0)
        progress = self.burst_overlay_timer / self.burst_overlay_duration
        
        # Fade effect - stronger at start and end
        if progress < 0.3:
            alpha = int(255 * (progress / 0.3))
        elif progress > 0.7:
            alpha = int(255 * ((1.0 - progress) / 0.3))
        else:
            alpha = 255
        
        # Create semi-transparent overlay with anime sci-fi colors
        overlay = pg.Surface((screen_width, screen_height))
        overlay.set_alpha(alpha // 4)  # Subtle background tint
        overlay.fill((0, 255, 255))  # Cyan tint
        screen.blit(overlay, (0, 0))
        
        # Draw burst particles - optimized
        for particle in self.burst_effect_particles:
            life_progress = 1.0 - (particle['life'] / particle['max_life'])
            
            # Calculate particle position
            angle_rad = math.radians(particle['angle'])
            distance = particle['speed'] * life_progress
            p_x = screen_width // 2 + math.cos(angle_rad) * distance
            p_y = screen_height // 2 + math.sin(angle_rad) * distance
            
            # Particle color and size fade
            particle_alpha = int(255 * (1.0 - life_progress))
            particle_size = max(1, particle['size'] * (1.0 - life_progress))
            
            # Neon particle colors
            colors = [(0, 255, 255), (255, 0, 255), (255, 255, 0)]  # Cyan, Magenta, Yellow
            color = colors[int(particle['angle']) % len(colors)]
            
            # Simplified particle rendering - just draw circles directly instead of surface creation
            if particle_size > 0:
                pos = (int(p_x), int(p_y))
                # Main particle
                pg.draw.circle(screen, color, pos, int(particle_size))
                # Simple glow effect with one additional circle
                if particle_size > 2:
                    glow_color = (color[0] // 2, color[1] // 2, color[2] // 2)
                    pg.draw.circle(screen, glow_color, pos, int(particle_size + 2))
        
        # Draw character portrait if available
        if self.burst_portrait and progress < 0.6:  # Show portrait for first 60% of duration
            portrait_alpha = int(255 * (1.0 - progress / 0.6))
            
            # Position portrait (center-right area)
            portrait_x = screen_width - self.burst_portrait.get_width() - 50
            portrait_y = (screen_height - self.burst_portrait.get_height()) // 2
            
            # Apply pulsing scale effect
            pulse = 1.0 + 0.1 * math.sin(self.burst_overlay_timer * 8)
            scaled_portrait = pg.transform.scale(
                self.burst_portrait,
                (int(self.burst_portrait.get_width() * pulse),
                 int(self.burst_portrait.get_height() * pulse))
            )
            
            # Neon border around portrait
            border_rect = pg.Rect(portrait_x - 10, portrait_y - 10,
                                scaled_portrait.get_width() + 20,
                                scaled_portrait.get_height() + 20)
            
            # Draw glowing border
            for i in range(5):
                border_color = (0, 255, 255, 100 - i * 20)  # Cyan glow
                expanded_rect = border_rect.inflate(i * 4, i * 4)
                pg.draw.rect(screen, border_color, expanded_rect, 3)
            
            # Apply alpha to portrait
            scaled_portrait.set_alpha(portrait_alpha)
            screen.blit(scaled_portrait, (portrait_x, portrait_y))
            
            # Draw burst text effect
            font = pg.font.Font(None, 72)
            burst_text = font.render("BURST!", True, (255, 255, 0))  # Electric yellow
            text_rect = burst_text.get_rect()
            text_x = 50
            text_y = screen_height // 2 - text_rect.height // 2
            
            # Glowing text effect
            for i in range(5):
                glow_text = font.render("BURST!", True, (255, 255, 0, 150 - i * 30))
                screen.blit(glow_text, (text_x + i, text_y + i))
            
            burst_text.set_alpha(portrait_alpha)
            screen.blit(burst_text, (text_x, text_y))
    
    def take_damage(self, damage: int):
        """Apply damage to the player."""
        self.health = max(0, self.health - damage)
        
    def is_alive(self) -> bool:
        """Check if player is still alive."""
        return self.health > 0
    
    def get_rect(self) -> pg.Rect:
        """Get collision rectangle for the player."""
        return pg.Rect(self.pos.x - self.size, self.pos.y - self.size, 
                      self.size * 2, self.size * 2)
    
    def get_gun_tip_position(self) -> pg.Vector2:
        """Get the position of the gun tip for bullet spawning."""
        gun_length = 60  # Increased from 35 for better muzzle flash separation from sprite
        gun_tip_x = self.pos.x + math.cos(math.radians(self.angle)) * gun_length
        gun_tip_y = self.pos.y + math.sin(math.radians(self.angle)) * gun_length
        return pg.Vector2(gun_tip_x, gun_tip_y)
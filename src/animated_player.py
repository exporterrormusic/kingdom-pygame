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
            self.burst_gauge_fill_rate = character_config.stats.burst_gen / 2.0  # Scale for balanced gameplay
            self.weapon_type = character_config.weapon_type  # Get weapon type from config
            print(f"Applied {character_display_name} stats: SPD={self.speed:.1f}, HP={self.max_health}, Burst Rate={self.burst_gauge_fill_rate}, Weapon={self.weapon_type}")
        else:
            # Default stats for fallback
            self.speed = 200  # pixels per second
            self.max_health = 100
            self.weapon_damage = 25  # Default bullet damage
            self.burst_gauge_fill_rate = 15.0  # Points per successful hit
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
        
        # BURST gauge system
        self.burst_gauge = 0.0
        self.max_burst_gauge = 100.0
        self.burst_ready = False
        self.burst_cooldown = 0.0
        self.max_burst_cooldown = 15.0  # Time before burst can be used again
        
        # Burst visual overlay system
        self.burst_overlay_active = False
        self.burst_overlay_duration = 2.0  # seconds
        self.burst_overlay_timer = 0.0
        self.burst_portrait = None
        
        # COVER shield system
        self.shield_active = False
        self.shield_pos = pg.Vector2(0, 0)  # Shield position in world coordinates
        self.shield_width = 12  # Shield thickness
        self.shield_height = 80  # Much taller shield
        self.shield_distance = 70  # Increased distance from player to avoid clipping
        self.shield_speed_reduction = 0.5  # 50% speed reduction when shield is active
        self.shield_color = (100, 150, 255)  # Light blue color
        self.shield_border_color = (50, 100, 200)  # Darker blue border
        self.shield_curve_radius = 15  # Curve radius for shield shape
        
        # Ammo and reload system - initialize with weapon manager values
        self.current_ammo = self.max_ammo  # Start with full magazine
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
                # Reload complete
                self.current_ammo = self.max_ammo
                self.is_reloading = False
                self.reload_timer = 0.0
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
            
        # COVER shield input (Right mouse button)
        if mouse_buttons and len(mouse_buttons) > 2:
            self.shield_active = mouse_buttons[2]  # Right mouse button (index 2)
            
            # Update shield position when active
            if self.shield_active:
                self.update_shield_position()
    
    def update_shield_position(self):
        """Update shield position based on player position and facing direction."""
        # Position shield on a circle around the player at fixed distance
        angle_rad = math.radians(self.angle)
        shield_offset_x = math.cos(angle_rad) * self.shield_distance
        shield_offset_y = math.sin(angle_rad) * self.shield_distance
        
        # Shield position on the circle around player
        self.shield_pos.x = self.pos.x + shield_offset_x
        self.shield_pos.y = self.pos.y + shield_offset_y
    
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
        """Add red flash effect when player is hit."""
        self.hit_flash_duration = 0.3  # Flash duration in seconds
        self.hit_flash_timer = 0.0
    
    def update_burst_system(self, dt: float):
        """Update the BURST gauge system."""
        # Update cooldown
        if self.burst_cooldown > 0:
            self.burst_cooldown -= dt
            if self.burst_cooldown <= 0:
                self.burst_ready = True
        
        # Check if gauge is full and ready
        if self.burst_gauge >= self.max_burst_gauge and self.burst_cooldown <= 0:
            self.burst_ready = True
    
    def add_burst_charge(self):
        """Add charge to the BURST gauge when hitting an enemy."""
        if self.burst_gauge < self.max_burst_gauge:
            self.burst_gauge = min(self.max_burst_gauge, self.burst_gauge + self.burst_gauge_fill_rate)
    
    def can_use_burst(self) -> bool:
        """Check if BURST ability can be used."""
        return self.burst_ready and self.burst_gauge >= self.max_burst_gauge and self.burst_cooldown <= 0
    
    def use_burst(self) -> bool:
        """Use BURST ability if available."""
        if self.can_use_burst():
            self.burst_gauge = 0.0
            self.burst_ready = False
            self.burst_cooldown = self.max_burst_cooldown
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
    
    def update(self, dt: float, bullet_manager=None):
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
                # Apply shield speed reduction if shield is active
                effective_speed = self.speed
                if self.shield_active:
                    effective_speed = self.speed * (1 - self.shield_speed_reduction)
                self.velocity = movement * effective_speed
            else:
                self.velocity = pg.Vector2(0, 0)
        
        # Update position
        self.pos += self.velocity * dt
        
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
    
    def render(self, screen: pg.Surface, current_time: float = 0.0, offset=(0, 0)):
        """Render the player."""
        # Apply camera offset
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        if self.use_sprites and self.animated_sprite:
            # Render sprite animation
            self.animated_sprite.render(screen, offset)
            
            # Apply hit flash effect by tinting the sprite
            if self.hit_flash_duration > 0:
                flash_intensity = 1.0 - (self.hit_flash_timer / self.hit_flash_duration)
                if flash_intensity > 0:
                    # Get scaled dimensions
                    scaled_width, scaled_height = self.animated_sprite.animation.get_scaled_dimensions()
                    
                    # Create a red overlay surface
                    overlay = pg.Surface((scaled_width, scaled_height))
                    overlay.set_alpha(int(100 * flash_intensity))
                    overlay.fill(self.flash_color)
                    
                    overlay_x = render_x - scaled_width // 2
                    overlay_y = render_y - scaled_height // 2
                    screen.blit(overlay, (overlay_x, overlay_y))
        else:
            # Fallback to geometric rendering
            self._render_geometric(screen, render_x, render_y)
        
        # Draw shield if active
        if self.shield_active:
            self._render_shield(screen, offset)
        
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
        
        # Background
        pg.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        if self.is_reloading:
            # Show reload progress
            reload_progress = min(1.0, self.reload_timer / self.reload_duration)
            reload_width = reload_progress * bar_width
            # Yellow color during reload
            pg.draw.rect(screen, (255, 255, 0), (bar_x, bar_y, reload_width, bar_height))
            
            # Add pulsing effect during reload
            import math
            pulse = abs(math.sin(self.reload_timer * 8)) * 50  # Pulsing intensity
            reload_color = (255, 255, int(pulse))
            pg.draw.rect(screen, reload_color, (bar_x, bar_y, reload_width, bar_height))
        else:
            # Show current ammo
            ammo_ratio = self.current_ammo / self.max_ammo if self.max_ammo > 0 else 0
            ammo_width = ammo_ratio * bar_width
            
            # Color based on ammo level
            if ammo_ratio > 0.6:
                ammo_color = (0, 255, 0)    # Green - plenty of ammo
            elif ammo_ratio > 0.3:
                ammo_color = (255, 255, 0)  # Yellow - medium ammo
            else:
                ammo_color = (255, 0, 0)    # Red - low ammo
            
            pg.draw.rect(screen, ammo_color, (bar_x, bar_y, ammo_width, bar_height))
        
        # Border
        pg.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Ammo text
        font = pg.font.Font(None, 20)
        if self.is_reloading:
            ammo_text = font.render("RELOADING", True, (255, 255, 255))
        else:
            ammo_text = font.render(f"{self.current_ammo}/{self.max_ammo}", True, (255, 255, 255))
        
        text_rect = ammo_text.get_rect()
        text_x = render_x - text_rect.width // 2
        text_y = bar_y + bar_height + 2
        screen.blit(ammo_text, (text_x, text_y))
    
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
        elif self.burst_cooldown > 0:
            # In cooldown - dim red
            burst_color = (100, 50, 50)
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
        
        # Draw burst particles
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
            
            # Draw particle with glow effect
            for i in range(3):
                glow_size = particle_size + i * 2
                glow_alpha = particle_alpha // (i + 1)
                glow_color = (*color, glow_alpha)
                
                if glow_size > 0 and glow_alpha > 0:
                    particle_surf = pg.Surface((glow_size * 2, glow_size * 2), pg.SRCALPHA)
                    pg.draw.circle(particle_surf, glow_color, (glow_size, glow_size), int(glow_size))
                    screen.blit(particle_surf, (p_x - glow_size, p_y - glow_size))
        
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
    
    def _render_shield(self, screen: pg.Surface, offset=(0, 0)):
        """Render the curved, rotated shield when active."""
        if not self.shield_active:
            return
            
        # Apply screen offset
        shield_x = self.shield_pos.x - offset[0]
        shield_y = self.shield_pos.y - offset[1]
        
        # Shield should face outward from the player's position
        # Calculate the angle from player to shield position
        dx = self.shield_pos.x - self.pos.x
        dy = self.shield_pos.y - self.pos.y
        radius_angle = math.degrees(math.atan2(dy, dx))
        
        # Shield faces outward (same direction as the radius from player to shield)
        shield_angle = radius_angle
        shield_angle_rad = math.radians(shield_angle)
        
        # Create curved shield using multiple segments
        self._draw_curved_shield(screen, shield_x, shield_y, shield_angle_rad)
    
    def _draw_curved_shield(self, screen: pg.Surface, center_x: float, center_y: float, angle: float):
        """Draw a curved shield using arc segments."""
        import pygame as pg
        
        # Shield dimensions
        half_height = self.shield_height // 2
        curve_offset = self.shield_curve_radius
        
        # The shield should face the same direction as the radius (not perpendicular)
        # Remove the 90-degree rotation to fix the orientation
        perpendicular_angle = angle  # Use the radius angle directly
        
        # Calculate shield corner points relative to center, then rotate them
        # Create a curved shield by drawing an arc and connecting lines
        
        # Points for the shield curve (before rotation)
        shield_points = []
        
        # Create arc points for the curved front face
        num_arc_points = 8
        for i in range(num_arc_points + 1):
            # Create arc from -90 to +90 degrees relative to shield orientation
            arc_angle = math.radians(-90 + (180 * i / num_arc_points))
            arc_x = curve_offset * math.cos(arc_angle)
            arc_y = (half_height * 0.8) * math.sin(arc_angle)  # Slightly flattened arc
            
            # Rotate the point by the perpendicular angle (shield orientation)
            rotated_x = arc_x * math.cos(perpendicular_angle) - arc_y * math.sin(perpendicular_angle)
            rotated_y = arc_x * math.sin(perpendicular_angle) + arc_y * math.cos(perpendicular_angle)
            
            shield_points.append((center_x + rotated_x, center_y + rotated_y))
        
        # Add back edge points to complete the shield
        # Back left point
        back_x = -self.shield_width
        back_y = -half_height
        rotated_x = back_x * math.cos(perpendicular_angle) - back_y * math.sin(perpendicular_angle)
        rotated_y = back_x * math.sin(perpendicular_angle) + back_y * math.cos(perpendicular_angle)
        shield_points.append((center_x + rotated_x, center_y + rotated_y))
        
        # Back right point
        back_x = -self.shield_width
        back_y = half_height
        rotated_x = back_x * math.cos(perpendicular_angle) - back_y * math.sin(perpendicular_angle)
        rotated_y = back_x * math.sin(perpendicular_angle) + back_y * math.cos(perpendicular_angle)
        shield_points.append((center_x + rotated_x, center_y + rotated_y))
        
        # Draw the filled shield polygon
        if len(shield_points) >= 3:
            pg.draw.polygon(screen, self.shield_color, shield_points)
            pg.draw.polygon(screen, self.shield_border_color, shield_points, 3)
        
        # Add a center highlight line for extra visual detail
        # Calculate start and end points for center line
        line_start_x = 0
        line_start_y = -half_height * 0.6
        line_end_x = 0
        line_end_y = half_height * 0.6
        
        # Rotate center line points by perpendicular angle
        start_rotated_x = line_start_x * math.cos(perpendicular_angle) - line_start_y * math.sin(perpendicular_angle)
        start_rotated_y = line_start_x * math.sin(perpendicular_angle) + line_start_y * math.cos(perpendicular_angle)
        end_rotated_x = line_end_x * math.cos(perpendicular_angle) - line_end_y * math.sin(perpendicular_angle)
        end_rotated_y = line_end_x * math.sin(perpendicular_angle) + line_end_y * math.cos(perpendicular_angle)
        
        start_point = (center_x + start_rotated_x, center_y + start_rotated_y)
        end_point = (center_x + end_rotated_x, center_y + end_rotated_y)
        
        pg.draw.line(screen, self.shield_border_color, start_point, end_point, 2)
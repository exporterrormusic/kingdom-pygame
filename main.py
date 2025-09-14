#!/usr/bin/env python3
"""
Kingdom - Top-Down Twin-Stick Shooter
Main game with character selection and sprite animation support
"""

import pygame as pg
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.player import Player
from src.animated_player import AnimatedPlayer
from src.bullet import BulletManager
from src.enemy import EnemyManager
from src.collision import CollisionManager, EffectsManager
from src.game_states import StateManager, GameState
from src.character_manager import CharacterManager, CharacterSelectionMenu
from src.weapon_manager import weapon_manager
from src.missile_system import MissileManager
from src.slash_effect import SlashEffectManager
from src.missile_system import MissileManager
from src.slash_effect import SlashEffectManager
from src.slash_effect import SlashEffectManager
from src.missile_system import MissileManager

# Game constants
DEFAULT_SCREEN_WIDTH = 1920
DEFAULT_SCREEN_HEIGHT = 1080
BACKGROUND_COLOR = (20, 20, 40)
FPS = 60

class Game:
    """Main game class with character selection and sprite support."""
    
    def __init__(self):
        """Initialize the game."""
        pg.init()
        # Dynamic screen dimensions
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_height = DEFAULT_SCREEN_HEIGHT
        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))
        pg.display.set_caption("Kingdom-Pygame - Twin-Stick Shooter")
        self.clock = pg.time.Clock()
        
        # Track when we just entered pause to avoid immediate resume
        self.just_paused = False
        
        # Initialize cursor variables
        self.crosshair_cursor = None
        self.default_cursor = pg.mouse.get_cursor()  # Store default cursor
        
        # Create custom crosshair cursor
        self.create_crosshair_cursor()
        
        # Fonts
        self.large_font = pg.font.Font(None, 64)
        self.font = pg.font.Font(None, 48)
        self.small_font = pg.font.Font(None, 32)
        
        # Game systems
        self.state_manager = StateManager(self.screen, self.font, self.small_font)
        
        # Character system
        self.character_manager = CharacterManager()
        # Character Selection
        self.character_selection = CharacterSelectionMenu(self.screen_width, self.screen_height)
        self.selected_character = None
        
        # Game objects (will be created after character selection)
        self.player = None
        self.bullet_manager = BulletManager()
        self.enemy_manager = EnemyManager()
        self.effects_manager = EffectsManager()
        self.collision_manager = CollisionManager()
        self.slash_effect_manager = SlashEffectManager()
        self.missile_manager = MissileManager()
        
        # Import and initialize minigun effects manager
        from src.minigun_effects import MinigunEffectsManager
        from src.shotgun_effects import ShotgunEffectsManager
        self.minigun_effects_manager = MinigunEffectsManager()
        self.shotgun_effects_manager = ShotgunEffectsManager()
        
        # Camera shake system
        self.camera_shake_intensity = 0.0
        self.camera_shake_duration = 0.0
        self.camera_offset = pg.Vector2(0, 0)
        
        # Game state
        self.running = True
        self.dt = 0.0
        self.game_time = 0.0
        self.score = 0
        
        # Input handling
        self.keys_just_pressed = []
    
    def create_crosshair_cursor(self):
        """Create and set a custom crosshair cursor."""
        try:
            # Create a 24x24 pixel cursor surface
            cursor_size = 24
            cursor_surface = pg.Surface((cursor_size, cursor_size), pg.SRCALPHA)
            
            # Draw crosshair
            center = cursor_size // 2
            color = (255, 255, 255)  # White crosshair
            thickness = 2
            length = 8
            
            # Vertical line
            pg.draw.line(cursor_surface, color, 
                        (center, center - length), (center, center + length), thickness)
            # Horizontal line  
            pg.draw.line(cursor_surface, color,
                        (center - length, center), (center + length, center), thickness)
            
            # Center dot
            pg.draw.circle(cursor_surface, color, (center, center), 2)
            
            # Store crosshair cursor but don't set it yet
            self.crosshair_cursor = pg.cursors.Cursor((center, center), cursor_surface)
        except Exception as e:
            print(f"Error creating crosshair cursor: {e}")
            self.crosshair_cursor = None
    
    def set_menu_cursor(self):
        """Set cursor for menu interactions."""
        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
    
    def set_game_cursor(self):
        """Set cursor for gameplay."""
        if self.crosshair_cursor:
            pg.mouse.set_cursor(self.crosshair_cursor)
        else:
            # Fallback to system crosshair if custom cursor fails
            pg.mouse.set_cursor(pg.SYSTEM_CURSOR_CROSSHAIR)
    
    def create_player_from_selection(self):
        """Create player based on character selection."""
        if not self.selected_character:
            # Fallback to geometric player
            print("No character selected, using geometric player")
            self.player = Player(self.screen_width // 2, self.screen_height // 2)
            return
        
        # Get character sprite path
        char_path = self.character_manager.get_character_path(self.selected_character)
        
        if char_path and os.path.exists(char_path):
            # Create animated player with sprites
            try:
                # Determine frame size by loading the sprite sheet
                temp_sprite = pg.image.load(char_path)
                frame_width = temp_sprite.get_width() // 3
                frame_height = temp_sprite.get_height() // 4
                
                char_display_name = self.character_manager.get_current_character_name()
                char_config = self.character_manager.get_character_config(self.selected_character)
                
                self.player = AnimatedPlayer(
                    self.screen_width // 2, self.screen_height // 2, 
                    char_path, frame_width, frame_height,
                    self.state_manager.enhanced_menu.audio_manager,
                    self.selected_character,
                    char_display_name,
                    char_config  # Pass character config for unique stats
                )
                
                char_display_name = self.character_manager.get_current_character_name()
                print(f"Created player with character: {char_display_name}")
                
            except Exception as e:
                print(f"Failed to create animated player: {e}")
                # Fallback to geometric player
                self.player = Player(self.screen_width // 2, self.screen_height // 2)
        else:
            # Fallback to geometric player
            print("Character sprite not found, using geometric player")
            self.player = Player(self.screen_width // 2, self.screen_height // 2)
    
    def reset_game(self):
        """Reset the game to initial state."""
        self.create_player_from_selection()
        self.bullet_manager = BulletManager()
        self.missile_manager = MissileManager()
        
        # Set bullet manager fire rate based on player's weapon
        if hasattr(self.player, 'weapon_fire_rate'):
            self.bullet_manager.set_fire_rate(self.player.weapon_fire_rate)
            print(f"Set weapon fire rate: {self.player.weapon_fire_rate}")
        
        self.enemy_manager = EnemyManager()
        self.effects_manager = EffectsManager()
        self.collision_manager = CollisionManager()
        self.slash_effect_manager = SlashEffectManager()
        self.score = 0
        self.game_time = 0.0
        
        # Sword attack state for continuous damage
        self.active_sword_attack = None
        
        # Reset camera shake
        self.camera_shake_intensity = 0.0
        self.camera_shake_duration = 0.0
        self.camera_offset = pg.Vector2(0, 0)
    
    def add_camera_shake(self, intensity: float, duration: float):
        """Add camera shake effect."""
        self.camera_shake_intensity = max(self.camera_shake_intensity, intensity)
        self.camera_shake_duration = max(self.camera_shake_duration, duration)
    
    def update_camera_shake(self, dt: float):
        """Update camera shake effect."""
        if self.camera_shake_duration > 0:
            self.camera_shake_duration -= dt
            
            # Calculate shake offset
            import random
            shake_amount = self.camera_shake_intensity * (self.camera_shake_duration / 0.5)
            self.camera_offset.x = random.uniform(-shake_amount, shake_amount)
            self.camera_offset.y = random.uniform(-shake_amount, shake_amount)
            
            if self.camera_shake_duration <= 0:
                self.camera_offset = pg.Vector2(0, 0)
        else:
            self.camera_offset = pg.Vector2(0, 0)
    
    def handle_events(self):
        """Handle game events."""
        self.keys_just_pressed = []
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.USEREVENT + 1:  # Resolution change event
                new_width, new_height = event.resolution
                try:
                    self.screen = pg.display.set_mode((new_width, new_height))
                    self.screen_width, self.screen_height = new_width, new_height
                    # Update all systems that need to know about resolution change
                    self.state_manager.update_screen_dimensions(self.screen, self.screen_width, self.screen_height)
                    print(f"Resolution changed to: {new_width}x{new_height}")
                except Exception as e:
                    print(f"Failed to change resolution: {e}")
            elif event.type == pg.USEREVENT + 2:  # Fullscreen toggle event
                try:
                    if event.fullscreen:
                        # Use pygame's scaled fullscreen for smooth borderless experience
                        info = pg.display.Info()
                        desktop_width, desktop_height = info.current_w, info.current_h
                        print(f"Desktop resolution detected: {desktop_width}x{desktop_height}")
                        
                        # Use SCALED flag for automatic scaling to desktop resolution
                        self.screen = pg.display.set_mode((desktop_width, desktop_height), pg.FULLSCREEN | pg.SCALED)
                        pg.display.set_caption("Kingdom-Pygame - Twin-Stick Shooter")
                        
                        # Update screen dimensions
                        self.screen_width, self.screen_height = desktop_width, desktop_height
                        self.state_manager.update_screen_dimensions(self.screen, self.screen_width, self.screen_height)
                        print(f"Scaled fullscreen enabled: {desktop_width}x{desktop_height}")
                    else:
                        # Return to windowed mode
                        resolution_str = self.state_manager.enhanced_menu.resolutions[self.state_manager.enhanced_menu.current_resolution]
                        width, height = map(int, resolution_str.split('x'))
                        print(f"Returning to windowed mode: {width}x{height}")
                        
                        self.screen = pg.display.set_mode((width, height))
                        pg.display.set_caption("Kingdom-Pygame - Twin-Stick Shooter")
                        
                        self.screen_width, self.screen_height = width, height
                        self.state_manager.update_screen_dimensions(self.screen, self.screen_width, self.screen_height)
                        print(f"Windowed mode restored: {width}x{height}")
                except Exception as e:
                    print(f"Failed to toggle fullscreen: {e}")
            elif event.type == pg.KEYDOWN:
                self.keys_just_pressed.append(event.key)
                
                # Global pause toggle - but only handle if not already in pause menu navigation
                if (event.key == pg.K_ESCAPE or event.key == pg.K_p):
                    if self.state_manager.is_playing():
                        self.state_manager.change_state(GameState.PAUSED)
                        self.just_paused = True  # Mark that we just paused
                        # Clear the key from the list to prevent immediate resume
                        if event.key in self.keys_just_pressed:
                            self.keys_just_pressed.remove(event.key)
                        continue  # Skip further processing of this key
                    elif self.state_manager.is_paused():
                        # Let the pause menu handler deal with escape in pause state
                        pass
                
                # Handle character selection
                if self.state_manager.is_character_select():
                    result = self.character_selection.handle_input(event)
                    if result == "select":
                        # Character selected, start game
                        self.selected_character = self.character_selection.get_selected_character()
                        self.character_manager.set_current_character(self.selected_character)
                        self.reset_game()
                        self.state_manager.change_state(GameState.PLAYING)
                        # Start battle music
                        self.state_manager.enhanced_menu.start_battle_music()
                    elif result == "back":
                        # Go back to main menu
                        self.state_manager.change_state(GameState.MENU)
            
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pg.mouse.get_pos()
                    # Handle main menu mouse clicks
                    if self.state_manager.get_state() == GameState.MENU:
                        result = self.state_manager.enhanced_menu.handle_main_menu_mouse_click(mouse_pos)
                        if result:
                            if result == "new_game":
                                self.state_manager.change_state(GameState.CHARACTER_SELECT)
                            elif result == "load_game":
                                self.state_manager.change_state(GameState.SAVE_LOAD)
                            elif result == "settings":
                                self.state_manager.change_state(GameState.SETTINGS)
                            elif result == "quit":
                                self.running = False
                    # Handle settings menu mouse clicks
                    elif self.state_manager.get_state() == GameState.SETTINGS:
                        self.state_manager.enhanced_menu.handle_settings_mouse_click(mouse_pos)
                    # Handle pause menu mouse clicks
                    elif self.state_manager.is_paused():
                        result = self.state_manager.handle_pause_mouse_click(mouse_pos)
                        if result:
                            if result == "resume":
                                self.state_manager.change_state(GameState.PLAYING)
                            elif result == "settings":
                                self.state_manager.change_state(GameState.SETTINGS)
                            elif result == "main_menu":
                                self.state_manager.change_state(GameState.MENU)
                    # Handle character selection mouse clicks
                    elif self.state_manager.is_character_select():
                        result = self.character_selection.handle_mouse_click(mouse_pos)
                        if result == "select":
                            self.selected_character = self.character_selection.get_selected_character()
                            self.character_manager.set_current_character(self.selected_character)
                            self.reset_game()
                            self.state_manager.change_state(GameState.PLAYING)
                            self.state_manager.enhanced_menu.start_battle_music()
                        elif result == "back":
                            self.state_manager.change_state(GameState.MENU)
            
            elif event.type == pg.MOUSEMOTION:
                mouse_pos = pg.mouse.get_pos()
                # Handle main menu hover
                if self.state_manager.get_state() == GameState.MENU:
                    hovered_option = self.state_manager.enhanced_menu.check_mouse_hover_main_menu(mouse_pos)
                    if hovered_option is not None:
                        self.state_manager.enhanced_menu.main_menu_selection = hovered_option
            
            # Handle enhanced menu system input for welcome, main menu, and settings
            if self.state_manager.get_state() == GameState.WELCOME:
                if not self.state_manager.handle_welcome_input(event):
                    self.running = False
            elif self.state_manager.get_state() == GameState.MENU:
                if not self.state_manager.handle_enhanced_menu_input(event):
                    self.running = False
            elif self.state_manager.get_state() == GameState.SETTINGS:
                result = self.state_manager.enhanced_menu.handle_input(event)
                if result == "back":
                    # Go back to previous state (pause or main menu)
                    if self.state_manager.previous_state == GameState.PAUSED:
                        self.state_manager.change_state(GameState.PAUSED)
                    else:
                        self.state_manager.change_state(GameState.MENU)
            elif self.state_manager.get_state() == GameState.SAVE_LOAD:
                result = self.state_manager.enhanced_menu.handle_input(event)
                if result and result.startswith("load_slot_"):
                    slot_id = int(result.split("_")[-1])
                    # TODO: Load the actual game from save slot
                    print(f"Loading game from slot {slot_id}")
                    self.state_manager.change_state(GameState.CHARACTER_SELECT)
        
        # Handle continuous mouse hover for menu states
        if not pg.mouse.get_pressed()[0]:  # Only when not clicking
            mouse_pos = pg.mouse.get_pos()
            if self.state_manager.get_state() == GameState.MENU:
                # Update main menu selection based on mouse hover
                hovered_option = self.state_manager.enhanced_menu.check_mouse_hover_main_menu(mouse_pos)
                if hovered_option is not None:
                    self.state_manager.enhanced_menu.main_menu_selection = hovered_option
            elif self.state_manager.get_state() == GameState.SETTINGS:
                # Update settings hover
                self.state_manager.enhanced_menu.check_mouse_hover_settings_tabs(mouse_pos)
            elif self.state_manager.is_paused():
                # Update pause menu hover
                self.state_manager.handle_pause_mouse_hover(mouse_pos)
        
        # Handle legacy state-specific input (keeping for compatibility)
        if self.state_manager.is_game_over():
            if not self.state_manager.handle_game_over_input(self.keys_just_pressed):
                self.running = False
                
        elif self.state_manager.is_paused():
            # Don't process pause input on the same frame we just entered pause
            if not self.just_paused:
                self.state_manager.handle_pause_input(self.keys_just_pressed)
            else:
                self.just_paused = False  # Reset for next frame
            
        elif self.state_manager.is_playing():
            # Handle continuous game input
            keys = pg.key.get_pressed()
            mouse_pos = pg.mouse.get_pos()
            mouse_buttons = pg.mouse.get_pressed()
            
            # Player input (if player exists)
            if self.player:
                if hasattr(self.player, 'handle_input'):
                    # AnimatedPlayer
                    self.player.handle_input(keys, mouse_pos, self.game_time, 
                                           self.effects_manager, self.add_camera_shake, mouse_buttons, self.bullet_manager)
                else:
                    # Regular Player - handle input manually
                    self.player.handle_input(keys, mouse_pos, self.game_time, self.effects_manager, bullet_manager=self.bullet_manager)
                
                # Shooting
                if mouse_buttons[0]:  # Left mouse button
                    gun_tip = self.player.get_gun_tip_position()
                    
                    # Start continuous fire tracking for minigun (but not during reload)
                    if self.player.weapon_type == "Minigun" and not getattr(self.player, 'is_reloading', False):
                        self.bullet_manager.start_continuous_fire(self.game_time, self.player.weapon_type)
                        self.bullet_manager.update_minigun_fire_rate(self.game_time, self.player.weapon_type)
                    
                    # Check if player can shoot (has ammo and not reloading)
                    if hasattr(self.player, 'can_shoot') and self.player.can_shoot():
                        # Get weapon-specific bullet properties
                        bullet_props = self.player.get_bullet_properties()
                        weapon_damage = getattr(self.player, 'weapon_damage', 25)  # Default damage if no weapon_damage
                        
                        # Check weapon type for special mechanics
                        pellet_count = weapon_manager.get_pellet_count(self.player.weapon_type)
                        spread_angle = weapon_manager.get_spread_angle(self.player.weapon_type)
                        
                        bullet_fired = False
                        
                        # Handle sword melee attacks
                        if self.player.weapon_type == "Sword":
                            if self.bullet_manager.can_shoot(self.game_time):
                                # Perform melee slash attack
                                self.perform_sword_attack(weapon_damage)
                                self.bullet_manager.last_shot_time = self.game_time
                                bullet_fired = True
                        # Handle rocket launcher
                        elif self.player.weapon_type == "Rocket Launcher":
                            if self.bullet_manager.can_shoot(self.game_time):
                                # Fire missile towards the mouse position
                                target_pos = pg.Vector2(pg.mouse.get_pos())
                                # Convert screen coordinates to world coordinates by considering camera
                                target_pos -= self.camera_offset
                                
                                # Create missile
                                self.missile_manager.fire_missile(
                                    gun_tip.x, gun_tip.y,
                                    target_pos.x, target_pos.y,
                                    damage=weapon_damage
                                )
                                
                                self.bullet_manager.last_shot_time = self.game_time
                                bullet_fired = True
                        # Fire multiple pellets if it's a shotgun-type weapon
                        elif pellet_count > 1 and spread_angle > 0:
                            # Try to fire the first pellet to check fire rate
                            if self.bullet_manager.can_shoot(self.game_time):
                                # Fire multiple pellets with even spread
                                for i in range(pellet_count):
                                    # Calculate even spread angle for this pellet
                                    if pellet_count == 1:
                                        angle_offset = 0
                                    else:
                                        # Distribute pellets evenly across the spread angle
                                        angle_offset = (i - (pellet_count - 1) / 2) * (2 * spread_angle / (pellet_count - 1))
                                    
                                    pellet_angle = self.player.angle + angle_offset
                                    
                                    # Create individual pellet
                                    self.bullet_manager.bullets.append(
                                        self.bullet_manager.create_bullet(
                                            gun_tip.x, gun_tip.y, pellet_angle,
                                            damage=weapon_damage,
                                            speed=bullet_props["speed"],
                                            size_multiplier=bullet_props["size_multiplier"],
                                            color=bullet_props["color"],
                                            penetration=bullet_props.get("penetration", 1),
                                            shape=bullet_props.get("shape", "standard"),
                                            range_limit=bullet_props.get("range", 800),
                                            weapon_type=self.player.weapon_type
                                        )
                                    )
                                
                                # Update last shot time after firing all pellets
                                self.bullet_manager.last_shot_time = self.game_time
                                bullet_fired = True
                                
                                # Add spectacular shotgun muzzle flash effect
                                self.effects_manager.add_shotgun_muzzle_flash(
                                    gun_tip.x, gun_tip.y, self.player.angle
                                )
                        else:
                            # Single bullet weapons (AR, SMG, Sniper, Minigun)
                            bullet_fired = self.bullet_manager.shoot(
                                gun_tip.x, gun_tip.y, self.player.angle, self.game_time, 
                                damage=weapon_damage,
                                speed=bullet_props["speed"],
                                size_multiplier=bullet_props["size_multiplier"],
                                color=bullet_props["color"],
                                penetration=bullet_props.get("penetration", 1),
                                shape=bullet_props.get("shape", "standard"),
                                range_limit=bullet_props.get("range", 800),
                                weapon_type=self.player.weapon_type
                            )
                            
                            # Add muzzle flash effects for specific weapons
                            if bullet_fired and self.player.weapon_type == "Assault Rifle":
                                self.effects_manager.add_assault_rifle_muzzle_flash(
                                    gun_tip.x, gun_tip.y, self.player.angle
                                )
                            elif bullet_fired and self.player.weapon_type == "SMG":
                                self.effects_manager.add_smg_muzzle_flash(
                                    gun_tip.x, gun_tip.y, self.player.angle
                                )
                        
                        # Only use ammo if bullet was actually fired (except for melee weapons)
                        if bullet_fired and hasattr(self.player, 'use_ammo') and self.player.weapon_type != "Sword":
                            self.player.use_ammo(self.bullet_manager)
                else:
                    # Fire button not pressed - stop continuous fire for minigun
                    if hasattr(self, 'bullet_manager') and hasattr(self, 'player'):
                        weapon_type = getattr(self.player, 'weapon_type', None)
                        self.bullet_manager.stop_continuous_fire(weapon_type)
                        # Clear reload reset flag when fire button is released
                        if weapon_type == "Minigun":
                            self.bullet_manager.minigun_reload_reset = False
    
    def perform_sword_attack(self, damage):
        """Perform a melee sword attack with visual slash that deals continuous damage."""
        import math
        
        # Get sword attack properties from weapon manager
        sword_range = weapon_manager.get_weapon_property(self.player.weapon_type, 'firing', 'range', 300)
        slash_arc = weapon_manager.get_weapon_property(self.player.weapon_type, 'special_mechanics', 'slash_arc', 90)
        
        # Create visual slash effect that follows player AND deals damage
        self.create_slash_effect(sword_range, slash_arc, damage)
        
        # Add magical sword activation effect
        gun_tip = self.player.get_gun_tip_position()
        self.effects_manager.add_sword_activation_flash(gun_tip.x, gun_tip.y, self.player.angle)
        
        # No instant damage - the slash effect itself will handle damage continuously
    
    def check_slash_damage(self):
        """Check for continuous damage from active sword slash effects."""
        if not self.slash_effect_manager.effects:
            return
            
        # Get damage events from all active slash effects
        damage_events = self.slash_effect_manager.check_enemy_collisions(
            self.enemy_manager.enemies, 
            self.player
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
            
            # Add BURST charge to player when hitting enemy
            if hasattr(self.player, 'add_burst_charge'):
                self.player.add_burst_charge()
            
            # Check if enemy died and remove
            if not enemy.is_alive():
                # Add explosion/death particles at enemy position BEFORE removal
                self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 100))  # Purple-ish explosion
                self.effects_manager.add_sword_impact_effect(enemy.pos.x, enemy.pos.y)  # Sword-specific death effect
                self.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.score += 100
        
        # Add screen shake for sword impacts
        if enemies_hit:
            self.add_camera_shake(0.4, 0.2)
    
    def check_missile_visual_damage(self):
        """Check for continuous damage from missile bodies and explosions based on visual effects."""
        if not self.missile_manager.missiles:
            return
            
        # Get damage events from all active missiles
        damage_events = self.missile_manager.check_visual_damage(
            self.enemy_manager.enemies
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
            
            # Add BURST charge to player when hitting enemy
            if hasattr(self.player, 'add_burst_charge'):
                self.player.add_burst_charge()
            
            # Check if enemy died and remove
            if not enemy.is_alive():
                # Add appropriate explosion/death particles at enemy position BEFORE removal
                if damage_type == 'missile_body':
                    self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 150, 0))  # Orange explosion for missile hit
                else:  # explosion damage
                    self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 50))  # Red-orange explosion for missile explosion
                
                self.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.score += 100
        
        # Add screen shake for missile impacts
        if enemies_hit:
            impact_intensity = 0.6 if any(event['type'] == 'explosion' for event in damage_events) else 0.3
            self.add_camera_shake(impact_intensity, 0.3)
    
    def create_slash_effect(self, sword_range, slash_arc, damage):
        """Create a visual slash effect for the sword attack."""
        # Pass player reference and damage so slash follows player movement and deals damage
        self.slash_effect_manager.create_slash(
            self.player,  # Pass player reference
            0,  # Relative angle offset (0 = follows player direction exactly)
            sword_range,
            damage  # Pass damage value to the slash effect
        )
    
    def check_missile_enemy_collisions(self):
        """Check for missile collisions with enemies and handle explosions."""
        from src.missile_system import MissileState  # Import here to avoid circular imports
        
        kills = 0
        for missile in self.missile_manager.missiles[:]:  # Use slice copy for safe iteration
            if missile.state == MissileState.FLYING:
                # Check direct hit with enemies
                for enemy in self.enemy_manager.get_enemies():
                    distance = (missile.pos - enemy.pos).length()
                    if distance < enemy.size:
                        # Direct hit - explode missile
                        missile.explode()
                        break
                        
            elif missile.state == MissileState.EXPLODING:
                # Check AOE damage during explosion
                explosion_radius = 150  # Match the radius from weapons.json
                for enemy in self.enemy_manager.get_enemies():
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
                            self.effects_manager.add_explosion(enemy_pos[0], enemy_pos[1])
                
                # Add screen shake for explosion
                self.add_camera_shake(0.8, 0.4)
                
        return kills
    
    def check_whip_damage(self):
        """Check for minigun whip trail damage to enemies."""
        if not hasattr(self, 'minigun_effects_manager'):
            return 0
            
        kills = 0
        
        for enemy in self.enemy_manager.get_enemies():
            # Check if enemy collides with whip trail
            hit, damage, hit_x, hit_y = self.minigun_effects_manager.check_whip_collision(
                enemy.pos.x, enemy.pos.y, enemy.size
            )
            
            if hit:
                # Store enemy state before damage
                was_alive = enemy.is_alive()
                
                # Apply whip damage
                enemy.take_damage(damage)
                
                # Create impact spark at hit location
                self.minigun_effects_manager.create_impact_spark(hit_x, hit_y)
                
                # Check if enemy was killed
                if was_alive and not enemy.is_alive():
                    kills += 1
                    # Add small explosion effect
                    self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y)
                    
        return kills
    
    def update(self):
        """Update game logic."""
        # Always update state manager for menu animations
        self.state_manager.update(self.dt)
        
        if self.state_manager.is_playing() and self.player:
            # Update camera shake
            self.update_camera_shake(self.dt)
            
            # Update player
            self.player.update(self.dt, self.bullet_manager)
            
            # Update managers
            self.bullet_manager.update(self.dt, self.game_time)
            self.missile_manager.update(self.dt, self.enemy_manager.get_enemies())
            self.enemy_manager.update(self.dt, self.player.pos, self.game_time, self.bullet_manager)
            self.effects_manager.update(self.dt)
            self.slash_effect_manager.update(self.dt)
            
            # Update minigun effects if player is using minigun
            if self.player.weapon_type == "Minigun":
                gun_tip = self.player.get_gun_tip_position()
                is_firing = self.bullet_manager.is_firing_continuously
                self.minigun_effects_manager.update(
                    self.dt, is_firing, self.bullet_manager.current_fire_rate, 
                    (gun_tip.x, gun_tip.y), self.player.angle
                )
                
                # Update whip trail damage segments with current bullets for collision detection
                minigun_bullets = [bullet for bullet in self.bullet_manager.bullets 
                                 if hasattr(bullet, 'weapon_type') and bullet.weapon_type == 'Minigun']
                self.minigun_effects_manager.update_whip_trail_with_bullets(minigun_bullets)
            
            # Update shotgun fire trail effects if player is using shotgun
            if self.player.weapon_type == "Shotgun":
                self.shotgun_effects_manager.update(self.dt)
            
            # Check for continuous sword damage from active slash effects
            self.check_slash_damage()
            
            # Check for continuous missile damage from visual effects (body hits and explosions)
            self.check_missile_visual_damage()
            
            # Update game timer
            self.game_time += self.dt
            
            # Handle collisions
            kills = self.collision_manager.check_bullet_enemy_collisions(
                self.bullet_manager, self.enemy_manager, self.player, self.effects_manager)
            
            # Handle missile collisions with enemies
            missile_kills = self.check_missile_enemy_collisions()
            kills += missile_kills
            
            # Handle minigun whip damage when at full speed
            if self.player.weapon_type == "Minigun" and self.minigun_effects_manager.whip_trail_active:
                whip_kills = self.check_whip_damage()
                kills += whip_kills
            
            if kills > 0:
                self.score += kills * 100
            
            # Check player-enemy collisions
            player_hit = self.collision_manager.check_player_enemy_collisions(
                self.player, self.enemy_manager)
            
            # Check enemy bullet-player collisions
            bullet_hit = self.collision_manager.check_enemy_bullet_player_collisions(
                self.bullet_manager, self.player)
            
            if player_hit or bullet_hit:
                # Add camera shake and red flash for player hit
                self.add_camera_shake(15.0, 0.4)  # Stronger shake for player hit
                if hasattr(self.player, 'add_hit_flash'):
                    self.player.add_hit_flash()
                self.effects_manager.add_hit_effect(self.player.pos.x, self.player.pos.y, 
                                                  (255, 100, 100))
            
            # Check game over
            if not self.player.is_alive():
                self.state_manager.set_game_over_stats(
                    self.score, 
                    self.enemy_manager.get_wave(), 
                    self.enemy_manager.get_kills()
                )
                self.state_manager.change_state(GameState.GAME_OVER)
    
    def render(self):
        """Render the game."""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Set appropriate cursor based on game state
        current_state = self.state_manager.get_state()
        if current_state in [GameState.WELCOME, GameState.MENU, GameState.SETTINGS, 
                           GameState.SAVE_LOAD, GameState.CHARACTER_SELECT, GameState.PAUSED, GameState.GAME_OVER]:
            self.set_menu_cursor()
        elif current_state == GameState.PLAYING:
            self.set_game_cursor()
        
        # Apply camera shake offset for rendering
        shake_x = int(self.camera_offset.x) if hasattr(self, 'camera_offset') else 0
        shake_y = int(self.camera_offset.y) if hasattr(self, 'camera_offset') else 0
        offset = (shake_x, shake_y)
        
        # Render based on current state
        if self.state_manager.get_state() == GameState.WELCOME:
            self.state_manager.render_welcome()
            
        elif self.state_manager.get_state() == GameState.MENU:
            self.state_manager.render_enhanced_menu()
            
        elif self.state_manager.get_state() == GameState.SETTINGS:
            self.state_manager.render_settings()
            
        elif self.state_manager.get_state() == GameState.SAVE_LOAD:
            self.state_manager.render_save_load()
            
        elif self.state_manager.is_character_select():
            self.character_selection.update(self.dt)
            self.character_selection.render(self.screen)
            
        elif self.state_manager.is_playing():
            # Render game objects with camera shake offset
            if self.player:
                if hasattr(self.player, 'render') and len(self.player.render.__code__.co_varnames) > 3:
                    # AnimatedPlayer with offset support
                    self.player.render(self.screen, self.game_time, offset)
                else:
                    # Regular player
                    self.player.render(self.screen, self.game_time)
            
            # Render enemies first (bottom layer)
            self.enemy_manager.render(self.screen, offset)
            
            # Render bullets and missiles above enemies
            self.bullet_manager.render(self.screen, offset)
            self.missile_manager.render(self.screen, offset)
            
            # Render effects on top
            self.effects_manager.render(self.screen, offset)
            self.slash_effect_manager.render(self.screen, offset)
            
            # Render minigun muzzle flames if active
            if self.player.weapon_type == "Minigun":
                # Get minigun bullets for whip trail rendering
                minigun_bullets = [bullet for bullet in self.bullet_manager.bullets 
                                 if hasattr(bullet, 'weapon_type') and bullet.weapon_type == 'Minigun']
                
                # Render whip trail lines between bullets
                self.minigun_effects_manager.render_whip_trail_lines(self.screen, minigun_bullets, offset)
                
                # Render trail sparks
                self.minigun_effects_manager.render_muzzle_flames(self.screen, offset)
            
            # Render shotgun fire trails if active
            if self.player.weapon_type == "Shotgun":
                # Get shotgun pellets for fire trail rendering
                shotgun_bullets = [bullet for bullet in self.bullet_manager.bullets 
                                 if hasattr(bullet, 'weapon_type') and bullet.weapon_type == 'Shotgun']
                
                # Render fire trail lines between pellets
                self.shotgun_effects_manager.render_fire_trail_lines(self.screen, shotgun_bullets, offset)
                
                # Shell casings disabled
                self.minigun_effects_manager.render_shell_casings(self.screen, offset)
            
            # Render game UI
            self.render_game_ui()
            
        elif self.state_manager.is_paused():
            # Render game objects (frozen) with camera shake offset
            if self.player:
                if hasattr(self.player, 'render') and len(self.player.render.__code__.co_varnames) > 3:
                    # AnimatedPlayer with offset support
                    self.player.render(self.screen, self.game_time, offset)
                else:
                    # Regular player
                    self.player.render(self.screen, self.game_time)
                    
            self.bullet_manager.render(self.screen, offset)
            self.missile_manager.render(self.screen, offset)
            self.enemy_manager.render(self.screen, offset)
            self.effects_manager.render(self.screen, offset)
            self.slash_effect_manager.render(self.screen, offset)
            
            # Render game UI
            self.render_game_ui()
            
            # Render pause overlay
            self.state_manager.render_pause()
            
        elif self.state_manager.is_game_over():
            self.state_manager.render_game_over()
        
        pg.display.flip()
    
    def render_game_ui(self):
        """Render game UI elements."""
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (30, 30))
        
        # Wave
        wave_text = self.font.render(f"Wave: {self.enemy_manager.get_wave()}", True, (255, 255, 255))
        self.screen.blit(wave_text, (30, 80))
        
        # Character name (if available)
        if self.selected_character:
            char_name = self.character_manager.get_current_character_name()
            if char_name:
                char_text = self.small_font.render(f"Playing as: {char_name}", True, (200, 200, 200))
                self.screen.blit(char_text, (30, self.screen_height - 60))
    
    def run(self):
        """Main game loop."""
        print("Starting Kingdom-Pygame Twin-Stick Shooter...")
        print(f"Found characters: {self.character_manager.get_character_display_names()}")
        
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update()
            self.render()
        
        pg.quit()
        sys.exit()

def main():
    """Entry point of the game."""
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
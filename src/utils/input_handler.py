"""
Input Handler System for Kingdom-Pygame

Handles all game input including:
- Event processing (keyboard, mouse, gamepad)
- State-specific input handling (menu, gameplay, pause)
- Resolution and fullscreen management
- Debug toggles and shortcuts
- Player movement and weapon controls

Extracted from main.py to improve modularity and maintainability.
"""

import pygame as pg
from src.core.game_states import GameState
from src.weapons.weapon_manager import weapon_manager


class InputHandler:
    """Manages all input processing and event handling for the game."""
    
    def __init__(self, game):
        """Initialize input handler with reference to main game instance."""
        self.game = game
    
    def handle_events(self):
        """Handle game events."""
        self.game.keys_just_pressed = []
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.game.running = False
            elif event.type == pg.USEREVENT + 1:  # Resolution change event
                self._handle_resolution_change(event)
            elif event.type == pg.USEREVENT + 2:  # Fullscreen toggle event
                self._handle_fullscreen_toggle(event)
            elif event.type == pg.KEYDOWN:
                self._handle_keydown_event(event)
            elif event.type == pg.MOUSEBUTTONDOWN:
                self._handle_mouse_button_event(event)
            elif event.type == pg.MOUSEMOTION:
                self._handle_mouse_motion_event(event)
            elif event.type == pg.MOUSEWHEEL:
                self._handle_mouse_wheel_event(event)
            
            # Handle enhanced menu system input for welcome, main menu, and settings
            self._handle_state_specific_events(event)
        
        # Handle continuous mouse hover for menu states
        self._handle_continuous_mouse_hover()
        
        # Handle legacy state-specific input (keeping for compatibility)
        self._handle_legacy_state_input()
    
    def _handle_resolution_change(self, event):
        """Handle resolution change events."""
        new_width, new_height = event.resolution
        try:
            self.game.screen = pg.display.set_mode((new_width, new_height))
            self.game.screen_width, self.game.screen_height = new_width, new_height
            # Update all systems that need to know about resolution change
            self.game.state_manager.update_screen_dimensions(self.game.screen, self.game.screen_width, self.game.screen_height)
            print(f"Resolution changed to: {new_width}x{new_height}")
        except Exception as e:
            print(f"Failed to change resolution: {e}")
    
    def _handle_fullscreen_toggle(self, event):
        """Handle fullscreen toggle events."""
        try:
            if event.fullscreen:
                # Use pygame's scaled fullscreen for smooth borderless experience
                info = pg.display.Info()
                desktop_width, desktop_height = info.current_w, info.current_h
                print(f"Desktop resolution detected: {desktop_width}x{desktop_height}")
                
                # Use SCALED flag for automatic scaling to desktop resolution
                self.game.screen = pg.display.set_mode((desktop_width, desktop_height), pg.FULLSCREEN | pg.SCALED)
                pg.display.set_caption("Kingdom-Pygame - Twin-Stick Shooter")
                
                # Update screen dimensions
                self.game.screen_width, self.game.screen_height = desktop_width, desktop_height
                self.game.state_manager.update_screen_dimensions(self.game.screen, self.game.screen_width, self.game.screen_height)
                print(f"Scaled fullscreen enabled: {desktop_width}x{desktop_height}")
            else:
                # Return to windowed mode
                resolution_str = self.game.state_manager.enhanced_menu.resolutions[self.game.state_manager.enhanced_menu.current_resolution]
                width, height = map(int, resolution_str.split('x'))
                print(f"Returning to windowed mode: {width}x{height}")
                
                self.game.screen = pg.display.set_mode((width, height))
                pg.display.set_caption("Kingdom-Pygame - Twin-Stick Shooter")
                
                self.game.screen_width, self.game.screen_height = width, height
                self.game.state_manager.update_screen_dimensions(self.game.screen, self.game.screen_width, self.game.screen_height)
                print(f"Windowed mode restored: {width}x{height}")
        except Exception as e:
            print(f"Failed to toggle fullscreen: {e}")
    
    def _handle_keydown_event(self, event):
        """Handle keyboard key press events."""
        self.game.keys_just_pressed.append(event.key)
        
        # Debug toggles
        self._handle_debug_toggles(event)
        
        # Pause handling
        if (event.key == pg.K_ESCAPE or event.key == pg.K_p):
            if self.game.state_manager.is_playing():
                self.game.state_manager.change_state(GameState.PAUSED)
                self.game.just_paused = True  # Mark that we just paused
                # Clear the key from the list to prevent immediate resume
                if event.key in self.game.keys_just_pressed:
                    self.game.keys_just_pressed.remove(event.key)
                return  # Skip further processing of this key
            elif self.game.state_manager.is_paused():
                # Let the pause menu handler deal with escape in pause state
                pass
        
        # Debug toggles (only in game)
        if self.game.state_manager.is_playing():
            if event.key == pg.K_m:  # 'M' key to toggle map debug
                self.game.world_manager.toggle_map_debug()
                if event.key in self.game.keys_just_pressed:
                    self.game.keys_just_pressed.remove(event.key)
            elif event.key == pg.K_F3:  # 'F3' key to toggle performance debug
                self.game.show_debug_info = not self.game.show_debug_info
                if event.key in self.game.keys_just_pressed:
                    self.game.keys_just_pressed.remove(event.key)
        
        # Handle character selection
        if self.game.state_manager.is_character_select():
            self._handle_character_selection_input(event)
    
    def _handle_debug_toggles(self, event):
        """Handle debug toggle key presses."""
        # Debug toggle for combat contrast (C key)
        if event.key == pg.K_c:
            self.game.combat_contrast_enabled = not self.game.combat_contrast_enabled
            print(f"Combat contrast {'ENABLED' if self.game.combat_contrast_enabled else 'DISABLED'}")
            if not self.game.combat_contrast_enabled:
                self.game.combat_contrast_active = False
                self.game.combat_contrast_timer = 0.0
        
        # Debug toggle for BLEND_ADD effects (B key)
        if event.key == pg.K_b:
            self.game.blend_add_effects_enabled = not self.game.blend_add_effects_enabled
            print(f"BLEND_ADD effects {'ENABLED' if self.game.blend_add_effects_enabled else 'DISABLED'}")
        
        # Emergency disable all screen effects (X key)
        if event.key == pg.K_x:
            self.game.lighting_effects_enabled = False
            self.game.combat_contrast_enabled = False
            self.game.blend_add_effects_enabled = False
            self.game.enable_dynamic_lighting = False
            print("ALL SCREEN EFFECTS DISABLED - Press L, C, B, or I to re-enable individually")
    
    def _handle_character_selection_input(self, event):
        """Handle character selection input."""
        result = self.game.character_selection.handle_input(event)
        if result == "select":
            # Character selected, start game
            self.game.selected_character = self.game.character_selection.get_selected_character()
            self.game.character_manager.set_current_character(self.game.selected_character)
            self.game.reset_game()
            self.game.state_manager.change_state(GameState.PLAYING)
            # Start battle music
            self.game.state_manager.enhanced_menu.start_battle_music()
        elif result == "back":
            # Go back to main menu
            self.game.state_manager.change_state(GameState.MENU)
    
    def _handle_mouse_button_event(self, event):
        """Handle mouse button events."""
        if event.button == 1:  # Left mouse button
            mouse_pos = pg.mouse.get_pos()
            # Handle main menu mouse clicks
            if self.game.state_manager.get_state() == GameState.MENU:
                result = self.game.state_manager.enhanced_menu.handle_main_menu_mouse_click(mouse_pos)
                if result:
                    if result == "new_game":
                        self.game.state_manager.change_state(GameState.CHARACTER_SELECT)
                    elif result == "load_game":
                        self.game.state_manager.change_state(GameState.SAVE_LOAD)
                    elif result == "settings":
                        self.game.state_manager.change_state(GameState.SETTINGS)
                    elif result == "quit":
                        self.game.running = False
            # Handle settings menu mouse clicks
            elif self.game.state_manager.get_state() == GameState.SETTINGS:
                self.game.state_manager.enhanced_menu.handle_settings_mouse_click(mouse_pos)
            # Handle pause menu mouse clicks
            elif self.game.state_manager.is_paused():
                result = self.game.state_manager.handle_pause_mouse_click(mouse_pos)
                if result:
                    if result == "resume":
                        self.game.state_manager.change_state(GameState.PLAYING)
                    elif result == "settings":
                        self.game.state_manager.change_state(GameState.SETTINGS)
                    elif result == "main_menu":
                        self.game.state_manager.change_state(GameState.MENU)
            # Handle character selection mouse clicks
            elif self.game.state_manager.is_character_select():
                result = self.game.character_selection.handle_mouse_click(mouse_pos)
                if result == "select":
                    self.game.selected_character = self.game.character_selection.get_selected_character()
                    self.game.character_manager.set_current_character(self.game.selected_character)
                    self.game.reset_game()
                    self.game.state_manager.change_state(GameState.PLAYING)
                    self.game.state_manager.enhanced_menu.start_battle_music()
                elif result == "back":
                    self.game.state_manager.change_state(GameState.MENU)
    
    def _handle_mouse_motion_event(self, event):
        """Handle mouse motion events."""
        mouse_pos = pg.mouse.get_pos()
        # Handle main menu hover
        if self.game.state_manager.get_state() == GameState.MENU:
            hovered_option = self.game.state_manager.enhanced_menu.check_mouse_hover_main_menu(mouse_pos)
            if hovered_option is not None:
                self.game.state_manager.enhanced_menu.main_menu_selection = hovered_option
    
    def _handle_mouse_wheel_event(self, event):
        """Handle mouse wheel events for zooming."""
        # Mouse wheel zoom control (only during gameplay)
        if self.game.state_manager.is_playing():
            zoom_speed = 0.05  # Zoom sensitivity
            if event.y > 0:  # Scroll up - zoom in
                self.game.base_zoom = min(self.game.max_zoom, self.game.base_zoom + zoom_speed)
            elif event.y < 0:  # Scroll down - zoom out
                self.game.base_zoom = max(self.game.min_zoom, self.game.base_zoom - zoom_speed)
    
    def _handle_state_specific_events(self, event):
        """Handle events specific to different game states."""
        if self.game.state_manager.get_state() == GameState.WELCOME:
            if not self.game.state_manager.handle_welcome_input(event):
                self.game.running = False
        elif self.game.state_manager.get_state() == GameState.MENU:
            if not self.game.state_manager.handle_enhanced_menu_input(event):
                self.game.running = False
        elif self.game.state_manager.get_state() == GameState.SETTINGS:
            result = self.game.state_manager.enhanced_menu.handle_input(event)
            if result == "back":
                # Go back to previous state (pause or main menu)
                if self.game.state_manager.previous_state == GameState.PAUSED:
                    self.game.state_manager.change_state(GameState.PAUSED)
                else:
                    self.game.state_manager.change_state(GameState.MENU)
        elif self.game.state_manager.get_state() == GameState.SAVE_LOAD:
            result = self.game.state_manager.enhanced_menu.handle_input(event)
            if result and result.startswith("load_slot_"):
                slot_id = int(result.split("_")[-1])
                # Load game functionality not implemented yet
                print(f"Loading game from slot {slot_id}")
                self.game.state_manager.change_state(GameState.CHARACTER_SELECT)
    
    def _handle_continuous_mouse_hover(self):
        """Handle continuous mouse hover for menu states."""
        if not pg.mouse.get_pressed()[0]:  # Only when not clicking
            mouse_pos = pg.mouse.get_pos()
            if self.game.state_manager.get_state() == GameState.MENU:
                # Update main menu selection based on mouse hover
                hovered_option = self.game.state_manager.enhanced_menu.check_mouse_hover_main_menu(mouse_pos)
                if hovered_option is not None:
                    self.game.state_manager.enhanced_menu.main_menu_selection = hovered_option
            elif self.game.state_manager.get_state() == GameState.SETTINGS:
                # Update settings hover
                self.game.state_manager.enhanced_menu.check_mouse_hover_settings_tabs(mouse_pos)
            elif self.game.state_manager.is_paused():
                # Update pause menu hover
                self.game.state_manager.handle_pause_mouse_hover(mouse_pos)
    
    def _handle_legacy_state_input(self):
        """Handle legacy state-specific input (keeping for compatibility)."""
        if self.game.state_manager.is_game_over():
            if not self.game.state_manager.handle_game_over_input(self.game.keys_just_pressed):
                self.game.running = False
                
        elif self.game.state_manager.is_paused():
            # Don't process pause input on the same frame we just entered pause
            if not self.game.just_paused:
                self.game.state_manager.handle_pause_input(self.game.keys_just_pressed)
            else:
                self.game.just_paused = False  # Reset for next frame
            
        elif self.game.state_manager.is_playing():
            # Handle continuous game input
            self._handle_gameplay_input()
    
    def _handle_gameplay_input(self):
        """Handle continuous input during gameplay."""
        keys = pg.key.get_pressed()
        mouse_pos = pg.mouse.get_pos()
        world_mouse_pos = self.game.screen_to_world_pos(mouse_pos)  # Convert to world coordinates
        mouse_buttons = pg.mouse.get_pressed()
        
        # Handle camera zoom controls
        self.game.handle_zoom_input(keys)
        
        # Player input (if player exists)
        if self.game.player:
            if hasattr(self.game.player, 'handle_input'):
                # AnimatedPlayer
                self.game.player.handle_input(keys, world_mouse_pos, self.game.game_time, 
                                       self.game.effects_manager, self.game.add_camera_shake, mouse_buttons, self.game.bullet_manager)
            else:
                # Regular Player - handle input manually
                self.game.player.handle_input(keys, world_mouse_pos, self.game.game_time, self.game.effects_manager, bullet_manager=self.game.bullet_manager)
            
            # Auto-collect cores near player (no key press needed)
            collected_cores = self.game.world_manager.core_manager.try_collect_cores(self.game.player.pos)
            
            # Shooting
            if mouse_buttons[0]:  # Left mouse button
                self._handle_shooting()
            else:
                # Fire button not pressed - stop continuous fire for minigun
                self._handle_stop_shooting()
    
    def _handle_shooting(self):
        """Handle shooting mechanics during gameplay."""
        gun_tip = self.game.player.get_gun_tip_position()
        
        # Start continuous fire tracking for minigun (but not during reload)
        if self.game.player.weapon_type == "Minigun" and not getattr(self.game.player, 'is_reloading', False):
            self.game.bullet_manager.start_continuous_fire(self.game.game_time, self.game.player.weapon_type)
            self.game.bullet_manager.update_minigun_fire_rate(self.game.game_time, self.game.player.weapon_type)
        
        # Check if player can shoot (has ammo and not reloading)
        if hasattr(self.game.player, 'can_shoot') and self.game.player.can_shoot():
            # Get weapon-specific bullet properties
            bullet_props = self.game.player.get_bullet_properties()
            weapon_damage = getattr(self.game.player, 'weapon_damage', 25)  # Default damage if no weapon_damage
            
            # Check weapon type for special mechanics
            pellet_count = weapon_manager.get_pellet_count(self.game.player.weapon_type)
            spread_angle = weapon_manager.get_spread_angle(self.game.player.weapon_type)
            
            bullet_fired = False
            
            # Handle sword melee attacks
            if self.game.player.weapon_type == "Sword":
                if self.game.bullet_manager.can_shoot(self.game.game_time):
                    # Perform melee slash attack
                    self.game.perform_sword_attack(weapon_damage)
                    self.game.bullet_manager.last_shot_time = self.game.game_time
                    bullet_fired = True
            # Handle rocket launcher
            elif self.game.player.weapon_type == "Rocket Launcher":
                if self.game.bullet_manager.can_shoot(self.game.game_time):
                    # Fire missile towards the mouse position
                    mouse_screen_pos = pg.mouse.get_pos()
                    # Convert screen coordinates to world coordinates properly
                    target_world_pos = self.game.screen_to_world_pos(mouse_screen_pos)
                    
                    # Create missile
                    self.game.missile_manager.fire_missile(
                        gun_tip.x, gun_tip.y,
                        target_world_pos[0], target_world_pos[1],
                        damage=weapon_damage
                    )
                    
                    self.game.bullet_manager.last_shot_time = self.game.game_time
                    bullet_fired = True
            # Fire multiple pellets if it's a shotgun-type weapon
            elif pellet_count > 1 and spread_angle > 0:
                # Try to fire the first pellet to check fire rate
                if self.game.bullet_manager.can_shoot(self.game.game_time):
                    # Fire multiple pellets with even spread
                    for i in range(pellet_count):
                        # Calculate even spread angle for this pellet
                        if pellet_count == 1:
                            angle_offset = 0
                        else:
                            # Distribute pellets evenly across the spread angle
                            angle_offset = (i - (pellet_count - 1) / 2) * (2 * spread_angle / (pellet_count - 1))
                        
                        pellet_angle = self.game.player.angle + angle_offset
                        
                        # Create individual pellet
                        self.game.bullet_manager.bullets.append(
                            self.game.bullet_manager.create_bullet(
                                gun_tip.x, gun_tip.y, pellet_angle,
                                damage=weapon_damage,
                                speed=bullet_props["speed"],
                                size_multiplier=bullet_props["size_multiplier"],
                                color=bullet_props["color"],
                                penetration=bullet_props.get("penetration", 1),
                                shape=bullet_props.get("shape", "standard"),
                                range_limit=bullet_props.get("range", 800),
                                trail_length=bullet_props.get("trail_length", 5),
                                trail_width=bullet_props.get("trail_width", 2)
                            )
                        )
                    
                    self.game.bullet_manager.last_shot_time = self.game.game_time
                    bullet_fired = True
            # Regular single bullet weapons
            else:
                if self.game.bullet_manager.can_shoot(self.game.game_time):
                    # Create and fire the bullet
                    self.game.bullet_manager.bullets.append(
                        self.game.bullet_manager.create_bullet(
                            gun_tip.x, gun_tip.y, self.game.player.angle,
                            damage=weapon_damage,
                            speed=bullet_props["speed"],
                            size_multiplier=bullet_props["size_multiplier"],
                            color=bullet_props["color"],
                            penetration=bullet_props.get("penetration", 1),
                            shape=bullet_props.get("shape", "standard"),
                            range_limit=bullet_props.get("range", 800),
                            trail_length=bullet_props.get("trail_length", 5),
                            trail_width=bullet_props.get("trail_width", 2)
                        )
                    )
                    
                    self.game.bullet_manager.last_shot_time = self.game.game_time
                    bullet_fired = True
                    
                    # Add muzzle flash effect for minigun
                    if self.game.player.weapon_type == "Minigun":
                        if hasattr(self.game.effects_manager, 'add_minigun_muzzle_flash'):
                            self.game.effects_manager.add_minigun_muzzle_flash(
                                gun_tip.x, gun_tip.y, self.game.player.angle
                            )
            
            # Only use ammo if bullet was actually fired (except for melee weapons)
            if bullet_fired and hasattr(self.game.player, 'use_ammo') and self.game.player.weapon_type != "Sword":
                self.game.player.use_ammo(self.game.bullet_manager)
    
    def _handle_stop_shooting(self):
        """Handle stopping shooting mechanics."""
        if hasattr(self.game, 'bullet_manager') and hasattr(self.game, 'player'):
            weapon_type = getattr(self.game.player, 'weapon_type', None)
            self.game.bullet_manager.stop_continuous_fire(weapon_type)
            # Clear reload reset flag when fire button is released
            if weapon_type == "Minigun":
                self.game.bullet_manager.minigun_reload_reset = False
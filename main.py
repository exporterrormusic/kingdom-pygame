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

from src.entities.player import Player
from src.entities.animated_player import AnimatedPlayer
from src.entities.bullet import BulletManager
from src.entities.enemy import EnemyManager
from src.systems.collision import CollisionManager
from src.effects.visual_effects import EffectsManager
from src.effects.atmospheric_effects import AtmosphericEffects
from src.core.game_states import StateManager, GameState
from src.ui.menu_states import MenuState
from src.utils.character_manager import CharacterManager, CharacterSelectionMenu
from src.weapons.weapon_manager import weapon_manager
from src.systems.camera_system import CameraSystem
from src.effects.visual_effects import VisualEffectsSystem  
from src.weapons.combat_system import CombatSystem
from src.effects.missile_system import MissileManager
from src.effects.slash_effect import SlashEffectManager
from src.world.world_manager import WorldManager
from src.world.minimap import MiniMap
from src.utils.score_manager import ScoreManager

# Multiplayer imports
from src.networking.network_manager import NetworkManager
from src.networking.game_synchronizer import GameStateSynchronizer
from src.networking.modern_multiplayer_lobby import ModernMultiplayerLobby
from src.networking.multiplayer_renderer import MultiplayerRenderer

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
        
        # Performance monitoring
        self.fps_counter = 0
        self.fps_timer = 0.0
        self.current_fps = 60
        self.show_debug_info = False  # Toggle with F3
        
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
        
        # Initialize world manager for infinite world (needed before enemy manager)
        self.world_manager = WorldManager()
        
        # Initialize mini-map (larger size)
        self.minimap = MiniMap(size=250, margin=20)
        
        # Game objects (will be created after character selection)
        self.player = None
        self.bullet_manager = BulletManager()
        self.enemy_manager = EnemyManager(self.world_manager, spawn_point=(0, 0))
        
        # Pre-populate enemies at world borders for tactical gameplay
        self.enemy_manager.populate_enemies_on_start(
            screen_width=self.screen_width, 
            screen_height=self.screen_height, 
            player_pos=pg.Vector2(0, 0), 
            zoom_level=1.0
        )
        
        self.effects_manager = EffectsManager()
        self.collision_manager = CollisionManager()
        
        # Initialize modular systems
        self.camera_system = CameraSystem(self.screen_width, self.screen_height)
        self.visual_effects = VisualEffectsSystem(self.screen_width, self.screen_height)
        self.combat_system = CombatSystem(self)
        
        # Initialize score management system
        self.score_manager = ScoreManager()
        
        # Set menu system dependencies for advanced features
        self.state_manager.enhanced_menu.set_dependencies(
            character_manager=self.character_manager,
            score_manager=self.score_manager
        )
        
        self.slash_effect_manager = SlashEffectManager()
        self.missile_manager = MissileManager(self.state_manager.enhanced_menu.audio_manager)
        
        # Initialize atmospheric effects
        self.atmospheric_effects = AtmosphericEffects(3840, 2160, self.state_manager.enhanced_menu.audio_manager)  # World dimensions
        
        # Import and initialize minigun effects manager
        from src.effects.minigun_effects import MinigunEffectsManager
        from src.effects.shotgun_effects import ShotgunEffectsManager
        
        # Pass None for lighting_system since it's not available in this game
        self.minigun_effects_manager = MinigunEffectsManager(lighting_system=None)
        self.shotgun_effects_manager = ShotgunEffectsManager(lighting_system=None)
        
        # Camera zoom limits (handled by camera system)
        self.min_zoom = 0.8   # Limited zoom out to prevent going too wide
        self.max_zoom = 2.0   # Can zoom in to 0.5x current view (closer)
        
        # Game state
        self.running = True
        self.dt = 0.0
        self.game_time = 0.0
        # Remove old score tracking - now handled by score_manager
        
        # Input handling
        self.keys_just_pressed = []
        
        # Modern multiplayer systems
        self.multiplayer_lobby = ModernMultiplayerLobby(
            self.screen_width, self.screen_height, 
            self.character_manager, 
            self.state_manager.enhanced_menu.audio_manager,
            self.state_manager.enhanced_menu  # Pass enhanced_menu for background rendering
        )
        self.network_manager = None
        self.game_synchronizer = None
        self.multiplayer_renderer = MultiplayerRenderer(self.character_manager)
        self.is_multiplayer = False
        self.multiplayer_players = {}  # Network player states
    
    def _start_multiplayer_game(self):
        """Start a multiplayer game from the lobby."""
        if self.multiplayer_lobby.get_network_manager():
            # Setup multiplayer
            self.network_manager = self.multiplayer_lobby.get_network_manager()
            self.is_multiplayer = True
            
            print(f"[MULTIPLAYER_INIT] Starting multiplayer game - is_host={self.multiplayer_lobby.is_host}")
            
            # Create game synchronizer
            self.game_synchronizer = GameStateSynchronizer(
                self.network_manager, 
                is_host=self.multiplayer_lobby.is_host
            )
            
            # Set game object references for the synchronizer
            self.game_synchronizer.set_game_references(
                player=self.player,
                bullet_manager=self.bullet_manager,
                enemy_manager=self.enemy_manager,
                effects_manager=self.effects_manager
            )
            
            # Set local player character from lobby
            lobby_players = self.multiplayer_lobby.get_players()
            local_id = self.multiplayer_lobby.get_local_player_id()
            
            print(f"[MULTIPLAYER_INIT] Local player: {local_id}")
            print(f"[MULTIPLAYER_INIT] Lobby players: {lobby_players} (type: {type(lobby_players)})")
            
            if isinstance(lobby_players, dict) and local_id in lobby_players:
                self.selected_character = lobby_players[local_id].character.lower().replace(' ', '-')
                self.character_manager.set_current_character(self.selected_character)
            elif isinstance(lobby_players, list):
                # Find local player in list
                for player in lobby_players:
                    if hasattr(player, 'id') and player.id == local_id:
                        self.selected_character = player.character.lower().replace(' ', '-')
                        self.character_manager.set_current_character(self.selected_character)
                        break
            
            # Start the game
            self.reset_game()
            self.state_manager.start_game_session()
            self.state_manager.change_state(GameState.PLAYING)
            self.state_manager.enhanced_menu.start_battle_music()
            
            # Setup synchronizer
            self.game_synchronizer.set_local_player_id(local_id)
            self.game_synchronizer.set_game_references(
                self.player, self.bullet_manager, 
                self.enemy_manager, self.effects_manager
            )
            
            # Configure enemy manager for network play
            self.enemy_manager.set_network_mode(
                is_host=self.multiplayer_lobby.is_host,
                game_synchronizer=self.game_synchronizer
            )
    
    def _on_bullet_fired(self, bullet):
        """Called when a bullet is fired (for multiplayer synchronization)."""
        if self.is_multiplayer and self.game_synchronizer:
            local_player_id = self.multiplayer_lobby.get_local_player_id()
            if local_player_id:
                self.game_synchronizer.on_bullet_fired(bullet, local_player_id)
    
    def _on_explosion(self, x, y, color, radius=50, small=False):
        """Called when an explosion occurs (for multiplayer synchronization)."""
        if self.is_multiplayer and self.game_synchronizer:
            # Convert explosion parameters for network sync
            damage = 50 if not small else 25  # Estimate damage based on explosion size
            self.game_synchronizer.on_explosion(x, y, radius, damage)
    
    def _on_muzzle_flash(self, x, y, angle, weapon_type):
        """Called when a muzzle flash occurs (for multiplayer synchronization)."""
        if self.is_multiplayer and self.game_synchronizer:
            self.game_synchronizer.on_muzzle_flash(x, y, angle, weapon_type)

    def _on_bullet_hit(self, x, y):
        """Called when a bullet hits an enemy (for multiplayer synchronization)."""
        if self.is_multiplayer and self.game_synchronizer:
            self.game_synchronizer.on_bullet_hit(x, y)

    def _send_enemy_updates(self):
        """Send enemy position updates to clients (host only)."""
        if not hasattr(self, '_last_enemy_sync_time'):
            self._last_enemy_sync_time = 0.0
        
        current_time = self.game_time
        # Send enemy updates every 0.1 seconds (10 times per second)
        if current_time - self._last_enemy_sync_time < 0.1:
            return
        
        self._last_enemy_sync_time = current_time
        
        # Send updates for all living enemies
        for enemy in self.enemy_manager.get_enemies():
            if enemy.is_alive():
                self.game_synchronizer.send_enemy_update(enemy)

    # Camera system compatibility properties
    @property
    def camera_x(self):
        return self.camera_system.camera_x
    
    @camera_x.setter
    def camera_x(self, value):
        self.camera_system.camera_x = value
    
    @property
    def camera_y(self):
        return self.camera_system.camera_y
    
    @camera_y.setter
    def camera_y(self, value):
        self.camera_system.camera_y = value
    
    @property
    def camera_offset(self):
        return self.camera_system.camera_offset
    
    @camera_offset.setter
    def camera_offset(self, value):
        self.camera_system.camera_offset = value
    
    @property
    def base_zoom(self):
        return self.camera_system.base_zoom
    
    @base_zoom.setter
    def base_zoom(self, value):
        self.camera_system.base_zoom = value
    
    # Visual effects system compatibility properties
    @property
    def contrast_fade_effect(self):
        return self.visual_effects.combat_contrast_active
    
    @property
    def hit_border_effect(self):
        return self.visual_effects.hit_border_timer
    
    @property
    def vignette_effect(self):
        return self.visual_effects.vignette_enabled
    
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
            # Create AnimatedPlayer with default character instead of basic Player
            print("No character selected, using geometric player")
            # Use AnimatedPlayer with default character to have proper combat and sprite capabilities
            try:
                # Try to use a default character (like 'cecil') if available
                default_character = 'cecil'
                char_path = self.character_manager.get_character_path(default_character)
                if char_path and os.path.exists(char_path):
                    char_config = self.character_manager.get_character_config(default_character)
                    # Load sprite to get dimensions
                    temp_sprite = pg.image.load(char_path)
                    frame_width = temp_sprite.get_width() // 3
                    frame_height = temp_sprite.get_height() // 4
                    
                    self.player = AnimatedPlayer(
                        0, 0, char_path,
                        frame_width, frame_height,
                        getattr(self, 'audio_manager', None),
                        default_character, 
                        default_character.title(),
                        char_config
                    )
                    print(f"Created default AnimatedPlayer with character: {default_character}")
                else:
                    # Create AnimatedPlayer without sprite (geometric rendering)
                    self.player = AnimatedPlayer(
                        0, 0, None,
                        32, 32,
                        getattr(self, 'audio_manager', None)
                    )
                    print("Created geometric AnimatedPlayer")
            except (ImportError, Exception) as e:
                # Fallback to basic player if AnimatedPlayer creation fails
                self.player = Player(0, 0)
                print(f"Fallback to basic Player: {e}")
            return
        
        # Get character sprite path
        char_path = self.character_manager.get_character_path(self.selected_character)
        
        if char_path and os.path.exists(char_path):
            # Create animated player with sprites at world center
            try:
                # Determine frame size by loading the sprite sheet
                temp_sprite = pg.image.load(char_path)
                frame_width = temp_sprite.get_width() // 3
                frame_height = temp_sprite.get_height() // 4
                
                char_display_name = self.character_manager.get_current_character_name()
                char_config = self.character_manager.get_character_config(self.selected_character)
                
                self.player = AnimatedPlayer(
                    0, 0,  # Spawn at world center (0,0 in player coordinate system = center)
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
        self.missile_manager = MissileManager(self.state_manager.enhanced_menu.audio_manager)
        
        # Set bullet manager fire rate based on player's weapon
        if hasattr(self.player, 'weapon_fire_rate'):
            self.bullet_manager.set_fire_rate(self.player.weapon_fire_rate)
            print(f"Set weapon fire rate: {self.player.weapon_fire_rate}")
        
        self.enemy_manager = EnemyManager(self.world_manager, spawn_point=(0, 0))
        
        # Pre-populate enemies at world borders for tactical gameplay
        self.enemy_manager.populate_enemies_on_start(
            screen_width=self.screen_width, 
            screen_height=self.screen_height, 
            player_pos=pg.Vector2(0, 0), 
            zoom_level=1.0
        )
        
        self.effects_manager = EffectsManager()
        self.collision_manager = CollisionManager()
        self.slash_effect_manager = SlashEffectManager()
        
        # Initialize atmospheric effects and set random atmosphere for new level
        self.atmospheric_effects = AtmosphericEffects(3840, 2160, self.state_manager.enhanced_menu.audio_manager)  # World dimensions
        # Pass player position directly - both systems use same coordinate system centered at (0,0)
        player_pos = (self.player.pos.x, self.player.pos.y) if hasattr(self, 'player') and self.player else None
        self.atmospheric_effects.set_random_atmosphere(player_pos)
        
        # Start new survival match tracking
        self.score_manager.start_new_match(self.game_time)
        
        # Clear all cores on the map but keep player's collected cores (currency)
        if self.world_manager and hasattr(self.world_manager, 'core_manager'):
            # Only clear cores and chests on the map, not the player's total
            self.world_manager.core_manager.clear_all_cores()
            print(f"Game reset - Player keeps {self.score_manager.player_rapture_cores} cores as currency")
        
        # Reset world manager objectives to prevent survival timer carryover
        if self.world_manager:
            self.world_manager.generate_new_level()
        
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
            
    def update_camera(self):
        """Update camera position to follow player with expanded boundary constraints for border visibility."""
        if self.player:
            # Camera follows player
            self.camera_x = self.player.pos.x
            self.camera_y = self.player.pos.y
            
            # Clamp camera to stay within world bounds considering screen size and zoom
            half_screen_width = (self.screen_width / self.base_zoom) / 2
            half_screen_height = (self.screen_height / self.base_zoom) / 2
            
            # Rectangular world bounds with 100-pixel visible border
            world_min_x, world_min_y = -1920, -1080
            world_max_x, world_max_y = 1920, 1080
            border_size = 100
            
            # Expand viewable area to include border
            viewable_min_x = world_min_x - border_size
            viewable_min_y = world_min_y - border_size
            viewable_max_x = world_max_x + border_size
            viewable_max_y = world_max_y + border_size
            
            # Ensure camera doesn't show beyond viewable boundaries (world + border)
            self.camera_x = max(viewable_min_x + half_screen_width, 
                              min(viewable_max_x - half_screen_width, self.camera_x))
            self.camera_y = max(viewable_min_y + half_screen_height, 
                              min(viewable_max_y - half_screen_height, self.camera_y))
            
    def handle_zoom_input(self, keys):
        """Handle camera zoom input."""
        zoom_speed = 0.02  # Zoom change per frame
        
        if keys[pg.K_EQUALS] or keys[pg.K_PLUS]:  # Zoom in
            self.base_zoom = min(self.max_zoom, self.base_zoom + zoom_speed)
        elif keys[pg.K_MINUS]:  # Zoom out
            self.base_zoom = max(self.min_zoom, self.base_zoom - zoom_speed)
            
    def get_world_camera_offset(self):
        """Get camera offset for world rendering centered on player."""
        # Calculate offset to center player on screen
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        # Simple camera offset without zoom modification
        offset_x = center_x - self.camera_x + self.camera_offset.x
        offset_y = center_y - self.camera_y + self.camera_offset.y
        
        return (offset_x, offset_y)
    
    def calculate_offset(self):
        """Calculate camera offset for rendering - wrapper for get_world_camera_offset."""
        return self.get_world_camera_offset()
    
    def screen_to_world_pos(self, screen_pos):
        """Convert screen coordinates to world coordinates."""
        screen_x, screen_y = screen_pos
        
        # Convert screen position to world position
        # The world is centered on the player, so we need to offset by camera position
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        # World position = camera position + (screen position - screen center)
        world_x = self.camera_x + (screen_x - center_x)
        world_y = self.camera_y + (screen_y - center_y)
        
        return (world_x, world_y)
    
    def calculate_angle_to_target(self, start_x: float, start_y: float, target_x: float, target_y: float) -> float:
        """Calculate angle in degrees from start position to target position."""
        import math
        dx = target_x - start_x
        dy = target_y - start_y
        return math.degrees(math.atan2(dy, dx))
    
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
                    # For all other states, let them handle escape first
                    # The global handler will run later if they don't handle it
                
                # Debug toggles (only in game)
                if self.state_manager.is_playing():
                    if event.key == pg.K_m:  # 'M' key to toggle map debug
                        self.world_manager.toggle_map_debug()
                        if event.key in self.keys_just_pressed:
                            self.keys_just_pressed.remove(event.key)
                    elif event.key == pg.K_F3:  # 'F3' key to toggle performance debug
                        self.show_debug_info = not self.show_debug_info
                        if event.key in self.keys_just_pressed:
                            self.keys_just_pressed.remove(event.key)
                
                # Handle character selection
                if self.state_manager.is_character_select():
                    result = self.character_selection.handle_input(event)
                    if result == "select":
                        # Character selected
                        self.selected_character = self.character_selection.get_selected_character()
                        self.character_manager.set_current_character(self.selected_character)
                        
                        # Update multiplayer lobby preferred character if we came from there
                        if self.state_manager.previous_state == GameState.MULTIPLAYER_LOBBY:
                            self.multiplayer_lobby.preferred_character = self.selected_character
                            # Update character selection index to match
                            if self.selected_character in self.multiplayer_lobby.available_characters:
                                self.multiplayer_lobby.character_selection = self.multiplayer_lobby.available_characters.index(self.selected_character)
                            # Return to multiplayer lobby
                            self.state_manager.change_state(GameState.MULTIPLAYER_LOBBY)
                        else:
                            # Regular single player flow - start game
                            self.reset_game()
                            self.state_manager.start_game_session()  # Mark game session as active
                            self.state_manager.change_state(GameState.PLAYING)
                            # Start battle music
                            self.state_manager.enhanced_menu.start_battle_music()
                    elif result == "back":
                        # Go back to previous screen
                        if self.state_manager.previous_state == GameState.MULTIPLAYER_LOBBY:
                            self.state_manager.change_state(GameState.MULTIPLAYER_LOBBY)
                        else:
                            # Go back to play mode selection
                            self.state_manager.change_state(GameState.PLAY_MODE_SELECT)
                            # Restore main menu music when backing out
                            self.state_manager.enhanced_menu.start_main_menu_music()
                        # ESC was handled by character selection - remove from keys_just_pressed to prevent fallback
                        if pg.K_ESCAPE in self.keys_just_pressed:
                            self.keys_just_pressed.remove(pg.K_ESCAPE)
                        # Skip further processing of this event to prevent menu from seeing it
                        continue
            
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pg.mouse.get_pos()
                    # Handle main menu mouse clicks
                    if self.state_manager.get_state() == GameState.MENU:
                        result = self.state_manager.enhanced_menu.handle_main_menu_mouse_click(mouse_pos)
                        if result:
                            if result == "single_player":
                                self.state_manager.change_state(GameState.CHARACTER_SELECT)
                            elif result == "local_multiplayer":
                                self.state_manager.change_state(GameState.LOCAL_MULTIPLAYER)
                            elif result == "online_multiplayer":
                                self.state_manager.change_state(GameState.MULTIPLAYER_LOBBY)
                            elif result == "load_game":
                                self.state_manager.change_state(GameState.SAVE_LOAD)
                            elif result == "settings":
                                self.state_manager.change_state(GameState.SETTINGS)
                            elif result == "quit":
                                # Show quit confirmation instead of directly quitting
                                self.state_manager.show_quit_confirmation(GameState.MENU)
                    # Handle settings menu mouse clicks
                    elif self.state_manager.get_state() == GameState.SETTINGS:
                        self.state_manager.enhanced_menu.handle_settings_mouse_click(mouse_pos)
                    # Handle play mode selection mouse clicks
                    elif self.state_manager.get_state() == GameState.PLAY_MODE_SELECT:
                        result = self.state_manager.enhanced_menu.handle_play_mode_input(pg.event.Event(pg.MOUSEBUTTONDOWN, {'button': 1, 'pos': mouse_pos}))
                        if result == "new_game":
                            self.state_manager.change_state(GameState.CHARACTER_SELECT)
                        elif result == "local_multiplayer":
                            self.state_manager.change_state(GameState.LOCAL_MULTIPLAYER)
                        elif result == "online_multiplayer":
                            self.state_manager.change_state(GameState.MULTIPLAYER_LOBBY)
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
                            # Character selected
                            self.selected_character = self.character_selection.get_selected_character()
                            self.character_manager.set_current_character(self.selected_character)
                            
                            # Update multiplayer lobby preferred character if we came from there
                            if self.state_manager.previous_state == GameState.MULTIPLAYER_LOBBY:
                                self.multiplayer_lobby.preferred_character = self.selected_character
                                # Update character selection index to match
                                if self.selected_character in self.multiplayer_lobby.available_characters:
                                    self.multiplayer_lobby.character_selection = self.multiplayer_lobby.available_characters.index(self.selected_character)
                                # Return to multiplayer lobby
                                self.state_manager.change_state(GameState.MULTIPLAYER_LOBBY)
                            else:
                                # Regular single player flow - start game
                                self.reset_game()
                                self.state_manager.start_game_session()  # Mark game session as active
                                self.state_manager.change_state(GameState.PLAYING)
                                self.state_manager.enhanced_menu.start_battle_music()
                        elif result == "back":
                            # Go back to previous screen
                            if self.state_manager.previous_state == GameState.MULTIPLAYER_LOBBY:
                                self.state_manager.change_state(GameState.MULTIPLAYER_LOBBY)
                            else:
                                self.state_manager.change_state(GameState.MENU)
                    # Handle multiplayer lobby mouse clicks
                    elif self.state_manager.is_multiplayer_lobby():
                        result = self.multiplayer_lobby.handle_mouse_click(mouse_pos)
                        if result == "character_select":
                            self.state_manager.change_state(GameState.CHARACTER_SELECT)
                    # Handle quit confirmation mouse clicks
                    elif self.state_manager.is_quit_confirmation():
                        if not self.state_manager.handle_quit_confirmation_mouse_click(mouse_pos):
                            self.running = False  # User confirmed quit
            
            elif event.type == pg.MOUSEMOTION:
                mouse_pos = pg.mouse.get_pos()
                # Handle main menu hover
                if self.state_manager.get_state() == GameState.MENU:
                    hovered_option = self.state_manager.enhanced_menu.check_mouse_hover_main_menu(mouse_pos)
                    if hovered_option is not None:
                        self.state_manager.enhanced_menu.main_menu_selection = hovered_option
            
            elif event.type == pg.MOUSEWHEEL:
                # Mouse wheel zoom control (only during gameplay)
                if self.state_manager.is_playing():
                    zoom_speed = 0.05  # Zoom sensitivity
                    if event.y > 0:  # Scroll up - zoom in
                        self.base_zoom = min(self.max_zoom, self.base_zoom + zoom_speed)
                    elif event.y < 0:  # Scroll down - zoom out
                        self.base_zoom = max(self.min_zoom, self.base_zoom - zoom_speed)
            
            # Handle enhanced menu system input for welcome, main menu, and settings
            if self.state_manager.get_state() == GameState.WELCOME:
                if not self.state_manager.handle_welcome_input(event):
                    self.running = False
            elif self.state_manager.get_state() == GameState.MENU:
                result = self.state_manager.enhanced_menu.handle_input(event)
                if result == "quit":
                    # Show quit confirmation instead of directly quitting
                    self.state_manager.show_quit_confirmation(GameState.MENU)
                    # Consume the ESC key to prevent immediate cancellation
                    if pg.K_ESCAPE in self.keys_just_pressed:
                        self.keys_just_pressed.remove(pg.K_ESCAPE)
                elif result == "resume_game":
                    # Resume the paused game
                    self.state_manager.change_state(GameState.PLAYING)
                elif result == "new_game":
                    self.state_manager.change_state(GameState.CHARACTER_SELECT)
                elif result == "play":
                    self.state_manager.change_state(GameState.PLAY_MODE_SELECT)
                elif result == "multiplayer":
                    self.state_manager.change_state(GameState.MULTIPLAYER_LOBBY)
                elif result == "leaderboard_back":
                    # ESC was handled by leaderboard - remove from keys_just_pressed to prevent fallback
                    if pg.K_ESCAPE in self.keys_just_pressed:
                        self.keys_just_pressed.remove(pg.K_ESCAPE)
                elif result is None and event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    # ESC was handled by a submenu (achievements, etc.) but result is None
                    # This means the submenu successfully processed ESC and went back to main menu
                    # We need to consume the ESC key to prevent the fallback handler from running
                    if pg.K_ESCAPE in self.keys_just_pressed:
                        self.keys_just_pressed.remove(pg.K_ESCAPE)
                elif not self.state_manager.handle_enhanced_menu_input(event):
                    self.running = False
            elif self.state_manager.get_state() == GameState.PLAY_MODE_SELECT:
                result = self.state_manager.enhanced_menu.handle_input(event)
                if result == "new_game":
                    self.state_manager.change_state(GameState.CHARACTER_SELECT)
                elif result == "local_multiplayer":
                    self.state_manager.change_state(GameState.LOCAL_MULTIPLAYER)
                elif result == "online_multiplayer":
                    self.state_manager.change_state(GameState.MULTIPLAYER_LOBBY)
                elif result == "back":
                    # ESC was handled by play mode selection - change state and completely stop processing this event
                    self.state_manager.change_state(GameState.MENU)
                    self.state_manager.enhanced_menu.set_state(MenuState.MAIN)
                    if pg.K_ESCAPE in self.keys_just_pressed:
                        self.keys_just_pressed.remove(pg.K_ESCAPE)
                    # Break out of event processing completely to prevent any further handling
                    break
            elif self.state_manager.get_state() == GameState.LOCAL_MULTIPLAYER:
                # Handle ESC key to go back to play mode selection
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    self.state_manager.change_state(GameState.PLAY_MODE_SELECT)
            elif self.state_manager.get_state() == GameState.SETTINGS:
                result = self.state_manager.enhanced_menu.handle_input(event)
                if result == "back":
                    # ESC was handled by settings - remove from keys_just_pressed to prevent fallback
                    if pg.K_ESCAPE in self.keys_just_pressed:
                        self.keys_just_pressed.remove(pg.K_ESCAPE)
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
            elif self.state_manager.get_state() == GameState.MULTIPLAYER_LOBBY:
                # Handle multiplayer lobby input
                result = self.multiplayer_lobby.handle_input(event)
                if result == "back":
                    self.state_manager.change_state(GameState.MENU)
                    # ESC was handled by multiplayer lobby - remove from keys_just_pressed to prevent fallback
                    if pg.K_ESCAPE in self.keys_just_pressed:
                        self.keys_just_pressed.remove(pg.K_ESCAPE)
                elif result == "character_select":
                    # Go to character selection from multiplayer lobby
                    self.state_manager.change_state(GameState.CHARACTER_SELECT)
                elif result == "start_game":
                    # Start multiplayer game
                    self._start_multiplayer_game()
        
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
            elif self.state_manager.get_state() == GameState.PLAY_MODE_SELECT:
                # Update play mode selection hover
                self.state_manager.enhanced_menu.update_play_mode_hover(mouse_pos)
            elif self.state_manager.is_paused():
                # Update pause menu hover
                self.state_manager.handle_pause_mouse_hover(mouse_pos)
            elif self.state_manager.is_character_select():
                # Update character selection hover
                self.character_selection.handle_mouse_hover(mouse_pos)
            elif self.state_manager.is_quit_confirmation():
                # Update quit confirmation hover
                self.state_manager.handle_quit_confirmation_mouse_hover(mouse_pos)
        
        # Additional hover check specifically for play mode selection to ensure initial responsiveness
        elif self.state_manager.get_state() == GameState.PLAY_MODE_SELECT:
            mouse_pos = pg.mouse.get_pos()
            # Always check hover for play mode selection, even when clicking
            self.state_manager.enhanced_menu.update_play_mode_hover(mouse_pos)
        
        # Handle legacy state-specific input (keeping for compatibility)
        if self.state_manager.is_game_over():
            if not self.state_manager.handle_game_over_input(self.keys_just_pressed):
                self.running = False
        elif self.state_manager.is_quit_confirmation():
            # Handle quit confirmation input
            result = self.state_manager.handle_quit_confirmation_input(self.keys_just_pressed)
            if not result:
                self.running = False  # User confirmed quit
            else:
                # ESC was handled by quit confirmation (to cancel) - consume it
                if pg.K_ESCAPE in self.keys_just_pressed:
                    self.keys_just_pressed.remove(pg.K_ESCAPE)
                
        elif self.state_manager.is_paused():
            # Don't process pause input on the same frame we just entered pause
            if not self.just_paused:
                # Check current state before handling input
                previous_state = self.state_manager.get_state()
                self.state_manager.handle_pause_input(self.keys_just_pressed)
                # Check if we transitioned from pause to menu (quit to main menu)
                if previous_state == GameState.PAUSED and self.state_manager.get_state() == GameState.MENU:
                    # End the current match since player quit to main menu
                    character_name = self.character_manager.current_character
                    if character_name and self.player and self.player.is_alive():
                        # Player quit while alive - record the match
                        final_record = self.score_manager.end_match(character_name, self.game_time)
                        print(f"Match ended (quit to menu): Score {final_record.score}, Wave {final_record.waves_survived}, Kills {final_record.enemies_killed}")
            else:
                self.just_paused = False  # Reset for next frame
        
        # Fallback ESC handler for states that didn't handle ESC themselves
        if pg.K_ESCAPE in self.keys_just_pressed:
            current_state = self.state_manager.get_state()
            if current_state in [GameState.CHARACTER_SELECT, GameState.SAVE_LOAD, GameState.GAME_OVER]:
                self.state_manager.show_quit_confirmation(current_state)
            elif current_state == GameState.MENU:
                # For menu state, only show quit confirmation if we're in main menu
                if self.state_manager.enhanced_menu.get_state() == MenuState.MAIN:
                    self.state_manager.show_quit_confirmation(current_state)
            
        elif self.state_manager.is_playing():
            # Handle continuous game input
            keys = pg.key.get_pressed()
            mouse_pos = pg.mouse.get_pos()
            world_mouse_pos = self.screen_to_world_pos(mouse_pos)  # Convert to world coordinates
            mouse_buttons = pg.mouse.get_pressed()
            
            # Handle camera zoom controls
            self.handle_zoom_input(keys)
            
            # Player input (if player exists)
            if self.player:
                if hasattr(self.player, 'handle_input'):
                    # Check if it's AnimatedPlayer or regular Player by checking method signature
                    import inspect
                    sig = inspect.signature(self.player.handle_input)
                    param_count = len(sig.parameters)
                    
                    if param_count >= 7:  # AnimatedPlayer (7 params including self)
                        self.player.handle_input(keys, world_mouse_pos, self.game_time, 
                                               self.effects_manager, self.add_camera_shake, mouse_buttons, self.bullet_manager)
                    else:  # Regular Player (5 params including self)
                        self.player.handle_input(keys, world_mouse_pos, self.game_time, self.effects_manager, self.add_camera_shake)
                
                # Auto-collect cores near player (no key press needed)
                collected_cores = self.world_manager.core_manager.try_collect_cores(self.player.pos)
                
                # Shooting (either left mouse button held or special attack triggered)
                should_fire = mouse_buttons[0] or getattr(self.player, 'fire_special_attack_shot', False)
                if should_fire:  # Left mouse button or special attack
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
                                # Check if special attack - based on current right mouse state and flags
                                is_special_attack = (getattr(self.player, 'using_special_attack', False) and 
                                                   getattr(self.player, 'fire_special_attack_shot', False))
                                
                                if is_special_attack:
                                    # Perform thrust attack with mystical beam
                                    self.perform_sword_thrust_attack(weapon_damage)
                                else:
                                    # Perform normal melee slash attack
                                    self.perform_sword_attack(weapon_damage)
                                
                                # Note: No sword sound files available in assets/sounds/sfx/weapons/sword/
                                
                                self.bullet_manager.last_shot_time = self.game_time
                                bullet_fired = True
                                
                                # Reset special attack flags after firing - but only if not continuing special attack
                                if hasattr(self.player, 'using_special_attack'):
                                    # For Sword, only reset using_special_attack if right mouse is not held
                                    if self.player.weapon_type == "Sword":
                                        if not mouse_buttons[2]:  # Right mouse not held
                                            self.player.using_special_attack = False
                                    else:
                                        self.player.using_special_attack = False
                                        
                                if hasattr(self.player, 'fire_special_attack_shot'):
                                    # For Sword, keep firing if right mouse is still held
                                    if self.player.weapon_type == "Sword" and mouse_buttons[2]:
                                        # Keep the flag true for continuous Sword special attack firing
                                        pass  
                                    else:
                                        self.player.fire_special_attack_shot = False
                        
                        # Handle grenade launcher (right mouse button for Assault Rifle) - separate from normal firing
                        grenade_fired = False
                        if self.player.weapon_type == "Assault Rifle" and weapon_manager.has_grenade_launcher(self.player.weapon_type):
                            # Use right mouse (index 2) for grenade - single click only, not held
                            right_mouse_pressed = mouse_buttons[2]
                            right_mouse_just_pressed = (right_mouse_pressed and 
                                                      not getattr(self.player, 'right_mouse_was_pressed_grenade', False))
                            
                            # Store the current state for next frame
                            self.player.right_mouse_was_pressed_grenade = right_mouse_pressed
                            
                            if right_mouse_just_pressed and self.player.can_fire_grenade():  # Single click only
                                if self.bullet_manager.can_shoot(self.game_time):
                                    # Fire grenade towards the mouse position
                                    mouse_screen_pos = pg.mouse.get_pos()
                                    target_world_pos = self.screen_to_world_pos(mouse_screen_pos)
                                    
                                    # Get grenade properties
                                    grenade_props = weapon_manager.get_grenade_properties(self.player.weapon_type)
                                    
                                    # Fire grenade using missile system (same as rockets but different appearance)
                                    self.missile_manager.fire_grenade(
                                        gun_tip.x, gun_tip.y,
                                        target_world_pos[0], target_world_pos[1],
                                        damage=grenade_props.get("damage", 45),
                                        explosion_radius=150,  # Same as rockets
                                        speed=grenade_props.get("projectile_speed", 600)
                                    )
                                    
                                    # Play rocket launcher firing sound for grenade launcher
                                    self.state_manager.enhanced_menu.audio_manager.play_weapon_fire_sound("Rocket Launcher")
                                    
                                    self.player.use_grenade_round()
                                    self.bullet_manager.last_shot_time = self.game_time
                                    grenade_fired = True
                                    
                                    # Reset special attack flags for Assault Rifle after grenade firing
                                    if hasattr(self.player, 'fire_special_attack_shot'):
                                        self.player.fire_special_attack_shot = False
                                    if hasattr(self.player, 'using_special_attack'):
                                        self.player.using_special_attack = False
                                    
                                    # Add grenade launcher muzzle flash
                                    self.effects_manager.add_explosion(gun_tip.x, gun_tip.y, (255, 150, 50), small=True)
                                    
                                    # Call multiplayer synchronization callback for explosion
                                    self._on_explosion(gun_tip.x, gun_tip.y, (255, 150, 50), 25, small=True)
                        
                        # Direct fix for Assault Rifle normal firing
                        if not grenade_fired and self.player.weapon_type == "Assault Rifle":
                            # Only fire bullets for left mouse, NOT for special attacks (which use grenade launcher)
                            is_special_attack_active = getattr(self.player, 'fire_special_attack_shot', False)
                            
                            # Only fire bullets if it's NOT a special attack (left mouse only)
                            if not is_special_attack_active and mouse_buttons[0]:
                                # Check fire rate timing for assault rifle
                                if self.bullet_manager.can_shoot(self.game_time):
                                    # Normal bullet shooting for Assault Rifle (always fire bullets, grenade launcher is separate)
                                    bullet_color = bullet_props["color"]
                                    
                                    bullet_fired = self.bullet_manager.shoot(
                                        gun_tip.x, gun_tip.y, self.player.angle, self.game_time, 
                                        damage=weapon_damage,
                                        speed=bullet_props["speed"],
                                        size_multiplier=bullet_props["size_multiplier"],
                                        color=bullet_color,
                                        penetration=bullet_props.get("penetration", 1),
                                        shape=bullet_props.get("shape", "standard"),
                                        range_limit=bullet_props.get("range", 800),
                                        weapon_type=self.player.weapon_type,
                                        special_attack=False,  # Assault Rifle bullets are never special attacks
                                        trail_enabled=False,
                                        trail_duration=0.0
                                    )
                                
                                    # Call multiplayer synchronization callback if bullet was fired
                                    if bullet_fired and self.bullet_manager.bullets:
                                        self._on_bullet_fired(self.bullet_manager.bullets[-1])
                                
                                    if bullet_fired:
                                        # Play assault rifle firing sound
                                        self.state_manager.enhanced_menu.audio_manager.play_weapon_fire_sound("Assault Rifle")
                                        
                                        self.effects_manager.add_assault_rifle_muzzle_flash(
                                            gun_tip.x, gun_tip.y, self.player.angle
                                        )
                                    
                                    # Use ammo only if bullet was actually fired
                                    if bullet_fired and hasattr(self.player, 'use_ammo'):
                                        self.player.use_ammo(self.bullet_manager)
                        
                        # Handle normal weapon firing (not grenade launcher)
                        if not grenade_fired:  # Only fire normal bullets if grenade wasn't fired
                            # Handle rocket launcher
                            if self.player.weapon_type == "Rocket Launcher":
                                if self.bullet_manager.can_shoot(self.game_time):
                                    # Check if special attack
                                    is_special_attack = getattr(self.player, 'using_special_attack', False)
                                    
                                    # Fire missile towards the mouse position
                                    mouse_screen_pos = pg.mouse.get_pos()
                                    # Convert screen coordinates to world coordinates properly
                                    target_world_pos = self.screen_to_world_pos(mouse_screen_pos)
                                    
                                    # Calculate special attack properties
                                    missile_damage = weapon_damage
                                    explosion_radius = 150  # Default radius
                                    
                                    if is_special_attack:
                                        # Get special attack properties from weapons.json
                                        special_config = weapon_manager.get_weapon_property(
                                            "Rocket Launcher", "special_attack", "damage_multiplier", 1.5
                                        )
                                        radius_multiplier = weapon_manager.get_weapon_property(
                                            "Rocket Launcher", "special_attack", "explosion_radius_multiplier", 2.0
                                        )
                                        
                                        missile_damage = int(weapon_damage * special_config)
                                        explosion_radius = int(150 * radius_multiplier)
                                    
                                    # Create missile (special or normal)
                                    self.missile_manager.fire_missile(
                                        gun_tip.x, gun_tip.y,
                                        target_world_pos[0], target_world_pos[1],
                                        damage=missile_damage,
                                        explosion_radius=explosion_radius,
                                        special_attack=is_special_attack
                                    )
                                    
                                    # Play rocket firing sound
                                    self.state_manager.enhanced_menu.audio_manager.play_weapon_fire_sound("Rocket Launcher")
                                    
                                    self.bullet_manager.last_shot_time = self.game_time
                                    bullet_fired = True
                                    
                                    # Reset special attack flags after firing  
                                    if hasattr(self.player, 'using_special_attack'):
                                        self.player.using_special_attack = False
                                    if hasattr(self.player, 'fire_special_attack_shot'):
                                        self.player.fire_special_attack_shot = False
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
                                        
                                        # Create individual pellet with special attack color override
                                        is_special_attack = getattr(self.player, 'using_special_attack', False)
                                        
                                        # Use intense bright red for shotgun special attacks
                                        pellet_color = bullet_props["color"]
                                        if is_special_attack and self.player.weapon_type == "Shotgun":
                                            pellet_color = (255, 0, 0)  # Bright intense red for special attack
                                        
                                        self.bullet_manager.bullets.append(
                                            self.bullet_manager.create_bullet(
                                                gun_tip.x, gun_tip.y, pellet_angle,
                                                damage=weapon_damage,
                                                speed=bullet_props["speed"],
                                                size_multiplier=bullet_props["size_multiplier"],
                                                color=pellet_color,
                                                penetration=bullet_props.get("penetration", 1),
                                                shape=bullet_props.get("shape", "standard"),
                                                range_limit=bullet_props.get("range", 800),
                                                weapon_type=self.player.weapon_type,
                                                special_attack=is_special_attack
                                            )
                                        )
                                
                                    # Update last shot time after firing all pellets
                                    self.bullet_manager.last_shot_time = self.game_time
                                    bullet_fired = True
                                    
                                    # Play shotgun firing sound
                                    self.state_manager.enhanced_menu.audio_manager.play_weapon_fire_sound("Shotgun")
                                    
                                    # Reset special attack flag after firing
                                    if hasattr(self.player, 'using_special_attack'):
                                        self.player.using_special_attack = False
                                    
                                    # Reset special attack fire trigger
                                    if hasattr(self.player, 'fire_special_attack_shot'):
                                        self.player.fire_special_attack_shot = False
                                    
                                    # Add spectacular shotgun muzzle flash effect
                                    self.effects_manager.add_shotgun_muzzle_flash(
                                        gun_tip.x, gun_tip.y, self.player.angle
                                    )
                                    # Call multiplayer synchronization callback for muzzle flash
                                    self._on_muzzle_flash(gun_tip.x, gun_tip.y, self.player.angle, "Shotgun")
                            else:
                                # Single bullet weapons (AR, SMG, Sniper, Minigun)
                                is_special_attack = getattr(self.player, 'using_special_attack', False)
                                
                                # Use intense bright red for special attacks
                                bullet_color = bullet_props["color"]
                                if is_special_attack:
                                    bullet_color = (255, 0, 0)  # Bright intense red for special attack
                                
                                # Special handling for SMG bouncing bullets
                                if self.player.weapon_type == "SMG" and is_special_attack:
                                    # Get SMG special attack configuration
                                    range_multiplier = weapon_manager.get_weapon_property(
                                        "SMG", "special_attack", "range_multiplier", 0.5
                                    )
                                    max_bounces = weapon_manager.get_weapon_property(
                                        "SMG", "special_attack", "max_bounces", 1
                                    )
                                    bounce_range_mult = weapon_manager.get_weapon_property(
                                        "SMG", "special_attack", "bounce_range_multiplier", 0.5
                                    )
                                    enemy_targeting = weapon_manager.get_weapon_property(
                                        "SMG", "special_attack", "enemy_targeting", True
                                    )
                                    
                                    # Calculate reduced range and bounce range
                                    base_range = bullet_props.get("range", 675)
                                    reduced_range = int(base_range * range_multiplier)  # 50% of 675 = 337.5
                                    bounce_range = int(reduced_range * bounce_range_mult)  # 50% of reduced = 168.75
                                    
                                    # Fire two parallel streams for special attack
                                    import math
                                    
                                    # Both streams aim straight ahead (same angle as player)
                                    stream1_angle = self.player.angle
                                    stream2_angle = self.player.angle
                                    
                                    # Calculate offset positions perpendicular to the aim direction
                                    offset_distance = 30  # Distance to spread the streams apart
                                    perpendicular_angle = self.player.angle + 90  # 90 degrees to the side
                                    perp_rad = math.radians(perpendicular_angle)
                                    
                                    # Get base gun tip position
                                    base_tip = self.player.get_gun_tip_position()
                                    
                                    # Calculate offset positions for each stream (spread perpendicular to aim)
                                    offset_x = math.cos(perp_rad) * offset_distance
                                    offset_y = math.sin(perp_rad) * offset_distance
                                    
                                    stream1_tip = pg.Vector2(base_tip.x - offset_x, base_tip.y - offset_y)  # Left stream
                                    stream2_tip = pg.Vector2(base_tip.x + offset_x, base_tip.y + offset_y)  # Right stream
                                    
                                    # Fire first stream normally (handles fire rate timing)
                                    stream1_color = (255, 20, 20) if is_special_attack else bullet_color  # Bright red
                                    bullet_fired_1 = self.bullet_manager.shoot(
                                        stream1_tip.x, stream1_tip.y, stream1_angle, self.game_time, 
                                        damage=weapon_damage,
                                        speed=bullet_props["speed"],
                                        size_multiplier=bullet_props["size_multiplier"],
                                        color=stream1_color,
                                        penetration=bullet_props.get("penetration", 1),
                                        shape=bullet_props.get("shape", "standard"),
                                        range_limit=reduced_range,
                                        weapon_type=self.player.weapon_type,
                                        special_attack=is_special_attack,
                                        bounce_enabled=True,
                                        max_bounces=max_bounces,
                                        bounce_range=bounce_range,
                                        enemy_targeting=enemy_targeting
                                    )
                                    
                                    # Fire second stream directly (bypass fire rate check for simultaneous dual stream)
                                    bullet_fired_2 = False
                                    if bullet_fired_1:  # Only fire second stream if first one succeeded
                                        stream2_color = (255, 100, 0) if is_special_attack else bullet_color  # Orange-red
                                        bullet2 = self.bullet_manager.create_bullet(
                                            stream2_tip.x, stream2_tip.y, stream2_angle, 
                                            damage=weapon_damage,
                                            speed=bullet_props["speed"],
                                            size_multiplier=bullet_props["size_multiplier"],
                                            color=stream2_color,
                                            penetration=bullet_props.get("penetration", 1),
                                            shape=bullet_props.get("shape", "standard"),
                                            range_limit=reduced_range,
                                            weapon_type=self.player.weapon_type,
                                            special_attack=is_special_attack,
                                            bounce_enabled=True,
                                            max_bounces=max_bounces,
                                            bounce_range=bounce_range,
                                            enemy_targeting=enemy_targeting
                                        )
                                        if bullet2:
                                            self.bullet_manager.bullets.append(bullet2)
                                            bullet_fired_2 = True
                                    
                                    # Both streams fired successfully
                                    bullet_fired = bullet_fired_1 or bullet_fired_2
                                    
                                    # Play SMG firing sound if either stream fired
                                    if bullet_fired:
                                        self.state_manager.enhanced_menu.audio_manager.play_weapon_fire_sound("SMG")
                                    
                                    # Call multiplayer synchronization callbacks for fired bullets
                                    if bullet_fired_1 and len(self.bullet_manager.bullets) >= 1:
                                        self._on_bullet_fired(self.bullet_manager.bullets[-2 if bullet_fired_2 else -1])  # First stream bullet
                                    if bullet_fired_2 and len(self.bullet_manager.bullets) >= 1:
                                        self._on_bullet_fired(self.bullet_manager.bullets[-1])  # Second stream bullet
                                else:
                                    # Normal bullet shooting for non-SMG weapons (other than Assault Rifle which has its own fix)
                                    if self.player.weapon_type != "Assault Rifle":
                                        bullet_fired = self.bullet_manager.shoot(
                                            gun_tip.x, gun_tip.y, self.player.angle, self.game_time, 
                                            damage=weapon_damage,
                                            speed=bullet_props["speed"],
                                            size_multiplier=bullet_props["size_multiplier"],
                                            color=bullet_color,
                                            penetration=bullet_props.get("penetration", 1),
                                            shape=bullet_props.get("shape", "standard"),
                                            range_limit=bullet_props.get("range", 800),
                                            weapon_type=self.player.weapon_type,
                                            special_attack=is_special_attack,
                                            trail_enabled=(self.player.weapon_type == "Sniper" and is_special_attack),
                                            trail_duration=3.0 if (self.player.weapon_type == "Sniper" and is_special_attack) else 0.0
                                        )
                                        
                                        # Call multiplayer synchronization callback if bullet was fired
                                        if bullet_fired and self.bullet_manager.bullets:
                                            self._on_bullet_fired(self.bullet_manager.bullets[-1])
                                        
                                        # Play weapon firing sound
                                        if bullet_fired:
                                            self.state_manager.enhanced_menu.audio_manager.play_weapon_fire_sound(self.player.weapon_type)
                            
                            # Add muzzle flash effects for specific weapons
                            if bullet_fired and self.player.weapon_type == "Assault Rifle":
                                self.effects_manager.add_assault_rifle_muzzle_flash(
                                    gun_tip.x, gun_tip.y, self.player.angle
                                )
                                # Call multiplayer synchronization callback for muzzle flash
                                self._on_muzzle_flash(gun_tip.x, gun_tip.y, self.player.angle, "Assault Rifle")
                            elif bullet_fired and self.player.weapon_type == "SMG":
                                self.effects_manager.add_smg_muzzle_flash(
                                    gun_tip.x, gun_tip.y, self.player.angle
                                )
                                # Call multiplayer synchronization callback for muzzle flash
                                self._on_muzzle_flash(gun_tip.x, gun_tip.y, self.player.angle, "SMG")
                            
                            # Reset special attack flags after firing  
                            if bullet_fired:
                                if hasattr(self.player, 'using_special_attack'):
                                    # For Sword, only reset using_special_attack if right mouse is not held
                                    if self.player.weapon_type == "Sword":
                                        if not mouse_buttons[2]:  # Right mouse not held
                                            self.player.using_special_attack = False
                                    else:
                                        self.player.using_special_attack = False
                                        
                                # Only reset fire_special_attack_shot if not SMG/Sword with right mouse held
                                if hasattr(self.player, 'fire_special_attack_shot'):
                                    # For SMG and Sword, keep firing if right mouse is still held
                                    if self.player.weapon_type in ["SMG", "Sword"] and mouse_buttons[2]:
                                        # Keep the flag true for continuous SMG/Sword special attack firing
                                        pass  
                                    else:
                                        self.player.fire_special_attack_shot = False
                        
                        # Only use ammo if bullet was actually fired (except for melee weapons, grenades, and assault rifle)
                        if bullet_fired and not grenade_fired and hasattr(self.player, 'use_ammo') and self.player.weapon_type not in ["Sword", "Assault Rifle"]:
                            # Special ammo handling for different weapons
                            if self.player.weapon_type == "SMG" and is_special_attack:
                                # Double ammo consumption for SMG special attacks (two streams)
                                self.player.use_ammo(self.bullet_manager)  # First shot
                                self.player.use_ammo(self.bullet_manager)  # Second shot
                            elif self.player.weapon_type == "Sniper":
                                # Only use ammo for special attacks, normal sniper shots are free
                                if is_special_attack:
                                    self.player.use_ammo(self.bullet_manager)  # Special attack uses ammo
                                # Normal sniper shots don't use ammo
                            else:
                                # All other weapons use ammo normally
                                self.player.use_ammo(self.bullet_manager)  # Normal single shot
                else:
                    # Fire button not pressed - stop continuous fire for minigun
                    if hasattr(self, 'bullet_manager') and hasattr(self, 'player'):
                        weapon_type = getattr(self.player, 'weapon_type', None)
                        self.bullet_manager.stop_continuous_fire(weapon_type)
                        # Reset minigun reload flag when firing stops
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
        
        # Add mystical sparkles around the slash
        gun_tip = self.player.get_gun_tip_position()
        self.effects_manager.add_mystical_slash_sparkles(gun_tip.x, gun_tip.y, self.player.angle, sword_range)
        
        # No instant damage - the slash effect itself will handle damage continuously
    
    def perform_sword_thrust_attack(self, damage):
        """Perform a special sword thrust attack with mystical beam effect."""
        import math
        
        # Get special attack properties from weapon manager
        thrust_range = weapon_manager.get_weapon_property(self.player.weapon_type, 'special_attack', 'range', 500)
        damage_multiplier = weapon_manager.get_weapon_property(self.player.weapon_type, 'special_attack', 'damage_multiplier', 1.3)
        beam_width = weapon_manager.get_weapon_property(self.player.weapon_type, 'special_attack', 'beam_width', 15)
        beam_duration = weapon_manager.get_weapon_property(self.player.weapon_type, 'special_attack', 'beam_duration', 0.4)
        beam_color = weapon_manager.get_weapon_property(self.player.weapon_type, 'special_attack', 'beam_color', [100, 255, 200])
        
        # Calculate enhanced damage
        thrust_damage = damage * damage_multiplier
        
        # Create mystical beam effect
        self.create_mystical_beam_effect(thrust_range, beam_width, beam_duration, beam_color, thrust_damage)
        
        # Add mystical sparkles around the thrust
        gun_tip = self.player.get_gun_tip_position()
        self.effects_manager.add_mystical_thrust_sparkles(gun_tip.x, gun_tip.y, self.player.angle, thrust_range)
    
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
            
            # Add BURST points to player when hitting enemy
            if hasattr(self.player, 'add_burst_points'):
                self.player.add_burst_points(1)
            
            # Check if enemy died and remove
            if not enemy.is_alive():
                # Add explosion/death particles at enemy position BEFORE removal
                self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 100))  # Purple-ish explosion
                self.effects_manager.add_sword_impact_effect(enemy.pos.x, enemy.pos.y)  # Sword-specific death effect
                self.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.score_manager.add_kill_score(10)  # Use score manager instead of direct score tracking
        
        # Add screen shake for sword impacts
        if enemies_hit:
            self.add_camera_shake(0.4, 0.2)
    
    def check_beam_damage(self):
        """Check for continuous damage from active mystical beam effects."""
        # Get damage events from all active beam effects
        damage_events = self.effects_manager.check_beam_damage(self.enemy_manager.enemies)
        
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
            if hasattr(self.player, 'add_burst_points'):
                self.player.add_burst_points(1)
            
            # Check if enemy died and remove
            if not enemy.is_alive():
                # Add explosion/death particles at enemy position BEFORE removal
                self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 100))  # Purple-ish explosion
                self.effects_manager.add_sword_impact_effect(enemy.pos.x, enemy.pos.y)  # Sword-specific death effect
                self.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.score_manager.add_kill_score(10)  # Use score manager instead of direct score tracking
        
        # Add screen shake for beam impacts
        if enemies_hit:
            self.add_camera_shake(0.3, 0.15)
    
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
            
            # Add BURST points to player when hitting enemy
            if hasattr(self.player, 'add_burst_points'):
                self.player.add_burst_points(1)
            
            # Check if enemy died and remove
            if not enemy.is_alive():
                # Add appropriate explosion/death particles at enemy position BEFORE removal
                if damage_type == 'missile_body':
                    self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 150, 0))  # Orange explosion for missile hit
                else:  # explosion damage
                    self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 50))  # Red-orange explosion for missile explosion
                
                self.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.score_manager.add_kill_score(10)  # Use score manager instead of direct score tracking
        
        # Add screen shake for missile impacts
        if enemies_hit:
            impact_intensity = 0.6 if any(event['type'] == 'explosion' for event in damage_events) else 0.3
            self.add_camera_shake(impact_intensity, 0.3)
    
    def check_ground_fire_damage(self):
        """Check for damage from persistent ground fire effects."""
        if not self.missile_manager.ground_fires:
            return
        
        # Get damage events from all active ground fires
        damage_events = self.missile_manager.check_ground_fire_damage(
            self.enemy_manager.enemies, self.game_time
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
            
            # Add fire damage effect at enemy position
            self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 120, 0))
            
            # Check if enemy died from ground fire
            if not enemy.is_alive():
                self.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.score_manager.add_kill_score(10)  # Use score manager instead of direct score tracking
                
                # Add death explosion
                self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 100))
    
    def check_burning_trail_damage(self):
        """Check for damage from burning trail effects from sniper special attacks."""
        if not self.bullet_manager.burning_trails:
            return
        
        # Get damage events from all active burning trails
        damage_events = self.bullet_manager.check_burning_trail_damage(
            self.enemy_manager.enemies, self.game_time
        )
        
        kills = 0
        
        # Process each damage event
        for enemy, damage in damage_events:
            # Deal damage to the enemy
            enemy.take_damage(damage)
            
            # Add burning damage effect at enemy position (orange fire)
            self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 120, 30))
            
            # Check if enemy died from burning trail
            if not enemy.is_alive():
                self.enemy_manager.remove_enemy(enemy)
                kills += 1
                self.score_manager.add_kill_score(10)  # Use score manager instead of direct score tracking
                
                # Add death explosion
                self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (255, 100, 100))
    
    def create_slash_effect(self, sword_range, slash_arc, damage):
        """Create a visual slash effect for the sword attack."""
        # Pass player reference and damage so slash follows player movement and deals damage
        self.slash_effect_manager.create_slash(
            self.player,  # Pass player reference
            0,  # Relative angle offset (0 = follows player direction exactly)
            sword_range,
            damage  # Pass damage value to the slash effect
        )
    
    def create_mystical_beam_effect(self, beam_range, beam_width, beam_duration, beam_color, damage):
        """Create a mystical beam effect for sword thrust attack."""
        import math
        
        # Get player position and direction
        gun_tip = self.player.get_gun_tip_position()
        angle_rad = math.radians(self.player.angle)
        
        # Calculate beam end position
        end_x = gun_tip.x + beam_range * math.cos(angle_rad)
        end_y = gun_tip.y + beam_range * math.sin(angle_rad)
        
        # Add the mystical beam visual effect - pass player reference for following
        self.effects_manager.add_mystical_beam(
            self.player,  # Pass player reference instead of coordinates
            0.0,          # Relative angle (0 = forward direction)
            beam_range, beam_width, beam_duration, beam_color, damage
        )
        
        # No instant damage - the beam effect will handle damage continuously like the slash effect
    
    def check_beam_collision(self, start_x, start_y, end_x, end_y, beam_width, damage):
        """Check for enemy collisions along the mystical beam path."""
        import math
        
        # Calculate beam direction and length
        beam_dx = end_x - start_x
        beam_dy = end_y - start_y
        beam_length = math.sqrt(beam_dx**2 + beam_dy**2)
        
        if beam_length == 0:
            return
        
        # Normalize beam direction
        beam_dx /= beam_length
        beam_dy /= beam_length
        
        kills = 0
        enemies_hit = []
        
        # Check each enemy for collision with the beam
        for enemy in self.enemy_manager.get_enemies():
            # Calculate distance from enemy to beam line
            to_enemy_x = enemy.pos.x - start_x
            to_enemy_y = enemy.pos.y - start_y
            
            # Project enemy position onto beam line
            projection = to_enemy_x * beam_dx + to_enemy_y * beam_dy
            
            # Check if projection is within beam length
            if 0 <= projection <= beam_length:
                # Calculate perpendicular distance
                closest_x = start_x + projection * beam_dx
                closest_y = start_y + projection * beam_dy
                
                distance = math.sqrt((enemy.pos.x - closest_x)**2 + (enemy.pos.y - closest_y)**2)
                
                # Check if enemy is within beam width and hasn't been hit recently
                if distance <= (beam_width / 2 + enemy.size) and enemy not in enemies_hit:
                    # Deal damage to the enemy
                    enemy.take_damage(damage)
                    enemies_hit.append(enemy)
                    
                    # Add BURST points to player when hitting enemy
                    if hasattr(self.player, 'add_burst_points'):
                        self.player.add_burst_points(1)
                    
                    # Add mystical impact effect
                    self.effects_manager.add_mystical_impact_effect(enemy.pos.x, enemy.pos.y)
                    
                    # Check if enemy died and remove
                    if not enemy.is_alive():
                        # Add explosion/death particles at enemy position BEFORE removal
                        self.effects_manager.add_explosion(enemy.pos.x, enemy.pos.y, (100, 255, 200))  # Mystical green explosion
                        self.effects_manager.add_sword_impact_effect(enemy.pos.x, enemy.pos.y)
                        self.enemy_manager.remove_enemy(enemy)
                        kills += 1
                        self.score_manager.add_kill_score(10)  # Use score manager instead of direct score tracking
        
        # Add screen shake for mystical beam impacts
        if enemies_hit:
            screen_shake_intensity = min(5 + len(enemies_hit) * 2, 15)
            self.effects_manager.add_screen_shake(screen_shake_intensity, 0.3)
    
    def check_missile_enemy_collisions(self):
        """Check for missile collisions with enemies and handle explosions."""
        from src.effects.missile_system import MissileState  # Import here to avoid circular imports
        
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
                explosion_pos = (missile.pos.x, missile.pos.y)  # Store missile position for explosion effect
                
                for enemy in self.enemy_manager.get_enemies():
                    distance = (missile.pos - enemy.pos).length()
                    if distance <= explosion_radius:
                        was_alive = enemy.is_alive()
                        
                        # Apply explosion damage
                        enemy.take_damage(missile.damage)
                        if was_alive and not enemy.is_alive():
                            kills += 1
                
                # Add explosion effect at missile position (not enemy position)
                self.effects_manager.add_explosion(explosion_pos[0], explosion_pos[1])
                
                # Add screen shake for explosion
                self.add_camera_shake(0.4, 0.4)
                
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
        # Performance monitoring
        self.fps_counter += 1
        self.fps_timer += self.dt
        if self.fps_timer >= 1.0:  # Update FPS every second
            self.current_fps = int(self.fps_counter / self.fps_timer)
            self.fps_counter = 0
            self.fps_timer = 0.0
        
        # Always update state manager for menu animations
        self.state_manager.update(self.dt)
        
        # Update multiplayer lobby if active
        current_state = self.state_manager.get_state()
        if current_state == GameState.MULTIPLAYER_LOBBY:
            self.multiplayer_lobby.update(self.dt)
            # Check for game start even when no input events occur
            game_start_result = self.multiplayer_lobby.check_game_start_status()
            if game_start_result:
                if game_start_result == "start_game":
                    # Removed debug statement
                    self._start_multiplayer_game()
        else:
            # Only print state changes to avoid spam
            if hasattr(current_state, 'name'):
                state_name = current_state.name
            else:
                state_name = str(current_state)
            if not hasattr(self, '_last_debug_state') or self._last_debug_state != state_name:
                self._last_debug_state = state_name
        
        # Update multiplayer synchronization during gameplay
        if self.is_multiplayer and self.game_synchronizer and self.state_manager.is_playing():
            self.game_synchronizer.update(self.dt)
            # Get network players for rendering
            self.multiplayer_players = self.game_synchronizer.get_network_players()
            
            # Debug: Log multiplayer state every 10 seconds (reduced frequency)
            if hasattr(self, 'game_time') and self.game_time % 10.0 < self.dt:
                print(f"[MULTIPLAYER] is_multiplayer={self.is_multiplayer}, network_players={len(self.multiplayer_players)}, is_host={getattr(self.multiplayer_lobby, 'is_host', 'N/A')}")
                # Removed per-player position logging to reduce spam
            
            # Sync enemies if host (host authoritative)
            if self.multiplayer_lobby and self.multiplayer_lobby.is_host:
                self.enemy_manager.sync_enemies_to_network(self.game_time)
        
        if self.state_manager.is_playing() and self.player:
            # Update camera shake
            self.update_camera_shake(self.dt)
            
            # Update camera position to follow player
            self.update_camera()
            
            # Update world manager (NPCs, objectives, etc.)
            keys_pressed = pg.key.get_pressed()
            self.world_manager.update(self.dt, self.player.pos, keys_pressed)
            
            # Only end match when player dies - no objective completion
            # (Removed objective completion check for pure survival mode)
            
            # Update core system (replaces resource system) - pass player position and score manager for auto pickup
            self.world_manager.core_manager.update(self.dt, self.player.pos, self.score_manager)
            
            # Update player
            self.player.update(self.dt, self.bullet_manager, self.world_manager)
            
            # Add footprints for snow atmosphere with proper timing
            if hasattr(self.player, 'velocity') and self.player.velocity.length() > 30:  # Lower threshold for walking
                # Add footprints on a timer (every 0.3 seconds when moving)
                if not hasattr(self, 'last_footprint_time'):
                    self.last_footprint_time = 0
                
                # Footprints have been removed from new atmospheric effects system
            
            # Update managers
            self.bullet_manager.update(self.dt, self.game_time, self.world_manager)
            
            # Missiles handle their own explosions automatically
            self.missile_manager.update(self.dt, self.enemy_manager.get_enemies())
            
            # Enemy management: Only host manages enemies in multiplayer, clients receive updates
            if not self.is_multiplayer or (self.multiplayer_lobby and self.multiplayer_lobby.is_host):
                # Single player or multiplayer host: Update enemy AI, spawning, etc.
                self.enemy_manager.update(self.dt, self.player.pos, self.game_time, self.bullet_manager,
                                         self.base_zoom, self.screen_width, self.screen_height)
                if self.is_multiplayer and self.game_time % 15.0 < self.dt:  # Log every 15 seconds (reduced)
                    print(f"[ENEMY_SYNC] Host managing {len(self.enemy_manager.get_enemies())} enemies")
                
                # Send enemy position updates to clients (host only)
                if self.is_multiplayer and self.game_synchronizer:
                    self._send_enemy_updates()
            else:
                # Multiplayer client: Only update enemy rendering/animation, not AI or spawning
                # The actual enemy positions come from host via GameStateSynchronizer
                self.enemy_manager.update_render_only(self.dt)
                if self.game_time % 15.0 < self.dt:  # Log every 15 seconds (reduced)
                    enemy_count = len(self.enemy_manager.get_enemies()) if hasattr(self.enemy_manager, 'get_enemies') else 0
                    print(f"[ENEMY_SYNC] Client has {enemy_count} enemies from network")
            
            # Sync game state in multiplayer
            if self.is_multiplayer and self.game_synchronizer:
                # Sync wave updates (host only)
                if self.multiplayer_lobby and self.multiplayer_lobby.is_host:
                    self.game_synchronizer.on_wave_update(
                        self.enemy_manager.wave, 
                        self.enemy_manager.enemies_killed,
                        self.enemy_manager.wave_timer
                    )
                
                # Sync score updates (all players)
                local_player_id = self.multiplayer_lobby.get_local_player_id()
                if local_player_id and hasattr(self.score_manager, 'get_current_score'):
                    current_score = self.score_manager.get_current_score()
                    self.game_synchronizer.on_score_update(
                        local_player_id,
                        current_score,
                        self.score_manager.player_rapture_cores,
                        self.enemy_manager.enemies_killed
                    )
            
            self.effects_manager.update(self.dt, self.player.pos)
            self.slash_effect_manager.update(self.dt)
            
            # Update atmospheric effects with player position for proper particle respawning
            # Both player and atmospheric systems use same coordinate system centered at (0,0)
            player_pos = (self.player.pos.x, self.player.pos.y) if self.player else None
            self.atmospheric_effects.update(self.dt, player_pos)
            
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
            
            # Check for continuous beam damage from active mystical beam effects
            self.check_beam_damage()
            
            # Check for continuous missile damage from visual effects (body hits and explosions)
            self.check_missile_visual_damage()
            
            # Check for ground fire damage from special missile explosions
            self.check_ground_fire_damage()
            
            # Check for burning trail damage from special sniper attacks
            self.check_burning_trail_damage()
            
            # Update game timer
            self.game_time += self.dt
            
            # Handle collisions
            if not self.is_multiplayer or (self.multiplayer_lobby and self.multiplayer_lobby.is_host):
                # Single player or multiplayer host: Full collision processing with enemy death authority
                kills = self.collision_manager.check_bullet_enemy_collisions(
                    self.bullet_manager, self.enemy_manager, self.player, self.effects_manager, self.world_manager, self._on_bullet_hit)
                
                # Handle missile collisions with enemies
                missile_kills = self.check_missile_enemy_collisions()
                kills += missile_kills
                
                # Handle minigun whip damage when at full speed
                if self.player.weapon_type == "Minigun" and self.minigun_effects_manager.whip_trail_active:
                    whip_kills = self.check_whip_damage()
                    kills += whip_kills
                
                # Add score for kills (10 points per enemy)
                if kills > 0:
                    # Add kills to score manager instead of direct score tracking
                    for _ in range(kills):
                        self.score_manager.add_kill_score(10)
            else:
                # Multiplayer client: Detect collisions but send damage to host instead of applying locally
                kills = self.collision_manager.check_bullet_enemy_collisions_network_client(
                    self.bullet_manager, self.enemy_manager, self.player, self.effects_manager, 
                    self.world_manager, self.game_synchronizer, self._on_bullet_hit)

            # Check bullet-chest collisions (all players can damage chests)
            bullets_to_remove = []
            for bullet in self.bullet_manager.bullets[:]:  # Copy to allow modification
                if bullet.type.value == "player":  # Only player bullets can damage chests
                    if self.world_manager.core_manager.check_bullet_chest_collision(bullet.get_rect(), bullet.damage):
                        bullets_to_remove.append(bullet)

            # Remove bullets that hit chests
            for bullet in bullets_to_remove:
                self.bullet_manager.remove_bullet(bullet)
            
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
                self.effects_manager.add_hit_effect(self.player.pos.x, self.player.pos.y, 0)
            
            # Check game over
            if not self.player.is_alive():
                # End the match and record it in the leaderboard
                character_name = self.character_manager.current_character
                if character_name:
                    final_record = self.score_manager.end_match(character_name, self.game_time)
                    print(f"Match ended! Final record: Score {final_record.score}, Wave {final_record.waves_survived}, Kills {final_record.enemies_killed}")
                
                # End the game session
                self.state_manager.end_game_session()
                
                self.state_manager.set_game_over_stats(
                    self.score_manager.current_match_score, 
                    self.enemy_manager.get_wave(), 
                    self.enemy_manager.get_kills()
                )
                self.state_manager.change_state(GameState.GAME_OVER)
    
    def render(self):
        """Render the game."""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Set appropriate cursor based on game state
        current_state = self.state_manager.get_state()
        if current_state in [GameState.WELCOME, GameState.MENU, GameState.PLAY_MODE_SELECT, GameState.SETTINGS, 
                           GameState.SAVE_LOAD, GameState.CHARACTER_SELECT, GameState.PAUSED, 
                           GameState.GAME_OVER, GameState.QUIT_CONFIRMATION]:
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
            
        elif self.state_manager.get_state() == GameState.PLAY_MODE_SELECT:
            self.state_manager.render_enhanced_menu()
            
        elif self.state_manager.get_state() == GameState.SETTINGS:
            self.state_manager.render_settings()
            
        elif self.state_manager.get_state() == GameState.SAVE_LOAD:
            self.state_manager.render_save_load()
            
        elif self.state_manager.is_character_select():
            self.character_selection.update(self.dt)
            self.character_selection.render(self.screen)
            
        elif self.state_manager.get_state() == GameState.MULTIPLAYER_LOBBY:
            self.multiplayer_lobby.render(self.screen)
            
        elif self.state_manager.get_state() == GameState.LOCAL_MULTIPLAYER:
            self._render_local_multiplayer()
            
        elif self.state_manager.is_playing():
            # Create a virtual surface for world rendering that can be scaled for zoom
            if self.base_zoom != 1.0:
                # Calculate the size of the virtual surface based on zoom
                # Zoom out = larger virtual surface, zoom in = smaller virtual surface
                virtual_width = int(self.screen_width / self.base_zoom)
                virtual_height = int(self.screen_height / self.base_zoom)
                virtual_surface = pg.Surface((virtual_width, virtual_height))
                virtual_surface.fill(BACKGROUND_COLOR)
                
                # Render everything to the virtual surface with adjusted offsets
                virtual_center_x = virtual_width // 2
                virtual_center_y = virtual_height // 2
                virtual_offset = (virtual_center_x - self.camera_x + self.camera_offset.x,
                                virtual_center_y - self.camera_y + self.camera_offset.y)
            else:
                # No zoom, render directly to screen
                virtual_surface = self.screen
                virtual_offset = self.get_world_camera_offset()
            
            # Render level-based world background
            if self.player:
                self.world_manager.render_world_background(
                    virtual_surface, self.camera_x, self.camera_y, 
                    virtual_surface.get_width(), virtual_surface.get_height()
                )
            
            # Render map tiles (above background, below everything else)
            self.world_manager.render_map(virtual_surface, virtual_offset)
            
            # Render cores and chests (above terrain, below player) - replaces resource nodes
            self.world_manager.core_manager.render(virtual_surface, virtual_offset)
            
            # Render NPCs (above terrain, below player)
            self.world_manager.render_npcs(virtual_surface, virtual_offset)
            
            # Render game objects with world offset
            if self.player:
                if hasattr(self.player, 'render') and len(self.player.render.__code__.co_varnames) > 3:
                    # AnimatedPlayer with offset support
                    self.player.render(virtual_surface, self.game_time, virtual_offset)
                else:
                    # Regular player
                    self.player.render(virtual_surface, self.game_time)
            
            # Render enemies (bottom layer)
            self.enemy_manager.render(virtual_surface, virtual_offset)
            
            # Render multiplayer players (above enemies, same layer as local player)
            if self.is_multiplayer and self.multiplayer_players:
                self.multiplayer_renderer.render_network_players(
                    virtual_surface, self.multiplayer_players, virtual_offset
                )
            
            # Render effects on top
            self.effects_manager.render(virtual_surface, virtual_offset)
            self.slash_effect_manager.render(virtual_surface, virtual_offset)
            
            # Render bullets and missiles LAST to make sure they're visible (temporary debug)
            self.bullet_manager.render(virtual_surface, virtual_offset)
            self.missile_manager.render(virtual_surface, virtual_offset)
            
            # Render network bullets for multiplayer
            if self.is_multiplayer and self.game_synchronizer:
                network_bullets = self.game_synchronizer.get_network_bullets()
                # Removed generic network bullet rendering - network bullets are now created in bullet manager with proper weapon appearance
                # if network_bullets:
                #     self.multiplayer_renderer.render_network_bullets(
                #         virtual_surface, network_bullets, virtual_offset
                #     )
            
            # Render minigun muzzle flames if active
            if self.player.weapon_type == "Minigun":
                # Get minigun bullets for whip trail rendering
                minigun_bullets = [bullet for bullet in self.bullet_manager.bullets 
                                 if hasattr(bullet, 'weapon_type') and bullet.weapon_type == 'Minigun']
                
                # Render whip trail lines between bullets
                self.minigun_effects_manager.render_whip_trail_lines(virtual_surface, minigun_bullets, virtual_offset)
                
                # Render trail sparks
                self.minigun_effects_manager.render_muzzle_flames(virtual_surface, virtual_offset)
            
            # Render shotgun fire trails if active
            if self.player.weapon_type == "Shotgun":
                # Get shotgun pellets for fire trail rendering
                shotgun_bullets = [bullet for bullet in self.bullet_manager.bullets 
                                 if hasattr(bullet, 'weapon_type') and bullet.weapon_type == 'Shotgun']
                
                # Render fire trail lines between pellets
                self.shotgun_effects_manager.render_fire_trail_lines(virtual_surface, shotgun_bullets, virtual_offset)
                
            # Shell casings disabled
            self.minigun_effects_manager.render_shell_casings(virtual_surface, virtual_offset)
            
            # Render atmospheric effects particles in world space (they need to be on the virtual surface)
            self.atmospheric_effects.render(virtual_surface, virtual_offset)
            
            # If we used a virtual surface, scale it to the screen
            if self.base_zoom != 1.0:
                scaled_surface = pg.transform.scale(virtual_surface, (self.screen_width, self.screen_height))
                self.screen.blit(scaled_surface, (0, 0))
            else:
                # No scaling needed, just blit the virtual surface
                self.screen.blit(virtual_surface, (0, 0))
            
            # Render atmospheric screen overlays (storm tint, lightning) on top of everything
            self.atmospheric_effects.render_screen_effects(self.screen)            # Render map debug overlay (after scaling)
            self.world_manager.render_map_debug(self.screen, self.calculate_offset())
            
            # Render game UI
            self.render_game_ui_clean()
            
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
            self.render_game_ui_clean()
            
            # Render multiplayer UI if active
            if self.is_multiplayer and self.multiplayer_players:
                local_player_id = self.multiplayer_lobby.get_local_player_id() if self.multiplayer_lobby else "local"
                self.multiplayer_renderer.render_multiplayer_ui(
                    self.screen, self.multiplayer_players, local_player_id
                )
            
            # Render pause overlay
            self.state_manager.render_pause()
            
        elif self.state_manager.is_game_over():
            self.state_manager.render_game_over()
        
        elif self.state_manager.is_quit_confirmation():
            # First render the background state (what we're potentially quitting from)
            if self.state_manager.quit_confirmation_from_state == GameState.MENU:
                self.state_manager.render_enhanced_menu()
            elif self.state_manager.quit_confirmation_from_state == GameState.CHARACTER_SELECT:
                self.character_selection.render(self.screen)
            elif self.state_manager.quit_confirmation_from_state == GameState.SETTINGS:
                self.state_manager.render_settings()
            elif self.state_manager.quit_confirmation_from_state == GameState.SAVE_LOAD:
                self.state_manager.render_save_load()
            elif self.state_manager.quit_confirmation_from_state == GameState.GAME_OVER:
                self.state_manager.render_game_over()
            
            # Then render the quit confirmation overlay on top
            self.state_manager.render_quit_confirmation()
        
        pg.display.flip()
    
    def draw_clean_ui_panel(self, rect: pg.Rect, alpha: int = 200):
        """Draw a clean UI panel with main menu styling."""
        # Panel background
        panel_surface = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
        panel_surface.fill((20, 20, 30, alpha))  # Dark semi-transparent
        self.screen.blit(panel_surface, rect.topleft)
        
        # Panel border
        pg.draw.rect(self.screen, (100, 100, 120), rect, 2, border_radius=8)

    def draw_ui_text_with_shadow(self, text: str, font: pg.font.Font, pos: tuple, 
                                color: tuple = (255, 255, 255), shadow_color: tuple = (40, 40, 50)):
        """Draw text with a subtle shadow for readability."""
        # Shadow
        shadow_surface = font.render(text, True, shadow_color)
        shadow_rect = shadow_surface.get_rect()
        shadow_rect.topleft = (pos[0] + 1, pos[1] + 1)
        self.screen.blit(shadow_surface, shadow_rect)
        
        # Main text
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.topleft = pos
        self.screen.blit(text_surface, text_rect)
        
        return text_rect

    def draw_progress_bar(self, rect: pg.Rect, progress: float, 
                         bg_color: tuple = (50, 50, 50), fill_color: tuple = (100, 255, 100),
                         border_color: tuple = (100, 100, 120)):
        """Draw a styled progress bar."""
        # Background
        pg.draw.rect(self.screen, bg_color, rect, border_radius=5)
        
        # Fill
        if progress > 0:
            fill_width = int(rect.width * progress)
            fill_rect = pg.Rect(rect.x, rect.y, fill_width, rect.height)
            pg.draw.rect(self.screen, fill_color, fill_rect, border_radius=5)
        
        # Border
        pg.draw.rect(self.screen, border_color, rect, 2, border_radius=5)

    def render_game_ui_clean(self):
        """Render cleaned up game UI with main menu styling."""
        
        # === TOP LEFT PANEL: Score and Wave ===
        top_panel_width = 300
        top_panel_height = 120
        top_panel_rect = pg.Rect(20, 20, top_panel_width, top_panel_height)
        self.draw_clean_ui_panel(top_panel_rect)
        
        # Score
        score_text = f"Score: {self.score_manager.current_match_score}"
        self.draw_ui_text_with_shadow(score_text, self.font, (35, 35))
        
        # Wave with progress bar
        if self.player:
            wave_text = f"Wave: {self.enemy_manager.wave}"
            self.draw_ui_text_with_shadow(wave_text, self.small_font, (35, 70))
            
            # Wave progress bar
            wave_progress = self.enemy_manager.get_wave_progress()
            time_to_next = self.enemy_manager.get_time_to_next_wave()
            
            progress_rect = pg.Rect(35, 95, 200, 12)
            progress_color = (255, 100, 100) if time_to_next < 5 else (100, 255, 100)
            self.draw_progress_bar(progress_rect, wave_progress, fill_color=progress_color)
            
            # Timer text
            timer_text = f"{time_to_next:.1f}s"
            self.draw_ui_text_with_shadow(timer_text, self.small_font, (250, 93), (180, 180, 180))
        
        # === BOTTOM RIGHT: Rapture Cores ===
        if self.score_manager and hasattr(self.score_manager, 'player_rapture_cores'):
            core_count = self.score_manager.player_rapture_cores
            core_text = f"Cores: {core_count}"
            
            # Calculate text size for positioning
            text_width, text_height = self.small_font.size(core_text)
            core_panel_width = text_width + 40  # Reduced width
            core_panel_height = 40
            
            # Position up and left to avoid control instructions overlap
            core_x = self.screen_width - core_panel_width - 20
            core_y = self.screen_height - core_panel_height - 80  # Moved up by 60px
            core_panel_rect = pg.Rect(core_x, core_y, core_panel_width, core_panel_height)
            
            self.draw_clean_ui_panel(core_panel_rect, alpha=180)
            
            # Core text with bright orange color (rapture cores color)
            text_x = core_x + 15
            text_y = core_y + (core_panel_height - text_height) // 2
            self.draw_ui_text_with_shadow(core_text, self.small_font, (text_x, text_y), (255, 140, 0))
        
        # === TOP RIGHT: Minimap and Objective ===
        # Render minimap first
        if self.player:
            npcs = self.world_manager.get_npcs()
            objectives = []
            if hasattr(self.world_manager, 'objectives'):
                objectives = self.world_manager.objectives
            elif hasattr(self.world_manager.core_manager, 'objectives'):
                objectives = self.world_manager.core_manager.objectives
            
            self.minimap.render(self.screen, 
                              (self.player.pos.x, self.player.pos.y),
                              enemies=self.enemy_manager.get_enemies(),
                              npcs=npcs,
                              objectives=objectives)
            
            # Objective panel under minimap
            minimap_bottom_y = self.minimap.margin + self.minimap.height + 10
            objective_text = "OBJECTIVE: SURVIVE"  # Static survival objective
            
            if objective_text:
                obj_text_width, obj_text_height = self.small_font.size(objective_text)
                obj_panel_width = obj_text_width + 20
                obj_panel_height = 35
                
                # Right-align to minimap edge (expand leftward)
                minimap_right_edge = self.screen_width - self.minimap.margin
                obj_x = minimap_right_edge - obj_panel_width
                obj_y = minimap_bottom_y
                obj_panel_rect = pg.Rect(obj_x, obj_y, obj_panel_width, obj_panel_height)
                
                self.draw_clean_ui_panel(obj_panel_rect, alpha=180)
                
                # Objective text (survival theme color)
                obj_color = (255, 200, 100)  # Warm survival color
                text_x = obj_x + 10
                text_y = obj_y + (obj_panel_height - obj_text_height) // 2
                self.draw_ui_text_with_shadow(objective_text, self.small_font, (text_x, text_y), obj_color)
        
        # === BOTTOM LEFT: Character and Controls (subtle) ===
        if self.selected_character:
            char_name = self.character_manager.get_current_character_name()
            if char_name:
                char_text = f"Playing as: {char_name}"
                self.draw_ui_text_with_shadow(char_text, self.small_font, (30, self.screen_height - 80), (180, 180, 180))
        
        # Controls hint (very subtle)
        controls_text = "WASD + Mouse • +/- Zoom"
        controls_width = self.small_font.size(controls_text)[0]
        self.draw_ui_text_with_shadow(controls_text, self.small_font, 
                                     (self.screen_width - controls_width - 20, self.screen_height - 30), 
                                     (120, 120, 120))
        
        # === DEBUG INFO (if enabled) ===
        if self.show_debug_info:
            debug_y = self.screen_height - 125
            
            # FPS counter
            fps_color = (0, 255, 0) if self.current_fps >= 45 else (255, 255, 0) if self.current_fps >= 30 else (255, 0, 0)
            fps_text = self.small_font.render(f"FPS: {self.current_fps}", True, fps_color)
            self.screen.blit(fps_text, (self.screen_width - 200, debug_y))
            
            # Enemy count
            enemy_count = len(self.enemy_manager.enemies) if self.enemy_manager else 0
            enemy_text = self.small_font.render(f"Enemies: {enemy_count}", True, (255, 255, 255))
            self.screen.blit(enemy_text, (self.screen_width - 200, debug_y + 25))
            
            # Bullet count
            bullet_count = len(self.bullet_manager.bullets) + len(self.bullet_manager.enemy_bullets)
            bullet_text = self.small_font.render(f"Bullets: {bullet_count}", True, (255, 255, 255))
            self.screen.blit(bullet_text, (self.screen_width - 200, debug_y + 50))
            
            # Performance status
            perf_status = "Good" if self.current_fps >= 45 else "Poor" if self.current_fps < 30 else "Fair"
            perf_color = fps_color
            perf_text = self.small_font.render(f"Performance: {perf_status}", True, perf_color)
            self.screen.blit(perf_text, (self.screen_width - 200, debug_y + 75))
            
            # Instructions
            debug_info_text = self.small_font.render("F3 to toggle debug", True, (150, 150, 150))
            self.screen.blit(debug_info_text, (self.screen_width - 200, debug_y + 100))
    
    def _render_local_multiplayer(self):
        """Render the local multiplayer screen with basic UI."""
        # Clear screen with background
        self.screen.fill((20, 25, 35))
        
        # Title
        title_font = pg.font.Font(None, 96)
        title_text = title_font.render("LOCAL MULTIPLAYER", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_font = pg.font.Font(None, 48)
        subtitle_text = subtitle_font.render("Coming Soon!", True, (255, 255, 100))
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, 300))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Description
        desc_font = pg.font.Font(None, 32)
        descriptions = [
            "Local multiplayer will support:",
            "• 2-4 players on the same screen",
            "• Player 1: WASD + Mouse",
            "• Player 2: Arrow Keys + Right Click", 
            "• Additional players with controller support"
        ]
        
        for i, desc in enumerate(descriptions):
            desc_text = desc_font.render(desc, True, (200, 200, 200))
            desc_rect = desc_text.get_rect(center=(self.screen_width // 2, 420 + i * 50))
            self.screen.blit(desc_text, desc_rect)
        
        # Back instruction
        back_font = pg.font.Font(None, 36)
        back_text = back_font.render("Press ESC to go back", True, (150, 255, 150))
        back_rect = back_text.get_rect(center=(self.screen_width // 2, 700))
        self.screen.blit(back_text, back_rect)
    
    def run(self):
        """Main game loop."""
        print("Starting Kingdom-Pygame Twin-Stick Shooter...")
        # print(f"Found characters: {self.character_manager.get_character_display_names()}")
        
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
"""
Enhanced menu system for KINGDOM CLEANUP: A NIKKE FAN GAME
Now modularized for better maintainability.
"""

import pygame as pg
import math
import os
import random
from typing import Optional, Dict, List, Tuple
from enum import Enum
from src.utils.save_manager import GameSaveManager, SaveSlot
from src.systems.audio_manager import AudioManager
from src.ui.menu_states import MenuState, MenuStateManager
from src.ui.achievement_ui import AchievementUI


class EnhancedMenuSystem:
    """Enhanced menu system with welcome screen, main menu, and settings."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize the enhanced menu system."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_state = MenuState.MAIN  # Start with main menu, skip welcome screen
        
        # Track previous game state to handle escape key properly
        self.came_from_paused_game = False
        
        # Animation states
        self.animation_time = 0.0
        self.grid_alpha = 30  # Base alpha for grid overlay
        
        # Clean white and dark gray color scheme
        self.primary_color = (255, 255, 255)    # Pure white
        self.secondary_color = (180, 180, 180)  # Light gray
        self.accent_color = (220, 220, 220)     # Off-white
        self.text_color = (240, 240, 240)       # Near white
        self.bg_color = (20, 20, 25)            # Very dark gray
        self.glow_color = (200, 200, 200)       # Light gray glow
        
        # Audio manager
        self.audio_manager = AudioManager()
        
        # Save manager
        self.save_manager = GameSaveManager()
        self.save_manager.apply_settings(self.audio_manager)
        
        # Achievement UI
        self.achievement_ui = AchievementUI(screen_width, screen_height)
        
        # Menu selection
        self.main_menu_selection = 0
        self.main_menu_options = ["LEADERBOARDS", "ACHIEVEMENTS", "SHOP", "PLAY", "THE OUTPOST", "SETTINGS", "QUIT"]
        
        # Play mode selection
        self.play_mode_selection = 0
        self.play_mode_options = ["SOLO", "LOCAL MULTIPLAYER", "ONLINE MULTIPLAYER"]
        self.play_mode_needs_hover_check = False  # Flag for initial hover detection
        
        # Save/Load menu
        self.save_load_selection = 0
        self.save_load_mode = "load"  # "load" or "save"
        
        # Settings
        self.settings_tab = 0  # 0=Audio, 1=Video, 2=Controls
        self.settings_selection = 0
        self.settings_tabs = ["AUDIO", "VIDEO", "CONTROLS"]
        
        # Video settings
        self.resolutions = ["1920x1080", "1600x900", "1366x768", "1280x720"]
        self.current_resolution = 0
        self.fullscreen = False
        
        # Control bindings (default)
        # Key binding state
        self.remapping_key = None  # Which key is being remapped
        self.key_bindings = {
            "move_up": pg.K_w,
            "move_down": pg.K_s,
            "move_left": pg.K_a,
            "move_right": pg.K_d,
            "dash": pg.K_LSHIFT,
            "burst": pg.K_e,
            "pause": pg.K_p
        }
        
        # Audio slider dragging state
        self.dragging_slider = None  # Which slider is being dragged (0 or 1, or None)
        self.mouse_held = False  # Track if mouse is being held down
        
        # Load menu assets
        self.load_assets()
        
        # Initialize fonts - pixel art style with crisp rendering
        self.title_font = pg.font.Font(None, 140)  # Larger for more impact
        self.subtitle_font = pg.font.Font(None, 48)  # Smaller for better hierarchy
        self.menu_font = pg.font.Font(None, 48)
        self.small_font = pg.font.Font(None, 32)
        self.large_font = pg.font.Font(None, 72)
        
        # Pixel art specific fonts - use None for crisp system font
        self.pixel_title_font = pg.font.Font(None, 96)  # Perfect pixel size
        self.pixel_subtitle_font = pg.font.Font(None, 40)  # Complementary pixel size
        
        # Colors - Clean White Theme (matching main menu)
        self.primary_color = (255, 255, 255)    # Pure white
        self.secondary_color = (180, 180, 180)  # Light gray
        self.accent_color = (220, 220, 220)     # Light accent
        self.text_color = (255, 255, 255)       # Bright white
        self.bg_color = (20, 20, 30)            # Dark background
        self.glow_color = (200, 200, 200)       # Light glow
        self.warning_color = (255, 100, 100)    # Red warning
        self.success_color = (100, 255, 100)    # Green success
    
    def set_dependencies(self, character_manager=None, score_manager=None):
        """Set external dependencies for advanced features like leaderboards."""
        if character_manager:
            self.character_manager = character_manager
        if score_manager:
            self.score_manager = score_manager
        
    def load_assets(self):
        """Load menu assets."""
        try:
            # Welcome screen assets
            self.welcome_bg = pg.image.load("assets/images/Menu/Welcome/menu-bkg.jpg")
            self.main_logo = pg.image.load("assets/images/Menu/Welcome/main-logo.png")
            self.secondary_logo = pg.image.load("assets/images/Menu/Welcome/secondary-logo.png")
            
            # Scale images appropriately
            self.welcome_bg = pg.transform.scale(self.welcome_bg, (self.screen_width, self.screen_height))
            
            # Scale logos to fit properly - main logo much smaller
            logo_scale = 0.4  # Increased main logo size for better readability
            self.main_logo = pg.transform.scale(
                self.main_logo, 
                (int(self.main_logo.get_width() * logo_scale),
                 int(self.main_logo.get_height() * logo_scale))
            )
            
            secondary_scale = 0.3  # Slightly smaller secondary logo
            self.secondary_logo = pg.transform.scale(
                self.secondary_logo,
                (int(self.secondary_logo.get_width() * secondary_scale),
                 int(self.secondary_logo.get_height() * secondary_scale))
            )
            
            # Load random main menu background
            self.load_random_main_menu_background()
            
            print("Menu assets loaded successfully")
            
        except Exception as e:
            print(f"Could not load menu assets: {e}")
            # Create placeholder surfaces
            self.welcome_bg = pg.Surface((self.screen_width, self.screen_height))
            self.welcome_bg.fill((20, 20, 40))
            self.main_logo = pg.Surface((400, 200))
            self.main_logo.fill((100, 100, 100))
            self.secondary_logo = pg.Surface((300, 100))
            self.secondary_logo.fill((80, 80, 80))
            # Default main menu background
            self.main_menu_bg = pg.Surface((self.screen_width, self.screen_height))
            self.main_menu_bg.fill((20, 20, 40))
    
    def load_random_main_menu_background(self):
        """Load a random background from the BKG folder for main menu."""
        # Disabled when using venetian blinds carousel - backgrounds are handled by the carousel system
        return
    
    def start_welcome_music(self):
        """Start playing welcome music."""
        self.audio_manager.play_music("assets/sounds/music/welcome.mp3")
    
    def start_main_menu_music(self):
        """Start playing main menu music."""
        self.audio_manager.play_music("assets/sounds/music/main-menu.mp3")
    
    def _get_random_battle_music(self) -> str:
        """Get a random battle music file from the battle music folder."""
        battle_music_dir = "assets/sounds/music/battle"
        try:
            # Get all .wav and .mp3 files from the battle music directory
            battle_files = []
            if os.path.exists(battle_music_dir):
                for file in os.listdir(battle_music_dir):
                    if file.lower().endswith(('.wav', '.mp3')):
                        battle_files.append(os.path.join(battle_music_dir, file))
            
            print(f"Found {len(battle_files)} battle music files: {battle_files}")
            
            # Return a random file if any exist, otherwise fallback to the battle folder file
            if battle_files:
                selected = random.choice(battle_files)
                print(f"Selected battle music: {selected}")
                return selected
            else:
                print("No battle files found, using fallback")
                return "assets/sounds/music/battle/battle.wav"  # Correct fallback path
        except Exception as e:
            print(f"Exception in _get_random_battle_music: {e}")
            return "assets/sounds/music/battle/battle.wav"  # Correct fallback path on error
    
    def start_battle_music(self):
        """Start playing battle music - randomly selected from battle music folder."""
        battle_music_file = self._get_random_battle_music()
        print(f"Starting battle music: {battle_music_file}")
        self.audio_manager.play_music(battle_music_file)
    
    def get_main_menu_option_rect(self, option_index: int) -> pg.Rect:
        """Get the rectangle for a main menu option in HoloCure horizontal layout."""
        # Match the layout from _render_clean_menu_options
        button_width = 180  # Updated to match HoloCure design
        button_height = 83  # Updated to match 1.5x taller buttons
        button_spacing = 60  # Updated to match HoloCure design
        total_width = len(self.main_menu_options) * button_width + (len(self.main_menu_options) - 1) * button_spacing
        start_x = (self.screen_width - total_width) // 2
        
        # Calculate menu bar area (matching _render_clean_menu_options)
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        menu_y = bar_y + (bar_height - button_height) // 2  # Center buttons vertically in the bar
        
        x_pos = start_x + option_index * (button_width + button_spacing)
        y_pos = menu_y
        
        return pg.Rect(x_pos, y_pos, button_width, button_height)
    
    def check_mouse_hover_main_menu(self, mouse_pos: tuple) -> int:
        """Check if mouse is hovering over a main menu option."""
        for i, option in enumerate(self.main_menu_options):
            option_rect = self.get_main_menu_option_rect(i)
            if option_rect.collidepoint(mouse_pos):
                return i
        return None
    
    def update_play_mode_hover(self, mouse_pos: tuple):
        """Update play mode selection based on mouse position and handle initial hover check."""
        hovered_option = self.check_mouse_hover_play_mode(mouse_pos)
        if hovered_option is not None:
            self.play_mode_selection = hovered_option
        
        # Handle initial hover check flag
        if self.play_mode_needs_hover_check:
            self.play_mode_needs_hover_check = False
    
    def check_mouse_hover_play_mode(self, mouse_pos: tuple) -> Optional[int]:
        """Check if mouse is hovering over a play mode option."""
        for i, option in enumerate(self.play_mode_options):
            option_rect = self.get_play_mode_option_rect(i)
            if option_rect.collidepoint(mouse_pos):
                return i
        return None
    
    def get_play_mode_option_rect(self, option_index: int) -> pg.Rect:
        """Get rectangle for play mode option that matches the horizontal rendering."""
        # Match the horizontal layout from _render_play_mode_options
        button_width = 380   # Very wide buttons to ensure text fits completely
        button_height = 83   # Same as in rendering
        button_spacing = 40  # Minimal spacing to fit the very wide buttons
        
        total_width = len(self.play_mode_options) * button_width + (len(self.play_mode_options) - 1) * button_spacing
        start_x = (self.screen_width - total_width) // 2
        
        # Position at same height as main menu
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        menu_y = bar_y + (bar_height - button_height) // 2
        
        x_pos = start_x + option_index * (button_width + button_spacing)
        
        return pg.Rect(x_pos, menu_y, button_width, button_height)
    
    def handle_main_menu_mouse_click(self, mouse_pos: tuple):
        """Handle mouse clicks on main menu options."""
        clicked_option = self.check_mouse_hover_main_menu(mouse_pos)
        if clicked_option is not None:
            self.main_menu_selection = clicked_option
            # Simulate enter key press for the selected option
            return self.main_menu_options[clicked_option].lower().replace(" ", "_")
        return None
    
    def get_settings_tab_rect(self, tab_index: int) -> pg.Rect:
        """Get the rectangle for a settings tab."""
        tab_y = 200
        tab_width = 200
        tab_spacing = 50
        total_tab_width = len(self.settings_tabs) * tab_width + (len(self.settings_tabs) - 1) * tab_spacing
        start_x = (self.screen_width - total_tab_width) // 2
        tab_x = start_x + tab_index * (tab_width + tab_spacing)
        return pg.Rect(tab_x, tab_y, tab_width, 50)
    
    def get_audio_slider_rect(self, setting_index: int) -> pg.Rect:
        """Get the rectangle for an audio slider."""
        content_y = 320  # Match the rendering start position
        y_pos = content_y + setting_index * 80
        # Make clickable area taller to include the handle (radius 8)
        return pg.Rect(self.screen_width // 2 + 50, y_pos + 2, 200, 36)
    
    def get_video_setting_rect(self, setting_index: int) -> pg.Rect:
        """Get the rectangle for a video setting button."""
        y_pos = 350 + setting_index * 80
        value_rect_center = (self.screen_width // 2 + 150, y_pos + 15)
        return pg.Rect(value_rect_center[0] - 50, value_rect_center[1] - 15, 100, 30)
    
    def handle_settings_mouse_click(self, mouse_pos: tuple):
        """Handle mouse clicks in settings menu."""
        # Check tab clicks
        clicked_tab = self.check_mouse_hover_settings_tabs(mouse_pos)
        if clicked_tab is not None:
            self.settings_tab = clicked_tab
            self.settings_selection = 0
            return
        
        # Handle setting-specific clicks based on current tab
        if self.settings_tab == 0:  # Audio
            self.handle_audio_mouse_click(mouse_pos)
        elif self.settings_tab == 1:  # Video
            self.handle_video_mouse_click(mouse_pos)
        elif self.settings_tab == 2:  # Controls
            self.handle_control_mouse_click(mouse_pos)
    
    def handle_audio_mouse_click(self, mouse_pos: tuple):
        """Handle mouse clicks on audio sliders."""
        for i in range(2):  # Music and SFX volume
            slider_rect = self.get_audio_slider_rect(i)
            if slider_rect.collidepoint(mouse_pos):
                # Calculate volume based on mouse X position
                relative_x = mouse_pos[0] - slider_rect.x
                volume_percent = max(0, min(100, int((relative_x / slider_rect.width) * 100)))
                
                if i == 0:  # Music Volume
                    self.audio_manager.set_music_volume(volume_percent / 100.0)
                elif i == 1:  # SFX Volume
                    self.audio_manager.set_sfx_volume(volume_percent / 100.0)
                
                self.settings_selection = i
                break
    
    def handle_video_mouse_click(self, mouse_pos: tuple):
        """Handle mouse clicks on video settings."""
        for i in range(2):  # Resolution and Fullscreen
            setting_rect = self.get_video_setting_rect(i)
            if setting_rect.collidepoint(mouse_pos):
                self.settings_selection = i
                if i == 0:  # Resolution
                    self.current_resolution = (self.current_resolution + 1) % len(self.resolutions)
                    self.apply_resolution_change()
                elif i == 1:  # Fullscreen
                    self.fullscreen = not self.fullscreen
                    self.apply_fullscreen_change()
                break
    
    def apply_resolution_change(self):
        """Apply resolution change to the game."""
        resolution_str = self.resolutions[self.current_resolution]
        new_width, new_height = map(int, resolution_str.split('x'))
        print(f"Changing resolution to: {new_width}x{new_height}")
        # Note: This requires the game to handle screen resize
        # We'll send an event to notify the main game loop
        resolution_event = pg.event.Event(pg.USEREVENT + 1, {'resolution': (new_width, new_height)})
        pg.event.post(resolution_event)
    
    def apply_fullscreen_change(self):
        """Apply fullscreen toggle to the game."""
        print(f"Toggling fullscreen: {self.fullscreen}")
        # Send fullscreen toggle event to main game loop
        fullscreen_event = pg.event.Event(pg.USEREVENT + 2, {'fullscreen': self.fullscreen})
        pg.event.post(fullscreen_event)
    
    def apply_resolution_change(self):
        """Apply resolution change to the game."""
        resolution_str = self.resolutions[self.current_resolution]
        width, height = map(int, resolution_str.split('x'))
        print(f"Changing resolution to: {width}x{height}")
        # Send resolution change event to main game loop
        resolution_event = pg.event.Event(pg.USEREVENT + 1, {'resolution': (width, height)})
        pg.event.post(resolution_event)
    
    def check_mouse_hover_main_menu(self, mouse_pos: tuple):
        """Check if mouse is hovering over main menu options and update selection."""
        for i in range(len(self.main_menu_options)):
            option_rect = self.get_main_menu_option_rect(i)
            if option_rect.collidepoint(mouse_pos):
                if self.main_menu_selection != i:
                    self.main_menu_selection = i
                return i
        return None
    
    def check_mouse_hover_leaderboard(self, mouse_pos: tuple):
        """Check if mouse is hovering over leaderboard entries and update selection."""
        if not hasattr(self, 'character_manager'):
            return None
            
        # Get character data sorted for leaderboard display (match the rendering logic exactly)
        character_list = self.character_manager.get_character_list()
        character_display_names = self.character_manager.get_character_display_names()
        
        if not character_list:
            return None
            
        # Create list of (character, display_name, best_score) tuples for sorting
        character_data = []
        for char_name, display_name in zip(character_list, character_display_names):
            best_score = self.score_manager.get_character_best_score(char_name)
            character_data.append((char_name, display_name, best_score if best_score is not None else 0))
        
        # Sort by best score (descending), then by display name (ascending) for ties
        character_data.sort(key=lambda x: (-x[2], x[1]))
        
        if not character_data:
            return None
        
        # Initialize selection if needed
        if not hasattr(self, 'leaderboard_selected'):
            self.leaderboard_selected = 0
        if not hasattr(self, 'leaderboard_scroll_offset'):
            self.leaderboard_scroll_offset = 0
            
        # Character entry dimensions (match the rendering code exactly)
        entry_height = 100
        entry_width = min(900, self.screen_width - 100)  # Reasonable row width, not full screen
        start_y = 200
        start_x = (self.screen_width - entry_width) // 2  # Center the row on screen
        
        # Calculate visible entries
        max_visible = max(1, (self.screen_height - start_y - 100) // entry_height)
        total_characters = len(character_data)
        
        # Check each visible entry
        for i in range(max_visible):
            data_index = i + self.leaderboard_scroll_offset
            if data_index >= total_characters:
                break
                
            y_pos = start_y + i * entry_height
            entry_rect = pg.Rect(start_x, y_pos, entry_width, entry_height - 10)
            
            if entry_rect.collidepoint(mouse_pos):
                if self.leaderboard_selected != data_index:
                    self.leaderboard_selected = data_index
                return data_index
                
        return None

    def check_mouse_hover_settings_tabs(self, mouse_pos: tuple):
        """Check if mouse is hovering over settings tabs and update selection."""
        for i in range(len(self.settings_tabs)):
            tab_rect = self.get_settings_tab_rect(i)
            if tab_rect.collidepoint(mouse_pos):
                if self.settings_tab != i:
                    self.settings_tab = i
                    self.settings_selection = 0  # Reset setting selection when switching tabs
                return i
        return None
    
    def check_mouse_hover_settings_items(self, mouse_pos: tuple):
        """Check if mouse is hovering over settings items and update selection."""
        if self.settings_tab == 0:  # Audio
            for i in range(2):  # 2 audio settings
                item_rect = self.get_audio_item_rect(i)
                if item_rect.collidepoint(mouse_pos):
                    self.settings_selection = i
                    return
        elif self.settings_tab == 1:  # Video
            for i in range(2):  # 2 video settings
                item_rect = self.get_video_item_rect(i)
                if item_rect.collidepoint(mouse_pos):
                    self.settings_selection = i
                    return
        else:  # Controls
            for i in range(len(self.key_bindings)):
                item_rect = self.get_control_item_rect(i)
                if item_rect.collidepoint(mouse_pos):
                    self.settings_selection = i
                    return
    
    def handle_settings_item_click(self, mouse_pos: tuple):
        """Handle clicks on individual settings items."""
        if self.settings_tab == 0:  # Audio
            for i in range(2):  # 2 audio settings
                slider_rect = self.get_audio_slider_rect(i)
                if slider_rect.collidepoint(mouse_pos):
                    # Start dragging this slider
                    self.dragging_slider = i
                    # Calculate new volume based on click position
                    click_x = mouse_pos[0] - slider_rect.x
                    new_value = int((click_x / slider_rect.width) * 100)
                    new_value = max(0, min(100, new_value))
                    
                    if i == 0:  # Music volume
                        self.audio_manager.set_music_volume(new_value / 100.0)
                    else:  # SFX volume
                        self.audio_manager.set_sfx_volume(new_value / 100.0)
                    self.save_manager.save_settings()
                    return
        elif self.settings_tab == 1:  # Video
            for i in range(2):  # 2 video settings
                item_rect = self.get_video_item_rect(i)
                if item_rect.collidepoint(mouse_pos):
                    if i == 0:  # Resolution
                        self.current_resolution = (self.current_resolution + 1) % len(self.resolutions)
                        self.apply_resolution_change()
                        self.save_manager.save_settings()
                    elif i == 1:  # Fullscreen
                        self.fullscreen = not self.fullscreen
                        self.apply_fullscreen_change()
                        self.save_manager.save_settings()
                    return
        else:  # Controls
            for i in range(len(self.key_bindings)):
                item_rect = self.get_control_item_rect(i)
                if item_rect.collidepoint(mouse_pos):
                    # Start remapping this key
                    control_key = list(self.key_bindings.keys())[i]
                    self.remapping_key = control_key
                    return
    
    def handle_slider_drag(self, mouse_pos: tuple):
        """Handle dragging on audio sliders."""
        if self.dragging_slider is not None and self.settings_tab == 0:  # Audio tab
            slider_rect = self.get_audio_slider_rect(self.dragging_slider)
            
            # Calculate new volume based on mouse position
            click_x = mouse_pos[0] - slider_rect.x
            new_value = int((click_x / slider_rect.width) * 100)
            new_value = max(0, min(100, new_value))
            
            if self.dragging_slider == 0:  # Music volume
                self.audio_manager.set_music_volume(new_value / 100.0)
            else:  # SFX volume
                self.audio_manager.set_sfx_volume(new_value / 100.0)
            
            # Save settings less frequently during dragging to improve performance
            # Only save every 10% change or when dragging ends
    
    def get_audio_item_rect(self, item_index: int) -> pg.Rect:
        """Get the rectangle for an audio item (including name and slider)."""
        y_pos = 320 + item_index * 80
        return pg.Rect(self.screen_width // 2 - 200, y_pos - 20, 500, 60)
    
    def get_video_item_rect(self, item_index: int) -> pg.Rect:
        """Get the rectangle for a video item."""
        y_pos = 320 + item_index * 80
        return pg.Rect(self.screen_width // 2 - 200, y_pos - 20, 400, 60)
    
    def get_control_item_rect(self, item_index: int) -> pg.Rect:
        """Get the rectangle for a control item."""
        y_pos = 320 + item_index * 60
        return pg.Rect(self.screen_width // 2 - 200, y_pos - 20, 400, 50)
    
    def handle_welcome_input(self, event) -> Optional[str]:
        """Handle welcome screen input with mouse and keyboard support."""
        if (event.type == pg.MOUSEBUTTONDOWN and event.button == 1) or (event.type == pg.KEYDOWN and event.key == pg.K_SPACE):
            self.current_state = MenuState.MAIN
            self.start_main_menu_music()
            return "main_menu"
        return None
    
    def handle_main_menu_input(self, event) -> Optional[str]:
        """Handle main menu input with mouse and keyboard support."""
        if event.type == pg.MOUSEMOTION:
            # Update selection based on mouse hover
            self.check_mouse_hover_main_menu(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                clicked_option = self.check_mouse_hover_main_menu(event.pos)
                if clicked_option is not None:
                    # Simulate ENTER key press for the clicked option
                    self.main_menu_selection = clicked_option
                    if self.main_menu_selection == 0:  # LEADERBOARDS
                        self.set_state(MenuState.LEADERBOARD)
                        return None
                    elif self.main_menu_selection == 1:  # ACHIEVEMENTS
                        self.set_state(MenuState.ACHIEVEMENTS)
                        return None
                    elif self.main_menu_selection == 2:  # SHOP
                        print("Shop not implemented yet")
                        return None
                    elif self.main_menu_selection == 3:  # PLAY
                        return "play"
                    elif self.main_menu_selection == 4:  # THE OUTPOST
                        print("The Outpost not implemented yet")
                        return None
                    elif self.main_menu_selection == 5:  # SETTINGS
                        self.current_state = MenuState.SETTINGS
                        self.settings_tab = 0
                        self.settings_selection = 0
                        return None
                    elif self.main_menu_selection == 6:  # QUIT
                        return "quit"
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT or event.key == pg.K_a:
                self.main_menu_selection = (self.main_menu_selection - 1) % len(self.main_menu_options)
            elif event.key == pg.K_RIGHT or event.key == pg.K_d:
                self.main_menu_selection = (self.main_menu_selection + 1) % len(self.main_menu_options)
            elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                if self.main_menu_selection == 0:  # LEADERBOARDS
                    self.set_state(MenuState.LEADERBOARD)
                    return None
                elif self.main_menu_selection == 1:  # ACHIEVEMENTS
                    self.set_state(MenuState.ACHIEVEMENTS)
                    return None
                elif self.main_menu_selection == 2:  # SHOP
                    print("Shop not implemented yet")
                    return None
                elif self.main_menu_selection == 3:  # PLAY
                    self.set_state(MenuState.PLAY_MODE_SELECT)
                    return None
                elif self.main_menu_selection == 4:  # THE OUTPOST
                    print("The Outpost not implemented yet")
                    return None
                elif self.main_menu_selection == 5:  # SETTINGS
                    self.current_state = MenuState.SETTINGS
                    self.settings_tab = 0
                    self.settings_selection = 0
                    return None
                elif self.main_menu_selection == 6:  # QUIT
                    return "quit"
                elif self.main_menu_selection == 1:  # LOAD GAME
                    self.current_state = MenuState.SAVE_LOAD
                    self.save_load_mode = "load"
                    self.save_load_selection = 0
                    return None
                elif self.main_menu_selection == 2:  # SETTINGS
                    self.current_state = MenuState.SETTINGS
                    self.settings_tab = 0
                    self.settings_selection = 0
            elif event.key == pg.K_ESCAPE:
                # If we came from a paused game, return to game instead of quitting
                if self.came_from_paused_game:
                    return "resume_game"
                else:
                    return "quit"
        return None
    
    def handle_play_mode_input(self, event) -> Optional[str]:
        """Handle play mode selection input with mouse and keyboard support."""
        if event.type == pg.MOUSEMOTION:
            # Update selection based on mouse hover
            hovered_option = self.check_mouse_hover_play_mode(event.pos)
            if hovered_option is not None:
                self.play_mode_selection = hovered_option
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                clicked_option = self.check_mouse_hover_play_mode(event.pos)
                if clicked_option is not None:
                    self.play_mode_selection = clicked_option
                    if self.play_mode_selection == 0:  # SOLO
                        return "new_game"
                    elif self.play_mode_selection == 1:  # LOCAL MULTIPLAYER
                        return "local_multiplayer"
                    elif self.play_mode_selection == 2:  # ONLINE MULTIPLAYER
                        return "online_multiplayer"
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_UP or event.key == pg.K_w:
                self.play_mode_selection = (self.play_mode_selection - 1) % len(self.play_mode_options)
            elif event.key == pg.K_DOWN or event.key == pg.K_s:
                self.play_mode_selection = (self.play_mode_selection + 1) % len(self.play_mode_options)
            elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                if self.play_mode_selection == 0:  # SOLO
                    return "new_game"
                elif self.play_mode_selection == 1:  # LOCAL MULTIPLAYER
                    return "local_multiplayer"
                elif self.play_mode_selection == 2:  # ONLINE MULTIPLAYER
                    return "online_multiplayer"
            elif event.key == pg.K_ESCAPE:
                # Go back to main menu - but don't change state here, let main.py handle it
                return "back"  # Return "back" to signal escape was handled
        return None
    
    def handle_settings_input(self, event) -> Optional[str]:
        """Handle settings menu input with mouse and keyboard support."""
        # Handle key remapping first
        if self.remapping_key and event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.cancel_key_remap()
            else:
                self.handle_key_remap(event.key)
            return None
            
        if event.type == pg.MOUSEMOTION:
            # Update tab selection based on mouse hover
            self.check_mouse_hover_settings_tabs(event.pos)
            # Update settings item selection based on mouse hover
            self.check_mouse_hover_settings_items(event.pos)
            # Handle slider dragging
            if self.mouse_held and self.dragging_slider is not None:
                self.handle_slider_drag(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.mouse_held = True
                clicked_tab = self.check_mouse_hover_settings_tabs(event.pos)
                if clicked_tab is not None:
                    self.settings_tab = clicked_tab
                    self.settings_selection = 0  # Reset setting selection when switching tabs
                else:
                    # Check for clicks on settings items
                    self.handle_settings_item_click(event.pos)
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                if self.dragging_slider is not None:
                    # Save settings when dragging ends
                    self.save_manager.save_settings()
                self.mouse_held = False
                self.dragging_slider = None
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.current_state = MenuState.MAIN
                return "back"  # Signal to go back
            elif event.key == pg.K_LEFT or event.key == pg.K_a:
                if self.settings_tab == 0:  # Audio tab
                    self._adjust_audio_setting(-5)  # Decrease by 5%
                else:
                    self.settings_tab = (self.settings_tab - 1) % len(self.settings_tabs)
                    self.settings_selection = 0
            elif event.key == pg.K_RIGHT or event.key == pg.K_d:
                if self.settings_tab == 0:  # Audio tab
                    self._adjust_audio_setting(5)  # Increase by 5%
                else:
                    self.settings_tab = (self.settings_tab + 1) % len(self.settings_tabs)
                    self.settings_selection = 0
            elif event.key == pg.K_UP or event.key == pg.K_w:
                max_items = self._get_max_settings_items()
                self.settings_selection = (self.settings_selection - 1) % max_items
            elif event.key == pg.K_DOWN or event.key == pg.K_s:
                max_items = self._get_max_settings_items()
                self.settings_selection = (self.settings_selection + 1) % max_items
            elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                self._handle_settings_selection()
        return None
    
    def _get_max_settings_items(self) -> int:
        """Get maximum settings items for current tab."""
        if self.settings_tab == 0:  # Audio
            return 2  # Music Volume, SFX Volume
        elif self.settings_tab == 1:  # Video
            return 2  # Resolution, Fullscreen
        else:  # Controls
            return len(self.key_bindings)
    
    def _handle_settings_selection(self):
        """Handle settings selection activation."""
        if self.settings_tab == 0:  # Audio
            pass  # Volume will be handled by left/right keys
        elif self.settings_tab == 1:  # Video
            if self.settings_selection == 0:  # Resolution
                self.current_resolution = (self.current_resolution + 1) % len(self.resolutions)
                self.apply_resolution_change()
                self.save_manager.save_settings()
            elif self.settings_selection == 1:  # Fullscreen
                self.fullscreen = not self.fullscreen
                self.apply_fullscreen_change()
                self.save_manager.save_settings()
        else:  # Controls
            pass  # Key remapping would go here
    
    def _adjust_audio_setting(self, change: int):
        """Adjust audio setting by specified amount."""
        if self.settings_selection == 0:  # Music Volume
            new_volume = self.audio_manager.music_volume * 100 + change
            new_volume = max(0, min(100, new_volume))
            self.audio_manager.set_music_volume(new_volume / 100.0)
        elif self.settings_selection == 1:  # SFX Volume
            new_volume = self.audio_manager.sfx_volume * 100 + change
            new_volume = max(0, min(100, new_volume))
            self.audio_manager.set_sfx_volume(new_volume / 100.0)
    
    def handle_save_load_input(self, event) -> Optional[str]:
        """Handle save/load menu input."""
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.current_state = MenuState.MAIN
                return None
            elif event.key == pg.K_UP or event.key == pg.K_w:
                self.save_load_selection = (self.save_load_selection - 1) % 5  # 5 save slots
            elif event.key == pg.K_DOWN or event.key == pg.K_s:
                self.save_load_selection = (self.save_load_selection + 1) % 5  # 5 save slots
            elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                slot_id = self.save_load_selection + 1
                if self.save_load_mode == "load":
                    save_slot = self.save_manager.load_save(slot_id)
                    if save_slot:
                        return f"load_slot_{slot_id}"
                elif self.save_load_mode == "save":
                    return f"save_slot_{slot_id}"
            elif event.key == pg.K_DELETE and self.save_load_mode == "load":
                slot_id = self.save_load_selection + 1
                self.save_manager.delete_save(slot_id)
        return None
    
    def update(self, dt: float):
        """Update menu animations."""
        self.animation_time += dt
        
        # Update achievement UI
        if hasattr(self, 'achievement_ui'):
            self.achievement_ui.update()
        
        # Optimize cache cleanup - only clean every few seconds to avoid constant work
        if hasattr(self, '_last_cache_cleanup'):
            if self.animation_time - self._last_cache_cleanup > 5.0:
                self._cleanup_old_caches()
                self._last_cache_cleanup = self.animation_time
        else:
            self._last_cache_cleanup = self.animation_time
    
    def _cleanup_old_caches(self):
        """Clean up old cached items to prevent memory growth."""
        # Keep only the most recent 5 items in each cache
        if hasattr(self, '_bg_cache') and len(self._bg_cache) > 5:
            keys = list(self._bg_cache.keys())
            for key in keys[:-5]:
                del self._bg_cache[key]
                
        if hasattr(self, '_logo_cache') and len(self._logo_cache) > 5:
            keys = list(self._logo_cache.keys())
            for key in keys[:-5]:
                del self._logo_cache[key]
                
        if hasattr(self, '_sec_cache') and len(self._sec_cache) > 5:
            keys = list(self._sec_cache.keys())
            for key in keys[:-5]:
                del self._sec_cache[key]
                
        if hasattr(self, '_font_cache') and len(self._font_cache) > 4:
            keys = list(self._font_cache.keys())
            for key in keys[:-4]:
                del self._font_cache[key]
    
    def clear_animation_caches(self):
        """Clear cached animations when screen dimensions change."""
        if hasattr(self, '_bg_cache'):
            del self._bg_cache
        if hasattr(self, '_logo_cache'):
            del self._logo_cache
        if hasattr(self, '_sec_cache'):
            del self._sec_cache
        if hasattr(self, '_font_cache'):
            del self._font_cache
    
    def draw_glow_rect(self, screen: pg.Surface, rect: pg.Rect, color: tuple, glow_size: int = 3, glow: bool = True, pulse_intensity: float = 1.0):
        """Draw a rectangle with subtle glow effect for better readability."""
        if glow:
            # Simplified glow effect - just one subtle outline
            for i in range(1, glow_size + 1):
                alpha = int((30 * (glow_size - i + 1) / glow_size) * pulse_intensity)
                glow_color = (*color[:3], alpha)
                glow_rect = rect.inflate(i * 2, i * 2)
                pg.draw.rect(screen, glow_color, glow_rect, 1, border_radius=8)
        
        # Draw main rectangle with clean border
        pg.draw.rect(screen, color, rect, 2, border_radius=8)
    
    def draw_neon_text(self, screen: pg.Surface, text: str, font: pg.font.Font, pos: tuple, color: tuple, glow: bool = False):
        """Draw text with optional subtle glow effect."""
        if glow:
            # Simple text shadow for readability
            shadow_text = font.render(text, True, (60, 60, 60))
            screen.blit(shadow_text, (pos[0] + 1, pos[1] + 1))
        
        # Draw main text
        main_text = font.render(text, True, color)
        screen.blit(main_text, pos)
        return main_text.get_rect(topleft=pos)
    
    def draw_grid_overlay(self, screen: pg.Surface, alpha: int = 20):
        """Draw simplified grid overlay for better performance."""
        if alpha < 10:  # Skip drawing if too transparent
            return
            
        # Use a simpler, less intensive grid pattern
        spacing = 100
        offset = int(self.animation_time * 10) % spacing  # Slower animation
        
        # Draw fewer lines for better performance
        for x in range(offset, self.screen_width, spacing):
            pg.draw.line(screen, (*self.glow_color, alpha), (x, 0), (x, self.screen_height), 1)
        
        for y in range(offset, self.screen_height, spacing):
            pg.draw.line(screen, (*self.glow_color, alpha), (0, y), (self.screen_width, y), 1)
    
    def render_welcome(self, screen: pg.Surface):
        """Render the welcome screen."""
        # Simplified zoom animation that ensures background always covers screen
        zoom_factor = 1.15 + math.sin(self.animation_time * 0.8) * 0.1  # 105%-125% zoom - never below 105%
        
        # Cache scaled background to avoid constant scaling
        cache_key = f"bg_{zoom_factor:.3f}"
        if not hasattr(self, '_bg_cache') or cache_key not in self._bg_cache:
            if not hasattr(self, '_bg_cache'):
                self._bg_cache = {}
            
            # Calculate dimensions to ensure full screen coverage with margin
            # Use zoom_factor directly on screen dimensions with extra padding
            bg_width = int(self.screen_width * zoom_factor)
            bg_height = int(self.screen_height * zoom_factor)
            
            # Ensure minimum coverage even if image aspect ratio is different
            original_aspect = self.welcome_bg.get_width() / self.welcome_bg.get_height()
            screen_aspect = self.screen_width / self.screen_height
            
            if original_aspect < screen_aspect:
                # Image is taller relative to screen, fit to width
                bg_width = int(self.screen_width * zoom_factor)
                bg_height = int(bg_width / original_aspect)
            else:
                # Image is wider relative to screen, fit to height  
                bg_height = int(self.screen_height * zoom_factor)
                bg_width = int(bg_height * original_aspect)
            
            self._bg_cache[cache_key] = {
                'surface': pg.transform.scale(self.welcome_bg, (bg_width, bg_height)),
                'width': bg_width,
                'height': bg_height
            }
            
            # Limit cache size to prevent memory issues
            if len(self._bg_cache) > 10:
                oldest_key = next(iter(self._bg_cache))
                del self._bg_cache[oldest_key]
        
        cached_bg = self._bg_cache[cache_key]
        bg_x = (self.screen_width - cached_bg['width']) // 2
        bg_y = (self.screen_height - cached_bg['height']) // 2
        screen.blit(cached_bg['surface'], (bg_x, bg_y))
        
        # More dramatic logo zoom with smoother animation
        logo_zoom = 1.0 + math.sin(self.animation_time * 0.6) * 0.08  # 92%-108% zoom
        logo_cache_key = f"logo_{logo_zoom:.3f}"
        
        if not hasattr(self, '_logo_cache'):
            self._logo_cache = {}
            
        if logo_cache_key not in self._logo_cache:
            logo_width = int(self.main_logo.get_width() * logo_zoom)
            logo_height = int(self.main_logo.get_height() * logo_zoom)
            self._logo_cache[logo_cache_key] = {
                'surface': pg.transform.scale(self.main_logo, (logo_width, logo_height)),
                'width': logo_width,
                'height': logo_height
            }
            
            # Limit cache size
            if len(self._logo_cache) > 8:
                oldest_key = next(iter(self._logo_cache))
                del self._logo_cache[oldest_key]
        
        cached_logo = self._logo_cache[logo_cache_key]
        logo_x = (self.screen_width - cached_logo['width']) // 2
        logo_y = 120  # Moved up from 200 to 120
        screen.blit(cached_logo['surface'], (logo_x, logo_y))
        
        # More dramatic secondary logo zoom with different timing
        sec_zoom = 1.0 + math.sin(self.animation_time * 0.9 + 1.0) * 0.06  # 94%-106% zoom, phase offset
        sec_cache_key = f"sec_{sec_zoom:.3f}"
        
        if not hasattr(self, '_sec_cache'):
            self._sec_cache = {}
            
        if sec_cache_key not in self._sec_cache:
            sec_width = int(self.secondary_logo.get_width() * sec_zoom)
            sec_height = int(self.secondary_logo.get_height() * sec_zoom)
            self._sec_cache[sec_cache_key] = {
                'surface': pg.transform.scale(self.secondary_logo, (sec_width, sec_height)),
                'width': sec_width,
                'height': sec_height
            }
            
            # Limit cache size
            if len(self._sec_cache) > 8:
                oldest_key = next(iter(self._sec_cache))
                del self._sec_cache[oldest_key]
        
        cached_sec = self._sec_cache[sec_cache_key]
        sec_x = (self.screen_width - cached_sec['width']) // 2
        sec_y = logo_y + cached_logo['height'] + 40  # Reduced spacing from 50 to 40 since logos moved up
        screen.blit(cached_sec['surface'], (sec_x, sec_y))
        
        # Smoother breathing text animation
        breath_scale = 1.0 + math.sin(self.animation_time * 2.5) * 0.12  # 88%-112% breathing, more dramatic
        click_font_size = max(32, int(48 * breath_scale))  # Ensure minimum readable size
        
        # Cache font rendering for better performance
        font_cache_key = f"font_{click_font_size}"
        if not hasattr(self, '_font_cache'):
            self._font_cache = {}
            
        if font_cache_key not in self._font_cache:
            click_font = pg.font.Font(None, click_font_size)
            self._font_cache[font_cache_key] = click_font.render("CLICK TO START", True, self.accent_color)
            
            # Limit font cache
            if len(self._font_cache) > 6:
                oldest_key = next(iter(self._font_cache))
                del self._font_cache[oldest_key]
        
        click_text = self._font_cache[font_cache_key]
        click_rect = click_text.get_rect(center=(self.screen_width // 2, self.screen_height - 80))
        screen.blit(click_text, click_rect)
    
    def render_main_menu(self, screen: pg.Surface):
        """Render the main menu with clean anime aesthetic."""
        # Clean background gradient
        self._draw_clean_background(screen)
        
        # Main logo (larger and cleaner)
        self._render_main_logo_clean(screen)
        
        # Clean menu options
        self._render_clean_menu_options(screen)
        
        # Subtle version info
        self._render_version_info(screen)
    
    def _draw_clean_background(self, screen: pg.Surface):
        """Draw a clean background with venetian blinds carousel effect."""
        # Draw venetian blinds carousel with all background images
        self._draw_venetian_blinds_carousel(screen)
        
        # Add semi-transparent overlay for better text readability
        overlay = pg.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(120)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Animated infinite vertical scrolling grid with holographic effects
        self._draw_animated_grid(screen)
    
    def _draw_animated_grid(self, screen: pg.Surface):
        """Draw an infinitely scrolling vertical grid."""
        grid_size = 40
        grid_color = (50, 50, 50)
        
        # Infinite vertical scrolling - grid moves down continuously
        scroll_speed = 20  # pixels per second
        vertical_offset = int(self.animation_time * scroll_speed) % grid_size
        
        # Draw vertical lines (static)
        for x in range(0, self.screen_width, grid_size):
            pg.draw.line(screen, grid_color, (x, 0), (x, self.screen_height), 1)
        
        # Draw horizontal lines with infinite scrolling
        for y in range(-grid_size + vertical_offset, self.screen_height + grid_size, grid_size):
            pg.draw.line(screen, grid_color, (0, y), (self.screen_width, y), 1)
    
    def _draw_venetian_blinds_carousel(self, screen: pg.Surface):
        """Draw vertical slightly angled venetian blinds with rotating background images."""
        # Get all available background images
        bg_images = self._get_all_background_images()
        if not bg_images:
            # Fallback gradient if no images
            for y in range(self.screen_height):
                progress = y / self.screen_height
                color_value = int(25 + progress * 5)
                color = (color_value, color_value, color_value + 2)
                pg.draw.line(screen, color, (0, y), (self.screen_width, y))
            return
        
        # Animation parameters - optimized
        current_time = pg.time.get_ticks() / 1000.0
        blind_width = 540  # 1.35x wider (was 400, now 400 * 1.35 = 540)
        blind_angle = 15  # Slight angle in degrees
        carousel_speed = 100  # Pixels per second movement
        
        # Calculate total width needed for seamless looping
        total_carousel_width = blind_width * len(bg_images)
        
        # Calculate animation offset for seamless looping
        animation_offset = (current_time * carousel_speed) % total_carousel_width
        
        # Pre-calculate angle values for performance
        import math
        angle_rad = math.radians(blind_angle)
        angle_offset = int(self.screen_height * math.tan(angle_rad))
        
        # Calculate how many blinds we need to cover the screen completely
        # For angled blinds, we need extra blinds to account for the angle extension
        # The rightmost blind's bottom-right corner extends by angle_offset
        extra_width_needed = abs(angle_offset) + blind_width  # Extra coverage for angle + one more blind
        blinds_needed = int(math.ceil((self.screen_width + extra_width_needed) / blind_width)) + 3
        
        # Start drawing from further off-screen to ensure full coverage of angled blinds
        start_blind_index = int(animation_offset / blind_width) - 1  # Start one blind earlier
        
        for i in range(blinds_needed):
            # Calculate blind position - ensure continuous coverage
            blind_x = (start_blind_index + i) * blind_width - animation_offset
            
            # Determine which background image to use for this blind (stable cycling)
            # Use the blind's absolute position in the sequence, not floating point calculations
            absolute_blind_index = (start_blind_index + i) % len(bg_images)
            bg_image = bg_images[absolute_blind_index]
            
            # Create angled blind slat with proper cropping
            self._draw_angled_blind_slat_optimized(screen, bg_image, blind_x, blind_width, 
                                                 angle_offset, angle_rad)
    
    def _draw_angled_blind_slat_optimized(self, screen: pg.Surface, bg_image: pg.Surface, 
                                        start_x: int, width: int, angle_offset: int, angle_rad: float):
        """Optimized drawing of a single angled venetian blind slat with proper cropping."""
        import math
        
        # Create the angled blind polygon points
        points = [
            (start_x, 0),                                    # Top-left
            (start_x + width, 0),                           # Top-right  
            (start_x + width + angle_offset, self.screen_height),  # Bottom-right
            (start_x + angle_offset, self.screen_height)    # Bottom-left
        ]
        
        # DISABLE CULLING - render all blinds to prevent premature disappearing
        # The performance impact is minimal since we only have a few blinds at once
        # This ensures perfect visual continuity at the cost of slightly more rendering
        
        # Calculate bounding rectangle
        min_x = max(0, min(p[0] for p in points))
        max_x = min(self.screen_width, max(p[0] for p in points))
        
        if max_x <= min_x:
            return
        
        # Use a more efficient mask approach with BLEND_RGBA_MULT
        blind_width_actual = max_x - min_x
        
        # Create the background portion for this blind
        bg_portion = pg.Surface((blind_width_actual, self.screen_height))
        bg_x_offset = start_x - min_x
        bg_portion.blit(bg_image, (bg_x_offset, 0))
        
        # Create mask with the angled shape
        mask = pg.Surface((blind_width_actual, self.screen_height), pg.SRCALPHA)
        mask.fill((0, 0, 0, 0))  # Transparent
        
        # Adjust points for the mask surface
        adjusted_points = [(p[0] - min_x, p[1]) for p in points]
        pg.draw.polygon(mask, (255, 255, 255, 255), adjusted_points)
        
        # Create final surface
        final_blind = pg.Surface((blind_width_actual, self.screen_height), pg.SRCALPHA)
        final_blind.blit(bg_portion, (0, 0))
        final_blind.blit(mask, (0, 0), special_flags=pg.BLEND_RGBA_MIN)
        
        # Draw to screen
        screen.blit(final_blind, (min_x, 0))
        
        # Draw thicker edge highlights with better visibility conditions
        line_thickness = 3  # Make lines thicker (was 1)
        highlight_color = (255, 255, 255, 60)  # Slightly more visible
        
        # Left edge line - draw if any part of the left edge is potentially visible
        left_edge_visible = (points[0][0] >= -line_thickness and points[3][0] >= -line_thickness) or \
                           (points[0][0] <= self.screen_width + line_thickness and points[3][0] <= self.screen_width + line_thickness)
        if left_edge_visible:
            pg.draw.line(screen, highlight_color, points[0], points[3], line_thickness)
            
        # Right edge line - draw if any part of the right edge is potentially visible  
        right_edge_visible = (points[1][0] >= -line_thickness and points[2][0] >= -line_thickness) or \
                             (points[1][0] <= self.screen_width + line_thickness and points[2][0] <= self.screen_width + line_thickness)
        if right_edge_visible:
            pg.draw.line(screen, highlight_color, points[1], points[2], line_thickness)
    
    def _get_all_background_images(self):
        """Get all available background images from the menu backgrounds folder (cached)."""
        # Cache images for performance
        if hasattr(self, '_cached_bg_images') and self._cached_bg_images:
            return self._cached_bg_images
        
        import os
        bg_images = []
        
        # Check for background images in assets/images/Menu/BKG/
        bkg_path = "assets/images/Menu/BKG"
        if os.path.exists(bkg_path):
            # Sort filenames to ensure consistent order - this prevents random changes
            filenames = sorted([f for f in os.listdir(bkg_path) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            
            for filename in filenames:
                try:
                    img_path = os.path.join(bkg_path, filename)
                    img = pg.image.load(img_path).convert()
                    # Scale to screen size
                    img = pg.transform.scale(img, (self.screen_width, self.screen_height))
                    bg_images.append(img)
                    # print(f"Loaded background image: {filename}")
                except Exception as e:
                    print(f"Failed to load background image {filename}: {e}")
        
        # Cache the loaded images
        self._cached_bg_images = bg_images
        # print(f"Cached {len(bg_images)} background images for venetian blinds carousel")
        return bg_images
    
    def _render_main_logo_clean(self, screen: pg.Surface, scale: float = 1.0):
        """Render the main logo with pixel art military sci-fi styling."""
        title_text = "KINGDOM CLEANUP"
        subtitle_text = "A NIKKE FAN GAME"
        
        # Pixel art title positioning - more space from top for dramatic effect
        title_y = int(120 * scale)
        subtitle_y = int(200 * scale)  # Increased spacing from 190 to 200 (50px gap instead of 50px)
        
        # === PIXEL ART TITLE ===
        # Create pixel-perfect title with blocky, crisp edges
        font_size = int(96 * scale) if scale != 1.0 else None
        title_font = pg.font.Font(None, font_size) if font_size else self.pixel_title_font
        
        title_surface = title_font.render(title_text, False, (255, 255, 255))  # False = no antialiasing for pixel art
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, title_y))
        
        # Pixel art shadow layers - blocky and stepped
        pixel_shadow_colors = [(30, 30, 40), (50, 50, 60), (70, 70, 80)]
        pixel_shadow_offsets = [(int(6 * scale), int(6 * scale)), (int(4 * scale), int(4 * scale)), (int(2 * scale), int(2 * scale))]
        
        for shadow_color, offset in zip(pixel_shadow_colors, pixel_shadow_offsets):
            shadow_surface = title_font.render(title_text, False, shadow_color)
            shadow_rect = shadow_surface.get_rect(center=(self.screen_width // 2 + offset[0], title_y + offset[1]))
            screen.blit(shadow_surface, shadow_rect)
        
        # Pixel art glow effect - create blocky highlight
        glow_surface = title_font.render(title_text, False, (240, 240, 240))
        glow_rect = glow_surface.get_rect(center=(self.screen_width // 2 - int(1 * scale), title_y - int(1 * scale)))
        screen.blit(glow_surface, glow_rect)
        
        # Main title - crisp and pixel perfect
        screen.blit(title_surface, title_rect)
        
        # Pixel art border around title - chunky and blocky
        border_thickness = 3
        border_padding = 15
        title_border_rect = pg.Rect(
            title_rect.left - border_padding, 
            title_rect.top - border_padding,
            title_rect.width + border_padding * 2,
            title_rect.height + border_padding * 2
        )
        
        # Draw multiple pixel art border layers
        pg.draw.rect(screen, (100, 100, 120), title_border_rect, border_thickness)
        pg.draw.rect(screen, (150, 150, 170), title_border_rect.inflate(-6, -6), 1)
        
        # === PIXEL ART SUBTITLE ===
        subtitle_surface = self.pixel_subtitle_font.render(subtitle_text, False, (180, 180, 200))
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_width // 2, subtitle_y))
        
        # Subtitle shadow - single layer for cleaner look
        subtitle_shadow = self.pixel_subtitle_font.render(subtitle_text, False, (40, 40, 50))
        subtitle_shadow_rect = subtitle_surface.get_rect(center=(self.screen_width // 2 + 2, subtitle_y + 2))
        screen.blit(subtitle_shadow, subtitle_shadow_rect)
        
        screen.blit(subtitle_surface, subtitle_rect)
        
        # === PIXEL ART DECORATIVE ELEMENTS ===
        # Chunky pixel art line design
        line_y = subtitle_y + 40
        line_width = 500
        line_start_x = self.screen_width // 2 - line_width // 2
        line_end_x = self.screen_width // 2 + line_width // 2
        
        # Main decorative line - thick and pixel perfect
        pg.draw.line(screen, (120, 120, 140), (line_start_x, line_y), (line_end_x, line_y), 4)
        pg.draw.line(screen, (160, 160, 180), (line_start_x, line_y - 1), (line_end_x, line_y - 1), 2)
        
        # Pixel art corner elements - blocky squares instead of chevrons
        corner_size = 12
        corner_color = (200, 200, 220)
        
        # Left corner block
        left_corner_rect = pg.Rect(line_start_x - 25, line_y - corner_size//2, corner_size, corner_size)
        pg.draw.rect(screen, corner_color, left_corner_rect)
        pg.draw.rect(screen, (100, 100, 120), left_corner_rect, 2)
        
        # Right corner block  
        right_corner_rect = pg.Rect(line_end_x + 13, line_y - corner_size//2, corner_size, corner_size)
        pg.draw.rect(screen, corner_color, right_corner_rect)
        pg.draw.rect(screen, (100, 100, 120), right_corner_rect, 2)
        
        # Additional pixel art details - small accent squares
        accent_size = 6
        accent_color = (255, 255, 255)
        
        # Left accent squares
        for i in range(3):
            x_pos = line_start_x - 60 - i * 15
            accent_rect = pg.Rect(x_pos, line_y - accent_size//2, accent_size, accent_size)
            pg.draw.rect(screen, accent_color, accent_rect)
        
        # Right accent squares
        for i in range(3):
            x_pos = line_end_x + 50 + i * 15  
            accent_rect = pg.Rect(x_pos, line_y - accent_size//2, accent_size, accent_size)
            pg.draw.rect(screen, accent_color, accent_rect)
    
    def _render_clean_menu_options(self, screen: pg.Surface):
        """Render menu options in HoloCure horizontal layout style."""
        # Button configuration - matching old HoloCure design with taller buttons
        button_width = 180  # Larger buttons as in old design (was 140)
        button_height = 83  # 1.5x taller than original 55px (55 * 1.5 = 82.5, rounded to 83)
        button_spacing = 60  # Increased spacing as in old design (was 30)
        total_width = len(self.main_menu_options) * button_width + (len(self.main_menu_options) - 1) * button_spacing
        start_x = (self.screen_width - total_width) // 2
        
        # Calculate menu bar area - matching old design (1/4 from bottom instead of 1/3)
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        menu_y = bar_y + (bar_height - button_height) // 2  # Center buttons vertically in the bar
        
        # Draw bottom menu bar background (matching old style)
        bar_surface = pg.Surface((self.screen_width, bar_height))
        bar_surface.set_alpha(200)
        bar_surface.fill((20, 20, 30))  # Dark semi-transparent background
        screen.blit(bar_surface, (0, bar_y))
        
        # Draw bar borders - top and bottom
        pg.draw.line(screen, (100, 100, 120), (0, bar_y), (self.screen_width, bar_y), 2)
        pg.draw.line(screen, (100, 100, 120), (0, bar_y + bar_height), (self.screen_width, bar_y + bar_height), 2)
        
        for i, option in enumerate(self.main_menu_options):
            # Calculate button position
            x_pos = start_x + i * (button_width + button_spacing)
            y_pos = menu_y  # Use menu_y directly instead of menu_center_y calculation
            is_selected = (i == self.main_menu_selection)
            is_play_button = (option == "PLAY")
            
            # Button rectangle
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            # HoloCure-style button styling
            if is_selected:
                # Selected button - bright white glow effect
                glow_size = 8
                glow_rect = pg.Rect(x_pos - glow_size, y_pos - glow_size, 
                                   button_width + glow_size * 2, button_height + glow_size * 2)
                glow_surface = pg.Surface((glow_rect.width, glow_rect.height))
                glow_surface.set_alpha(80)
                glow_surface.fill((255, 255, 255))  # Bright white glow
                screen.blit(glow_surface, glow_rect.topleft)
                
                # Additional outer glow
                outer_glow_size = 12
                outer_glow_rect = pg.Rect(x_pos - outer_glow_size, y_pos - outer_glow_size, 
                                         button_width + outer_glow_size * 2, button_height + outer_glow_size * 2)
                outer_glow_surface = pg.Surface((outer_glow_rect.width, outer_glow_rect.height))
                outer_glow_surface.set_alpha(40)
                outer_glow_surface.fill((255, 255, 255))  # Softer outer glow
                screen.blit(outer_glow_surface, outer_glow_rect.topleft)
                
                # Button background
                bg_surface = pg.Surface((button_width, button_height))
                bg_surface.set_alpha(255)
                bg_surface.fill((150, 150, 170))  # Brighter background
                screen.blit(bg_surface, (x_pos, y_pos))
                
                # Button border
                pg.draw.rect(screen, (255, 255, 255), button_rect, 4)  # Bright white border
                button_color = (255, 255, 255)
                text_color = (255, 255, 255)
            elif is_play_button:
                # Play button - special white background with gray text
                bg_surface = pg.Surface((button_width, button_height))
                bg_surface.set_alpha(255)
                bg_surface.fill((240, 240, 240))  # White background
                screen.blit(bg_surface, (x_pos, y_pos))
                
                # Button border
                pg.draw.rect(screen, (200, 200, 200), button_rect, 3)  # Light gray border
                button_color = (100, 100, 100)  # Gray for icon
                text_color = (100, 100, 100)   # Gray text
            else:
                # Normal button
                bg_surface = pg.Surface((button_width, button_height))
                bg_surface.set_alpha(150)
                bg_surface.fill((40, 40, 50))  # Dark background
                screen.blit(bg_surface, (x_pos, y_pos))
                
                # Button border
                pg.draw.rect(screen, (120, 120, 120), button_rect, 2)  # Gray border
                button_color = (180, 180, 180)
                text_color = (180, 180, 180)
            
            # Draw icon - positioned in upper portion of taller button
            icon_size = int(button_height * 0.4)  # Slightly smaller icon relative to button height
            icon_center_x = x_pos + button_width // 2
            icon_center_y = y_pos + int(button_height * 0.3)  # Position in upper third of button
            self._draw_menu_icon(screen, option, icon_center_x, icon_center_y, button_color)
            
            # Draw small text label below icon with more separation
            label_font = pg.font.Font(None, 18 if is_selected else 16)
            text_surface = label_font.render(option, True, text_color)
            text_y = y_pos + int(button_height * 0.7)  # Position in lower third of button
            text_rect = text_surface.get_rect(center=(icon_center_x, text_y))
            screen.blit(text_surface, text_rect)
    
    def _draw_menu_icon(self, screen: pg.Surface, option: str, center_x: int, center_y: int, color: tuple):
        """Draw HoloCure-style detailed icons for menu options."""
        cx, cy = center_x, center_y
        
        if option == "LEADERBOARDS":
            # Crown icon for leaderboards
            self._draw_crown_icon(screen, cx, cy, 32, color)
        elif option == "ACHIEVEMENTS":
            # Trophy icon for achievements
            self._draw_trophy_icon(screen, cx, cy, 32, color)
        elif option == "SHOP":
            # Shopping bag icon
            self._draw_shopping_bag_icon(screen, cx, cy, 32, color)
        elif option == "PLAY":
            # Play button (triangle with circle)
            self._draw_play_icon(screen, cx, cy, 32, color)
        elif option == "THE OUTPOST":
            # House icon for outpost
            self._draw_house_icon(screen, cx, cy, 32, color)
        elif option == "SETTINGS":
            # Settings cog icon
            self._draw_cog_icon(screen, cx, cy, 32, color)
        elif option == "QUIT":
            # X icon with circle
            quit_color = (255, 100, 100) if color == (255, 255, 255) else (200, 80, 80)
            self._draw_quit_icon(screen, cx, cy, 32, quit_color)
    
    def _draw_crown_icon(self, screen: pg.Surface, cx: int, cy: int, size: int, color: tuple):
        """Draw a crown icon for leaderboards."""
        # Crown base
        base_width = int(size * 0.8)
        base_height = int(size * 0.3)
        base_rect = pg.Rect(cx - base_width//2, cy + size//4, base_width, base_height)
        pg.draw.rect(screen, color, base_rect)
        
        # Crown points (triangular peaks)
        peak_height = int(size * 0.4)
        for i in range(3):
            x_offset = (i - 1) * base_width // 3
            peak_x = cx + x_offset
            peak_y = cy - peak_height//2
            
            # Draw triangular peak
            points = [
                (peak_x, peak_y),
                (peak_x - size//8, peak_y + peak_height),
                (peak_x + size//8, peak_y + peak_height)
            ]
            pg.draw.polygon(screen, color, points)
        
        # Crown jewels (small circles)
        for i in range(3):
            jewel_x = cx + (i - 1) * base_width // 4
            jewel_y = cy - size//8
            pg.draw.circle(screen, (255, 255, 100), (jewel_x, jewel_y), size//12)
    
    def _draw_trophy_icon(self, screen: pg.Surface, cx: int, cy: int, size: int, color: tuple):
        """Draw a trophy icon for achievements."""
        # Trophy cup (main body)
        cup_width = int(size * 0.5)
        cup_height = int(size * 0.4)
        cup_rect = pg.Rect(cx - cup_width//2, cy - size//4, cup_width, cup_height)
        pg.draw.ellipse(screen, color, cup_rect, 3)
        
        # Trophy handles
        handle_size = size // 8
        # Left handle
        left_handle = pg.Rect(cx - cup_width//2 - handle_size, cy - size//8, handle_size*2, handle_size)
        pg.draw.ellipse(screen, color, left_handle, 2)
        # Right handle  
        right_handle = pg.Rect(cx + cup_width//2 - handle_size, cy - size//8, handle_size*2, handle_size)
        pg.draw.ellipse(screen, color, right_handle, 2)
        
        # Trophy stem
        stem_width = size // 10
        stem_height = int(size * 0.3)
        stem_rect = pg.Rect(cx - stem_width//2, cy + cup_height//4, stem_width, stem_height)
        pg.draw.rect(screen, color, stem_rect)
        
        # Trophy base
        base_width = int(size * 0.4)
        base_height = size // 8
        base_rect = pg.Rect(cx - base_width//2, cy + size//3, base_width, base_height)
        pg.draw.rect(screen, color, base_rect)
    
    def _draw_shopping_bag_icon(self, screen: pg.Surface, cx: int, cy: int, size: int, color: tuple):
        """Draw a shopping bag icon for shop."""
        # Bag body
        bag_width = int(size * 0.6)
        bag_height = int(size * 0.7)
        bag_rect = pg.Rect(cx - bag_width//2, cy - bag_height//4, bag_width, bag_height)
        pg.draw.rect(screen, color, bag_rect, 3)
        
        # Bag handles
        handle_width = int(size * 0.3)
        handle_height = int(size * 0.25)
        # Left handle
        left_handle = pg.Rect(cx - bag_width//3, cy - bag_height//2, handle_width, handle_height)
        pg.draw.ellipse(screen, color, left_handle, 2)
        # Right handle
        right_handle = pg.Rect(cx - handle_width//3, cy - bag_height//2, handle_width, handle_height)
        pg.draw.ellipse(screen, color, right_handle, 2)
        
        # Bag fold line
        fold_y = cy - bag_height//6
        pg.draw.line(screen, color, (cx - bag_width//2, fold_y), (cx + bag_width//2, fold_y), 2)
    
    def _draw_play_icon(self, screen: pg.Surface, cx: int, cy: int, size: int, color: tuple):
        """Draw a play button (triangle) icon."""
        # Play triangle pointing right
        triangle_size = int(size * 0.6)
        points = [
            (cx - triangle_size//3, cy - triangle_size//2),
            (cx - triangle_size//3, cy + triangle_size//2),
            (cx + triangle_size//2, cy)
        ]
        pg.draw.polygon(screen, color, points)
        
        # Circle border around triangle
        pg.draw.circle(screen, color, (cx, cy), int(size * 0.45), 3)
    
    def _draw_house_icon(self, screen: pg.Surface, cx: int, cy: int, size: int, color: tuple):
        """Draw a house icon for outpost."""
        # House base (square)
        base_size = int(size * 0.5)
        base_rect = pg.Rect(cx - base_size//2, cy, base_size, base_size//2)
        pg.draw.rect(screen, color, base_rect, 2)
        
        # House roof (triangle)
        roof_points = [
            (cx - base_size//2, cy),
            (cx + base_size//2, cy),
            (cx, cy - base_size//3)
        ]
        pg.draw.polygon(screen, color, roof_points, 2)
        
        # Door
        door_width = base_size // 4
        door_height = base_size // 3
        door_rect = pg.Rect(cx - door_width//2, cy + base_size//6, door_width, door_height)
        pg.draw.rect(screen, color, door_rect, 2)
        
        # Window
        window_size = base_size // 6
        window_rect = pg.Rect(cx + base_size//6, cy - base_size//8, window_size, window_size)
        pg.draw.rect(screen, color, window_rect, 1)
    
    def _draw_cog_icon(self, screen: pg.Surface, cx: int, cy: int, size: int, color: tuple):
        """Draw a settings cog/gear icon."""
        import math
        
        # Inner circle
        inner_radius = int(size * 0.15)
        pg.draw.circle(screen, color, (cx, cy), inner_radius, 2)
        
        # Outer ring with teeth
        outer_radius = int(size * 0.35)
        num_teeth = 8
        
        for i in range(num_teeth):
            angle = i * (360 / num_teeth) * math.pi / 180
            # Outer tooth point
            outer_x = cx + int(outer_radius * math.cos(angle))
            outer_y = cy + int(outer_radius * math.sin(angle))
            # Inner connection point
            inner_x = cx + int(inner_radius * 1.5 * math.cos(angle))
            inner_y = cy + int(inner_radius * 1.5 * math.sin(angle))
            
            pg.draw.line(screen, color, (inner_x, inner_y), (outer_x, outer_y), 3)
        
        # Draw circle outline
        pg.draw.circle(screen, color, (cx, cy), outer_radius, 2)
    
    def _draw_quit_icon(self, screen: pg.Surface, cx: int, cy: int, size: int, color: tuple):
        """Draw a red X icon for quit."""
        # X lines
        line_length = int(size * 0.5)
        thickness = max(3, size // 10)
        
        # Top-left to bottom-right
        start1 = (cx - line_length//2, cy - line_length//2)
        end1 = (cx + line_length//2, cy + line_length//2)
        pg.draw.line(screen, color, start1, end1, thickness)
        
        # Top-right to bottom-left  
        start2 = (cx + line_length//2, cy - line_length//2)
        end2 = (cx - line_length//2, cy + line_length//2)
        pg.draw.line(screen, color, start2, end2, thickness)
        
        # Circle border
        pg.draw.circle(screen, color, (cx, cy), int(size * 0.4), 2)
    
    def _render_version_info(self, screen: pg.Surface):
        """Render version info and GitHub link."""
        # Version in corner (keep existing)
        version_text = "v1.0.0"
        version_surface = pg.font.Font(None, 24).render(version_text, True, (120, 120, 120))
        version_rect = version_surface.get_rect(bottomright=(self.screen_width - 20, self.screen_height - 20))
        screen.blit(version_surface, version_rect)
        
        # GitHub link at bottom of screen with minimal padding
        github_text = "github.com/exporterrormusic/kingdom-pygame"
        github_font = pg.font.Font(None, 28)
        github_surface = github_font.render(github_text, True, (140, 140, 140))
        
        # Position at bottom of screen with minimal padding (10 pixels from bottom)
        github_y = self.screen_height - 10
        
        github_rect = github_surface.get_rect(center=(self.screen_width // 2, github_y))
        screen.blit(github_surface, github_rect)
    
    def render_play_mode_select(self, screen: pg.Surface):
        """Render the play mode selection screen with clean anime aesthetic."""
        # Clean background gradient
        self._draw_clean_background(screen)
        
        # Main logo (same size as main menu)
        self._render_main_logo_clean(screen, scale=1.0)
        
        # Render play mode options (no title text, bigger buttons)
        self._render_play_mode_options(screen)
        
        # Add GitHub link like main menu
        self._render_version_info(screen)
        
        # Back instruction
        back_text = self.small_font.render("ESC - Back", True, (180, 180, 180))
        back_rect = back_text.get_rect(topleft=(20, 20))
        screen.blit(back_text, back_rect)
    
    def _render_play_mode_options(self, screen: pg.Surface):
        """Render play mode options horizontally like the main menu."""
        # Use horizontal layout like main menu with wider buttons for longer text
        button_width = 380   # Very wide buttons to ensure "LOCAL MULTIPLAYER" and "ONLINE MULTIPLAYER" fit completely
        button_height = 83   # Same height as main menu
        button_spacing = 40  # Minimal spacing to fit the very wide buttons
        
        total_width = len(self.play_mode_options) * button_width + (len(self.play_mode_options) - 1) * button_spacing
        start_x = (self.screen_width - total_width) // 2
        
        # Position at same height as main menu
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        menu_y = bar_y + (bar_height - button_height) // 2
        
        # Render background bar like main menu
        bar_rect = pg.Rect(0, bar_y, self.screen_width, bar_height)
        bar_surface = pg.Surface((self.screen_width, bar_height))
        bar_surface.set_alpha(200)  # Match main menu alpha
        bar_surface.fill((20, 20, 30))  # Match main menu bar color
        screen.blit(bar_surface, (0, bar_y))
        
        # Draw bar borders - top and bottom lines like main menu
        pg.draw.line(screen, (100, 100, 120), (0, bar_y), (self.screen_width, bar_y), 2)
        pg.draw.line(screen, (100, 100, 120), (0, bar_y + bar_height), (self.screen_width, bar_y + bar_height), 2)
        
        for i, option in enumerate(self.play_mode_options):
            x_pos = start_x + i * (button_width + button_spacing)
            button_rect = pg.Rect(x_pos, menu_y, button_width, button_height)
            
            is_selected = (i == self.play_mode_selection)
            
            # Button styling matching main menu
            if is_selected:
                # Selected button - bright glow effect
                glow_size = 8
                glow_rect = pg.Rect(x_pos - glow_size, menu_y - glow_size, 
                                   button_width + glow_size * 2, button_height + glow_size * 2)
                glow_surface = pg.Surface((glow_rect.width, glow_rect.height))
                glow_surface.set_alpha(80)
                glow_surface.fill(self.glow_color)
                screen.blit(glow_surface, glow_rect.topleft)
                
                # Button background
                button_surface = pg.Surface((button_width, button_height))
                button_surface.set_alpha(220)
                button_surface.fill((60, 70, 80))  # Brighter for selected
                screen.blit(button_surface, (x_pos, menu_y))
                
                # Button border
                pg.draw.rect(screen, self.primary_color, button_rect, 3)
                text_color = self.primary_color
            else:
                # Unselected button
                button_surface = pg.Surface((button_width, button_height))
                button_surface.set_alpha(160)
                button_surface.fill((40, 45, 55))  # Darker for unselected
                screen.blit(button_surface, (x_pos, menu_y))
                
                # Button border
                pg.draw.rect(screen, self.secondary_color, button_rect, 2)
                text_color = self.secondary_color
            
            # Button text
            text_surface = self.menu_font.render(option, True, text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)
    
    def render_settings(self, screen: pg.Surface):
        """Render the settings menu with clean main menu style."""
        # Use the same clean background as main menu
        self._draw_clean_background(screen)
        
        # Settings title with main menu styling
        title_surface = self.large_font.render("SETTINGS", True, self.primary_color)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 100))
        # Subtle text shadow like main menu
        shadow_surface = self.large_font.render("SETTINGS", True, (60, 60, 60))
        shadow_rect = shadow_surface.get_rect(center=(self.screen_width // 2 + 1, 101))
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(title_surface, title_rect)
        
        # Tab buttons with clean main menu styling
        tab_y = 200
        tab_width = 200
        tab_spacing = 50
        total_tab_width = len(self.settings_tabs) * tab_width + (len(self.settings_tabs) - 1) * tab_spacing
        start_x = (self.screen_width - total_tab_width) // 2
        
        for i, tab in enumerate(self.settings_tabs):
            tab_x = start_x + i * (tab_width + tab_spacing)
            tab_rect = pg.Rect(tab_x, tab_y, tab_width, 50)
            
            # Clean tab styling matching main menu buttons
            if i == self.settings_tab:
                # Active tab - solid color like selected main menu option
                pg.draw.rect(screen, self.primary_color, tab_rect, border_radius=8)
                text_color = (0, 0, 0)  # Dark text on bright background
            else:
                # Inactive tab - subtle border like unselected main menu options
                pg.draw.rect(screen, (40, 40, 50), tab_rect, border_radius=8)
                pg.draw.rect(screen, self.secondary_color, tab_rect, 2, border_radius=8)
                text_color = self.text_color
            
            # Tab text with clean styling
            tab_text = self.menu_font.render(tab, True, text_color)
            tab_text_rect = tab_text.get_rect(center=tab_rect.center)
            screen.blit(tab_text, tab_text_rect)
        
        # Settings content with clean styling
        content_y = 320
        if self.settings_tab == 0:  # Audio
            self._render_audio_settings_clean(screen, content_y)
        elif self.settings_tab == 1:  # Video
            self._render_video_settings_clean(screen, content_y)
        else:  # Controls
            self._render_control_settings_clean(screen, content_y)
        
        # Navigation with clean styling - simpler text
        nav_y = self.screen_height - 50
        nav_text = "ESC to go back • ARROW KEYS to navigate • ENTER to select"
        nav_surface = self.small_font.render(nav_text, True, self.secondary_color)
        nav_rect = nav_surface.get_rect(center=(self.screen_width // 2, nav_y))
        screen.blit(nav_surface, nav_rect)
    
    def _render_audio_settings_clean(self, screen: pg.Surface, y_start: int):
        """Render audio settings with interactive sliders."""
        settings = [
            ("Music Volume", int(self.audio_manager.music_volume * 100)),
            ("SFX Volume", int(self.audio_manager.sfx_volume * 100))
        ]
        
        for i, (setting, value) in enumerate(settings):
            y_pos = y_start + i * 80
            selected = i == self.settings_selection
            
            # Setting name with clean styling when selected
            if selected:
                # Subtle highlight for selected setting
                name_text = self.menu_font.render(setting, True, self.primary_color)
                text_color = self.primary_color
            else:
                name_text = self.menu_font.render(setting, True, self.text_color)
                text_color = self.text_color
            
            screen.blit(name_text, (self.screen_width // 2 - 200, y_pos))
            
            # Clean volume slider
            slider_rect = pg.Rect(self.screen_width // 2 + 50, y_pos + 10, 200, 20)
            
            # Slider background with clean border
            bg_color = (40, 40, 50) if not selected else (50, 50, 60)
            pg.draw.rect(screen, bg_color, slider_rect, border_radius=10)
            
            border_color = self.primary_color if selected else self.secondary_color
            pg.draw.rect(screen, border_color, slider_rect, 2, border_radius=10)
            
            # Filled portion of slider
            fill_width = int(200 * (value / 100))
            if fill_width > 0:
                fill_rect = pg.Rect(self.screen_width // 2 + 50, y_pos + 10, fill_width, 20)
                slider_color = self.primary_color if selected else self.secondary_color
                pg.draw.rect(screen, slider_color, fill_rect, border_radius=10)
            
            # Slider handle (small circle)
            handle_x = self.screen_width // 2 + 50 + fill_width
            handle_center = (handle_x, y_pos + 20)
            handle_color = (255, 255, 255) if selected else (200, 200, 200)
            pg.draw.circle(screen, handle_color, handle_center, 8)
            pg.draw.circle(screen, border_color, handle_center, 8, 2)
            
            # Value text
            value_text = self.small_font.render(f"{value}%", True, text_color)
            screen.blit(value_text, (self.screen_width // 2 + 270, y_pos + 5))

    def _render_video_settings_clean(self, screen: pg.Surface, y_start: int):
        """Render video settings with resolution and fullscreen options."""
        settings = [
            ("Resolution", self.resolutions[self.current_resolution]),
            ("Fullscreen", "ON" if self.fullscreen else "OFF")
        ]
        
        for i, (setting, value) in enumerate(settings):
            y_pos = y_start + i * 80
            selected = i == self.settings_selection
            
            # Setting name with clean styling when selected
            if selected:
                # Subtle highlight for selected setting
                name_text = self.menu_font.render(setting, True, self.primary_color)
                text_color = self.primary_color
                value_color = self.primary_color
            else:
                name_text = self.menu_font.render(setting, True, self.text_color)
                text_color = self.text_color
                value_color = self.secondary_color
            
            screen.blit(name_text, (self.screen_width // 2 - 200, y_pos))
            
            # Value with clean border box matching main menu style
            value_text = self.menu_font.render(str(value), True, value_color)
            value_rect = value_text.get_rect(center=(self.screen_width // 2 + 150, y_pos + 15))
            
            # Clean border around value like main menu buttons
            border_rect = pg.Rect(value_rect.x - 15, value_rect.y - 8, value_rect.width + 30, value_rect.height + 16)
            if selected:
                pg.draw.rect(screen, (50, 50, 60), border_rect, border_radius=5)
                pg.draw.rect(screen, self.primary_color, border_rect, 2, border_radius=5)
            else:
                pg.draw.rect(screen, (30, 30, 40), border_rect, border_radius=5)
                pg.draw.rect(screen, self.secondary_color, border_rect, 1, border_radius=5)
            
            screen.blit(value_text, value_rect)
    
    def _render_video_settings(self, screen: pg.Surface, y_start: int):
        """Render video settings with anime sci-fi theme."""
        settings = [
            ("Resolution", self.resolutions[self.current_resolution]),
            ("Fullscreen", "ON" if self.fullscreen else "OFF")
        ]
        
        for i, (setting, value) in enumerate(settings):
            y_pos = y_start + i * 80
            selected = i == self.settings_selection
            
            # Setting name with clean main menu styling
            if selected:
                text_color = self.primary_color
                value_color = self.primary_color
            else:
                text_color = self.text_color
                value_color = self.secondary_color
            
            name_text = self.menu_font.render(setting, True, text_color)
            screen.blit(name_text, (self.screen_width // 2 - 200, y_pos))
            
            # Value with clean border box matching main menu style
            value_text = self.menu_font.render(str(value), True, value_color)
            value_rect = value_text.get_rect(center=(self.screen_width // 2 + 150, y_pos + 15))
            
            # Clean border around value like main menu buttons
            border_rect = pg.Rect(value_rect.x - 15, value_rect.y - 8, value_rect.width + 30, value_rect.height + 16)
            if selected:
                pg.draw.rect(screen, (50, 50, 60), border_rect, border_radius=5)
                pg.draw.rect(screen, self.primary_color, border_rect, 2, border_radius=5)
            else:
                pg.draw.rect(screen, (30, 30, 40), border_rect, border_radius=5)
                pg.draw.rect(screen, self.secondary_color, border_rect, 1, border_radius=5)
            
            screen.blit(value_text, value_rect)
    
    def _render_control_settings_clean(self, screen: pg.Surface, y_start: int):
        """Render control settings with clean main menu styling."""
        control_names = {
            "move_up": "Move Up",
            "move_down": "Move Down", 
            "move_left": "Move Left",
            "move_right": "Move Right",
            "dash": "Dash",
            "burst": "Burst",
            "pause": "Pause"
        }
        
        # Instruction text with clean styling
        instruction_text = "Click on any key to change it"
        inst_surface = self.menu_font.render(instruction_text, True, self.secondary_color)
        inst_rect = inst_surface.get_rect(center=(self.screen_width // 2, y_start - 30))
        screen.blit(inst_surface, inst_rect)
        
        for i, (key, binding) in enumerate(self.key_bindings.items()):
            y_pos = y_start + i * 60
            selected = i == self.settings_selection
            is_remapping = self.remapping_key == key
            
            # Control name with clean main menu styling
            if is_remapping:
                text_color = (255, 200, 100)  # Yellow for remapping
                binding_color = (255, 200, 100)
            elif selected:
                text_color = self.primary_color
                binding_color = self.primary_color
            else:
                text_color = self.text_color
                binding_color = self.secondary_color
            
            name_text = self.menu_font.render(control_names[key], True, text_color)
            screen.blit(name_text, (self.screen_width // 2 - 200, y_pos))
            
            # Single key binding with clean clickable key box
            key_name = pg.key.name(binding).upper()
            
            # Create clean clickable key box matching main menu style
            key_x_start = self.screen_width // 2 + 50
            
            # Key box with clean main menu styling
            key_text = self.small_font.render(key_name, True, binding_color)
            key_rect = key_text.get_rect(center=(key_x_start + 35, y_pos + 18))
            # Make boxes larger and cleaner for easier clicking
            box_rect = pg.Rect(key_rect.x - 20, key_rect.y - 12, key_rect.width + 40, key_rect.height + 24)
            
            # Clean key box styling matching main menu buttons
            if is_remapping:
                # Yellow highlight for remapping
                pg.draw.rect(screen, (80, 80, 20), box_rect, border_radius=5)
                pg.draw.rect(screen, (255, 200, 100), box_rect, 2, border_radius=5)
            elif selected:
                # Selected style matching main menu
                pg.draw.rect(screen, (50, 50, 60), box_rect, border_radius=5)
                pg.draw.rect(screen, self.primary_color, box_rect, 2, border_radius=5)
            else:
                # Unselected clean style
                pg.draw.rect(screen, (30, 30, 40), box_rect, border_radius=5)
                pg.draw.rect(screen, self.secondary_color, box_rect, 1, border_radius=5)
            
            screen.blit(key_text, key_rect)
    
    def get_control_key_rect(self, control_index: int, key_index: int) -> pg.Rect:
        """Get the rectangle for a specific key binding box."""
        y_start = 370  # Match the control settings rendering
        y_pos = y_start + control_index * 60
        
        # Calculate key box position - match the rendering logic exactly
        key_x_start = self.screen_width // 2 + 50
        control_key = list(self.key_bindings.keys())[control_index]
        binding = self.key_bindings[control_key]
        
        # Single key binding - no need to iterate
        key_name = pg.key.name(binding).upper()
        key_text = self.small_font.render(key_name, True, (255, 255, 255))
        key_rect = key_text.get_rect(center=(key_x_start + 35, y_pos + 18))
        # Match the larger clickable box dimensions from rendering
        box_rect = pg.Rect(key_rect.x - 20, key_rect.y - 12, key_rect.width + 40, key_rect.height + 24)
        
        return box_rect
        
        return pg.Rect(0, 0, 0, 0)  # Fallback
    
    def handle_control_mouse_click(self, mouse_pos: tuple):
        """Handle mouse clicks on control key bindings."""
        if self.remapping_key:
            return  # Already remapping
            
        # Check which key binding was clicked - single key system
        for i, (control_key, binding) in enumerate(self.key_bindings.items()):
            key_rect = self.get_control_key_rect(i, 0)  # Single key, so index is always 0
            if key_rect.collidepoint(mouse_pos):
                print(f"Starting remap for {control_key}")
                self.remapping_key = control_key
                self.remap_key_index = 0  # Always 0 for single keys
                return
    
    def handle_key_remap(self, new_key: int):
        """Handle remapping a key to a new value."""
        if not self.remapping_key:
            return
            
        print(f"Remapping {self.remapping_key} to {pg.key.name(new_key)}")
            
        # Don't allow remapping to certain system keys
        forbidden_keys = [pg.K_ESCAPE]  # Keep ESC for cancel
        if new_key in forbidden_keys:
            return
            
        # Update the key binding for single key system
        old_key = self.key_bindings[self.remapping_key]
        self.key_bindings[self.remapping_key] = new_key
        print(f"Remapped {self.remapping_key} from {pg.key.name(old_key)} to {pg.key.name(new_key)}")
            
        # Clear remapping state
        self.remapping_key = None
        self.remap_key_index = None
        self.remap_key_index = None
        print("Remapping completed")
        print(f"Remapped key to: {pg.key.name(new_key)}")
    
    def cancel_key_remap(self):
        """Cancel current key remapping."""
        self.remapping_key = None
        self.remap_key_index = None
    
    def render_save_load(self, screen: pg.Surface):
        """Render the save/load menu."""
        screen.fill(self.bg_color)
        
        # Title
        title = "LOAD GAME" if self.save_load_mode == "load" else "SAVE GAME"
        title_text = self.large_font.render(title, True, self.primary_color)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Save slots
        save_slots = self.save_manager.get_save_slots()
        start_y = 250
        
        for i in range(5):  # 5 save slots
            slot_id = i + 1
            y_pos = start_y + i * 100
            selected = i == self.save_load_selection
            
            # Slot background
            slot_rect = pg.Rect(self.screen_width // 2 - 400, y_pos - 30, 800, 80)
            if selected:
                pg.draw.rect(screen, self.primary_color, slot_rect, 3, border_radius=10)
                glow_rect = slot_rect.inflate(10, 10)
                glow_color = tuple(int(c * 0.3) for c in self.primary_color)
                pg.draw.rect(screen, glow_color, glow_rect, 2, border_radius=15)
            else:
                pg.draw.rect(screen, (50, 50, 50), slot_rect, 2, border_radius=10)
            
            # Slot number
            slot_text = self.menu_font.render(f"Slot {slot_id}", True, self.text_color)
            screen.blit(slot_text, (slot_rect.x + 20, slot_rect.y + 10))
            
            # Slot data
            slot_data = save_slots[slot_id]
            if slot_data.is_empty:
                empty_text = self.small_font.render("Empty", True, (120, 120, 120))
                screen.blit(empty_text, (slot_rect.x + 20, slot_rect.y + 45))
            else:
                # Character and level
                char_text = self.small_font.render(f"{slot_data.character_name} - Wave {slot_data.wave}", True, self.text_color)
                screen.blit(char_text, (slot_rect.x + 20, slot_rect.y + 45))
                
                # Score and date
                score_text = self.small_font.render(f"Score: {slot_data.score:,}", True, (150, 150, 150))
                screen.blit(score_text, (slot_rect.x + 300, slot_rect.y + 45))
                
                date_text = self.small_font.render(slot_data.save_date, True, (120, 120, 120))
                screen.blit(date_text, (slot_rect.x + 500, slot_rect.y + 45))
        
        # Instructions
        instructions = ["UP/DOWN to select • ENTER to confirm • ESC to go back"]
        if self.save_load_mode == "load":
            instructions.append("DELETE to remove save")
        
        for i, instruction in enumerate(instructions):
            instruction_text = self.small_font.render(instruction, True, (120, 120, 120))
            instruction_rect = instruction_text.get_rect(center=(self.screen_width // 2, self.screen_height - 80 + i * 30))
            screen.blit(instruction_text, instruction_rect)
    
    def render(self, screen: pg.Surface):
        """Render the current menu state."""
        if self.current_state == MenuState.WELCOME:
            self.render_welcome(screen)
        elif self.current_state == MenuState.MAIN:
            self.render_main_menu(screen)
        elif self.current_state == MenuState.PLAY_MODE_SELECT:
            self.render_play_mode_select(screen)
        elif self.current_state == MenuState.SETTINGS:
            self.render_settings(screen)
        elif self.current_state == MenuState.SAVE_LOAD:
            self.render_save_load(screen)
        elif self.current_state == MenuState.LEADERBOARD:
            self.render_leaderboard(screen)
        elif self.current_state == MenuState.ACHIEVEMENTS:
            self.achievement_ui.render(screen)
    
    def handle_input(self, event) -> Optional[str]:
        """Handle input for current menu state."""
        if self.current_state == MenuState.WELCOME:
            return self.handle_welcome_input(event)
        elif self.current_state == MenuState.MAIN:
            return self.handle_main_menu_input(event)
        elif self.current_state == MenuState.PLAY_MODE_SELECT:
            return self.handle_play_mode_input(event)
        elif self.current_state == MenuState.SETTINGS:
            return self.handle_settings_input(event)
        elif self.current_state == MenuState.SAVE_LOAD:
            return self.handle_save_load_input(event)
        elif self.current_state == MenuState.LEADERBOARD:
            return self.handle_leaderboard_input(event)
        elif self.current_state == MenuState.ACHIEVEMENTS:
            action = self.achievement_ui.handle_input(event)
            if action == "back":
                self.set_state(MenuState.MAIN)
                return None
            return action
        return None
    
    def set_state(self, state: MenuState, preserve_music: bool = False):
        """Set the menu state."""
        self.current_state = state
        
        # Initialize state-specific settings
        if state == MenuState.PLAY_MODE_SELECT:
            # Reset to first option and flag for hover check on next frame
            self.play_mode_selection = 0
            self.play_mode_needs_hover_check = True
        
        # Start appropriate music only if not preserving current music
        if not preserve_music:
            if state == MenuState.WELCOME:
                self.start_welcome_music()
            elif state in [MenuState.MAIN, MenuState.SETTINGS, MenuState.LEADERBOARD]:
                self.start_main_menu_music()
    
    def set_came_from_paused_game(self, came_from_paused: bool):
        """Set whether the menu was opened from a paused game."""
        self.came_from_paused_game = came_from_paused
    
    def get_state(self) -> MenuState:
        """Get current menu state."""
        return self.current_state
    
    # Music control methods
    def start_welcome_music(self):
        """Start welcome screen music."""
        self.audio_manager.play_music("assets/sounds/music/welcome.mp3")
    
    def start_main_menu_music(self):
        """Start main menu music."""
        self.audio_manager.play_music("assets/sounds/music/main-menu.mp3")
    
    def start_character_select_music(self):
        """Start character selection music."""
        self.audio_manager.play_music("assets/sounds/music/character-select.mp3")
    
    def start_battle_music(self):
        """Start battle music - randomly selected from battle music folder."""
        battle_music_file = self._get_random_battle_music()
        print(f"Starting battle music (method 2): {battle_music_file}")
        self.audio_manager.play_music(battle_music_file)
    
    def get_achievement_manager(self):
        """Get the achievement manager for triggering achievement updates."""
        if hasattr(self, 'achievement_ui'):
            return self.achievement_ui.achievement_manager
        return None
    
    def show_achievement_notification(self, achievement):
        """Show an achievement notification."""
        if hasattr(self, 'achievement_ui'):
            self.achievement_ui.show_achievement_notification(achievement)
    
    def update_screen_dimensions(self, new_width: int, new_height: int):
        """Update screen dimensions and rescale background."""
        self.screen_width = new_width
        self.screen_height = new_height
        
        # Reload and rescale the main menu background for new dimensions
        self.load_random_main_menu_background()
    
    def render_leaderboard(self, screen):
        """Render the leaderboard screen with clean anime aesthetic."""
        # Clean background matching main menu style
        self._draw_clean_background(screen)
        
        # Title
        self._render_leaderboard_title(screen)
        
        # Character leaderboard list
        self._render_character_leaderboard(screen)
        
        # Navigation instructions
        self._render_leaderboard_instructions(screen)
    
    def _render_leaderboard_title(self, screen):
        """Render the leaderboard title."""
        title_text = self.large_font.render("LEADERBOARD", True, self.primary_color)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 120))
        
        # Add subtle glow effect
        glow_surface = pg.Surface((title_rect.width + 20, title_rect.height + 20))
        glow_surface.set_alpha(80)
        glow_surface.fill(self.primary_color)
        glow_rect = glow_surface.get_rect(center=title_rect.center)
        screen.blit(glow_surface, glow_rect)
        screen.blit(title_text, title_rect)
    
    def _render_character_leaderboard(self, screen):
        """Render the character leaderboard entries."""
        if not hasattr(self, 'character_manager') or not hasattr(self, 'score_manager'):
            # Fallback if dependencies aren't available
            no_data_text = self.menu_font.render("Character data not available", True, (255, 100, 100))
            text_rect = no_data_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            screen.blit(no_data_text, text_rect)
            return
        
        character_list = self.character_manager.get_character_list()
        character_display_names = self.character_manager.get_character_display_names()
        
        if not character_list:
            no_chars_text = self.menu_font.render("No characters available", True, (255, 100, 100))
            text_rect = no_chars_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            screen.blit(no_chars_text, text_rect)
            return
        
        # Create list of (character, display_name, best_score) tuples for sorting
        character_data = []
        for char_name, display_name in zip(character_list, character_display_names):
            best_score = self.score_manager.get_character_best_score(char_name)
            character_data.append((char_name, display_name, best_score if best_score is not None else 0))
        
        # Sort by best score (descending), then by display name (ascending) for ties
        character_data.sort(key=lambda x: (-x[2], x[1]))
        
        # Get currently selected index and scroll offset
        if hasattr(self, 'leaderboard_selected'):
            selected_index = self.leaderboard_selected
        else:
            selected_index = 0
            self.leaderboard_selected = 0
            
        if hasattr(self, 'leaderboard_scroll_offset'):
            scroll_offset = self.leaderboard_scroll_offset
        else:
            scroll_offset = 0
            self.leaderboard_scroll_offset = 0
        
        # Character entry dimensions - use reasonable width
        entry_height = 100
        entry_width = min(900, self.screen_width - 100)  # Reasonable row width, not full screen
        start_y = 200
        start_x = (self.screen_width - entry_width) // 2  # Center the row on screen
        
        # Calculate visible entries and ensure selected is in view
        max_visible = max(1, (self.screen_height - start_y - 100) // entry_height)
        total_characters = len(character_data)
        
        # Ensure selected index is within bounds
        self.leaderboard_selected = max(0, min(selected_index, total_characters - 1))
        
        # Auto-scroll to keep selected item in view
        if self.leaderboard_selected < scroll_offset:
            self.leaderboard_scroll_offset = self.leaderboard_selected
        elif self.leaderboard_selected >= scroll_offset + max_visible:
            self.leaderboard_scroll_offset = self.leaderboard_selected - max_visible + 1
        
        # Ensure scroll offset is within bounds
        max_scroll = max(0, total_characters - max_visible)
        self.leaderboard_scroll_offset = max(0, min(self.leaderboard_scroll_offset, max_scroll))
        
        # Render visible entries
        for i in range(max_visible):
            data_index = i + self.leaderboard_scroll_offset
            if data_index >= total_characters:
                break
                
            char_name, display_name, best_score = character_data[data_index]
            y_pos = start_y + i * entry_height
            entry_rect = pg.Rect(start_x, y_pos, entry_width, entry_height - 10)
            
            # Check if this entry is selected
            is_selected = (data_index == self.leaderboard_selected)
            
            # Draw entry background with clean style
            if is_selected:
                # Selected entry - bright outline
                glow_rect = pg.Rect(entry_rect.x - 3, entry_rect.y - 3, entry_rect.width + 6, entry_rect.height + 6)
                pg.draw.rect(screen, self.primary_color, glow_rect, border_radius=8)
                
                bg_color = (40, 40, 60, 180)
                bg_surface = pg.Surface((entry_rect.width, entry_rect.height), pg.SRCALPHA)
                bg_surface.fill(bg_color)
                screen.blit(bg_surface, entry_rect)
            else:
                # Normal entry
                bg_color = (30, 30, 40, 120)
                bg_surface = pg.Surface((entry_rect.width, entry_rect.height), pg.SRCALPHA)
                bg_surface.fill(bg_color)
                screen.blit(bg_surface, entry_rect)
            
            # Draw clean border
            border_color = self.primary_color if is_selected else self.secondary_color
            pg.draw.rect(screen, border_color, entry_rect, width=1, border_radius=5)
            
            # Full-width horizontal layout: Number | Sprite | Name | Score/Wave
            # Define section widths for horizontal layout with full width usage
            rank_width = 80       # Fixed width for rank numbers (e.g., "#1", "#999")
            sprite_width = 100    # Fixed width for character sprites
            name_width = entry_width - rank_width - sprite_width - 300  # Flexible name width
            stats_width = 300     # Fixed width for score and wave data
            
            # Calculate section positions
            rank_x = entry_rect.x + 10
            sprite_x = rank_x + rank_width
            name_x = sprite_x + sprite_width
            stats_x = name_x + name_width
            
            # Draw vertical separator lines between sections (subtle white lines)
            separator_color = (255, 255, 255, 60)  # Subtle white with transparency
            line_top = entry_rect.y + 5
            line_bottom = entry_rect.y + entry_rect.height - 5
            
            # Separator after rank section
            pg.draw.line(screen, separator_color, (sprite_x - 5, line_top), (sprite_x - 5, line_bottom), 1)
            # Separator after sprite section  
            pg.draw.line(screen, separator_color, (name_x - 5, line_top), (name_x - 5, line_bottom), 1)
            # Separator after name section
            pg.draw.line(screen, separator_color, (stats_x - 5, line_top), (stats_x - 5, line_bottom), 1)
            
            # 1. RANK NUMBER SECTION
            rank_text = f"#{data_index + 1}"
            rank_surface = self.menu_font.render(rank_text, True, (255, 215, 100))
            rank_text_x = rank_x + (rank_width - rank_surface.get_width()) // 2  # Center in section
            rank_text_y = entry_rect.y + (entry_rect.height - rank_surface.get_height()) // 2  # Center vertically
            screen.blit(rank_surface, (rank_text_x, rank_text_y))
            
            # 2. CHARACTER SPRITE SECTION
            sprite_size = 90  # Large sprite for better visibility
            sprite_pos_x = sprite_x + (sprite_width - sprite_size) // 2  # Center in section
            sprite_pos_y = entry_rect.y + (entry_rect.height - sprite_size) // 2  # Center vertically
            
            # Try to load character sprite
            character_sprite = self._load_character_sprite_for_leaderboard(char_name, sprite_size)
            if character_sprite:
                screen.blit(character_sprite, (sprite_pos_x, sprite_pos_y))
            else:
                # Fallback: draw clean character placeholder
                fallback_rect = pg.Rect(sprite_pos_x, sprite_pos_y, sprite_size, sprite_size)
                fallback_color = (80 + (hash(char_name) % 80), 120, 160)
                pg.draw.rect(screen, fallback_color, fallback_rect, border_radius=5)
                pg.draw.rect(screen, self.secondary_color, fallback_rect, width=2, border_radius=5)
                
                # Draw character initial
                if display_name:
                    initial = display_name[0].upper()
                    initial_text = self.menu_font.render(initial, True, self.primary_color)
                    initial_rect = initial_text.get_rect(center=fallback_rect.center)
                    screen.blit(initial_text, initial_rect)
            
            # 3. CHARACTER NAME SECTION
            name_text = self.menu_font.render(display_name, True, self.primary_color)
            name_text_x = name_x + 10  # Small left padding in section
            name_text_y = entry_rect.y + (entry_rect.height - name_text.get_height()) // 2  # Center vertically
            screen.blit(name_text, (name_text_x, name_text_y))
            
            # 4. STATS SECTION (Score and Wave in same section)
            stats_text_x = stats_x + 10  # Small left padding in section
            
            # Score display
            if best_score > 0:
                score_text = f"Score: {best_score:,}"
                score_color = (255, 215, 100)
            else:
                score_text = "No records"
                score_color = self.secondary_color
            
            score_surface = self.small_font.render(score_text, True, score_color)
            score_text_y = entry_rect.y + 20  # Upper part of stats section
            screen.blit(score_surface, (stats_text_x, score_text_y))
            
            # Wave display
            if best_score > 0:
                best_wave = self.score_manager.get_character_best_waves(char_name)
                if best_wave is not None:
                    wave_text = f"Wave: {best_wave}"
                    wave_surface = self.small_font.render(wave_text, True, (150, 255, 150))
                    wave_text_y = entry_rect.y + 50  # Lower part of stats section
                    screen.blit(wave_surface, (stats_text_x, wave_text_y))
        
        # Draw scrolling indicators if needed
        if total_characters > max_visible:
            self._render_scroll_indicators(screen, start_y, entry_height * max_visible, 
                                         self.leaderboard_scroll_offset, total_characters, max_visible)
    
    def _load_character_sprite_for_leaderboard(self, char_name: str, sprite_size: int):
        """Load and cache a character sprite for leaderboard display."""
        if not hasattr(self, '_sprite_cache'):
            self._sprite_cache = {}
        
        cache_key = f"{char_name}_{sprite_size}"
        
        if cache_key in self._sprite_cache:
            return self._sprite_cache[cache_key]
        
        try:
            sprite_path = self.character_manager.get_character_path(char_name)
            if sprite_path and os.path.exists(sprite_path):
                # Load the sprite sheet
                sprite_sheet = pg.image.load(sprite_path).convert_alpha()
                
                # Try to determine sprite frame size more accurately
                sheet_width = sprite_sheet.get_width()
                sheet_height = sprite_sheet.get_height()
                
                # Common sprite sheet layouts to try
                layouts = [
                    (4, 4),  # 4x4 grid (16 frames)
                    (8, 4),  # 8x4 grid (32 frames)
                    (4, 8),  # 4x8 grid (32 frames)
                    (8, 8),  # 8x8 grid (64 frames)
                    (1, 1),  # Single sprite
                ]
                
                best_frame = None
                
                for cols, rows in layouts:
                    try:
                        frame_width = sheet_width // cols
                        frame_height = sheet_height // rows
                        
                        # Skip if frame would be too small
                        if frame_width < 16 or frame_height < 16:
                            continue
                            
                        # Extract first frame
                        frame = pg.Surface((frame_width, frame_height), pg.SRCALPHA)
                        frame.blit(sprite_sheet, (0, 0), (0, 0, frame_width, frame_height))
                        
                        # Check if frame has meaningful content (not mostly transparent)
                        pixels = pg.surfarray.array3d(frame)
                        alpha_data = pg.surfarray.array_alpha(frame)
                        non_transparent_ratio = (alpha_data > 50).sum() / alpha_data.size
                        
                        if non_transparent_ratio > 0.1:  # At least 10% non-transparent
                            best_frame = frame
                            break
                    except:
                        continue
                
                if best_frame is None:
                    # Fallback: try to use the whole image if it's reasonably sized
                    if sheet_width <= 256 and sheet_height <= 256:
                        best_frame = sprite_sheet
                
                if best_frame:
                    # Scale preserving aspect ratio
                    orig_width = best_frame.get_width()
                    orig_height = best_frame.get_height()
                    
                    # Calculate scale factor to fit within sprite_size x sprite_size
                    scale = min(sprite_size / orig_width, sprite_size / orig_height)
                    new_width = int(orig_width * scale)
                    new_height = int(orig_height * scale)
                    
                    scaled_sprite = pg.transform.scale(best_frame, (new_width, new_height))
                    
                    # Create final surface centered
                    final_sprite = pg.Surface((sprite_size, sprite_size), pg.SRCALPHA)
                    final_sprite.fill((0, 0, 0, 0))  # Transparent background
                    
                    # Center the scaled sprite
                    x_offset = (sprite_size - new_width) // 2
                    y_offset = (sprite_size - new_height) // 2
                    final_sprite.blit(scaled_sprite, (x_offset, y_offset))
                    
                    # Cache it
                    self._sprite_cache[cache_key] = final_sprite
                    return final_sprite
                
        except Exception as e:
            print(f"Error loading character sprite for {char_name}: {e}")
        
        return None
    
    def _render_scroll_indicators(self, screen, start_y: int, visible_height: int, 
                                scroll_offset: int, total_items: int, visible_items: int):
        """Render scroll indicators on the right side."""
        if total_items <= visible_items:
            return
        
        # Scroll bar dimensions
        bar_width = 8
        bar_x = self.screen_width - 60
        bar_y = start_y
        bar_height = visible_height
        
        # Draw scroll bar background
        bar_bg = pg.Rect(bar_x, bar_y, bar_width, bar_height)
        pg.draw.rect(screen, (60, 60, 60), bar_bg, border_radius=4)
        
        # Calculate scroll thumb position and size
        thumb_ratio = visible_items / total_items
        thumb_height = max(20, int(bar_height * thumb_ratio))
        
        scroll_ratio = scroll_offset / (total_items - visible_items) if total_items > visible_items else 0
        thumb_y = bar_y + int((bar_height - thumb_height) * scroll_ratio)
        
        # Draw scroll thumb
        thumb_rect = pg.Rect(bar_x, thumb_y, bar_width, thumb_height)
        pg.draw.rect(screen, self.primary_color, thumb_rect, border_radius=4)
        
        # Draw scroll arrows
        arrow_size = 15
        # Up arrow
        if scroll_offset > 0:
            up_arrow_y = start_y - 25
            up_points = [
                (bar_x + bar_width // 2, up_arrow_y),
                (bar_x + bar_width // 2 - arrow_size // 2, up_arrow_y + arrow_size),
                (bar_x + bar_width // 2 + arrow_size // 2, up_arrow_y + arrow_size)
            ]
            pg.draw.polygon(screen, self.primary_color, up_points)
        
        # Down arrow
        if scroll_offset + visible_items < total_items:
            down_arrow_y = start_y + visible_height + 10
            down_points = [
                (bar_x + bar_width // 2, down_arrow_y + arrow_size),
                (bar_x + bar_width // 2 - arrow_size // 2, down_arrow_y),
                (bar_x + bar_width // 2 + arrow_size // 2, down_arrow_y)
            ]
            pg.draw.polygon(screen, self.primary_color, down_points)
    
    def _render_leaderboard_instructions(self, screen):
        """Render navigation instructions."""
        instructions = ["↑↓ Navigate • ESC Back to Menu"]
        
        instruction_text = self.small_font.render(instructions[0], True, self.secondary_color)
        instruction_rect = instruction_text.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        screen.blit(instruction_text, instruction_rect)
    
    def handle_leaderboard_input(self, event) -> Optional[str]:
        """Handle input for leaderboard screen."""
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                # Return to main menu
                self.set_state(MenuState.MAIN)
                return "leaderboard_back"  # Return to main menu
            elif event.key == pg.K_UP:
                # Navigate up in leaderboard
                if hasattr(self, 'character_manager'):
                    character_count = len(self.character_manager.get_character_list())
                    if character_count > 0:
                        if not hasattr(self, 'leaderboard_selected'):
                            self.leaderboard_selected = 0
                        self.leaderboard_selected = (self.leaderboard_selected - 1) % character_count
                return None
            elif event.key == pg.K_DOWN:
                # Navigate down in leaderboard
                if hasattr(self, 'character_manager'):
                    character_count = len(self.character_manager.get_character_list())
                    if character_count > 0:
                        if not hasattr(self, 'leaderboard_selected'):
                            self.leaderboard_selected = 0
                        self.leaderboard_selected = (self.leaderboard_selected + 1) % character_count
                return None
            elif event.key == pg.K_PAGEUP:
                # Page up (move up by visible page size)
                if hasattr(self, 'character_manager'):
                    character_count = len(self.character_manager.get_character_list())
                    if character_count > 0:
                        max_visible = max(1, (self.screen_height - 300) // 100)  # Estimate visible entries
                        if not hasattr(self, 'leaderboard_selected'):
                            self.leaderboard_selected = 0
                        self.leaderboard_selected = max(0, self.leaderboard_selected - max_visible)
                return None
            elif event.key == pg.K_PAGEDOWN:
                # Page down (move down by visible page size)
                if hasattr(self, 'character_manager'):
                    character_count = len(self.character_manager.get_character_list())
                    if character_count > 0:
                        max_visible = max(1, (self.screen_height - 300) // 100)  # Estimate visible entries
                        if not hasattr(self, 'leaderboard_selected'):
                            self.leaderboard_selected = 0
                        self.leaderboard_selected = min(character_count - 1, self.leaderboard_selected + max_visible)
                return None
        elif event.type == pg.MOUSEMOTION:
            # Update selection based on mouse hover
            self.check_mouse_hover_leaderboard(event.pos)
            return None
        elif event.type == pg.MOUSEWHEEL:
            # Mouse wheel scrolling support
            if hasattr(self, 'character_manager'):
                character_count = len(self.character_manager.get_character_list())
                if character_count > 0:
                    if not hasattr(self, 'leaderboard_selected'):
                        self.leaderboard_selected = 0
                    
                    # Scroll up (negative y) or down (positive y)
                    scroll_direction = -event.y  # Invert for natural scrolling
                    self.leaderboard_selected = max(0, min(character_count - 1, 
                                                          self.leaderboard_selected + scroll_direction))
            return None
        return None
"""
Enhanced menu system for S.A.C.K. BATTLE: A NIKKE FAN GAME
Includes welcome screen, main menu, and settings with music support.
"""

import pygame as pg
import math
import os
import random
from typing import Optional, Dict, List, Tuple
from enum import Enum
from src.save_manager import GameSaveManager, SaveSlot

class MenuState(Enum):
    """Different menu states."""
    WELCOME = "welcome"
    MAIN = "main"
    SETTINGS = "settings"
    SAVE_LOAD = "save_load"

class AudioManager:
    """Handles background music and sound effects."""
    
    def __init__(self):
        """Initialize the audio manager."""
        pg.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        pg.mixer.set_num_channels(16)  # Increase number of channels for better sound mixing
        self.current_music = None
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.music_paused = False
        self.sound_cache = {}  # Cache for sound effects
        self.burst_channel = pg.mixer.Channel(15)  # Dedicated channel for burst sounds
        
    def play_music(self, music_path: str, loop: bool = True):
        """Play background music."""
        if self.current_music != music_path:
            try:
                pg.mixer.music.load(music_path)
                pg.mixer.music.set_volume(self.music_volume)
                pg.mixer.music.play(-1 if loop else 0)
                self.current_music = music_path
                print(f"Playing music: {music_path}")
            except Exception as e:
                print(f"Could not load music {music_path}: {e}")
    
    def stop_music(self):
        """Stop background music."""
        pg.mixer.music.stop()
        self.current_music = None
    
    def pause_music(self):
        """Pause background music."""
        pg.mixer.music.pause()
        self.music_paused = True
    
    def resume_music(self):
        """Resume background music."""
        pg.mixer.music.unpause()
        self.music_paused = False
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        pg.mixer.music.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume: float):
        """Set SFX volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def load_sound(self, sound_path: str) -> Optional[pg.mixer.Sound]:
        """Load and cache a sound effect."""
        if sound_path in self.sound_cache:
            return self.sound_cache[sound_path]
        
        try:
            if os.path.exists(sound_path):
                sound = pg.mixer.Sound(sound_path)
                sound.set_volume(self.sfx_volume)
                self.sound_cache[sound_path] = sound
                print(f"Loaded sound: {sound_path}")
                return sound
            else:
                print(f"Sound file not found: {sound_path}")
                return None
        except Exception as e:
            print(f"Could not load sound {sound_path}: {e}")
            return None
    
    def play_sound(self, sound_path: str):
        """Play a sound effect."""
        sound = self.load_sound(sound_path)
        if sound:
            sound.set_volume(self.sfx_volume)
            sound.play()
    
    def play_burst_sound(self, character_name: str):
        """Play character-specific burst sound on dedicated channel."""
        burst_path = f"assets/images/Characters/{character_name}/burst.mp3"
        sound = self.load_sound(burst_path)
        if sound:
            # Stop any currently playing burst sound and play new one
            if self.burst_channel.get_busy():
                self.burst_channel.stop()
            sound.set_volume(self.sfx_volume)
            self.burst_channel.play(sound)
            print(f"Playing burst sound for {character_name}")

class EnhancedMenuSystem:
    """Enhanced menu system with welcome screen, main menu, and settings."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize the enhanced menu system."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_state = MenuState.WELCOME
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
        
        # Menu selection
        self.main_menu_selection = 0
        self.main_menu_options = ["NEW GAME", "LOAD GAME", "SETTINGS", "QUIT"]
        
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
        
        # Initialize fonts
        self.title_font = pg.font.Font(None, 120)
        self.subtitle_font = pg.font.Font(None, 60)
        self.menu_font = pg.font.Font(None, 48)
        self.small_font = pg.font.Font(None, 32)
        self.large_font = pg.font.Font(None, 72)
        
        # Colors - Clean White Theme (matching main menu)
        self.primary_color = (255, 255, 255)    # Pure white
        self.secondary_color = (180, 180, 180)  # Light gray
        self.accent_color = (220, 220, 220)     # Light accent
        self.text_color = (255, 255, 255)       # Bright white
        self.bg_color = (20, 20, 30)            # Dark background
        self.glow_color = (200, 200, 200)       # Light glow
        self.warning_color = (255, 100, 100)    # Red warning
        self.success_color = (100, 255, 100)    # Green success
        
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
        try:
            bkg_folder = "assets/images/Menu/BKG"
            if os.path.exists(bkg_folder):
                backgrounds = [f for f in os.listdir(bkg_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if backgrounds:
                    random_bg = random.choice(backgrounds)
                    bg_path = os.path.join(bkg_folder, random_bg)
                    self.main_menu_bg = pg.image.load(bg_path)
                    self.main_menu_bg = pg.transform.scale(self.main_menu_bg, (self.screen_width, self.screen_height))
                    print(f"Loaded random main menu background: {random_bg}")
                    return
            
            # Fallback if no backgrounds found
            self.main_menu_bg = pg.Surface((self.screen_width, self.screen_height))
            self.main_menu_bg.fill((20, 20, 40))
            print("Using default main menu background")
            
        except Exception as e:
            print(f"Error loading random background: {e}")
            self.main_menu_bg = pg.Surface((self.screen_width, self.screen_height))
            self.main_menu_bg.fill((20, 20, 40))
    
    def start_welcome_music(self):
        """Start playing welcome music."""
        self.audio_manager.play_music("assets/sounds/music/welcome.mp3")
    
    def start_main_menu_music(self):
        """Start playing main menu music."""
        self.audio_manager.play_music("assets/sounds/music/main-menu.mp3")
    
    def start_battle_music(self):
        """Start playing battle music."""
        self.audio_manager.play_music("assets/sounds/music/battle.wav")
    
    def get_main_menu_option_rect(self, option_index: int) -> pg.Rect:
        """Get the rectangle for a main menu option."""
        menu_start_y = 300
        option_spacing = 80
        y_pos = menu_start_y + option_index * option_spacing
        return pg.Rect(self.screen_width // 2 - 200, y_pos - 30, 400, 60)
    
    def check_mouse_hover_main_menu(self, mouse_pos: tuple) -> int:
        """Check if mouse is hovering over a main menu option."""
        for i, option in enumerate(self.main_menu_options):
            option_rect = self.get_main_menu_option_rect(i)
            if option_rect.collidepoint(mouse_pos):
                return i
        return None
    
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
                    if self.main_menu_selection == 0:  # NEW GAME
                        return "new_game"
                    elif self.main_menu_selection == 1:  # LOAD GAME
                        self.current_state = MenuState.SAVE_LOAD
                        self.save_load_mode = "load"
                        self.save_load_selection = 0
                        return None
                    elif self.main_menu_selection == 2:  # SETTINGS
                        self.current_state = MenuState.SETTINGS
                        self.settings_tab = 0
                        self.settings_selection = 0
                        return None
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_UP or event.key == pg.K_w:
                self.main_menu_selection = (self.main_menu_selection - 1) % len(self.main_menu_options)
            elif event.key == pg.K_DOWN or event.key == pg.K_s:
                self.main_menu_selection = (self.main_menu_selection + 1) % len(self.main_menu_options)
            elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                if self.main_menu_selection == 0:  # NEW GAME
                    return "new_game"
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
                return "quit"
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
        """Draw a clean background with random image."""
        # Use random background if available
        if hasattr(self, 'main_menu_bg') and self.main_menu_bg:
            screen.blit(self.main_menu_bg, (0, 0))
            # Add semi-transparent overlay for better text readability
            overlay = pg.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
        else:
            # Fallback: Dark gradient from top to bottom
            for y in range(self.screen_height):
                progress = y / self.screen_height
                # Smooth gradient from dark gray to darker gray
                color_value = int(25 + progress * 5)  # 25 to 30
                color = (color_value, color_value, color_value + 2)
                pg.draw.line(screen, color, (0, y), (self.screen_width, y))
        
        # Subtle grid pattern for texture (reduce opacity over background)
        grid_size = 40
        grid_color = (35, 35, 40) if not hasattr(self, 'main_menu_bg') else (50, 50, 50)
        for x in range(0, self.screen_width, grid_size):
            pg.draw.line(screen, grid_color, (x, 0), (x, self.screen_height), 1)
        for y in range(0, self.screen_height, grid_size):
            pg.draw.line(screen, grid_color, (0, y), (self.screen_width, y), 1)
    
    def _render_main_logo_clean(self, screen: pg.Surface):
        """Render the main logo with clean styling."""
        # Clean title text without glow effects
        title_text = "S.A.C.K. BATTLE"
        subtitle_text = "A NIKKE FAN GAME"
        
        # Main title
        title_surface = self.title_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 150))
        
        # Subtle shadow for depth
        shadow_surface = self.title_font.render(title_text, True, (100, 100, 100))
        shadow_rect = shadow_surface.get_rect(center=(self.screen_width // 2 + 3, 153))
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_surface = self.subtitle_font.render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_width // 2, 200))
        screen.blit(subtitle_surface, subtitle_rect)
        
        # Clean decorative line
        line_width = 300
        line_y = 230
        line_start_x = self.screen_width // 2 - line_width // 2
        line_end_x = self.screen_width // 2 + line_width // 2
        pg.draw.line(screen, (180, 180, 180), (line_start_x, line_y), (line_end_x, line_y), 2)
    
    def _render_clean_menu_options(self, screen: pg.Surface):
        """Render menu options with clean anime styling."""
        menu_start_y = 300
        option_spacing = 80
        
        for i, option in enumerate(self.main_menu_options):
            y_pos = menu_start_y + i * option_spacing
            is_selected = (i == self.main_menu_selection)
            
            # Clean selection indicator
            if is_selected:
                # Simple highlight bar
                highlight_rect = pg.Rect(self.screen_width // 2 - 200, y_pos - 30, 400, 60)
                pg.draw.rect(screen, (50, 50, 55), highlight_rect, border_radius=8)
                pg.draw.rect(screen, (180, 180, 180), highlight_rect, 2, border_radius=8)
            
            # Option text
            text_color = (255, 255, 255) if is_selected else (180, 180, 180)
            option_surface = self.menu_font.render(option, True, text_color)
            option_rect = option_surface.get_rect(center=(self.screen_width // 2, y_pos))
            
            # Clean text shadow for selected items
            if is_selected:
                shadow_surface = self.menu_font.render(option, True, (80, 80, 80))
                shadow_rect = shadow_surface.get_rect(center=(self.screen_width // 2 + 2, y_pos + 2))
                screen.blit(shadow_surface, shadow_rect)
            
            screen.blit(option_surface, option_rect)
        
        # Navigation instructions
        nav_text = "Use ARROW KEYS or MOUSE to navigate • ENTER or CLICK to select"
        nav_surface = self.small_font.render(nav_text, True, (140, 140, 140))
        nav_rect = nav_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        screen.blit(nav_surface, nav_rect)
    
    def _render_version_info(self, screen: pg.Surface):
        """Render version info in corner."""
        version_text = "v1.0.0"
        version_surface = pg.font.Font(None, 24).render(version_text, True, (120, 120, 120))
        version_rect = version_surface.get_rect(bottomright=(self.screen_width - 20, self.screen_height - 20))
        screen.blit(version_surface, version_rect)
    
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
        elif self.current_state == MenuState.SETTINGS:
            self.render_settings(screen)
        elif self.current_state == MenuState.SAVE_LOAD:
            self.render_save_load(screen)
    
    def handle_input(self, event) -> Optional[str]:
        """Handle input for current menu state."""
        if self.current_state == MenuState.WELCOME:
            return self.handle_welcome_input(event)
        elif self.current_state == MenuState.MAIN:
            return self.handle_main_menu_input(event)
        elif self.current_state == MenuState.SETTINGS:
            return self.handle_settings_input(event)
        elif self.current_state == MenuState.SAVE_LOAD:
            return self.handle_save_load_input(event)
        return None
    
    def set_state(self, state: MenuState, preserve_music: bool = False):
        """Set the menu state."""
        self.current_state = state
        
        # Start appropriate music only if not preserving current music
        if not preserve_music:
            if state == MenuState.WELCOME:
                self.start_welcome_music()
            elif state in [MenuState.MAIN, MenuState.SETTINGS]:
                self.start_main_menu_music()
    
    def get_state(self) -> MenuState:
        """Get current menu state."""
        return self.current_state
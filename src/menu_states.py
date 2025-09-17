"""
Menu state management system for Kingdom-Pygame.
Handles menu navigation, settings, and save/load functionality.
"""

import pygame as pg
import math
import os
from typing import Optional, Dict, List, Tuple
from enum import Enum
from src.save_manager import GameSaveManager, SaveSlot


class MenuState(Enum):
    """Different menu states."""
    WELCOME = "welcome"
    MAIN = "main"
    SETTINGS = "settings"
    SAVE_LOAD = "save_load"
    LEADERBOARD = "leaderboard"


class MenuStateManager:
    """Manages menu states, navigation, and user interactions."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize the menu state manager."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Current state
        self.current_state = MenuState.WELCOME
        
        # Menu navigation
        self.main_menu_selected = 0
        self.main_menu_options = ["Start Game", "Load Game", "Leaderboard", "Settings", "Exit"]
        
        # Settings navigation
        self.settings_tab = 0  # 0: Audio, 1: Video, 2: Controls
        self.settings_tabs = ["Audio", "Video", "Controls"]
        self.settings_selected = 0
        self.dragging_slider = False
        self.dragging_setting = None
        
        # Settings values
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.fullscreen_enabled = False
        self.resolution_index = 0
        self.available_resolutions = [
            (1280, 720),
            (1920, 1080),
            (2560, 1440),
            (3840, 2160)
        ]
        
        # Save/Load system
        self.save_manager = GameSaveManager()
        self.save_load_mode = "load"  # "load" or "save"
        self.selected_slot = 0
        self.max_save_slots = 5
        
        # Leaderboard navigation
        self.leaderboard_selected = 0
        self.leaderboard_scroll_offset = 0
        
        # Animation timers
        self.animation_time = 0.0
        self.pulse_intensity = 1.0
    
    def update(self, dt: float):
        """Update state manager timers."""
        self.animation_time += dt
        self.pulse_intensity = 1.0 + math.sin(self.animation_time * 3) * 0.3
    
    def set_state(self, state: MenuState, preserve_music: bool = False):
        """Set the menu state."""
        self.current_state = state
        
        # Reset selections when changing states
        if state == MenuState.MAIN:
            self.main_menu_selected = 0
        elif state == MenuState.SETTINGS:
            self.settings_selected = 0
            self.settings_tab = 0
        elif state == MenuState.SAVE_LOAD:
            self.selected_slot = 0
        elif state == MenuState.LEADERBOARD:
            self.leaderboard_selected = 0
            self.leaderboard_scroll_offset = 0
    
    def get_state(self) -> MenuState:
        """Get current menu state."""
        return self.current_state
    
    # Navigation helpers
    def get_main_menu_option_rect(self, option_index: int) -> pg.Rect:
        """Get rectangle for main menu option."""
        option_height = 80
        total_height = len(self.main_menu_options) * option_height
        start_y = (self.screen_height - total_height) // 2 + 50
        y = start_y + option_index * option_height
        
        return pg.Rect(self.screen_width // 2 - 150, y, 300, 60)
    
    def check_mouse_hover_main_menu(self, mouse_pos: tuple) -> int:
        """Check which main menu option is hovered."""
        for i in range(len(self.main_menu_options)):
            rect = self.get_main_menu_option_rect(i)
            if rect.collidepoint(mouse_pos):
                return i
        return -1
    
    def handle_main_menu_mouse_click(self, mouse_pos: tuple):
        """Handle mouse click on main menu."""
        for i in range(len(self.main_menu_options)):
            rect = self.get_main_menu_option_rect(i)
            if rect.collidepoint(mouse_pos):
                self.main_menu_selected = i
                return self.main_menu_options[i].lower().replace(" ", "_")
        return None
    
    # Settings navigation
    def get_settings_tab_rect(self, tab_index: int) -> pg.Rect:
        """Get rectangle for settings tab."""
        tab_width = 120
        total_width = len(self.settings_tabs) * tab_width
        start_x = (self.screen_width - total_width) // 2
        x = start_x + tab_index * tab_width
        
        return pg.Rect(x, 150, tab_width - 10, 40)
    
    def get_audio_slider_rect(self, setting_index: int) -> pg.Rect:
        """Get rectangle for audio slider."""
        y = 250 + setting_index * 60
        return pg.Rect(self.screen_width // 2 - 100, y, 200, 30)
    
    def get_video_setting_rect(self, setting_index: int) -> pg.Rect:
        """Get rectangle for video setting."""
        y = 250 + setting_index * 60
        return pg.Rect(self.screen_width // 2 - 150, y, 300, 40)
    
    def handle_settings_mouse_click(self, mouse_pos: tuple):
        """Handle mouse click in settings."""
        # Check tab clicks
        for i in range(len(self.settings_tabs)):
            tab_rect = self.get_settings_tab_rect(i)
            if tab_rect.collidepoint(mouse_pos):
                self.settings_tab = i
                self.settings_selected = 0
                return None
        
        # Handle tab-specific clicks
        if self.settings_tab == 0:  # Audio
            return self.handle_audio_mouse_click(mouse_pos)
        elif self.settings_tab == 1:  # Video
            return self.handle_video_mouse_click(mouse_pos)
        
        return None
    
    def handle_audio_mouse_click(self, mouse_pos: tuple):
        """Handle audio settings mouse click."""
        # Music volume slider
        music_rect = self.get_audio_slider_rect(0)
        if music_rect.collidepoint(mouse_pos):
            self.dragging_slider = True
            self.dragging_setting = "music_volume"
            self.update_slider_value(mouse_pos, music_rect, "music_volume")
            return None
        
        # SFX volume slider
        sfx_rect = self.get_audio_slider_rect(1)
        if sfx_rect.collidepoint(mouse_pos):
            self.dragging_slider = True
            self.dragging_setting = "sfx_volume"
            self.update_slider_value(mouse_pos, sfx_rect, "sfx_volume")
            return None
        
        return None
    
    def handle_video_mouse_click(self, mouse_pos: tuple):
        """Handle video settings mouse click."""
        # Resolution setting
        resolution_rect = self.get_video_setting_rect(0)
        if resolution_rect.collidepoint(mouse_pos):
            self.cycle_resolution()
            return "resolution_changed"
        
        # Fullscreen toggle
        fullscreen_rect = self.get_video_setting_rect(1)
        if fullscreen_rect.collidepoint(mouse_pos):
            self.fullscreen_enabled = not self.fullscreen_enabled
            return "fullscreen_changed"
        
        return None
    
    def update_slider_value(self, mouse_pos: tuple, slider_rect: pg.Rect, setting_name: str):
        """Update slider value based on mouse position."""
        progress = (mouse_pos[0] - slider_rect.x) / slider_rect.width
        progress = max(0.0, min(1.0, progress))
        
        if setting_name == "music_volume":
            self.music_volume = progress
        elif setting_name == "sfx_volume":
            self.sfx_volume = progress
    
    def handle_slider_drag(self, mouse_pos: tuple):
        """Handle slider dragging."""
        if not self.dragging_slider or not self.dragging_setting:
            return
        
        if self.dragging_setting == "music_volume":
            slider_rect = self.get_audio_slider_rect(0)
            self.update_slider_value(mouse_pos, slider_rect, "music_volume")
        elif self.dragging_setting == "sfx_volume":
            slider_rect = self.get_audio_slider_rect(1)
            self.update_slider_value(mouse_pos, slider_rect, "sfx_volume")
    
    def stop_slider_drag(self):
        """Stop slider dragging."""
        self.dragging_slider = False
        self.dragging_setting = None
    
    def cycle_resolution(self):
        """Cycle to next available resolution."""
        self.resolution_index = (self.resolution_index + 1) % len(self.available_resolutions)
    
    def get_current_resolution(self) -> tuple:
        """Get currently selected resolution."""
        return self.available_resolutions[self.resolution_index]
    
    def get_resolution_text(self) -> str:
        """Get resolution as text."""
        width, height = self.get_current_resolution()
        return f"{width}x{height}"
    
    # Save/Load functionality
    def set_save_load_mode(self, mode: str):
        """Set save/load mode ('save' or 'load')."""
        self.save_load_mode = mode
        self.selected_slot = 0
    
    def get_save_slot_rect(self, slot_index: int) -> pg.Rect:
        """Get rectangle for save slot."""
        y = 200 + slot_index * 80
        return pg.Rect(50, y, self.screen_width - 100, 70)
    
    def get_selected_save_slot(self) -> int:
        """Get currently selected save slot."""
        return self.selected_slot
    
    def navigate_save_slots(self, direction: int):
        """Navigate save slots up/down."""
        self.selected_slot = max(0, min(self.max_save_slots - 1, self.selected_slot + direction))
    
    def get_save_slot_data(self, slot_index: int) -> Optional[SaveSlot]:
        """Get save slot data."""
        return self.save_manager.get_save_slot(slot_index)
    
    def delete_save_slot(self, slot_index: int):
        """Delete a save slot."""
        self.save_manager.delete_save(slot_index)
    
    # Settings persistence
    def get_settings_dict(self) -> Dict:
        """Get all settings as dictionary."""
        return {
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "fullscreen_enabled": self.fullscreen_enabled,
            "resolution_index": self.resolution_index
        }
    
    def apply_settings_dict(self, settings: Dict):
        """Apply settings from dictionary."""
        self.music_volume = settings.get("music_volume", 0.7)
        self.sfx_volume = settings.get("sfx_volume", 0.8)
        self.fullscreen_enabled = settings.get("fullscreen_enabled", False)
        self.resolution_index = settings.get("resolution_index", 0)
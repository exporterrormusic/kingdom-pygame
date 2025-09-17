"""
Game states system for the twin-stick shooter.
Handles different game states like menu, playing, and game over.
"""

import pygame as pg
from enum import Enum
from typing import Optional
import sys
from src.enhanced_menu import EnhancedMenuSystem, MenuState

class GameState(Enum):
    """Different game states."""
    WELCOME = "welcome"
    MENU = "menu"
    CHARACTER_SELECT = "character_select"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    PAUSED = "paused"
    SETTINGS = "settings"
    SAVE_LOAD = "save_load"

class StateManager:
    """Manages game state transitions and rendering."""
    
    def __init__(self, screen: pg.Surface, font: pg.font.Font, small_font: pg.font.Font):
        """Initialize the state manager."""
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.current_state = GameState.MENU  # Start with main menu
        self.previous_state = None
        
        # Initialize enhanced menu system
        self.enhanced_menu = EnhancedMenuSystem(screen.get_width(), screen.get_height())
        # Start main menu music since we're starting with the main menu
        self.enhanced_menu.start_main_menu_music()
        
        # Menu selection (legacy for old menu rendering)
        self.menu_selection = 0
        self.menu_options = ["Select Character", "Quit"]
        
        # Game over data
        self.final_score = 0
        self.final_wave = 0
        self.final_kills = 0
        
        # Pause menu
        self.pause_selection = 0
        self.pause_options = ["Resume", "Settings", "Main Menu"]
    
    def handle_welcome_input(self, event) -> bool:
        """Handle input for welcome screen. Returns True if state should change."""
        result = self.enhanced_menu.handle_input(event)
        if result == "main_menu":
            self.change_state(GameState.MENU)
            return True
        return True
    
    def handle_enhanced_menu_input(self, event) -> bool:
        """Handle input for enhanced menu. Returns True if should continue."""
        result = self.enhanced_menu.handle_input(event)
        if result == "new_game":
            self.change_state(GameState.CHARACTER_SELECT)
            return True
        elif result == "load_game":
            # TODO: Implement load game functionality
            return True
        elif result == "quit":
            return False
        return True
    
    def handle_menu_input(self, keys_pressed: dict, keys_just_pressed: list) -> bool:
        """Handle input for menu state. Returns True if state should change."""
        if pg.K_UP in keys_just_pressed or pg.K_w in keys_just_pressed:
            self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
        elif pg.K_DOWN in keys_just_pressed or pg.K_s in keys_just_pressed:
            self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
        elif pg.K_RETURN in keys_just_pressed or pg.K_SPACE in keys_just_pressed:
            if self.menu_selection == 0:  # Select Character
                self.change_state(GameState.CHARACTER_SELECT)
                return True
            elif self.menu_selection == 1:  # Quit
                return False
        
        return True
    
    def handle_game_over_input(self, keys_just_pressed: list) -> bool:
        """Handle input for game over state. Returns True if should continue."""
        if (pg.K_RETURN in keys_just_pressed or pg.K_SPACE in keys_just_pressed or
            pg.K_r in keys_just_pressed):
            # Quick restart - go directly to character select for survival mode
            self.change_state(GameState.CHARACTER_SELECT)
            return True
        elif pg.K_ESCAPE in keys_just_pressed:
            # Return to main menu
            self.change_state(GameState.MENU)
            return True
        
        return True
    
    def handle_pause_input(self, keys_just_pressed: list):
        """Handle input for pause state."""
        if pg.K_p in keys_just_pressed or pg.K_ESCAPE in keys_just_pressed:
            self.change_state(GameState.PLAYING)
        elif pg.K_UP in keys_just_pressed or pg.K_w in keys_just_pressed:
            self.pause_selection = (self.pause_selection - 1) % len(self.pause_options)
        elif pg.K_DOWN in keys_just_pressed or pg.K_s in keys_just_pressed:
            self.pause_selection = (self.pause_selection + 1) % len(self.pause_options)
        elif pg.K_RETURN in keys_just_pressed or pg.K_SPACE in keys_just_pressed:
            if self.pause_selection == 0:  # Resume
                self.change_state(GameState.PLAYING)
            elif self.pause_selection == 1:  # Settings
                self.change_state(GameState.SETTINGS)
            elif self.pause_selection == 2:  # Main Menu
                self.change_state(GameState.MENU)
    
    def update(self, dt: float):
        """Update state animations and effects."""
        if self.current_state in [GameState.WELCOME, GameState.MENU, GameState.SETTINGS, GameState.SAVE_LOAD]:
            self.enhanced_menu.update(dt)
    
    def change_state(self, new_state: GameState):
        """Change to a new game state."""
        self.previous_state = self.current_state
        self.current_state = new_state
        
        # Reset menu selection when entering menu
        if new_state == GameState.MENU:
            self.menu_selection = 0
        elif new_state == GameState.PAUSED:
            self.pause_selection = 0
        elif new_state == GameState.CHARACTER_SELECT:
            # Start character select music when entering character selection
            self.enhanced_menu.start_character_select_music()
            
        # Update enhanced menu state
        if new_state == GameState.WELCOME:
            self.enhanced_menu.set_state(MenuState.WELCOME)
            self.enhanced_menu.set_came_from_paused_game(False)
        elif new_state == GameState.MENU:
            # Set whether we came from a paused game
            came_from_paused = (self.previous_state == GameState.PAUSED)
            self.enhanced_menu.set_came_from_paused_game(came_from_paused)
            self.enhanced_menu.set_state(MenuState.MAIN)
        elif new_state == GameState.SETTINGS:
            # Preserve music if coming from paused game, otherwise use default music
            preserve_music = (self.previous_state == GameState.PAUSED)
            self.enhanced_menu.set_state(MenuState.SETTINGS, preserve_music)
        elif new_state == GameState.SAVE_LOAD:
            self.enhanced_menu.set_state(MenuState.SAVE_LOAD)
    
    def render_welcome(self):
        """Render the welcome screen using enhanced menu."""
        self.enhanced_menu.render(self.screen)
    
    def render_enhanced_menu(self):
        """Render the enhanced main menu."""
        self.enhanced_menu.render(self.screen)
    
    def render_settings(self):
        """Render the settings menu using enhanced menu."""
        self.enhanced_menu.render(self.screen)
    
    def render_save_load(self):
        """Render the save/load menu using enhanced menu."""
        self.enhanced_menu.render(self.screen)
    
    def render_menu(self):
        """Render the main menu."""
        # Clear screen with dark background
        self.screen.fill((15, 15, 25))
        
        # Title (larger for 1920x1080)
        title_font = pg.font.Font(None, 96)  # Much larger title
        subtitle_font = pg.font.Font(None, 48)  # Larger subtitle
        
        title_text = title_font.render("KINGDOM", True, (255, 255, 255))
        subtitle_text = subtitle_font.render("Twin-Stick Shooter", True, (150, 150, 150))
        
        title_rect = title_text.get_rect(center=(960, 300))
        subtitle_rect = subtitle_text.get_rect(center=(960, 380))
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Menu options (larger)
        option_font = pg.font.Font(None, 64)  # Larger menu options
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 100) if i == self.menu_selection else (255, 255, 255)
            option_text = option_font.render(option, True, color)
            option_rect = option_text.get_rect(center=(960, 500 + i * 80))
            self.screen.blit(option_text, option_rect)
            
            # Selection indicator
            if i == self.menu_selection:
                pg.draw.rect(self.screen, (255, 255, 100), option_rect, 3)
        
        # Controls (larger and better positioned)
        controls_text = [
            "Controls:",
            "WASD/Arrows - Move",
            "Mouse - Aim",
            "Left Click - Shoot",
            "Shift - Dash (once per press)",
            "P - Pause",
            "ESC - Quit"
        ]
        
        control_font = pg.font.Font(None, 36)
        for i, control in enumerate(controls_text):
            color = (255, 255, 255) if i == 0 else (150, 150, 150)
            font = pg.font.Font(None, 48) if i == 0 else control_font
            control_surface = font.render(control, True, color)
            self.screen.blit(control_surface, (100, 700 + i * 40))
        
        # Navigation hint (larger)
        nav_font = pg.font.Font(None, 32)
        nav_text = nav_font.render("Use UP/DOWN arrows and ENTER to select", True, (100, 100, 100))
        nav_rect = nav_text.get_rect(center=(960, 1000))
        self.screen.blit(nav_text, nav_rect)
    
    def render_game_over(self):
        """Render the survival mode game over screen."""
        # Semi-transparent overlay
        overlay = pg.Surface((1920, 1080))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text (larger)
        game_over_font = pg.font.Font(None, 96)
        game_over_text = game_over_font.render("SURVIVAL ENDED", True, (255, 100, 100))
        game_over_rect = game_over_text.get_rect(center=(960, 350))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Survival results subtitle
        subtitle_font = pg.font.Font(None, 48)
        subtitle_text = subtitle_font.render("Final Results", True, (200, 200, 255))
        subtitle_rect = subtitle_text.get_rect(center=(960, 420))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Final stats (organized for survival mode)
        stats_font = pg.font.Font(None, 56)
        
        # Calculate survival time (assuming 30 seconds per wave)
        survival_time_seconds = (self.final_wave - 1) * 30
        survival_minutes = survival_time_seconds // 60
        survival_seconds = survival_time_seconds % 60
        
        stats = [
            f"Score: {self.final_score} points",
            f"Waves Survived: {self.final_wave}",
            f"Survival Time: {survival_minutes}m {survival_seconds}s",
            f"Enemies Killed: {self.final_kills}"
        ]
        
        for i, stat in enumerate(stats):
            stat_text = stats_font.render(stat, True, (255, 255, 255))
            stat_rect = stat_text.get_rect(center=(960, 500 + i * 60))
            self.screen.blit(stat_text, stat_rect)
        
        # Performance rating
        rating_font = pg.font.Font(None, 40)
        if self.final_wave >= 10:
            rating = "LEGENDARY SURVIVOR!"
            rating_color = (255, 215, 0)  # Gold
        elif self.final_wave >= 7:
            rating = "Elite Warrior"
            rating_color = (255, 100, 255)  # Purple
        elif self.final_wave >= 5:
            rating = "Skilled Fighter"
            rating_color = (100, 255, 100)  # Green
        elif self.final_wave >= 3:
            rating = "Decent Survivor"
            rating_color = (100, 200, 255)  # Blue
        else:
            rating = "Keep Training"
            rating_color = (255, 200, 100)  # Orange
            
        rating_text = rating_font.render(rating, True, rating_color)
        rating_rect = rating_text.get_rect(center=(960, 750))
        self.screen.blit(rating_text, rating_rect)
        
        # Restart prompt (larger)
        prompt_font = pg.font.Font(None, 40)
        restart_text = prompt_font.render("Press ENTER or SPACE to play again", True, (200, 255, 200))
        restart_rect = restart_text.get_rect(center=(960, 820))
        self.screen.blit(restart_text, restart_rect)
        
        quit_text = prompt_font.render("Press ESC to return to main menu", True, (200, 200, 200))
        quit_rect = quit_text.get_rect(center=(960, 860))
        self.screen.blit(quit_text, quit_rect)
    
    def render_pause(self):
        """Render the enhanced pause screen."""
        # Semi-transparent overlay - use dynamic screen dimensions
        overlay = pg.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(120)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Get screen center
        screen_center_x = self.screen.get_width() // 2
        screen_center_y = self.screen.get_height() // 2
        
        # Pause text (larger)
        pause_font = pg.font.Font(None, 96)
        pause_text = pause_font.render("PAUSED", True, (255, 255, 255))
        pause_rect = pause_text.get_rect(center=(screen_center_x, screen_center_y - 150))
        self.screen.blit(pause_text, pause_rect)
        
        # Pause menu options
        for i, option in enumerate(self.pause_options):
            y_pos = screen_center_y + i * 60
            
            # Selection highlight
            if i == self.pause_selection:
                highlight_color = (255, 100, 150)  # Pink highlight
                highlight_rect = pg.Rect(screen_center_x - 200, y_pos - 25, 400, 50)
                pg.draw.rect(self.screen, highlight_color, highlight_rect, 3, border_radius=10)
            
            # Option text
            text_color = (255, 255, 100) if i == self.pause_selection else (255, 255, 255)
            option_text = self.font.render(option, True, text_color)
            option_rect = option_text.get_rect(center=(screen_center_x, y_pos))
            self.screen.blit(option_text, option_rect)
        
        # Instructions
        instruction_font = pg.font.Font(None, 32)
        instructions = ["UP/DOWN to select • ENTER to confirm", "P or ESC to resume quickly"]
        for i, instruction in enumerate(instructions):
            instruction_text = instruction_font.render(instruction, True, (200, 200, 200))
            instruction_rect = instruction_text.get_rect(center=(960, 750 + i * 35))
            self.screen.blit(instruction_text, instruction_rect)
    
    def set_game_over_stats(self, score: int, wave: int, kills: int):
        """Set the final game stats for game over screen."""
        self.final_score = score
        self.final_wave = wave
        self.final_kills = kills
    
    def get_state(self) -> GameState:
        """Get current game state."""
        return self.current_state
    
    def is_playing(self) -> bool:
        """Check if currently in playing state."""
        return self.current_state == GameState.PLAYING
    
    def is_menu(self) -> bool:
        """Check if currently in menu state."""
        return self.current_state == GameState.MENU
    
    def is_character_select(self) -> bool:
        """Check if currently in character selection state."""
        return self.current_state == GameState.CHARACTER_SELECT
    
    def is_game_over(self) -> bool:
        """Check if currently in game over state."""
        return self.current_state == GameState.GAME_OVER
    
    def is_paused(self) -> bool:
        """Check if currently paused."""
        return self.current_state == GameState.PAUSED
    
    def update_screen_dimensions(self, screen: pg.Surface, width: int, height: int):
        """Update screen dimensions across all systems."""
        self.screen = screen
        # Update the enhanced menu system with new screen dimensions
        self.enhanced_menu.screen = screen
        # Force menu to recalculate positions for new screen size
        self.enhanced_menu.screen_width = width
        self.enhanced_menu.screen_height = height
        # Clear cached animations for new screen size
        self.enhanced_menu.clear_animation_caches()
    
    def handle_pause_mouse_hover(self, mouse_pos: tuple):
        """Handle mouse hover on pause menu options."""
        screen_center_x = self.screen.get_width() // 2
        screen_center_y = self.screen.get_height() // 2
        
        for i, option in enumerate(self.pause_options):
            y_pos = screen_center_y + i * 60
            # Check if mouse is within option bounds
            option_rect = pg.Rect(screen_center_x - 200, y_pos - 25, 400, 50)
            
            if option_rect.collidepoint(mouse_pos):
                self.pause_selection = i
                break
    
    def handle_pause_mouse_click(self, mouse_pos: tuple) -> str:
        """Handle mouse clicks on pause menu options."""
        screen_center_x = self.screen.get_width() // 2
        screen_center_y = self.screen.get_height() // 2
        
        for i, option in enumerate(self.pause_options):
            y_pos = screen_center_y + i * 60
            # Check if click is within option bounds
            option_rect = pg.Rect(screen_center_x - 200, y_pos - 25, 400, 50)
            
            if option_rect.collidepoint(mouse_pos):
                # Update selection and return action
                self.pause_selection = i
                if i == 0:  # Resume
                    return "resume"
                elif i == 1:  # Settings
                    return "settings"
                elif i == 2:  # Main Menu
                    return "main_menu"
        return None
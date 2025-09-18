"""
Character management system for selecting and loading character sprites.
Handles the Characters folder structure and character selection.
"""

import pygame as pg
import os
import math
from typing import List, Dict, Optional
from src.utils.character_config import character_config_manager, CharacterConfig

class CharacterManager:
    """Manages available characters and character selection."""
    
    def __init__(self, characters_folder: str = "assets/images/Characters"):
        """Initialize character manager."""
        self.characters_folder = characters_folder
        self.available_characters = self._scan_characters()
        self.current_character = None
        
        # Set default character if any available
        if self.available_characters:
            self.current_character = list(self.available_characters.keys())[0]
    
    def _scan_characters(self) -> Dict[str, Dict[str, str]]:
        """Scan for available character folders with config files."""
        characters = {}
        
        if not os.path.exists(self.characters_folder):
            print(f"Warning: Characters folder not found: {self.characters_folder}")
            return characters
        
        try:
            # Get available characters from config manager
            available_chars = character_config_manager.get_all_character_names()
            display_names = character_config_manager.get_character_display_names()
            
            for char_name in available_chars:
                sprite_path = character_config_manager.get_character_sprite_path(char_name)
                
                if sprite_path and os.path.exists(sprite_path):
                    characters[char_name] = {
                        'display_name': display_names[char_name],
                        'file_path': sprite_path,
                        'folder_path': os.path.join(self.characters_folder, char_name)
                    }
                    
        except Exception as e:
            print(f"Error scanning characters folder: {e}")
        
        print(f"Found {len(characters)} characters: {list(characters.keys())}")
        return characters
    
    def get_character_list(self) -> List[str]:
        """Get list of available character names."""
        return list(self.available_characters.keys())
    
    def get_character_display_names(self) -> List[str]:
        """Get list of display names for characters."""
        return [char_info['display_name'] for char_info in self.available_characters.values()]
    
    def get_character_path(self, character_name: str) -> Optional[str]:
        """Get file path for a specific character."""
        if character_name in self.available_characters:
            return self.available_characters[character_name]['file_path']
        return None
    
    def set_current_character(self, character_name: str) -> bool:
        """Set the current selected character."""
        if character_name in self.available_characters:
            self.current_character = character_name
            print(f"Selected character: {self.available_characters[character_name]['display_name']}")
            return True
        return False
    
    def get_current_character_path(self) -> Optional[str]:
        """Get path for currently selected character."""
        if self.current_character:
            return self.get_character_path(self.current_character)
        return None
    
    def get_current_character_name(self) -> Optional[str]:
        """Get display name for currently selected character."""
        if self.current_character and self.current_character in self.available_characters:
            return self.available_characters[self.current_character]['display_name']
        return None
    
    def get_next_character(self) -> str:
        """Get next character in the list (for cycling)."""
        char_list = self.get_character_list()
        if not char_list or not self.current_character:
            return char_list[0] if char_list else None
        
        try:
            current_index = char_list.index(self.current_character)
            next_index = (current_index + 1) % len(char_list)
            return char_list[next_index]
        except ValueError:
            return char_list[0]
    
    def get_character_config(self, character_name: str) -> Optional[CharacterConfig]:
        """Get character configuration data."""
        return character_config_manager.get_character_config(character_name)

class CharacterSelectionMenu:
    """Enhanced character selection menu with animations and detail display."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize enhanced character selection menu."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.character_manager = CharacterManager()
        
        # Menu state
        self.selected_index = 0
        self.characters = self.character_manager.get_character_list()
        self.display_names = self.character_manager.get_character_display_names()
        
        # Animation state
        self.selection_animation_time = 0.0
        self.hover_scale = 1.0
        self.selection_glow_intensity = 0.0
        
        # Grid layout settings
        self.columns = 3  # Reduced for better layout with details panel
        self.rows = (len(self.characters) + self.columns - 1) // self.columns
        
        # Layout dimensions
        self.grid_width = int(screen_width * 0.6)  # 60% for grid
        self.detail_width = int(screen_width * 0.35)  # 35% for details
        self.grid_start_x = 50
        self.detail_start_x = self.grid_start_x + self.grid_width + 20
        
        # Fonts
        self.title_font = pg.font.Font(None, 72)
        self.menu_font = pg.font.Font(None, 32)
        self.detail_font = pg.font.Font(None, 28)
        self.stat_font = pg.font.Font(None, 24)
        self.instruction_font = pg.font.Font(None, 28)
        
        # Colors
        self.bg_color = (15, 15, 30)
        self.title_color = (255, 255, 255)
        self.selected_color = (255, 255, 100)
        self.normal_color = (200, 200, 200)
        self.instruction_color = (150, 150, 150)
        self.panel_color = (40, 40, 60)
        self.panel_border_color = (100, 100, 120)
        self.stat_bar_bg = (60, 60, 80)
        self.stat_bar_fill = (100, 200, 100)
        
        # Preview sprites and animations
        self.character_previews = self._load_character_previews()
        self.selected_character_animation = None
        self.animation_time = 0.0
        
        # Initialize with first character selected
        if self.characters:
            self._on_selection_change()
        
    def _load_character_previews(self) -> Dict[str, pg.Surface]:
        """Load character preview sprites with proper aspect ratios."""
        previews = {}
        
        for char_name in self.characters:
            char_path = self.character_manager.get_character_path(char_name)
            if char_path and os.path.exists(char_path):
                try:
                    # Load sprite sheet
                    sprite_sheet = pg.image.load(char_path).convert_alpha()
                    
                    # Extract first frame (down-facing, frame 0) with proper dimensions
                    frame_width = sprite_sheet.get_width() // 3
                    frame_height = sprite_sheet.get_height() // 4
                    
                    first_frame = sprite_sheet.subsurface((0, 0, frame_width, frame_height))
                    
                    # Scale maintaining aspect ratio
                    target_size = 128  # Larger preview size
                    aspect_ratio = frame_width / frame_height
                    
                    if aspect_ratio > 1:
                        # Wider than tall
                        new_width = target_size
                        new_height = int(target_size / aspect_ratio)
                    else:
                        # Taller than wide
                        new_height = target_size
                        new_width = int(target_size * aspect_ratio)
                    
                    scaled_frame = pg.transform.scale(first_frame, (new_width, new_height))
                    previews[char_name] = scaled_frame
                    
                except Exception as e:
                    print(f"Could not load preview for {char_name}: {e}")
        
        return previews
    
    def _load_character_animation(self, char_name: str) -> Optional[List[pg.Surface]]:
        """Load animation frames for character detail display."""
        char_path = self.character_manager.get_character_path(char_name)
        if not char_path or not os.path.exists(char_path):
            return None
            
        try:
            sprite_sheet = pg.image.load(char_path).convert_alpha()
            
            # Extract down-facing animation frames (row 0)
            frame_width = sprite_sheet.get_width() // 3
            frame_height = sprite_sheet.get_height() // 4
            frames = []
            
            for frame in range(3):  # 3 frames for down animation
                x = frame * frame_width
                y = 0  # Down-facing row
                frame_surface = sprite_sheet.subsurface((x, y, frame_width, frame_height))
                
                # Scale for detail display
                detail_size = 200
                aspect_ratio = frame_width / frame_height
                
                if aspect_ratio > 1:
                    new_width = detail_size
                    new_height = int(detail_size / aspect_ratio)
                else:
                    new_height = detail_size
                    new_width = int(detail_size * aspect_ratio)
                
                scaled_frame = pg.transform.scale(frame_surface, (new_width, new_height))
                frames.append(scaled_frame)
            
            return frames
            
        except Exception as e:
            print(f"Could not load animation for {char_name}: {e}")
            return None
    
    def handle_mouse_click(self, mouse_pos: tuple):
        """Handle mouse clicks on character selection grid."""
        grid_start_y = 120
        cell_width = self.grid_width // self.columns
        cell_height = 180
        
        for i, char_name in enumerate(self.characters):
            row = i // self.columns
            col = i % self.columns
            
            # Calculate cell position
            cell_x = self.grid_start_x + col * cell_width
            cell_y = grid_start_y + row * cell_height
            
            cell_rect = pg.Rect(cell_x, cell_y, cell_width, cell_height)
            if cell_rect.collidepoint(mouse_pos):
                if self.selected_index == i:
                    # Double-click effect: select character
                    return "select"
                else:
                    # Single click: change selection
                    self.selected_index = i
                    self._on_selection_change()
                    return "navigate"
        
        return None
    
    def handle_mouse_hover(self, mouse_pos: tuple):
        """Handle mouse hover on character selection grid."""
        grid_start_y = 120
        cell_width = self.grid_width // self.columns
        cell_height = 180
        
        for i, char_name in enumerate(self.characters):
            row = i // self.columns
            col = i % self.columns
            
            # Calculate cell position
            cell_x = self.grid_start_x + col * cell_width
            cell_y = grid_start_y + row * cell_height
            
            cell_rect = pg.Rect(cell_x, cell_y, cell_width, cell_height)
            if cell_rect.collidepoint(mouse_pos):
                if self.selected_index != i:
                    # Change selection on hover
                    self.selected_index = i
                    self._on_selection_change()
                break
    
    def handle_input(self, event):
        """Handle menu input events with enhanced feedback."""
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP or event.key == pg.K_w:
                # Move up in grid
                new_row = (self.selected_index // self.columns) - 1
                if new_row >= 0:
                    col = self.selected_index % self.columns
                    new_index = new_row * self.columns + col
                    if new_index < len(self.characters):
                        self.selected_index = new_index
                        self._on_selection_change()
                return "navigate"
            elif event.key == pg.K_DOWN or event.key == pg.K_s:
                # Move down in grid
                new_row = (self.selected_index // self.columns) + 1
                if new_row < self.rows:
                    col = self.selected_index % self.columns
                    new_index = new_row * self.columns + col
                    if new_index < len(self.characters):
                        self.selected_index = new_index
                        self._on_selection_change()
                return "navigate"
            elif event.key == pg.K_LEFT or event.key == pg.K_a:
                # Move left in grid
                if self.selected_index % self.columns > 0:
                    self.selected_index -= 1
                    self._on_selection_change()
                return "navigate"
            elif event.key == pg.K_RIGHT or event.key == pg.K_d:
                # Move right in grid
                if (self.selected_index % self.columns < self.columns - 1 and 
                    self.selected_index + 1 < len(self.characters)):
                    self.selected_index += 1
                    self._on_selection_change()
                return "navigate"
            elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                # Select character and start game
                selected_char = self.characters[self.selected_index]
                self.character_manager.set_current_character(selected_char)
                return "select"
            elif event.key == pg.K_ESCAPE:
                return "back"
        
        return None
    
    def _on_selection_change(self):
        """Handle selection change events."""
        # Load new character animation
        char_name = self.characters[self.selected_index]
        self.selected_character_animation = self._load_character_animation(char_name)
        self.animation_time = 0.0
    
    def update(self, dt: float):
        """Update menu animations."""
        self.selection_animation_time += dt * 3.0  # Speed multiplier for glow effects
        self.animation_time += dt * 2.0  # Slower character animation speed
        
        # Smooth selection glow
        self.selection_glow_intensity = (math.sin(self.selection_animation_time) + 1.0) * 0.5
        
        # Hover scale effect
        target_scale = 1.1 if True else 1.0  # Could add hover detection
        self.hover_scale = self.hover_scale * 0.9 + target_scale * 0.1
    
    def get_selected_character(self) -> str:
        """Get currently selected character name."""
        if self.characters and 0 <= self.selected_index < len(self.characters):
            return self.characters[self.selected_index]
        return None
    
    def render(self, screen: pg.Surface):
        """Render the enhanced character selection menu with detail panel."""
        screen.fill(self.bg_color)
        
        # Title
        title_text = self.title_font.render("SELECT CHARACTER", True, self.title_color)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 60))
        screen.blit(title_text, title_rect)
        
        # Character grid
        self._render_character_grid(screen)
        
        # Character details panel
        self._render_character_details(screen)
        
        # Instructions
        self._render_instructions(screen)
    
    def _render_character_grid(self, screen: pg.Surface):
        """Render the character selection grid with animations."""
        grid_start_y = 120
        cell_width = self.grid_width // self.columns
        cell_height = 180
        
        for i, char_name in enumerate(self.characters):
            row = i // self.columns
            col = i % self.columns
            
            # Calculate cell position
            cell_x = self.grid_start_x + col * cell_width
            cell_y = grid_start_y + row * cell_height
            
            # Center content within cell
            center_x = cell_x + cell_width // 2
            center_y = cell_y + cell_height // 2
            
            is_selected = (i == self.selected_index)
            
            # Enhanced selection effects
            if is_selected:
                # Animated glow effect
                glow_intensity = int(self.selection_glow_intensity * 100 + 155)
                glow_color = (glow_intensity, glow_intensity, 100)
                
                # Multiple glow layers for depth
                for glow_size in [40, 30, 20]:
                    glow_rect = pg.Rect(0, 0, cell_width - 20 + glow_size, cell_height - 20 + glow_size)
                    glow_rect.center = (center_x, center_y)
                    pg.draw.rect(screen, glow_color, glow_rect, 3, border_radius=15)
                
                # Main selection border
                border_rect = pg.Rect(0, 0, cell_width - 10, cell_height - 10)
                border_rect.center = (center_x, center_y)
                pg.draw.rect(screen, self.selected_color, border_rect, 4, border_radius=10)
            
            # Character preview with hover scale
            if char_name in self.character_previews:
                preview = self.character_previews[char_name]
                
                if is_selected:
                    # Scale selected character
                    scale_factor = 1.0 + self.selection_glow_intensity * 0.1
                    scaled_w = int(preview.get_width() * scale_factor)
                    scaled_h = int(preview.get_height() * scale_factor)
                    preview = pg.transform.scale(preview, (scaled_w, scaled_h))
                
                preview_rect = preview.get_rect(center=(center_x, center_y - 20))
                screen.blit(preview, preview_rect)
            
            # Character name with enhanced styling
            display_name = self.display_names[i] if i < len(self.display_names) else char_name
            text_color = self.selected_color if is_selected else self.normal_color
            
            name_text = self.menu_font.render(display_name, True, text_color)
            name_rect = name_text.get_rect(center=(center_x, center_y + 70))
            
            # Text shadow for selected character
            if is_selected:
                shadow_text = self.menu_font.render(display_name, True, (50, 50, 50))
                shadow_rect = shadow_text.get_rect(center=(center_x + 2, center_y + 72))
                screen.blit(shadow_text, shadow_rect)
            
            screen.blit(name_text, name_rect)
    
    def _render_character_details(self, screen: pg.Surface):
        """Render character details panel with stats and animation."""
        if not self.characters or self.selected_index >= len(self.characters):
            return
        
        char_name = self.characters[self.selected_index]
        config = self.character_manager.get_character_config(char_name)
        
        if not config:
            return
        
        # Detail panel background
        panel_rect = pg.Rect(self.detail_start_x, 120, self.detail_width, self.screen_height - 240)
        pg.draw.rect(screen, self.panel_color, panel_rect, border_radius=15)
        pg.draw.rect(screen, self.panel_border_color, panel_rect, 3, border_radius=15)
        
        y_offset = 140
        
        # Character animation
        if self.selected_character_animation:
            frame_index = int(self.animation_time / 0.3) % len(self.selected_character_animation)
            char_frame = self.selected_character_animation[frame_index]
            
            char_rect = char_frame.get_rect(center=(self.detail_start_x + self.detail_width // 2, y_offset + 100))
            screen.blit(char_frame, char_rect)
        
        y_offset += 220
        
        # Character info
        name_text = self.detail_font.render(config.display_name, True, self.title_color)
        name_rect = name_text.get_rect(center=(self.detail_start_x + self.detail_width // 2, y_offset))
        screen.blit(name_text, name_rect)
        
        y_offset += 40
        
        weapon_text = self.stat_font.render(f"Weapon: {config.weapon_name}", True, self.normal_color)
        weapon_rect = weapon_text.get_rect(center=(self.detail_start_x + self.detail_width // 2, y_offset))
        screen.blit(weapon_text, weapon_rect)
        
        y_offset += 25
        
        type_text = self.stat_font.render(f"Type: {config.weapon_type}", True, self.normal_color)
        type_rect = type_text.get_rect(center=(self.detail_start_x + self.detail_width // 2, y_offset))
        screen.blit(type_text, type_rect)
        
        y_offset += 50
        
        # Stat bars
        # Get weapon damage from weapon system
        from src.weapons.weapon_manager import weapon_manager
        weapon_damage = weapon_manager.get_damage(config.weapon_type) if weapon_manager.get_damage(config.weapon_type) else 25
        
        stats = [
            ("WPN DMG", weapon_damage, 300),  # Set max to 300 for proper scaling
            ("SPD", config.stats.speed, 300), # Set max to 300 for proper scaling
            ("HP", config.stats.hp, 300),     # Set max to 300 for proper scaling  
            ("BURST MULT", config.stats.burst_multiplier, 20) # Set max to 20 for multiplier scaling
        ]
        
        bar_width = self.detail_width - 60
        bar_height = 20
        
        for stat_name, stat_value, max_value in stats:
            # Stat name
            stat_text = self.stat_font.render(stat_name, True, self.normal_color)
            screen.blit(stat_text, (self.detail_start_x + 30, y_offset))
            
            # Stat bar background
            bar_rect = pg.Rect(self.detail_start_x + 30, y_offset + 25, bar_width, bar_height)
            pg.draw.rect(screen, self.stat_bar_bg, bar_rect, border_radius=10)
            
            # Stat bar fill
            fill_width = int((stat_value / max_value) * bar_width)
            if fill_width > 0:
                fill_rect = pg.Rect(self.detail_start_x + 30, y_offset + 25, fill_width, bar_height)
                pg.draw.rect(screen, self.stat_bar_fill, fill_rect, border_radius=10)
            
            # Stat value text
            value_text = self.stat_font.render(str(stat_value), True, self.normal_color)
            value_rect = value_text.get_rect(center=(self.detail_start_x + self.detail_width - 30, y_offset + 35))
            screen.blit(value_text, value_rect)
            
            y_offset += 60
    
    def _render_instructions(self, screen: pg.Surface):
        """Render control instructions."""
        instructions = [
            "Arrow Keys / WASD - Navigate",
            "ENTER / SPACE - Select Character", 
            "ESC - Back to Menu"
        ]
        
        instruction_y = self.screen_height - 100
        for i, instruction in enumerate(instructions):
            text = self.instruction_font.render(instruction, True, self.instruction_color)
            text_rect = text.get_rect(center=(self.screen_width // 2, instruction_y + i * 30))
            screen.blit(text, text_rect)
"""
Modern Multiplayer Lobby System for Kingdom-Pygame.
Features join codes, Discord integration, secure P2P networking, and polished UI.
"""

import pygame as pg
import random
import string
import threading
import time
import hashlib
import base64
import os
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
from dataclasses import dataclass
from .secure_network_manager import SecureNetworkManager, NetworkMode, ConnectionSecurity, PeerInfo, RelayServerInfo


@dataclass
class DropdownOption:
    """Dropdown menu option."""
    value: str
    display_text: str
    enabled: bool = True


class Dropdown:
    """Dropdown menu component for settings."""
    
    def __init__(self, x: int, y: int, width: int, height: int, options: List[DropdownOption], 
                 selected_value: str = None, font: pg.font.Font = None):
        self.rect = pg.Rect(x, y, width, height)
        self.options = options
        self.selected_value = selected_value or (options[0].value if options else None)
        self.font = font or pg.font.Font(None, 24)
        self.is_open = False
        self.dropdown_rect = None
        self.option_rects = []
        self.hover_index = -1
        
        # Colors
        self.bg_color = (40, 40, 50)
        self.border_color = (120, 120, 120)
        self.selected_color = (60, 60, 70)
        self.hover_color = (80, 80, 90)
        self.text_color = (255, 255, 255)
        self.arrow_color = (180, 180, 180)
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse click and return selected value if changed."""
        print(f"[DEBUG] Dropdown.handle_click called with pos={pos}, is_open={self.is_open}")
        
        # Check if clicking on main dropdown button
        if self.rect.collidepoint(pos):
            print(f"[DEBUG] Click on main button, was_open={self.is_open}")
            # Toggle dropdown open/closed state
            self.is_open = not self.is_open
            print(f"[DEBUG] Toggled to is_open={self.is_open}")
            if self.is_open:
                self._update_dropdown_rects()
            return None
        
        # If dropdown is open and clicking on an option
        if self.is_open and self.dropdown_rect and self.dropdown_rect.collidepoint(pos):
            print(f"[DEBUG] Click in expanded area")
            # Ensure option rects are up to date
            self._update_dropdown_rects()
            
            # Check which option was clicked
            for i, option_rect in enumerate(self.option_rects):
                if option_rect.collidepoint(pos):
                    if i < len(self.options) and self.options[i].enabled:
                        old_value = self.selected_value
                        self.selected_value = self.options[i].value
                        self.is_open = False
                        print(f"[DEBUG] Selected option {i}: {self.selected_value}")
                        return self.selected_value if self.selected_value != old_value else None
        
        # Click outside dropdown - close it if open
        if self.is_open:
            print(f"[DEBUG] Click outside, closing dropdown")
            self.is_open = False
        
        return None
    
    def _update_dropdown_rects(self):
        """Update dropdown and option rectangles."""
        if self.is_open:
            # Dropdown area
            dropdown_height = len(self.options) * self.rect.height
            self.dropdown_rect = pg.Rect(self.rect.x, self.rect.bottom, 
                                       self.rect.width, dropdown_height)
            
            # Option rectangles
            self.option_rects = []
            for i, option in enumerate(self.options):
                option_y = self.dropdown_rect.y + i * self.rect.height
                option_rect = pg.Rect(self.dropdown_rect.x, option_y, self.dropdown_rect.width, self.rect.height)
                self.option_rects.append(option_rect)

    def handle_hover(self, pos: Tuple[int, int]):
        """Handle mouse hover for dropdown options."""
        self.hover_index = -1
        
        if self.is_open and self.dropdown_rect and self.dropdown_rect.collidepoint(pos):
            for i, option_rect in enumerate(self.option_rects):
                if option_rect.collidepoint(pos):
                    self.hover_index = i
                    break
    
    def render(self, screen: pg.Surface):
        """Render the dropdown menu."""        
        # Main dropdown button
        pg.draw.rect(screen, self.bg_color, self.rect)
        pg.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Selected value text
        selected_option = next((opt for opt in self.options if opt.value == self.selected_value), None)
        display_text = selected_option.display_text if selected_option else self.selected_value
        
        text_surface = self.font.render(display_text, True, self.text_color)
        text_x = self.rect.x + 8
        text_y = self.rect.centery - text_surface.get_height() // 2
        screen.blit(text_surface, (text_x, text_y))
        
        # Dropdown arrow
        arrow_size = 6
        arrow_x = self.rect.right - 15
        arrow_y = self.rect.centery
        
        if self.is_open:
            # Up arrow
            arrow_points = [
                (arrow_x, arrow_y + arrow_size // 2),
                (arrow_x - arrow_size, arrow_y - arrow_size // 2),
                (arrow_x + arrow_size, arrow_y - arrow_size // 2)
            ]
        else:
            # Down arrow
            arrow_points = [
                (arrow_x, arrow_y + arrow_size // 2),
                (arrow_x - arrow_size, arrow_y - arrow_size // 2),
                (arrow_x + arrow_size, arrow_y - arrow_size // 2)
            ]
        
        pg.draw.polygon(screen, self.arrow_color, arrow_points)
        
        # Dropdown list when open
        if self.is_open:
            dropdown_height = len(self.options) * self.rect.height
            self.dropdown_rect = pg.Rect(self.rect.x, self.rect.bottom, self.rect.width, dropdown_height)
            
            # Dropdown background
            pg.draw.rect(screen, self.bg_color, self.dropdown_rect)
            pg.draw.rect(screen, self.border_color, self.dropdown_rect, 2)
            
            # Options
            self.option_rects = []
            for i, option in enumerate(self.options):
                option_y = self.dropdown_rect.y + i * self.rect.height
                option_rect = pg.Rect(self.dropdown_rect.x, option_y, self.dropdown_rect.width, self.rect.height)
                self.option_rects.append(option_rect)
                
                # Option background
                if i == self.hover_index:
                    pg.draw.rect(screen, self.hover_color, option_rect)
                elif option.value == self.selected_value:
                    pg.draw.rect(screen, self.selected_color, option_rect)
                
                # Option text
                text_color = self.text_color if option.enabled else (100, 100, 100)
                option_text = self.font.render(option.display_text, True, text_color)
                option_text_x = option_rect.x + 8
                option_text_y = option_rect.centery - option_text.get_height() // 2
                screen.blit(option_text, (option_text_x, option_text_y))
        else:
            self.dropdown_rect = None
            self.option_rects = []


class LobbyTab(Enum):
    """Lobby interface tabs."""
    CREATE = "create"
    JOIN = "join"
    SETTINGS = "settings"


class ConnectionMethod(Enum):
    """Methods for connecting to lobbies."""
    JOIN_CODE = "join_code"
    DISCORD_INVITE = "discord_invite"
    RELAY_SERVER = "relay_server"


@dataclass
class LobbyCode:
    """Lobby join code information."""
    code: str
    display_code: str  # Human-friendly format like "FIRE-WOLF-2024"
    host_id: str
    created_time: float
    expires_time: float
    max_players: int
    game_mode: str
    is_private: bool = False
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_time
    
    def format_for_display(self) -> str:
        """Format code for easy sharing (XXXX-XXXX-XXXX)."""
        if len(self.display_code) >= 12:
            return f"{self.display_code[:4]}-{self.display_code[4:8]}-{self.display_code[8:12]}"
        return self.display_code
    
    def format_for_discord(self) -> str:
        """Format code for Discord sharing."""
        return f"🎮 **Kingdom Cleanup Lobby**\\n🔹 Code: `{self.format_for_display()}`\\n🔹 Mode: {self.game_mode}\\n🔹 Players: {self.max_players} max"


@dataclass 
class PlayerProfile:
    """Extended player information."""
    player_id: str
    display_name: str
    character: str
    ready: bool = False
    is_host: bool = False
    connection_quality: str = "Good"  # Good, Fair, Poor
    ping_ms: int = 0
    avatar_color: Tuple[int, int, int] = (100, 150, 255)
    level: int = 1
    preferred_weapon: str = "Assault Rifle"


class ModernMultiplayerLobby:
    """Modern multiplayer lobby with advanced features."""
    
    def __init__(self, screen_width: int, screen_height: int, character_manager=None, audio_manager=None, enhanced_menu=None):
        self.screen_width = screen_width  
        self.screen_height = screen_height
        self.character_manager = character_manager
        self.audio_manager = audio_manager
        self.enhanced_menu = enhanced_menu  # Store reference for background rendering
        
        # Initialize fonts to match main menu
        self.title_font = pg.font.Font(None, 72)
        self.tab_font = pg.font.Font(None, 40)
        self.menu_font = pg.font.Font(None, 48)  # Fixed to match main menu (was 36)
        self.small_font = pg.font.Font(None, 28)
        self.code_font = pg.font.Font(None, 48)  # For lobby codes
        
        # Pixel art specific fonts - use None for crisp system font (match main menu)
        self.pixel_title_font = pg.font.Font(None, 96)  # Perfect pixel size
        self.pixel_subtitle_font = pg.font.Font(None, 40)  # Complementary pixel size
        
        # Enhanced color scheme for better visual appeal and readability
        self.primary_color = (255, 255, 255)      # Main menu primary_color
        self.secondary_color = (180, 180, 180)    # Main menu secondary_color  
        self.accent_color = (220, 220, 220)       # Main menu accent_color
        self.text_color = (240, 240, 240)         # Main menu text_color
        self.bg_color = (20, 20, 25)              # Main menu bg_color
        self.panel_color = (40, 40, 50)           # Main menu normal button bg
        self.glow_color = (200, 200, 200)         # Main menu glow_color
        self.hover_color = (255, 255, 255)        # Main menu primary for hover
        self.border_color = (120, 120, 120)       # Main menu normal button border
        self.success_color = (100, 255, 100)      # Main menu success_color
        self.warning_color = (255, 165, 0)        # Keep warning orange
        # Add missing color definitions for consistent styling
        self.text_secondary = (180, 180, 180)     # Main menu secondary_color for dimmed text
        self.inactive_color = (120, 120, 120)     # Darker gray for inactive elements
        self.error_color = (255, 80, 80)         # Bright red
        self.text_secondary = (180, 190, 220)    # Muted blue-white
        self.inactive_color = (100, 110, 140)    # Inactive elements
        
        # Tab system
        self.current_tab = LobbyTab.CREATE
        self.tab_selection = 0
        self.tabs = [LobbyTab.CREATE, LobbyTab.JOIN, LobbyTab.SETTINGS]
        self.tab_names = {
            LobbyTab.CREATE: "CREATE LOBBY",
            LobbyTab.JOIN: "JOIN LOBBY", 
            LobbyTab.SETTINGS: "SETTINGS"
        }
        
        # Create Lobby Tab
        self.create_selection = 0
        self.create_options = ["Quick Match", "Custom Game", "Private Lobby"]
        self.lobby_name = "My Lobby"
        self.custom_lobby_code = ""  # Custom join code input
        self.max_players = 4
        self.game_mode = "Survival"
        self.lobby_privacy = "Public"  # "Public" or "Private"
        
        # Environmental and map settings
        self.environmental_effects = "None"  # "None", "Snow", "Rain", "Sakura"
        self.available_environments = ["None", "Snow", "Rain", "Sakura"]
        self.available_maps = ["Field-Large"]  # Will expand in future
        
        # Join Tab
        self.join_button_hovered = False
        self.map_selection = "Field-Large"
        self.is_private = False
        
        # Join Lobby Tab
        self.join_selection = 0
        self.join_method = ConnectionMethod.JOIN_CODE
        self.join_code_input = ""
        self.found_lobbies = []  # Auto-discovered local lobbies
        
        # Discord Integration
        self.discord_connected = False
        self.discord_username = ""
        self.discord_status = "Connect Discord for easy lobby sharing"
        self.friends_list = []
        
        # Settings
        self.settings_selection = 0
        self.player_name = "Player"
        
        # Character selection system
        if self.character_manager:
            # Use character manager's data when available
            self.available_characters = self.character_manager.get_character_list()
            if not self.available_characters:
                # Fallback if no characters found
                self.available_characters = [
                    "Cecil", "Commander", "Crown", "Kilo", "Marian", 
                    "Rapunzel", "Scarlet", "Sin", "Snow White", "Trony", "Wells"
                ]
        else:
            # Fallback when no character manager
            self.available_characters = [
                "Cecil", "Commander", "Crown", "Kilo", "Marian", 
                "Rapunzel", "Scarlet", "Sin", "Snow White", "Trony", "Wells"
            ]
        
        self.character_selection = 0  # Index for character selection
        self.preferred_character = self.available_characters[0] if self.available_characters else "Cecil"
        
        self.connection_method = "Auto"  # Auto, Direct, Relay
        self.show_ping = True
        self.auto_ready = False
        self.connection_status = ""  # Connection status for display
        self.use_relay_servers = False  # Network setting for relay vs direct connection
        
        # Click handling state to prevent double-clicks
        self.last_click_pos = None
        self.last_click_time = 0
        self.click_debounce_time = 0.1  # 100ms debounce
        
        # Debug hover detection
        self.debug_hover = False  # Enable to debug hover issues
        
        # Current lobby state
        self.current_lobby_code = None
        self.players_in_lobby = {}  # player_id -> PlayerProfile
        self.is_host = False
        self.is_ready = False  # Track local player's ready state
        self.network_manager = None
        self.connection_status = "Offline"
        
        # UI State
        self.editing_field = None
        self.animation_time = 0.0
        self.status_message = ""
        self.status_color = self.text_color
        self.status_timer = 0.0
        
        # Dropdown menus for lobby settings
        self.lobby_dropdowns = {}
        self.active_dropdown = None  # Track which dropdown is currently open
        
        # Player list scrolling
        self.player_scroll_offset = 0
        self.max_visible_players = 5  # Will be calculated based on available space
        
        # Initialize dropdown options
        self._init_dropdown_options()
        
        # Code generation
        self.code_words = [
            "FIRE", "WOLF", "STAR", "MOON", "WIND", "STORM", "BLADE", "NIGHT",
            "FROST", "SPARK", "DAWN", "SHADOW", "LIGHT", "STORM", "EAGLE", "TIGER",
            "DRAGON", "PHOENIX", "THUNDER", "LIGHTNING", "CRYSTAL", "SILVER", "GOLD", "IRON",
            "SNOW", "ICE", "FLAME", "OCEAN", "FOREST", "MOUNTAIN", "RIVER", "STEEL"
        ]
        
        # Lobby browser
        self.refresh_lobbies_timer = 0.0
        self.refresh_interval = 2.0  # Refresh every 2 seconds
        
        # Enhanced lobby settings using newer format
        self.lobby_settings = {
            "max_players": 4,
            "game_mode": "Survival",
            "difficulty": "Normal",
            "time_limit": "None",
            "friendly_fire": False,
            "respawn_enabled": True
        }
        
        # Game start coordination
        self.game_start_result = None  # Result to return to main.py when game should start
    
    def update(self, dt: float):
        """Update the multiplayer lobby - check for network messages."""
        # Check for incoming network messages if connected
        if self.network_manager and self.connection_status in ["Hosting", "Connected"]:
            print(f"[DEBUG] ModernMultiplayerLobby.update() called - connection_status: {self.connection_status}")
            self._process_network_messages()
        else:
            print(f"[DEBUG] ModernMultiplayerLobby.update() skipped - network_manager: {self.network_manager is not None}, connection_status: {self.connection_status}")
    
    def _process_network_messages(self):
        """Process incoming network messages for lobby updates."""
        print(f"[DEBUG] _process_network_messages() called")
        if not self.network_manager:
            print(f"[DEBUG] No network_manager available")
            return
            
        # Check for incoming messages
        if hasattr(self.network_manager, '_receive_direct_message'):
            try:
                print(f"[DEBUG] Calling _receive_direct_message...")
                message = self.network_manager._receive_direct_message(timeout=0.1)
                if message:
                    print(f"[DEBUG] Lobby received network message: {message}")
                    self._handle_network_message(message)
                else:
                    print(f"[DEBUG] No message received from _receive_direct_message")
            except Exception as e:
                print(f"Error processing network message: {e}")
        else:
            print(f"[DEBUG] Network manager doesn't have _receive_direct_message method")
    
    def _handle_network_message(self, message: dict):
        """Handle incoming network message."""
        if not message or 'type' not in message:
            return
            
        message_type = message.get('type')
        
        if message_type == 'lobby_ready_state':
            # Handle ready state updates from other players
            data = message.get('data', {})
            player_id = data.get('player_id')
            player_name = data.get('player_name', 'Unknown')
            is_ready = data.get('is_ready', False)
            
            print(f"Received ready state: {player_name} ({'ready' if is_ready else 'not ready'})")
            
            # Update the peer's ready state in network manager
            if hasattr(self.network_manager, 'peers') and player_id in self.network_manager.peers:
                self.network_manager.peers[player_id].ready = is_ready
                print(f"Updated peer {player_id} ready state to {is_ready}")
                
                # Also update in the peer list if using get_peer_list
                if hasattr(self.network_manager, 'get_peer_list'):
                    peer_list = self.network_manager.get_peer_list()
                    for peer in peer_list:
                        if peer.peer_id == player_id:
                            peer.ready = is_ready
                            print(f"Also updated peer in peer_list: {peer.display_name} ready={is_ready}")
                            break
        
        elif message_type == 'lobby_setting_change':
            # Handle lobby setting changes from host
            if not self.is_host:  # Only clients should apply host's setting changes
                print(f"[DEBUG] Client received lobby_setting_change message: {message}")
                data = message.get('data', {})
                setting_name = data.get('setting')
                setting_value = data.get('value')
                print(f"[DEBUG] Client calling _apply_lobby_setting_change with: {setting_name} = {setting_value}")
                self._apply_lobby_setting_change(setting_name, setting_value)
                print(f"[DEBUG] Client finished _apply_lobby_setting_change")
            else:
                print(f"[DEBUG] Host received lobby_setting_change message (ignoring): {message}")
        
        elif message_type == 'game_start':
            # Handle game start message from host
            if not self.is_host:  # Only clients should respond to host's game start
                print(f"[DEBUG] Client received game_start message: {message}")
                data = message.get('data', {})
                # Apply game settings and start the game
                if data:
                    self.game_mode = data.get('game_mode', self.game_mode)
                    self.map_selection = data.get('map_selection', self.map_selection)
                    self.max_players = data.get('max_players', self.max_players)
                    self.environmental_effects = data.get('environmental_effects', self.environmental_effects)
                    print(f"[DEBUG] Client updated game settings: mode={self.game_mode}, map={self.map_selection}, max_players={self.max_players}")
                # Signal to main.py that the client should start the game
                self.game_start_result = "start_game"
                print(f"[DEBUG] Client setting game_start_result = 'start_game'")
                print(f"[DEBUG] Client game_start_result is now: {self.game_start_result}")
                print("Client starting game based on host command")
            else:
                print(f"[DEBUG] Host received game_start message (ignoring): {message}")
                
    def _apply_lobby_setting_change(self, setting_name: str, value: str):
        """Apply lobby setting change received from host."""
        print(f"[DEBUG] Applying lobby setting change: {setting_name} = {value}")
        
        try:
            if setting_name == 'environment':
                self.environmental_effects = value
                print(f"[DEBUG] Updated environmental_effects to: {self.environmental_effects}")
                # Update dropdown UI
                if hasattr(self, 'lobby_dropdowns') and 'environment' in self.lobby_dropdowns:
                    self.lobby_dropdowns['environment'].selected_value = value
                    print(f"[DEBUG] Updated environment dropdown to: {value}")
                else:
                    print(f"[DEBUG] Environment dropdown not available yet")
                    
            elif setting_name == 'map':
                self.map_selection = value
                print(f"[DEBUG] Updated map_selection to: {self.map_selection}")
                # Update dropdown UI
                if hasattr(self, 'lobby_dropdowns') and 'map' in self.lobby_dropdowns:
                    self.lobby_dropdowns['map'].selected_value = value
                    print(f"[DEBUG] Updated map dropdown to: {value}")
                else:
                    print(f"[DEBUG] Map dropdown not available yet")
                    
            elif setting_name == 'privacy':
                self.lobby_privacy = value
                print(f"[DEBUG] Updated lobby_privacy to: {self.lobby_privacy}")
                # Update dropdown UI  
                if hasattr(self, 'lobby_dropdowns') and 'privacy' in self.lobby_dropdowns:
                    self.lobby_dropdowns['privacy'].selected_value = value
                    print(f"[DEBUG] Updated privacy dropdown to: {value}")
                else:
                    print(f"[DEBUG] Privacy dropdown not available yet")
                    
            elif setting_name == 'max_players':
                self.max_players = int(value)
                print(f"[DEBUG] Updated max_players to: {self.max_players}")
                # Update dropdown UI
                if hasattr(self, 'lobby_dropdowns') and 'max_players' in self.lobby_dropdowns:
                    self.lobby_dropdowns['max_players'].selected_value = value  # Keep as string for dropdown
                    print(f"[DEBUG] Updated max_players dropdown to: {value}")
                else:
                    print(f"[DEBUG] Max_players dropdown not available yet")
            else:
                print(f"[DEBUG] Unknown setting: {setting_name}")
                
            print(f"Applied setting change: {setting_name} = {value}")
            
        except Exception as e:
            print(f"[ERROR] Failed to apply lobby setting change: {e}")
            import traceback
            traceback.print_exc()
            # Update dropdown UI
            if 'max_players' in self.lobby_dropdowns:
                self.lobby_dropdowns['max_players'].selected_value = value  # Keep as string for dropdown
                print(f"[DEBUG] Updated max_players dropdown to: {value}")
        else:
            print(f"[DEBUG] Unknown setting: {setting_name}")
        print(f"Applied setting change: {setting_name} = {value}")
    
    def _format_character_name(self, character_name: str) -> str:
        """Format character name with proper capitalization and spacing."""
        if not character_name:
            return ""
        
        # Replace hyphens and underscores with spaces
        formatted = character_name.replace('-', ' ').replace('_', ' ')
        
        # Split into words and capitalize each word
        words = formatted.split()
        capitalized_words = [word.capitalize() for word in words]
        
        return ' '.join(capitalized_words)
    
    def _init_dropdown_options(self):
        """Initialize dropdown menu options."""
        # Environment options
        self.environment_options = [
            DropdownOption("None", "No Effects"),
            DropdownOption("Snow", "Snow Storm"),
            DropdownOption("Rain", "Heavy Rain"), 
            DropdownOption("Sakura", "Sakura Petals")
        ]
        
        # Map options
        self.map_options = [
            DropdownOption("Field-Large", "Large Field"),
            DropdownOption("Urban-Ruins", "Urban Ruins"),
            DropdownOption("Forest-Dense", "Dense Forest")
        ]
        
        # Privacy options
        self.privacy_options = [
            DropdownOption("Public", "Public Lobby"),
            DropdownOption("Private", "Private Lobby")
        ]
        
        # Max players options
        self.max_players_options = [
            DropdownOption("2", "2 Players"),
            DropdownOption("3", "3 Players"),
            DropdownOption("4", "4 Players"),
            DropdownOption("6", "6 Players"),
            DropdownOption("8", "8 Players")
        ]
        
        # Discord friends list (simulated for demo)
        if not hasattr(self, 'discord_friends'):
            self.discord_friends = [
                {"name": "PlayerOne", "status": "In Lobby", "game": "Kingdom Cleanup", "lobby_code": "FIRE-WOLF-2024"},
                {"name": "GameMaster", "status": "Playing", "game": "Kingdom Cleanup", "lobby_code": "STAR-MOON-5678"},
                {"name": "ProGamer", "status": "In Menu", "game": "Kingdom Cleanup", "lobby_code": None},
                {"name": "CasualPlayer", "status": "Online", "game": "Other Game", "lobby_code": None},
            ]
    
    def start_lobby_music(self):
        """Start character select music for the lobby."""
        if self.audio_manager:
            try:
                self.audio_manager.play_music("assets/sounds/music/character-select.mp3")
            except Exception as e:
                print(f"Could not play lobby music: {e}")
    
    def generate_lobby_code(self, custom_code: str = None) -> LobbyCode:
        """Generate a user-friendly lobby code or use custom code if provided."""
        if custom_code and custom_code.strip():
            # Use custom code provided by user
            display_code = custom_code.strip().upper()
            # Still create secure hash for internal use
            timestamp = str(int(time.time()))
            raw_data = f"{display_code}_{timestamp}_{random.randint(10000, 99999)}"
            code_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16].upper()
        else:
            # Generate random code
            word1 = random.choice(self.code_words)
            word2 = random.choice(self.code_words)
            number = random.randint(1000, 9999)
            display_code = f"{word1}{word2}{number}"
            
            # Create actual connection code (secure hash)
            timestamp = str(int(time.time()))
            raw_data = f"{display_code}_{timestamp}_{random.randint(10000, 99999)}"
            code_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16].upper()
        
        return LobbyCode(
            code=code_hash,
            display_code=display_code,
            host_id=self.player_name,
            created_time=time.time(),
            expires_time=time.time() + (4 * 60 * 60),  # 4 hours
            max_players=self.max_players,
            game_mode=self.game_mode,
            is_private=self.is_private
        )
    
    def handle_input(self, event) -> Optional[str]:
        """Handle input events for the modern lobby."""
        if event.type == pg.KEYDOWN:
            # Check if we're in the lobby view first
            if self.connection_status in ["Hosting", "Connected"]:
                return self._handle_lobby_input(event)
            
            # Global navigation
            if event.key == pg.K_ESCAPE:
                if self.editing_field:
                    self.editing_field = None
                    return None
                # Close dropdowns when going back to main menu
                self._close_all_dropdowns()
                return "back"
            
            elif event.key == pg.K_TAB:
                if not self.editing_field:
                    # Close dropdowns when switching tabs
                    self._close_all_dropdowns()
                    self.tab_selection = (self.tab_selection + 1) % len(self.tabs)
                    self.current_tab = self.tabs[self.tab_selection]
                    return None
            
            # Tab-specific input handling
            if self.current_tab == LobbyTab.CREATE:
                return self._handle_create_input(event)
            elif self.current_tab == LobbyTab.JOIN:
                return self._handle_join_input(event)
            elif self.current_tab == LobbyTab.SETTINGS:
                return self._handle_settings_input(event)
        
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                # Check if we're in lobby view first
                if self.connection_status in ["Hosting", "Connected"]:
                    return self._handle_lobby_mouse_click(event.pos)
                else:
                    return self._handle_mouse_click(event.pos)
        
        elif event.type == pg.MOUSEMOTION:
            self._handle_mouse_hover(event.pos)
        
        elif event.type == pg.MOUSEWHEEL:
            # Handle mouse wheel scrolling in lobby view
            if self.connection_status in ["Hosting", "Connected"]:
                self._handle_player_scroll(event.y)
        
        # Check for game start signal at the end of all event handling
        if self.game_start_result:
            result = self.game_start_result
            self.game_start_result = None  # Clear the signal
            print(f"[DEBUG] Returning game_start_result: {result}")
            return result
        
        return None
    
    def check_game_start_status(self) -> Optional[str]:
        """Check if the game should start, even without input events."""
        if self.game_start_result:
            result = self.game_start_result
            self.game_start_result = None  # Clear the signal
            print(f"[DEBUG] check_game_start_status returning: {result}")
            return result
        return None
    
    def handle_mouse_click(self, pos) -> Optional[str]:
        """Handle mouse clicks for external integration."""
        return self._handle_mouse_click(pos)
    
    def _handle_create_input(self, event) -> Optional[str]:
        """Handle input for CREATE tab."""
        if event.key == pg.K_UP:
            if not self.editing_field:
                self.create_selection = (self.create_selection - 1) % len(self.create_options)
        elif event.key == pg.K_DOWN:
            if not self.editing_field:
                self.create_selection = (self.create_selection + 1) % len(self.create_options)
        elif event.key == pg.K_RETURN:
            if self.editing_field:
                self.editing_field = None
            else:
                return self._execute_create_action()
        
        # Handle text input for editable fields
        if self.editing_field == "lobby_name":
            if event.key == pg.K_BACKSPACE:
                if self.lobby_name:
                    self.lobby_name = self.lobby_name[:-1]
            elif event.unicode.isprintable() and len(self.lobby_name) < 30:
                self.lobby_name += event.unicode
        elif self.editing_field == "custom_lobby_code":
            if event.key == pg.K_BACKSPACE:
                if self.custom_lobby_code:
                    self.custom_lobby_code = self.custom_lobby_code[:-1]
            elif event.unicode.isalnum() or event.unicode in "-_":
                if len(self.custom_lobby_code) < 20:
                    self.custom_lobby_code += event.unicode.upper()
        
        return None
    
    def _handle_join_input(self, event) -> Optional[str]:
        """Handle input for JOIN tab."""
        if event.key == pg.K_UP:
            if not self.editing_field:
                self.join_selection = max(0, self.join_selection - 1)
        elif event.key == pg.K_DOWN:
            if not self.editing_field:
                max_selection = 3 + len(self.found_lobbies)  # Method + input + refresh + found lobbies
                self.join_selection = min(max_selection - 1, self.join_selection + 1)
        elif event.key == pg.K_RETURN:
            if self.editing_field:
                self.editing_field = None
            else:
                return self._execute_join_action()
        
        # Handle text input
        if self.editing_field == "join_code":
            if event.key == pg.K_BACKSPACE:
                if self.join_code_input:
                    self.join_code_input = self.join_code_input[:-1]
            elif event.unicode.isalnum() or event.unicode in "-_":
                if len(self.join_code_input) < 20:
                    self.join_code_input += event.unicode.upper()
        
        return None
    
    def _handle_discord_input(self, event) -> Optional[str]:
        """Handle input for DISCORD tab."""
        # Discord integration handling would go here
        return None
    
    def _handle_settings_input(self, event) -> Optional[str]:
        """Handle input for SETTINGS tab."""
        if event.key == pg.K_UP:
            if not self.editing_field:
                self.settings_selection = (self.settings_selection - 1) % 7  # Updated for Discord
        elif event.key == pg.K_DOWN:
            if not self.editing_field:
                self.settings_selection = (self.settings_selection + 1) % 7
        elif event.key == pg.K_LEFT:
            if not self.editing_field and self.settings_selection == 1:  # Character selection
                self.character_selection = (self.character_selection - 1) % len(self.available_characters)
                self.preferred_character = self.available_characters[self.character_selection]
        elif event.key == pg.K_RIGHT:
            if not self.editing_field and self.settings_selection == 1:  # Character selection
                self.character_selection = (self.character_selection + 1) % len(self.available_characters)
                self.preferred_character = self.available_characters[self.character_selection]
        elif event.key == pg.K_RETURN:
            if self.editing_field:
                self.editing_field = None
            else:
                self._toggle_setting()
        
        # Handle text input for name
        if self.editing_field == "player_name":
            if event.key == pg.K_BACKSPACE:
                if self.player_name:
                    self.player_name = self.player_name[:-1]
            elif event.unicode.isprintable() and len(self.player_name) < 20:
                self.player_name += event.unicode
        
        return None
    
    def _toggle_setting(self):
        """Toggle or activate the currently selected setting."""
        settings_list = [
            "player_name",     # 0
            "character",       # 1  
            "discord",         # 2
            "connection_method",  # 3
            "show_ping",       # 4
            "auto_ready",      # 5
            "voice_chat"       # 6
        ]
        
        setting_name = settings_list[self.settings_selection]
        
        if setting_name == "player_name":
            self.editing_field = "player_name"
        elif setting_name == "character":
            # Character selection is handled by arrow keys
            pass
        elif setting_name == "discord":
            if not self.discord_connected:
                self._attempt_discord_connection()
            else:
                self._disconnect_discord()
        elif setting_name == "connection_method":
            methods = ["P2P", "Relay", "LAN"]
            current_index = methods.index(self.connection_method)
            self.connection_method = methods[(current_index + 1) % len(methods)]
        elif setting_name == "show_ping":
            self.show_ping = not self.show_ping
        elif setting_name == "auto_ready":
            self.auto_ready = not self.auto_ready
        elif setting_name == "voice_chat":
            self._set_status("Voice chat is not yet implemented", (255, 255, 0))
    
    def _attempt_discord_connection(self):
        """Attempt to connect to Discord."""
        try:
            # For now, simulate Discord connection
            # In a real implementation, this would use Discord's API
            self.discord_connected = True
            self._set_status("Connected to Discord successfully!", (0, 255, 0))
        except Exception as e:
            self._set_status(f"Failed to connect to Discord: {str(e)}", (255, 0, 0))
    
    def _disconnect_discord(self):
        """Disconnect from Discord."""
        self.discord_connected = False
        self._set_status("Disconnected from Discord", (255, 255, 0))
    
    def _share_to_discord(self):
        """Share the current lobby code to Discord."""
        if self.discord_connected and self.current_lobby_code:
            # In a real implementation, this would use Discord's API to share the message
            # For now, simulate sharing by copying to clipboard or showing a message
            share_message = f"Join my Kingdom lobby! Code: {self.current_lobby_code.format_for_display()}"
            
            try:
                # Try to copy to clipboard (this would work in a real implementation)
                import pyperclip
                pyperclip.copy(share_message)
                self._set_status("Lobby code copied to clipboard for Discord!", (0, 255, 0))
            except ImportError:
                # Fallback if pyperclip not available
                self._set_status(f"Share this: {share_message}", (0, 255, 0))
        else:
            self._set_status("No lobby to share or Discord not connected", (255, 0, 0))
    
    def _handle_mouse_click(self, pos) -> Optional[str]:
        """Handle mouse clicks across all tabs."""
        import time
        
        # Debounce duplicate clicks
        current_time = time.time()
        if (self.last_click_pos == pos and 
            current_time - self.last_click_time < self.click_debounce_time):
            return None
        
        self.last_click_pos = pos
        self.last_click_time = current_time
        
        # Check tab clicks first
        tab_clicked = self._check_tab_click(pos)
        if tab_clicked:
            return None
            
        # Handle content-specific clicks
        if self.connection_status in ["Hosting", "Connected"]:
            # In lobby mode - route to lobby-specific click handler
            return self._handle_lobby_view_click(pos)
        elif self.current_tab == LobbyTab.CREATE:
            return self._handle_create_mouse_click(pos)
        elif self.current_tab == LobbyTab.JOIN:
            return self._handle_join_mouse_click(pos)
        elif self.current_tab == LobbyTab.SETTINGS:
            return self._handle_settings_mouse_click(pos)
        
        return None
    
    def _check_tab_click(self, pos) -> bool:
        """Check if a tab was clicked using the new tab bar coordinates."""
        # Match the new bottom tab bar positioning
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)  # Match main menu positioning
        tab_spacing = 40  # Spacing between tabs like main menu buttons
        tab_width = 380   # Much wider tabs to match SOLO/LOCAL MULTIPLAYER button width (MUST MATCH RENDERING)
        tab_height = 80   # Tab height within bar
        
        # Check if we're in a lobby - different button layout
        in_lobby = (self.connection_status in ["Hosting", "Connected"])
        
        if in_lobby:
            # READY/CANCEL or START/CANCEL button layout
            # Host can START when all players are ready
            if self.is_host and self._are_all_players_ready():
                buttons = ["START", "CANCEL"]
            else:
                # Show "NOT READY" or "READY" based on current state
                ready_text = "NOT READY" if self.is_ready else "READY"
                buttons = [ready_text, "CANCEL"]
            total_width = len(buttons) * tab_width + (len(buttons) - 1) * tab_spacing
        else:
            # Normal tab layout
            buttons = [self.tab_names[tab] for tab in self.tabs]
            total_width = len(self.tabs) * tab_width + (len(self.tabs) - 1) * tab_spacing
        
        start_x = (self.screen_width - total_width) // 2
        tab_y_offset = bar_y + (bar_height - tab_height) // 2  # Center tabs in bar
        
        if in_lobby:
            # Handle READY/CANCEL button clicks
            for i, button_name in enumerate(buttons):
                tab_x = start_x + i * (tab_width + tab_spacing)
                tab_rect = pg.Rect(tab_x, tab_y_offset, tab_width, tab_height)
                
                if tab_rect.collidepoint(pos):
                    if button_name == "START":
                        print("START button clicked!")
                        # Handle game start (host only)
                        self._handle_start_game_button()
                        return True
                    elif button_name in ["READY", "NOT READY"]:
                        print(f"{button_name} button clicked!")
                        # Handle ready state toggle
                        self._handle_ready_button()
                        return True
                    elif button_name == "CANCEL":
                        print("CANCEL button clicked!")
                        # Handle cancel/leave lobby
                        self._handle_cancel_button()
                        return True
        else:
            # Handle normal tab clicks
            for i, tab in enumerate(self.tabs):
                tab_x = start_x + i * (tab_width + tab_spacing)
                tab_rect = pg.Rect(tab_x, tab_y_offset, tab_width, tab_height)
                
                if tab_rect.collidepoint(pos):
                    # Close all dropdowns when switching tabs
                    self._close_all_dropdowns()
                    self.current_tab = tab
                    self.tab_selection = i
                    return True
        
        return False
    
    def _handle_lobby_view_click(self, pos) -> Optional[str]:
        """Handle mouse clicks when in lobby view mode."""
        return self._handle_lobby_mouse_click(pos)
    
    def _handle_ready_button(self):
        """Handle the READY button click in lobby."""
        # Toggle ready state
        self.is_ready = not self.is_ready
        
        if self.is_ready:
            print("Player is ready!")
            self.status_message = "Ready! Waiting for other players..."
        else:
            print("Player is not ready!")
            self.status_message = "Not ready"
        
        self.status_timer = pg.time.get_ticks()
        
        # Sync ready state with network manager
        if self.network_manager and hasattr(self.network_manager, 'update_ready_state'):
            self.network_manager.update_ready_state(self.is_ready)
        
        # Broadcast ready state to all players (host broadcasts to clients, client sends to host)
        if self.network_manager:
            self._broadcast_ready_state_update()
    
    def _broadcast_ready_state_update(self):
        """Broadcast ready state updates to all connected clients."""
        if not self.network_manager:
            return
            
        # Create ready state update data
        ready_data = {
            "player_id": getattr(self.network_manager, 'local_peer_id', 'unknown'),
            "player_name": self.player_name,
            "is_ready": self.is_ready
        }
        
        # Send to all connected peers using the network manager's send_message
        if hasattr(self.network_manager, 'send_message'):
            # Send to all peers (target_peer=None means broadcast)
            print(f"[DEBUG] About to broadcast ready state message: {ready_data}")
            self.network_manager.send_message("lobby_ready_state", ready_data, target_peer=None)
            print(f"Broadcasted ready state: {self.player_name} is {'ready' if self.is_ready else 'not ready'}")
        else:
            print(f"[DEBUG] No send_message method available on network manager")
    
    def _are_all_players_ready(self) -> bool:
        """Check if all players in the lobby are ready."""
        connected_players = self._get_connected_players()
        
        # Only debug when something changes to avoid spam
        current_state = [(p.get('display_name'), p.get('ready', False)) for p in connected_players]
        if not hasattr(self, '_last_player_state') or self._last_player_state != current_state:
            print(f"[DEBUG] Players changed: {len(connected_players)} players")
            for i, player in enumerate(connected_players):
                print(f"[DEBUG]   {player.get('display_name')} - ready: {player.get('ready', False)}")
            self._last_player_state = current_state
        
        # Need at least 2 players to start a multiplayer game
        if len(connected_players) < 2:
            return False
            
        # Check if all players are ready
        for player in connected_players:
            if not player.get('ready', False):
                return False
                
        return True
    
    def _handle_start_game_button(self):
        """Handle the START GAME button click (host only when all players ready)."""
        if not self.is_host:
            return
            
        if not self._are_all_players_ready():
            self.status_message = "Not all players are ready!"
            self.status_timer = pg.time.get_ticks()
            return
            
        print("Starting multiplayer game...")
        self.status_message = "Starting game..."
        self.status_timer = pg.time.get_ticks()
        
        # TODO: Implement actual game start
        # This would transition to the game state with multiplayer settings
        # For now, just show a message
        self._start_multiplayer_game()
    
    def _start_multiplayer_game(self):
        """Start the multiplayer game with current lobby settings."""
        # Return the signal for main.py to handle multiplayer game start
        if self.enhanced_menu:
            # For proper multiplayer start, return to the main game loop
            # The main.py will handle setting up multiplayer networking
            print(f"Starting multiplayer game with {len(self._get_connected_players())} players")
            print(f"Game mode: {self.game_mode}")
            print(f"Map: {self.map_selection}")
            print(f"Players: {[p['display_name'] for p in self._get_connected_players()]}")
            
            # Send game start message to all clients
            if self.is_host and self.network_manager:
                game_data = {
                    'game_mode': self.game_mode,
                    'map_selection': self.map_selection,
                    'max_players': self.max_players,
                    'environmental_effects': self.environmental_effects
                }
                self.network_manager.send_message("game_start", game_data, target_peer=None)
                print("Broadcasted game start message to clients")
            
            # Return the result that main.py expects for multiplayer game start
            self.game_start_result = "start_game"
    
    def _handle_cancel_button(self):
        """Handle the CANCEL button click in lobby."""
        # Leave the lobby and return to main multiplayer menu
        print("Leaving lobby...")
        self._leave_lobby()  # Use proper lobby cleanup method
        self.current_tab = LobbyTab.CREATE  # Return to CREATE tab
        self.status_message = "Left lobby"
        self.status_timer = pg.time.get_ticks()
    
    def _draw_tab_icon(self, screen: pg.Surface, tab: str, center_x: int, center_y: int, color: Tuple[int, int, int]):
        """Draw appropriate icon for each tab like the main menu icons."""
        icon_size = 20  # Base icon size
        
        if tab == "CREATE":
            # Play/Create icon - triangle pointing right with circle
            triangle_points = [
                (center_x - icon_size//2, center_y - icon_size//2),
                (center_x + icon_size//2, center_y),
                (center_x - icon_size//2, center_y + icon_size//2)
            ]
            pg.draw.polygon(screen, color, triangle_points)
            # Outer circle
            pg.draw.circle(screen, color, (center_x, center_y), icon_size//2 + 6, 3)
            
        elif tab == "JOIN":
            # Network/Connection icon - two connected nodes
            node1_x = center_x - icon_size//3
            node2_x = center_x + icon_size//3
            
            # Draw connection line
            pg.draw.line(screen, color, (node1_x, center_y), (node2_x, center_y), 4)
            
            # Draw nodes as circles
            pg.draw.circle(screen, color, (node1_x, center_y), 8, 3)
            pg.draw.circle(screen, color, (node2_x, center_y), 8, 3)
            
            # Add additional connection lines to show network
            pg.draw.line(screen, color, (node1_x - 5, center_y - 8), (node1_x + 5, center_y + 8), 2)
            pg.draw.line(screen, color, (node2_x - 5, center_y - 8), (node2_x + 5, center_y + 8), 2)
            
        elif tab == "DISCORD":
            # Chat/Message icon - speech bubble
            bubble_rect = pg.Rect(center_x - icon_size//2, center_y - icon_size//2 - 2, icon_size, icon_size//2 + 4)
            pg.draw.rect(screen, color, bubble_rect, 3)
            
            # Speech bubble tail
            tail_points = [
                (center_x - icon_size//4, center_y + icon_size//4 - 2),
                (center_x - icon_size//3, center_y + icon_size//2 + 4),
                (center_x - icon_size//6, center_y + icon_size//4 - 2)
            ]
            pg.draw.polygon(screen, color, tail_points)
            
            # Dots inside bubble
            dot_y = center_y - icon_size//4
            for i in range(3):
                dot_x = center_x - icon_size//4 + i * (icon_size//6)
                pg.draw.circle(screen, color, (dot_x, dot_y), 2)
                
        elif tab == "SETTINGS":
            # Cog/Gear icon - similar to main menu settings
            # Draw gear teeth as lines radiating from center
            for angle in range(0, 360, 30):  # 12 teeth
                rad = pg.math.Vector2()
                rad.from_polar((icon_size//2 + 4, angle))
                start_pos = (center_x, center_y)
                end_pos = (center_x + rad.x, center_y + rad.y)
                pg.draw.line(screen, color, start_pos, end_pos, 3)
            
            # Inner circle (center of gear)
            pg.draw.circle(screen, color, (center_x, center_y), icon_size//4, 3)
            
            # Outer circle outline
            pg.draw.circle(screen, color, (center_x, center_y), icon_size//2, 2)
    
    def _handle_mouse_hover(self, pos):
        """Handle mouse hover for all elements."""
        # Debug hover detection
        if self.debug_hover:
            print(f"HOVER DEBUG: Mouse at {pos}")

        # Tab hover using new bottom coordinates - handle lobby vs normal mode
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)  # Match main menu positioning
        tab_spacing = 40  # Spacing between tabs like main menu buttons
        tab_height = 80   # Tab height within bar
        
        # Check if we're in lobby mode - different button layout and dimensions
        in_lobby = (self.connection_status in ["Hosting", "Connected"])
        
        if in_lobby:
            # READY/CANCEL/START buttons - use rendering dimensions exactly
            tab_width = 380   # Match _render_tab_bar rendering width
            # Use same button logic as click handling
            if self.is_host and self._are_all_players_ready():
                buttons = ["START", "CANCEL"]
            else:
                ready_text = "NOT READY" if self.is_ready else "READY"
                buttons = [ready_text, "CANCEL"]
            total_width = len(buttons) * tab_width + (len(buttons) - 1) * tab_spacing
            start_x = (self.screen_width - total_width) // 2
            tab_y_offset = bar_y + (bar_height - tab_height) // 2
            
            for i, button_name in enumerate(buttons):
                tab_x = start_x + i * (tab_width + tab_spacing)
                tab_rect = pg.Rect(tab_x, tab_y_offset, tab_width, tab_height)
                
                if tab_rect.collidepoint(pos):
                    self.tab_selection = i
                    if self.debug_hover:
                        print(f"HOVER DEBUG: {button_name} button (index {i}) hovered at rect {tab_rect}")
                    break
        else:
            # Normal tab mode - use original logic
            tab_width = 200   # Wider tabs to contain text better
            total_width = len(self.tabs) * tab_width + (len(self.tabs) - 1) * tab_spacing
            start_x = (self.screen_width - total_width) // 2
            tab_y_offset = bar_y + (bar_height - tab_height) // 2
            
            for i, tab in enumerate(self.tabs):
                tab_x = start_x + i * (tab_width + tab_spacing)
                tab_rect = pg.Rect(tab_x, tab_y_offset, tab_width, tab_height)
                
                if tab_rect.collidepoint(pos):
                    self.tab_selection = i
                    if self.debug_hover:
                        print(f"HOVER DEBUG: Tab {i} hovered at rect {tab_rect}")
                    break
        
        # Handle dropdown hover in lobby view and settings
        if self.connection_status in ["Hosting", "Connected"]:
            for dropdown in self.lobby_dropdowns.values():
                if dropdown:
                    dropdown.handle_hover(pos)
        elif self.current_tab == LobbyTab.SETTINGS:
            # Handle settings hover - match exact layout calculations from _render_settings_tab
            self._handle_settings_hover(pos)
            for dropdown in self.lobby_dropdowns.values():
                if dropdown:
                    dropdown.handle_hover(pos)
        
        # Handle button hover based on current tab
        if self.current_tab == LobbyTab.CREATE:
            # Handle CREATE LOBBY button hover
            if not self.current_lobby_code:
                # Calculate positioning to match _render_create_tab layout exactly
                content_y = 100  # Match rendering (no title, start higher)
                container_title_y = content_y + 40  # Container title position
                name_label_y = container_title_y + 80  # Match rendering spacing exactly
                name_input_y = name_label_y + 30  # Match rendering spacing
                code_label_y = name_input_y + 60  # Match rendering spacing  
                code_input_y = code_label_y + 30  # Match rendering spacing
                button_y = code_input_y + 100  # Match rendering spacing
                button_width = 300
                button_height = 60
                button_rect = pg.Rect((self.screen_width - button_width) // 2, button_y, button_width, button_height)
                self.create_button_hovered = button_rect.collidepoint(pos)
            else:
                self.create_button_hovered = False
                # Handle Discord share button hover if lobby is active
                if self.discord_connected and hasattr(self, 'discord_share_rect'):
                    self.discord_share_hovered = self.discord_share_rect.collidepoint(pos)
                else:
                    self.discord_share_hovered = False
                    
                # Handle SELECT CHARACTER button hover if lobby is active
                if hasattr(self, 'select_char_rect'):
                    self.select_char_hovered = self.select_char_rect.collidepoint(pos)
                else:
                    self.select_char_hovered = False
                
        elif self.current_tab == LobbyTab.JOIN:
            # Update JOIN button hover using corrected positioning - match _render_join_tab exactly
            content_y = 150
            margin = 50
            total_width = self.screen_width - (margin * 2)
            friends_width = int(total_width * 0.3)
            join_gap = 20
            join_width = total_width - friends_width - join_gap
            join_x = margin + friends_width + join_gap
            
            title_y = content_y + 60
            instruction_y = title_y + 60
            character_section_y = instruction_y + 80  # Character section in rendering
            char_selection_y = character_section_y + 40  # Character selection position
            code_section_y = char_selection_y + 80  # Match rendering exactly  
            input_y = code_section_y + 50
            button_y = input_y + 100
            button_width = 200
            button_height = 50
            join_rect = pg.Rect(join_x + (join_width - button_width) // 2, button_y, button_width, button_height)
            
            self.join_button_hovered = join_rect.collidepoint(pos)
    
    def _handle_settings_hover(self, pos):
        """Handle mouse hover for settings elements using exact same layout as rendering."""
        # Calculate layout parameters exactly matching _render_settings_tab
        margin = 80
        content_y = 120
        title_y = content_y + 50
        settings_start_y = title_y + 90
        setting_height = 100
        
        # Two-column layout - match rendering exactly
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        panel_width = self.screen_width - (margin * 2)
        col_spacing = 60
        col_width = (panel_width - col_spacing - 80) // 2
        left_col_x = margin + 40
        right_col_x = left_col_x + col_width + col_spacing
        
        settings_list = [
            ("Player Name", self.player_name, "editable"),
            ("Default Character", self.preferred_character, "character_cycle"),
            ("Discord", "Connected" if self.discord_connected else "Connect", "discord"),
            ("Connection Method", self.connection_method, "dropdown"),
            ("Show Ping", "ON" if self.show_ping else "OFF", "dropdown"),
            ("Auto Ready", "ON" if self.auto_ready else "OFF", "dropdown")
        ]
        
        # Check hover for each setting
        for i, (setting_name, setting_value, setting_type) in enumerate(settings_list):
            # Determine column and position - exact match to rendering
            col_index = i % 2
            row_index = i // 2
            
            if col_index == 0:  # Left column
                setting_x = left_col_x
            else:  # Right column
                setting_x = right_col_x
            
            setting_y_pos = settings_start_y + row_index * setting_height
            
            # Don't check if it would overflow the panel
            if setting_y_pos + setting_height > content_y + (bar_y - content_y - 20) - 20:
                break
            
            # Create hover area matching the ACTUAL UI element dimensions
            if setting_type in ["dropdown", "discord"]:
                # For dropdowns and Discord button, use actual control dimensions
                value_y = setting_y_pos + 40  # Match dropdown positioning exactly
                control_width = min(350, col_width - 10)  # Match dropdown/Discord width
                control_height = 45  # Match dropdown/Discord height
                hover_rect = pg.Rect(setting_x, value_y, control_width, control_height)
            elif setting_type == "editable":
                # For text input, use input field dimensions
                value_y = setting_y_pos + 40
                input_width = min(350, col_width - 10)
                input_height = 45
                hover_rect = pg.Rect(setting_x, value_y, input_width, input_height)
            elif setting_type == "character_cycle":
                # For character selection, use character box dimensions
                value_y = setting_y_pos + 40
                char_width = min(350, col_width - 10)
                char_height = 45
                hover_rect = pg.Rect(setting_x, value_y, char_width, char_height)
            else:
                # Default to entire setting area
                hover_rect = pg.Rect(setting_x - 10, setting_y_pos - 5, col_width + 20, setting_height - 10)
            
            if hover_rect.collidepoint(pos):
                self.settings_selection = i
                if self.debug_hover:
                    print(f"HOVER DEBUG: Settings item {i} ({setting_name}) hovered at {hover_rect}")
                break
        else:
            # No setting hovered - could reset selection but might interfere with navigation
            pass
    
    def _draw_settings_hover_debug(self, screen):
        """Draw debug rectangles to show hover detection areas."""
        import pygame as pg
        
        # Calculate layout parameters exactly matching _render_settings_tab
        margin = 80
        content_y = 120
        title_y = content_y + 50
        settings_start_y = title_y + 90
        setting_height = 100
        
        # Two-column layout - match rendering exactly
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        panel_width = self.screen_width - (margin * 2)
        col_spacing = 60
        col_width = (panel_width - col_spacing - 80) // 2
        left_col_x = margin + 40
        right_col_x = left_col_x + col_width + col_spacing
        
        settings_list = [
            ("Player Name", "editable"),
            ("Default Character", "character_cycle"),
            ("Discord", "discord"),
            ("Connection Method", "dropdown"),
            ("Show Ping", "dropdown"),
            ("Auto Ready", "dropdown")
        ]
        
        # Draw debug rectangles for each setting
        for i, (setting_name, setting_type) in enumerate(settings_list):
            # Determine column and position - exact match to rendering
            col_index = i % 2
            row_index = i // 2
            
            if col_index == 0:  # Left column
                setting_x = left_col_x
            else:  # Right column
                setting_x = right_col_x
            
            setting_y_pos = settings_start_y + row_index * setting_height
            
            # Don't check if it would overflow the panel
            if setting_y_pos + setting_height > content_y + (bar_y - content_y - 20) - 20:
                break
            
            # Create hover area matching the ACTUAL UI element dimensions (same logic as hover detection)
            if setting_type in ["dropdown", "discord"]:
                # For dropdowns and Discord button, use actual control dimensions
                value_y = setting_y_pos + 40  # Match dropdown positioning exactly
                control_width = min(350, col_width - 10)  # Match dropdown/Discord width
                control_height = 45  # Match dropdown/Discord height
                hover_rect = pg.Rect(setting_x, value_y, control_width, control_height)
            elif setting_type == "editable":
                # For text input, use input field dimensions
                value_y = setting_y_pos + 40
                input_width = min(350, col_width - 10)
                input_height = 45
                hover_rect = pg.Rect(setting_x, value_y, input_width, input_height)
            elif setting_type == "character_cycle":
                # For character selection, use character box dimensions
                value_y = setting_y_pos + 40
                char_width = min(350, col_width - 10)
                char_height = 45
                hover_rect = pg.Rect(setting_x, value_y, char_width, char_height)
            else:
                # Default to entire setting area
                hover_rect = pg.Rect(setting_x - 10, setting_y_pos - 5, col_width + 20, setting_height - 10)
            
            # Draw debug rectangle
            debug_color = (255, 0, 0) if i == self.settings_selection else (0, 255, 0)
            pg.draw.rect(screen, debug_color, hover_rect, 2)
            
            # Draw setting name for reference
            debug_font = pg.font.Font(None, 20)
            debug_text = debug_font.render(f"{i}: {setting_name}", True, (255, 255, 255))
            screen.blit(debug_text, (hover_rect.x, hover_rect.y - 20))
    
    def _handle_create_mouse_click(self, pos) -> Optional[str]:
        """Handle mouse clicks in the CREATE tab."""
        if not self.current_lobby_code:
            # Check if clicking the lobby name input field
            if hasattr(self, 'lobby_name_rect') and self.lobby_name_rect.collidepoint(pos):
                self.editing_field = "lobby_name"
                return None
            
            # Check if clicking the custom lobby code input field
            if hasattr(self, 'custom_lobby_code_rect') and self.custom_lobby_code_rect.collidepoint(pos):
                self.editing_field = "custom_lobby_code"
                return None
            
            # Check if clicking the CREATE LOBBY button - match exact rendering positioning with container
            content_y = 100  # Match rendering (no title, start higher)
            container_title_y = content_y + 40  # Match container title
            name_label_y = container_title_y + 80  # Match rendering spacing
            name_input_y = name_label_y + 30  # Match rendering spacing
            code_label_y = name_input_y + 60  # Match rendering spacing
            code_input_y = code_label_y + 30  # Match rendering spacing
            button_y = code_input_y + 100  # Match rendering spacing
            button_width = 300
            button_height = 60
            button_rect = pg.Rect((self.screen_width - button_width) // 2, button_y, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                return self._execute_create_action()
        else:
            # Check if clicking Discord share button (if lobby is active and Discord connected)
            if self.discord_connected and hasattr(self, 'discord_share_rect'):
                if self.discord_share_rect.collidepoint(pos):
                    self._share_to_discord()
            
            # Check if clicking SELECT CHARACTER button
            if hasattr(self, 'select_char_rect'):
                if self.select_char_rect.collidepoint(pos):
                    return "character_select"
        
        return None
    
    def _handle_join_mouse_click(self, pos) -> Optional[str]:
        """Handle mouse clicks in the JOIN tab using new coordinates."""
        # Check Discord friend join buttons first
        if hasattr(self, 'friend_join_rects'):
            for friend_name, (join_rect, lobby_code) in self.friend_join_rects.items():
                if join_rect.collidepoint(pos):
                    # Auto-fill the lobby code and attempt join
                    self.join_code_input = lobby_code
                    self._set_status(f"Joining {friend_name}'s lobby...", self.success_color)
                    return self._join_by_code()
        
        # Calculate right panel position for input field and button clicks
        margin = 50
        total_width = self.screen_width - (margin * 2)
        friends_width = int(total_width * 0.3)
        join_gap = 20
        join_width = total_width - friends_width - join_gap
        join_x = margin + friends_width + join_gap
        
        # Match the new join tab positioning with character selection
        content_y = 150
        title_y = content_y + 60
        instruction_y = title_y + 60
        character_section_y = instruction_y + 80
        char_selection_y = character_section_y + 40
        code_section_y = char_selection_y + 80  # Updated to account for character selection
        input_y = code_section_y + 50
        button_y = input_y + 100
        
        # Character selection click detection
        if hasattr(self, 'join_character_left_rect') and self.join_character_left_rect.collidepoint(pos):
            # Left arrow clicked - previous character
            current_index = self.available_characters.index(self.preferred_character)
            new_index = (current_index - 1) % len(self.available_characters)
            self.preferred_character = self.available_characters[new_index]
            self.character_selection = new_index
            return None
        
        if hasattr(self, 'join_character_right_rect') and self.join_character_right_rect.collidepoint(pos):
            # Right arrow clicked - next character
            current_index = self.available_characters.index(self.preferred_character)
            new_index = (current_index + 1) % len(self.available_characters)
            self.preferred_character = self.available_characters[new_index]
            self.character_selection = new_index
            return None
        
        # Input field click detection (centered in right panel)
        input_width = 400
        input_height = 50
        code_rect = pg.Rect(join_x + (join_width - input_width) // 2, input_y, input_width, input_height)
        
        if code_rect.collidepoint(pos):
            self.editing_field = "join_code"
            return None
        
        # Join button click detection (centered in right panel)
        button_width = 200
        button_height = 50
        join_button_rect = pg.Rect(join_x + (join_width - button_width) // 2, button_y, button_width, button_height)
        
        if join_button_rect.collidepoint(pos):
            return self._join_by_code()
        
        return None
    
    def _handle_discord_mouse_click(self, pos) -> Optional[str]:
        """Handle mouse clicks in the DISCORD tab."""
        button_width = 250
        button_height = 40
        button_x = (self.screen_width - button_width) // 2
        
        # Share Lobby button
        share_button_y = 300
        share_rect = pg.Rect(button_x, share_button_y, button_width, button_height)
        if share_rect.collidepoint(pos):
            if self.current_lobby_code:
                # Copy lobby info to clipboard (simulated)
                print(f"Copied lobby info to clipboard: {self.current_lobby_code}")
                self._set_status("Lobby info copied to clipboard!", self.success_color)
            else:
                self._set_status("No active lobby to share", self.warning_color)
            return None
        
        return None
    
    def _ensure_settings_dropdowns_initialized(self):
        """Ensure settings dropdowns are created with correct positions."""
        # Calculate layout parameters (match rendering)
        margin = 80
        content_y = 120
        title_y = content_y + 50
        settings_start_y = title_y + 90
        setting_height = 100
        
        # Calculate panel dimensions
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        panel_width = self.screen_width - (margin * 2)
        panel_height = bar_y - content_y - 20
        
        # Two-column layout
        col_spacing = 60
        col_width = (panel_width - col_spacing - 80) // 2
        left_col_x = margin + 40
        right_col_x = left_col_x + col_width + col_spacing
        
        settings_list = [
            ("Player Name", self.player_name, "editable"),
            ("Default Character", self.preferred_character, "character_cycle"),
            ("Discord", "Connected" if self.discord_connected else "Connect", "discord"),
            ("Connection Method", self.connection_method, "dropdown"),
            ("Show Ping", "ON" if self.show_ping else "OFF", "dropdown"),
            ("Auto Ready", "ON" if self.auto_ready else "OFF", "dropdown")
        ]
        
        # Create dropdowns for dropdown settings
        for i, (setting_name, setting_value, setting_type) in enumerate(settings_list):
            if setting_type == "dropdown":
                # Calculate position
                col_index = i % 2
                row_index = i // 2
                
                if col_index == 0:  # Left column
                    setting_x = left_col_x
                else:  # Right column
                    setting_x = right_col_x
                
                setting_y_pos = settings_start_y + row_index * setting_height
                value_y = setting_y_pos + 40
                
                dropdown_width = min(350, col_width - 10)  # Increased from 280 to 350 for better text fit
                dropdown_height = 45
                setting_key = setting_name.lower().replace(" ", "_")
                
                # Create dropdown if it doesn't exist
                if setting_key not in self.lobby_dropdowns:
                    if setting_key == "connection_method":
                        options = [DropdownOption("Auto", "Auto Connection"), 
                                 DropdownOption("Direct", "Direct Connection"), 
                                 DropdownOption("Relay", "Relay Connection")]
                        current_value = self.connection_method
                    elif setting_key == "show_ping":
                        options = [DropdownOption("ON", "Show Ping"), DropdownOption("OFF", "Hide Ping")]
                        current_value = "ON" if self.show_ping else "OFF"
                    elif setting_key == "auto_ready":
                        options = [DropdownOption("ON", "Auto Ready"), DropdownOption("OFF", "Manual Ready")]
                        current_value = "ON" if self.auto_ready else "OFF"
                    else:
                        continue
                    
                    self.lobby_dropdowns[setting_key] = Dropdown(
                        setting_x, value_y, dropdown_width, dropdown_height,
                        options, current_value, self.menu_font
                    )
                else:
                    # Only update position if it has changed
                    existing_rect = self.lobby_dropdowns[setting_key].rect
                    if existing_rect.x != setting_x or existing_rect.y != value_y:
                        self.lobby_dropdowns[setting_key].rect = pg.Rect(
                            setting_x, value_y, dropdown_width, dropdown_height
                        )

    def _handle_settings_mouse_click(self, pos) -> Optional[str]:
        """Handle mouse clicks in the SETTINGS tab using two-column layout."""
        # Ensure dropdowns are initialized before handling clicks
        self._ensure_settings_dropdowns_initialized()
        
        # Handle dropdown clicks first
        settings_dropdowns = ['connection_method', 'show_ping', 'auto_ready']
        for setting_name in settings_dropdowns:
            if setting_name in self.lobby_dropdowns and self.lobby_dropdowns[setting_name]:
                dropdown = self.lobby_dropdowns[setting_name]
                result = dropdown.handle_click(pos)
                if result is not None:
                    # Dropdown value changed
                    self._handle_dropdown_selection(setting_name, result)
                    return None
                # If dropdown was opened/closed, close other dropdowns
                if dropdown.rect.collidepoint(pos):
                    # Close other dropdowns when opening a new one
                    for other_name in settings_dropdowns:
                        if other_name != setting_name and other_name in self.lobby_dropdowns:
                            other_dropdown = self.lobby_dropdowns[other_name]
                            if other_dropdown and other_dropdown.is_open:
                                other_dropdown.is_open = False
                    return None
        
        # Calculate two-column layout for other setting interactions - match rendering
        margin = 80  # Match rendering (was 100)
        content_y = 120  # Match rendering (was 150)
        title_y = content_y + 50  # Match rendering (was 60)
        settings_start_y = title_y + 90  # Match rendering (was 80)
        setting_height = 100  # Match rendering (was 80)
        
        # Two-column layout calculations - match rendering
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        panel_width = self.screen_width - (margin * 2)
        col_spacing = 60  # Match rendering (was 40)
        col_width = (panel_width - col_spacing - 80) // 2  # Two equal columns with margins
        left_col_x = margin + 40
        right_col_x = left_col_x + col_width + col_spacing
        
        settings_list = [
            ("Player Name", self.player_name, "editable"),
            ("Default Character", self.preferred_character, "character_cycle"),
            ("Discord", "Connected" if self.discord_connected else "Connect", "discord"),
            ("Connection Method", self.connection_method, "dropdown"),
            ("Show Ping", "ON" if self.show_ping else "OFF", "dropdown"),
            ("Auto Ready", "ON" if self.auto_ready else "OFF", "dropdown")
        ]
        
        # Check setting interactions using two-column layout
        for i, (setting_name, setting_value, setting_type) in enumerate(settings_list):
            # Determine column and position (same as rendering)
            col_index = i % 2
            row_index = i // 2
            
            if col_index == 0:  # Left column
                setting_x = left_col_x
            else:  # Right column
                setting_x = right_col_x
            
            setting_y_pos = settings_start_y + row_index * setting_height
            
            # Don't process if it would overflow the panel
            if setting_y_pos + setting_height > content_y + panel_width - 20:
                break
            
            # Create click area for this setting
            setting_rect = pg.Rect(setting_x - 10, setting_y_pos - 5, col_width + 20, setting_height - 10)
            
            if setting_rect.collidepoint(pos):
                self.settings_selection = i
                
                if setting_type == "editable" and setting_name == "Player Name":
                    self.editing_field = "player_name"
                elif setting_type == "character_cycle":
                    # Open character select menu instead of cycling
                    return "character_select"
                elif setting_type == "discord":
                    if not self.discord_connected:
                        self._attempt_discord_connection()
                    else:
                        self._disconnect_discord()
                # Dropdown types are handled above
                
                return None
        
        return None
    
    def _execute_create_action(self) -> Optional[str]:
        """Execute lobby creation - delegate to _start_hosting for proper setup."""
        return self._start_hosting()
    
    def _create_quick_match(self) -> Optional[str]:
        """Create a quick match lobby."""
        self.game_mode = "Survival"
        self.max_players = 4
        self.is_private = False
        return self._start_hosting()
    
    def _create_custom_game(self) -> Optional[str]:
        """Create a custom game lobby."""
        return self._start_hosting()
    
    def _create_private_lobby(self) -> Optional[str]:
        """Create a private lobby."""
        self.is_private = True
        return self._start_hosting()
    
    def _start_hosting(self) -> Optional[str]:
        """Start hosting a lobby."""
        try:
            # Generate lobby code with custom code if provided
            custom_lobby_code = self.custom_lobby_code if self.custom_lobby_code.strip() else None
            self.current_lobby_code = self.generate_lobby_code(custom_code=custom_lobby_code)
            
            # Initialize secure network manager with relay servers and encryption
            self.network_manager = SecureNetworkManager(
                mode=NetworkMode.RELAY if self.use_relay_servers else NetworkMode.DIRECT,
                security=ConnectionSecurity.ENCRYPTED
            )
            
            # Create lobby with secure networking
            success, result = self.network_manager.create_lobby(
                lobby_name=self.player_name,
                max_players=self.max_players,
                game_mode=self.game_mode,
                is_private=self.lobby_privacy == "Private",
                lobby_code=self.current_lobby_code.display_code  # Pass the display code string
            )
            
            if success:
                # Keep the display code for UI, but store the network result
                self.network_lobby_code = result  # Store network code
                # Keep current_lobby_code as LobbyCode object for UI display
                self.is_host = True
                self.connection_status = "Hosting"
                
                # Add host to lobby
                host_profile = PlayerProfile(
                    player_id="host",
                    display_name=self.player_name,
                    character=self.preferred_character,
                    is_host=True,
                    avatar_color=(255, 215, 0)  # Gold for host
                )
                self.players_in_lobby["host"] = host_profile
                
                self._set_status(f"Lobby created! Code: {self.current_lobby_code.format_for_display()}", 
                               self.success_color)
                return "lobby_created"
            else:
                self._set_status("Failed to create lobby", self.error_color)
        except Exception as e:
            self._set_status(f"Error: {str(e)}", self.error_color)
        
        return None
    
    def _execute_join_action(self) -> Optional[str]:
        """Execute the selected join action."""
        if self.join_method == ConnectionMethod.JOIN_CODE:
            return self._join_by_code()
        else:
            return self._join_selected_lobby()
    
    def _join_by_code(self) -> Optional[str]:
        """Join lobby using a code."""
        if not self.join_code_input.strip():
            self._set_status("Please enter a lobby code", self.warning_color)
            return None
        
        lobby_code = self.join_code_input.strip().upper()
        self._set_status("Looking up lobby code...", self.warning_color)
        
        try:
            # Initialize secure network manager for code-based joining - match host mode
            self.network_manager = SecureNetworkManager(
                mode=NetworkMode.RELAY if self.use_relay_servers else NetworkMode.DIRECT,
                security=ConnectionSecurity.ENCRYPTED
            )
            
            # Join lobby by code
            success, result = self.network_manager.join_lobby_by_code(lobby_code, self.player_name)
            
            if success:
                self.connection_status = "Connected"
                self._set_status(f"Joined! {result}", self.success_color)
                return "joined_lobby"
            else:
                self._set_status(f"Failed: {result}", self.error_color)
                return None
                
        except Exception as e:
            self._set_status(f"Error: {str(e)}", self.error_color)
            return None
    
    def _attempt_join(self, host: str, port: int) -> Optional[str]:
        """Attempt to join a lobby."""
        try:
            # Initialize secure network manager
            self.network_manager = SecureNetworkManager(
                mode=NetworkMode.DIRECT,  # For IP joining
                security=ConnectionSecurity.BASIC  # Basic for direct IP
            )
            
            success, result = self.network_manager.join_lobby_direct(host, port, self.player_name)
            
            if success:
                self.connection_status = "Connected"
                self._set_status(f"Connected! {result}", self.success_color)
                return "joined_lobby"
            else:
                self._set_status(f"Failed: {result}", self.error_color)
        except Exception as e:
            self._set_status(f"Connection error: {str(e)}", self.error_color)
        
        return None
    
    def _set_status(self, message: str, color: Tuple[int, int, int]):
        """Set status message with color and timer."""
        self.status_message = message
        self.status_color = color
        self.status_timer = time.time()
    
    def update(self, dt: float):
        """Update lobby state."""
        print(f"[DEBUG] ModernMultiplayerLobby.update() called - connection_status: '{self.connection_status}', network_manager: {self.network_manager is not None}")
        self.animation_time += dt
        
        # Clear old status messages
        if time.time() - self.status_timer > 5.0:
            self.status_message = ""
        
        # Refresh lobby list periodically
        self.refresh_lobbies_timer += dt
        if self.refresh_lobbies_timer >= self.lobby_refresh_interval:
            self.refresh_lobbies_timer = 0.0
            self._refresh_lobby_list()
        
        # Update network - ALWAYS call this to process messages
        if self.network_manager:
            print(f"[DEBUG] Calling lobby's network message processing (status: '{self.connection_status}')")
            self._process_network_messages()
        else:
            print(f"[DEBUG] No network_manager available in update")
    
    def _refresh_lobby_list(self):
        """Refresh the list of available lobbies."""
        # In production, this would query relay servers for public lobbies
        # For now, simulate local discovery
        pass
    
    def render(self, screen: pg.Surface):
        """Render the modern multiplayer lobby."""
        # Use enhanced menu's background rendering for consistency
        if self.enhanced_menu:
            self.enhanced_menu._draw_clean_background(screen)
        else:
            # Fallback if no enhanced menu available
            screen.fill((20, 20, 40))
        
        # Tab bar (main menu style)
        self._render_tab_bar(screen)
        
        # Tab content
        self._render_tab_content(screen)
        
        # Status message
        if self.status_message:
            self._render_status(screen)
            
        # Render all dropdowns on top for proper z-order
        self._render_dropdowns_on_top(screen)
    
    def _render_title(self, screen: pg.Surface):
        """Draw a clean background with venetian blinds carousel effect - identical to main menu."""
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
        """Draw an infinitely scrolling vertical grid - identical to main menu."""
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
        """Draw vertical slightly angled venetian blinds with rotating background images - identical to main menu."""
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
        blinds_needed = int(math.ceil((self.screen_width + abs(angle_offset) + blind_width) / blind_width)) + 3
        
        # Start drawing from further off-screen to ensure full coverage of angled blinds
        start_blind_index = int(animation_offset / blind_width) - 1  # Start one blind earlier
        
        for i in range(blinds_needed):
            # Calculate blind position - ensure continuous coverage
            blind_x = (start_blind_index + i) * blind_width - animation_offset
            
            # Determine which background image to use for this blind (stable cycling)
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
        
        # Calculate bounding rectangle for clipping
        min_x = min(point[0] for point in points)
        max_x = max(point[0] for point in points)
        
        # Skip if completely outside screen bounds
        if max_x < 0 or min_x > self.screen_width:
            return
        
        # Create a surface for this blind slat
        slat_width = max_x - min_x + 2  # Add small buffer
        if slat_width <= 0:
            return
            
        slat_surface = pg.Surface((slat_width, self.screen_height))
        
        # Scale and position the background image to fill the slat
        if bg_image.get_width() > 0 and bg_image.get_height() > 0:
            scale_x = slat_width / bg_image.get_width()
            scale_y = self.screen_height / bg_image.get_height()
            scale = max(scale_x, scale_y)  # Cover the entire slat
            
            new_width = int(bg_image.get_width() * scale)
            new_height = int(bg_image.get_height() * scale)
            
            scaled_bg = pg.transform.scale(bg_image, (new_width, new_height))
            
            # Center the scaled image
            offset_x = (slat_width - new_width) // 2
            offset_y = (self.screen_height - new_height) // 2
            
            slat_surface.blit(scaled_bg, (offset_x, offset_y))
        
        # Apply the angled mask using polygon clipping
        mask_surface = pg.Surface((slat_width, self.screen_height), pg.SRCALPHA)
        mask_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Adjust points for local surface coordinates
        local_points = [(x - min_x, y) for x, y in points]
        pg.draw.polygon(mask_surface, (255, 255, 255, 255), local_points)
        
        # Apply mask
        slat_surface.blit(mask_surface, (0, 0), special_flags=pg.BLEND_ALPHA_SDL2)
        
        # Blit to screen at the correct position
        screen.blit(slat_surface, (min_x, 0))
    
    def _get_all_background_images(self):
        """Get all available background images - identical to main menu."""
        if not hasattr(self, '_cached_bg_images') or not self._cached_bg_images:
            import os
            bg_images = []
            
            # Check for background images in assets/images/Menu/BKG/ (same as main menu)
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
                        print(f"Loaded background image: {filename}")
                    except Exception as e:
                        print(f"Failed to load background image {filename}: {e}")
            
            # Cache the loaded images
            self._cached_bg_images = bg_images
            print(f"Cached {len(bg_images)} background images for venetian blinds carousel")
            
        return getattr(self, '_cached_bg_images', [])
    
    def _render_title(self, screen: pg.Surface):
        """Render title identical to main menu - KINGDOM CLEANUP with subtitle."""
        self._render_main_logo_clean(screen)
    
    def _render_main_logo_clean(self, screen: pg.Surface, scale: float = 1.0):
        """Render the main logo with pixel art military sci-fi styling - identical to main menu."""
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
        subtitle_shadow = self.pixel_subtitle_font.render(subtitle_text, False, (60, 60, 60))
        subtitle_shadow_rect = subtitle_shadow.get_rect(center=(self.screen_width // 2 + 2, subtitle_y + 2))
        screen.blit(subtitle_shadow, subtitle_shadow_rect)
        
        # Main subtitle
        screen.blit(subtitle_surface, subtitle_rect)
    
    def _render_tab_bar(self, screen: pg.Surface):
        """Render tab bar matching main menu bar style at bottom of screen."""
        # Main menu bar positioning and dimensions - moved to bottom
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)  # Match main menu positioning
        tab_spacing = 40  # Spacing between tabs like main menu buttons
        tab_width = 380   # Much wider tabs to match SOLO/LOCAL MULTIPLAYER button width
        tab_height = 80   # Tab height within bar
        
        # Check if we're in a lobby (hosting or connected) - show READY/CANCEL instead of normal tabs
        in_lobby = (self.connection_status in ["Hosting", "Connected"])
        
        if in_lobby:
            # Show READY/START and CANCEL buttons instead of normal tabs
            # Host can START when all players are ready
            if self.is_host and self._are_all_players_ready():
                buttons = ["START", "CANCEL"]
            else:
                # Show "NOT READY" or "READY" based on current state
                ready_text = "NOT READY" if self.is_ready else "READY"
                buttons = [ready_text, "CANCEL"]
            total_width = len(buttons) * tab_width + (len(buttons) - 1) * tab_spacing
        else:
            # Show normal tabs
            buttons = [self.tab_names[tab] for tab in self.tabs]
            total_width = len(self.tabs) * tab_width + (len(self.tabs) - 1) * tab_spacing
        
        start_x = (self.screen_width - total_width) // 2
        tab_y_offset = bar_y + (bar_height - tab_height) // 2  # Center tabs in bar
        
        # Draw main menu style bar background
        bar_surface = pg.Surface((self.screen_width, bar_height))
        bar_surface.set_alpha(200)
        bar_surface.fill((20, 20, 30))  # Main menu bar color
        screen.blit(bar_surface, (0, bar_y))
        
        # Draw main menu style bar borders - top and bottom
        pg.draw.line(screen, (100, 100, 120), (0, bar_y), (self.screen_width, bar_y), 2)
        pg.draw.line(screen, (100, 100, 120), (0, bar_y + bar_height), (self.screen_width, bar_y + bar_height), 2)
        
        if in_lobby:
            # Render READY/CANCEL buttons
            for i, button_name in enumerate(buttons):
                tab_x = start_x + i * (tab_width + tab_spacing)
                tab_rect = pg.Rect(tab_x, tab_y_offset, tab_width, tab_height)
                is_hovered = (i == self.tab_selection and self.tab_selection < 2)  # Only first 2 slots for lobby buttons
                
                # Button styling
                if button_name == "READY":
                    # Green READY button
                    if is_hovered:
                        # Hovered ready - bright green glow
                        glow_size = 8
                        glow_rect = pg.Rect(tab_x - glow_size, tab_y_offset - glow_size, 
                                           tab_width + glow_size * 2, tab_height + glow_size * 2)
                        glow_surface = pg.Surface((glow_rect.width, glow_rect.height))
                        glow_surface.set_alpha(80)
                        glow_surface.fill((0, 255, 0))  # Bright green glow
                        screen.blit(glow_surface, glow_rect.topleft)
                        
                        bg_color = (0, 120, 0)
                        border_color = (0, 255, 0)
                        text_color = (255, 255, 255)
                    else:
                        bg_color = (0, 80, 0)
                        border_color = (0, 150, 0)
                        text_color = (200, 255, 200)
                        
                elif button_name == "NOT READY":
                    # Orange NOT READY button
                    if is_hovered:
                        # Hovered not ready - bright orange glow
                        glow_size = 8
                        glow_rect = pg.Rect(tab_x - glow_size, tab_y_offset - glow_size, 
                                           tab_width + glow_size * 2, tab_height + glow_size * 2)
                        glow_surface = pg.Surface((glow_rect.width, glow_rect.height))
                        glow_surface.set_alpha(80)
                        glow_surface.fill((255, 165, 0))  # Bright orange glow
                        screen.blit(glow_surface, glow_rect.topleft)
                        
                        bg_color = (160, 80, 0)
                        border_color = (255, 165, 0)
                        text_color = (255, 255, 255)
                    else:
                        bg_color = (120, 60, 0)
                        border_color = (200, 130, 0)
                        text_color = (255, 220, 180)
                        
                elif button_name == "START":
                    # Bright blue START button (special host action)
                    if is_hovered:
                        # Hovered start - bright blue glow
                        glow_size = 8
                        glow_rect = pg.Rect(tab_x - glow_size, tab_y_offset - glow_size, 
                                           tab_width + glow_size * 2, tab_height + glow_size * 2)
                        glow_surface = pg.Surface((glow_rect.width, glow_rect.height))
                        glow_surface.set_alpha(80)
                        glow_surface.fill((0, 150, 255))  # Bright blue glow
                        screen.blit(glow_surface, glow_rect.topleft)
                        
                        bg_color = (0, 100, 200)
                        border_color = (0, 150, 255)
                        text_color = (255, 255, 255)
                    else:
                        bg_color = (0, 80, 160)
                        border_color = (0, 120, 200)
                        text_color = (200, 230, 255)
                        
                elif button_name == "CANCEL":
                    # Red CANCEL button
                    if is_hovered:
                        # Hovered cancel - bright red glow
                        glow_size = 8
                        glow_rect = pg.Rect(tab_x - glow_size, tab_y_offset - glow_size, 
                                           tab_width + glow_size * 2, tab_height + glow_size * 2)
                        glow_surface = pg.Surface((glow_rect.width, glow_rect.height))
                        glow_surface.set_alpha(80)
                        glow_surface.fill((255, 0, 0))  # Bright red glow
                        screen.blit(glow_surface, glow_rect.topleft)
                        
                        bg_color = (120, 0, 0)
                        border_color = (255, 0, 0)
                        text_color = (255, 255, 255)
                    else:
                        bg_color = (80, 0, 0)
                        border_color = (150, 0, 0)
                        text_color = (255, 200, 200)
                
                # Button background
                bg_surface = pg.Surface((tab_width, tab_height))
                bg_surface.set_alpha(255)
                bg_surface.fill(bg_color)
                screen.blit(bg_surface, (tab_x, tab_y_offset))
                
                # Button border
                pg.draw.rect(screen, border_color, tab_rect, 3)
                
                # Button text
                text_surface = self.menu_font.render(button_name, True, text_color)
                button_rect = pg.Rect(tab_x, tab_y_offset, tab_width, tab_height)
                text_rect = text_surface.get_rect(center=button_rect.center)
                screen.blit(text_surface, text_rect)
        else:
            # Render normal tabs
            for i, tab in enumerate(self.tabs):
                tab_x = start_x + i * (tab_width + tab_spacing)
                tab_rect = pg.Rect(tab_x, tab_y_offset, tab_width, tab_height)
                is_selected = (tab == self.current_tab)
                is_hovered = (i == self.tab_selection)
                
                # Main menu button styling
                if is_selected:
                    # Selected tab - bright white glow effect (like main menu)
                    glow_size = 8
                    glow_rect = pg.Rect(tab_x - glow_size, tab_y_offset - glow_size, 
                                       tab_width + glow_size * 2, tab_height + glow_size * 2)
                    glow_surface = pg.Surface((glow_rect.width, glow_rect.height))
                    glow_surface.set_alpha(80)
                    glow_surface.fill((255, 255, 255))  # Bright white glow
                    screen.blit(glow_surface, glow_rect.topleft)
                    
                    # Additional outer glow
                    outer_glow_size = 12
                    outer_glow_rect = pg.Rect(tab_x - outer_glow_size, tab_y_offset - outer_glow_size, 
                                             tab_width + outer_glow_size * 2, tab_height + outer_glow_size * 2)
                    outer_glow_surface = pg.Surface((outer_glow_rect.width, outer_glow_rect.height))
                    outer_glow_surface.set_alpha(40)
                    outer_glow_surface.fill((255, 255, 255))  # Softer outer glow
                    screen.blit(outer_glow_surface, outer_glow_rect.topleft)
                    
                    # Tab background
                    bg_surface = pg.Surface((tab_width, tab_height))
                    bg_surface.set_alpha(255)
                    bg_surface.fill((150, 150, 170))  # Brighter background like main menu
                    screen.blit(bg_surface, (tab_x, tab_y_offset))
                    
                    # Tab border
                    pg.draw.rect(screen, (255, 255, 255), tab_rect, 4)  # Bright white border
                    text_color = (255, 255, 255)
                    
                elif is_hovered:
                    # Hovered tab - subtle glow
                    hover_surface = pg.Surface((tab_width, tab_height))
                    hover_surface.set_alpha(180)
                    hover_surface.fill((60, 60, 70))  # Slightly lighter than normal
                    screen.blit(hover_surface, (tab_x, tab_y_offset))
                    
                    # Border
                    pg.draw.rect(screen, (180, 180, 180), tab_rect, 3)
                    text_color = (255, 255, 255)
                else:
                    # Normal tab - main menu normal button style
                    bg_surface = pg.Surface((tab_width, tab_height))
                    bg_surface.set_alpha(150)
                    bg_surface.fill((40, 40, 50))  # Dark background like main menu
                    screen.blit(bg_surface, (tab_x, tab_y_offset))
                    
                    # Border
                    pg.draw.rect(screen, (120, 120, 120), tab_rect, 2)  # Gray border
                    text_color = (180, 180, 180)
                
                # Draw text label to match main menu SOLO/LOCAL MULTIPLAYER buttons exactly
                tab_name = self.tab_names[tab]
                text_surface = self.menu_font.render(tab_name, True, text_color)  # Use menu_font (48px) like SOLO/LOCAL
                button_rect = pg.Rect(tab_x, tab_y_offset, tab_width, tab_height)
                text_rect = text_surface.get_rect(center=button_rect.center)  # Center text in button like main menu
                screen.blit(text_surface, text_rect)
    
    def _render_tab_content(self, screen: pg.Surface):
        """Render content for the current tab."""
        # If connected to a lobby, show the lobby view instead of normal tabs
        if self.connection_status in ["Hosting", "Connected"]:
            self._render_lobby_view(screen)
        elif self.current_tab == LobbyTab.CREATE:
            self._render_create_tab(screen)
        elif self.current_tab == LobbyTab.JOIN:
            self._render_join_tab(screen)
        elif self.current_tab == LobbyTab.SETTINGS:
            self._render_settings_tab(screen)
    
    def _render_create_tab(self, screen: pg.Surface):
        """Render CREATE LOBBY tab with left/right split layout above the tab bar."""
        # Calculate available space above tab bar with no title
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        content_y = 100  # Start higher since no title (was 300)
        available_height = bar_y - content_y - 20  # Leave 20px margin above tab bar
        
        margin = 50
        
        # Section title
        title_y = content_y - 40
        title_surface = self.menu_font.render("Create Lobby", True, self.primary_color)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, title_y))
        screen.blit(title_surface, title_rect)
        
        if self.current_lobby_code and self.is_host:
            # Active lobby - use left/right split layout
            
            # Left side: Lobby Configuration
            left_width = (self.screen_width - margin * 3) // 2  # Split screen minus margins
            left_x = margin
            left_panel_rect = pg.Rect(left_x, content_y, left_width, available_height)
            
            # Left panel background
            left_surface = pg.Surface((left_width, available_height))
            left_surface.set_alpha(150)
            left_surface.fill((40, 40, 50))
            screen.blit(left_surface, (left_x, content_y))
            pg.draw.rect(screen, (120, 120, 120), left_panel_rect, 2)
            
            # Left panel title
            left_title_y = content_y + 20
            left_title = self.menu_font.render("Lobby Settings", True, self.primary_color)
            left_title_rect = left_title.get_rect(center=(left_x + left_width // 2, left_title_y))
            screen.blit(left_title, left_title_rect)
            
            # Lobby status
            status_y = left_title_y + 40
            status_text = self.small_font.render("Status: Active", True, self.success_color)
            screen.blit(status_text, (left_x + 20, status_y))
            
            # Join code display
            code_y = status_y + 35
            code_label = self.small_font.render("Join Code:", True, self.text_color)
            screen.blit(code_label, (left_x + 20, code_y))
            
            code_display_y = code_y + 25
            code_text = self.current_lobby_code.format_for_display()
            code_surface = self.menu_font.render(code_text, True, (255, 255, 100))
            
            # Code background
            code_bg_width = left_width - 40
            code_bg_height = 35
            code_bg_rect = pg.Rect(left_x + 20, code_display_y - 5, code_bg_width, code_bg_height)
            pg.draw.rect(screen, (60, 60, 70), code_bg_rect)
            pg.draw.rect(screen, (255, 255, 100), code_bg_rect, 2)
            screen.blit(code_surface, (left_x + 25, code_display_y))
            
            # Players info
            players_y = code_display_y + 50
            player_count = len(self.players_in_lobby)
            players_text = f"Players: {player_count}/{self.max_players}"
            players_surface = self.small_font.render(players_text, True, self.text_color)
            screen.blit(players_surface, (left_x + 20, players_y))
            
            # Game mode info
            mode_y = players_y + 30
            mode_text = f"Game Mode: {self.game_mode}"
            mode_surface = self.small_font.render(mode_text, True, self.text_color)
            screen.blit(mode_surface, (left_x + 20, mode_y))
            
            # Discord share button if connected
            if self.discord_connected:
                discord_y = mode_y + 40
                discord_button_width = left_width - 40
                discord_button_height = 35
                discord_button_rect = pg.Rect(left_x + 20, discord_y, discord_button_width, discord_button_height)
                
                # Button styling
                is_hovered = getattr(self, 'discord_share_hovered', False)
                if is_hovered:
                    bg_surface = pg.Surface((discord_button_width, discord_button_height))
                    bg_surface.set_alpha(220)
                    bg_surface.fill((88, 101, 242))  # Discord color
                    screen.blit(bg_surface, discord_button_rect.topleft)
                    pg.draw.rect(screen, (114, 137, 218), discord_button_rect, 2)
                    text_color = (255, 255, 255)
                else:
                    bg_surface = pg.Surface((discord_button_width, discord_button_height))
                    bg_surface.set_alpha(180)
                    bg_surface.fill((114, 137, 218))  # Discord color
                    screen.blit(bg_surface, discord_button_rect.topleft)
                    pg.draw.rect(screen, (88, 101, 242), discord_button_rect, 2)
                    text_color = (230, 230, 230)
                
                # Button text
                discord_text = self.small_font.render("Share to Discord", True, text_color)
                discord_text_rect = discord_text.get_rect(center=discord_button_rect.center)
                screen.blit(discord_text, discord_text_rect)
                
                # Store rect for click detection
                self.discord_share_rect = discord_button_rect
            
            # Right side: Character Selection
            right_width = left_width  # Same width as left panel
            right_x = left_x + left_width + margin
            right_panel_rect = pg.Rect(right_x, content_y, right_width, available_height)
            
            # Right panel background
            right_surface = pg.Surface((right_width, available_height))
            right_surface.set_alpha(150)
            right_surface.fill((40, 40, 50))
            screen.blit(right_surface, (right_x, content_y))
            pg.draw.rect(screen, (120, 120, 120), right_panel_rect, 2)
            
            # Right panel title
            right_title_y = content_y + 20
            right_title = self.menu_font.render("Character Selection", True, self.primary_color)
            right_title_rect = right_title.get_rect(center=(right_x + right_width // 2, right_title_y))
            screen.blit(right_title, right_title_rect)
            
            # Current character label
            char_label_y = right_title_y + 40
            char_label = self.small_font.render("Selected Character:", True, self.text_color)
            screen.blit(char_label, (right_x + 20, char_label_y))
            
            # Character preview area - centered in right panel
            preview_y = char_label_y + 35
            preview_width = 120
            preview_height = 140
            preview_x = right_x + (right_width - preview_width) // 2
            preview_rect = pg.Rect(preview_x, preview_y, preview_width, preview_height)
            
            # Preview background
            bg_surface = pg.Surface((preview_width, preview_height))
            bg_surface.set_alpha(180)
            bg_surface.fill((50, 50, 60))
            screen.blit(bg_surface, preview_rect.topleft)
            pg.draw.rect(screen, (120, 120, 120), preview_rect, 2)
            
            # Character preview - Load and display actual sprite
            if self.character_manager and self.preferred_character:
                try:
                    char_path = self.character_manager.get_character_path(self.preferred_character)
                    if char_path and os.path.exists(char_path):
                        # Load sprite sheet
                        sprite_sheet = pg.image.load(char_path).convert_alpha()
                        
                        # Extract first frame (down-facing, frame 0) with proper dimensions
                        frame_width = sprite_sheet.get_width() // 3
                        frame_height = sprite_sheet.get_height() // 4
                        
                        first_frame = sprite_sheet.subsurface((0, 0, frame_width, frame_height))
                        
                        # Scale sprite to fit preview area while maintaining aspect ratio
                        max_width = preview_width - 20  # Leave margin
                        max_height = preview_height - 20
                        aspect_ratio = frame_width / frame_height
                        
                        if aspect_ratio > 1:
                            # Wider than tall
                            sprite_width = min(max_width, max_height * aspect_ratio)
                            sprite_height = sprite_width / aspect_ratio
                        else:
                            # Taller than wide
                            sprite_height = min(max_height, max_width / aspect_ratio)
                            sprite_width = sprite_height * aspect_ratio
                        
                        scaled_sprite = pg.transform.scale(first_frame, (int(sprite_width), int(sprite_height)))
                        sprite_rect = scaled_sprite.get_rect(center=(preview_rect.centerx, preview_rect.centery))
                        screen.blit(scaled_sprite, sprite_rect)
                    else:
                        # Fallback to character name if sprite not found
                        formatted_character = self._format_character_name(self.preferred_character)
                        char_name_surface = self.small_font.render(formatted_character, True, self.text_color)
                        char_name_rect = char_name_surface.get_rect(center=(preview_rect.centerx, preview_rect.centery))
                        screen.blit(char_name_surface, char_name_rect)
                except Exception as e:
                    # Error loading sprite, show character name
                    formatted_character = self._format_character_name(self.preferred_character)
                    char_name_surface = self.small_font.render(formatted_character, True, self.text_color)
                    char_name_rect = char_name_surface.get_rect(center=(preview_rect.centerx, preview_rect.centery))
                    screen.blit(char_name_surface, char_name_rect)
            else:
                # No character manager or character selected, show text placeholder
                formatted_character = self._format_character_name(self.preferred_character)
                char_name_surface = self.small_font.render(formatted_character, True, self.text_color)
                char_name_rect = char_name_surface.get_rect(center=(preview_rect.centerx, preview_rect.centery))
                screen.blit(char_name_surface, char_name_rect)
            
            # SELECT CHARACTER button - positioned below preview with margin from bottom
            select_char_button_width = right_width - 40
            select_char_button_height = 40
            select_char_y = preview_y + preview_height + 20
            select_char_button_rect = pg.Rect(right_x + 20, select_char_y, select_char_button_width, select_char_button_height)
            
            # Button styling
            is_hovered = getattr(self, 'select_char_hovered', False)
            if is_hovered:
                bg_surface = pg.Surface((select_char_button_width, select_char_button_height))
                bg_surface.set_alpha(220)
                bg_surface.fill((80, 80, 90))
                screen.blit(bg_surface, select_char_button_rect.topleft)
                pg.draw.rect(screen, (200, 200, 200), select_char_button_rect, 3)
                text_color = (255, 255, 255)
            else:
                bg_surface = pg.Surface((select_char_button_width, select_char_button_height))
                bg_surface.set_alpha(180)
                bg_surface.fill((50, 50, 60))
                screen.blit(bg_surface, select_char_button_rect.topleft)
                pg.draw.rect(screen, (120, 120, 120), select_char_button_rect, 2)
                text_color = (200, 200, 200)
            
            # Button text
            select_char_text = self.small_font.render("SELECT CHARACTER", True, text_color)
            select_char_text_rect = select_char_text.get_rect(center=select_char_button_rect.center)
            screen.blit(select_char_text, select_char_text_rect)
            
            # Store rect for click detection
            self.select_char_rect = select_char_button_rect
            
        else:
            # No lobby created yet - show lobby creation form with container box
            
            # Container panel with same styling as JOIN and SETTINGS
            container_margin = 100
            container_width = self.screen_width - (container_margin * 2)
            container_height = available_height
            container_rect = pg.Rect(container_margin, content_y, container_width, container_height)
            
            # Main menu style panel background
            panel_surface = pg.Surface((container_width, container_height))
            panel_surface.set_alpha(150)
            panel_surface.fill((40, 40, 50))  # Main menu panel color
            screen.blit(panel_surface, (container_margin, content_y))
            pg.draw.rect(screen, (120, 120, 120), container_rect, 2)  # Main menu border
            
            # Container title
            container_title_y = content_y + 40
            container_title = self.menu_font.render("Create New Lobby", True, self.primary_color)
            container_title_rect = container_title.get_rect(center=(self.screen_width // 2, container_title_y))
            screen.blit(container_title, container_title_rect)
            
            # Lobby name input field - positioned within container
            name_label_y = container_title_y + 80
            name_label = self.small_font.render("Lobby Name:", True, self.text_color)
            name_label_rect = name_label.get_rect(center=(self.screen_width // 2, name_label_y))
            screen.blit(name_label, name_label_rect)
            
            # Lobby name input field
            name_input_y = name_label_y + 30
            name_input_width = 400
            name_input_height = 40
            name_input_rect = pg.Rect((self.screen_width - name_input_width) // 2, name_input_y, name_input_width, name_input_height)
            
            # Input field styling
            is_editing_name = (self.editing_field == "lobby_name")
            if is_editing_name:
                bg_color = (60, 70, 80)
                border_color = (200, 200, 200)
                border_width = 3
            else:
                bg_color = (40, 40, 50)
                border_color = (120, 120, 120)
                border_width = 2
            
            # Input field background and border
            bg_surface = pg.Surface((name_input_width, name_input_height))
            bg_surface.set_alpha(200)
            bg_surface.fill(bg_color)
            screen.blit(bg_surface, name_input_rect.topleft)
            pg.draw.rect(screen, border_color, name_input_rect, border_width)
            
            # Display lobby name text
            display_name = self.lobby_name if self.lobby_name else "My Lobby"
            name_text = self.small_font.render(display_name, True, self.text_color)
            text_x = name_input_rect.x + 10
            text_y = name_input_rect.centery - name_text.get_height() // 2
            screen.blit(name_text, (text_x, text_y))
            
            # Cursor for editing
            if is_editing_name:
                cursor_x = text_x + name_text.get_width() + 2
                pg.draw.line(screen, self.text_color, (cursor_x, text_y), (cursor_x, text_y + name_text.get_height()), 2)
            
            # Store rect for click detection
            self.lobby_name_rect = name_input_rect
            
            # Custom Join Code input field
            code_label_y = name_input_y + 60
            code_label = self.small_font.render("Custom Join Code (optional):", True, self.text_color)
            code_label_rect = code_label.get_rect(center=(self.screen_width // 2, code_label_y))
            screen.blit(code_label, code_label_rect)
            
            # Custom code input field
            code_input_y = code_label_y + 30
            code_input_rect = pg.Rect((self.screen_width - name_input_width) // 2, code_input_y, name_input_width, name_input_height)
            
            # Input field styling for custom code
            is_editing_code = (self.editing_field == "custom_lobby_code")
            if is_editing_code:
                bg_color = (60, 70, 80)
                border_color = (200, 200, 200)
                border_width = 3
            else:
                bg_color = (40, 40, 50)
                border_color = (120, 120, 120)
                border_width = 2
            
            # Input field background and border
            bg_surface = pg.Surface((name_input_width, name_input_height))
            bg_surface.set_alpha(200)
            bg_surface.fill(bg_color)
            screen.blit(bg_surface, code_input_rect.topleft)
            pg.draw.rect(screen, border_color, code_input_rect, border_width)
            
            # Display custom code text
            display_code = self.custom_lobby_code if self.custom_lobby_code else "Leave blank for auto-generated"
            code_text_color = self.text_color if self.custom_lobby_code else (120, 120, 120)
            code_text = self.small_font.render(display_code, True, code_text_color)
            code_text_x = code_input_rect.x + 10
            code_text_y = code_input_rect.centery - code_text.get_height() // 2
            screen.blit(code_text, (code_text_x, code_text_y))
            
            # Cursor for editing
            if is_editing_code and self.custom_lobby_code:
                cursor_x = code_text_x + code_text.get_width() + 2
                pg.draw.line(screen, self.text_color, (cursor_x, code_text_y), (cursor_x, code_text_y + code_text.get_height()), 2)
            
            # Store rect for click detection
            self.custom_lobby_code_rect = code_input_rect
            
            # CREATE LOBBY button positioned below inputs
            button_y = code_input_y + 100  # Match click detection positioning
            button_width = 300
            button_height = 60
            button_rect = pg.Rect((self.screen_width - button_width) // 2, button_y, button_width, button_height)
            
            # Button styling
            is_hovered = getattr(self, 'create_button_hovered', False)
            if is_hovered:
                bg_surface = pg.Surface((button_width, button_height))
                bg_surface.set_alpha(220)
                bg_surface.fill((80, 80, 90))
                screen.blit(bg_surface, button_rect.topleft)
                pg.draw.rect(screen, (200, 200, 200), button_rect, 3)
                text_color = (255, 255, 255)
            else:
                bg_surface = pg.Surface((button_width, button_height))
                bg_surface.set_alpha(180)
                bg_surface.fill((50, 50, 60))
                screen.blit(bg_surface, button_rect.topleft)
                pg.draw.rect(screen, (120, 120, 120), button_rect, 2)
                text_color = (200, 200, 200)
            
            # Button text
            button_text = self.menu_font.render("CREATE LOBBY", True, text_color)
            button_text_rect = button_text.get_rect(center=button_rect.center)
            screen.blit(button_text, button_text_rect)
            
            # Instructions below button - centered within container
            instruction_y = button_y + 80
            instructions = [
                "Click CREATE LOBBY to generate a join code",
                "Share the code with friends to invite them",
                "Maximum 4 players per lobby"
            ]
            
            for i, instruction in enumerate(instructions):
                instruction_surface = self.small_font.render(instruction, True, self.text_secondary)
                instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, instruction_y + i * 25))
                screen.blit(instruction_surface, instruction_rect)
                instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, instruction_y + i * 25))
                screen.blit(instruction_surface, instruction_rect)
    def _render_join_tab(self, screen: pg.Surface):
        """Render JOIN LOBBY tab with Discord friends panel and main join area."""
        content_y = 150  # More vertical spacing (was 300)
        margin = 50     # Side margins
        
        # Container layout: Discord friends on left, join area on right
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        total_width = self.screen_width - (margin * 2)
        total_height = bar_y - content_y - 20  # Leave 20px margin above tab bar
        
        # Left panel: Discord friends (30% width)
        friends_width = int(total_width * 0.3)
        friends_x = margin
        friends_rect = pg.Rect(friends_x, content_y, friends_width, total_height)
        
        # Right panel: Join area (70% width with gap)
        join_gap = 20
        join_width = total_width - friends_width - join_gap
        join_x = friends_x + friends_width + join_gap
        join_rect = pg.Rect(join_x, content_y, join_width, total_height)
        
        # === LEFT PANEL: DISCORD FRIENDS ===
        # Friends panel background
        friends_surface = pg.Surface((friends_width, total_height))
        friends_surface.set_alpha(150)
        friends_surface.fill((40, 40, 50))
        screen.blit(friends_surface, (friends_x, content_y))
        pg.draw.rect(screen, (120, 120, 120), friends_rect, 2)
        
        # Friends panel title
        friends_title_y = content_y + 20
        friends_title = self.menu_font.render("Discord Friends", True, self.primary_color)
        friends_title_rect = friends_title.get_rect(center=(friends_x + friends_width // 2, friends_title_y))
        screen.blit(friends_title, friends_title_rect)
        
        # Discord connection status
        connection_y = friends_title_y + 40
        if self.discord_connected:
            status_text = "✓ Connected to Discord"
            status_color = self.success_color
        else:
            status_text = "⚠ Discord Not Connected"
            status_color = self.warning_color
        
        status_surface = self.small_font.render(status_text, True, status_color)
        status_rect = status_surface.get_rect(center=(friends_x + friends_width // 2, connection_y))
        screen.blit(status_surface, status_rect)
        
        # Friends list
        friends_list_y = connection_y + 50
        if self.discord_connected and hasattr(self, 'discord_friends'):
            # Filter friends playing the same game
            kingdom_friends = [f for f in self.discord_friends if f['game'] == 'Kingdom Cleanup']
            
            if kingdom_friends:
                list_title = self.small_font.render("Playing Kingdom Cleanup:", True, self.text_color)
                screen.blit(list_title, (friends_x + 10, friends_list_y))
                
                friend_item_y = friends_list_y + 30
                for i, friend in enumerate(kingdom_friends):
                    if friend_item_y + 60 > content_y + total_height - 20:
                        break  # Don't overflow panel
                    
                    # Friend item background
                    item_rect = pg.Rect(friends_x + 5, friend_item_y, friends_width - 10, 55)
                    
                    # Different background based on availability
                    if friend['lobby_code']:
                        # Has joinable lobby
                        bg_color = (50, 60, 40)  # Green tint
                        border_color = (100, 120, 80)
                    else:
                        # Available but no lobby
                        bg_color = (50, 50, 60)  # Blue tint
                        border_color = (100, 100, 120)
                    
                    item_surface = pg.Surface((friends_width - 10, 55))
                    item_surface.set_alpha(120)
                    item_surface.fill(bg_color)
                    screen.blit(item_surface, (friends_x + 5, friend_item_y))
                    pg.draw.rect(screen, border_color, item_rect, 1)
                    
                    # Friend name
                    name_surface = self.small_font.render(friend['name'], True, self.text_color)
                    screen.blit(name_surface, (friends_x + 10, friend_item_y + 5))
                    
                    # Friend status
                    status_text = friend['status']
                    if friend['lobby_code']:
                        status_text += f" [{friend['lobby_code'][:8]}...]"
                    
                    status_surface = self.small_font.render(status_text, True, self.text_secondary)
                    # Truncate if too long
                    if status_surface.get_width() > friends_width - 20:
                        truncated_status = status_text[:20] + "..." if len(status_text) > 20 else status_text
                        status_surface = self.small_font.render(truncated_status, True, self.text_secondary)
                    screen.blit(status_surface, (friends_x + 10, friend_item_y + 25))
                    
                    # Join button for friends with lobbies
                    if friend['lobby_code']:
                        join_btn_width = 60
                        join_btn_height = 20
                        join_btn_x = friends_x + friends_width - join_btn_width - 10
                        join_btn_y = friend_item_y + 30
                        join_btn_rect = pg.Rect(join_btn_x, join_btn_y, join_btn_width, join_btn_height)
                        
                        # Join button styling
                        pg.draw.rect(screen, (0, 150, 0), join_btn_rect)
                        pg.draw.rect(screen, (0, 200, 0), join_btn_rect, 1)
                        
                        join_text = self.small_font.render("JOIN", True, (255, 255, 255))
                        join_text_rect = join_text.get_rect(center=join_btn_rect.center)
                        screen.blit(join_text, join_text_rect)
                        
                        # Store for click detection
                        if not hasattr(self, 'friend_join_rects'):
                            self.friend_join_rects = {}
                        self.friend_join_rects[friend['name']] = (join_btn_rect, friend['lobby_code'])
                    
                    friend_item_y += 65  # Space between friend items
            else:
                no_friends_text = "No friends playing Kingdom Cleanup"
                no_friends_surface = self.small_font.render(no_friends_text, True, self.inactive_color)
                no_friends_rect = no_friends_surface.get_rect(center=(friends_x + friends_width // 2, friends_list_y + 50))
                screen.blit(no_friends_surface, no_friends_rect)
        else:
            # Discord not connected
            connect_instruction = "Connect Discord to see friends"
            instruction_surface = self.small_font.render(connect_instruction, True, self.inactive_color)
            instruction_rect = instruction_surface.get_rect(center=(friends_x + friends_width // 2, friends_list_y + 30))
            screen.blit(instruction_surface, instruction_rect)
        
        # === RIGHT PANEL: JOIN AREA ===
        # Join panel background
        join_surface = pg.Surface((join_width, total_height))
        join_surface.set_alpha(150)
        join_surface.fill((40, 40, 50))
        screen.blit(join_surface, (join_x, content_y))
        pg.draw.rect(screen, (120, 120, 120), join_rect, 2)
        
        # Section title with proper spacing
        title_y = content_y + 60  # Increased spacing
        title_surface = self.menu_font.render("Join a Lobby", True, self.primary_color)
        title_rect = title_surface.get_rect(center=(join_x + join_width // 2, title_y))
        screen.blit(title_surface, title_rect)
        
        # Add clear instructions
        instruction_y = title_y + 60  # More space between title and instructions
        instruction_text = "Enter a friend's game code to connect to their lobby"
        instruction_surface = self.small_font.render(instruction_text, True, self.text_secondary)
        instruction_rect = instruction_surface.get_rect(center=(join_x + join_width // 2, instruction_y))
        screen.blit(instruction_surface, instruction_rect)
        
        # Character selection section - add between instructions and join code
        character_section_y = instruction_y + 80
        
        # Character selection label
        char_label = self.small_font.render("Select your character:", True, self.text_color)
        char_label_rect = char_label.get_rect(center=(join_x + join_width // 2, character_section_y))
        screen.blit(char_label, char_label_rect)
        
        # Character selection box with arrows (similar to settings tab)
        char_selection_y = character_section_y + 40
        char_width = 300
        char_height = 45
        char_rect = pg.Rect(join_x + (join_width - char_width) // 2, char_selection_y, char_width, char_height)
        
        # Character display box
        bg_color = (50, 50, 60)
        pg.draw.rect(screen, bg_color, char_rect)
        pg.draw.rect(screen, (120, 120, 120), char_rect, 2)
        
        # Left arrow
        left_arrow_x = char_rect.x + 12
        left_arrow_y = char_rect.centery
        left_arrow = "◀"
        left_surface = self.menu_font.render(left_arrow, True, self.primary_color)
        left_rect = left_surface.get_rect(center=(left_arrow_x + 15, left_arrow_y))
        screen.blit(left_surface, left_rect)
        
        # Right arrow
        right_arrow_x = char_rect.right - 25
        right_arrow = "▶"
        right_surface = self.menu_font.render(right_arrow, True, self.primary_color)
        right_rect = right_surface.get_rect(center=(right_arrow_x - 15, left_arrow_y))
        screen.blit(right_surface, right_rect)
        
        # Character name (centered)
        current_character = getattr(self, 'preferred_character', 'Cecil')
        formatted_character = self._format_character_name(current_character)
        char_surface = self.menu_font.render(formatted_character, True, self.accent_color)
        char_text_rect = char_surface.get_rect(center=(char_rect.centerx, char_rect.centery))
        screen.blit(char_surface, char_text_rect)
        
        # Store character selection rectangle for click detection
        self.join_character_rect = char_rect
        self.join_character_left_rect = pg.Rect(char_rect.x, char_rect.y, 50, char_rect.height)
        self.join_character_right_rect = pg.Rect(char_rect.right - 50, char_rect.y, 50, char_rect.height)
        
        # Join code section (featured method) - positioned after character selection
        code_section_y = char_selection_y + 80  # More space for character selection
        input_width = 400
        input_height = 50
        
        # Code input label
        code_label = self.small_font.render("Enter Lobby Code:", True, self.text_color)
        label_rect = code_label.get_rect(center=(join_x + join_width // 2, code_section_y))
        screen.blit(code_label, label_rect)
        
        # Enhanced code input field with main menu styling - centered in right panel
        input_y = code_section_y + 50  # More space between section and input
        code_rect = pg.Rect(join_x + (join_width - input_width) // 2, input_y, input_width, input_height)
        is_editing_code = (self.editing_field == "join_code")
        
        # Input field background (main menu style)
        input_surface = pg.Surface((input_width, input_height))
        input_surface.set_alpha(180)
        input_surface.fill((40, 40, 50))  # Dark background
        screen.blit(input_surface, code_rect.topleft)
        
        # Input field border
        border_color = self.primary_color if is_editing_code else self.border_color
        border_width = 3 if is_editing_code else 2
        pg.draw.rect(screen, border_color, code_rect, border_width)
        
        # Format and display code with placeholder
        display_code = self.join_code_input
        if len(display_code) >= 4:
            formatted_code = f"{display_code[:4]}-{display_code[4:8]}-{display_code[8:]}"
            if len(formatted_code) > 14:
                formatted_code = formatted_code[:14]
            display_code = formatted_code
        
        placeholder_text = "XXXX-XXXX-XXXX" if not display_code else display_code
        text_color = self.text_color if display_code else self.inactive_color
        
        code_text = self.menu_font.render(placeholder_text, True, text_color)
        code_text_rect = code_text.get_rect(center=code_rect.center)
        screen.blit(code_text, code_text_rect)
        
        # Join button with main menu styling - centered in right panel
        button_y = input_y + 100  # More space before button
        button_width = 200
        button_height = 50
        join_button_rect = pg.Rect(join_x + (join_width - button_width) // 2, button_y, button_width, button_height)
        
        # Main menu button styling for join button
        if self.join_button_hovered:
            # Hovered button
            bg_surface = pg.Surface((button_width, button_height))
            bg_surface.set_alpha(180)
            bg_surface.fill((60, 60, 70))  # Slightly lighter
            screen.blit(bg_surface, join_button_rect.topleft)
            pg.draw.rect(screen, (180, 180, 180), join_button_rect, 3)
            button_text_color = (255, 255, 255)
        else:
            # Normal button
            bg_surface = pg.Surface((button_width, button_height))
            bg_surface.set_alpha(150)
            bg_surface.fill((40, 40, 50))  # Dark background
            screen.blit(bg_surface, join_button_rect.topleft)
            pg.draw.rect(screen, (120, 120, 120), join_button_rect, 2)
            button_text_color = (180, 180, 180)
        
        # Button text
        join_text = self.menu_font.render("JOIN GAME", True, button_text_color)
        join_text_rect = join_text.get_rect(center=join_button_rect.center)
        screen.blit(join_text, join_text_rect)
        
        # Status messages with proper spacing
        if hasattr(self, 'connection_status') and self.connection_status:
            status_y = button_y + 80
            status_color = self.success_color if 'success' in self.connection_status.lower() else self.error_color
            status_text = self.small_font.render(self.connection_status, True, status_color)
            status_rect = status_text.get_rect(center=(join_x + join_width // 2, status_y))
            screen.blit(status_text, status_rect)
    
    def _render_discord_tab(self, screen: pg.Surface):
        """Render DISCORD integration tab with proper spacing and main menu styling."""
        content_y = 300  # Start below the bar
        margin = 100     # Side margins
        
        # Container panel with better proportions
        panel_width = self.screen_width - (margin * 2)
        panel_height = self.screen_height - content_y - 100  # Leave space at bottom
        panel_rect = pg.Rect(margin, content_y, panel_width, panel_height)
        
        # Main menu style panel background
        panel_surface = pg.Surface((panel_width, panel_height))
        panel_surface.set_alpha(150)
        panel_surface.fill((40, 40, 50))  # Main menu panel color
        screen.blit(panel_surface, (margin, content_y))
        pg.draw.rect(screen, (120, 120, 120), panel_rect, 2)  # Main menu border
        
        # Section title with proper spacing
        title_y = content_y + 40
        title_surface = self.menu_font.render("Discord Integration", True, self.primary_color)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, title_y))
        screen.blit(title_surface, title_rect)
        
        # Add clear instructions
        instruction_y = title_y + 40
        instruction_text = "Discord: Connect with friends and share lobby codes through Discord"
        instruction_surface = self.small_font.render(instruction_text, True, self.text_secondary)
        instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, instruction_y))
        screen.blit(instruction_surface, instruction_rect)
        
        # Discord connection status
        status_y = instruction_y + 60
        status_color = self.success_color if self.discord_connected else self.warning_color
        status_text = "✓ Connected to Discord" if self.discord_connected else "⚠ Discord Not Connected"
        
        status_surface = self.menu_font.render(status_text, True, status_color)
        status_rect = status_surface.get_rect(center=(self.screen_width // 2, status_y))
        screen.blit(status_surface, status_rect)
        
        # Discord features
        features_y = status_y + 80
        features_title = self.menu_font.render("Discord Features:", True, self.text_color)
        features_rect = features_title.get_rect(center=(self.screen_width // 2, features_y))
        screen.blit(features_title, features_rect)
        
        features = [
            "🎮 Share lobby codes with friends",
            "👥 See who's online and available", 
            "📢 Rich presence in Discord status",
            "🚀 Quick join from Discord messages",
            "🎯 Auto-invite Discord friends"
        ]
        
        for i, feature in enumerate(features):
            feature_color = self.secondary_color if self.discord_connected else self.inactive_color
            feature_surface = self.small_font.render(feature, True, feature_color)
            feature_rect = feature_surface.get_rect(center=(self.screen_width // 2, features_y + 40 + i * 30))
            screen.blit(feature_surface, feature_rect)
        
        # Connect button
        button_y = features_y + 40 + len(features) * 30 + 40
        button_rect = pg.Rect(self.screen_width // 2 - 100, button_y, 200, 50)
        
        if self.discord_connected:
            pg.draw.rect(screen, (100, 50, 50), button_rect)
            pg.draw.rect(screen, self.error_color, button_rect, 2)
            button_text = "Disconnect"
            text_color = self.error_color
        else:
            pg.draw.rect(screen, (50, 100, 200), button_rect)
            pg.draw.rect(screen, (100, 150, 255), button_rect, 2)
            button_text = "Connect Discord"
            text_color = (200, 220, 255)
        
        button_surface = self.menu_font.render(button_text, True, text_color)
        button_text_rect = button_surface.get_rect(center=button_rect.center)
        screen.blit(button_surface, button_text_rect)
    
    def _render_settings_tab(self, screen: pg.Surface):
        """Render SETTINGS tab with two-column dropdown layout and better space utilization."""
        content_y = 120  # Start higher to use more space
        margin = 80      # Smaller side margins for more space
        
        # Container panel with better proportions - match lobby view sizing
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        panel_width = self.screen_width - (margin * 2)
        panel_height = bar_y - content_y - 20  # Leave 20px margin above tab bar
        panel_rect = pg.Rect(margin, content_y, panel_width, panel_height)
        
        # Main menu style panel background
        panel_surface = pg.Surface((panel_width, panel_height))
        panel_surface.set_alpha(150)
        panel_surface.fill((40, 40, 50))  # Main menu panel color
        screen.blit(panel_surface, (margin, content_y))
        pg.draw.rect(screen, (120, 120, 120), panel_rect, 2)  # Main menu border
        
        # Section title with better spacing and larger font
        title_y = content_y + 50  # Better spacing
        title_surface = self.menu_font.render("Multiplayer Settings", True, self.primary_color)  # Use menu_font (48px)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, title_y))
        screen.blit(title_surface, title_rect)
        
        # Two-column layout with better space utilization
        settings_start_y = title_y + 90  # More space after title
        setting_height = 100  # Larger height for each setting row (was 80)
        
        # Column configuration with better spacing
        col_spacing = 60  # More space between columns (was 40)
        col_width = (panel_width - col_spacing - 80) // 2  # Two equal columns with margins
        left_col_x = margin + 40
        right_col_x = left_col_x + col_width + col_spacing
        
        settings_list = [
            ("Player Name", self.player_name, "editable"),
            ("Default Character", self.preferred_character, "character_cycle"),
            ("Discord", "Connected" if self.discord_connected else "Connect", "discord"),
            ("Connection Method", self.connection_method, "dropdown"),
            ("Show Ping", "ON" if self.show_ping else "OFF", "dropdown"),
            ("Auto Ready", "ON" if self.auto_ready else "OFF", "dropdown")
        ]
        
        # Render settings in two columns like lobby settings
        for i, (setting_name, setting_value, setting_type) in enumerate(settings_list):
            # Determine column and position
            col_index = i % 2
            row_index = i // 2
            
            if col_index == 0:  # Left column
                setting_x = left_col_x
            else:  # Right column
                setting_x = right_col_x
            
            setting_y_pos = settings_start_y + row_index * setting_height
            
            # Don't draw if it would overflow the panel
            if setting_y_pos + setting_height > content_y + panel_height - 20:
                break
            
            is_selected = (i == self.settings_selection)
            
            # Setting background for better visibility (optional highlight)
            if is_selected:
                highlight_rect = pg.Rect(setting_x - 10, setting_y_pos - 5, col_width + 20, setting_height - 10)
                bg_surface = pg.Surface((col_width + 20, setting_height - 10))
                bg_surface.set_alpha(100)
                bg_surface.fill((60, 60, 70))
                screen.blit(bg_surface, highlight_rect.topleft)
                pg.draw.rect(screen, (120, 120, 120), highlight_rect, 1)
            
            # Setting label with larger font
            label_y = setting_y_pos
            name_color = self.primary_color if is_selected else self.text_color
            name_surface = self.menu_font.render(setting_name + ":", True, name_color)  # Use menu_font instead of small_font
            screen.blit(name_surface, (setting_x, label_y))
            
            # Setting value/control with more spacing below label
            value_y = label_y + 40  # More space between label and value (was 30)
            setting_key = setting_name.lower().replace(" ", "_")
            
            if setting_type == "editable" and setting_name == "Player Name":
                # Editable text field - larger
                input_width = min(350, col_width - 10)  # Wider input (was 250)
                input_height = 45  # Taller input (was 35)
                input_rect = pg.Rect(setting_x, value_y, input_width, input_height)
                
                is_editing = (self.editing_field == "player_name")
                bg_color = (60, 60, 70) if is_editing else (40, 40, 50)
                border_color = self.primary_color if is_editing else self.border_color
                border_width = 2 if is_editing else 1
                
                pg.draw.rect(screen, bg_color, input_rect)
                pg.draw.rect(screen, border_color, input_rect, border_width)
                
                # Text with larger font
                text_color = self.text_color if setting_value else self.inactive_color
                text_surface = self.menu_font.render(setting_value or "Enter name...", True, text_color)  # Use menu_font
                text_x = input_rect.x + 12  # More padding
                text_y = input_rect.centery - text_surface.get_height() // 2
                screen.blit(text_surface, (text_x, text_y))
                
                # Cursor
                if is_editing:
                    cursor_x = text_x + text_surface.get_width() + 2
                    cursor_y = input_rect.centery
                    pg.draw.line(screen, self.text_color, 
                               (cursor_x, cursor_y - 10), (cursor_x, cursor_y + 10), 2)
                
            elif setting_type == "character_cycle":
                # Character selection with larger layout
                char_width = min(350, col_width - 10)  # Increased from 300 to 350 for better text fit
                char_height = 45  # Taller character box (was 35)
                char_rect = pg.Rect(setting_x, value_y, char_width, char_height)
                
                # Character display box
                bg_color = (50, 50, 60) if is_selected else (40, 40, 50)
                pg.draw.rect(screen, bg_color, char_rect)
                pg.draw.rect(screen, (120, 120, 120), char_rect, 2)
                
                # Left arrow with larger font
                left_arrow_x = char_rect.x + 12
                left_arrow_y = char_rect.centery
                left_arrow = "◀"
                left_surface = self.menu_font.render(left_arrow, True, self.primary_color if is_selected else self.text_secondary)  # Use menu_font
                left_rect = left_surface.get_rect(center=(left_arrow_x + 15, left_arrow_y))
                screen.blit(left_surface, left_rect)
                
                # Right arrow with larger font
                right_arrow_x = char_rect.right - 25
                right_arrow = "▶"
                right_surface = self.menu_font.render(right_arrow, True, self.primary_color if is_selected else self.text_secondary)  # Use menu_font
                right_rect = right_surface.get_rect(center=(right_arrow_x - 15, left_arrow_y))
                screen.blit(right_surface, right_rect)
                
                # Character name (centered) with larger font
                formatted_character = self._format_character_name(setting_value)
                char_surface = self.menu_font.render(formatted_character, True, self.accent_color)  # Use menu_font
                char_text_rect = char_surface.get_rect(center=(char_rect.centerx, char_rect.centery))
                screen.blit(char_surface, char_text_rect)
                
            elif setting_type == "discord":
                # Discord connection status with larger button
                discord_width = min(350, col_width - 10)  # Increased from 280 to 350 for better text fit
                discord_height = 45  # Taller Discord button (was 35)
                discord_rect = pg.Rect(setting_x, value_y, discord_width, discord_height)
                
                if self.discord_connected:
                    bg_color = (0, 80, 0)  # Green
                    border_color = (0, 150, 0)
                    text_color = (200, 255, 200)
                    display_text = "✓ Connected"
                else:
                    bg_color = (80, 40, 0)  # Orange
                    border_color = (150, 100, 0)
                    text_color = (255, 200, 100)
                    display_text = "Click to Connect"
                
                pg.draw.rect(screen, bg_color, discord_rect)
                pg.draw.rect(screen, border_color, discord_rect, 2)
                
                discord_surface = self.menu_font.render(display_text, True, text_color)  # Use menu_font
                discord_text_rect = discord_surface.get_rect(center=discord_rect.center)
                screen.blit(discord_surface, discord_text_rect)
                
            elif setting_type == "dropdown":
                # Dropdown menu for this setting - always render closed state, let _render_dropdowns_on_top handle open state
                dropdown_width = min(350, col_width - 10)  # Increased from 280 to 350 for better text fit
                dropdown_height = 45  # Taller dropdown (was 35)
                
                # Ensure dropdown is initialized only once
                if setting_key not in self.lobby_dropdowns:
                    self._ensure_settings_dropdowns_initialized()
                
                # Always render closed state - _render_dropdowns_on_top will handle open state
                if setting_key in self.lobby_dropdowns:
                    dropdown = self.lobby_dropdowns[setting_key]
                    # Temporarily render as closed for base layer
                    was_open = dropdown.is_open
                    dropdown.is_open = False
                    dropdown.render(screen)
                    dropdown.is_open = was_open  # Restore open state
            
            else:
                # Regular text display
                value_color = self.primary_color if is_selected else self.text_secondary
                value_surface = self.small_font.render(str(setting_value), True, value_color)
                screen.blit(value_surface, (setting_x, value_y))
    
    def _render_lobby_view(self, screen: pg.Surface):
        """Render the active lobby view showing connected players and settings."""
        # Calculate layout with proper spacing for bottom actions and no title
        content_y = 100  # Start much higher since no title (was 300)
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        bottom_actions_height = 80  # Reserve space for bottom actions
        available_height = bar_y - content_y - bottom_actions_height  # Leave space for actions
        
        # Main lobby panel
        lobby_width = self.screen_width - 100
        lobby_x = 50
        lobby_rect = pg.Rect(lobby_x, content_y, lobby_width, available_height)
        
        # Background
        bg_surface = pg.Surface((lobby_width, available_height))
        bg_surface.set_alpha(180)
        bg_surface.fill((30, 30, 40))
        screen.blit(bg_surface, (lobby_x, content_y))
        pg.draw.rect(screen, (120, 120, 120), lobby_rect, 3)
        
        # Lobby header - title and code on same row
        header_y = content_y + 20
        
        # Lobby title
        if self.is_host:
            title_text = f"Hosting Lobby"
        else:
            title_text = f"Connected to Lobby"
            
        title_surface = self.menu_font.render(title_text, True, self.primary_color)
        screen.blit(title_surface, (lobby_x + 20, header_y))
        
        # Show lobby code on same row, right-aligned
        if self.current_lobby_code:
            if hasattr(self.current_lobby_code, 'display_code'):
                code_text = f"Code: {self.current_lobby_code.display_code}"
            else:
                code_text = f"Code: {str(self.current_lobby_code)}"
            code_surface = self.small_font.render(code_text, True, self.accent_color)
            code_width = code_surface.get_width()
            code_x = lobby_x + lobby_width - 20 - code_width  # Right-aligned
            screen.blit(code_surface, (code_x, header_y + 5))  # Slight vertical offset for alignment
        
        # Redesigned layout: smaller players section (1/3) and larger settings section (2/3)
        divider_margin = 20  # Reduced margin for divider
        players_width = (lobby_width - 80) // 3  # Players get 1/3 of space
        settings_width = (lobby_width - 80) * 2 // 3 - divider_margin  # Settings get 2/3 of space
        
        left_x = lobby_x + 20
        right_x = left_x + players_width + divider_margin
        content_start_y = header_y + 50  # Reduced spacing since code is on same row
        
        # === VISUAL DIVIDER ===
        divider_x = left_x + players_width + divider_margin // 2
        divider_top = content_start_y
        divider_bottom = content_y + available_height - 100  # More space for bottom actions
        
        # Draw vertical divider line
        pg.draw.line(screen, (80, 80, 90), (divider_x, divider_top), (divider_x, divider_bottom), 2)
        
        # Draw subtle gradient bars on either side
        for offset in [-6, 6]:
            gradient_color = (50, 50, 60, 30)  # Semi-transparent
            pg.draw.line(screen, gradient_color[:3], 
                        (divider_x + offset, divider_top), 
                        (divider_x + offset, divider_bottom), 1)
        
        # === LEFT COLUMN: PLAYERS ===
        # Add background panel for players section - using new players_width
        players_panel_rect = pg.Rect(left_x - 10, content_start_y - 10, players_width + 20, divider_bottom - content_start_y + 20)
        players_panel_surface = pg.Surface((players_panel_rect.width, players_panel_rect.height))
        players_panel_surface.set_alpha(40)
        players_panel_surface.fill((20, 30, 40))
        screen.blit(players_panel_surface, players_panel_rect.topleft)
        pg.draw.rect(screen, (60, 80, 100), players_panel_rect, 1, border_radius=5)
        
        players_title = self.menu_font.render("Players", True, self.secondary_color)
        screen.blit(players_title, (left_x, content_start_y))
        
        players_y = content_start_y + 40
        
        # Get connected players from network manager
        connected_players = self._get_connected_players()
        
        # Calculate available space for players and add scrolling if needed
        available_player_height = divider_bottom - players_y - 10
        self.max_visible_players = available_player_height // 60  # Each player slot is 60px high
        
        # Apply scrolling offset
        start_index = self.player_scroll_offset
        end_index = min(len(connected_players), start_index + self.max_visible_players)
        visible_players = connected_players[start_index:end_index]
        
        # Render visible players
        for i, player in enumerate(visible_players):
            player_y = players_y + i * 60
            
            # Player slot background - using new players_width
            slot_rect = pg.Rect(left_x, player_y, players_width - 20, 55)
            slot_surface = pg.Surface((players_width - 20, 55))
            slot_surface.set_alpha(120)
            
            if player.get('is_host', False):
                slot_surface.fill((60, 60, 0))  # Gold tint for host
                border_color = (200, 200, 0)
            else:
                slot_surface.fill((40, 40, 50))
                border_color = (100, 100, 120)
                
            screen.blit(slot_surface, (left_x, player_y))
            pg.draw.rect(screen, border_color, slot_rect, 2)
            
            # Player name - shorter text for narrower column
            name_text = player.get('display_name', 'Unknown')
            if player.get('is_host', False):
                name_text += " (Host)"
                
            name_surface = self.small_font.render(name_text, True, self.text_color)
            # Truncate if too wide
            if name_surface.get_width() > players_width - 40:
                truncated_name = name_text[:15] + "..." if len(name_text) > 15 else name_text
                name_surface = self.small_font.render(truncated_name, True, self.text_color)
            screen.blit(name_surface, (left_x + 10, player_y + 5))
            
            # Character selection - shorter text
            char_text = player.get('character', 'None')
            formatted_char_text = self._format_character_name(char_text)
            if len(formatted_char_text) > 10:
                formatted_char_text = formatted_char_text[:7] + "..."
            char_surface = self.small_font.render(formatted_char_text, True, self.text_secondary)
            screen.blit(char_surface, (left_x + 10, player_y + 25))
            
            # Ready status - compact
            ready_text = "✓" if player.get('ready', False) else "○"
            ready_color = self.success_color if player.get('ready', False) else self.warning_color
            ready_surface = self.small_font.render(ready_text, True, ready_color)
            screen.blit(ready_surface, (left_x + players_width - 30, player_y + 15))
        
        # Show scrolling indicator and scroll bar if needed
        total_slots = max(getattr(self, 'max_players', 4), len(connected_players))
        if total_slots > self.max_visible_players:
            # Scroll indicator text
            scroll_text = f"Slots: {start_index + 1}-{min(start_index + self.max_visible_players, total_slots)} of {total_slots}"
            scroll_surface = self.small_font.render(scroll_text, True, self.text_secondary)
            scroll_y = players_y + self.max_visible_players * 60 + 5
            screen.blit(scroll_surface, (left_x, scroll_y))
            
            # Scroll bar on right side of players panel
            scrollbar_x = left_x + players_width - 15
            scrollbar_y = players_y
            scrollbar_height = self.max_visible_players * 60
            scrollbar_width = 8
            
            # Scroll bar background
            scrollbar_bg_rect = pg.Rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
            pg.draw.rect(screen, (30, 30, 30), scrollbar_bg_rect)
            pg.draw.rect(screen, (60, 60, 60), scrollbar_bg_rect, 1)
            
            # Scroll bar thumb
            thumb_height = max(20, (self.max_visible_players / total_slots) * scrollbar_height)
            max_scroll_offset = total_slots - self.max_visible_players
            thumb_y = scrollbar_y + (self.player_scroll_offset / max_scroll_offset) * (scrollbar_height - thumb_height) if max_scroll_offset > 0 else scrollbar_y
            
            thumb_rect = pg.Rect(scrollbar_x + 1, int(thumb_y), scrollbar_width - 2, int(thumb_height))
            pg.draw.rect(screen, (100, 100, 100), thumb_rect)
            pg.draw.rect(screen, (150, 150, 150), thumb_rect, 1)
        
        # Add empty slots for all remaining slots up to max_players (these can be scrolled to)
        total_slots = getattr(self, 'max_players', 4)
        total_players_and_slots = max(total_slots, len(connected_players))  # Show at least max_players slots
        
        # Calculate how many empty slots we need to render in current view
        current_view_end = start_index + len(visible_players)
        empty_slots_in_view = min(total_players_and_slots - current_view_end, self.max_visible_players - len(visible_players))
        
        for i in range(max(0, empty_slots_in_view)):
            empty_slot_index = len(visible_players) + i
            player_y = players_y + empty_slot_index * 60
            
            # Don't draw empty slots if they would exceed visible area
            if player_y + 55 > divider_bottom:
                break
                
            slot_rect = pg.Rect(left_x, player_y, players_width - 20, 55)
            
            # Empty slot
            slot_surface = pg.Surface((players_width - 20, 55))
            slot_surface.set_alpha(80)
            slot_surface.fill((20, 20, 25))
            screen.blit(slot_surface, (left_x, player_y))
            pg.draw.rect(screen, (60, 60, 60), slot_rect, 1)
            
            # Show slot number for empty slots
            slot_number = current_view_end + i + 1
            empty_text = f"Slot {slot_number}"
            empty_surface = self.small_font.render(empty_text, True, self.inactive_color)
            screen.blit(empty_surface, (left_x + 10, player_y + 15))
        
        # === RIGHT COLUMN: LOBBY SETTINGS (Two-Column Layout) ===
        # Add background panel for settings section - using new settings_width
        settings_panel_rect = pg.Rect(right_x - 10, content_start_y - 10, settings_width + 20, divider_bottom - content_start_y + 20)
        settings_panel_surface = pg.Surface((settings_panel_rect.width, settings_panel_rect.height))
        settings_panel_surface.set_alpha(40)
        settings_panel_surface.fill((40, 30, 20))
        screen.blit(settings_panel_surface, settings_panel_rect.topleft)
        pg.draw.rect(screen, (100, 80, 60), settings_panel_rect, 1, border_radius=5)
        
        settings_title = self.menu_font.render("Lobby Settings", True, self.secondary_color)
        screen.blit(settings_title, (right_x, content_start_y))
        
        settings_y = content_start_y + 40
        setting_height = 60  # Increased height for better spacing (was 40)
        
        # Two-column layout for settings
        left_col_x = right_x
        right_col_x = right_x + settings_width // 2
        col_width = settings_width // 2 - 10  # Space between columns
        
        # Initialize click rects for host controls
        if not hasattr(self, 'lobby_setting_rects'):
            self.lobby_setting_rects = {}
        
        settings_data = [
            ("Game Mode", getattr(self, 'game_mode', 'Survival'), False),
            ("Map", self.map_selection, self.is_host),
            ("Environment", self.environmental_effects, self.is_host),
            ("Max Players", self.max_players, self.is_host),
            ("Privacy", self.lobby_privacy, self.is_host),
            ("Character", self.preferred_character, self.is_host)
        ]
        
        # Render settings in two columns with dropdowns
        for i, (setting_name, setting_value, interactive) in enumerate(settings_data):
            # Determine column and position
            col_index = i % 2
            row_index = i // 2
            
            if col_index == 0:  # Left column
                setting_x = left_col_x
            else:  # Right column
                setting_x = right_col_x
            
            setting_y_pos = settings_y + row_index * setting_height
            
            # Don't draw if it would overflow the panel
            if setting_y_pos + setting_height > divider_bottom - 10:
                break
            
            # Setting label
            label_text = f"{setting_name}:"
            label_surface = self.small_font.render(label_text, True, self.text_color)
            screen.blit(label_surface, (setting_x, setting_y_pos))
            
            # Setting value with dropdown or special handling
            value_y = setting_y_pos + 25
            setting_key = setting_name.lower().replace(" ", "_")
            
            if setting_name == "Character" and interactive:
                # Special CHARACTER setting - clicking opens character select
                char_rect = pg.Rect(setting_x, value_y, col_width - 10, 30)
                
                # Draw clickable character box
                if self.is_host:
                    bg_color = (60, 60, 70)
                    border_color = (120, 120, 120)
                else:
                    bg_color = (40, 40, 50)
                    border_color = (80, 80, 80)
                
                pg.draw.rect(screen, bg_color, char_rect)
                pg.draw.rect(screen, border_color, char_rect, 2)
                
                char_text = f"📝 {setting_value}"
                char_surface = self.small_font.render(char_text, True, self.primary_color if interactive else self.text_secondary)
                char_text_rect = char_surface.get_rect(center=(char_rect.centerx, char_rect.centery))
                screen.blit(char_surface, char_text_rect)
                
                # Store rect for click detection
                self.character_setting_rect = char_rect
                
            elif interactive and self.is_host and setting_key in ['environment', 'map', 'privacy', 'max_players']:
                # Use dropdown for these settings
                dropdown_width = col_width - 10
                dropdown_height = 30
                
                # Create or update dropdown
                if setting_key not in self.lobby_dropdowns:
                    # Determine options based on setting type
                    if setting_key == 'environment':
                        options = self.environment_options
                        current_value = self.environmental_effects
                    elif setting_key == 'map':
                        options = self.map_options
                        current_value = self.map_selection
                    elif setting_key == 'privacy':
                        options = self.privacy_options
                        current_value = self.lobby_privacy
                    elif setting_key == 'max_players':
                        options = self.max_players_options
                        current_value = str(self.max_players)
                    else:
                        options = []
                        current_value = ""
                    
                    # Create dropdown
                    self.lobby_dropdowns[setting_key] = Dropdown(
                        setting_x, value_y, dropdown_width, dropdown_height,
                        options, current_value, self.small_font
                    )
                else:
                    # Update position in case layout changed
                    self.lobby_dropdowns[setting_key].rect = pg.Rect(
                        setting_x, value_y, dropdown_width, dropdown_height
                    )
                
                # Render dropdown - closed state here, open state in _render_dropdowns_on_top
                if not self.lobby_dropdowns[setting_key].is_open:
                    self.lobby_dropdowns[setting_key].render(screen)
                
            else:
                # Read-only setting or non-dropdown
                if interactive and self.is_host:
                    value_text = f"< {setting_value} >"
                    value_surface = self.small_font.render(value_text, True, self.primary_color)
                else:
                    value_surface = self.small_font.render(str(setting_value), True, self.text_secondary)
                screen.blit(value_surface, (setting_x, value_y))
                
                # Store click rect for non-dropdown interactive settings
                if interactive and self.is_host:
                    value_rect = pg.Rect(setting_x - 5, setting_y_pos - 2, col_width, setting_height - 5)
                    if not hasattr(self, 'lobby_setting_rects'):
                        self.lobby_setting_rects = {}
                    self.lobby_setting_rects[setting_key] = value_rect
                    
                    # Draw subtle border for clickable elements
                    pg.draw.rect(screen, (80, 80, 90), value_rect, 1)
        
        # Host instructions (only show for host) - positioned at bottom of settings area
        if self.is_host:
            instructions_y = divider_bottom - 25
            instruction_text = "Click settings to change • Use keyboard shortcuts"
            instruction_surface = self.small_font.render(instruction_text, True, self.text_secondary)
            # Center the instruction text in the settings area
            instruction_x = right_x + (settings_width - instruction_surface.get_width()) // 2
            screen.blit(instruction_surface, (instruction_x, instructions_y))
        
        # === BOTTOM ACTIONS ===
        # Position actions below the tab bar, at bottom of screen
        bar_height = 120
        bar_y = self.screen_height - (self.screen_height // 4) - (bar_height // 2)
        action_y = bar_y + bar_height + 10  # 10px below tab bar
        
        # Bottom action instructions have been moved to Settings tab
        # Players can find all keyboard controls in the Settings tab
    
    def _get_connected_players(self) -> List[Dict[str, Any]]:
        """Get list of connected players from network manager."""
        players = []
        
        # Always add self (whether host or client)
        if self.is_host:
            # Host should show their actual ready state
            host_player = {
                'display_name': getattr(self, 'player_name', 'Host'),
                'character': getattr(self, 'preferred_character', 'Cecil'),
                'is_host': True,
                'ready': getattr(self, 'is_ready', False),  # Use actual ready state
                'peer_id': 'host'
            }
            players.append(host_player)
        else:
            # If we're not host, add ourselves as a client
            client_player = {
                'display_name': getattr(self, 'player_name', 'Player'),
                'character': getattr(self, 'preferred_character', 'Cecil'),
                'is_host': False,
                'ready': getattr(self, 'is_ready', False),
                'peer_id': getattr(self, 'local_peer_id', 'client')
            }
            players.append(client_player)
        
        # Add connected peers from network manager
        if self.network_manager:
            # Use get_peer_list() method instead of directly accessing peers
            if hasattr(self.network_manager, 'get_peer_list'):
                peer_list = self.network_manager.get_peer_list()
                for peer_info in peer_list:
                    # Don't duplicate ourselves
                    is_self = (peer_info.peer_id == getattr(self.network_manager, 'local_peer_id', None))
                    if not is_self:
                        peer_player = {
                            'display_name': peer_info.display_name,
                            'character': getattr(peer_info, 'character', 'Not selected'),
                            'is_host': getattr(peer_info, 'is_host', False),
                            'ready': getattr(peer_info, 'ready', False),
                            'peer_id': peer_info.peer_id
                        }
                        players.append(peer_player)
        
        # TEMPORARY: Add mock peer to test UI (remove once networking is fixed)
        if self.is_host and len(players) == 1:
            # Mock peer that reacts to host's ready state for testing
            mock_peer = {
                'display_name': 'Test Client',
                'character': 'Crown',
                'is_host': False,
                'ready': self.is_ready,  # Mock peer copies host's ready state for testing
                'peer_id': 'mock_client_123'
            }
            # Only add mock if no real peers (for testing UI)
            if not self.network_manager or not hasattr(self.network_manager, 'get_peer_list') or len(self.network_manager.get_peer_list()) == 0:
                # Mock peer disabled - uncomment next line only for UI testing:
                # players.append(mock_peer)
                pass
        
        return players
    
    def _render_status(self, screen: pg.Surface):
        """Render status message at bottom."""
        status_surface = self.small_font.render(self.status_message, True, self.status_color)
        status_rect = status_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        screen.blit(status_surface, status_rect)
        
    def get_current_lobby_code(self) -> Optional[str]:
        """Get the current lobby code for sharing."""
        if self.current_lobby_code:
            return self.current_lobby_code.format_for_display()
        return None
    
    def get_discord_share_message(self) -> Optional[str]:
        """Get formatted message for Discord sharing."""
        if self.current_lobby_code:
            return self.current_lobby_code.format_for_discord()
        return None
    
    # ===== MAIN GAME COMPATIBILITY METHODS =====
    # These methods maintain compatibility with the main game loop
    
    def get_network_manager(self):
        """Get the current network manager for game integration."""
        return self.network_manager
    
    def get_players(self) -> List[Dict[str, Any]]:
        """Get list of players for game integration."""
        if not self.network_manager:
            return []
            
        players = []
        peer_list = self.network_manager.get_peer_list()
        
        # Add host as first player
        if self.is_host:
            players.append({
                "id": self.network_manager.local_peer_id,
                "name": self.player_name,
                "is_host": True,
                "is_ready": True
            })
        
        # Add other players
        for peer in peer_list:
            if peer.peer_id != self.network_manager.local_peer_id:
                players.append({
                    "id": peer.peer_id,
                    "name": peer.display_name,
                    "is_host": peer.is_host,
                    "is_ready": True  # For now, assume all connected players are ready
                })
        
        return players
    
    def get_local_player_id(self) -> str:
        """Get the local player ID for game integration."""
        if self.network_manager:
            return self.network_manager.local_peer_id
        return "local_player"
    
    def set_status_message(self, message: str, color: tuple = None):
        """Set a status message to display."""
        self.status_message = message
        self.status_color = color or self.text_color
        self.status_timer = 3.0  # Display for 3 seconds
    
    def _handle_lobby_input(self, event) -> Optional[str]:
        """Handle input when in the lobby view."""
        if event.key == pg.K_ESCAPE:
            # Leave lobby
            self._leave_lobby()
            return None
        
        elif event.key == pg.K_RETURN or event.key == pg.K_KP_ENTER:
            if self.is_host:
                # Start game
                return self._start_game()
            
        elif event.key == pg.K_SPACE:
            if not self.is_host:
                # Toggle ready status (for clients)
                self._toggle_ready()
        
        # Character selection (C key)
        elif event.key == pg.K_c:
            return "character_select"
        
        # Host-only setting shortcuts
        elif self.is_host:
            if event.key == pg.K_e:
                # E key - cycle environmental effects
                self._cycle_lobby_setting('environment')
            elif event.key == pg.K_m:
                # M key - cycle maps
                self._cycle_lobby_setting('map')
            elif event.key == pg.K_p:
                # P key - toggle privacy
                self._cycle_lobby_setting('privacy')
            elif event.key == pg.K_EQUALS or event.key == pg.K_PLUS:
                # + key - increase max players
                if self.max_players < 8:
                    max_player_options = [2, 3, 4, 6, 8]
                    if self.max_players in max_player_options:
                        current_index = max_player_options.index(self.max_players)
                        if current_index < len(max_player_options) - 1:
                            self.max_players = max_player_options[current_index + 1]
                    else:
                        self.max_players = 4
                    self._set_status(f"Max players: {self.max_players}", self.success_color)
            elif event.key == pg.K_MINUS:
                # - key - decrease max players
                if self.max_players > 2:
                    max_player_options = [2, 3, 4, 6, 8]
                    if self.max_players in max_player_options:
                        current_index = max_player_options.index(self.max_players)
                        if current_index > 0:
                            self.max_players = max_player_options[current_index - 1]
                    else:
                        self.max_players = 4
                    self._set_status(f"Max players: {self.max_players}", self.success_color)
            
        return None
    
    def _handle_lobby_mouse_click(self, pos) -> Optional[str]:
        """Handle mouse clicks in lobby view."""
        import time
        
        # Prevent double-processing of the same click
        current_time = time.time()
        if (hasattr(self, '_last_lobby_click_pos') and hasattr(self, '_last_lobby_click_time') and
            self._last_lobby_click_pos == pos and 
            current_time - self._last_lobby_click_time < 0.1):  # 100ms debounce
            print(f"[DEBUG] Ignoring duplicate lobby click at {pos}")
            return None
            
        self._last_lobby_click_pos = pos
        self._last_lobby_click_time = current_time
        print(f"[DEBUG] Processing lobby click at {pos}")
        
        # Handle dropdown clicks first
        for setting_name, dropdown in self.lobby_dropdowns.items():
            # Check if click is for this dropdown (main button OR expanded area)
            is_dropdown_click = dropdown.rect.collidepoint(pos)
            if not is_dropdown_click and dropdown.is_open and hasattr(dropdown, 'dropdown_rect') and dropdown.dropdown_rect:
                is_dropdown_click = dropdown.dropdown_rect.collidepoint(pos)
            
            if is_dropdown_click:
                print(f"[DEBUG] Click detected for {setting_name} dropdown")
                result = dropdown.handle_click(pos)
                if result is not None:
                    print(f"[DEBUG] Dropdown {setting_name} selected value: {result}")
                    # Dropdown value changed
                    self._handle_dropdown_selection(setting_name, result)
                    return None
                else:
                    print(f"[DEBUG] Clicked dropdown {setting_name} (now {'open' if dropdown.is_open else 'closed'})")
                    # Close other dropdowns when opening a new one
                    if dropdown.is_open:
                        for other_name, other_dropdown in self.lobby_dropdowns.items():
                            if other_name != setting_name and other_dropdown.is_open:
                                other_dropdown.is_open = False
                    return None
        
        # Check if clicking the CHARACTER setting to open character select
        if hasattr(self, 'character_setting_rect') and self.character_setting_rect.collidepoint(pos):
            return "character_select"
        
        # Only host can change settings (non-dropdown ones)
        if not self.is_host or not hasattr(self, 'lobby_setting_rects'):
            return None
        
        # Check each setting click area for non-dropdown settings
        for setting_name, rect in self.lobby_setting_rects.items():
            if rect.collidepoint(pos):
                if setting_name not in self.lobby_dropdowns:  # Not a dropdown setting
                    self._cycle_lobby_setting(setting_name)
                return None
        
        return None
    
    def _handle_player_scroll(self, scroll_y: int):
        """Handle mouse wheel scrolling in player list."""
        # Get total number of slots (players + empty slots up to max_players)
        connected_players = self._get_connected_players()
        total_slots = max(getattr(self, 'max_players', 4), len(connected_players))
        
        # Only scroll if there are more slots than can fit
        if total_slots <= self.max_visible_players:
            return
        
        # Calculate scroll limits based on total slots
        max_scroll = max(0, total_slots - self.max_visible_players)
        
        # Update scroll offset
        self.player_scroll_offset = max(0, min(max_scroll, self.player_scroll_offset - scroll_y))
    
    def _handle_dropdown_selection(self, setting_name: str, selected_value: str):
        """Handle dropdown selection changes."""
        if setting_name == 'environment':
            self.environmental_effects = selected_value
            self._set_status(f"Environment changed to {selected_value}", self.success_color)
        elif setting_name == 'map':
            self.map_selection = selected_value
            self._set_status(f"Map changed to {selected_value}", self.success_color)
        elif setting_name == 'privacy':
            self.lobby_privacy = selected_value
            self._set_status(f"Privacy changed to {selected_value}", self.success_color)
        elif setting_name == 'max_players':
            self.max_players = int(selected_value)
            self._set_status(f"Max players changed to {selected_value}", self.success_color)
        elif setting_name == 'connection_method':
            self.connection_method = selected_value
            self._set_status(f"Connection method changed to {selected_value}", self.success_color)
        elif setting_name == 'show_ping':
            self.show_ping = (selected_value == "ON")
            self._set_status(f"Show ping {'enabled' if self.show_ping else 'disabled'}", self.success_color)
        elif setting_name == 'auto_ready':
            self.auto_ready = (selected_value == "ON")
            self._set_status(f"Auto ready {'enabled' if self.auto_ready else 'disabled'}", self.success_color)
        
        # If this is the host, broadcast the setting change to all clients
        if self.is_host and self.network_manager:
            self._broadcast_lobby_setting_change(setting_name, selected_value)
    
    def _broadcast_lobby_setting_change(self, setting_name: str, value: str):
        """Broadcast lobby setting change to all clients (host only)."""
        if not self.network_manager or not hasattr(self.network_manager, 'send_message'):
            return
            
        setting_data = {
            "setting": setting_name,
            "value": value
        }
        
        try:
            self.network_manager.send_message("lobby_setting_change", setting_data, target_peer=None)
            print(f"Broadcasted setting change: {setting_name} = {value}")
        except Exception as e:
            print(f"Error broadcasting setting change: {e}")
    
    def _cycle_lobby_setting(self, setting_name: str):
        """Cycle through values for a lobby setting."""
        if setting_name == 'environment':
            # Cycle through environmental effects
            current_index = self.available_environments.index(self.environmental_effects)
            next_index = (current_index + 1) % len(self.available_environments)
            self.environmental_effects = self.available_environments[next_index]
            self._set_status(f"Environment changed to {self.environmental_effects}", self.success_color)
            
        elif setting_name == 'map':
            # Cycle through available maps (only if more than one)
            if len(self.available_maps) > 1:
                current_index = self.available_maps.index(self.map_selection)
                next_index = (current_index + 1) % len(self.available_maps)
                self.map_selection = self.available_maps[next_index]
                self._set_status(f"Map changed to {self.map_selection}", self.success_color)
            
        elif setting_name == 'max_players':
            # Cycle through max players (2-8)
            max_player_options = [2, 3, 4, 6, 8]
            if self.max_players in max_player_options:
                current_index = max_player_options.index(self.max_players)
                next_index = (current_index + 1) % len(max_player_options)
                self.max_players = max_player_options[next_index]
            else:
                self.max_players = 4  # Default
            self._set_status(f"Max players changed to {self.max_players}", self.success_color)
            
        elif setting_name == 'privacy':
            # Toggle between Public and Private
            self.lobby_privacy = "Private" if self.lobby_privacy == "Public" else "Public"
            self._set_status(f"Privacy changed to {self.lobby_privacy}", self.success_color)
            
        elif setting_name == 'character':
            # Cycle through available characters
            if self.character_manager and hasattr(self.character_manager, 'available_characters'):
                available_chars = list(self.character_manager.available_characters.keys())
                if available_chars:
                    if self.preferred_character in available_chars:
                        current_index = available_chars.index(self.preferred_character)
                        next_index = (current_index + 1) % len(available_chars)
                        self.preferred_character = available_chars[next_index]
                    else:
                        self.preferred_character = available_chars[0]
                    self._set_status(f"Character changed to {self.preferred_character}", self.success_color)
    
    def _leave_lobby(self):
        """Leave the current lobby."""
        if self.network_manager:
            # Close network connection
            if hasattr(self.network_manager, 'shutdown'):
                self.network_manager.shutdown()
            self.network_manager = None
        
        # Reset lobby state
        self.current_lobby_code = None
        self.connection_status = "Offline"
        self.is_host = False
        self.players_in_lobby = {}
        self._set_status("Left lobby", self.warning_color)
    
    def _start_game(self) -> Optional[str]:
        """Start the game (host only)."""
        if not self.is_host:
            return None
            
        # Check if all players are ready (placeholder logic)
        connected_players = self._get_connected_players()
        if len(connected_players) < 2:
            self._set_status("Need at least 2 players to start", self.warning_color)
            return None
        
        # TODO: Send start game message to all clients
        # For now, just return to character select or game
        return "character_select"
    
    def _toggle_ready(self):
        """Toggle ready status for client."""
        # Use the existing working ready functionality
        self._handle_ready_button()
    
    def _render_dropdowns_on_top(self, screen: pg.Surface):
        """Render open dropdowns relevant to current tab on top of other UI elements for proper z-order."""
        # Only render OPEN dropdowns for the current context
        if self.current_tab == LobbyTab.SETTINGS:
            # Render open settings dropdowns
            settings_dropdowns = ['connection_method', 'show_ping', 'auto_ready']
            for setting_name in settings_dropdowns:
                if setting_name in self.lobby_dropdowns and self.lobby_dropdowns[setting_name]:
                    dropdown = self.lobby_dropdowns[setting_name]
                    if dropdown.is_open:
                        dropdown.render(screen)
        elif self.current_tab == LobbyTab.CREATE and hasattr(self, 'current_lobby_code') and self.current_lobby_code:
            # Render open lobby settings dropdowns when in active lobby
            lobby_dropdowns = ['environment', 'map', 'privacy', 'max_players']
            for setting_name in lobby_dropdowns:
                if setting_name in self.lobby_dropdowns and self.lobby_dropdowns[setting_name] and self.lobby_dropdowns[setting_name].is_open:
                    self.lobby_dropdowns[setting_name].render(screen)
        
        # Debug: Draw hover detection rectangles if debug mode is enabled
        if self.debug_hover and self.current_tab == LobbyTab.SETTINGS:
            self._draw_settings_hover_debug(screen)
    
    def _close_all_dropdowns(self):
        """Close all open dropdowns."""
        for dropdown in self.lobby_dropdowns.values():
            if dropdown and hasattr(dropdown, 'is_open'):
                dropdown.is_open = False
    
    def update(self, dt: float):
        """Update method for main game compatibility."""
        print(f"[DEBUG] ModernMultiplayerLobby.update() (line 4067) called - connection_status: '{self.connection_status}', network_manager: {self.network_manager is not None}")
        
        # Update status message timer
        if self.status_timer > 0:
            self.status_timer -= dt
            if self.status_timer <= 0:
                self.status_message = ""
        
        # Process network messages for lobby synchronization 
        if self.network_manager and hasattr(self.network_manager, '_receive_direct_message'):
            print(f"[DEBUG] Processing network messages in main update method")
            try:
                message = self.network_manager._receive_direct_message(timeout=0.1)
                if message:
                    print(f"[DEBUG] Main update method received message: {message}")
                    self._handle_network_message(message)
                else:
                    print(f"[DEBUG] No message received in main update")
            except Exception as e:
                print(f"[ERROR] Error processing network message in main update: {e}")
        else:
            print(f"[DEBUG] No network manager or _receive_direct_message method available")
"""
Multiplayer Lobby System for Kingdom-Pygame.
Handles room creation, joining, player management, and game startup.
"""

import pygame as pg
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from .network_manager import NetworkManager, MessageType


class LobbyState(Enum):
    """States of the lobby system."""
    OFFLINE = "offline"
    HOSTING = "hosting"
    JOINING = "joining"
    IN_LOBBY = "in_lobby"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class PlayerInfo:
    """Information about a player in the lobby."""
    player_id: str
    name: str
    character: str
    ready: bool = False
    is_host: bool = False


@dataclass
class LobbyInfo:
    """Information about a lobby/room."""
    host_name: str
    player_count: int
    max_players: int
    game_mode: str = "Survival"
    map_name: str = "Field-Large"


class MultiplayerLobby:
    """Manages multiplayer lobby functionality."""
    
    def __init__(self, screen_width: int, screen_height: int, font, small_font):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.small_font = small_font
        
        # Network management
        self.network_manager = None
        self.state = LobbyState.OFFLINE
        
        # Lobby data
        self.players = {}  # player_id -> PlayerInfo
        self.local_player_id = None
        self.local_player_name = "Player"
        self.is_host = False
        
        # UI state
        self.selected_option = 0
        self.lobby_options = ["Host Game", "Join Game", "Back"]
        self.join_options = ["Connect", "Back"]
        self.lobby_menu_options = ["Ready", "Change Character", "Leave"]
        
        # Input fields
        self.host_port = "7777"
        self.join_address = "localhost"
        self.join_port = "7777"
        self.player_name = "Player"
        self.editing_field = None  # Which field is being edited
        
        # Game settings (for host)
        self.max_players = 4
        self.game_mode = "Survival"
        self.map_name = "Field-Large"
        
        # Visual settings
        self.background_color = (20, 25, 40)
        self.menu_color = (40, 50, 70)
        self.selected_color = (80, 120, 200)
        self.text_color = (220, 220, 220)
        self.highlight_color = (255, 255, 100)
        
        # Connection status
        self.connection_status = ""
        self.status_color = (255, 255, 255)
        self.last_status_time = 0
        
        # Character selection
        self.available_characters = [
            "Cecil", "Commander", "Crown", "Kilo", "Marian", 
            "Rapunzel", "Scarlet", "Sin", "Snow White", "Trony", "Wells"
        ]
        self.selected_character_index = 0
        self.local_character = self.available_characters[0]
        
        # Ready state
        self.local_ready = False
    
    def handle_input(self, event):
        """Handle input events for the lobby."""
        if event.type == pg.KEYDOWN:
            if self.state == LobbyState.OFFLINE:
                return self._handle_main_lobby_input(event)
            elif self.state == LobbyState.HOSTING:
                return self._handle_host_setup_input(event)
            elif self.state == LobbyState.JOINING:
                return self._handle_join_setup_input(event)
            elif self.state == LobbyState.IN_LOBBY:
                return self._handle_in_lobby_input(event)
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                return self._handle_mouse_click(event.pos)
        elif event.type == pg.MOUSEMOTION:
            self._handle_mouse_hover(event.pos)
        
        return None
    
    def _handle_main_lobby_input(self, event):
        """Handle input in main lobby menu."""
        if event.key == pg.K_UP:
            self.selected_option = (self.selected_option - 1) % len(self.lobby_options)
        elif event.key == pg.K_DOWN:
            self.selected_option = (self.selected_option + 1) % len(self.lobby_options)
        elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
            option = self.lobby_options[self.selected_option]
            if option == "Host Game":
                self.state = LobbyState.HOSTING
                self.selected_option = 0
                return None
            elif option == "Join Game":
                self.state = LobbyState.JOINING
                self.selected_option = 0
                return None
            elif option == "Back":
                return "back"
        elif event.key == pg.K_ESCAPE:
            return "back"
        
        return None
    
    def _handle_host_setup_input(self, event):
        """Handle input in host setup menu."""
        if event.key == pg.K_ESCAPE:
            if self.editing_field:
                self.editing_field = None  # Stop editing if currently editing
            else:
                self.state = LobbyState.OFFLINE
                self.selected_option = 0
                return "back"  # Signal that escape was handled
        elif event.key == pg.K_RETURN:
            if self.editing_field:
                self.editing_field = None  # Stop editing
            elif self.selected_option == 0:  # Start hosting
                return self._start_hosting()
            elif self.selected_option == 1:  # Back
                self.state = LobbyState.OFFLINE
                self.selected_option = 0
        elif event.key == pg.K_UP:
            if not self.editing_field:
                self.selected_option = (self.selected_option - 1) % 2
        elif event.key == pg.K_DOWN:
            if not self.editing_field:
                self.selected_option = (self.selected_option + 1) % 2
        elif event.key == pg.K_TAB:
            # Cycle through input fields
            if self.editing_field == "port":
                self.editing_field = "name"
            elif self.editing_field == "name":
                self.editing_field = None
            else:
                self.editing_field = "port"
        
        # Handle text input for fields
        if self.editing_field == "port":
            if event.key == pg.K_BACKSPACE:
                if self.host_port:
                    self.host_port = self.host_port[:-1]
            elif event.unicode.isdigit() and len(self.host_port) < 5:
                self.host_port += event.unicode
        elif self.editing_field == "name":
            if event.key == pg.K_BACKSPACE:
                if self.player_name:
                    self.player_name = self.player_name[:-1]
            elif event.unicode.isprintable() and len(self.player_name) < 20:
                self.player_name += event.unicode
        
        return None
    
    def _handle_join_setup_input(self, event):
        """Handle input in join setup menu."""
        if event.key == pg.K_ESCAPE:
            if self.editing_field:
                self.editing_field = None  # Stop editing if currently editing
            else:
                self.state = LobbyState.OFFLINE
                self.selected_option = 0
                return "back"  # Signal that escape was handled
        elif event.key == pg.K_RETURN:
            if self.editing_field:
                self.editing_field = None  # Stop editing
            elif self.selected_option == 0:  # Connect
                return self._start_joining()
            elif self.selected_option == 1:  # Back
                self.state = LobbyState.OFFLINE
                self.selected_option = 0
        elif event.key == pg.K_UP:
            if not self.editing_field:
                self.selected_option = (self.selected_option - 1) % 2
        elif event.key == pg.K_DOWN:
            if not self.editing_field:
                self.selected_option = (self.selected_option + 1) % 2
        elif event.key == pg.K_TAB:
            # Cycle through input fields
            if self.editing_field == "address":
                self.editing_field = "port"
            elif self.editing_field == "port":
                self.editing_field = "name"
            elif self.editing_field == "name":
                self.editing_field = None
            else:
                self.editing_field = "address"
        
        # Handle text input for fields
        if self.editing_field == "address":
            if event.key == pg.K_BACKSPACE:
                if self.join_address:
                    self.join_address = self.join_address[:-1]
            elif event.unicode.isprintable() and len(self.join_address) < 30:
                self.join_address += event.unicode
        elif self.editing_field == "port":
            if event.key == pg.K_BACKSPACE:
                if self.join_port:
                    self.join_port = self.join_port[:-1]
            elif event.unicode.isdigit() and len(self.join_port) < 5:
                self.join_port += event.unicode
        elif self.editing_field == "name":
            if event.key == pg.K_BACKSPACE:
                if self.player_name:
                    self.player_name = self.player_name[:-1]
            elif event.unicode.isprintable() and len(self.player_name) < 20:
                self.player_name += event.unicode
        
        return None
    
    def _handle_in_lobby_input(self, event):
        """Handle input when in a lobby."""
        if event.key == pg.K_ESCAPE:
            return self._leave_lobby()
        elif event.key == pg.K_UP:
            self.selected_option = (self.selected_option - 1) % len(self.lobby_menu_options)
        elif event.key == pg.K_DOWN:
            self.selected_option = (self.selected_option + 1) % len(self.lobby_menu_options)
        elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
            option = self.lobby_menu_options[self.selected_option]
            if option == "Ready":
                self._toggle_ready()
            elif option == "Change Character":
                self._cycle_character()
            elif option == "Leave":
                return self._leave_lobby()
        elif event.key == pg.K_LEFT and self.selected_option == 1:  # Change character
            self._cycle_character(-1)
        elif event.key == pg.K_RIGHT and self.selected_option == 1:  # Change character
            self._cycle_character(1)
        
        return None
    
    def _handle_mouse_click(self, pos):
        """Handle mouse clicks in the lobby."""
        if self.state == LobbyState.OFFLINE:
            return self._handle_main_lobby_mouse_click(pos)
        elif self.state == LobbyState.HOSTING:
            return self._handle_host_setup_mouse_click(pos)
        elif self.state == LobbyState.JOINING:
            return self._handle_join_setup_mouse_click(pos)
        elif self.state == LobbyState.IN_LOBBY:
            return self._handle_in_lobby_mouse_click(pos)
        return None
    
    def _handle_mouse_hover(self, pos):
        """Handle mouse hover in the lobby."""
        if self.state == LobbyState.OFFLINE:
            self._handle_main_lobby_mouse_hover(pos)
        elif self.state == LobbyState.HOSTING:
            self._handle_host_setup_mouse_hover(pos)
        elif self.state == LobbyState.JOINING:
            self._handle_join_setup_mouse_hover(pos)
        elif self.state == LobbyState.IN_LOBBY:
            self._handle_in_lobby_mouse_hover(pos)
    
    def _handle_main_lobby_mouse_click(self, pos):
        """Handle mouse clicks in main lobby menu."""
        y_start = 220
        button_width = 300
        button_height = 50
        
        for i, option in enumerate(self.lobby_options):
            y_pos = y_start + i * 80
            x_pos = (self.screen_width - button_width) // 2
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                self.selected_option = i
                if option == "Host Game":
                    self.state = LobbyState.HOSTING
                    self.selected_option = 0
                    return None
                elif option == "Join Game":
                    self.state = LobbyState.JOINING
                    self.selected_option = 0
                    return None
                elif option == "Back":
                    return "back"
        return None
    
    def _handle_main_lobby_mouse_hover(self, pos):
        """Handle mouse hover in main lobby menu."""
        y_start = 220
        button_width = 300
        button_height = 50
        
        for i, option in enumerate(self.lobby_options):
            y_pos = y_start + i * 80
            x_pos = (self.screen_width - button_width) // 2
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                self.selected_option = i
                break
    
    def _handle_host_setup_mouse_click(self, pos):
        """Handle mouse clicks in host setup screen."""
        # Check input field clicks
        # Port input field
        port_rect = pg.Rect(self.screen_width // 2 - 50, 175, 100, 30)
        if port_rect.collidepoint(pos):
            self.editing_field = "port"
            return None
            
        # Name input field  
        name_rect = pg.Rect(self.screen_width // 2 - 50, 235, 150, 30)
        if name_rect.collidepoint(pos):
            self.editing_field = "name"
            return None
        
        # Check button clicks
        y_start = 420
        button_width = 200
        button_height = 40
        options = ["Start Hosting", "Back"]
        
        for i, option in enumerate(options):
            x_pos = (self.screen_width - button_width) // 2
            y_pos = y_start + i * 60
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                self.selected_option = i
                if option == "Start Hosting":
                    return self._start_hosting()
                elif option == "Back":
                    self.state = LobbyState.OFFLINE
                    self.selected_option = 0
                    return None
        
        # Click outside input fields to stop editing
        self.editing_field = None
        return None
    
    def _handle_host_setup_mouse_hover(self, pos):
        """Handle mouse hover in host setup screen."""
        # Check button hover
        y_start = 420
        button_width = 200
        button_height = 40
        
        for i, option in enumerate(["Start Hosting", "Back"]):
            x_pos = (self.screen_width - button_width) // 2
            y_pos = y_start + i * 60
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                self.selected_option = i
                break
    
    def _handle_join_setup_mouse_click(self, pos):
        """Handle mouse clicks in join setup screen."""
        # Check input field clicks
        # Address input field
        addr_rect = pg.Rect(self.screen_width // 2 - 50, 175, 200, 30)
        if addr_rect.collidepoint(pos):
            self.editing_field = "address"
            return None
            
        # Port input field
        port_rect = pg.Rect(self.screen_width // 2 - 50, 235, 100, 30)
        if port_rect.collidepoint(pos):
            self.editing_field = "port"
            return None
            
        # Name input field  
        name_rect = pg.Rect(self.screen_width // 2 - 50, 295, 150, 30)
        if name_rect.collidepoint(pos):
            self.editing_field = "name"
            return None
        
        # Check button clicks
        y_start = 380
        button_width = 200
        button_height = 40
        options = ["Connect", "Back"]
        
        for i, option in enumerate(options):
            x_pos = (self.screen_width - button_width) // 2
            y_pos = y_start + i * 60
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                self.selected_option = i
                if option == "Connect":
                    return self._start_joining()
                elif option == "Back":
                    self.state = LobbyState.OFFLINE
                    self.selected_option = 0
                    return None
        
        # Click outside input fields to stop editing
        self.editing_field = None
        return None
    
    def _handle_join_setup_mouse_hover(self, pos):
        """Handle mouse hover in join setup screen."""
        # Check button hover
        y_start = 380
        button_width = 200
        button_height = 40
        
        for i, option in enumerate(["Connect", "Back"]):
            x_pos = (self.screen_width - button_width) // 2
            y_pos = y_start + i * 60
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                self.selected_option = i
                break
    
    def _handle_in_lobby_mouse_click(self, pos):
        """Handle mouse clicks in the in-lobby screen."""
        # For now, just handle keyboard - can expand later
        return None
    
    def _handle_in_lobby_mouse_hover(self, pos):
        """Handle mouse hover in the in-lobby screen."""
        # For now, just handle keyboard - can expand later
        pass

    def _start_hosting(self):
        """Start hosting a game."""
        try:
            port = int(self.host_port) if self.host_port else 7777
            self.network_manager = NetworkManager(is_server=True)
            
            if self.network_manager.start_server("localhost", port):
                self.state = LobbyState.IN_LOBBY
                self.is_host = True
                self.local_player_id = "host"
                
                # Add host to players list
                self.players[self.local_player_id] = PlayerInfo(
                    player_id=self.local_player_id,
                    name=self.player_name,
                    character=self.local_character,
                    ready=False,
                    is_host=True
                )
                
                self._set_status("Hosting game on port " + str(port), (100, 255, 100))
                self._setup_network_handlers()
                return None
            else:
                self._set_status("Failed to start server", (255, 100, 100))
        except Exception as e:
            self._set_status(f"Error: {e}", (255, 100, 100))
        
        return None
    
    def _start_joining(self):
        """Start joining a game."""
        try:
            address = self.join_address if self.join_address else "localhost"
            port = int(self.join_port) if self.join_port else 7777
            
            self.network_manager = NetworkManager(is_server=False)
            self.state = LobbyState.CONNECTING
            
            if self.network_manager.connect_to_server(address, port, self.player_name):
                self._set_status("Connecting...", (255, 255, 100))
                self._setup_network_handlers()
                return None
            else:
                self._set_status("Failed to connect", (255, 100, 100))
                self.state = LobbyState.JOINING
        except Exception as e:
            self._set_status(f"Connection error: {e}", (255, 100, 100))
            self.state = LobbyState.JOINING
        
        return None
    
    def _leave_lobby(self):
        """Leave the current lobby."""
        if self.network_manager:
            self.network_manager.disconnect()
            self.network_manager = None
        
        self.state = LobbyState.OFFLINE
        self.players.clear()
        self.local_player_id = None
        self.is_host = False
        self.local_ready = False
        self.selected_option = 0
        self._set_status("Left lobby", (255, 255, 100))
        
        return "back"  # Signal that we're leaving the lobby
    
    def _toggle_ready(self):
        """Toggle ready state."""
        self.local_ready = not self.local_ready
        if self.local_player_id in self.players:
            self.players[self.local_player_id].ready = self.local_ready
        
        # Send ready state to other players
        if self.network_manager:
            self.network_manager.send_message(
                MessageType.PLAYER_UPDATE,
                {
                    "player_id": self.local_player_id,
                    "ready": self.local_ready
                }
            )
    
    def _cycle_character(self, direction: int = 1):
        """Cycle through available characters."""
        self.selected_character_index = (
            self.selected_character_index + direction
        ) % len(self.available_characters)
        self.local_character = self.available_characters[self.selected_character_index]
        
        if self.local_player_id in self.players:
            self.players[self.local_player_id].character = self.local_character
        
        # Send character change to other players
        if self.network_manager:
            self.network_manager.send_message(
                MessageType.PLAYER_UPDATE,
                {
                    "player_id": self.local_player_id,
                    "character": self.local_character
                }
            )
    
    def _setup_network_handlers(self):
        """Setup network message handlers."""
        if self.network_manager:
            self.network_manager.register_message_handler(
                MessageType.CONNECT, self._handle_player_connect
            )
            self.network_manager.register_message_handler(
                MessageType.PLAYER_JOIN, self._handle_player_join
            )
            self.network_manager.register_message_handler(
                MessageType.PLAYER_LEAVE, self._handle_player_leave
            )
            self.network_manager.register_message_handler(
                MessageType.PLAYER_UPDATE, self._handle_player_update_lobby
            )
            self.network_manager.register_message_handler(
                MessageType.GAME_START, self._handle_game_start
            )
    
    def _handle_player_connect(self, message):
        """Handle player connection confirmation."""
        data = message.data
        if not self.is_host:
            self.local_player_id = data.get('player_id')
            self.state = LobbyState.IN_LOBBY
            
            # Add existing players
            for player_data in data.get('connected_players', []):
                player_id = player_data['id']
                player_name = player_data['name']
                self.players[player_id] = PlayerInfo(
                    player_id=player_id,
                    name=player_name,
                    character="Cecil",  # Default character
                    ready=False,
                    is_host=(player_id == "host")
                )
            
            # Add local player
            self.players[self.local_player_id] = PlayerInfo(
                player_id=self.local_player_id,
                name=self.player_name,
                character=self.local_character,
                ready=False,
                is_host=False
            )
            
            self._set_status("Connected to lobby", (100, 255, 100))
    
    def _handle_player_join(self, message):
        """Handle another player joining."""
        data = message.data
        player_id = data['player_id']
        player_name = data['player_name']
        
        self.players[player_id] = PlayerInfo(
            player_id=player_id,
            name=player_name,
            character="Cecil",  # Default character
            ready=False,
            is_host=False
        )
        
        self._set_status(f"{player_name} joined", (100, 255, 100))
    
    def _handle_player_leave(self, message):
        """Handle player leaving."""
        data = message.data
        player_id = data['player_id']
        
        if player_id in self.players:
            player_name = self.players[player_id].name
            del self.players[player_id]
            self._set_status(f"{player_name} left", (255, 255, 100))
    
    def _handle_player_update_lobby(self, message):
        """Handle player update in lobby."""
        data = message.data
        player_id = data['player_id']
        
        if player_id in self.players:
            if 'ready' in data:
                self.players[player_id].ready = data['ready']
            if 'character' in data:
                self.players[player_id].character = data['character']
    
    def _handle_game_start(self, message):
        """Handle game start message."""
        return "start_game"
    
    def _set_status(self, message: str, color: Tuple[int, int, int]):
        """Set status message with color."""
        self.connection_status = message
        self.status_color = color
        self.last_status_time = time.time()
    
    def update(self, dt: float):
        """Update lobby state."""
        if self.network_manager:
            self.network_manager.process_messages()
        
        # Clear old status messages
        if time.time() - self.last_status_time > 3.0:
            self.connection_status = ""
    
    def can_start_game(self) -> bool:
        """Check if game can be started."""
        if not self.is_host or len(self.players) < 1:
            return False
        
        # Check if all players are ready
        for player in self.players.values():
            if not player.ready:
                return False
        
        return True
    
    def start_game(self):
        """Start the game (host only)."""
        if self.can_start_game() and self.network_manager:
            self.network_manager.send_message(
                MessageType.GAME_START,
                {"map": self.map_name, "mode": self.game_mode}
            )
            return "start_game"
        return None
    
    def render(self, screen: pg.Surface):
        """Render the lobby UI."""
        screen.fill(self.background_color)
        
        if self.state == LobbyState.OFFLINE:
            self._render_main_lobby(screen)
        elif self.state == LobbyState.HOSTING:
            self._render_host_setup(screen)
        elif self.state == LobbyState.JOINING or self.state == LobbyState.CONNECTING:
            self._render_join_setup(screen)
        elif self.state == LobbyState.IN_LOBBY:
            self._render_in_lobby(screen)
        
        # Render status message
        if self.connection_status:
            status_surface = self.small_font.render(self.connection_status, True, self.status_color)
            status_rect = status_surface.get_rect(
                centerx=self.screen_width // 2,
                bottom=self.screen_height - 20
            )
            screen.blit(status_surface, status_rect)
    
    def _render_main_lobby(self, screen: pg.Surface):
        """Render main lobby menu."""
        # Title
        title = self.font.render("MULTIPLAYER", True, self.text_color)
        title_rect = title.get_rect(centerx=self.screen_width // 2, y=100)
        screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.small_font.render("Choose an option below", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect(centerx=self.screen_width // 2, y=140)
        screen.blit(subtitle, subtitle_rect)
        
        # Menu options with better visual feedback
        y_start = 220
        button_width = 300
        button_height = 50
        
        for i, option in enumerate(self.lobby_options):
            y_pos = y_start + i * 80
            x_pos = (self.screen_width - button_width) // 2
            
            # Button background
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            if i == self.selected_option:
                # Highlight selected option
                pg.draw.rect(screen, self.selected_color, button_rect)
                pg.draw.rect(screen, self.highlight_color, button_rect, 3)
                text_color = (255, 255, 255)
            else:
                # Normal button
                pg.draw.rect(screen, self.menu_color, button_rect)
                pg.draw.rect(screen, (100, 100, 100), button_rect, 2)
                text_color = self.text_color
            
            # Button text
            text = self.font.render(option, True, text_color)
            text_rect = text.get_rect(center=button_rect.center)
            screen.blit(text, text_rect)
        
        # Instructions
        instructions = [
            "Use arrow keys or mouse to navigate",
            "Press ENTER or click to select",
            "Press ESC to go back"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_surface = self.small_font.render(instruction, True, (150, 150, 150))
            inst_rect = inst_surface.get_rect(centerx=self.screen_width // 2, y=self.screen_height - 120 + i * 25)
            screen.blit(inst_surface, inst_rect)
    
    def _render_host_setup(self, screen: pg.Surface):
        """Render host setup screen."""
        # Title
        title = self.font.render("HOST GAME", True, self.text_color)
        title_rect = title.get_rect(centerx=self.screen_width // 2, y=80)
        screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.small_font.render("Configure your server settings", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect(centerx=self.screen_width // 2, y=120)
        screen.blit(subtitle, subtitle_rect)
        
        # Port input field
        y_pos = 180
        port_label = self.small_font.render("Server Port:", True, self.text_color)
        screen.blit(port_label, (self.screen_width // 2 - 150, y_pos))
        
        # Port input box
        port_rect = pg.Rect(self.screen_width // 2 - 50, y_pos - 5, 100, 30)
        port_color = self.highlight_color if self.editing_field == "port" else (100, 100, 100)
        pg.draw.rect(screen, (40, 40, 40), port_rect)
        pg.draw.rect(screen, port_color, port_rect, 2)
        
        port_text = self.small_font.render(self.host_port, True, self.text_color)
        port_text_rect = port_text.get_rect(center=port_rect.center)
        screen.blit(port_text, port_text_rect)
        
        # Add cursor if editing port
        if self.editing_field == "port":
            cursor_x = port_text_rect.right + 3
            cursor_y = port_text_rect.centery
            pg.draw.line(screen, self.text_color, (cursor_x, cursor_y - 8), (cursor_x, cursor_y + 8), 2)
        
        # Player name input
        y_pos = 240
        name_label = self.small_font.render("Your Name:", True, self.text_color)
        screen.blit(name_label, (self.screen_width // 2 - 150, y_pos))
        
        name_rect = pg.Rect(self.screen_width // 2 - 50, y_pos - 5, 150, 30)
        name_color = self.highlight_color if self.editing_field == "name" else (100, 100, 100)
        pg.draw.rect(screen, (40, 40, 40), name_rect)
        pg.draw.rect(screen, name_color, name_rect, 2)
        
        name_text = self.small_font.render(self.player_name, True, self.text_color)
        name_text_rect = name_text.get_rect(center=name_rect.center)
        screen.blit(name_text, name_text_rect)
        
        # Add cursor if editing name
        if self.editing_field == "name":
            cursor_x = name_text_rect.right + 3
            cursor_y = name_text_rect.centery
            pg.draw.line(screen, self.text_color, (cursor_x, cursor_y - 8), (cursor_x, cursor_y + 8), 2)
        
        # Game settings
        y_pos = 300
        settings_label = self.font.render("Game Settings", True, self.text_color)
        settings_rect = settings_label.get_rect(centerx=self.screen_width // 2, y=y_pos)
        screen.blit(settings_label, settings_rect)
        
        y_pos = 340
        max_players_text = self.small_font.render(f"Max Players: {self.max_players}", True, self.text_color)
        screen.blit(max_players_text, (self.screen_width // 2 - 100, y_pos))
        
        game_mode_text = self.small_font.render(f"Game Mode: {self.game_mode}", True, self.text_color)
        screen.blit(game_mode_text, (self.screen_width // 2 - 100, y_pos + 30))
        
        # Action buttons
        y_start = 420
        button_width = 200
        button_height = 40
        options = ["Start Hosting", "Back"]
        
        for i, option in enumerate(options):
            x_pos = (self.screen_width - button_width) // 2
            y_pos = y_start + i * 60
            button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
            
            if i == self.selected_option:
                pg.draw.rect(screen, self.selected_color, button_rect)
                pg.draw.rect(screen, self.highlight_color, button_rect, 3)
                text_color = (255, 255, 255)
            else:
                pg.draw.rect(screen, self.menu_color, button_rect)
                pg.draw.rect(screen, (100, 100, 100), button_rect, 2)
                text_color = self.text_color
            
            text = self.font.render(option, True, text_color)
            text_rect = text.get_rect(center=button_rect.center)
            screen.blit(text, text_rect)
        
        # Instructions
        instructions = [
            "Click input fields or use TAB to edit",
            "ENTER: Select highlighted option",
            "ESC: Go back to main menu"
        ]
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, (150, 150, 150))
            text_rect = text.get_rect(centerx=self.screen_width // 2, y=self.screen_height - 80 + i * 20)
            screen.blit(text, text_rect)
    
    def _render_join_setup(self, screen: pg.Surface):
        """Render join setup screen."""
        # Title
        title_text = "CONNECTING..." if self.state == LobbyState.CONNECTING else "JOIN GAME"
        title = self.font.render(title_text, True, self.text_color)
        title_rect = title.get_rect(centerx=self.screen_width // 2, y=80)
        screen.blit(title, title_rect)
        
        # Subtitle
        if self.state != LobbyState.CONNECTING:
            subtitle = self.small_font.render("Enter server details to connect", True, (180, 180, 180))
            subtitle_rect = subtitle.get_rect(centerx=self.screen_width // 2, y=120)
            screen.blit(subtitle, subtitle_rect)
        
        # Server address input
        y_pos = 180
        addr_label = self.small_font.render("Server Address:", True, self.text_color)
        screen.blit(addr_label, (self.screen_width // 2 - 150, y_pos))
        
        addr_rect = pg.Rect(self.screen_width // 2 - 50, y_pos - 5, 200, 30)
        addr_color = self.highlight_color if self.editing_field == "address" else (100, 100, 100)
        pg.draw.rect(screen, (40, 40, 40), addr_rect)
        pg.draw.rect(screen, addr_color, addr_rect, 2)
        
        addr_text = self.small_font.render(self.join_address, True, self.text_color)
        addr_text_rect = addr_text.get_rect(center=addr_rect.center)
        screen.blit(addr_text, addr_text_rect)
        
        # Add cursor if editing address
        if self.editing_field == "address":
            cursor_x = addr_text_rect.right + 3
            cursor_y = addr_text_rect.centery
            pg.draw.line(screen, self.text_color, (cursor_x, cursor_y - 8), (cursor_x, cursor_y + 8), 2)
        
        # Port input
        y_pos = 240
        port_label = self.small_font.render("Server Port:", True, self.text_color)
        screen.blit(port_label, (self.screen_width // 2 - 150, y_pos))
        
        port_rect = pg.Rect(self.screen_width // 2 - 50, y_pos - 5, 100, 30)
        port_color = self.highlight_color if self.editing_field == "port" else (100, 100, 100)
        pg.draw.rect(screen, (40, 40, 40), port_rect)
        pg.draw.rect(screen, port_color, port_rect, 2)
        
        port_text = self.small_font.render(self.join_port, True, self.text_color)
        port_text_rect = port_text.get_rect(center=port_rect.center)
        screen.blit(port_text, port_text_rect)
        
        # Add cursor if editing port
        if self.editing_field == "port":
            cursor_x = port_text_rect.right + 3
            cursor_y = port_text_rect.centery
            pg.draw.line(screen, self.text_color, (cursor_x, cursor_y - 8), (cursor_x, cursor_y + 8), 2)
        
        # Player name input
        y_pos = 300
        name_label = self.small_font.render("Your Name:", True, self.text_color)
        screen.blit(name_label, (self.screen_width // 2 - 150, y_pos))
        
        name_rect = pg.Rect(self.screen_width // 2 - 50, y_pos - 5, 150, 30)
        name_color = self.highlight_color if self.editing_field == "name" else (100, 100, 100)
        pg.draw.rect(screen, (40, 40, 40), name_rect)
        pg.draw.rect(screen, name_color, name_rect, 2)
        
        name_text = self.small_font.render(self.player_name, True, self.text_color)
        name_text_rect = name_text.get_rect(center=name_rect.center)
        screen.blit(name_text, name_text_rect)
        
        # Add cursor if editing name
        if self.editing_field == "name":
            cursor_x = name_text_rect.right + 3
            cursor_y = name_text_rect.centery
            pg.draw.line(screen, self.text_color, (cursor_x, cursor_y - 8), (cursor_x, cursor_y + 8), 2)
        
        port_text = self.small_font.render(self.join_port, True, self.text_color)
        port_text_rect = port_text.get_rect(center=port_rect.center)
        screen.blit(port_text, port_text_rect)
        
        # Player name input
        y_pos = 300
        name_label = self.small_font.render("Your Name:", True, self.text_color)
        screen.blit(name_label, (self.screen_width // 2 - 150, y_pos))
        
        name_rect = pg.Rect(self.screen_width // 2 - 50, y_pos - 5, 150, 30)
        name_color = self.highlight_color if self.editing_field == "name" else (100, 100, 100)
        pg.draw.rect(screen, (40, 40, 40), name_rect)
        pg.draw.rect(screen, name_color, name_rect, 2)
        
        name_text = self.small_font.render(self.player_name, True, self.text_color)
        name_text_rect = name_text.get_rect(center=name_rect.center)
        screen.blit(name_text, name_text_rect)
        
        # Action buttons (if not connecting)
        if self.state != LobbyState.CONNECTING:
            y_start = 380
            button_width = 200
            button_height = 40
            options = ["Connect", "Back"]
            
            for i, option in enumerate(options):
                x_pos = (self.screen_width - button_width) // 2
                y_pos = y_start + i * 60
                button_rect = pg.Rect(x_pos, y_pos, button_width, button_height)
                
                if i == self.selected_option:
                    pg.draw.rect(screen, self.selected_color, button_rect)
                    pg.draw.rect(screen, self.highlight_color, button_rect, 3)
                    text_color = (255, 255, 255)
                else:
                    pg.draw.rect(screen, self.menu_color, button_rect)
                    pg.draw.rect(screen, (100, 100, 100), button_rect, 2)
                    text_color = self.text_color
                
                text = self.font.render(option, True, text_color)
                text_rect = text.get_rect(center=button_rect.center)
                screen.blit(text, text_rect)
            
            # Instructions
            instructions = [
                "Click input fields or use TAB to edit",
                "ENTER: Select highlighted option",
                "ESC: Go back to main menu"
            ]
            for i, instruction in enumerate(instructions):
                text = self.small_font.render(instruction, True, (150, 150, 150))
                text_rect = text.get_rect(centerx=self.screen_width // 2, y=self.screen_height - 80 + i * 20)
                screen.blit(text, text_rect)
        else:
            # Connecting spinner/message
            connecting_text = self.font.render("Attempting to connect...", True, self.text_color)
            connecting_rect = connecting_text.get_rect(centerx=self.screen_width // 2, y=400)
            screen.blit(connecting_text, connecting_rect)
            
            cancel_text = self.small_font.render("Press ESC to cancel", True, (150, 150, 150))
            cancel_rect = cancel_text.get_rect(centerx=self.screen_width // 2, y=450)
            screen.blit(cancel_text, cancel_rect)
        
        # Instructions
        instructions = [
            "Tab: Switch field",
            "Enter: Select option",
            "Escape: Back"
        ]
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, (150, 150, 150))
            screen.blit(text, (50, self.screen_height - 100 + i * 20))
    
    def _render_in_lobby(self, screen: pg.Surface):
        """Render in-lobby screen."""
        title = self.font.render("Lobby", True, self.text_color)
        title_rect = title.get_rect(centerx=self.screen_width // 2, y=50)
        screen.blit(title, title_rect)
        
        # Player list
        y_start = 120
        for i, player in enumerate(self.players.values()):
            y = y_start + i * 40
            
            # Player name
            name_color = self.highlight_color if player.is_host else self.text_color
            name_text = self.small_font.render(f"{player.name} {'(Host)' if player.is_host else ''}", True, name_color)
            screen.blit(name_text, (100, y))
            
            # Character
            char_text = self.small_font.render(player.character, True, self.text_color)
            screen.blit(char_text, (300, y))
            
            # Ready status
            ready_color = (100, 255, 100) if player.ready else (255, 100, 100)
            ready_text = self.small_font.render("Ready" if player.ready else "Not Ready", True, ready_color)
            screen.blit(ready_text, (500, y))
        
        # Menu options
        y_start = max(300, y_start + len(self.players) * 40 + 50)
        for i, option in enumerate(self.lobby_menu_options):
            color = self.highlight_color if i == self.selected_option else self.text_color
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(centerx=self.screen_width // 2, y=y_start + i * 50)
            screen.blit(text, text_rect)
        
        # Current character display
        if self.selected_option == 1:  # Change Character selected
            char_display = f"< {self.local_character} >"
            char_text = self.small_font.render(char_display, True, self.highlight_color)
            char_rect = char_text.get_rect(centerx=self.screen_width // 2, y=y_start + 1 * 50 + 30)
            screen.blit(char_text, char_rect)
        
        # Game start button (host only)
        if self.is_host:
            can_start = self.can_start_game()
            start_color = (100, 255, 100) if can_start else (100, 100, 100)
            start_text = self.font.render("Start Game" if can_start else "Waiting for players...", True, start_color)
            start_rect = start_text.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - 100)
            screen.blit(start_text, start_rect)
            
            if can_start:
                hint_text = self.small_font.render("Press S to start", True, (150, 150, 150))
                hint_rect = hint_text.get_rect(centerx=self.screen_width // 2, bottom=self.screen_height - 70)
                screen.blit(hint_text, hint_rect)
    
    def get_state(self) -> LobbyState:
        """Get current lobby state."""
        return self.state
    
    def get_network_manager(self) -> Optional[NetworkManager]:
        """Get network manager instance."""
        return self.network_manager
    
    def get_players(self) -> Dict[str, PlayerInfo]:
        """Get all players in lobby."""
        return self.players.copy()
    
    def get_local_player_id(self) -> Optional[str]:
        """Get local player ID."""
        return self.local_player_id
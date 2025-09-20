"""
Discord integration for Kingdom Cleanup multiplayer system.
Handles Rich Presence, lobby sharing, and Discord-based invitations.
"""

import time
import json
from typing import Dict, Optional, List, Any
from dataclasses import dataclass


@dataclass 
class DiscordLobbyInfo:
    """Discord-compatible lobby information."""
    lobby_code: str
    host_name: str
    current_players: int
    max_players: int
    game_mode: str
    region: str
    join_secret: str  # For Discord invites
    

class DiscordIntegration:
    """Discord Rich Presence and lobby integration."""
    
    def __init__(self):
        self.is_connected = False
        self.client_id = "1234567890123456789"  # Would be actual Discord app ID
        self.current_activity = None
        self.start_timestamp = int(time.time())
        
        # Try to initialize Discord RPC
        self._initialize_discord()
        
    def _initialize_discord(self):
        """Initialize Discord Rich Presence."""
        try:
            # In production, this would use pypresence or similar Discord RPC library
            # import pypresence
            # self.rpc = pypresence.Presence(self.client_id)
            # self.rpc.connect()
            
            print("Discord RPC: Simulated connection established")
            self.is_connected = True
            
        except Exception as e:
            print(f"Discord RPC: Connection failed - {e}")
            self.is_connected = False
    
    def update_main_menu_presence(self):
        """Update presence for main menu state."""
        activity = {
            "details": "In Main Menu",
            "state": "Browsing Options",
            "timestamps": {"start": self.start_timestamp},
            "assets": {
                "large_image": "kingdom_logo",
                "large_text": "Kingdom Cleanup",
                "small_image": "menu_icon",
                "small_text": "Main Menu"
            },
            "buttons": [
                {"label": "Play Kingdom Cleanup", "url": "https://kingdom-game.com"}
            ]
        }
        
        self._update_activity(activity)
    
    def update_lobby_presence(self, lobby_info: DiscordLobbyInfo):
        """Update presence for multiplayer lobby."""
        activity = {
            "details": f"{lobby_info.game_mode} Lobby",
            "state": f"{lobby_info.current_players}/{lobby_info.max_players} Players",
            "timestamps": {"start": self.start_timestamp},
            "party": {
                "id": lobby_info.lobby_code,
                "size": [lobby_info.current_players, lobby_info.max_players]
            },
            "secrets": {
                "join": lobby_info.join_secret
            },
            "assets": {
                "large_image": "kingdom_logo", 
                "large_text": "Kingdom Cleanup",
                "small_image": "multiplayer_icon",
                "small_text": f"Lobby: {lobby_info.lobby_code}"
            },
            "buttons": [
                {"label": "Join Lobby", "url": f"https://kingdom-game.com/join/{lobby_info.lobby_code}"}
            ]
        }
        
        self._update_activity(activity)
    
    def update_game_presence(self, game_mode: str, level_name: str, player_count: int):
        """Update presence for active gameplay."""
        activity = {
            "details": f"Playing {game_mode}",
            "state": f"Level: {level_name}",
            "timestamps": {"start": int(time.time())},
            "party": {
                "size": [player_count, 4] if player_count > 1 else None
            },
            "assets": {
                "large_image": "kingdom_logo",
                "large_text": "Kingdom Cleanup", 
                "small_image": "playing_icon",
                "small_text": f"{player_count} Player{'s' if player_count != 1 else ''}"
            }
        }
        
        self._update_activity(activity)
    
    def clear_presence(self):
        """Clear Discord presence."""
        if self.is_connected:
            try:
                # self.rpc.clear()
                print("Discord RPC: Presence cleared")
            except Exception as e:
                print(f"Discord RPC: Clear failed - {e}")
    
    def _update_activity(self, activity: Dict[str, Any]):
        """Internal method to update Discord activity."""
        if not self.is_connected:
            return
            
        try:
            # In production: self.rpc.update(**activity)
            print(f"Discord RPC: Updated activity - {activity['details']}: {activity['state']}")
            self.current_activity = activity
            
        except Exception as e:
            print(f"Discord RPC: Update failed - {e}")
    
    def generate_lobby_invite_url(self, lobby_code: str) -> str:
        """Generate a shareable lobby invite URL."""
        return f"https://kingdom-game.com/join/{lobby_code}"
    
    def generate_discord_embed(self, lobby_info: DiscordLobbyInfo) -> Dict[str, Any]:
        """Generate Discord embed for lobby sharing."""
        return {
            "title": "🎮 Kingdom Cleanup Lobby",
            "description": f"Join {lobby_info.host_name}'s game!",
            "color": 0x4A90E2,  # Blue color
            "fields": [
                {
                    "name": "🔑 Join Code",
                    "value": f"`{lobby_info.lobby_code}`",
                    "inline": True
                },
                {
                    "name": "🎯 Game Mode", 
                    "value": lobby_info.game_mode,
                    "inline": True
                },
                {
                    "name": "👥 Players",
                    "value": f"{lobby_info.current_players}/{lobby_info.max_players}",
                    "inline": True
                },
                {
                    "name": "🌍 Region",
                    "value": lobby_info.region,
                    "inline": True
                }
            ],
            "footer": {
                "text": "Kingdom Cleanup Multiplayer",
                "icon_url": "https://kingdom-game.com/assets/icon.png"
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    def format_lobby_message(self, lobby_info: DiscordLobbyInfo) -> str:
        """Format lobby information for sharing in Discord chat."""
        message = f"🎮 **Kingdom Cleanup Lobby**\\n"
        message += f"🔹 **Code:** `{lobby_info.lobby_code}`\\n"
        message += f"🔹 **Host:** {lobby_info.host_name}\\n"
        message += f"🔹 **Mode:** {lobby_info.game_mode}\\n"
        message += f"🔹 **Players:** {lobby_info.current_players}/{lobby_info.max_players}\\n"
        message += f"🔹 **Region:** {lobby_info.region}\\n\\n"
        message += f"🔗 **Quick Join:** https://kingdom-game.com/join/{lobby_info.lobby_code}"
        
        return message
    
    def handle_join_request(self, join_secret: str) -> Optional[str]:
        """Handle Discord join request and extract lobby code."""
        try:
            # In production, this would decode the join secret
            # For now, assume the secret contains the lobby code
            return join_secret  # Simplified implementation
            
        except Exception as e:
            print(f"Discord join request error: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from Discord RPC."""
        if self.is_connected:
            try:
                # self.rpc.close()
                print("Discord RPC: Disconnected")
                self.is_connected = False
            except Exception as e:
                print(f"Discord disconnect error: {e}")


# Global Discord integration instance
discord_integration = DiscordIntegration()


def get_discord_integration() -> DiscordIntegration:
    """Get the global Discord integration instance."""
    return discord_integration


def create_lobby_info(lobby_code: str, host_name: str, current_players: int, 
                     max_players: int, game_mode: str, region: str) -> DiscordLobbyInfo:
    """Create Discord lobby info from lobby data."""
    return DiscordLobbyInfo(
        lobby_code=lobby_code,
        host_name=host_name,
        current_players=current_players,
        max_players=max_players,
        game_mode=game_mode,
        region=region,
        join_secret=f"join_{lobby_code}"  # Simple join secret format
    )


def format_lobby_for_clipboard(lobby_code: str, host_name: str, game_mode: str, 
                              current_players: int, max_players: int) -> str:
    """Format lobby information for clipboard sharing."""
    return (f"Join my Kingdom Cleanup lobby!\\n"
            f"Code: {lobby_code}\\n"
            f"Host: {host_name}\\n" 
            f"Mode: {game_mode}\\n"
            f"Players: {current_players}/{max_players}")
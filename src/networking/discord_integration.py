"""
Discord integration for Kingdom Cleanup multiplayer system.
Handles Rich Presence, lobby sharing, and Discord-based invitations.
"""

import time
import json
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

try:
    import pypresence
    PYPRESENCE_AVAILABLE = True
except ImportError:
    PYPRESENCE_AVAILABLE = False
    print("pypresence not available - Discord integration will be simulated")

try:
    from discord_config import DISCORD_CLIENT_ID, DISCORD_ASSETS, GAME_INFO
except ImportError:
    # Fallback configuration
    DISCORD_CLIENT_ID = "YOUR_DISCORD_CLIENT_ID_HERE"
    DISCORD_ASSETS = {
        "large_image": "kingdom_logo",
        "menu_icon": "menu_icon", 
        "multiplayer_icon": "multiplayer_icon",
        "playing_icon": "playing_icon",
    }
    GAME_INFO = {
        "name": "Kingdom Cleanup",
        "description": "A twin-stick shooter with multiplayer",
        "website": "https://github.com/exporterrormusic/kingdom-pygame",
    }


@dataclass 
class DiscordLobbyInfo:
    """Discord-compatible lobby information."""
    
    def __init__(self, lobby_code: str = "", host_name: str = "", current_players: int = 0, 
                 max_players: int = 4, game_mode: str = "Battle", region: str = "US", 
                 join_secret: str = ""):
        self.lobby_code = lobby_code
        self.host_name = host_name
        self.current_players = current_players
        self.max_players = max_players
        self.game_mode = game_mode
        self.region = region
        self.join_secret = join_secret or f"kingdom_lobby_{lobby_code}"
    

class DiscordIntegration:
    """Discord Rich Presence and lobby integration."""
    
    def __init__(self):
        self.is_connected = False
        self.client_id = DISCORD_CLIENT_ID
        self.current_activity = None
        self.start_timestamp = int(time.time())
        self.rpc = None
        
        # Try to initialize Discord RPC
        self._initialize_discord()
        
    def _initialize_discord(self):
        """Initialize Discord Rich Presence."""
        if not PYPRESENCE_AVAILABLE:
            print("Discord RPC: pypresence not available - using simulation mode")
            self.is_connected = False
            return
            
        if self.client_id == "YOUR_DISCORD_CLIENT_ID_HERE":
            print("Discord RPC: Please set your Discord Client ID in discord_config.py")
            print("Get it from: https://discord.com/developers/applications")
            self.is_connected = False
            return
            
        try:
            print(f"Discord RPC: Attempting to connect with Client ID: {self.client_id}")
            self.rpc = pypresence.Presence(self.client_id)
            self.rpc.connect()
            
            print("Discord RPC: Successfully connected!")
            self.is_connected = True
            
            # Note: Join event handling requires additional setup
            # Discord join requests work through Rich Presence activity settings
            # The join secret in activity enables the "Join" button for friends
            print("Discord RPC: Join functionality enabled via Rich Presence")
            
            # Set initial presence
            self.update_main_menu_presence()
            
        except Exception as e:
            print(f"Discord RPC: Connection failed - {e}")
            print("Make sure Discord is running and your Client ID is correct")
            self.is_connected = False
            self.rpc = None
    
    def update_main_menu_presence(self):
        """Update presence for main menu state."""
        activity = {
            "details": "In Main Menu",
            "state": "Browsing Options",
            "start": self.start_timestamp,
            "large_image": DISCORD_ASSETS["large_image"],
            "large_text": GAME_INFO["name"],
            "small_image": DISCORD_ASSETS["menu_icon"],
            "small_text": "Main Menu"
        }
        
        self._update_activity(activity)
    
    def update_lobby_presence(self, lobby_info: DiscordLobbyInfo):
        """Update presence for multiplayer lobby."""
        activity = {
            "details": f"{lobby_info.game_mode} Lobby",
            "state": f"{lobby_info.current_players}/{lobby_info.max_players} Players",
            "start": self.start_timestamp,
            "large_image": DISCORD_ASSETS["large_image"], 
            "large_text": GAME_INFO["name"],
            "small_image": DISCORD_ASSETS["multiplayer_icon"],
            "small_text": f"Lobby: {lobby_info.lobby_code}",
            "party_id": lobby_info.lobby_code,
            "party_size": [lobby_info.current_players, lobby_info.max_players],
            # Use join secret for Discord's join button
            "join": f"kingdom_lobby_{lobby_info.lobby_code}",
            # Note: Cannot use buttons with join secrets - Discord automatically shows "Join" button
        }
        
        self._update_activity(activity)
    
    def update_game_presence(self, game_mode: str, level_name: str, player_count: int):
        """Update presence for active gameplay."""
        activity = {
            "details": f"Playing {game_mode}",
            "state": f"Level: {level_name}",
            "start": int(time.time()),
            "large_image": DISCORD_ASSETS["large_image"],
            "large_text": GAME_INFO["name"], 
            "small_image": DISCORD_ASSETS["playing_icon"],
            "small_text": f"{player_count} Player{'s' if player_count != 1 else ''}"
        }
        
        if player_count > 1:
            activity["party_size"] = [player_count, 4]
        
        self._update_activity(activity)
    
    def clear_presence(self):
        """Clear Discord presence."""
        if self.is_connected and self.rpc:
            try:
                self.rpc.clear()
                print("Discord RPC: Presence cleared")
            except Exception as e:
                print(f"Discord RPC: Clear failed - {e}")
    
    def _update_activity(self, activity: Dict[str, Any]):
        """Internal method to update Discord activity."""
        if not self.is_connected or not self.rpc:
            print(f"Discord RPC: Simulated update - {activity['details']}: {activity['state']}")
            self.current_activity = activity
            return
            
        try:
            # Filter out None values and clean up activity
            clean_activity = self._clean_activity(activity)
            self.rpc.update(**clean_activity)
            print(f"Discord RPC: Updated activity - {activity['details']}: {activity['state']}")
            self.current_activity = activity
            
        except Exception as e:
            print(f"Discord RPC: Update failed - {e}")
            
    def _clean_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Clean activity dict by removing None values and invalid fields."""
        clean = {}
        for key, value in activity.items():
            if value is not None:
                if isinstance(value, dict):
                    clean_nested = {k: v for k, v in value.items() if v is not None}
                    if clean_nested:  # Only add if not empty
                        clean[key] = clean_nested
                else:
                    clean[key] = value
        return clean
    
    def get_friends_playing(self, game_name: str) -> List[Dict[str, Any]]:
        """
        Get list of Discord friends currently playing the specified game.
        NOTE: This requires additional Discord permissions and OAuth setup.
        For now, returns empty list - friends API requires special Discord approval.
        """
        # Discord friends API requires additional permissions and OAuth setup
        # that goes beyond basic Rich Presence. This would require:
        # 1. Discord application approval for friends access
        # 2. OAuth2 flow for user authorization  
        # 3. Additional scopes: 'identify' and potentially 'relationships.read'
        # 4. User consent for friends list access
        
        # For now, return empty list to avoid showing fake data
        return []
    
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
            print(f"Processing Discord join request: {join_secret}")
            
            # Handle our custom join secret format
            if join_secret.startswith("kingdom_lobby_"):
                lobby_code = join_secret.replace("kingdom_lobby_", "")
                print(f"Extracted lobby code: {lobby_code}")
                return lobby_code
            
            # Fallback - assume the secret contains the lobby code
            return join_secret
            
        except Exception as e:
            print(f"Discord join request error: {e}")
            return None
    
    def _handle_join_event(self, data):
        """Handle Discord join events from RPC."""
        try:
            join_secret = data.get('secret', '') or data.get('join_secret', '')
            if join_secret:
                lobby_code = self.handle_join_request(join_secret)
                if lobby_code:
                    print(f"Discord join event processed - Lobby Code: {lobby_code}")
                    # TODO: Notify main game to join lobby
                    # This would typically be handled by a callback system
                    self._notify_game_of_join_request(lobby_code)
        except Exception as e:
            print(f"Error handling Discord join event: {e}")
    
    def _notify_game_of_join_request(self, lobby_code: str):
        """Notify the main game that a Discord join was requested."""
        # This is where we'd integrate with the main game loop
        # For now, just log it - integration would require main game support
        print(f"DISCORD JOIN REQUESTED: {lobby_code}")
        print("To implement: Main game should auto-navigate to join screen with this code")
    
    def disconnect(self):
        """Disconnect from Discord RPC."""
        if self.is_connected and self.rpc:
            try:
                self.rpc.close()
                print("Discord RPC: Disconnected")
                self.is_connected = False
                self.rpc = None
            except Exception as e:
                print(f"Discord disconnect error: {e}")
        else:
            print("Discord RPC: Already disconnected")


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
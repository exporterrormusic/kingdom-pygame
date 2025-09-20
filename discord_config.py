"""
Discord configuration for Kingdom-Pygame.
Replace DISCORD_CLIENT_ID with your actual Discord application ID.
"""

# TODO: Replace this with your actual Discord Application ID from Discord Developer Portal
# Get it from: https://discord.com/developers/applications -> Your Application -> General Information -> Application ID
DISCORD_CLIENT_ID = "YOUR_DISCORD_CLIENT_ID_HERE"

# Rich Presence asset names (these should match what you uploaded to Discord Developer Portal)
DISCORD_ASSETS = {
    "large_image": "kingdom_logo",        # Main game logo
    "menu_icon": "menu_icon",            # Menu/browsing icon
    "multiplayer_icon": "multiplayer_icon", # Multiplayer lobby icon
    "playing_icon": "playing_icon",       # In-game playing icon
}

# Game information for Discord Rich Presence
GAME_INFO = {
    "name": "Kingdom Cleanup",
    "description": "A twin-stick shooter with multiplayer",
    "website": "https://github.com/exporterrormusic/kingdom-pygame",  # Your game's URL
}
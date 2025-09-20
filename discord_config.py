"""
Discord configuration for Kingdom-Pygame.
Replace DISCORD_CLIENT_ID with your actual Discord application ID.
"""

# TODO: Replace this with your actual Discord Application ID from Discord Developer Portal
# Get it from: https://discord.com/developers/applications -> Your Application -> General Information -> Application ID
DISCORD_CLIENT_ID = "1418843255847784501"

# Rich Presence asset names (these should match what you uploaded to Discord Developer Portal)
DISCORD_ASSETS = {
    "large_image": "twitchcrown",        # Main game logo (matches your uploaded asset)
    "menu_icon": "twitchcrown",          # Menu/browsing icon (using same image)
    "multiplayer_icon": "twitchcrown",   # Multiplayer lobby icon (using same image)
    "playing_icon": "twitchcrown",       # In-game playing icon (using same image)
}

# Game information for Discord Rich Presence
GAME_INFO = {
    "name": "Kingdom Cleanup",
    "description": "A twin-stick shooter with multiplayer",
    "website": "https://github.com/exporterrormusic/kingdom-pygame",  # Your game's URL
}
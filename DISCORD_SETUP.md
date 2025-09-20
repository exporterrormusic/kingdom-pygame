# Discord Integration Setup Instructions

## Step 1: Create Discord Application

1. Go to **https://discord.com/developers/applications**
2. Log in with your Discord account
3. Click **"New Application"**
4. Name it: `Kingdom Cleanup` (or your preferred name)
5. Click **"Create"**

## Step 2: Get Your Client ID

1. On the **General Information** tab, find **Application ID**
2. **Copy this ID** (it will be a long number like `1234567890123456789`)
3. Open `discord_config.py` in your Kingdom-Pygame folder
4. Replace `YOUR_DISCORD_CLIENT_ID_HERE` with your actual Application ID

Example:
```python
DISCORD_CLIENT_ID = "1234567890123456789"  # Replace with your actual ID
```

## Step 3: Set Up Rich Presence Assets (Optional)

1. In Discord Developer Portal, go to **Rich Presence** tab
2. Upload images for your game:
   - **kingdom_logo**: Your main game logo (512x512 recommended)
   - **menu_icon**: Icon for menu/browsing (256x256)
   - **multiplayer_icon**: Icon for multiplayer lobbies (256x256)  
   - **playing_icon**: Icon for active gameplay (256x256)
3. Use the exact names above as the **Asset Name** when uploading

## Step 4: Test the Integration

1. Make sure Discord is running on your computer
2. Run Kingdom-Pygame
3. Go to **Online Multiplayer** → **Settings**
4. Click **"Connect Discord"**
5. You should see "Connected to Discord successfully!"
6. Your Discord status should show "Kingdom Cleanup - In Main Menu"

## Step 5: Test Lobby Features

1. Create a lobby in the game
2. Your Discord status should update to show the lobby
3. Try the "Share to Discord" feature (copies lobby code to clipboard)
4. Other Discord users can paste and use the lobby code to join

## Troubleshooting

- **"Failed to connect to Discord"**: Make sure Discord is running and your Client ID is correct
- **"Discord integration not available"**: Dependencies not installed - run the game, it should show installation status
- **Rich Presence not showing**: Discord assets may not be uploaded or names don't match exactly

## Advanced Features (Coming Soon)

- Join from Discord (requires additional setup)
- Discord friends integration  
- Automatic invites through Discord

## Support

If you have issues, check the console output for detailed error messages.
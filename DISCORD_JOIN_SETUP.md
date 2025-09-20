# Discord Join Button Setup Guide

## Overview 🎯

This guide explains how to enable the "Join" button in Discord Rich Presence so friends can join your game lobbies directly from Discord.

## Current Implementation Status ✅

### **What's Already Working:**
- ✅ Rich Presence shows lobby information
- ✅ Party information (player count, lobby ID)
- ✅ Join secret generation
- ✅ Join request handling code

### **What Needs Setup:**
- ⚙️ Discord Application OAuth2 configuration
- ⚙️ Join request permission in Discord Developer Portal

---

## Step-by-Step Setup 🛠️

### **Step 1: Discord Developer Portal Setup**

1. Go to **https://discord.com/developers/applications**
2. Select your **Kingdom Cleanup** application
3. Go to **OAuth2** tab in the left sidebar

### **Step 2: Configure OAuth2 Settings**

1. **Scopes**: Check these boxes:
   - `applications.commands`
   - `rpc`
   - `rpc.activities.write`

2. **Redirect URIs**: Add:
   ```
   http://localhost:3000/auth/discord/callback
   ```

3. **Copy the Client ID** (you already have this)

### **Step 3: Enable Rich Presence Join**

1. Still in Discord Developer Portal
2. Go to **Rich Presence** tab
3. **Enable "Rich Presence Join Requests"**
4. Save changes

### **Step 4: Test the Join Button**

1. **Start your game** with Discord running
2. **Create a lobby** 
3. **Check your Discord profile** - friends should see:
   - Your game status: "Kingdom Cleanup - Survival Lobby (2/4 Players)"
   - A **"Join Game"** button or "Ask to Join" option

---

## How It Works 🔧

### **When You Create a Lobby:**
```
Discord Status: "Kingdom Cleanup - Survival Lobby (2/4 Players)"
Join Secret: "kingdom_lobby_FIRE-WOLF-2024"
```

### **When Friend Clicks Join:**
1. Discord sends join request to your game
2. Game extracts lobby code from join secret
3. Friend's game auto-navigates to join screen
4. Lobby code is pre-filled

### **Join Process Flow:**
```
Friend sees your status → Clicks "Join" → Discord sends request → 
Your game gets notified → Friend's game opens join screen
```

---

## Troubleshooting 🔍

### **No Join Button Visible:**
- ✅ Check Discord Developer Portal OAuth2 settings
- ✅ Make sure "Rich Presence Join Requests" is enabled
- ✅ Verify your Discord Client ID is correct
- ✅ Restart Discord and your game

### **Join Button Doesn't Work:**
- ✅ Check console for "Discord join request received" messages
- ✅ Make sure both players have the game installed
- ✅ Verify network connectivity for lobby joining

### **"Ask to Join" Instead of Direct Join:**
- This is normal Discord behavior for some applications
- Player clicks "Ask to Join" → You approve → They get lobby code

---

## Advanced Features 🚀

### **Future Enhancements:**
- **Auto-accept join requests** from friends
- **Spectator mode** join options
- **Team/party invites** through Discord
- **Cross-game lobby notifications**

### **URL Scheme Integration:**
The game also supports `kingdom-cleanup://join/LOBBY-CODE` URLs that can be:
- Shared in Discord messages
- Used in Discord bot commands  
- Embedded in web pages

---

## Testing Checklist ✔️

- [ ] Discord application created and configured
- [ ] OAuth2 settings enabled with correct scopes
- [ ] Rich Presence Join Requests enabled
- [ ] Game shows "Discord RPC: Successfully connected!"
- [ ] Creating lobby updates Discord status
- [ ] Friends can see your lobby status
- [ ] Join button/option appears for friends
- [ ] Console shows join request messages when tested

---

## Current Limitations 📝

1. **Manual approval may be required** - Discord's security model
2. **Both players need the game** - Can't join if game not installed
3. **Network connectivity required** - For actual lobby joining
4. **Platform-specific** - Currently works on Windows with Discord desktop

---

## Need Help? 🆘

Check the console output for detailed Discord RPC messages:
- `Discord RPC: Successfully connected!` - ✅ Good
- `Discord join request received: ...` - ✅ Join working
- `Discord RPC: Connection failed` - ❌ Check setup

The join functionality is **implemented and ready** - just needs the Discord Developer Portal configuration!
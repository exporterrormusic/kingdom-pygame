"""
Test different Discord asset names to find what works.
"""

from src.networking.discord_integration import DiscordIntegration
import time

# Test different possible asset names
test_assets = [
    "large_image",      # Default Discord name
    "kingdom_logo",     # Current config
    "logo",            # Simple name
    "game_logo",       # Common naming
    "main",            # Simple
    None               # No image (should work)
]

print("Testing Discord asset names...")
print("=" * 50)

for asset_name in test_assets:
    print(f"\n🔍 Testing asset: '{asset_name}'")
    
    try:
        discord = DiscordIntegration()
        time.sleep(2)
        
        # Create custom activity with test asset
        if asset_name:
            activity = {
                "details": "Testing Assets",
                "state": f"Asset: {asset_name}",
                "large_image": asset_name,
                "large_text": "Kingdom Cleanup"
            }
        else:
            activity = {
                "details": "Testing No Asset",
                "state": "No image should show",
            }
        
        discord._update_activity(activity)
        print(f"✅ Asset '{asset_name}' - Check Discord now!")
        time.sleep(5)
        
        discord.disconnect()
        
    except Exception as e:
        print(f"❌ Asset '{asset_name}' failed: {e}")

print("\n" + "=" * 50)
print("Check Discord to see which asset names worked!")
print("Note: It may take a few seconds for Discord to update the image.")
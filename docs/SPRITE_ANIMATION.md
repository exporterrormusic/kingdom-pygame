# Sprite Animation System Guide

## Overview

The Kingdom-Pygame game now supports **sprite sheet animations** for character avatars! You can use your 3x4 grid sprite sheets, or the game will automatically fall back to geometric rendering if no sprites are provided.

## How It Works

### **Manual Sprite Sheet Slicing**
Pygame doesn't have built-in automatic animation, so our system:
1. **Automatically slices** your 3x4 sprite sheet into individual frames
2. **Maps animations** to movement directions (DOWN, LEFT, RIGHT, UP)
3. **Handles timing** and frame transitions
4. **Integrates seamlessly** with existing game systems

### **3x4 Grid Format**
```
Row 0: DOWN animation  (3 frames)
Row 1: LEFT animation  (3 frames)  
Row 2: RIGHT animation (3 frames)
Row 3: UP animation    (3 frames)
```

## Using Sprites

### **1. Basic Setup**
```python
# Place your sprite sheet in assets/images/
from src.animated_player import AnimatedPlayer

# Create player with sprites (32x32 pixel frames)
player = AnimatedPlayer(x=400, y=300, 
                       sprite_sheet_path="assets/images/character.png",
                       frame_width=32, 
                       frame_height=32)
```

### **2. Fallback Support**
```python
# Create player without sprites (uses geometric shapes)
player = AnimatedPlayer(x=400, y=300)  # No sprite_sheet_path
```

### **3. Standalone Animated Sprites**
```pythonww
from src.sprite_animation import create_animated_sprite

# For NPCs, enemies, etc.
sprite = create_animated_sprite("character.png", x=200, y=150, 
                               frame_width=32, frame_height=32)
```

## File Structure

```
Kingdom-Pygame/
├── assets/
│   └── images/
│       ├── character.png      # Your 3x4 sprite sheet
│       ├── enemy.png         # Enemy sprites
│       └── example_character.png  # Generated test sprite
├── src/
│   ├── sprite_animation.py   # Core animation system
│   └── animated_player.py    # Enhanced player with sprites
└── test_sprites.py          # Testing and examples
```

## Animation Features

### **Automatic Direction Detection**
- **Movement-based**: Animations automatically play based on WASD input
- **Direction priority**: Horizontal movement takes precedence over vertical
- **Idle state**: Animation stops when not moving

### **Integration with Existing Systems**
- ✅ **Camera shake**: Works with sprite rendering
- ✅ **Hit flash**: Red tint overlay on sprites when hit
- ✅ **Dash effects**: Compatible with existing particle system
- ✅ **Health bars**: Positioned correctly above sprites
- ✅ **Collision detection**: Uses sprite dimensions

### **Performance Optimized**
- **Pre-sliced frames**: Sprite sheet sliced once at initialization
- **Efficient rendering**: Only current frame is drawn
- **Fallback mode**: Zero performance impact if no sprites used

## Classes Overview

### **`SpriteAnimation`**
- Core animation handler
- Manages frame timing and transitions
- Supports customizable animation speed

### **`AnimatedSprite`** 
- Standalone animated sprite
- Perfect for NPCs, enemies, pickups
- Automatic movement-based animation

### **`AnimatedPlayer`**
- Enhanced player class with sprite support
- **Backward compatible** with existing game code
- Falls back to geometric rendering if needed

## Usage Examples

### **Replace Existing Player**
```python
# In main.py, replace:
from src.player import Player
player = Player(x, y)

# With:
from src.animated_player import AnimatedPlayer  
player = AnimatedPlayer(x, y, "assets/images/character.png", 32, 32)
```

### **Custom Animation Speed**
```python
# Slower animation (0.2 seconds per frame)
player = AnimatedPlayer(x, y, "character.png", 32, 32)
player.animated_sprite.animation.animation_speed = 0.2

# Faster animation (0.1 seconds per frame)
player.animated_sprite.animation.animation_speed = 0.1
```

### **Manual Animation Control**
```python
# Force specific animation
player.animated_sprite.animation.play_animation('up')

# Stop animation
player.animated_sprite.animation.stop_animation()
```

## Testing

Run the sprite test to verify everything works:
```bash
python test_sprites.py
```

This will:
- Create an example sprite sheet
- Test both sprite and geometric rendering
- Verify all animation features work correctly

## Adding Your Own Sprites

1. **Create/obtain** a sprite sheet in 3x4 grid format
2. **Save** it in `assets/images/` directory  
3. **Update** your player creation code to use the sprite path
4. **Adjust** `frame_width` and `frame_height` to match your sprites
5. **Test** with the existing game systems

The system is designed to be **drop-in compatible** - your existing game will continue working, but now with beautiful animated sprites!
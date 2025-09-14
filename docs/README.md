# Kingdom - Twin-Stick Shooter

A fast-paced top-down twin-stick shooter game built with Pygame CE. Fight waves of enemies in an arena-style battleground!

## Features

- **Twin-stick controls**: Move with WASD/arrows, aim with mouse
- **Single-press dashing**: Press Shift while moving to dash once (not continuous)
- **Multiple enemy types**: Basic, Fast, and Tank enemies with different behaviors
- **Wave-based progression**: Enemies get stronger and more numerous over time
- **Particle effects**: Visual feedback for hits, explosions, and damage
- **Score system**: Earn points by defeating enemies
- **Game states**: Menu, pause, and game over screens

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
1. Clone or download this project
2. Navigate to the project directory:
   ```bash
   cd Kingdom-Pygame
   ```

3. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   ```

4. Activate the virtual environment:
   - **Windows**: `.venv\Scripts\activate`
   - **macOS/Linux**: `source .venv/bin/activate`

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Play

### Running the Game
```bash
python main.py
```

### Controls
- **WASD** or **Arrow Keys**: Move your character
- **Mouse**: Aim your weapon
- **Left Mouse Button**: Shoot
- **Shift** (while moving): Dash once per key press in movement direction
- **P**: Pause/unpause the game
- **ESC**: Pause (during game) or quit (from menu)

### Gameplay
- Survive waves of enemies that spawn from the edges of the screen
- Different enemy types have different speeds, health, and damage
- Your health regenerates slowly when not taking damage
- Score points by defeating enemies (100 points per enemy)
- Waves get progressively harder with more enemies and tougher types

### Enemy Types
- **Red (Basic)**: Standard enemy with moderate speed and health
- **Orange (Fast)**: Quick enemies with lower health - marked with triangle
- **Purple (Tank)**: Slow but tough enemies with high health - marked with square

## Project Structure

```
Kingdom-Pygame/
├── main.py              # Main game entry point
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── src/                # Source code
│   ├── __init__.py     # Package initialization
│   ├── player.py       # Player character class
│   ├── bullet.py       # Bullet system and physics
│   ├── enemy.py        # Enemy AI and behavior
│   ├── collision.py    # Collision detection and effects
│   └── game_states.py  # Menu and game state management
├── assets/             # Game assets
│   ├── images/         # Sprite images (currently using procedural graphics)
│   ├── sounds/         # Sound effects and music
│   └── README.md       # Asset guidelines
└── config/             # Configuration files (reserved for future use)
```

## Development

### Code Structure
- **Object-oriented design** with separate classes for different game entities
- **Component-based architecture** with managers for bullets, enemies, collisions
- **State machine** for game flow (menu → playing → game over)
- **Frame-rate independent** movement using delta time

### Key Components
- `Player`: Handles twin-stick movement and aiming mechanics
- `BulletManager`: Manages bullet lifecycle, physics, and rendering
- `EnemyManager`: Spawns enemies and handles AI behavior  
- `CollisionManager`: Detects and responds to collisions between objects
- `StateManager`: Controls game flow between menu, gameplay, and game over
- `EffectsManager`: Particle effects for visual feedback

### Performance Features
- Efficient collision detection using pygame rectangles and distance checks
- Object pooling for bullets and particles
- Optimized rendering with minimal draw calls
- Delta time-based updates for smooth 60 FPS gameplay

## Future Enhancements

- [ ] Sound effects and background music
- [ ] Power-ups and weapon upgrades
- [ ] Multiple weapon types
- [ ] Boss enemies
- [ ] High score persistence
- [ ] Multiple levels/arenas
- [ ] Cooperative multiplayer
- [ ] Better graphics and animations

## Technical Details

- **Engine**: Pygame CE (Community Edition)
- **Language**: Python 3.8+
- **Resolution**: 1920x1080 (Full HD)
- **Architecture**: Object-oriented with component managers
- **Graphics**: 2D vector-based rendering
- **Physics**: Custom implementation for bullets and movement
- **AI**: Basic state machine for enemy behavior

## Contributing

Feel free to contribute improvements, bug fixes, or new features! Areas that could use enhancement:
- Graphics and visual effects
- Sound design
- Additional enemy types or behaviors
- Performance optimizations
- New gameplay features

## License

This project is open source. Feel free to use, modify, and distribute as needed.

## Credits

Built with Pygame CE - the community edition of Pygame with modern features and improvements.

---

Have fun playing Kingdom! 🎮
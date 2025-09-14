# Dash System Implementation

## Overview
Added a dash mechanic to the twin-stick shooter that allows players to quickly move in the direction they're holding WASD keys by pressing Shift.

## Features Added

### Dash Mechanics
- **Trigger**: Press Shift while moving with WASD (single press, not continuous)
- **No Cooldown**: Can dash again immediately after releasing and pressing Shift
- **Distance**: 150 pixels per dash
- **Duration**: 0.15 seconds (quick burst movement)
- **Direction**: Follows WASD input direction, supports diagonals

### Visual Feedback
- **Player appearance**: Turns white while dashing
- **Trail effect**: Semi-transparent trail behind player during dash
- **No cooldown indicator**: Removed cooldown mechanics for unlimited dashing

### Particle Effects
- **Dash trail**: Blue particles spawn behind the player when dashing
- **Integration**: Uses existing effects manager system

## Technical Implementation

### Player Class Changes (`src/player.py`)
- Added dash state variables (duration, velocity)
- Removed cooldown mechanics for unlimited dashing
- `try_dash()`: Handles dash initiation and direction calculation (no cooldown check)
- Updated `handle_input()`: Detects Shift key press
- Updated `update()`: Manages dash state and movement
- Updated `render()`: Visual feedback for dashing state (removed cooldown indicator)

### Main Game Changes (`main.py`)
- Updated resolution to 1920x1080
- Pass `effects_manager` to player input handling
- Removed dash cooldown display from UI
- Updated boundary checking for new resolution
- Added Shift controls to help text

### Effects System (`src/collision.py`)
- Added `add_dash_effect()`: Creates particle trail during dash

## Controls Updated
- **WASD/Arrows**: Move
- **Mouse**: Aim and shoot
- **Shift (while moving)**: Dash in movement direction
- **P**: Pause
- **ESC**: Quit/Menu

## Gameplay Impact
- **Controlled mobility**: Players can dash precisely without accidental continuous dashing
- **Tactical timing**: Each dash requires a deliberate key press for strategic movement
- **Positioning**: Quick repositioning for better shooting angles  
- **Responsive gameplay**: Immediate response to danger with single key presses
- **Balanced movement**: Prevents dash-spamming while maintaining mobility

## UI Scaling for 1920x1080
- **Larger fonts**: All UI text scaled up for better readability at higher resolution
- **Bigger health bars**: Player and enemy health bars increased in size
- **Better positioning**: UI elements repositioned and spaced for larger screen
- **Improved visibility**: Menu text, game over screens, and pause overlays all scaled appropriately

## Code Quality
- **Simplified design**: Removed complexity of cooldown management
- **Modular design**: Dash system integrates cleanly with existing code
- **Configurable**: Easy to adjust dash distance and duration
- **Visual polish**: Multiple layers of feedback (color, trail, particles)
- **Performance**: Minimal impact on frame rate
- **Scalable**: Works seamlessly with new 1920x1080 resolution

The dash system enhances the twin-stick shooter gameplay with unlimited tactical movement options while maintaining the game's fast-paced feel!
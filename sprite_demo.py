"""
Example integration showing how to use animated sprites in the main game.
This demonstrates switching from geometric to sprite rendering.
"""

import pygame as pg
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the animated player instead of regular player
try:
    from src.animated_player import AnimatedPlayer
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append('src')
    from animated_player import AnimatedPlayer

from src.bullet import BulletManager
from src.enemy import EnemyManager
from src.collision import CollisionManager, EffectsManager
from src.game_states import StateManager, GameState

# Game constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
BACKGROUND_COLOR = (20, 20, 40)
FPS = 60

class SpriteDemo:
    """Demonstration of sprite integration in the game."""
    
    def __init__(self):
        """Initialize the sprite demo."""
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Kingdom-Pygame - Sprite Animation Demo")
        self.clock = pg.time.Clock()
        
        # Create both types of players for comparison
        self.geometric_player = AnimatedPlayer(300, 400)  # No sprites
        self.sprite_player = AnimatedPlayer(600, 400, 
                                          "assets/images/example_character.png", 
                                          32, 32)  # With sprites
        
        # Current active player
        self.current_player = self.sprite_player
        
        # Game systems
        self.bullet_manager = BulletManager()
        self.enemy_manager = EnemyManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.effects_manager = EffectsManager()
        self.collision_manager = CollisionManager(self.effects_manager)
        
        # Camera shake system
        self.camera_shake_intensity = 0.0
        self.camera_shake_duration = 0.0
        self.camera_offset = pg.Vector2(0, 0)
        
        # Game state
        self.running = True
        self.dt = 0.0
        
    def add_camera_shake(self, intensity: float, duration: float):
        """Add camera shake effect."""
        self.camera_shake_intensity = max(self.camera_shake_intensity, intensity)
        self.camera_shake_duration = max(self.camera_shake_duration, duration)
    
    def update_camera_shake(self, dt: float):
        """Update camera shake effect."""
        if self.camera_shake_duration > 0:
            self.camera_shake_duration -= dt
            
            # Calculate shake offset
            import random
            shake_amount = self.camera_shake_intensity * (self.camera_shake_duration / 0.5)
            self.camera_offset.x = random.uniform(-shake_amount, shake_amount)
            self.camera_offset.y = random.uniform(-shake_amount, shake_amount)
            
            if self.camera_shake_duration <= 0:
                self.camera_offset = pg.Vector2(0, 0)
        else:
            self.camera_offset = pg.Vector2(0, 0)
    
    def handle_events(self):
        """Handle game events."""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
                elif event.key == pg.K_SPACE:
                    # Switch between geometric and sprite player
                    if self.current_player == self.geometric_player:
                        self.current_player = self.sprite_player
                        print("Switched to sprite player")
                    else:
                        self.current_player = self.geometric_player
                        print("Switched to geometric player")
                    
        # Handle input for current player
        keys = pg.key.get_pressed()
        mouse_pos = pg.mouse.get_pos()
        mouse_buttons = pg.mouse.get_pressed()
        
        # Player input
        self.current_player.handle_input(keys, mouse_pos, 0.0, 
                                       self.effects_manager, 
                                       self.add_camera_shake)
        
        # Shooting
        if mouse_buttons[0]:  # Left mouse button
            gun_tip = self.current_player.get_gun_tip_position()
            self.bullet_manager.shoot(gun_tip.x, gun_tip.y, 
                                    self.current_player.angle, 0.0)
    
    def update(self):
        """Update game logic."""
        # Update camera shake
        self.update_camera_shake(self.dt)
        
        # Update players (both for demonstration)
        self.geometric_player.update(self.dt)
        self.sprite_player.update(self.dt)
        
        # Update game systems
        self.bullet_manager.update(self.dt)
        self.enemy_manager.update(self.dt, self.current_player.pos, 0.0)
        self.effects_manager.update(self.dt)
        
        # Handle collisions
        kills = self.collision_manager.check_bullet_enemy_collisions(
            self.bullet_manager, self.enemy_manager)
        
        # Check player-enemy collisions
        player_hit = self.collision_manager.check_player_enemy_collisions(
            self.current_player, self.enemy_manager)
        
        if player_hit:
            # Add camera shake and hit flash
            self.add_camera_shake(15.0, 0.4)
            self.current_player.add_hit_flash()
            self.effects_manager.add_hit_effect(
                self.current_player.pos.x, 
                self.current_player.pos.y, 
                (255, 100, 100)
            )
    
    def render(self):
        """Render the game."""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Camera shake offset
        shake_x = int(self.camera_offset.x)
        shake_y = int(self.camera_offset.y)
        offset = (shake_x, shake_y)
        
        # Render both players for comparison (inactive one is transparent)
        if self.current_player == self.sprite_player:
            # Render geometric player with transparency
            temp_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
            self.geometric_player.render(temp_surface, 0.0, offset)
            temp_surface.set_alpha(100)  # Make it semi-transparent
            self.screen.blit(temp_surface, (0, 0))
            
            # Render active sprite player
            self.sprite_player.render(self.screen, 0.0, offset)
        else:
            # Render sprite player with transparency
            temp_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
            self.sprite_player.render(temp_surface, 0.0, offset)
            temp_surface.set_alpha(100)  # Make it semi-transparent
            self.screen.blit(temp_surface, (0, 0))
            
            # Render active geometric player
            self.geometric_player.render(self.screen, 0.0, offset)
        
        # Render game systems
        self.bullet_manager.render(self.screen, offset)
        self.enemy_manager.render(self.screen, offset)
        self.effects_manager.render(self.screen, offset)
        
        # Render UI instructions
        font = pg.font.Font(None, 36)
        instructions = [
            "SPRITE ANIMATION DEMO",
            f"Current Player: {'SPRITE' if self.current_player == self.sprite_player else 'GEOMETRIC'}",
            "",
            "Controls:",
            "WASD - Move",
            "Mouse - Aim",
            "Left Click - Shoot", 
            "Shift - Dash",
            "SPACE - Switch Player Type",
            "ESC - Quit"
        ]
        
        y_offset = 50
        for i, instruction in enumerate(instructions):
            color = (255, 255, 255) if i != 1 else (100, 255, 100)
            if i == 1:  # Highlight current player type
                color = (255, 255, 100)
            
            text = font.render(instruction, True, color)
            self.screen.blit(text, (50, y_offset + i * 40))
        
        pg.display.flip()
    
    def run(self):
        """Main game loop."""
        print("Starting Sprite Animation Demo...")
        print("Press SPACE to switch between geometric and sprite rendering")
        print("Move with WASD to see animations in action!")
        
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update()
            self.render()
        
        pg.quit()
        sys.exit()

if __name__ == "__main__":
    demo = SpriteDemo()
    demo.run()
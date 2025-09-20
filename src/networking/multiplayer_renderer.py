"""
Multiplayer Renderer for Kingdom-Pygame.
Handles rendering of network players and multiplayer-specific effects.
"""

import pygame as pg
import math
from typing import Dict, Tuple, Optional
from .game_synchronizer import PlayerState, BulletState


class MultiplayerRenderer:
    """Renders multiplayer-specific elements like network players."""
    
    def __init__(self, character_manager=None):
        self.character_manager = character_manager
        
        # Cache for network player animated sprites
        self.network_player_sprites = {}  # player_id -> AnimatedSprite
        
        # Network player visual properties
        self.network_player_size = 20
        self.network_player_colors = {
            "Cecil": (150, 100, 255),
            "Commander": (255, 100, 100),
            "Crown": (100, 255, 100),
            "Kilo": (255, 255, 100),
            "Marian": (255, 150, 100),
            "Rapunzel": (255, 100, 255),
            "Scarlet": (200, 50, 50),
            "Sin": (100, 100, 100),
            "Snow White": (255, 255, 255),
            "Trony": (100, 200, 255),
            "Wells": (150, 255, 150)
        }
        
        # Animation interpolation
        self.position_smoothing = 0.8  # How much to smooth position updates
        self.previous_positions = {}   # player_id -> (x, y)
        
        # Name tag settings
        self.name_font = pg.font.Font(None, 24)
        self.name_tag_color = (255, 255, 255)
        self.name_tag_background = (0, 0, 0, 128)
    
    def _get_or_create_sprite(self, player: PlayerState):
        """Get or create animated sprite for network player."""
        if player.player_id not in self.network_player_sprites:
            try:
                # Import here to avoid circular imports
                from src.utils.sprite_animation import SpriteAnimation
                
                # Create sprite animation for this character
                character_id = player.character_id.lower().replace(' ', '-')
                sprite_path = f"assets/images/Characters/{character_id}/{character_id}-sprite.png"
                
                # Check if file exists
                import os
                if not os.path.exists(sprite_path):
                    print(f"[MULTIPLAYER] Sprite file not found: {sprite_path}")
                    # Try alternative character ID format
                    alt_character_id = player.character_id.lower()
                    alt_sprite_path = f"assets/images/Characters/{alt_character_id}/{alt_character_id}-sprite.png"
                    if os.path.exists(alt_sprite_path):
                        print(f"[MULTIPLAYER] Using alternative path: {alt_sprite_path}")
                        character_id = alt_character_id
                        sprite_path = alt_sprite_path
                    else:
                        print(f"[MULTIPLAYER] Alternative path also not found: {alt_sprite_path}")
                        return None
                else:
                    print(f"[MULTIPLAYER] Sprite file found: {sprite_path}")
                
                # Calculate frame dimensions dynamically like the main player does
                import pygame
                temp_sprite = pygame.image.load(sprite_path)
                frame_width = temp_sprite.get_width() // 3  # Assuming 3 frames per row
                frame_height = temp_sprite.get_height() // 4  # Assuming 4 rows (directions)
                
                sprite = SpriteAnimation(sprite_path, frame_width, frame_height, scale_factor=0.2)
                
                if sprite and sprite.frames:
                    self.network_player_sprites[player.player_id] = sprite
                    print(f"[MULTIPLAYER] Successfully created sprite for network player {player.player_id} ({character_id})")
                    return sprite
                else:
                    print(f"[MULTIPLAYER] Failed to load sprite for {character_id} - sprite: {sprite is not None}, frames: {sprite.frames if sprite else 'N/A'}")
                    return None
            except Exception as e:
                print(f"[MULTIPLAYER] Error creating sprite for {player.character_id}: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            sprite = self.network_player_sprites.get(player.player_id)
            return sprite
    
    def render_network_players(self, screen: pg.Surface, players: Dict[str, PlayerState], 
                             camera_offset: Tuple[float, float]):
        """Render all network players."""
        if players:
            # Debug once every few seconds instead of per frame
            import time
            for player_id, player_state in players.items():
                if player_state.is_alive:
                    self._render_network_player(screen, player_state, camera_offset)
    
    def _render_network_player(self, screen: pg.Surface, player: PlayerState, 
                              camera_offset: Tuple[float, float]):
        """Render a single network player."""
        # Apply camera offset
        render_x = int(player.position[0] + camera_offset[0])
        render_y = int(player.position[1] + camera_offset[1])
        
        # Debug: Add more detailed positioning info
        import time
        if not hasattr(self, '_last_pos_debug'):
            self._last_pos_debug = {}
        # Reduced debug logging to every 10 seconds
        current_time = time.time() 
        if player.player_id not in self._last_pos_debug or current_time - self._last_pos_debug.get(player.player_id, 0) > 10:
            self._last_pos_debug[player.player_id] = current_time
            # Only log essential position info
        # Skip if off-screen (with larger margin for debugging)
        margin = 200
        if (render_x < -margin or render_x > screen.get_width() + margin or
            render_y < -margin or render_y > screen.get_height() + margin):
            # Remove off-screen spam
            return
        
        # Try to get or create animated sprite
        sprite_animation = self._get_or_create_sprite(player)
        
        # Add minimal debug for sprite issues (rate limited)
        import time
        if not hasattr(self, '_sprite_debug_time'):
            self._sprite_debug_time = {}
        current_time = time.time()
        if player.player_id not in self._sprite_debug_time or current_time - self._sprite_debug_time.get(player.player_id, 0) > 5.0:
            self._sprite_debug_time[player.player_id] = current_time
            if not sprite_animation or not getattr(sprite_animation, 'frames', None):
                print(f"[SPRITE_ISSUE] Player {player.player_id}: sprite={sprite_animation is not None}, has_frames={getattr(sprite_animation, 'frames', None) is not None}")
        
        if sprite_animation and sprite_animation.frames:
            # Debug logging with rate limiting
            import time
            if not hasattr(self, '_last_debug_time'):
                self._last_debug_time = {}
            # Update animation based on movement
            velocity = pg.Vector2(player.velocity[0], player.velocity[1])
            is_moving = velocity.length() > 0.1
            
            # Debug velocity and movement detection
            if not hasattr(self, '_velocity_debug_time'):
                self._velocity_debug_time = {}
            current_time = time.time()
            if player.player_id not in self._velocity_debug_time or current_time - self._velocity_debug_time[player.player_id] > 2:
                self._velocity_debug_time[player.player_id] = current_time
                print(f"[MULTIPLAYER_RENDER] Player {player.player_id}: velocity=({velocity.x:.2f}, {velocity.y:.2f}), length={velocity.length():.2f}, is_moving={is_moving}")
            
            # Determine direction based on velocity or angle
            if is_moving:
                # Use velocity direction
                if abs(velocity.x) > abs(velocity.y):
                    direction = 'right' if velocity.x > 0 else 'left'
                else:
                    direction = 'down' if velocity.y > 0 else 'up'
            else:
                # Use facing angle
                angle = player.angle % 360
                if 315 <= angle or angle < 45:
                    direction = 'right'
                elif 45 <= angle < 135:
                    direction = 'down'
                elif 135 <= angle < 225:
                    direction = 'left'
                else:
                    direction = 'up'
            
            # Update sprite animation (dt = 1/60 as approximation)
            if is_moving:
                sprite_animation.play_animation(direction)
            else:
                sprite_animation.show_first_frame(direction)
            sprite_animation.update(1/60.0)
            
            # Render the sprite animation
            sprite_animation.render(screen, render_x, render_y, offset=(0, 0))
        else:
            # Fallback to geometric rendering if sprite fails
            self._render_geometric_player(screen, player, render_x, render_y)
        
        # Draw name tag and UI elements
        self._draw_name_tag(screen, render_x, render_y, player.player_name)
        self._draw_health_bar(screen, render_x, render_y, player.health, player.max_health)
    
    def _render_geometric_player(self, screen: pg.Surface, player: PlayerState, render_x: int, render_y: int):
        """Fallback geometric rendering for network players."""
        # Get player color based on character
        color = self.network_player_colors.get(player.character_id, (100, 150, 255))
        outline_color = (255, 255, 255)
        
        # Dash effect
        if player.is_dashing:
            color = (255, 255, 255)
            # Add dash trail
            for i in range(3):
                trail_size = self.network_player_size - (i * 3)
                if trail_size > 0:
                    trail_alpha = int(128 * (1 - i * 0.3))
                    trail_surface = pg.Surface((trail_size * 2, trail_size * 2), pg.SRCALPHA)
                    trail_color = (*color, trail_alpha)
                    pg.draw.circle(trail_surface, trail_color, (trail_size, trail_size), trail_size)
                    screen.blit(trail_surface, (render_x - trail_size, render_y - trail_size))
        
        # Draw player body
        pg.draw.circle(screen, color, (render_x, render_y), self.network_player_size)
        pg.draw.circle(screen, outline_color, (render_x, render_y), self.network_player_size, 2)
        
        # Draw direction indicator
        gun_length = self.network_player_size + 10
        angle_rad = math.radians(player.angle)
        
        end_x = render_x + math.cos(angle_rad) * gun_length
        end_y = render_y + math.sin(angle_rad) * gun_length
        
        pg.draw.line(screen, outline_color, (render_x, render_y), (end_x, end_y), 3)
        
        # Draw aiming arrow
        self._draw_aiming_arrow(screen, render_x, render_y, player.angle, player.is_dashing)
        
        # Draw aiming arrow
        self._draw_aiming_arrow(screen, render_x, render_y, player.angle, player.is_dashing)
        
        # Draw health bar
        self._draw_health_bar(screen, render_x, render_y, player.health, player.max_health)
        
        # Draw name tag
        self._draw_name_tag(screen, render_x, render_y, player.player_id)
        
        # Draw weapon indicator
        self._draw_weapon_indicator(screen, render_x, render_y, player.weapon_type)
    
    def _draw_aiming_arrow(self, screen: pg.Surface, x: int, y: int, angle: float, is_dashing: bool):
        """Draw aiming arrow around player."""
        angle_rad = math.radians(angle)
        arrow_distance = self.network_player_size + 25
        
        # Arrow tip position
        tip_x = x + math.cos(angle_rad) * arrow_distance
        tip_y = y + math.sin(angle_rad) * arrow_distance
        
        # V-shape arrow
        arrow_length = 15
        arrow_width = math.radians(25)
        
        left_angle = angle_rad + arrow_width
        left_x = tip_x - math.cos(left_angle) * arrow_length
        left_y = tip_y - math.sin(left_angle) * arrow_length
        
        right_angle = angle_rad - arrow_width
        right_x = tip_x - math.cos(right_angle) * arrow_length
        right_y = tip_y - math.sin(right_angle) * arrow_length
        
        # Arrow colors
        arrow_color = (255, 255, 150) if is_dashing else (200, 200, 255)
        arrow_outline = (255, 255, 255)
        
        # Draw arrow with outline
        pg.draw.line(screen, arrow_outline, (tip_x, tip_y), (left_x, left_y), 4)
        pg.draw.line(screen, arrow_outline, (tip_x, tip_y), (right_x, right_y), 4)
        pg.draw.line(screen, arrow_color, (tip_x, tip_y), (left_x, left_y), 2)
        pg.draw.line(screen, arrow_color, (tip_x, tip_y), (right_x, right_y), 2)
        
        # Tip dot
        pg.draw.circle(screen, arrow_color, (int(tip_x), int(tip_y)), 2)
    
    def _draw_health_bar(self, screen: pg.Surface, x: int, y: int, health: int, max_health: int):
        """Draw health bar above player."""
        if health >= max_health:
            return  # Don't show full health bars
        
        bar_width = 50
        bar_height = 6
        bar_x = x - bar_width // 2
        bar_y = y - self.network_player_size - 15
        
        # Background
        pg.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        
        # Health bar
        health_ratio = health / max_health
        health_width = health_ratio * bar_width
        
        if health_ratio > 0.6:
            health_color = (0, 255, 0)
        elif health_ratio > 0.3:
            health_color = (255, 255, 0)
        else:
            health_color = (255, 0, 0)
        
        pg.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Border
        pg.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def _draw_name_tag(self, screen: pg.Surface, x: int, y: int, player_id: str):
        """Draw player name tag."""
        # Simplified name (remove host/client prefix)
        display_name = player_id.split('_')[-1] if '_' in player_id else player_id
        if display_name == "host":
            display_name = "Host"
        
        # Render name
        name_surface = self.name_font.render(display_name, True, self.name_tag_color)
        name_rect = name_surface.get_rect()
        name_rect.centerx = x
        name_rect.bottom = y - self.network_player_size - 25
        
        # Background
        bg_rect = name_rect.copy()
        bg_rect.inflate(6, 2)
        bg_surface = pg.Surface((bg_rect.width, bg_rect.height), pg.SRCALPHA)
        bg_surface.fill(self.name_tag_background)
        screen.blit(bg_surface, bg_rect)
        
        # Name text
        screen.blit(name_surface, name_rect)
    
    def _draw_weapon_indicator(self, screen: pg.Surface, x: int, y: int, weapon_type: str):
        """Draw weapon type indicator."""
        # Simple weapon indicators
        weapon_symbols = {
            "Assault Rifle": "AR",
            "Shotgun": "SG",
            "Sniper": "SR",
            "Minigun": "MG",
            "Rocket Launcher": "RL",
            "Sword": "SW"
        }
        
        symbol = weapon_symbols.get(weapon_type, "??")
        weapon_surface = self.name_font.render(symbol, True, (200, 200, 200))
        weapon_rect = weapon_surface.get_rect()
        weapon_rect.centerx = x + self.network_player_size + 20
        weapon_rect.centery = y
        
        # Background circle
        pg.draw.circle(screen, (0, 0, 0, 128), weapon_rect.center, 12)
        pg.draw.circle(screen, (100, 100, 100), weapon_rect.center, 12, 1)
        
        # Symbol
        screen.blit(weapon_surface, weapon_rect)
    
    def render_network_bullets(self, screen: pg.Surface, bullets: Dict[str, BulletState], camera_offset: Tuple[float, float]):
        """Render bullets from network players."""
        for bullet_id, bullet_state in bullets.items():
            render_x = int(bullet_state.position[0] + camera_offset[0])
            render_y = int(bullet_state.position[1] + camera_offset[1])
            
            # Skip if off-screen
            if (render_x < -10 or render_x > screen.get_width() + 10 or
                render_y < -10 or render_y > screen.get_height() + 10):
                continue
            
            # Different visual style based on bullet type
            bullet_color = (255, 255, 100)  # Yellow bullets
            bullet_size = 3
            
            if bullet_state.special_attack:
                bullet_color = (255, 100, 100)  # Red for special attacks
                bullet_size = 5
            
            # Add transparency to distinguish from local bullets
            bullet_surface = pg.Surface((bullet_size * 2, bullet_size * 2), pg.SRCALPHA)
            pg.draw.circle(bullet_surface, (*bullet_color, 180), (bullet_size, bullet_size), bullet_size)
            pg.draw.circle(bullet_surface, (255, 255, 255, 120), (bullet_size, bullet_size), bullet_size, 1)
            
            screen.blit(bullet_surface, (render_x - bullet_size, render_y - bullet_size))
    
    def render_multiplayer_ui(self, screen: pg.Surface, players: Dict[str, PlayerState], local_player_id: str):
        """Render multiplayer-specific UI elements."""
        # Player list in top-right corner
        ui_x = screen.get_width() - 200
        ui_y = 10
        
        # Background panel
        panel_width = 190
        panel_height = min(300, 30 + len(players) * 25)
        panel_surface = pg.Surface((panel_width, panel_height), pg.SRCALPHA)
        panel_surface.fill((0, 0, 0, 128))
        screen.blit(panel_surface, (ui_x, ui_y))
        
        # Title
        title_surface = self.name_font.render("Players", True, (255, 255, 255))
        screen.blit(title_surface, (ui_x + 10, ui_y + 5))
        
        # Player list
        y_offset = 30
        for i, (player_id, player) in enumerate(players.items()):
            if not player.is_alive:
                continue
            
            # Player color dot
            color = self.network_player_colors.get(player.character_id, (100, 150, 255))
            pg.draw.circle(screen, color, (ui_x + 15, ui_y + y_offset + 8), 6)
            
            # Player name
            name = player_id if player_id != local_player_id else f"{player_id} (You)"
            name_surface = pg.font.Font(None, 20).render(name, True, (255, 255, 255))
            screen.blit(name_surface, (ui_x + 30, ui_y + y_offset))
            
            # Health bar
            health_ratio = player.health / player.max_health
            bar_width = 60
            bar_height = 4
            bar_x = ui_x + 120
            bar_y = ui_y + y_offset + 6
            
            # Health bar background
            pg.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
            
            # Health bar fill
            health_color = (0, 255, 0) if health_ratio > 0.6 else (255, 255, 0) if health_ratio > 0.3 else (255, 0, 0)
            pg.draw.rect(screen, health_color, (bar_x, bar_y, bar_width * health_ratio, bar_height))
            
            y_offset += 25
    
    def get_network_player_at_position(self, players: Dict[str, PlayerState], 
                                      world_pos: Tuple[float, float]) -> Optional[str]:
        """Get network player at world position (for targeting/interaction)."""
        x, y = world_pos
        
        for player_id, player in players.items():
            if not player.is_alive:
                continue
            
            px, py = player.position
            distance = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            
            if distance <= self.network_player_size + 5:  # Small margin
                return player_id
        
        return None
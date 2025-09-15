"""
NPC System for Kingdom Pygame
Implements rescue NPCs for mission objectives.
"""

import pygame as pg
import random
import math
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class NPCState:
    """Current state of the NPC."""
    is_rescued: bool = False
    rescue_progress: float = 0.0
    is_being_rescued: bool = False
    rescue_time_required: float = 3.0  # Time to rescue in seconds


class NPC:
    """Non-Player Character for rescue missions."""
    
    def __init__(self, x: float, y: float, character_name: str, character_config=None):
        """Initialize NPC with position and character data."""
        self.pos = pg.Vector2(x, y)
        self.character_name = character_name
        self.character_config = character_config
        self.state = NPCState()
        
        # Visual properties
        self.radius = 35  # Collision radius - increased for better interaction
        self.visual_radius = 40  # Visual rendering radius - increased from 35
        
        # Animation
        self.glow_phase = random.uniform(0, math.pi * 2)
        self.float_phase = random.uniform(0, math.pi * 2)
        self.distress_phase = random.uniform(0, math.pi * 2)
        
        # Rescue interaction
        self.interaction_radius = 100  # Distance for starting rescue - increased from 80
        self.rescue_ui_visible = False
        
        # Load character sprite if available
        self.sprite_surface = None
        self.sprite_frames = None
        self.current_animation_frame = 0
        self.frame_timer = 0.0
        self.frame_rate = 0.15  # Animation speed
        
        self._load_character_sprite()
    
    def _load_character_sprite(self):
        """Load the character sprite for visual representation."""
        if not self.character_name:
            return
            
        # Try to load character sprite
        sprite_path = f"assets/images/Characters/{self.character_name.lower()}/{self.character_name.lower()}-sprite.png"
        if os.path.exists(sprite_path):
            try:
                self.sprite_surface = pg.image.load(sprite_path).convert_alpha()
                
                # Assume 3x4 sprite sheet (3 frames per row, 4 rows)
                if self.sprite_surface:
                    sprite_width = self.sprite_surface.get_width() // 3
                    sprite_height = self.sprite_surface.get_height() // 4
                    
                    # Extract idle animation frames (assume first row)
                    self.sprite_frames = []
                    for frame in range(3):
                        frame_rect = pg.Rect(frame * sprite_width, 0, sprite_width, sprite_height)
                        frame_surface = pg.Surface((sprite_width, sprite_height), pg.SRCALPHA)
                        frame_surface.blit(self.sprite_surface, (0, 0), frame_rect)
                        # Scale to player-like size instead of tiny NPC size
                        scaled_frame = pg.transform.scale(frame_surface, (80, 80))  # Increased from 60x60
                        self.sprite_frames.append(scaled_frame)
            except Exception as e:
                print(f"Failed to load NPC sprite for {self.character_name}: {e}")
    
    def update(self, dt: float, player_pos: pg.Vector2 = None):
        """Update NPC animation and rescue progress."""
        try:
            # Update animation phases
            self.glow_phase += dt * 2.0
            self.float_phase += dt * 1.5
            self.distress_phase += dt * 4.0  # Faster distress animation
            
            # Update sprite animation
            if self.sprite_frames:
                self.frame_timer += dt
                if self.frame_timer >= self.frame_rate:
                    self.frame_timer = 0.0
                    self.current_animation_frame = (self.current_animation_frame + 1) % len(self.sprite_frames)
            
            # Check if player is nearby for rescue interaction
            if player_pos:
                distance = self.pos.distance_to(player_pos)
                self.rescue_ui_visible = distance <= self.interaction_radius and not self.state.is_rescued
                
                # Handle rescue progress
                if self.state.is_being_rescued and distance <= self.interaction_radius:
                    self.state.rescue_progress += dt
                    if self.state.rescue_progress >= self.state.rescue_time_required:
                        self.complete_rescue()
                elif distance > self.interaction_radius:
                    # Reset rescue if player moves away
                    self.state.is_being_rescued = False
                    self.state.rescue_progress = 0.0
        except Exception as e:
            print(f"Error in NPC update for {self.character_name}: {e}")
            import traceback
            traceback.print_exc()
    
    def start_rescue(self):
        """Start the rescue process."""
        if not self.state.is_rescued:
            self.state.is_being_rescued = True
            self.state.rescue_progress = 0.0
    
    def complete_rescue(self):
        """Complete the rescue."""
        self.state.is_rescued = True
        self.state.is_being_rescued = False
        self.rescue_ui_visible = False
        print(f"Successfully rescued {self.character_name}!")
    
    def can_interact(self, player_pos: pg.Vector2) -> bool:
        """Check if player can interact with this NPC."""
        if self.state.is_rescued:
            return False
        distance = self.pos.distance_to(player_pos)
        return distance <= self.interaction_radius
    
    def get_rescue_progress_percent(self) -> float:
        """Get rescue progress as percentage (0-100)."""
        if self.state.rescue_time_required <= 0:
            return 100.0
        return min(100.0, (self.state.rescue_progress / self.state.rescue_time_required) * 100.0)
    
    def render(self, screen: pg.Surface, offset: tuple = (0, 0)):
        """Render the NPC with distress animations."""
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        # Don't render if rescued (they disappear when saved)
        if self.state.is_rescued:
            return
        
        # Floating animation
        float_offset = math.sin(self.float_phase) * 3
        final_y = render_y + float_offset
        
        # Distress glow effect
        glow_intensity = 0.7 + 0.3 * math.sin(self.distress_phase)
        glow_color = (255, 100, 100)  # Red distress glow
        
        if self.state.is_being_rescued:
            # Change to green/yellow during rescue
            rescue_ratio = self.get_rescue_progress_percent() / 100.0
            glow_color = (
                int(255 * (1 - rescue_ratio) + 100 * rescue_ratio),  # Red to green
                int(100 * (1 - rescue_ratio) + 255 * rescue_ratio),  # Low to high green  
                0
            )
        
        # Draw distress glow
        glow_radius = int(self.visual_radius + 10 * glow_intensity)
        glow_surface = pg.Surface((glow_radius * 2, glow_radius * 2), pg.SRCALPHA)
        glow_alpha = int(80 * glow_intensity)
        pg.draw.circle(glow_surface, (*glow_color, glow_alpha), 
                      (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (render_x - glow_radius, final_y - glow_radius))
        
        # Draw character sprite or fallback
        if self.sprite_frames and self.current_animation_frame < len(self.sprite_frames):
            # Render character sprite
            frame = self.sprite_frames[self.current_animation_frame]
            sprite_rect = frame.get_rect(center=(render_x, final_y))
            screen.blit(frame, sprite_rect)
        else:
            # Fallback: simple colored circle with character name initial
            circle_color = (200, 150, 255) if not self.state.is_being_rescued else glow_color
            pg.draw.circle(screen, circle_color, (render_x, int(final_y)), self.visual_radius)
            pg.draw.circle(screen, (255, 255, 255), (render_x, int(final_y)), self.visual_radius, 3)
            
            # Draw character name initial
            if self.character_name:
                font = pg.font.Font(None, 36)
                initial_text = font.render(self.character_name[0].upper(), True, (0, 0, 0))
                text_rect = initial_text.get_rect(center=(render_x, int(final_y)))
                screen.blit(initial_text, text_rect)
        
        # Draw interaction prompt
        if self.rescue_ui_visible:
            self._render_rescue_ui(screen, render_x, final_y - 60)
    
    def _render_rescue_ui(self, screen: pg.Surface, center_x: float, center_y: float):
        """Render rescue interaction UI."""
        font = pg.font.Font(None, 24)
        small_font = pg.font.Font(None, 20)
        
        if not self.state.is_being_rescued:
            # Show "Hold E to Rescue" prompt
            prompt_text = font.render(f"Hold E to Rescue {self.character_name}", True, (255, 255, 255))
            prompt_rect = prompt_text.get_rect(center=(center_x, center_y))
            
            # Background for text
            bg_rect = prompt_rect.inflate(20, 10)
            pg.draw.rect(screen, (0, 0, 0, 180), bg_rect)
            pg.draw.rect(screen, (255, 255, 255), bg_rect, 2)
            
            screen.blit(prompt_text, prompt_rect)
        else:
            # Show rescue progress bar
            progress_percent = self.get_rescue_progress_percent()
            
            # Progress bar background
            bar_width = 120
            bar_height = 12
            bar_rect = pg.Rect(center_x - bar_width // 2, center_y, bar_width, bar_height)
            pg.draw.rect(screen, (50, 50, 50), bar_rect)
            pg.draw.rect(screen, (255, 255, 255), bar_rect, 2)
            
            # Progress bar fill
            fill_width = int(bar_width * progress_percent / 100.0)
            if fill_width > 0:
                fill_rect = pg.Rect(center_x - bar_width // 2, center_y, fill_width, bar_height)
                fill_color = (100, 255, 100)  # Green
                pg.draw.rect(screen, fill_color, fill_rect)
            
            # Progress text
            progress_text = small_font.render(f"Rescuing... {progress_percent:.0f}%", True, (255, 255, 255))
            text_rect = progress_text.get_rect(center=(center_x, center_y - 20))
            screen.blit(progress_text, text_rect)


class NPCManager:
    """Manages all NPCs in the game."""
    
    def __init__(self):
        """Initialize NPC manager."""
        self.npcs = []
        self.rescued_count = 0
    
    def add_npc(self, x: float, y: float, character_name: str) -> NPC:
        """Add an NPC to the manager."""
        # For now, skip loading character config (can be added later)
        character_config = None
        
        npc = NPC(x, y, character_name, character_config)
        self.npcs.append(npc)
        return npc
    
    def update(self, dt: float, player_pos: pg.Vector2 = None):
        """Update all NPCs."""
        try:
            for npc in self.npcs:
                npc.update(dt, player_pos)
        except Exception as e:
            print(f"Error in NPCManager update: {e}")
            import traceback
            traceback.print_exc()
    
    def render(self, screen: pg.Surface, offset: tuple = (0, 0)):
        """Render all NPCs."""
        for npc in self.npcs:
            npc.render(screen, offset)
    
    def handle_player_interaction(self, player_pos: pg.Vector2, keys_pressed) -> bool:
        """Handle player interaction with NPCs. Returns True if any rescue was completed."""
        rescue_completed = False
        
        try:
            for npc in self.npcs:
                if npc.can_interact(player_pos) and not npc.state.is_rescued:
                    # Check for E key hold - keys_pressed is ScancodeWrapper, use direct indexing
                    e_pressed = False
                    try:
                        e_pressed = keys_pressed[pg.K_e]
                    except (KeyError, IndexError, TypeError) as e:
                        print(f"Error accessing E key in keys_pressed: {e}")
                        continue
                    
                    if e_pressed:
                        if not npc.state.is_being_rescued:
                            npc.start_rescue()
                        # Rescue continues in npc.update()
                    else:
                        # Stop rescue if E key released
                        if npc.state.is_being_rescued:
                            npc.state.is_being_rescued = False
                            npc.state.rescue_progress = 0.0
                    
                    # Check if rescue was just completed
                    if npc.state.is_rescued and not getattr(npc, '_rescue_counted', False):
                        npc._rescue_counted = True
                        self.rescued_count += 1
                        rescue_completed = True
        except Exception as e:
            print(f"Error in handle_player_interaction: {e}")
            import traceback
            traceback.print_exc()
        
        return rescue_completed
    
    def get_npcs_in_range(self, player_pos: pg.Vector2, max_distance: float):
        """Get all NPCs within a certain range of the player."""
        nearby_npcs = []
        for npc in self.npcs:
            if npc.pos.distance_to(player_pos) <= max_distance:
                nearby_npcs.append(npc)
        return nearby_npcs
    
    def get_rescued_count(self) -> int:
        """Get the number of NPCs that have been rescued."""
        return self.rescued_count
    
    def get_total_npc_count(self) -> int:
        """Get the total number of NPCs."""
        return len(self.npcs)
    
    def is_all_rescued(self) -> bool:
        """Check if all NPCs have been rescued."""
        return self.rescued_count >= len(self.npcs)
    
    def clear(self):
        """Clear all NPCs (for level resets)."""
        self.npcs.clear()
        self.rescued_count = 0
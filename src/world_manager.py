"""
Level-based World Manager for Kingdom Pygame.

This module handles the generation and management of wave-based levels
with objectives and wave progression.
"""

import os
import json
import math
import random
from typing import Dict, Tuple, List, Optional
from enum import Enum
from dataclasses import dataclass
import pygame as pg

# Import the map system
try:
    from src.map_system import MapManager
except ImportError:
    try:
        from map_system import MapManager
    except ImportError:
        MapManager = None

# Objective Types for Level System
class ObjectiveType(Enum):
    COLLECT_CORES = "collect_cores"
    RESCUE_NPC = "rescue_npc" 
    SURVIVE_TIME = "survive_time"

# Area Types for Environmental Effects
class AreaType(Enum):
    PEACEFUL = "peaceful"      # Safe areas with cherry blossoms
    COMBAT = "combat"          # Active combat zones  
    MYSTICAL = "mystical"      # Magical areas with spirit wisps
    INDUSTRIAL = "industrial"  # Tech/urban areas
    NATURAL = "natural"        # Forest/outdoor areas

@dataclass
class LevelObjective:
    """Represents a level objective with progress tracking."""
    type: ObjectiveType
    description: str
    target_value: int
    current_progress: int = 0
    is_completed: bool = False
    
    # Additional fields for NPC rescue missions
    npc_character_name: Optional[str] = None
    npc_spawn_position: Optional[Tuple[int, int]] = None

@dataclass
class WaveInfo:
    """Information about a wave."""
    wave_number: int
    enemy_count: int
    enemy_spawn_rate: float  # enemies per second
    enemy_health_multiplier: float
    enemy_damage_multiplier: float
    description: str

class WorldManager:
    """Manages level-based world generation with wave system and objectives."""
    
    def __init__(self, seed: int = None):
        """Initialize the world manager for level-based gameplay."""
        self.seed = seed or random.randint(0, 1000000)
        random.seed(self.seed)
        
        # New level-based world settings (rectangular)
        self.world_width = 3840   # 3840 pixel width
        self.world_height = 2160   # 2160 pixel height
        self.world_bounds = (-1920, -1080, 1920, 1080)  # min_x, min_y, max_x, max_y (3840x2160)
        
        # Current level properties
        self.current_level = 1
        self.current_wave = 1
        self.current_objective = None
        
        # Wave system properties
        self.wave_started = False
        self.wave_start_time = 0.0
        self.enemies_spawned_this_wave = 0
        self.enemies_remaining_to_spawn = 0
        self.wave_spawn_rate = 1.0  # enemies per second
        self.next_spawn_time = 0.0
        
        # Wave definitions
        self.waves = {
            1: WaveInfo(1, 10, 1.0, 1.0, 1.0, "Wave 1: Light assault"),
            2: WaveInfo(2, 15, 1.2, 1.1, 1.1, "Wave 2: Reinforcements"),
            3: WaveInfo(3, 20, 1.5, 1.2, 1.2, "Wave 3: Heavy attack"),
            4: WaveInfo(4, 25, 1.8, 1.3, 1.3, "Wave 4: Elite forces"),
            5: WaveInfo(5, 30, 2.0, 1.5, 1.5, "Wave 5: Final assault")
        }
        
        # Core system integration
        from src.core_system import CoreManager
        self.core_manager = CoreManager()
        
        # Map system integration
        self.map_manager = MapManager() if MapManager else None
        if self.map_manager:
            # Try to load the large map
            success = self.map_manager.load_map("Field-Large")
            if success:
                print("Successfully loaded Field-Large map with collision system")
            else:
                print("Failed to load map, collision system disabled")
        
        # NPC system integration
        from src.npc import NPCManager
        self.npc_manager = NPCManager()
        
        # Character configuration loading for NPC rescue missions
        self.available_characters = self._load_character_configs()
        
        # Initialize first level
        self.generate_new_level()
        
    def _load_character_configs(self) -> List[str]:
        """Load available character names for NPC rescue missions."""
        characters = []
        char_dir = "assets/images/Characters"
        if os.path.exists(char_dir):
            for folder in os.listdir(char_dir):
                if os.path.isdir(os.path.join(char_dir, folder)):
                    # Convert folder name to display name
                    char_name = folder.replace('-', ' ').title()
                    characters.append(char_name)
        return characters
        
    def generate_new_level(self, character_level: int = 1):
        """Generate a new level with wave system and objective."""
        self.current_level = character_level
        
        # Start wave 1 for this level
        self.current_wave = 1
        self.start_wave(1)
        
        # Generate random objective based on level
        self.current_objective = self._generate_random_objective(character_level)
        
        # Clear cores but don't generate chests - cores now only come from enemies
        self.core_manager.clear_all_cores()
        
        wave_info = self.waves.get(self.current_wave, self.waves[1])
        print(f"Generated Level {character_level}: {wave_info.description}, {self.current_objective.description}")
        print("Cores will only be available from defeated enemies")
        
    def _generate_random_objective(self, character_level: int) -> LevelObjective:
        """Generate a random objective scaled to character level."""
        objective_type = random.choice(list(ObjectiveType))
        
        if objective_type == ObjectiveType.COLLECT_CORES:
            # Scale cores needed: 5 + (level-1)*3, so level 1=5, level 2=8, level 3=11, etc.
            cores_needed = 5 + (character_level - 1) * 3
            return LevelObjective(
                type=ObjectiveType.COLLECT_CORES,
                description=f"Collect {cores_needed} Rapture Cores",
                target_value=cores_needed
            )
            
        elif objective_type == ObjectiveType.RESCUE_NPC:
            # Select random character that's not the player
            if self.available_characters:
                npc_name = random.choice(self.available_characters)
                # Place NPC in far corner of map (updated for rectangular world)
                corner_positions = [
                    (-4000, -2500), (4000, -2500), (-4000, 2500), (4000, 2500)
                ]
                npc_pos = random.choice(corner_positions)
                
                # Actually spawn the NPC
                self.npc_manager.add_npc(npc_pos[0], npc_pos[1], npc_name)
                print(f"Spawned NPC {npc_name} at {npc_pos}")
                
                return LevelObjective(
                    type=ObjectiveType.RESCUE_NPC,
                    description=f"Rescue {npc_name}",
                    target_value=1,
                    npc_character_name=npc_name,
                    npc_spawn_position=npc_pos
                )
            else:
                # Fallback to cores if no characters available
                return self._generate_random_objective(character_level)
                
        else:  # ObjectiveType.SURVIVE_TIME
            # Scale time: 60 + (level-1)*30 seconds, so level 1=1min, level 2=1.5min, etc.
            survive_seconds = 60 + (character_level - 1) * 30
            return LevelObjective(
                type=ObjectiveType.SURVIVE_TIME,
                description=f"Survive for {survive_seconds//60}:{survive_seconds%60:02d}",
                target_value=survive_seconds
            )
    
    # Level-based World Management Methods
    
    def get_distance_from_center(self, world_x: float, world_y: float) -> float:
        """Calculate distance from world center (0,0)."""
        return math.sqrt(world_x**2 + world_y**2)
        
    def is_within_world_bounds(self, world_x: float, world_y: float) -> bool:
        """Check if coordinates are within the 3840x2160 world boundaries."""
        return (self.world_bounds[0] <= world_x <= self.world_bounds[2] and
                self.world_bounds[1] <= world_y <= self.world_bounds[3])
    
    def get_area_type(self, world_x: float, world_y: float) -> AreaType:
        """Determine the area type for environmental effects."""
        distance_from_center = self.get_distance_from_center(world_x, world_y)
        
        # Check if there are active enemies nearby (combat zone)
        # This will be updated by the main game loop when enemies are present
        if hasattr(self, '_combat_zones') and self._is_in_combat_zone(world_x, world_y):
            return AreaType.COMBAT
        
        # Use position-based area determination
        # Mystical areas in the corners of the world
        corner_distance = min(
            abs(world_x - self.world_bounds[0]) + abs(world_y - self.world_bounds[1]),  # Bottom-left
            abs(world_x - self.world_bounds[2]) + abs(world_y - self.world_bounds[1]),  # Bottom-right
            abs(world_x - self.world_bounds[0]) + abs(world_y - self.world_bounds[3]),  # Top-left
            abs(world_x - self.world_bounds[2]) + abs(world_y - self.world_bounds[3])   # Top-right
        )
        
        if corner_distance < 300:  # Near corners = mystical
            return AreaType.MYSTICAL
        elif distance_from_center > 800:  # Far from center = natural/wilderness
            return AreaType.NATURAL
        else:  # Medium distance = industrial/developed
            return AreaType.INDUSTRIAL
    
    def update_combat_zones(self, enemy_positions: List[Tuple[float, float]]):
        """Update active combat zones based on enemy positions."""
        if not hasattr(self, '_combat_zones'):
            self._combat_zones = []
        
        # Clear old combat zones
        self._combat_zones.clear()
        
        # Create combat zones around enemy clusters
        for enemy_x, enemy_y in enemy_positions:
            self._combat_zones.append((enemy_x, enemy_y, 200))  # 200 pixel combat radius
    
    def _is_in_combat_zone(self, world_x: float, world_y: float) -> bool:
        """Check if position is within any active combat zone."""
        if not hasattr(self, '_combat_zones'):
            return False
        
        for zone_x, zone_y, zone_radius in self._combat_zones:
            distance = math.sqrt((world_x - zone_x)**2 + (world_y - zone_y)**2)
            if distance <= zone_radius:
                return True
        return False
    
    # Map Collision Methods
    
    def is_position_blocked_by_map(self, world_x: float, world_y: float) -> bool:
        """Check if position is blocked by map collision (layers 2 and 3)."""
        if self.map_manager:
            return self.map_manager.is_position_blocked(world_x, world_y)
        return False
    
    def get_map_collision_rects_near(self, world_x: float, world_y: float, radius: float = 100.0):
        """Get map collision rectangles near position."""
        if self.map_manager:
            return self.map_manager.get_collision_rects_near(world_x, world_y, radius)
        return []
    
    def is_movement_blocked(self, from_x: float, from_y: float, to_x: float, to_y: float) -> bool:
        """Check if movement from one position to another is blocked by map collision."""
        # Check both start and end positions
        if self.is_position_blocked_by_map(from_x, from_y) or self.is_position_blocked_by_map(to_x, to_y):
            return True
        
        # For more precise collision, we could check intermediate points along the path
        # But for now, checking endpoints should be sufficient
        return False
    
    def render_map_debug(self, screen, camera_offset):
        """Render map debug visualization."""
        if self.map_manager:
            self.map_manager.render_debug(screen, camera_offset)
    
    def render_map(self, screen, camera_offset):
        """Render the map with textures."""
        if self.map_manager:
            self.map_manager.render_map(screen, camera_offset)
    
    def toggle_map_debug(self):
        """Toggle map debug rendering."""
        if self.map_manager:
            self.map_manager.toggle_debug_render()
    
    # Wave System Methods
    
    def start_wave(self, wave_number: int):
        """Start a specific wave."""
        if wave_number in self.waves:
            self.current_wave = wave_number
            wave_info = self.waves[wave_number]
            self.wave_started = True
            self.wave_start_time = 0.0  # Will be set by game time
            self.enemies_spawned_this_wave = 0
            self.enemies_remaining_to_spawn = wave_info.enemy_count
            self.wave_spawn_rate = wave_info.enemy_spawn_rate
            self.next_spawn_time = 0.0
            print(f"Starting {wave_info.description}")
    
    def should_spawn_enemy(self, current_time: float) -> bool:
        """Check if an enemy should be spawned based on wave timing."""
        if not self.wave_started or self.enemies_remaining_to_spawn <= 0:
            return False
        
        if current_time >= self.next_spawn_time:
            self.next_spawn_time = current_time + (1.0 / self.wave_spawn_rate)
            self.enemies_spawned_this_wave += 1
            self.enemies_remaining_to_spawn -= 1
            return True
        return False
    
    def get_current_wave_info(self) -> WaveInfo:
        """Get information about the current wave."""
        return self.waves.get(self.current_wave, self.waves[1])
    
    def is_wave_complete(self) -> bool:
        """Check if the current wave is complete (all enemies spawned)."""
        return self.enemies_remaining_to_spawn <= 0
    
    def advance_to_next_wave(self):
        """Advance to the next wave."""
        next_wave = self.current_wave + 1
        if next_wave in self.waves:
            self.start_wave(next_wave)
        else:
            # Repeat highest wave with increased difficulty
            max_wave = max(self.waves.keys())
            wave_info = self.waves[max_wave]
            # Create scaled wave
            new_wave_info = WaveInfo(
                next_wave,
                wave_info.enemy_count + 5,  # +5 enemies each repeat
                wave_info.enemy_spawn_rate * 1.1,  # 10% faster spawning
                wave_info.enemy_health_multiplier * 1.1,  # 10% more health
                wave_info.enemy_damage_multiplier * 1.1,  # 10% more damage
                f"Wave {next_wave}: Endless assault"
            )
            self.waves[next_wave] = new_wave_info
            self.start_wave(next_wave)
    
    def get_current_wave_danger_level(self) -> float:
        """Get danger level based on current wave."""
        wave_info = self.get_current_wave_info()
        # Danger level is based on wave multipliers
        return wave_info.enemy_health_multiplier + wave_info.enemy_damage_multiplier - 1.0
    
    # Objective Management Methods
    
    def update_objective_progress(self, progress_type: str, value: int = 1):
        """Update the current objective's progress."""
        if not self.current_objective:
            return
            
        if (progress_type == "cores" and 
            self.current_objective.type == ObjectiveType.COLLECT_CORES):
            self.current_objective.current_progress += value
            
        elif (progress_type == "time" and 
              self.current_objective.type == ObjectiveType.SURVIVE_TIME):
            self.current_objective.current_progress += value
            
        elif (progress_type == "npc_rescued" and 
              self.current_objective.type == ObjectiveType.RESCUE_NPC):
            self.current_objective.current_progress = 1
            self.current_objective.is_completed = True
    
    def is_objective_complete(self) -> bool:
        """Check if the current objective is complete."""
        if not self.current_objective:
            return False
            
        if self.current_objective.is_completed:
            return True
            
        # Check completion based on objective type
        if self.current_objective.type == ObjectiveType.COLLECT_CORES:
            cores_collected = self.core_manager.get_total_cores_collected()
            return cores_collected >= self.current_objective.target_value
            
        elif self.current_objective.type == ObjectiveType.SURVIVE_TIME:
            return self.current_objective.current_progress >= self.current_objective.target_value
            
        elif self.current_objective.type == ObjectiveType.RESCUE_NPC:
            # Check if all NPCs have been rescued
            return self.npc_manager.is_all_rescued()
            
        return False
        
    def get_objective_progress_text(self) -> str:
        """Get formatted text showing objective progress."""
        if not self.current_objective:
            return "No objective"
            
        obj = self.current_objective
        
        if obj.type == ObjectiveType.COLLECT_CORES:
            current = self.core_manager.get_total_cores_collected()
            return f"{obj.description}: {current}/{obj.target_value}"
            
        elif obj.type == ObjectiveType.SURVIVE_TIME:
            remaining = obj.target_value - obj.current_progress
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            return f"{obj.description}: {minutes}:{seconds:02d} remaining"
            
        elif obj.type == ObjectiveType.RESCUE_NPC:
            status = "COMPLETE" if obj.is_completed else "Find NPC"
            return f"{obj.description}: {status}"
            
        return obj.description
    
    # Rendering Methods for Uniform Background
    
    def render_world_background(self, surface, camera_x: float, camera_y: float, 
                               screen_width: int, screen_height: int):
        """Render the uniform background for the current level with world boundaries and black border."""
        
        # Fill entire screen with void color (far outside world bounds)
        void_color = (10, 10, 10)  # Very dark color for outside world bounds
        surface.fill(void_color)
        
        # Define border size
        border_size = 100
        
        # Calculate extended area including black border
        border_bounds = (self.world_bounds[0] - border_size, self.world_bounds[1] - border_size,
                        self.world_bounds[2] + border_size, self.world_bounds[3] + border_size)
        
        # Calculate visible border area
        border_left = max(border_bounds[0], camera_x - screen_width // 2)
        border_right = min(border_bounds[2], camera_x + screen_width // 2)
        border_top = max(border_bounds[1], camera_y - screen_height // 2)
        border_bottom = min(border_bounds[3], camera_y + screen_height // 2)
        
        # Calculate screen positions for border area
        border_screen_left = screen_width // 2 + (border_left - camera_x)
        border_screen_right = screen_width // 2 + (border_right - camera_x)
        border_screen_top = screen_height // 2 + (border_top - camera_y)
        border_screen_bottom = screen_height // 2 + (border_bottom - camera_y)
        
        # Fill border area with black
        if border_right > border_left and border_bottom > border_top:
            border_rect = pg.Rect(int(border_screen_left), int(border_screen_top), 
                                 int(border_screen_right - border_screen_left), 
                                 int(border_screen_bottom - border_screen_top))
            border_rect = border_rect.clip(pg.Rect(0, 0, screen_width, screen_height))
            if border_rect.width > 0 and border_rect.height > 0:
                pg.draw.rect(surface, (0, 0, 0), border_rect)  # Black border
        
        # Calculate visible world area (constrained to world bounds)
        left = max(self.world_bounds[0], camera_x - screen_width // 2)
        right = min(self.world_bounds[2], camera_x + screen_width // 2)
        top = max(self.world_bounds[1], camera_y - screen_height // 2)
        bottom = min(self.world_bounds[3], camera_y + screen_height // 2)
        
        # Calculate screen positions for world area
        world_screen_left = screen_width // 2 + (left - camera_x)
        world_screen_right = screen_width // 2 + (right - camera_x)
        world_screen_top = screen_height // 2 + (top - camera_y)
        world_screen_bottom = screen_height // 2 + (bottom - camera_y)
        
        # Fill the world area with grass-green color (on top of black border)
        grass_green = (34, 139, 34)
        if right > left and bottom > top:
            world_rect = pg.Rect(int(world_screen_left), int(world_screen_top), 
                                int(world_screen_right - world_screen_left), 
                                int(world_screen_bottom - world_screen_top))
            world_rect = world_rect.clip(pg.Rect(0, 0, screen_width, screen_height))
            if world_rect.width > 0 and world_rect.height > 0:
                pg.draw.rect(surface, grass_green, world_rect)
        
        # Add simple decorative elements only within world bounds
        if right > left and bottom > top:
            self._render_simple_decorations(surface, int(left), int(top), 
                                         int(right - left), int(bottom - top),
                                         camera_x, camera_y)
        
        # Render world boundaries as visible edges
        self._render_world_boundaries(surface, camera_x, camera_y, screen_width, screen_height)
    
    def _render_world_boundaries(self, surface, camera_x: float, camera_y: float,
                                screen_width: int, screen_height: int):
        """Render visible world boundaries as dark borders."""
        boundary_color = (50, 50, 50)  # Dark gray boundary
        boundary_width = 10
        
        # Calculate screen positions of world boundaries
        left_boundary_x = screen_width // 2 + (self.world_bounds[0] - camera_x)
        right_boundary_x = screen_width // 2 + (self.world_bounds[2] - camera_x)
        top_boundary_y = screen_height // 2 + (self.world_bounds[1] - camera_y)
        bottom_boundary_y = screen_height // 2 + (self.world_bounds[3] - camera_y)
        
        # Draw visible boundaries
        if left_boundary_x >= 0 and left_boundary_x <= screen_width:
            pg.draw.rect(surface, boundary_color, 
                        (left_boundary_x - boundary_width, 0, boundary_width, screen_height))
        
        if right_boundary_x >= 0 and right_boundary_x <= screen_width:
            pg.draw.rect(surface, boundary_color,
                        (right_boundary_x, 0, boundary_width, screen_height))
        
        if top_boundary_y >= 0 and top_boundary_y <= screen_height:
            pg.draw.rect(surface, boundary_color,
                        (0, top_boundary_y - boundary_width, screen_width, boundary_width))
        
        if bottom_boundary_y >= 0 and bottom_boundary_y <= screen_height:
            pg.draw.rect(surface, boundary_color,
                        (0, bottom_boundary_y, screen_width, boundary_width))
    
    def _render_simple_decorations(self, surface, x: int, y: int, width: int, height: int,
                                 camera_x: float, camera_y: float):
        """Add simple grass and flower decorations."""
        # Ensure width and height are integers
        width = int(width)
        height = int(height)
        
        # Reduce decoration density significantly for performance
        decoration_density = 0.0001  # Much lower density
        num_decorations = max(5, int(width * height * decoration_density))  # Min 5, max based on area
        
        # Use camera position as seed for consistent decorations that don't flicker
        seed_x = int(camera_x // 100) * 100  # Round to nearest 100 for stability
        seed_y = int(camera_y // 100) * 100
        random.seed(seed_x ^ seed_y)  # Consistent but varied decorations
        
        for _ in range(num_decorations):
            dec_x = x + random.randint(0, max(1, width - 1))  
            dec_y = y + random.randint(0, max(1, height - 1))
            
            # Convert screen coordinates back to world coordinates
            world_x = dec_x - (surface.get_width()//2) + camera_x
            world_y = dec_y - (surface.get_height()//2) + camera_y
            
            # Don't draw decorations outside world boundaries
            if not self.is_within_world_bounds(world_x, world_y):
                continue
                
            # Add simple grass and flowers
            if random.random() < 0.7:
                # Grass tufts
                pg.draw.circle(surface, (0, 120, 0), (dec_x, dec_y), 1)
            else:
                # Simple flowers
                flower_colors = [(255, 255, 0), (255, 192, 203), (138, 43, 226)]
                pg.draw.circle(surface, random.choice(flower_colors), (dec_x, dec_y), 1)
    
    def update(self, dt: float, player_pos: pg.Vector2 = None, keys_pressed: dict = None):
        """Update world manager systems including NPCs and objectives."""
        # Update NPC system
        if player_pos:
            self.npc_manager.update(dt, player_pos)
            
            # Handle NPC interactions
            if keys_pressed:
                rescue_completed = self.npc_manager.handle_player_interaction(player_pos, keys_pressed)
                
                # If a rescue was completed and this is a rescue objective, check completion
                if rescue_completed and self.current_objective and self.current_objective.type == ObjectiveType.RESCUE_NPC:
                    if self.npc_manager.is_all_rescued():
                        self.current_objective.is_completed = True
                        print(f"Objective completed: {self.current_objective.description}")
        
        # Update survive time objectives
        if self.current_objective and self.current_objective.type == ObjectiveType.SURVIVE_TIME:
            self.current_objective.current_progress += dt
            if self.current_objective.current_progress >= self.current_objective.target_value:
                self.current_objective.is_completed = True
                print(f"Objective completed: Survived required time!")
    
    def render_npcs(self, surface: pg.Surface, offset: tuple = (0, 0)):
        """Render all NPCs."""
        self.npc_manager.render(surface, offset)
    
    def get_npcs(self):
        """Get list of NPCs for minimap and other systems."""
        return [{'pos': npc.pos, 'name': npc.character_name, 'rescued': npc.state.is_rescued} 
                for npc in self.npc_manager.npcs]
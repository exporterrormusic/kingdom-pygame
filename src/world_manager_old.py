"""
Level-Based World Management System
Handles single-biome level generation with objectives and base areas.
"""

import pygame as pg
import math
import random
import json
import os
from typing import Dict, Tuple, List, Optional
from enum import Enum
from dataclasses import dataclass

class BiomeType(Enum):
    """Different biome types available in the world."""
    FIELD = "field"
    FOREST = "forest" 
    DESERT = "desert"
    SNOW = "snow"
    CITY = "city"

class ObjectiveType(Enum):
    """Types of level objectives."""
    COLLECT_CORES = "collect_cores"
    RESCUE_NPC = "rescue_npc"  
    SURVIVE_TIME = "survive_time"

@dataclass
class BiomeInfo:
    """Information about a biome type."""
    name: str
    color: Tuple[int, int, int]  # Primary color for terrain
    accent_color: Tuple[int, int, int]  # Secondary color for features
    description: str
    danger_level: int  # Base danger level for this biome (1-5)

@dataclass
class LevelObjective:
    """Information about the current level's objective."""
    type: ObjectiveType
    description: str
    target_value: int  # cores needed, minutes to survive, etc.
    current_progress: int = 0
    npc_character_name: str = None  # For rescue missions
    npc_spawn_position: Tuple[float, float] = None
    completed: bool = False

class PerlinNoise:
    """Simple Perlin noise implementation for terrain generation."""
    
    def __init__(self, seed: int = None):
        """Initialize with optional seed for reproducible generation."""
        if seed is not None:
            random.seed(seed)
        
        # Generate permutation table
        self.p = list(range(256))
        random.shuffle(self.p)
        self.p *= 2  # Duplicate for easier indexing
        
    def fade(self, t: float) -> float:
        """Fade function for smooth interpolation."""
        return t * t * t * (t * (t * 6 - 15) + 10)
        
    def lerp(self, t: float, a: float, b: float) -> float:
        """Linear interpolation between a and b."""
        return a + t * (b - a)
        
    def grad(self, hash_val: int, x: float, y: float) -> float:
        """Gradient function."""
        h = hash_val & 15
        u = x if h < 8 else y
        v = y if h < 4 else (x if h == 12 or h == 14 else 0)
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
        
    def noise(self, x: float, y: float) -> float:
        """Generate 2D Perlin noise value between -1 and 1."""
        # Find unit square coordinates
        X = int(x) & 255
        Y = int(y) & 255
        
        # Find relative x,y coordinates in square
        x -= int(x)
        y -= int(y)
        
        # Compute fade curves
        u = self.fade(x)
        v = self.fade(y)
        
        # Hash coordinates of square corners
        A = self.p[X] + Y
        AA = self.p[A]
        AB = self.p[A + 1]
        B = self.p[X + 1] + Y
        BA = self.p[B]
        BB = self.p[B + 1]
        
        # Blend results from the 8 corners
        return self.lerp(v,
                        self.lerp(u, self.grad(self.p[AA], x, y),
                                   self.grad(self.p[BA], x - 1, y)),
                        self.lerp(u, self.grad(self.p[AB], x, y - 1),
                                   self.grad(self.p[BB], x - 1, y - 1)))

class Chunk:
    """Represents a chunk of the infinite world."""
    
    def __init__(self, chunk_x: int, chunk_y: int, size: int = 2048):
        """Initialize a chunk at given chunk coordinates."""
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size
        self.world_x = chunk_x * size
        self.world_y = chunk_y * size
        
        # Terrain data
        self.biome_map = {}  # Dict[(x, y), BiomeType] for biome at each point
        self.terrain_surface = None  # Cached rendered terrain surface
        self.needs_render = True
        
        # Features (resources, obstacles, etc.)
        self.resources = []  # List of resources in this chunk
        self.obstacles = []  # List of obstacles in this chunk
        
        # Generation state
        self.is_generated = False
        
    def world_to_chunk_coords(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to chunk-local coordinates."""
        local_x = int(world_x - self.world_x)
        local_y = int(world_y - self.world_y)
        return local_x, local_y
        
    def contains_point(self, world_x: float, world_y: float) -> bool:
        """Check if world coordinates are within this chunk."""
        return (self.world_x <= world_x < self.world_x + self.size and
                self.world_y <= world_y < self.world_y + self.size)

class WorldManager:
    """Manages level-based world generation with single biomes and objectives."""
    
    def __init__(self, seed: int = None):
        """Initialize the world manager for level-based gameplay."""
        self.seed = seed or random.randint(0, 1000000)
        random.seed(self.seed)
        
        # New level-based world settings
        self.world_size = 7000  # 7000x7000 pixel world
        self.world_bounds = (-3500, -3500, 3500, 3500)  # min_x, min_y, max_x, max_y
        
        # Base area (safe zone at center)
        self.base_center = (0, 0)
        self.base_radius = 250  # 500x500 area = 250 pixel radius
        
        # Current level properties
        self.current_level = 1
        self.current_biome = BiomeType.FIELD
        self.current_objective = None
        
        # Biome definitions (same as before but now single biome per level)
        self.biomes = {
            BiomeType.FIELD: BiomeInfo("Field", (34, 139, 34), (0, 100, 0), "Rolling grasslands", 1),
            BiomeType.FOREST: BiomeInfo("Forest", (0, 100, 0), (139, 69, 19), "Dense woodlands", 2),
            BiomeType.DESERT: BiomeInfo("Desert", (238, 203, 173), (205, 133, 63), "Arid wastelands", 3), 
            BiomeType.SNOW: BiomeInfo("Snow", (255, 250, 250), (176, 196, 222), "Frozen tundra", 4),
            BiomeType.CITY: BiomeInfo("City", (105, 105, 105), (169, 169, 169), "Urban ruins", 5)
        }
        
        # Core system integration
        from src.core_system import CoreManager
        self.core_manager = CoreManager()
        
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
        """Generate a new level with random biome and objective."""
        self.current_level = character_level
        
        # Select random biome for this level
        self.current_biome = random.choice(list(BiomeType))
        
        # Generate random objective based on level
        self.current_objective = self._generate_random_objective(character_level)
        
        # Reset core manager for new level
        self.core_manager.clear_all_cores()
        
        print(f"Generated Level {character_level}: {self.current_biome.value} biome, {self.current_objective.description}")
        
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
                # Place NPC in far corner of map
                corner_positions = [
                    (-3000, -3000), (3000, -3000), (-3000, 3000), (3000, 3000)
                ]
                npc_pos = random.choice(corner_positions)
                
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
    
    def get_distance_from_base(self, world_x: float, world_y: float) -> float:
        """Calculate distance from base center (0,0)."""
        return math.sqrt(world_x**2 + world_y**2)
        
    def is_in_safe_zone(self, world_x: float, world_y: float) -> bool:
        """Check if coordinates are in the base safe zone (circular, 250 pixel radius)."""
        return self.get_distance_from_base(world_x, world_y) <= self.base_radius
        
    def is_within_world_bounds(self, world_x: float, world_y: float) -> bool:
        """Check if coordinates are within the 7000x7000 world boundaries."""
        return (self.world_bounds[0] <= world_x <= self.world_bounds[2] and
                self.world_bounds[1] <= world_y <= self.world_bounds[3])
    
    def get_biome_at_point(self, world_x: float, world_y: float) -> BiomeType:
        """Return the current level's biome for any point in the world."""
        return self.current_biome
        
    def get_current_biome_danger_level(self, world_x: float, world_y: float) -> int:
        """Get danger level based on position and current biome."""
        if self.is_in_safe_zone(world_x, world_y):
            return 0  # Safe zone has no danger
        
        # Return current biome's danger level
        return self.biomes[self.current_biome].danger_level
    
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
            return self.current_objective.is_completed
            
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
            minutes = remaining // 60
            seconds = remaining % 60
            return f"{obj.description}: {minutes}:{seconds:02d} remaining"
            
        elif obj.type == ObjectiveType.RESCUE_NPC:
            status = "COMPLETE" if obj.is_completed else "Find NPC"
            return f"{obj.description}: {status}"
            
        return obj.description
    
    # Rendering Methods for Single Biome
    
    def render_world_background(self, surface, camera_x: float, camera_y: float, 
                               screen_width: int, screen_height: int):
        """Render the single biome background for the current level."""
        # Calculate visible world area
        left = camera_x - screen_width // 2
        right = camera_x + screen_width // 2  
        top = camera_y - screen_height // 2
        bottom = camera_y + screen_height // 2
        
        # Get current biome info
        biome_info = self.biomes[self.current_biome]
        
        # Fill entire visible area with biome base color
        surface.fill(biome_info.base_color)
        
        # Add biome-specific decorative elements
        self._render_biome_decorations(surface, left, top, right - left, bottom - top,
                                     camera_x, camera_y, biome_info)
        
        # Render safe zone as a visible circle
        self._render_safe_zone(surface, camera_x, camera_y, screen_width, screen_height)
    
    def _render_safe_zone(self, surface, camera_x: float, camera_y: float,
                         screen_width: int, screen_height: int):
        """Render the safe zone as a visible lighter circle at world center."""
        # Calculate safe zone position on screen
        safe_zone_screen_x = screen_width // 2 + (self.base_center[0] - camera_x)
        safe_zone_screen_y = screen_height // 2 + (self.base_center[1] - camera_y)
        
        # Only render if safe zone is visible on screen
        if (-self.base_radius <= safe_zone_screen_x - screen_width//2 <= screen_width + self.base_radius and
            -self.base_radius <= safe_zone_screen_y - screen_height//2 <= screen_height + self.base_radius):
            
            # Create lighter version of biome color for safe zone
            base_color = self.biomes[self.current_biome].base_color
            safe_color = tuple(min(255, c + 30) for c in base_color)
            
            # Draw safe zone circle
            pg.draw.circle(surface, safe_color, 
                         (int(safe_zone_screen_x), int(safe_zone_screen_y)), 
                         self.base_radius, 0)
            
            # Draw border
            border_color = tuple(min(255, c + 50) for c in base_color)
            pg.draw.circle(surface, border_color,
                         (int(safe_zone_screen_x), int(safe_zone_screen_y)),
                         self.base_radius, 3)
    
    def _render_biome_decorations(self, surface, x: int, y: int, width: int, height: int,
                                camera_x: float, camera_y: float, biome_info):
        """Add decorative elements specific to the current biome."""
        # Simple decoration pattern based on biome type
        decoration_density = 0.001  # Decorations per pixel
        num_decorations = int(width * height * decoration_density)
        
        random.seed(int(camera_x) ^ int(camera_y))  # Consistent decorations
        
        for _ in range(num_decorations):
            dec_x = x + random.randint(0, width - 1)  
            dec_y = y + random.randint(0, height - 1)
            
            # Convert screen coordinates back to world coordinates
            world_x = dec_x - (surface.get_width()//2) + camera_x
            world_y = dec_y - (surface.get_height()//2) + camera_y
            
            # Don't draw decorations in safe zone
            if self.is_in_safe_zone(world_x, world_y):
                continue
                
            # Add biome-specific decorations
            if self.current_biome == BiomeType.FIELD:
                # Small grass tufts and flowers
                if random.random() < 0.7:
                    pg.draw.circle(surface, (0, 120, 0), (dec_x, dec_y), 1)
                else:
                    flower_colors = [(255, 255, 0), (255, 192, 203), (138, 43, 226)]
                    pg.draw.circle(surface, random.choice(flower_colors), (dec_x, dec_y), 1)
                    
            elif self.current_biome == BiomeType.FOREST:
                # Trees and mushrooms
                tree_color = (101, 67, 33)
                pg.draw.circle(surface, tree_color, (dec_x, dec_y), 2)
                if random.random() < 0.3:
                    pg.draw.circle(surface, (255, 0, 0), (dec_x, dec_y), 1)
                    
            elif self.current_biome == BiomeType.DESERT:
                # Rocks and cacti
                if random.random() < 0.6:
                    rock_color = (160, 82, 45)
                    pg.draw.circle(surface, rock_color, (dec_x, dec_y), 1)
                else:
                    cactus_color = (34, 139, 34)
                    pg.draw.circle(surface, cactus_color, (dec_x, dec_y), 2)
                    
            elif self.current_biome == BiomeType.SNOW:
                # Snowflakes and ice
                snow_color = (240, 248, 255)
                ice_color = (176, 224, 230)
                color = snow_color if random.random() < 0.8 else ice_color
                pg.draw.circle(surface, color, (dec_x, dec_y), 1)
                
            elif self.current_biome == BiomeType.CITY:
                # Rubble and debris
                debris_colors = [(105, 105, 105), (169, 169, 169), (128, 128, 128)]
                pg.draw.rect(surface, random.choice(debris_colors), 
                           pg.Rect(dec_x, dec_y, 2, 2))
        os.makedirs(os.path.dirname(self.world_save_path), exist_ok=True)
        try:
            data = {
                'seed': self.seed,
                'base_x': self.base_x,
                'base_y': self.base_y
            }
            with open(self.world_save_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving world data: {e}")
            
    def world_to_chunk_coords(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to chunk coordinates."""
        chunk_x = int(world_x // self.chunk_size)
        chunk_y = int(world_y // self.chunk_size)
        return chunk_x, chunk_y
        
    def get_distance_from_base(self, world_x: float, world_y: float) -> float:
        """Calculate distance from base (0,0)."""
        return math.sqrt(world_x**2 + world_y**2)
        
    def is_in_safe_zone(self, world_x: float, world_y: float) -> bool:
        """Check if coordinates are in the base safe zone."""
        return self.get_distance_from_base(world_x, world_y) <= self.base_safe_radius
    
    def get_current_biome_danger_level(self, world_x: float, world_y: float) -> int:
        """Get danger level of current biome at position."""
        if self.is_in_safe_zone(world_x, world_y):
            return 0  # Safe zone has no danger
        
        biome_type = self.get_biome_at_point(world_x, world_y)
        return self.biomes[biome_type].danger_level
        
    def get_biome_at_point(self, world_x: float, world_y: float) -> BiomeType:
        """Determine the biome at a world coordinate using structured regions."""
        
        # World boundaries: -10000 to +10000 (20,000x20,000 pixel world)
        # Spawn area: -2500 to +2500 (5000x5000 pixel central square)
        
        # Central spawn area is always field
        if -2500 <= world_x <= 2500 and -2500 <= world_y <= 2500:
            return BiomeType.FIELD
        
        # Determine biome based on dominant direction from spawn
        abs_x = abs(world_x)
        abs_y = abs(world_y)
        
        # If we're outside the spawn square, determine which region we're in
        # Priority: the dimension with the larger distance from spawn determines biome
        if abs_x > abs_y:
            # Horizontal regions have priority
            if world_x < -2500:
                return BiomeType.FOREST  # West = Forest
            elif world_x > 2500:
                return BiomeType.CITY    # East = City
        else:
            # Vertical regions have priority
            if world_y < -2500:
                return BiomeType.SNOW    # North = Snow (negative Y is up)
            elif world_y > 2500:
                return BiomeType.DESERT  # South = Desert (positive Y is down)
        
        # Fallback to field (shouldn't happen with the logic above)
        return BiomeType.FIELD
            
    def generate_chunk(self, chunk_x: int, chunk_y: int) -> Chunk:
        """Generate a new chunk with terrain and features."""
        chunk = Chunk(chunk_x, chunk_y, self.chunk_size)
        
        # Generate biome data for this chunk
        self._generate_chunk_terrain(chunk)
        
        # Generate features (resources, obstacles) for this chunk
        self._generate_chunk_features(chunk)
        
        chunk.is_generated = True
        return chunk
        
    def _generate_chunk_terrain(self, chunk: Chunk):
        """Generate terrain/biome data for a chunk."""
        sample_resolution = 32  # Sample every 32 pixels for performance
        
        for y in range(0, chunk.size, sample_resolution):
            for x in range(0, chunk.size, sample_resolution):
                world_x = chunk.world_x + x
                world_y = chunk.world_y + y
                
                biome = self.get_biome_at_point(world_x, world_y)
                chunk.biome_map[(x, y)] = biome
                
    def _generate_chunk_features(self, chunk: Chunk):
        """Generate resources and obstacles for a chunk."""
        # Calculate average distance from base for this chunk
        chunk_center_x = chunk.world_x + chunk.size // 2
        chunk_center_y = chunk.world_y + chunk.size // 2
        base_distance = self.get_distance_from_base(chunk_center_x, chunk_center_y)
        
        # Skip feature generation if in safe zone
        if base_distance < self.base_safe_radius:
            return
            
        # Generate cores/chests for this chunk (replaces resource nodes)
        biome_type = self.get_biome_at_point(chunk_center_x, chunk_center_y)
        danger_level = self.biomes[biome_type].danger_level
        
        self.core_manager.generate_chunk_cores(
            chunk.chunk_x, chunk.chunk_y, chunk.size, biome_type, danger_level
        )
        
    def get_chunk(self, chunk_x: int, chunk_y: int) -> Chunk:
        """Get or generate a chunk."""
        chunk_key = (chunk_x, chunk_y)
        
        # Check active chunks first
        if chunk_key in self.active_chunks:
            return self.active_chunks[chunk_key]
            
        # Check cache
        if chunk_key in self.chunk_cache:
            chunk = self.chunk_cache.pop(chunk_key)
            self.active_chunks[chunk_key] = chunk
            return chunk
            
        # Generate new chunk
        chunk = self.generate_chunk(chunk_x, chunk_y)
        self.active_chunks[chunk_key] = chunk
        return chunk
        
    def update(self, player_x: float, player_y: float):
        """Update world management based on player position."""
        # Update chunk loading around player
        self._update_chunk_loading(player_x, player_y)
        
    def _update_chunk_loading(self, player_x: float, player_y: float):
        """Load/unload chunks based on player position."""
        player_chunk_x, player_chunk_y = self.world_to_chunk_coords(player_x, player_y)
        
        # World boundaries: 20,000x20,000 pixels (-10,000 to +10,000)
        world_min = -10000
        world_max = 10000
        
        # Define loading radius (3x3 chunks around player)
        load_radius = 1  # Load in 3x3 grid (1 chunk in each direction)
        unload_radius = 2  # Unload beyond 5x5 grid
        
        # Load needed chunks (within world boundaries)
        for dx in range(-load_radius, load_radius + 1):
            for dy in range(-load_radius, load_radius + 1):
                chunk_x = player_chunk_x + dx
                chunk_y = player_chunk_y + dy
                
                # Check if chunk is within world boundaries
                chunk_world_x = chunk_x * self.chunk_size
                chunk_world_y = chunk_y * self.chunk_size
                
                # Skip chunks outside world boundaries
                if (chunk_world_x < world_min or chunk_world_x >= world_max or
                    chunk_world_y < world_min or chunk_world_y >= world_max):
                    continue
                
                if (chunk_x, chunk_y) not in self.active_chunks:
                    self.get_chunk(chunk_x, chunk_y)
                    
        # Unload distant chunks
        chunks_to_unload = []
        for chunk_key, chunk in self.active_chunks.items():
            chunk_x, chunk_y = chunk_key
            dx = abs(chunk_x - player_chunk_x)
            dy = abs(chunk_y - player_chunk_y)
            
            if dx > unload_radius or dy > unload_radius:
                chunks_to_unload.append(chunk_key)
                
        # Move distant chunks to cache
        for chunk_key in chunks_to_unload:
            chunk = self.active_chunks.pop(chunk_key)
            self.chunk_cache[chunk_key] = chunk
            
            # Limit cache size
            if len(self.chunk_cache) > self.max_cache_size:
                # Remove oldest cached chunk
                oldest_key = next(iter(self.chunk_cache))
                del self.chunk_cache[oldest_key]
                
    def render_terrain(self, screen: pg.Surface, camera_x: float, camera_y: float, 
                      screen_width: int, screen_height: int):
        """Render visible terrain to screen."""
        # Calculate visible chunk range
        visible_chunks = self._get_visible_chunks(camera_x, camera_y, screen_width, screen_height)
        
        for chunk_key in visible_chunks:
            if chunk_key in self.active_chunks:
                chunk = self.active_chunks[chunk_key]
                self._render_chunk_terrain(screen, chunk, camera_x, camera_y)
                
    def _get_visible_chunks(self, camera_x: float, camera_y: float, 
                           screen_width: int, screen_height: int) -> List[Tuple[int, int]]:
        """Get list of chunks that are currently visible on screen."""
        # Calculate screen bounds in world coordinates
        left = camera_x - screen_width // 2
        right = camera_x + screen_width // 2
        top = camera_y - screen_height // 2
        bottom = camera_y + screen_height // 2
        
        # Convert to chunk coordinates
        chunk_left = int(left // self.chunk_size)
        chunk_right = int(right // self.chunk_size)
        chunk_top = int(top // self.chunk_size)
        chunk_bottom = int(bottom // self.chunk_size)
        
        visible_chunks = []
        for cx in range(chunk_left, chunk_right + 1):
            for cy in range(chunk_top, chunk_bottom + 1):
                visible_chunks.append((cx, cy))
                
        return visible_chunks
        
    def _render_chunk_terrain(self, screen: pg.Surface, chunk: Chunk, 
                             camera_x: float, camera_y: float):
        """Render a single chunk's terrain."""
        # Create terrain surface if needed
        if chunk.terrain_surface is None or chunk.needs_render:
            self._create_chunk_terrain_surface(chunk)
            
        # Calculate screen position for this chunk
        screen_x = chunk.world_x - camera_x + screen.get_width() // 2
        screen_y = chunk.world_y - camera_y + screen.get_height() // 2
        
        # Render the chunk
        screen.blit(chunk.terrain_surface, (screen_x, screen_y))
        
    def _create_chunk_terrain_surface(self, chunk: Chunk):
        """Create enhanced terrain surface for a chunk with better graphics."""
        surface = pg.Surface((chunk.size, chunk.size))
        
        # Sample resolution for rendering
        resolution = 32
        
        for y in range(0, chunk.size, resolution):
            for x in range(0, chunk.size, resolution):
                # Get biome at this point
                biome_key = (x, y)
                if biome_key in chunk.biome_map:
                    biome_type = chunk.biome_map[biome_key]
                    biome_info = self.biomes[biome_type]
                    
                    # Draw base terrain tile
                    rect = pg.Rect(x, y, resolution, resolution)
                    surface.fill(biome_info.color, rect)
                    
                    # Add biome-specific patterns and textures
                    world_x = chunk.world_x + x
                    world_y = chunk.world_y + y
                    self._add_biome_texture(surface, x, y, resolution, biome_type, biome_info, world_x, world_y)
        
        chunk.terrain_surface = surface
        chunk.needs_render = False
        
    def _add_biome_texture(self, surface: pg.Surface, x: int, y: int, size: int, 
                          biome_type: BiomeType, biome_info: BiomeInfo, world_x: int, world_y: int):
        """Add biome-specific textures and patterns."""
        import random
        
        # Seed random based on position for consistent patterns
        random.seed(hash((x, y)) % 1000000)
        
        # Check if in base area for special patterns
        distance_from_base = self.get_distance_from_base(world_x, world_y)
        is_in_base_area = distance_from_base < self.base_area_radius
        is_in_safe_zone = distance_from_base < self.base_safe_radius
        
        # Special base area patterns (for future shops/structures)
        if is_in_safe_zone:
            # Very safe central area - clear paths and foundations
            if random.random() < 0.6:
                # Add stone/path elements
                path_color = (120, 120, 120)
                path_x = x + random.randint(0, size-4)
                path_y = y + random.randint(0, size-4)
                path_size = random.randint(2, 6)
                pg.draw.circle(surface, path_color, (path_x, path_y), path_size)
        elif is_in_base_area:
            # Extended base area - prepared ground for expansion
            if random.random() < 0.4:
                # Add cleared ground markers
                clear_color = (60, 90, 60)  # Darker green for prepared ground
                clear_x = x + random.randint(1, size-3)
                clear_y = y + random.randint(1, size-3)
                clear_size = random.randint(1, 3)
                pg.draw.circle(surface, clear_color, (clear_x, clear_y), clear_size)
        
        if biome_type == BiomeType.FIELD:
            # Grass texture - small green dots and lines
            for i in range(random.randint(3, 8)):
                dot_x = x + random.randint(2, size-2)
                dot_y = y + random.randint(2, size-2)
                dot_size = random.randint(1, 3)
                dot_color = (random.randint(20, 60), random.randint(120, 160), random.randint(20, 60))
                pg.draw.circle(surface, dot_color, (dot_x, dot_y), dot_size)
                
        elif biome_type == BiomeType.FOREST:
            # Tree clusters - dark circular patches
            for i in range(random.randint(2, 5)):
                tree_x = x + random.randint(4, size-4)
                tree_y = y + random.randint(4, size-4)
                tree_size = random.randint(3, 8)
                tree_color = (random.randint(10, 40), random.randint(60, 90), random.randint(10, 40))
                pg.draw.circle(surface, tree_color, (tree_x, tree_y), tree_size)
                
        elif biome_type == BiomeType.DESERT:
            # Sand dunes - wavy light/dark patterns
            for i in range(random.randint(1, 4)):
                wave_y = y + random.randint(0, size)
                wave_color = (random.randint(220, 255), random.randint(180, 220), random.randint(140, 180))
                wave_height = random.randint(2, 6)
                wave_rect = pg.Rect(x, wave_y, size, wave_height)
                surface.fill(wave_color, wave_rect)
                
        elif biome_type == BiomeType.SNOW:
            # Snow patches - white irregular shapes
            for i in range(random.randint(2, 6)):
                snow_x = x + random.randint(0, size-6)
                snow_y = y + random.randint(0, size-6)
                snow_width = random.randint(4, 12)
                snow_height = random.randint(4, 12)
                snow_color = (255, 255, 255)
                snow_rect = pg.Rect(snow_x, snow_y, snow_width, snow_height)
                surface.fill(snow_color, snow_rect)
                
        elif biome_type == BiomeType.CITY:
            # Building ruins - rectangular gray patterns
            for i in range(random.randint(1, 3)):
                building_x = x + random.randint(2, size-8)
                building_y = y + random.randint(2, size-8)
                building_width = random.randint(6, 14)
                building_height = random.randint(6, 14)
                building_color = (random.randint(80, 120), random.randint(80, 120), random.randint(80, 120))
                building_rect = pg.Rect(building_x, building_y, building_width, building_height)
                surface.fill(building_color, building_rect)
                
                # Add windows/details
                if random.random() < 0.6:
                    window_color = (random.randint(40, 80), random.randint(40, 80), random.randint(40, 80))
                    window_rect = pg.Rect(building_x + 2, building_y + 2, 
                                        building_width - 4, building_height - 4)
                    surface.fill(window_color, window_rect)
        
        # Add occasional accent elements for all biomes
        if random.random() < 0.4:  # 40% chance
            accent_x = x + random.randint(1, size-1)
            accent_y = y + random.randint(1, size-1)
            accent_size = random.randint(1, 2)
            pg.draw.circle(surface, biome_info.accent_color, (accent_x, accent_y), accent_size)
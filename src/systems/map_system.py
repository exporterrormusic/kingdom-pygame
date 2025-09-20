"""
Map System for Kingdom Pygame
Handles TMX map loading, rendering, and collision detection.
"""

import pygame as pg
import xml.etree.ElementTree as ET
import os
from typing import List, Tuple, Optional, Set, Dict

class Tileset:
    """Represents a tileset with image and tile information."""
    
    def __init__(self, first_gid: int, source_path: str, base_path: str):
        self.first_gid = first_gid
        self.source_path = source_path
        self.base_path = base_path
        self.name = ""
        self.tile_width = 16
        self.tile_height = 16
        self.tile_count = 0
        self.columns = 0
        self.image_path = ""
        self.image = None
        
        self._load_tileset()
    
    def _load_tileset(self):
        """Load tileset from TSX file."""
        try:
            tsx_path = os.path.join(self.base_path, self.source_path)
            tree = ET.parse(tsx_path)
            root = tree.getroot()
            
            # Read tileset properties
            self.name = root.get('name', '')
            self.tile_width = int(root.get('tilewidth', 16))
            self.tile_height = int(root.get('tileheight', 16))
            self.tile_count = int(root.get('tilecount', 0))
            self.columns = int(root.get('columns', 1))
            
            # Find image element
            image_elem = root.find('image')
            if image_elem is not None:
                image_source = image_elem.get('source', '')
                # Convert relative path to absolute
                if image_source.startswith('../'):
                    # Handle relative paths like ../Downloads/GRASS+.png
                    self.image_path = os.path.join(self.base_path, image_source.replace('../Downloads/', ''))
                else:
                    self.image_path = os.path.join(self.base_path, image_source)
                
                # Load the tileset image
                if os.path.exists(self.image_path):
                    self.image = pg.image.load(self.image_path).convert_alpha()  # Enable alpha
                    # print(f"Loaded tileset image: {self.image_path}")
                else:
                    print(f"Tileset image not found: {self.image_path}")
            
        except Exception as e:
            print(f"Error loading tileset {self.source_path}: {e}")
    
    def get_tile_image(self, tile_id: int) -> Optional[pg.Surface]:
        """Get tile image by tile ID."""
        if not self.image or tile_id < self.first_gid:
            return None
        
        # Convert global tile ID to local tile ID
        local_id = tile_id - self.first_gid
        if local_id >= self.tile_count:
            return None
        
        # Calculate tile position in tileset
        tile_x = (local_id % self.columns) * self.tile_width
        tile_y = (local_id // self.columns) * self.tile_height
        
        # Extract tile from tileset image
        tile_rect = pg.Rect(tile_x, tile_y, self.tile_width, self.tile_height)
        tile_surface = pg.Surface((self.tile_width, self.tile_height), pg.SRCALPHA)  # Enable alpha
        tile_surface.blit(self.image, (0, 0), tile_rect)
        
        return tile_surface

class MapLayer:
    """Represents a single map layer."""
    
    def __init__(self, name: str, width: int, height: int, data: List[int]):
        self.name = name
        self.width = width
        self.height = height
        self.data = data  # Flattened list of tile IDs
    
    def get_tile_id(self, x: int, y: int) -> int:
        """Get tile ID at specific coordinates."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return 0
        return self.data[y * self.width + x]
    
    def is_solid_tile(self, x: int, y: int, solid_tile_ids: Set[int]) -> bool:
        """Check if tile at coordinates is solid."""
        tile_id = self.get_tile_id(x, y)
        return tile_id in solid_tile_ids

class TiledMap:
    """TMX map loader and manager."""
    
    def __init__(self, tmx_file_path: str):
        self.file_path = tmx_file_path
        self.width = 0
        self.height = 0
        self.tile_width = 16
        self.tile_height = 16
        self.layers = []
        self.tilesets = []  # List of tilesets
        
        # World scaling - stretch map to fill entire game world
        self.world_width = 3840
        self.world_height = 2160
        
        # Collision settings
        self.collision_layers = ["Tile Layer 2", "Tile Layer 3"]  # Both layers provide collision
        self.invisible_collision_layers = ["Tile Layer 3"]  # Only Layer 3 is invisible
        self.solid_tile_ids = {330, 286}  # Tile IDs that are solid
        
        self._load_map()
    
    def _load_map(self):
        """Load TMX map file."""
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            
            # Read map properties
            self.width = int(root.get('width', 0))
            self.height = int(root.get('height', 0))
            self.tile_width = int(root.get('tilewidth', 16))
            self.tile_height = int(root.get('tileheight', 16))
            
            # Load tilesets
            base_path = os.path.dirname(self.file_path)
            for tileset_elem in root.findall('tileset'):
                first_gid = int(tileset_elem.get('firstgid', 1))
                source = tileset_elem.get('source', '')
                if source:
                    tileset = Tileset(first_gid, source, base_path)
                    self.tilesets.append(tileset)
                    # print(f"Loaded tileset: {tileset.name} (firstgid: {first_gid})")
            
            # Load layers (they might be nested in groups) 
            # Use .//layer to find all layer elements regardless of nesting
            for layer_elem in root.findall('.//layer'):
                layer_name = layer_elem.get('name', '')
                layer_width = int(layer_elem.get('width', self.width))
                layer_height = int(layer_elem.get('height', self.height))
                
                # Parse CSV data
                data_elem = layer_elem.find('data')
                if data_elem is not None and data_elem.get('encoding') == 'csv':
                    csv_data = data_elem.text.strip()
                    tile_data = [int(x.strip()) for x in csv_data.split(',') if x.strip()]
                    
                    layer = MapLayer(layer_name, layer_width, layer_height, tile_data)
                    self.layers.append(layer)
                    
                    layer_type = "VISUAL"
                    if layer_name in self.collision_layers:
                        if layer_name in self.invisible_collision_layers:
                            layer_type = "INVISIBLE COLLISION"
                        else:
                            layer_type = "VISIBLE COLLISION"
                    
                    # print(f"Loaded layer: {layer_name} ({layer_width}x{layer_height}) - {layer_type}")
            
            # print(f"Map loaded: {self.width}x{self.height} tiles ({self.get_pixel_width()}x{self.get_pixel_height()} pixels)")
            
        except Exception as e:
            print(f"Error loading map {self.file_path}: {e}")
    
    def get_pixel_width(self) -> int:
        """Get map width in pixels (scaled to world size)."""
        return self.world_width
    
    def get_pixel_height(self) -> int:
        """Get map height in pixels (scaled to world size)."""
        return self.world_height
    
    def get_scaled_tile_width(self) -> float:
        """Get scaled tile width to fit world dimensions."""
        return self.world_width / self.width
    
    def get_scaled_tile_height(self) -> float:
        """Get scaled tile height to fit world dimensions."""
        return self.world_height / self.height
    
    def get_tile_image(self, tile_id: int) -> Optional[pg.Surface]:
        """Get tile image by tile ID from appropriate tileset."""
        if tile_id == 0:
            return None  # Empty tile
        
        # Find the appropriate tileset for this tile ID
        tileset = None
        for ts in reversed(self.tilesets):  # Check in reverse order to find the right tileset
            if tile_id >= ts.first_gid:
                tileset = ts
                break
        
        if tileset:
            tile_image = tileset.get_tile_image(tile_id)
            if tile_image:
                # Convert to per-pixel alpha and set proper alpha handling
                tile_image = tile_image.convert_alpha()
                # If the image has a colorkey (transparency), preserve it
                if tile_image.get_colorkey():
                    tile_image = tile_image.convert_alpha()
            return tile_image
        
        return None
    
    def get_layer_by_name(self, name: str) -> Optional[MapLayer]:
        """Get layer by name."""
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None
    
    def world_to_tile_coords(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to tile coordinates (accounting for scaling)."""
        # World bounds: -1920 to +1920 (width), -1080 to +1080 (height)
        # Map should fill this entire space
        
        # Convert world coords to map space (0 to world_width/height)
        map_space_x = world_x + self.world_width / 2  # Shift from [-1920, 1920] to [0, 3840]
        map_space_y = world_y + self.world_height / 2  # Shift from [-1080, 1080] to [0, 2160]
        
        # Convert to tile coordinates using scaled tile size
        scaled_tile_width = self.get_scaled_tile_width()
        scaled_tile_height = self.get_scaled_tile_height()
        
        tile_x = int(map_space_x / scaled_tile_width)
        tile_y = int(map_space_y / scaled_tile_height)
        
        return tile_x, tile_y
    
    def is_collision_at_world_pos(self, world_x: float, world_y: float) -> bool:
        """Check if there's a collision at world position."""
        tile_x, tile_y = self.world_to_tile_coords(world_x, world_y)
        
        # Check collision layers
        for layer in self.layers:
            if layer.name in self.collision_layers:
                if layer.is_solid_tile(tile_x, tile_y, self.solid_tile_ids):
                    return True
        
        return False
    
    def get_collision_rect_at_tile(self, tile_x: int, tile_y: int) -> Optional[pg.Rect]:
        """Get collision rectangle for tile at given tile coordinates."""
        # Check if any collision layer has a solid tile here
        has_collision = False
        for layer in self.layers:
            if layer.name in self.collision_layers:
                if layer.is_solid_tile(tile_x, tile_y, self.solid_tile_ids):
                    has_collision = True
                    break
        
        if not has_collision:
            return None
        
        # Convert back to world coordinates using scaled tile dimensions
        scaled_tile_width = self.get_scaled_tile_width()
        scaled_tile_height = self.get_scaled_tile_height()
        
        # Calculate world position
        world_x = tile_x * scaled_tile_width - self.world_width / 2
        world_y = tile_y * scaled_tile_height - self.world_height / 2
        
        return pg.Rect(world_x, world_y, scaled_tile_width, scaled_tile_height)
    
    def get_nearby_collision_rects(self, center_x: float, center_y: float, radius: float) -> List[pg.Rect]:
        """Get collision rectangles near a center point within radius."""
        collision_rects = []
        
        # Calculate tile range to check using scaled dimensions
        scaled_tile_width = self.get_scaled_tile_width()
        scaled_tile_height = self.get_scaled_tile_height()
        tile_radius_x = int(radius / scaled_tile_width) + 1
        tile_radius_y = int(radius / scaled_tile_height) + 1
        center_tile_x, center_tile_y = self.world_to_tile_coords(center_x, center_y)
        
        for y in range(center_tile_y - tile_radius_y, center_tile_y + tile_radius_y + 1):
            for x in range(center_tile_x - tile_radius_x, center_tile_x + tile_radius_x + 1):
                rect = self.get_collision_rect_at_tile(x, y)
                if rect:
                    # Check if rect is within radius
                    rect_center_x = rect.centerx
                    rect_center_y = rect.centery
                    distance = ((rect_center_x - center_x) ** 2 + (rect_center_y - center_y) ** 2) ** 0.5
                    if distance <= radius:
                        collision_rects.append(rect)
        
        return collision_rects
    
    def render_debug(self, screen: pg.Surface, camera_offset: Tuple[float, float] = (0, 0)):
        """Render debug visualization of collision tiles."""
        scaled_tile_width = self.get_scaled_tile_width()
        scaled_tile_height = self.get_scaled_tile_height()
        
        # Only render collision layers for debugging
        for layer in self.layers:
            if layer.name in self.collision_layers:
                for y in range(layer.height):
                    for x in range(layer.width):
                        tile_id = layer.get_tile_id(x, y)
                        if tile_id in self.solid_tile_ids:
                            # Calculate world position using scaled coordinates
                            world_x = x * scaled_tile_width - self.world_width / 2
                            world_y = y * scaled_tile_height - self.world_height / 2
                            
                            # Apply camera offset
                            screen_x = world_x + camera_offset[0]
                            screen_y = world_y + camera_offset[1]
                            
                            # Only draw if on screen
                            if (-scaled_tile_width <= screen_x <= screen.get_width() and
                                -scaled_tile_height <= screen_y <= screen.get_height()):
                                
                                # Different colors for different layers/tile types
                                if layer.name == "Tile Layer 2" and tile_id == 330:
                                    color = (255, 0, 0, 100)  # Red for border walls
                                elif layer.name == "Tile Layer 3" and tile_id == 286:
                                    color = (0, 255, 0, 100)  # Green for obstacles
                                else:
                                    color = (255, 255, 0, 100)  # Yellow for other
                                
                                # Draw collision tile with scaled dimensions
                                rect = pg.Rect(screen_x, screen_y, scaled_tile_width, scaled_tile_height)
                                pg.draw.rect(screen, color[:3], rect, 2)  # Draw border only
    
    def render(self, screen: pg.Surface, camera_offset: Tuple[float, float] = (0, 0), debug_mode: bool = False):
        """Render the map with textures."""
        scaled_tile_width = self.get_scaled_tile_width()
        scaled_tile_height = self.get_scaled_tile_height()
        
        # Render visual layers: Layer 1 (background) and Layer 2 (obstacles)
        # Skip Layer 3 as it's invisible collision boundaries only
        for layer in self.layers:
            # Render Layer 1 (background) and Layer 2 (visible obstacles)
            # Skip Layer 3 (invisible collision boundaries)
            if layer.name == "Tile Layer 3":
                continue
            for y in range(layer.height):
                for x in range(layer.width):
                    tile_id = layer.get_tile_id(x, y)
                    if tile_id == 0:
                        continue  # Skip empty tiles
                    
                    # Calculate world position using scaled coordinates
                    world_x = x * scaled_tile_width - self.world_width / 2
                    world_y = y * scaled_tile_height - self.world_height / 2
                    
                    # Apply camera offset
                    screen_x = world_x + camera_offset[0]
                    screen_y = world_y + camera_offset[1]
                    
                    # Only render if on screen (with some margin for performance)
                    if (-scaled_tile_width <= screen_x <= screen.get_width() and
                        -scaled_tile_height <= screen_y <= screen.get_height()):
                        
                        # Get tile image
                        tile_image = self.get_tile_image(tile_id)
                        if tile_image:
                            # Scale tile image to match scaled tile size
                            scaled_image = pg.transform.scale(tile_image, (int(scaled_tile_width), int(scaled_tile_height)))
                            screen.blit(scaled_image, (screen_x, screen_y))
        
        # Render debug overlay if requested (collision boundaries)
        if debug_mode:
            self.render_debug(screen, camera_offset)

class MapManager:
    """Manages map loading and collision detection for the game."""
    
    def __init__(self):
        self.current_map = None
        self.debug_render = False
    
    def load_map(self, map_name: str) -> bool:
        """Load a map by name."""
        map_path = os.path.join("assets", "maps", f"{map_name}.tmx")
        
        if not os.path.exists(map_path):
            print(f"Map file not found: {map_path}")
            return False
        
        try:
            self.current_map = TiledMap(map_path)
            print(f"Successfully loaded map: {map_name}")
            return True
        except Exception as e:
            print(f"Failed to load map {map_name}: {e}")
            return False
    
    def is_position_blocked(self, x: float, y: float) -> bool:
        """Check if position is blocked by map collision."""
        if not self.current_map:
            return False
        
        return self.current_map.is_collision_at_world_pos(x, y)
    
    def get_collision_rects_near(self, x: float, y: float, radius: float) -> List[pg.Rect]:
        """Get collision rectangles near position."""
        if not self.current_map:
            return []
        
        return self.current_map.get_nearby_collision_rects(x, y, radius)
    
    def render_debug(self, screen: pg.Surface, camera_offset: Tuple[float, float] = (0, 0)):
        """Render debug visualization."""
        if self.debug_render and self.current_map:
            self.current_map.render_debug(screen, camera_offset)
    
    def render_map(self, screen: pg.Surface, camera_offset: Tuple[float, float] = (0, 0)):
        """Render the map with textures."""
        if self.current_map:
            self.current_map.render(screen, camera_offset, self.debug_render)
    
    def toggle_debug_render(self):
        """Toggle debug rendering on/off."""
        self.debug_render = not self.debug_render
        print(f"Map debug rendering: {'ON' if self.debug_render else 'OFF'}")
    
    def get_map_bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """Get map boundaries as (min_x, min_y, max_x, max_y)."""
        if not self.current_map:
            return None
        
        map_pixel_width = self.current_map.get_pixel_width()
        map_pixel_height = self.current_map.get_pixel_height()
        
        # Assuming map is centered at origin
        min_x = -map_pixel_width // 2
        min_y = -map_pixel_height // 2
        max_x = min_x + map_pixel_width
        max_y = min_y + map_pixel_height
        
        return (min_x, min_y, max_x, max_y)
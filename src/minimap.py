#!/usr/bin/env python3
"""
Mini-Map System for Kingdom Pygame
Shows player location, enemies, NPCs, and base in top-right corner
"""

import pygame as pg
import math
from typing import List, Tuple, Optional

class MiniMap:
    """Mini-map that displays world overview with entities."""
    
    def __init__(self, size: int = 150, margin: int = 20):
        """
        Initialize the mini-map.
        
        Args:
            size: Size of the mini-map height in pixels (width will be calculated)
            margin: Margin from screen edge
        """
        self.height = size
        self.margin = margin
        
        # Rectangular world dimensions
        self.world_width = 3840   # World is 3840 wide (-1920 to +1920)
        self.world_height = 2160   # World is 2160 high (-1080 to +1080)
        
        # Calculate mini-map width to maintain aspect ratio
        aspect_ratio = self.world_width / self.world_height  # 3840/2160 = 1.78 (16:9)
        self.width = int(self.height * aspect_ratio)  # Make mini-map rectangular
        
        self.base_radius = 250   # Safe zone radius
        
        # Colors for different entities
        self.colors = {
            'background': (30, 30, 30, 180),      # Semi-transparent dark background
            'border': (100, 100, 100, 255),       # Gray border
            'world_bounds': (60, 60, 60, 255),    # Dark gray world bounds
            'safe_zone': (80, 80, 0, 255),        # Dark yellow safe zone
            'player': (100, 150, 255, 255),       # Blue player
            'enemy': (255, 50, 50, 255),          # Red enemies
            'npc': (50, 255, 50, 255),            # Green NPCs
            'base': (255, 255, 100, 255),         # Yellow base
            'objective': (255, 150, 0, 255)       # Orange objectives
        }
        
        # Create rectangular surface for mini-map with per-pixel alpha
        self.surface = pg.Surface((self.width, self.height), pg.SRCALPHA)
        
    def world_to_minimap(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to mini-map pixel coordinates."""
        # Normalize world coordinates: x (-1920 to +1920) to (0 to 1), y (-1080 to +1080) to (0 to 1)
        normalized_x = (world_x + 1920) / self.world_width   # -1920 to +1920 -> 0 to 1
        normalized_y = (world_y + 1080) / self.world_height  # -1080 to +1080 -> 0 to 1
        
        # Convert to mini-map coordinates
        map_x = int(normalized_x * self.width)   # 0 to width
        map_y = int(normalized_y * self.height)  # 0 to height
        
        # Clamp to mini-map bounds
        map_x = max(0, min(self.width - 1, map_x))
        map_y = max(0, min(self.height - 1, map_y))
        
        return map_x, map_y
    
    def render(self, screen: pg.Surface, player_pos: Tuple[float, float],
               enemies: List = None, npcs: List = None, 
               objectives: List = None) -> None:
        """
        Render the mini-map to the screen.
        
        Args:
            screen: Main game screen surface
            player_pos: Player world coordinates (x, y)
            enemies: List of enemy objects with .pos attributes
            npcs: List of NPC objects with .pos attributes
            objectives: List of objective objects with position data
        """
        # Clear the mini-map surface
        self.surface.fill((0, 0, 0, 0))  # Transparent
        
        # Draw background
        pg.draw.rect(self.surface, self.colors['background'], 
                    (0, 0, self.width, self.height))
        
        # Draw world bounds outline
        pg.draw.rect(self.surface, self.colors['world_bounds'], 
                    (0, 0, self.width, self.height), 2)
        
        # Draw safe zone (base area)
        base_map_x, base_map_y = self.world_to_minimap(0, 0)  # Base at world center
        # Use smaller dimension for radius calculation to maintain proper scaling
        min_dimension = min(self.width, self.height)
        safe_zone_radius = int((self.base_radius / min(self.world_width, self.world_height)) * min_dimension)
        if safe_zone_radius > 0:
            pg.draw.circle(self.surface, self.colors['safe_zone'],
                         (base_map_x, base_map_y), safe_zone_radius, 1)
        
        # Draw base marker (center of safe zone)
        pg.draw.circle(self.surface, self.colors['base'],
                     (base_map_x, base_map_y), 3)
        
        # Draw enemies
        if enemies:
            for enemy in enemies:
                if hasattr(enemy, 'pos'):
                    enemy_x, enemy_y = self.world_to_minimap(enemy.pos.x, enemy.pos.y)
                    pg.draw.circle(self.surface, self.colors['enemy'],
                                 (enemy_x, enemy_y), 2)
        
        # Draw NPCs
        if npcs:
            for npc in npcs:
                if hasattr(npc, 'pos'):
                    npc_x, npc_y = self.world_to_minimap(npc.pos.x, npc.pos.y)
                    pg.draw.circle(self.surface, self.colors['npc'],
                                 (npc_x, npc_y), 2)
        
        # Draw objectives
        if objectives:
            for obj in objectives:
                # Handle different objective position formats
                obj_pos = None
                if hasattr(obj, 'pos'):
                    obj_pos = (obj.pos.x, obj.pos.y)
                elif hasattr(obj, 'position'):
                    obj_pos = obj.position
                elif isinstance(obj, (tuple, list)) and len(obj) >= 2:
                    obj_pos = obj[:2]
                
                if obj_pos:
                    obj_x, obj_y = self.world_to_minimap(obj_pos[0], obj_pos[1])
                    pg.draw.circle(self.surface, self.colors['objective'],
                                 (obj_x, obj_y), 2)
        
        # Draw player (on top of everything)
        player_x, player_y = self.world_to_minimap(player_pos[0], player_pos[1])
        pg.draw.circle(self.surface, self.colors['player'],
                     (player_x, player_y), 3)
        
        # Draw border
        pg.draw.rect(self.surface, self.colors['border'], 
                    (0, 0, self.width, self.height), 2)
        
        # Calculate position in top-right corner
        screen_width = screen.get_width()
        pos_x = screen_width - self.width - self.margin
        pos_y = self.margin
        
        # Blit to main screen
        screen.blit(self.surface, (pos_x, pos_y))
        
        # Add mini-map label
        font = pg.font.Font(None, 24)
        label = font.render("MAP", True, (255, 255, 255))
        label_rect = label.get_rect()
        label_rect.centerx = pos_x + self.width // 2
        label_rect.bottom = pos_y - 5
        screen.blit(label, label_rect)
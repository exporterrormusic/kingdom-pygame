"""
Resource System for Kingdom-Pygame
Handles resource nodes, collection, and inventory management.
"""

import pygame as pg
import math
import random
from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

class ResourceType(Enum):
    """Types of resources that can be collected."""
    WOOD = "wood"
    METAL = "metal" 
    CRYSTAL = "crystal"
    STONE = "stone"
    ENERGY = "energy"

@dataclass
class ResourceInfo:
    """Information about a resource type."""
    name: str
    color: Tuple[int, int, int]
    rarity: float  # 0.0 to 1.0, higher = rarer
    value: int     # Base value per unit
    description: str

class ResourceNode:
    """A resource node that can be harvested in the world."""
    
    def __init__(self, x: float, y: float, resource_type: ResourceType, amount: int, biome_bonus: float = 1.0):
        """Initialize a resource node."""
        self.pos = pg.Vector2(x, y)
        self.resource_type = resource_type
        self.max_amount = amount
        self.current_amount = amount
        self.biome_bonus = biome_bonus  # Multiplier based on biome danger level
        self.size = 20  # Visual size
        self.collection_radius = 40  # How close player needs to be
        self.is_depleted = False
        self.respawn_time = 60.0  # Seconds until respawn
        self.deplete_timer = 0.0
        
    def can_collect(self) -> bool:
        """Check if this node can be collected from."""
        return not self.is_depleted and self.current_amount > 0
        
    def collect(self, amount: int = 1) -> int:
        """Collect resources from this node. Returns actual amount collected."""
        if not self.can_collect():
            return 0
            
        collected = min(amount, self.current_amount)
        self.current_amount -= collected
        
        if self.current_amount <= 0:
            self.is_depleted = True
            self.deplete_timer = 0.0
            
        return collected
        
    def update(self, dt: float):
        """Update the resource node."""
        if self.is_depleted:
            self.deplete_timer += dt
            if self.deplete_timer >= self.respawn_time:
                # Respawn with some amount
                self.current_amount = max(1, int(self.max_amount * 0.7))  # 70% respawn
                self.is_depleted = False
                self.deplete_timer = 0.0
                
    def render(self, screen: pg.Surface, offset: Tuple[int, int]):
        """Render the resource node."""
        if self.is_depleted:
            return  # Don't render depleted nodes
            
        # Apply camera offset
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        # Only render if on screen
        if -50 <= render_x <= screen.get_width() + 50 and -50 <= render_y <= screen.get_height() + 50:
            # Get resource info for color
            resource_info = RESOURCE_TYPES[self.resource_type]
            
            # Draw node with size based on amount
            node_radius = int(self.size * (0.5 + 0.5 * (self.current_amount / self.max_amount)))
            
            # Outer glow
            glow_color = tuple(min(255, c + 50) for c in resource_info.color)
            pg.draw.circle(screen, glow_color, (render_x, render_y), node_radius + 3)
            
            # Main node
            pg.draw.circle(screen, resource_info.color, (render_x, render_y), node_radius)
            
            # Inner shine
            shine_color = tuple(min(255, c + 100) for c in resource_info.color)
            pg.draw.circle(screen, shine_color, (render_x - 3, render_y - 3), max(3, node_radius // 2))
            
    def is_near_player(self, player_pos: pg.Vector2) -> bool:
        """Check if player is close enough to collect."""
        return self.pos.distance_to(player_pos) <= self.collection_radius

class ResourceManager:
    """Manages resource nodes and collection throughout the world."""
    
    def __init__(self):
        """Initialize the resource manager."""
        self.nodes: List[ResourceNode] = []
        self.player_inventory: Dict[ResourceType, int] = {
            ResourceType.WOOD: 0,
            ResourceType.METAL: 0,
            ResourceType.CRYSTAL: 0,
            ResourceType.STONE: 0,
            ResourceType.ENERGY: 0
        }
        self.inventory_capacity = 100  # Total inventory slots
        
    def get_total_inventory_used(self) -> int:
        """Get total number of inventory slots used."""
        return sum(self.player_inventory.values())
        
    def can_collect_resource(self, resource_type: ResourceType, amount: int = 1) -> bool:
        """Check if player can collect this resource."""
        return self.get_total_inventory_used() + amount <= self.inventory_capacity
        
    def add_resource(self, resource_type: ResourceType, amount: int) -> int:
        """Add resources to player inventory. Returns amount actually added."""
        if not self.can_collect_resource(resource_type, amount):
            # Calculate how much we can actually add
            available_space = self.inventory_capacity - self.get_total_inventory_used()
            amount = min(amount, available_space)
            
        if amount > 0:
            self.player_inventory[resource_type] += amount
            
        return amount
        
    def generate_resource_nodes_for_chunk(self, chunk_x: int, chunk_y: int, chunk_size: int, biome_type, biome_danger_level: int):
        """Generate resource nodes for a newly loaded chunk."""
        from src.world_manager import BiomeType  # Import here to avoid circular imports
        
        # Base resource generation parameters
        base_density = 0.15  # Base chance per area unit
        danger_multiplier = 1.0 + (biome_danger_level - 1) * 0.3  # Higher danger = more resources
        
        # Biome-specific resource preferences
        biome_resources = {
            BiomeType.FIELD: [(ResourceType.WOOD, 0.4), (ResourceType.STONE, 0.3), (ResourceType.METAL, 0.2), (ResourceType.CRYSTAL, 0.1)],
            BiomeType.FOREST: [(ResourceType.WOOD, 0.6), (ResourceType.CRYSTAL, 0.2), (ResourceType.STONE, 0.1), (ResourceType.METAL, 0.1)],
            BiomeType.DESERT: [(ResourceType.METAL, 0.4), (ResourceType.CRYSTAL, 0.3), (ResourceType.STONE, 0.2), (ResourceType.ENERGY, 0.1)],
            BiomeType.SNOW: [(ResourceType.CRYSTAL, 0.4), (ResourceType.ENERGY, 0.3), (ResourceType.METAL, 0.2), (ResourceType.STONE, 0.1)],
            BiomeType.CITY: [(ResourceType.METAL, 0.5), (ResourceType.ENERGY, 0.3), (ResourceType.CRYSTAL, 0.1), (ResourceType.STONE, 0.1)]
        }
        
        # Calculate number of nodes to generate
        area = chunk_size * chunk_size
        expected_nodes = int(area * base_density * danger_multiplier / 10000)  # Scale down for reasonable density
        actual_nodes = max(1, random.randint(expected_nodes // 2, expected_nodes * 2))
        
        # Generate nodes
        for _ in range(actual_nodes):
            # Random position within chunk
            node_x = chunk_x * chunk_size + random.randint(100, chunk_size - 100)
            node_y = chunk_y * chunk_size + random.randint(100, chunk_size - 100)
            
            # Select resource type based on biome preferences
            resource_weights = biome_resources.get(biome_type, biome_resources[BiomeType.FIELD])
            resource_type = random.choices(
                [r[0] for r in resource_weights],
                weights=[r[1] for r in resource_weights],
                k=1
            )[0]
            
            # Calculate resource amount based on danger level
            base_amount = random.randint(3, 8)
            bonus_amount = int(base_amount * (biome_danger_level - 1) * 0.5)
            total_amount = base_amount + bonus_amount
            
            # Create node
            node = ResourceNode(
                node_x, node_y, 
                resource_type, 
                total_amount,
                biome_bonus=danger_multiplier
            )
            self.nodes.append(node)
            
    def update(self, dt: float):
        """Update all resource nodes."""
        for node in self.nodes:
            node.update(dt)
            
    def render(self, screen: pg.Surface, offset: Tuple[int, int]):
        """Render all visible resource nodes."""
        for node in self.nodes:
            node.render(screen, offset)
            
    def get_nearby_nodes(self, player_pos: pg.Vector2, radius: float = 100) -> List[ResourceNode]:
        """Get resource nodes near the player."""
        nearby = []
        for node in self.nodes:
            if not node.is_depleted and node.pos.distance_to(player_pos) <= radius:
                nearby.append(node)
        return nearby
        
    def try_collect_resources(self, player_pos: pg.Vector2) -> Dict[ResourceType, int]:
        """Try to collect resources near the player. Returns what was collected."""
        collected = {}
        
        for node in self.nodes:
            if node.is_near_player(player_pos) and node.can_collect():
                # Try to collect from this node
                collected_amount = node.collect(1)  # Collect 1 at a time for now
                
                if collected_amount > 0:
                    # Try to add to player inventory
                    actually_added = self.add_resource(node.resource_type, collected_amount)
                    
                    if actually_added > 0:
                        if node.resource_type not in collected:
                            collected[node.resource_type] = 0
                        collected[node.resource_type] += actually_added
                        
                    # If we couldn't add all collected, put some back in the node
                    if actually_added < collected_amount:
                        node.current_amount += (collected_amount - actually_added)
                        
        return collected

# Resource type definitions
RESOURCE_TYPES = {
    ResourceType.WOOD: ResourceInfo("Wood", (139, 69, 19), 0.2, 1, "Common building material from trees"),
    ResourceType.METAL: ResourceInfo("Metal", (169, 169, 169), 0.4, 2, "Durable material for advanced construction"),
    ResourceType.CRYSTAL: ResourceInfo("Crystal", (138, 43, 226), 0.7, 5, "Rare energy-conductive crystals"),
    ResourceType.STONE: ResourceInfo("Stone", (105, 105, 105), 0.1, 1, "Basic construction material"),
    ResourceType.ENERGY: ResourceInfo("Energy", (255, 215, 0), 0.8, 8, "Concentrated energy cores")
}
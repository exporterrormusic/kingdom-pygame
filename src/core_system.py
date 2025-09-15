"""
Rapture Core System for Kingdom-Pygame
Handles Rapture Cores (single currency), collection, drops, and chests.
"""

import pygame as pg
import math
import random
from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

class CoreType(Enum):
    """Single core type - Rapture Core"""
    RAPTURE_CORE = "rapture_core"

@dataclass
class CoreInfo:
    """Information about Rapture Cores."""
    name: str
    color: Tuple[int, int, int]
    glow_color: Tuple[int, int, int]
    size: int
    description: str

# Core information
CORE_INFO = CoreInfo(
    name="Rapture Core",
    color=(255, 50, 50),      # Deep red
    glow_color=(255, 120, 120), # Bright red glow
    size=8,                   # Smaller than old resources
    description="Glowing red sci-fi energy cores"
)

class RaptureCore:
    """A single Rapture Core that can be collected."""
    
    def __init__(self, x: float, y: float, amount: int = 1):
        """Initialize a Rapture Core."""
        self.pos = pg.Vector2(x, y)
        self.original_pos = pg.Vector2(x, y)  # Store original position
        self.amount = amount
        self.collection_radius = 50   # Small radius for collection animation start
        self.magnetic_range = 275     # Moderate range - between original 500 and previous 150
        self.collected = False
        self.being_collected = False  # Animation state for collection
        self.collection_timer = 0.0   # Timer for collection animation
        self.collection_duration = 0.3  # How long the collection animation takes
        self.glow_phase = random.uniform(0, math.pi * 2)  # For pulsing glow effect
        self.float_phase = random.uniform(0, math.pi * 2)  # For floating animation
        self.being_attracted = False  # Whether core is being magnetically pulled
        
    def update(self, dt: float, player_pos: pg.Vector2 = None):
        """Update the core (glow animation and magnetic attraction)."""
        self.glow_phase += dt * 4.0  # Faster pulsing for evil effect
        self.float_phase += dt * 2.0  # Floating up and down
        
        # Handle collection animation
        if self.being_collected:
            self.collection_timer += dt
            if self.collection_timer >= self.collection_duration:
                self.collected = True  # Mark as fully collected
                return
                
        if player_pos and not self.collected and not self.being_collected:
            distance = self.pos.distance_to(player_pos)
            
            # Start collection animation when very close
            if distance <= self.collection_radius:
                self.being_collected = True
                self.collection_timer = 0.0
                return
            
            # Magnetic attraction when player gets close
            if distance <= self.magnetic_range:
                self.being_attracted = True
                # Pull toward player with increasing strength as they get closer
                attraction_strength = (self.magnetic_range - distance) / self.magnetic_range
                pull_speed = 1200 * attraction_strength * dt  # Much stronger magnetic pull (doubled from 600)
                
                # Calculate direction to player
                if distance > 1:  # Avoid division by zero
                    direction = (player_pos - self.pos).normalize()
                    self.pos += direction * pull_speed
            else:
                self.being_attracted = False
                # Gentle float back toward original position when not attracted
                if self.pos.distance_to(self.original_pos) > 5:
                    return_direction = (self.original_pos - self.pos).normalize()
                    self.pos += return_direction * 50 * dt
        
    def can_collect(self, player_pos: pg.Vector2) -> bool:
        """Check if core is ready to be collected (animation finished)."""
        return self.collected and not self.being_collected
        
    def is_ready_for_collection(self, player_pos: pg.Vector2) -> bool:
        """Check if player is close enough to start collection animation."""
        if self.collected or self.being_collected:
            return False
        distance = self.pos.distance_to(player_pos)
        return distance <= self.collection_radius
        
    def collect(self) -> int:
        """Collect this core. Returns amount collected."""
        if not self.collected:
            return 0
        return self.amount
        
    def render(self, screen: pg.Surface, offset: Tuple[int, int]):
        """Render the Rapture Core as a simple red eye with inner glow."""
        if self.collected and not self.being_collected:
            return
            
        # Collection animation effects
        collection_progress = 0.0
        if self.being_collected:
            collection_progress = min(1.0, self.collection_timer / self.collection_duration)
            
        # Apply camera offset and floating animation
        float_offset = math.sin(self.float_phase) * 2  # Gentle floating
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1] + float_offset)
        
        # Only render if on screen
        if -100 <= render_x <= screen.get_width() + 100 and -100 <= render_y <= screen.get_height() + 100:
            # Scale down the core during collection
            size_multiplier = 1.0 - (collection_progress * 0.8)  # Shrink to 20% of original size
            outer_size = int(CORE_INFO.size * 1.5 * size_multiplier)  # Outer red circle
            inner_size = int(CORE_INFO.size * 0.6 * size_multiplier)  # Inner glow
            
            # Don't render if too small
            if outer_size < 1:
                return
            
            # Pulsing intensity for the inner glow
            pulse_intensity = 0.6 + 0.4 * math.sin(self.glow_phase)
            attraction_boost = 1.5 if self.being_attracted else 1.0
            glow_intensity = pulse_intensity * attraction_boost
            
            # Collection animation effects
            if self.being_collected:
                glow_intensity *= (1.0 + collection_progress * 2.0)  # Bright flash during collection
                # Add screen shake effect
                shake_amount = collection_progress * 2
                render_x += int(math.sin(self.collection_timer * 30) * shake_amount)
                render_y += int(math.cos(self.collection_timer * 30) * shake_amount)
            
            # Draw outer red circle (eye outline)
            pg.draw.circle(screen, (150, 20, 20), (render_x, render_y), outer_size)
            
            # Draw inner glowing center (pupil/iris)
            if inner_size > 0:
                inner_alpha = int(180 * glow_intensity)
                inner_color = (255, min(255, 40 + int(inner_alpha * 0.3)), 40)
                pg.draw.circle(screen, inner_color, (render_x, render_y), inner_size)
                
            # Add a subtle outer glow for the eye effect
            if outer_size > 2:
                glow_size = outer_size + 2
                glow_surf = pg.Surface((glow_size * 2, glow_size * 2), pg.SRCALPHA)
                glow_alpha = int(40 * glow_intensity * (1.0 - collection_progress * 0.5))
                glow_color = (200, 50, 50, max(1, glow_alpha))
                pg.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                screen.blit(glow_surf, (render_x - glow_size, render_y - glow_size), special_flags=pg.BLEND_ADD)
class CoreChest:
    """A rare chest containing Rapture Cores."""
    
    def __init__(self, x: float, y: float, core_amount: int):
        """Initialize a core chest."""
        self.pos = pg.Vector2(x, y)
        self.core_amount = core_amount
        self.collection_radius = 100  # Reasonable chest opening range
        self.opened = False
        self.size = 60  # Much larger chest size
        self.glow_phase = random.uniform(0, math.pi * 2)  # Glowing animation
        self.health = 50  # Chest health - must be shot to open
        self.max_health = 50
        self.exploding = False
        self.explosion_timer = 0.0
        self.explosion_duration = 0.5
        
    def take_damage(self, damage: int) -> bool:
        """Damage the chest. Returns True if chest is destroyed."""
        if self.opened or self.exploding:
            return False
        
        self.health -= damage
        if self.health <= 0:
            self.exploding = True
            self.explosion_timer = 0.0
            return True
        return False
        
    def update(self, dt: float, core_manager) -> List:
        """Update chest state and return any cores to spawn."""
        cores_to_spawn = []
        
        if self.exploding:
            self.explosion_timer += dt
            
            # Spawn cores when explosion starts
            if self.explosion_timer <= dt:  # First frame of explosion
                # Create cores that will explode outward
                for i in range(self.core_amount):
                    angle = (i / self.core_amount) * math.pi * 2  # Distribute evenly around circle
                    distance = random.uniform(50, 120)  # Random distance from chest
                    
                    core_x = self.pos.x + math.cos(angle) * distance
                    core_y = self.pos.y + math.sin(angle) * distance
                    
                    core = RaptureCore(core_x, core_y, 1)
                    cores_to_spawn.append(core)
                    
            # Mark as opened when explosion finishes
            if self.explosion_timer >= self.explosion_duration:
                self.opened = True
                self.exploding = False
                
        return cores_to_spawn
        
    def get_collision_rect(self) -> pg.Rect:
        """Get collision rectangle for bullet collision detection."""
        return pg.Rect(self.pos.x - self.size//2, self.pos.y - self.size//2, self.size, self.size)
        
    def render(self, screen: pg.Surface, offset: Tuple[int, int]):
        """Render the massive, glowing chest."""
        if self.opened:
            return  # Don't render opened chests
            
        # Update glow animation
        self.glow_phase += 0.02  # Gentle glow pulsing
            
        # Apply camera offset
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        # Only render if on screen with larger bounds for big chest
        if -100 <= render_x <= screen.get_width() + 100 and -100 <= render_y <= screen.get_height() + 100:
            # Glowing aura effect around chest
            glow_intensity = 0.6 + 0.4 * math.sin(self.glow_phase)
            glow_size = int(self.size * 1.8 * glow_intensity)
            
            # Outer magical aura
            aura_surf = pg.Surface((glow_size * 2, glow_size * 2), pg.SRCALPHA)
            aura_color = (255, 215, 0, 40)  # Golden aura, semi-transparent
            pg.draw.circle(aura_surf, aura_color, (glow_size, glow_size), glow_size)
            screen.blit(aura_surf, (render_x - glow_size, render_y - glow_size), 
                       special_flags=pg.BLEND_ADD)
            
            # Inner golden glow
            inner_glow_size = int(self.size * 1.2 * glow_intensity)
            inner_glow_surf = pg.Surface((inner_glow_size * 2, inner_glow_size * 2), pg.SRCALPHA)
            inner_glow_color = (255, 215, 0, 80)  # Brighter golden glow
            pg.draw.circle(inner_glow_surf, inner_glow_color, (inner_glow_size, inner_glow_size), inner_glow_size)
            screen.blit(inner_glow_surf, (render_x - inner_glow_size, render_y - inner_glow_size), 
                       special_flags=pg.BLEND_ADD)
            
            # Draw massive chest with elaborate design
            chest_color = (101, 67, 33)      # Dark brown wood
            highlight_color = (139, 92, 46)  # Lighter brown highlight
            shadow_color = (67, 44, 22)     # Dark shadow
            gold_color = (255, 215, 0)      # Gold accents
            
            # Main chest body (larger)
            chest_rect = pg.Rect(render_x - self.size//2, render_y - self.size//2, 
                               self.size, self.size)
            pg.draw.rect(screen, chest_color, chest_rect)
            
            # 3D highlight effect
            highlight_rect = pg.Rect(render_x - self.size//2 + 3, render_y - self.size//2 + 3, 
                                   self.size - 6, self.size - 6)
            pg.draw.rect(screen, highlight_color, highlight_rect, 3)
            
            # Shadow/depth
            shadow_rect = pg.Rect(render_x - self.size//2 + 6, render_y - self.size//2 + 6, 
                                self.size - 12, self.size - 12)
            pg.draw.rect(screen, shadow_color, shadow_rect, 2)
            
            # Golden metal bands (horizontal)
            band_thickness = 6
            # Top band
            top_band = pg.Rect(render_x - self.size//2, render_y - self.size//2 + 10, 
                             self.size, band_thickness)
            pg.draw.rect(screen, gold_color, top_band)
            
            # Middle band
            middle_band = pg.Rect(render_x - self.size//2, render_y - band_thickness//2, 
                                self.size, band_thickness)
            pg.draw.rect(screen, gold_color, middle_band)
            
            # Bottom band
            bottom_band = pg.Rect(render_x - self.size//2, render_y + self.size//2 - 16, 
                                self.size, band_thickness)
            pg.draw.rect(screen, gold_color, bottom_band)
            
            # Golden corner reinforcements
            corner_size = 12
            corners = [
                (render_x - self.size//2, render_y - self.size//2),  # Top-left
                (render_x + self.size//2 - corner_size, render_y - self.size//2),  # Top-right
                (render_x - self.size//2, render_y + self.size//2 - corner_size),  # Bottom-left
                (render_x + self.size//2 - corner_size, render_y + self.size//2 - corner_size)  # Bottom-right
            ]
            for corner_x, corner_y in corners:
                corner_rect = pg.Rect(corner_x, corner_y, corner_size, corner_size)
                pg.draw.rect(screen, gold_color, corner_rect)
            
            # Massive golden lock in center
            lock_size = 20
            lock_rect = pg.Rect(render_x - lock_size//2, render_y - lock_size//2, 
                              lock_size, lock_size)
            pg.draw.rect(screen, gold_color, lock_rect)
            
            # Lock keyhole (black circle)
            pg.draw.circle(screen, (0, 0, 0), (render_x, render_y), 6)
            
            # Add sparkle effects around the chest
            if random.random() < 0.4:  # 40% chance for sparkles
                sparkle_count = random.randint(3, 8)
                for _ in range(sparkle_count):
                    sparkle_angle = random.uniform(0, math.pi * 2)
                    sparkle_distance = random.uniform(self.size * 0.8, self.size * 1.5)
                    sparkle_x = render_x + math.cos(sparkle_angle) * sparkle_distance
                    sparkle_y = render_y + math.sin(sparkle_angle) * sparkle_distance
                    sparkle_color = (255, 255, random.randint(100, 255))  # Golden sparkles
                    sparkle_size = random.randint(2, 4)
                    pg.draw.circle(screen, sparkle_color, (int(sparkle_x), int(sparkle_y)), sparkle_size)

class CoreManager:
    """Manages all Rapture Cores, enemy drops, and chests in the world."""
    
    def __init__(self):
        """Initialize the core manager."""
        self.cores: List[RaptureCore] = []
        self.chests: List[CoreChest] = []
        self.player_cores = 0  # Total cores collected
        self.cores_per_chunk = 1  # Very rare - only 1 chest per chunk sometimes
        
    def clear_all_cores(self):
        """Clear all cores and chests (used when starting a new level)."""
        self.cores.clear()
        self.chests.clear()
        # Note: Don't clear player_cores - that's persistent across levels
        
    def generate_cores_for_region(self, min_x: float, min_y: float, max_x: float, max_y: float):
        """Generate cores/chests for a specific region (used for level-based generation)."""
        # Calculate region size
        width = max_x - min_x
        height = max_y - min_y
        area = width * height
        
        # Generate chests based on area size - fewer chests but guaranteed
        chest_density = 0.000005  # About 1 chest per 200k pixel area
        num_chests = max(3, int(area * chest_density))  # At least 3 chests per level
        
        for _ in range(num_chests):
            # Random position within region
            chest_x = random.uniform(min_x + 200, max_x - 200)  # Stay away from edges
            chest_y = random.uniform(min_y + 200, max_y - 200)
            
            # More cores per chest since there are fewer chests
            core_amount = random.randint(8, 15)  # More cores per chest in level system
            
            chest = CoreChest(chest_x, chest_y, core_amount)
            self.chests.append(chest)
        
    def generate_chunk_cores(self, chunk_x: int, chunk_y: int, chunk_size: int, 
                           biome_type: str, danger_level: int):
        """Generate cores/chests for a new chunk."""
        # Much rarer chest generation - only in high danger areas
        chest_chance = 0.02 + (danger_level * 0.01)  # 2-7% chance per chunk (much rarer)
        
        if random.random() < chest_chance:
            # Place one chest in this chunk, more spread out
            chest_x = chunk_x + random.randint(400, chunk_size - 400)  # More spread out
            chest_y = chunk_y + random.randint(400, chunk_size - 400)
            
            # More cores in dangerous biomes and rarer chests
            core_amount = random.randint(3, 5 + danger_level * 2)  # 3-15 cores per chest
            
            chest = CoreChest(chest_x, chest_y, core_amount)
            self.chests.append(chest)
            
    def drop_core_from_enemy(self, enemy_pos: pg.Vector2, enemy_danger_level: int, 
                           enemy_type_multiplier: float = 1.0):
        """Drop cores when an enemy is defeated."""
        # Higher drop chance based on enemy difficulty
        drop_chance = 0.4 + (enemy_danger_level * 0.15) + (enemy_type_multiplier * 0.1)  # Much higher chance
        
        print(f"DEBUG: Enemy died at {enemy_pos}, drop chance: {drop_chance:.2f}")  # Debug print
        
        if random.random() < drop_chance:
            # Number of cores based on enemy strength
            core_count = random.randint(1, max(1, enemy_danger_level))
            print(f"DEBUG: Dropping {core_count} cores!")  # Debug print
            
            # Drop cores near enemy position with some spread
            for _ in range(core_count):
                drop_x = enemy_pos.x + random.randint(-30, 30)
                drop_y = enemy_pos.y + random.randint(-30, 30)
                core = RaptureCore(drop_x, drop_y, 1)
                self.cores.append(core)
        else:
            print("DEBUG: No core dropped")  # Debug print
                
    def try_collect_cores(self, player_pos: pg.Vector2) -> int:
        """Try to collect cores near player position."""
        total_collected = 0
        
        # Check individual cores for collection trigger
        for core in self.cores:
            if core.being_collected or core.collected:
                continue
                
            distance = core.pos.distance_to(player_pos)
            if distance <= core.collection_radius:
                # Start collection animation
                core.being_collected = True
                core.collection_timer = 0.0
        
        # Note: Actual collection happens in update() when animation completes
        return total_collected  # Return 0 since we're just triggering animations
        return total_collected
        
    def update(self, dt: float, player_pos: pg.Vector2 = None):
        """Update all cores and chests."""
        # Update core animations and magnetic attraction
        cores_to_remove = []
        for core in self.cores:
            core.update(dt, player_pos)
            
            # Remove cores that have finished their collection animation
            if core.collected:  # Core has finished collection animation
                self.player_cores += core.amount
                cores_to_remove.append(core)
        
        # Remove collected cores
        for core in cores_to_remove:
            self.cores.remove(core)
            
        # Update chests
        chests_to_remove = []
        for chest in self.chests:
            cores_to_add = chest.update(dt, self)
            # Add any cores spawned by exploding chests
            if cores_to_add:
                self.cores.extend(cores_to_add)
            
            # Remove chests that have finished exploding
            if chest.exploding and chest.explosion_timer >= chest.explosion_duration:
                chests_to_remove.append(chest)
        
        # Remove exploded chests
        for chest in chests_to_remove:
            self.chests.remove(chest)
    
    def check_bullet_chest_collision(self, bullet_rect: pg.Rect, damage: int) -> bool:
        """Check if bullet hits any chest and apply damage."""
        for chest in self.chests:
            if not chest.exploding and chest.get_collision_rect().colliderect(bullet_rect):
                chest.take_damage(damage)
                return True
        return False
            
    def render(self, screen: pg.Surface, world_offset: Tuple[int, int]):
        """Render all cores and chests."""
        # Render chests first (behind cores)
        for chest in self.chests:
            chest.render(screen, world_offset)
            
        # Render cores
        for core in self.cores:
            core.render(screen, world_offset)
            
    def get_player_cores(self) -> int:
        """Get total cores collected by player."""
        return self.player_cores
        
    def get_total_cores_collected(self) -> int:
        """Get total cores collected (alias for objective system compatibility)."""
        return self.player_cores
"""
Base Trail Renderer for Weapon Effects
Provides common trail rendering functionality for weapon effects like minigun whip trails and shotgun fire trails.
"""

import pygame as pg
import math
from typing import Tuple, List, Optional
from abc import ABC, abstractmethod


class BaseTrailRenderer(ABC):
    """Base class for rendering bullet trails with common functionality."""
    
    def __init__(self, lighting_system=None):
        self.lighting_system = lighting_system
        
    def render_bullet_trail_lines(self, screen: pg.Surface, bullets, offset: Tuple[float, float] = (0, 0)):
        """Render trail lines connecting bullets."""
        if len(bullets) < 2:
            return
            
        # Add lighting along the trail if available
        self._add_trail_lighting(bullets)
            
        # Draw curved connections between bullets
        for i in range(len(bullets) - 1):
            bullet1 = bullets[i]
            bullet2 = bullets[i + 1]
            
            start_pos = (bullet1.pos.x + offset[0], bullet1.pos.y + offset[1])
            end_pos = (bullet2.pos.x + offset[0], bullet2.pos.y + offset[1])
            
            # Generate curve points based on trail type
            curve_points = self._generate_curve_points(start_pos, end_pos)
            
            # Draw trail segments between curve points
            for j in range(len(curve_points) - 1):
                p1 = curve_points[j]
                p2 = curve_points[j + 1]
                self._draw_trail_segment(screen, p1, p2)
    
    # Alias for backward compatibility
    def render_bullet_trail(self, screen: pg.Surface, bullets, offset: Tuple[float, float] = (0, 0)):
        """Alias for render_bullet_trail_lines."""
        return self.render_bullet_trail_lines(screen, bullets, offset)
    
    def generate_damage_segments(self, bullets, damage: int = 6, width: int = 12):
        """Generate damage segments along curved bullet paths for collision detection."""
        if len(bullets) < 2:
            return []
            
        damage_segments = []
        
        # Create curved damage segments between consecutive bullets
        for i in range(len(bullets) - 1):
            bullet1 = bullets[i]
            bullet2 = bullets[i + 1]
            
            start_pos = (bullet1.pos.x, bullet1.pos.y)
            end_pos = (bullet2.pos.x, bullet2.pos.y)
            
            # Generate curved points for this bullet pair (fewer for collision)
            curve_points = self._generate_curve_points(start_pos, end_pos)
            
            # Create damage segments between each curve point
            for j in range(len(curve_points) - 1):
                p1 = curve_points[j]
                p2 = curve_points[j + 1]
                
                segment = {
                    'start_x': p1[0],
                    'start_y': p1[1],
                    'end_x': p2[0],
                    'end_y': p2[1],
                    'damage': damage,
                    'width': width
                }
                damage_segments.append(segment)
                
        return damage_segments
    
    def _generate_curve_points(self, start_pos: Tuple[float, float], end_pos: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Generate curved points between start and end positions."""
        points = [start_pos]
        
        # Calculate curve control points
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < self._get_min_curve_distance():
            points.append(end_pos)
            return points
            
        # Get trail-specific parameters
        num_points = self._get_curve_points_count(distance)
        curve_intensity = self._get_curve_intensity(distance)
        
        # Calculate perpendicular direction for curve offset
        perpendicular_x = -dy / distance * curve_intensity
        perpendicular_y = dx / distance * curve_intensity
        
        # Generate intermediate curve points
        for i in range(1, num_points + 1):
            t = i / (num_points + 1)
            curve_factor = self._get_curve_factor(t, distance)
            
            # Interpolate position with curve offset
            x = start_pos[0] + t * dx + curve_factor * perpendicular_x
            y = start_pos[1] + t * dy + curve_factor * perpendicular_y
            points.append((x, y))
            
        points.append(end_pos)
        return points
    
    def _add_trail_lighting(self, bullets):
        """Add lighting effects along the trail if lighting system is available."""
        if not self.lighting_system or len(bullets) < 4:
            return
            
        # Add subtle lights along the trail
        light_interval = self._get_lighting_interval()
        for i in range(2, len(bullets) - 2, light_interval):
            bullet = bullets[i]
            self.lighting_system.add_muzzle_flash(
                bullet.pos.x, bullet.pos.y,
                intensity=self._get_trail_light_intensity(),
                weapon_type=self._get_weapon_type()
            )
    
    @abstractmethod
    def _draw_trail_segment(self, screen: pg.Surface, p1: Tuple[float, float], p2: Tuple[float, float]):
        """Draw a single trail segment. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _get_min_curve_distance(self) -> float:
        """Get minimum distance to apply curves. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _get_curve_points_count(self, distance: float) -> int:
        """Get number of curve points based on distance. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _get_curve_intensity(self, distance: float) -> float:
        """Get curve intensity based on distance. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _get_curve_factor(self, t: float, distance: float) -> float:
        """Get curve factor for position t. Must be implemented by subclasses."""
        pass
    
    def _get_lighting_interval(self) -> int:
        """Get interval for trail lighting. Can be overridden by subclasses."""
        return 3
    
    def _get_trail_light_intensity(self) -> float:
        """Get intensity for trail lighting. Can be overridden by subclasses."""
        return 0.4
    
    def _get_weapon_type(self) -> str:
        """Get weapon type for lighting. Can be overridden by subclasses."""
        return "generic"


class MinigunTrailRenderer(BaseTrailRenderer):
    """Trail renderer for minigun whip trails."""
    
    def __init__(self, lighting_system=None):
        super().__init__(lighting_system)
        self.whip_trail_active = False
    
    def _draw_trail_segment(self, screen: pg.Surface, p1: Tuple[float, float], p2: Tuple[float, float]):
        """Draw thick glowing segment for minigun trails with blue plasma colors."""
        # Calculate segment properties
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = (dx * dx + dy * dy) ** 0.5
        
        if length < 1:
            return
            
        # Draw multiple layers for blue plasma glow effect (original minigun colors)
        # Outer plasma field (blue) - very thick
        pg.draw.line(screen, (0, 120, 255), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 20)
        
        # Middle plasma glow (brighter blue) - thick  
        pg.draw.line(screen, (50, 180, 255), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 14)
        
        # Inner plasma core (bright cyan) - medium
        pg.draw.line(screen, (100, 220, 255), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 8)
        
        # Bright energy center (white-cyan) - thin but bright
        pg.draw.line(screen, (255, 255, 255), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 4)
    
    def _get_min_curve_distance(self) -> float:
        return 10.0
    
    def _get_curve_points_count(self, distance: float) -> int:
        if distance < 25:
            return 2
        return 4
    
    def _get_curve_intensity(self, distance: float) -> float:
        return min(distance * 0.08, 15)
    
    def _get_curve_factor(self, t: float, distance: float) -> float:
        # Smooth curve with slight randomness for natural look
        return 4 * t * (1 - t) * (1 + 0.1 * math.sin(t * math.pi * 6))
    
    def _get_weapon_type(self) -> str:
        return "minigun"


class ShotgunTrailRenderer(BaseTrailRenderer):
    """Trail renderer for shotgun fire trails."""
    
    def _draw_trail_segment(self, screen: pg.Surface, p1: Tuple[float, float], p2: Tuple[float, float]):
        """Draw fire-themed glowing segment for shotgun trails."""
        # Calculate segment properties
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = (dx * dx + dy * dy) ** 0.5
        
        if length < 1:
            return
            
        # Draw fire-themed layers
        colors = [(255, 100, 0, 120), (255, 150, 0, 140), (255, 200, 50, 160), (255, 255, 100, 200)]
        thicknesses = [12, 8, 5, 2]
        
        for color, thickness in zip(colors, thicknesses):
            if thickness > 1:
                pg.draw.line(screen, color[:3], (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), thickness)
    
    def _get_min_curve_distance(self) -> float:
        return 15.0
    
    def _get_curve_points_count(self, distance: float) -> int:
        return 3
    
    def _get_curve_intensity(self, distance: float) -> float:
        return min(distance * 0.12, 20)
    
    def _get_curve_factor(self, t: float, distance: float) -> float:
        # More aggressive flame curve with flicker
        return 4 * t * (1 - t) * (1 + 0.3 * math.sin(t * math.pi * 4))
    
    def _get_weapon_type(self) -> str:
        return "shotgun"
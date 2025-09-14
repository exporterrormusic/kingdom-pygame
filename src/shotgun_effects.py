"""
Shotgun fire trail enhancement system.
Handles fire-themed connecting lines between shotgun pellets.
"""

import pygame as pg
import math
import random
from typing import Tuple, List

class ShotgunEffectsManager:
    """Manages fire trail effects for shotgun pellets."""
    
    def __init__(self):
        """Initialize the shotgun effects manager."""
        self.fire_trails = []  # Active fire trail segments
        self.fire_sparks = []  # Fire sparks along the trails
        self.trail_active = True  # Always active for shotgun
        
    def update(self, dt: float):
        """Update fire trail effects."""
        # Update fire sparks (let them fade over time)
        self.fire_sparks = [spark for spark in self.fire_sparks if spark['life'] > 0]
        for spark in self.fire_sparks:
            spark['life'] -= dt * 3.0  # Fade over time
            spark['size'] *= 0.98  # Shrink slightly
            
    def render_fire_trail_lines(self, screen: pg.Surface, bullets, offset: Tuple[float, float] = (0, 0)):
        """Render fire-themed glowing lines connecting shotgun pellets."""
        if len(bullets) < 2:
            return
            
        # Draw fire connections between bullets with flame-like curves
        for i in range(len(bullets) - 1):
            bullet1 = bullets[i]
            bullet2 = bullets[i + 1]
            
            start_pos = (bullet1.pos.x + offset[0], bullet1.pos.y + offset[1])
            end_pos = (bullet2.pos.x + offset[0], bullet2.pos.y + offset[1])
            
            # Create flame-like curved path
            flame_points = self._generate_flame_curve(start_pos, end_pos, 3)
            
            # Draw thick glowing fire trail segments
            for j in range(len(flame_points) - 1):
                p1 = flame_points[j]
                p2 = flame_points[j + 1]
                self._draw_fire_segment(screen, p1, p2)
                
        # Add fire sparks along the trails
        self._add_trail_sparks(bullets, offset)
        self._render_fire_sparks(screen, offset)
                
    def _generate_flame_curve(self, start_pos, end_pos, num_points):
        """Generate flame-like curved points between start and end positions."""
        points = [start_pos]
        
        # Calculate curve control points
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < 15:  # Very close pellets - straight line
            points.append(end_pos)
            return points
            
        # Flame-like curve with more aggressive flickering
        curve_intensity = min(distance * 0.12, 20)  # Slightly more curve than minigun
        perpendicular_x = -dy / distance * curve_intensity
        perpendicular_y = dx / distance * curve_intensity
        
        # Add flame-like variations
        for i in range(1, num_points + 1):
            t = i / (num_points + 1)
            
            # More aggressive flame curve
            curve_factor = 4 * t * (1 - t) * (1 + 0.3 * math.sin(t * math.pi * 4))  # Flame flicker
            
            # Base interpolation
            x = start_pos[0] + t * dx
            y = start_pos[1] + t * dy
            
            # Add flame curve with random flicker
            flame_offset_x = perpendicular_x * curve_factor
            flame_offset_y = perpendicular_y * curve_factor
            
            # Add flame-like random variations
            flicker = random.uniform(-4, 4)
            x += flame_offset_x + flicker
            y += flame_offset_y + flicker
            
            points.append((x, y))
            
        points.append(end_pos)
        return points
        
    def _draw_fire_segment(self, screen: pg.Surface, p1, p2):
        """Draw a thick glowing fire segment between two points."""
        # Draw multiple layers for fire glow effect
        
        # Outer fire glow (thick, red)
        try:
            pg.draw.line(screen, (255, 60, 0), p1, p2, 12)  # Thick red base
        except ValueError:
            return  # Skip invalid points
            
        # Middle fire layer (orange)
        try:
            pg.draw.line(screen, (255, 120, 0), p1, p2, 8)  # Orange middle
        except ValueError:
            return
            
        # Inner fire core (yellow)
        try:
            pg.draw.line(screen, (255, 180, 20), p1, p2, 4)  # Yellow core
        except ValueError:
            return
            
        # Hot center (white-yellow)
        try:
            pg.draw.line(screen, (255, 255, 100), p1, p2, 2)  # Bright center
        except ValueError:
            return
            
    def _add_trail_sparks(self, bullets, offset):
        """Add fire sparks along the bullet trails."""
        if len(bullets) < 2:
            return
            
        # Add sparks between bullets
        for i in range(len(bullets) - 1):
            bullet1 = bullets[i]
            bullet2 = bullets[i + 1]
            
            # Only add sparks occasionally to avoid too many
            if random.random() < 0.3:  # 30% chance per frame per connection
                # Position spark somewhere between the bullets
                t = random.uniform(0.2, 0.8)
                spark_x = bullet1.pos.x + t * (bullet2.pos.x - bullet1.pos.x) + offset[0]
                spark_y = bullet1.pos.y + t * (bullet2.pos.y - bullet1.pos.y) + offset[1]
                
                spark = {
                    'x': spark_x + random.uniform(-5, 5),
                    'y': spark_y + random.uniform(-5, 5),
                    'size': random.uniform(2, 5),
                    'life': 1.0,  # Fade over 1 second
                    'color': random.choice([
                        (255, 200, 0),   # Golden
                        (255, 150, 0),   # Orange
                        (255, 100, 0),   # Deep orange
                        (255, 255, 100)  # Bright yellow
                    ])
                }
                self.fire_sparks.append(spark)
                
    def _render_fire_sparks(self, screen: pg.Surface, offset):
        """Render fire sparks along the trails."""
        for spark in self.fire_sparks:
            if spark['life'] > 0:
                # Create fading alpha based on remaining life
                alpha = int(spark['life'] * 255)
                alpha = max(0, min(255, alpha))
                
                # Create spark surface with alpha
                spark_size = int(spark['size'])
                if spark_size > 0:
                    spark_surf = pg.Surface((spark_size * 2, spark_size * 2), pg.SRCALPHA)
                    color = (*spark['color'], alpha)
                    pg.draw.circle(spark_surf, color, (spark_size, spark_size), spark_size)
                    
                    # Render spark
                    screen.blit(spark_surf, (spark['x'] - spark_size, spark['y'] - spark_size), 
                              special_flags=pg.BLEND_ALPHA_SDL2)
"""
Impact sparks effect system for bullet-wall collisions.
Creates small particle effects when bullets hit walls or obstacles.
"""

import pygame as pg
import math
import random
from typing import List, Tuple


class ImpactSpark:
    """Individual spark particle."""
    
    def __init__(self, x: float, y: float, angle: float, speed: float, color: Tuple[int, int, int]):
        """Initialize a spark particle."""
        self.pos = pg.Vector2(x, y)
        self.velocity = pg.Vector2(
            math.cos(angle) * speed,
            math.sin(angle) * speed
        )
        self.color = color
        self.initial_color = color
        self.age = 0.0
        self.lifetime = random.uniform(0.2, 0.5)  # 0.2-0.5 seconds
        self.size = random.randint(2, 4)
        self.initial_size = self.size
        
    def update(self, dt: float) -> bool:
        """Update spark. Returns True if should be removed."""
        self.age += dt
        
        # Update position
        self.pos += self.velocity * dt
        
        # Apply gravity
        self.velocity.y += 300 * dt  # Gravity effect
        
        # Apply air resistance
        self.velocity *= 0.95
        
        # Fade out over time
        progress = self.age / self.lifetime
        alpha = 1.0 - progress
        
        # Fade color and size
        self.color = (
            int(self.initial_color[0] * alpha),
            int(self.initial_color[1] * alpha),
            int(self.initial_color[2] * alpha)
        )
        self.size = max(1, int(self.initial_size * alpha))
        
        return self.age >= self.lifetime
    
    def render(self, screen: pg.Surface, offset: Tuple[int, int]):
        """Render the spark."""
        render_x = int(self.pos.x + offset[0])
        render_y = int(self.pos.y + offset[1])
        
        # Only render if on screen
        if (-10 <= render_x <= screen.get_width() + 10 and 
            -10 <= render_y <= screen.get_height() + 10):
            
            # Draw spark as a small circle
            if self.size > 0:
                pg.draw.circle(screen, self.color, (render_x, render_y), self.size)


class ImpactSparksManager:
    """Manages impact spark effects for bullet-wall collisions."""
    
    def __init__(self):
        """Initialize the impact sparks manager."""
        self.sparks: List[ImpactSpark] = []
    
    def add_impact_sparks(self, x: float, y: float, impact_angle: float = None, surface_type: str = "wall"):
        """Create impact sparks at the specified position."""
        # Determine spark colors based on surface type
        if surface_type == "wall":
            colors = [(255, 255, 255), (255, 255, 200), (255, 200, 100)]  # White/yellow
        elif surface_type == "metal":
            colors = [(255, 255, 255), (200, 200, 255), (150, 150, 255)]  # White/blue
        elif surface_type == "dirt":
            colors = [(139, 69, 19), (160, 82, 45), (210, 180, 140)]  # Brown tones
        else:
            colors = [(255, 255, 255), (255, 255, 200), (255, 200, 100)]  # Default white/yellow
        
        # Create 3-5 sparks per impact
        num_sparks = random.randint(3, 5)
        
        for i in range(num_sparks):
            # Calculate spark direction
            if impact_angle is not None:
                # Reflect sparks based on impact angle
                base_angle = impact_angle + math.pi  # Opposite direction of impact
                angle_variation = random.uniform(-math.pi/3, math.pi/3)  # ±60 degrees spread
                spark_angle = base_angle + angle_variation
            else:
                # Random direction if no impact angle provided
                spark_angle = random.uniform(0, 2 * math.pi)
            
            # Random speed and color
            speed = random.uniform(50, 150)
            color = random.choice(colors)
            
            # Add slight position variation
            spark_x = x + random.uniform(-2, 2)
            spark_y = y + random.uniform(-2, 2)
            
            # Create spark
            spark = ImpactSpark(spark_x, spark_y, spark_angle, speed, color)
            self.sparks.append(spark)
    
    def update(self, dt: float):
        """Update all sparks and remove expired ones."""
        sparks_to_remove = []
        
        for spark in self.sparks:
            if spark.update(dt):
                sparks_to_remove.append(spark)
        
        # Remove expired sparks
        for spark in sparks_to_remove:
            self.sparks.remove(spark)
    
    def render(self, screen: pg.Surface, offset: Tuple[int, int] = (0, 0)):
        """Render all sparks."""
        for spark in self.sparks:
            spark.render(screen, offset)
    
    def clear(self):
        """Clear all sparks."""
        self.sparks.clear()
    
    def get_spark_count(self) -> int:
        """Get the number of active sparks."""
        return len(self.sparks)
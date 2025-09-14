"""
Visual slash effect system for sword attacks.
Creates impressive blade-like slash animations.
"""

import pygame as pg
import math
from typing import List, Tuple

class SlashEffect:
    """Individual slash effect for sword attacks that follows the player."""
    
    def __init__(self, player_ref, angle: float, slash_range: float, damage: float, duration: float = 0.4):
        """Initialize a slash effect that follows the player.
        
        Args:
            player_ref: Reference to the player object to follow
            angle: Direction angle in degrees relative to player
            slash_range: Maximum reach of the slash
            damage: Damage this slash deals to enemies
            duration: How long the effect lasts in seconds
        """
        self.player_ref = player_ref
        self.relative_angle = angle
        self.slash_range = slash_range
        self.damage = damage
        self.duration = duration
        self.age = 0.0
        self.damaged_enemies = set()  # Track which enemies have been damaged
        
        # Slash properties
        self.arc_angle = 90  # 90-degree arc for sword slash
        self.thickness = 12   # Increased thickness for better visibility
        
        # Animation properties
        self.max_alpha = 0.8  # Reduced for transparency
        self.color_base = (150, 100, 255)  # Purple base
        self.color_edge = (200, 150, 255)  # Light purple edge
        
    def update(self, dt: float) -> bool:
        """Update the slash effect. Returns True if effect should be removed."""
        self.age += dt
        return self.age >= self.duration
    
    def get_current_position(self) -> Tuple[float, float]:
        """Get current position of the slash (follows player)."""
        if self.player_ref:
            gun_tip = self.player_ref.get_gun_tip_position()
            return (gun_tip.x, gun_tip.y)
        return (0, 0)
    
    def get_current_angle(self) -> float:
        """Get current angle of the slash (follows player rotation)."""
        if self.player_ref:
            return self.player_ref.angle + self.relative_angle
        return self.relative_angle
    
    def get_alpha(self) -> float:
        """Get current alpha based on age."""
        # Fade out over duration with transparency
        progress = self.age / self.duration
        return self.max_alpha * (1.0 - progress)
    
    def get_current_range(self) -> float:
        """Get current slash range based on animation progress."""
        # Maintain full range throughout the duration
        return self.slash_range
    
    def check_enemy_collision(self, enemy, player_ref) -> bool:
        """Check if enemy is currently being hit by this slash effect."""
        if self.age >= self.duration or not player_ref:
            return False
            
        # Skip if already damaged by this slash
        if id(enemy) in self.damaged_enemies:
            return False
            
        import math
        
        # Get current weapon tip position and angle
        gun_tip = player_ref.get_gun_tip_position()
        current_angle = self.get_current_angle()
        
        # Calculate vector from weapon tip to enemy
        dx = enemy.pos.x - gun_tip.x
        dy = enemy.pos.y - gun_tip.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Use visual animation progress to match damage area with visual effect
        wipe_progress = self.get_wipe_progress()
        current_visual_range = self.slash_range * wipe_progress
        
        # Check if enemy is within the current visual slash range
        if distance <= current_visual_range:
            # Calculate angle to enemy
            enemy_angle = math.atan2(dy, dx)
            player_angle_rad = math.radians(current_angle)
            
            # Calculate angle difference from slash direction
            angle_diff = enemy_angle - player_angle_rad
            
            # Normalize angle difference to [-π, π]
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            # Check if enemy is within the slash arc
            arc_radians = math.radians(self.arc_angle)
            half_arc = arc_radians / 2
            
            if abs(angle_diff) <= half_arc:
                # Mark this enemy as damaged by this slash
                self.damaged_enemies.add(id(enemy))
                return True
                
        return False
        return self.slash_range * progress
    
    def get_wipe_progress(self) -> float:
        """Get the progress of the top-to-bottom wipe animation (0.0 to 1.0)."""
        return min(1.0, (self.age / self.duration) * 1.5)  # Wipe completes in first 2/3 of duration
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render enhanced magical slash effect that follows player."""
        if self.age >= self.duration:
            return
            
        # Get current position and angle (follows player)
        current_pos = self.get_current_position()
        current_angle = self.get_current_angle()
        
        # Calculate render position with offset
        render_pos = (
            current_pos[0] + offset[0],
            current_pos[1] + offset[1]
        )
        
        current_range = self.get_current_range()
        wipe_progress = self.get_wipe_progress()
        alpha = self.get_alpha()
        
        if current_range <= 0 or alpha <= 0 or wipe_progress <= 0:
            return
        
        # Enhanced magical slash with purple theme
        self._draw_enhanced_slash_arc(screen, render_pos, current_range, alpha, wipe_progress, current_angle)
    
    def _draw_enhanced_slash_arc(self, screen: pg.Surface, render_pos: Tuple[float, float], 
                               current_range: float, alpha: float, wipe_progress: float, current_angle: float):
        """Draw enhanced magical slash arc with purple theme and transparency."""
        # Purple magical blade colors with glow
        blade_colors = [
            (80, 40, 120),    # Deep purple (outer glow)
            (120, 60, 180),   # Dark purple
            (160, 100, 220),  # Medium purple
            (200, 140, 255),  # Light purple  
            (220, 180, 255),  # Bright purple (inner)
        ]
        
        # Draw multiple arc layers for depth and glow
        for i, color in enumerate(blade_colors):
            layer_thickness = max(2, int(self.thickness * (5 - i) * 0.6))
            layer_range = current_range * (0.85 + i * 0.03) * wipe_progress
            layer_alpha = alpha * (0.3 + i * 0.15)  # More transparency
            
            if layer_range <= 0 or layer_alpha <= 0:
                continue
            
            # Calculate arc parameters using current angle
            start_angle_rad = math.radians(current_angle - self.arc_angle // 2)
            end_angle_rad = math.radians(current_angle + self.arc_angle // 2)
            
            # Draw arc segments with higher resolution for smoother appearance
            segments = 16
            angle_step = (end_angle_rad - start_angle_rad) / segments
            
            for seg in range(segments):
                angle1 = start_angle_rad + seg * angle_step
                angle2 = start_angle_rad + (seg + 1) * angle_step
                
                # Calculate points for this segment
                x1 = render_pos[0] + math.cos(angle1) * layer_range * 0.3
                y1 = render_pos[1] + math.sin(angle1) * layer_range * 0.3
                x2 = render_pos[0] + math.cos(angle1) * layer_range
                y2 = render_pos[1] + math.sin(angle1) * layer_range
                
                x3 = render_pos[0] + math.cos(angle2) * layer_range
                y3 = render_pos[1] + math.sin(angle2) * layer_range
                x4 = render_pos[0] + math.cos(angle2) * layer_range * 0.3
                y4 = render_pos[1] + math.sin(angle2) * layer_range * 0.3
                
                # Draw the segment
                points = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
                
                # Ensure all points are valid
                valid_points = []
                for point in points:
                    if isinstance(point[0], (int, float)) and isinstance(point[1], (int, float)):
                        valid_points.append((int(point[0]), int(point[1])))
                
                if len(valid_points) >= 3:
                    # Transparent purple color
                    final_color = (
                        max(0, min(255, int(color[0] * (1 + layer_alpha)))),
                        max(0, min(255, int(color[1] * (1 + layer_alpha)))),
                        max(0, min(255, int(color[2] * (1 + layer_alpha))))
                    )
                    pg.draw.polygon(screen, final_color, valid_points)
        
        # Add magical sparkles with purple theme
        self._draw_simple_sparkles(screen, render_pos, current_range * wipe_progress, alpha, current_angle)
    
    def _draw_simple_sparkles(self, screen: pg.Surface, render_pos: Tuple[float, float], 
                            current_range: float, alpha: float, current_angle: float):
        """Draw enhanced magical sparkles around the slash with purple theme."""
        import random
        
        # Number of sparkles based on range and alpha
        sparkle_count = max(0, int(10 * alpha * (current_range / 300)))
        
        for _ in range(sparkle_count):
            # Random position around the slash arc using current angle
            angle_offset = random.uniform(-self.arc_angle // 2, self.arc_angle // 2)
            sparkle_angle = math.radians(current_angle + angle_offset)
            sparkle_distance = random.uniform(current_range * 0.2, current_range * 1.1)
            
            sparkle_x = int(render_pos[0] + math.cos(sparkle_angle) * sparkle_distance)
            sparkle_y = int(render_pos[1] + math.sin(sparkle_angle) * sparkle_distance)
            
            # Enhanced sparkles with size variation and purple theme
            sparkle_size = random.randint(2, 5)
            sparkle_intensity = random.uniform(0.4, 0.8)
            sparkle_color = (
                max(0, min(255, int(180 * alpha * sparkle_intensity))),
                max(0, min(255, int(120 * alpha * sparkle_intensity))),
                max(0, min(255, int(255 * alpha * sparkle_intensity)))
            )
            
            # Draw enhanced star-shaped sparkle
            if sparkle_size >= 2:
                # Main cross
                pg.draw.line(screen, sparkle_color, 
                           (sparkle_x - sparkle_size, sparkle_y), 
                           (sparkle_x + sparkle_size, sparkle_y), 2)
                pg.draw.line(screen, sparkle_color, 
                           (sparkle_x, sparkle_y - sparkle_size), 
                           (sparkle_x, sparkle_y + sparkle_size), 2)
                
                # Diagonal cross for star effect
                if sparkle_size >= 4:
                    half_size = sparkle_size // 2
                    pg.draw.line(screen, sparkle_color, 
                               (sparkle_x - half_size, sparkle_y - half_size), 
                               (sparkle_x + half_size, sparkle_y + half_size), 1)
                    pg.draw.line(screen, sparkle_color, 
                               (sparkle_x - half_size, sparkle_y + half_size), 
                               (sparkle_x + half_size, sparkle_y - half_size), 1)
    
    def _draw_magical_slash_crescent(self, screen: pg.Surface, render_pos: Tuple[float, float], 
                                   current_range: float, alpha: float, wipe_progress: float):
        """Draw the main magical crescent slash effect."""
        import random
        
        # Calculate bounding box for efficient rendering
        bbox_size = int(current_range * 3.0)  # Larger for magical effects
        bbox_x = int(render_pos[0] - bbox_size // 2)
        bbox_y = int(render_pos[1] - bbox_size // 2)
        
        # Clamp to screen bounds
        bbox_x = max(0, min(bbox_x, screen.get_width() - bbox_size))
        bbox_y = max(0, min(bbox_y, screen.get_height() - bbox_size))
        bbox_size = min(bbox_size, screen.get_width() - bbox_x, screen.get_height() - bbox_y)
        
        if bbox_size <= 0:
            return
        
        # Create surface for magical effects
        temp_surface = pg.Surface((bbox_size, bbox_size), pg.SRCALPHA)
        local_center = (bbox_size // 2, bbox_size // 2)
        
        # Magical blade colors (RGB only for polygon drawing)
        blade_energy_rgb = (100, 150, 255)
        blade_glow_rgb = (150, 200, 255)
        blade_bright_rgb = (255, 255, 255)
        blade_core_rgb = (200, 200, 255)
        
        # Draw multiple crescent layers for magical depth
        layers = [
            (current_range * 1.4, blade_energy_rgb, max(0, min(255, int(alpha * 40))), 12),    # Outermost magical aura
            (current_range * 1.2, blade_glow_rgb, max(0, min(255, int(alpha * 80))), 10),      # Mid magical glow  
            (current_range * 1.0, blade_bright_rgb, max(0, min(255, int(alpha * 255))), 8),     # Bright magical edge
            (current_range * 0.8, blade_core_rgb, max(0, min(255, int(alpha * 200))), 6),       # Core magical blade
        ]
        
        for layer_range, layer_color_rgb, layer_alpha, segments in layers:
            if layer_range * wipe_progress <= 0 or layer_alpha <= 0:
                continue
                
            # Create crescent points for this layer
            points = self._create_crescent_points(local_center, layer_range * wipe_progress, segments)
            
            if len(points) >= 3:
                # Create separate surface for alpha blending
                layer_surface = pg.Surface((bbox_size, bbox_size), pg.SRCALPHA)
                layer_color_with_alpha = (layer_color_rgb[0], layer_color_rgb[1], layer_color_rgb[2], layer_alpha)
                pg.draw.polygon(layer_surface, layer_color_with_alpha, points)
                temp_surface.blit(layer_surface, (0, 0), special_flags=pg.BLEND_ALPHA_SDL2)
        
        # Blit the magical slash to the main screen
        screen.blit(temp_surface, (bbox_x, bbox_y), special_flags=pg.BLEND_ALPHA_SDL2)
    
    def _create_crescent_points(self, center: Tuple[float, float], radius: float, segments: int) -> List[Tuple[float, float]]:
        """Create points for a curved crescent shape."""
        points = []
        
        # Create curved crescent based on sword angle and arc
        start_angle_rad = math.radians(self.angle - self.arc_angle // 2)
        end_angle_rad = math.radians(self.angle + self.arc_angle // 2)
        angle_step = (end_angle_rad - start_angle_rad) / segments
        
        # Outer curve points
        for i in range(segments + 1):
            angle = start_angle_rad + i * angle_step
            # Add curve variation for crescent shape
            curve_radius = radius * (0.7 + 0.3 * math.sin(i * math.pi / segments))
            
            x = center[0] + math.cos(angle) * curve_radius
            y = center[1] + math.sin(angle) * curve_radius
            points.append((x, y))
        
        # Inner curve points (reverse direction for closed shape)
        inner_radius = radius * 0.3
        for i in range(segments, -1, -1):
            angle = start_angle_rad + i * angle_step
            curve_radius = inner_radius * (0.8 + 0.2 * math.sin(i * math.pi / segments))
            
            x = center[0] + math.cos(angle) * curve_radius
            y = center[1] + math.sin(angle) * curve_radius
            points.append((x, y))
        
        return points
    
    def _draw_magical_sparkles(self, screen: pg.Surface, render_pos: Tuple[float, float], 
                             current_range: float, alpha: float, wipe_progress: float):
        """Draw magical sparkle effects around the slash."""
        import random
        
        # Number of sparkles based on slash progress
        sparkle_count = int(12 * wipe_progress * alpha)
        
        for _ in range(sparkle_count):
            # Random position around the slash arc
            angle_offset = random.uniform(-self.arc_angle // 2, self.arc_angle // 2)
            sparkle_angle = math.radians(self.angle + angle_offset)
            sparkle_distance = random.uniform(current_range * 0.4, current_range * 1.2)
            
            sparkle_x = render_pos[0] + math.cos(sparkle_angle) * sparkle_distance
            sparkle_y = render_pos[1] + math.sin(sparkle_angle) * sparkle_distance
            
            # Sparkle properties
            sparkle_size = random.randint(2, 5)
            sparkle_alpha = int(alpha * random.uniform(120, 255))
            sparkle_color = (255, 255, 255, sparkle_alpha)
            
            # Draw star-shaped sparkle
            self._draw_star_sparkle(screen, (sparkle_x, sparkle_y), sparkle_size, sparkle_color)
    
    def _draw_star_sparkle(self, screen: pg.Surface, pos: Tuple[float, float], size: int, color: Tuple[int, int, int, int]):
        """Draw a star-shaped magical sparkle."""
        if len(color) == 4:  # Has alpha
            # Create sparkle surface
            sparkle_surface = pg.Surface((size * 3, size * 3), pg.SRCALPHA)
            center = (size * 1.5, size * 1.5)
            
            # Draw star shape
            line_width = max(size // 2, 1)
            # Horizontal line
            pg.draw.line(sparkle_surface, color, (0, center[1]), (size * 3, center[1]), line_width)
            # Vertical line  
            pg.draw.line(sparkle_surface, color, (center[0], 0), (center[0], size * 3), line_width)
            # Diagonal lines for star effect
            diag_width = max(size // 3, 1)
            pg.draw.line(sparkle_surface, color, (size // 2, size // 2), (size * 2.5, size * 2.5), diag_width)
            pg.draw.line(sparkle_surface, color, (size * 2.5, size // 2), (size // 2, size * 2.5), diag_width)
            
            # Blit sparkle to screen
            screen.blit(sparkle_surface, (int(pos[0] - size * 1.5), int(pos[1] - size * 1.5)), 
                       special_flags=pg.BLEND_ALPHA_SDL2)
        else:
            # Simple circular sparkle fallback
            pg.draw.circle(screen, color[:3], (int(pos[0]), int(pos[1])), size)


class SlashEffectManager:
    """Manages all active slash effects."""
    
    def __init__(self):
        """Initialize the slash effect manager."""
        self.effects: List[SlashEffect] = []
    
    def create_slash(self, player_ref, angle: float, slash_range: float, damage: float = 0):
        """Create a new slash effect that follows the player."""
        effect = SlashEffect(player_ref, angle, slash_range, damage)
        self.effects.append(effect)
    
    def update(self, dt: float):
        """Update all slash effects and remove expired ones."""
        effects_to_remove = []
        
        for effect in self.effects:
            if effect.update(dt):
                effects_to_remove.append(effect)
        
        for effect in effects_to_remove:
            self.effects.remove(effect)
    
    def render(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render all active slash effects."""
        for effect in self.effects:
            effect.render(screen, offset)
    
    def check_enemy_collisions(self, enemies, player_ref):
        """Check all active slash effects against enemies and return damage events."""
        damage_events = []
        
        for effect in self.effects:
            for enemy in enemies:
                if effect.check_enemy_collision(enemy, player_ref):
                    damage_events.append({
                        'enemy': enemy,
                        'damage': effect.damage,
                        'effect': effect
                    })
                    
        return damage_events
    
    def clear(self):
        """Clear all effects."""
        self.effects.clear()
    
    def get_effect_count(self) -> int:
        """Get the number of active effects."""
        return len(self.effects)
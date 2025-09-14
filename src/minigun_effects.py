"""
Minigun visual enhancement system.
Handles muzzle flames, barrel spin effects, and enhanced bullet rendering for minigun.
"""

import pygame as pg
import math
import random
from typing import Tuple

class MinigunEffectsManager:
    """Manages visual effects for the minigun weapon."""
    
    def __init__(self):
        """Initialize the minigun effects manager."""
        self.muzzle_flames = []  # Active muzzle flame effects
        self.shell_casings = []  # Active shell casing effects
        self.barrel_rotation = 0.0  # Current barrel rotation angle
        self.spin_speed = 0.0  # Current barrel spin speed
        self.max_spin_speed = 720.0  # Maximum degrees per second
        self.spin_up_time = 3.0  # Time to reach full spin
        self.is_spinning = False
        
        # Whip trail system for full-speed effect
        self.whip_trail_active = False
        self.whip_segments = []  # Active damage whip segments (line segments between bullets)
        self.impact_sparks = []  # Small sparks generated on enemy hits
        self.whip_damage_segments = []  # Track damage-dealing line segments
        
        # Effect timing
        self.last_flame_time = 0.0
        self.last_shell_time = 0.0
        self.flame_interval = 0.02  # Interval between flame spawns at full speed
        self.shell_interval = 0.05  # Interval between shell ejections
        
    def update(self, dt: float, is_firing: bool, fire_rate: float, gun_tip_pos: Tuple[float, float], gun_angle: float):
        """Update minigun effects with whip trail system."""
        # Update barrel spin
        self._update_barrel_spin(dt, is_firing, fire_rate)
        
        # Determine if at full speed (fire rate at minimum = full speed)
        at_full_speed = is_firing and fire_rate <= 0.03  # Full speed when fire rate is at minimum
        
        # Update whip trail system
        self.whip_trail_active = at_full_speed
        if at_full_speed:
            self._update_whip_trail(dt, gun_tip_pos, gun_angle)
        else:
            # Let existing whip effects fade
            self._fade_whip_trail(dt)
        
        # Clean up expired effects
        self.muzzle_flames = []  # No more muzzle spark effects
        self.shell_casings = []  # No shell casings
        self.impact_sparks = [spark for spark in self.impact_sparks if not spark.get('expired', False)]
        # Clear damage segments - they're rebuilt each frame
        self.whip_damage_segments = []
        
    def _update_barrel_spin(self, dt: float, is_firing: bool, fire_rate: float):
        """Update barrel rotation with dramatic anime-style spin effects."""
        if is_firing:
            # Anime-style dramatic spin up based on fire rate
            target_speed = self.max_spin_speed * (1.0 - fire_rate / 0.03)
            if self.spin_speed < target_speed:
                # Faster, more dramatic spin-up for anime effect
                spin_acceleration = (self.max_spin_speed / self.spin_up_time) * 2.5  # 2.5x faster spin-up
                self.spin_speed = min(target_speed, self.spin_speed + spin_acceleration * dt)
        else:
            # Slower, more dramatic spin-down for anime effect
            spin_deceleration = (self.max_spin_speed / (self.spin_up_time * 3))  # 3x slower spin-down
            self.spin_speed = max(0, self.spin_speed - spin_deceleration * dt)
        
        # Update rotation angle with overdramatic speed
        self.barrel_rotation += self.spin_speed * dt
        if self.barrel_rotation >= 360:
            self.barrel_rotation -= 360
            
    def _update_whip_trail(self, dt: float, gun_tip_pos: Tuple[float, float], gun_angle: float):
        """Update damage whip trail system."""
        # Update existing impact sparks
        for spark in self.impact_sparks:
            if not spark.get('expired', False):
                spark['age'] += dt
                age_progress = spark['age'] / spark['max_age']
                spark['alpha'] = max(0, int(255 * (1 - age_progress)))
                spark['size'] *= 1 + dt * 3  # Fast expansion
                
                if age_progress >= 1.0:
                    spark['expired'] = True
    
    def _fade_whip_trail(self, dt: float):
        """Fade out whip trail effects when not at full speed."""
        # Only impact sparks need fading - the line itself is drawn fresh each frame
        for spark in self.impact_sparks:
            if not spark.get('expired', False):
                spark['alpha'] = max(0, spark['alpha'] - int(600 * dt))  # Fast fade
                if spark['alpha'] <= 0:
                    spark['expired'] = True
            
    def update_whip_trail_with_bullets(self, bullets, offset=(0, 0)):
        """Update damage whip trail - create damage segments along curved bullet paths."""
        if not self.whip_trail_active or len(bullets) < 2:
            self.whip_damage_segments = []
            return
            
        # Create curved damage segments between consecutive bullets
        self.whip_damage_segments = []
        for i in range(len(bullets) - 1):
            bullet1 = bullets[i]
            bullet2 = bullets[i + 1]
            
            start_pos = (bullet1.pos.x, bullet1.pos.y)
            end_pos = (bullet2.pos.x, bullet2.pos.y)
            
            # Generate curved points for this bullet pair
            curve_points = self._generate_curve_points(start_pos, end_pos, 3)  # 3 points for collision
            
            # Create damage segments between each curve point
            for j in range(len(curve_points) - 1):
                p1 = curve_points[j]
                p2 = curve_points[j + 1]
                
                segment = {
                    'start_x': p1[0],
                    'start_y': p1[1],
                    'end_x': p2[0],
                    'end_y': p2[1],
                    'damage': 6,  # Whip damage per hit - same as before
                    'width': 12   # Increased collision width for thicker trail
                }
                self.whip_damage_segments.append(segment)
    
    def create_impact_spark(self, x: float, y: float):
        """Create a small impact spark when enemy hits the whip."""
        spark = {
            'x': x + random.uniform(-3, 3),
            'y': y + random.uniform(-3, 3),
            'age': 0.0,
            'max_age': random.uniform(0.15, 0.25),  # Shorter duration
            'size': random.uniform(2, 4),  # Slightly larger to match thicker trail
            'alpha': 255,
            'color': random.choice([
                (100, 220, 255),  # Bright cyan to match bullet inner core
                (150, 240, 255),  # Electric cyan
                (200, 250, 255),  # Bright white-cyan
                (255, 255, 255)   # Pure white for brightness
            ]),
            'expired': False,
            'type': 'impact_spark'
        }
        self.impact_sparks.append(spark)
        
    def get_whip_damage_segments(self):
        """Get current damage segments for collision checking."""
        return self.whip_damage_segments
        
    def check_whip_collision(self, enemy_x: float, enemy_y: float, enemy_radius: float):
        """Check if an enemy collides with any whip damage segment.
        Returns (hit, damage, hit_x, hit_y) tuple."""
        if not self.whip_trail_active:
            return False, 0, 0, 0
            
        for segment in self.whip_damage_segments:
            # Check line-to-circle collision
            hit, hit_x, hit_y = self._line_circle_collision(
                segment['start_x'], segment['start_y'],
                segment['end_x'], segment['end_y'],
                enemy_x, enemy_y, enemy_radius + segment['width']
            )
            
            if hit:
                return True, segment['damage'], hit_x, hit_y
                
        return False, 0, 0, 0
    
    def _line_circle_collision(self, x1: float, y1: float, x2: float, y2: float, 
                             cx: float, cy: float, radius: float):
        """Check collision between line segment (x1,y1)-(x2,y2) and circle at (cx,cy) with radius.
        Returns (collision, closest_x, closest_y)."""
        
        # Vector from start to end of line
        dx = x2 - x1
        dy = y2 - y1
        
        # Vector from start of line to circle center
        fx = cx - x1
        fy = cy - y1
        
        # Handle zero-length line segment
        line_length_sq = dx * dx + dy * dy
        if line_length_sq == 0:
            # Line is a point, check distance to circle center
            dist_sq = fx * fx + fy * fy
            if dist_sq <= radius * radius:
                return True, x1, y1
            return False, x1, y1
        
        # Parameter t for closest point on line to circle center
        t = max(0, min(1, (fx * dx + fy * dy) / line_length_sq))
        
        # Closest point on line segment to circle center
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from circle center to closest point
        dist_x = cx - closest_x
        dist_y = cy - closest_y
        distance_sq = dist_x * dist_x + dist_y * dist_y
        
        # Check if collision occurs
        collision = distance_sq <= radius * radius
        return collision, closest_x, closest_y
                
    def render_muzzle_flames(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render impact sparks when enemies hit the damage whip."""
        for spark in self.impact_sparks:
            if not spark.get('expired', False) and spark['alpha'] > 0:
                render_x = int(spark['x'] + offset[0])
                render_y = int(spark['y'] + offset[1])
                
                # Create small glowing impact spark
                spark_size = max(int(spark['size']), 2)
                
                if spark_size > 0:
                    # Create surface for glow effect - smaller than before
                    glow_surface = pg.Surface((spark_size * 3, spark_size * 3), pg.SRCALPHA)
                    center = int(spark_size * 1.5)
                    
                    # Outer glow - smaller
                    glow_alpha = int(spark['alpha'] * 0.4)
                    if glow_alpha > 0:
                        pg.draw.circle(glow_surface, (*spark['color'], glow_alpha), (center, center), spark_size + 1)
                    
                    # Inner bright core - smaller
                    core_alpha = int(spark['alpha'] * 0.9)
                    if core_alpha > 0:
                        pg.draw.circle(glow_surface, (*spark['color'], core_alpha), (center, center), max(1, spark_size // 2))
                    
                    # Bright center point
                    pg.draw.circle(glow_surface, (255, 255, 255), (center, center), 1)
                    
                    # Render with additive blending for glow effect
                    screen.blit(glow_surface, (render_x - center, render_y - center), special_flags=pg.BLEND_ADD)
                    
    def render_whip_trail_lines(self, screen: pg.Surface, bullets, offset: Tuple[float, float] = (0, 0)):
        """Render thick, curved glowing lines connecting bullets when at full speed."""
        if not self.whip_trail_active or len(bullets) < 2:
            return
            
        # Draw curved connections between bullets with multiple segments for smoothness
        for i in range(len(bullets) - 1):
            bullet1 = bullets[i]
            bullet2 = bullets[i + 1]
            
            start_pos = (bullet1.pos.x + offset[0], bullet1.pos.y + offset[1])
            end_pos = (bullet2.pos.x + offset[0], bullet2.pos.y + offset[1])
            
            # Create curved path with multiple intermediate points
            curve_points = self._generate_curve_points(start_pos, end_pos, 4)  # 4 intermediate points
            
            # Draw thick glowing trail segments between curve points
            for j in range(len(curve_points) - 1):
                p1 = curve_points[j]
                p2 = curve_points[j + 1]
                self._draw_thick_glowing_segment(screen, p1, p2)
                
    def _generate_curve_points(self, start_pos, end_pos, num_points):
        """Generate curved points between start and end positions."""
        points = [start_pos]
        
        # Calculate curve control points for natural bullet trajectory
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < 10:  # Very close bullets - just straight line for performance
            points.append(end_pos)
            return points
            
        # Reduce curve points for very close bullets to optimize performance
        if distance < 25:
            num_points = min(num_points, 2)
        
        # Add slight curve based on bullet spacing and direction
        curve_intensity = min(distance * 0.08, 15)  # Slightly reduced for smoother look
        perpendicular_x = -dy / distance * curve_intensity
        perpendicular_y = dx / distance * curve_intensity
        
        # Add random slight variations for more natural look
        for i in range(1, num_points + 1):
            t = i / (num_points + 1)  # Parameter from 0 to 1
            
            # Quadratic curve calculation
            curve_factor = 4 * t * (1 - t)  # Peak at t=0.5
            
            # Base interpolation
            x = start_pos[0] + t * dx
            y = start_pos[1] + t * dy
            
            # Add curve offset with small random variation
            curve_offset_x = perpendicular_x * curve_factor
            curve_offset_y = perpendicular_y * curve_factor
            
            # Add small random variations for organic feel (reduced for smoother look)
            variation = random.uniform(-2, 2)
            curve_offset_x += variation
            curve_offset_y += variation
            
            points.append((x + curve_offset_x, y + curve_offset_y))
            
        points.append(end_pos)
        return points
        
    def _draw_thick_glowing_segment(self, screen, p1, p2):
        """Draw a thick glowing line segment matching bullet colors."""
        start_x, start_y = int(p1[0]), int(p1[1])
        end_x, end_y = int(p2[0]), int(p2[1])
        
        # Calculate segment length for surface size
        segment_length = int(((start_x - end_x)**2 + (start_y - end_y)**2)**0.5)
        if segment_length == 0:
            return
            
        # Create surface for the glowing segment
        surf_size = max(segment_length + 40, 40)
        glow_surface = pg.Surface((surf_size, surf_size), pg.SRCALPHA)
        
        # Local coordinates on the surface
        local_start = (20, surf_size // 2)
        local_end = (20 + segment_length, surf_size // 2)
        
        # Draw multiple glow layers matching bullet plasma colors
        # Outer plasma field (blue) - very thick
        pg.draw.line(glow_surface, (0, 120, 255, 80), local_start, local_end, 20)
        
        # Middle plasma glow (brighter blue) - thick
        pg.draw.line(glow_surface, (50, 180, 255, 140), local_start, local_end, 14)
        
        # Inner plasma core (bright cyan) - medium
        pg.draw.line(glow_surface, (100, 220, 255, 200), local_start, local_end, 8)
        
        # Bright energy center (white-cyan) - thin but bright
        pg.draw.line(glow_surface, (255, 255, 255, 255), local_start, local_end, 4)
        
        # Calculate rotation angle for the segment
        import math
        angle = math.degrees(math.atan2(end_y - start_y, end_x - start_x))
        
        # Rotate the surface to match segment direction
        rotated_surface = pg.transform.rotate(glow_surface, -angle)
        
        # Position the rotated surface
        rot_rect = rotated_surface.get_rect()
        rot_rect.center = ((start_x + end_x) // 2, (start_y + end_y) // 2)
        
        # Render with additive blending for glow effect
        screen.blit(rotated_surface, rot_rect, special_flags=pg.BLEND_ADD)
            
    def render_shell_casings(self, screen: pg.Surface, offset: Tuple[float, float] = (0, 0)):
        """Render shell casings - disabled for cleaner look."""
        # No shell rendering - removed for clean whip trail aesthetic
        pass
        
    def get_spin_intensity(self) -> float:
        """Get current spin intensity (0.0 to 1.0)."""
        return self.spin_speed / self.max_spin_speed
        
    def is_at_full_speed(self) -> bool:
        """Check if minigun is at full spinning speed."""
        return self.spin_speed >= self.max_spin_speed * 0.9
"""
Visual effects system for the twin-stick shooter game.
Handles combat contrast, hit borders, vignette effects, and atmospheric color grading.
"""

import pygame as pg
import math
from typing import Tuple
from .effects import (ComicDashLine, ParticleEffect, 
                      EnhancedExplosionEffect, MysticalBeamEffect)
from .base_weapon_effects import BaseWeaponEffectsManager, WeaponImpactEffectsManager
from .base_explosion_system import ExplosionManager


class VisualEffectsSystem:
    """Manages visual effects like combat contrast, hit borders, and atmospheric effects."""
    
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize the visual effects system."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Combat contrast effect
        self.combat_contrast_enabled = True
        self.combat_contrast_active = False
        self.combat_contrast_timer = 0.0
        
        # Hit border effect
        self.hit_border_duration = 0.0
        self.hit_border_timer = 0.0
        
        # Vignette effect
        self.vignette_enabled = True
        self.vignette_intensity = 0.3
        
        # Lighting effects
        self.lighting_effects_enabled = True
        self.ambient_lighting = 0.8
        
        # Delta time
        self.dt = 0.016
    
    def update_visual_effects(self, player, enemy_manager, dt: float):
        """Update dynamic visual effects based on game state."""
        self.dt = dt
        
        # Update combat contrast effect
        if player and enemy_manager:
            # For combat contrast - get all enemies and filter by distance
            all_enemies = enemy_manager.get_enemies()
            nearby_enemies = [enemy for enemy in all_enemies 
                             if (enemy.pos - player.pos).length() <= 300]
            if self.combat_contrast_enabled and (nearby_enemies or self.hit_border_duration > 0):
                self.combat_contrast_active = True
                self.combat_contrast_timer = min(1.0, self.combat_contrast_timer + dt * 3.0)
            else:
                self.combat_contrast_timer = max(0.0, self.combat_contrast_timer - dt * 2.0)
                self.combat_contrast_active = self.combat_contrast_timer > 0.1
        
        # Update hit border effect
        if self.hit_border_duration > 0:
            self.hit_border_timer += dt
            if self.hit_border_timer >= self.hit_border_duration:
                self.hit_border_duration = 0.0
                self.hit_border_timer = 0.0
    
    def trigger_hit_border(self, duration: float = 0.5):
        """Trigger red hit border effect."""
        self.hit_border_duration = duration
        self.hit_border_timer = 0.0
    
    def get_atmospheric_color_grading(self, atmospheric_effects):
        """Get color grading factors based on current atmospheric effects."""
        if not hasattr(atmospheric_effects, 'current_atmosphere') or not atmospheric_effects.current_atmosphere:
            return (1.0, 1.0, 1.0)  # No atmospheric effects
        
        atmosphere = atmospheric_effects.current_atmosphere
        if atmosphere == "rain":
            # Cooler blue/white tones
            return (0.8, 0.9, 1.2)
        elif atmosphere == "snow":
            # White/blue/dark tones
            return (0.9, 0.95, 1.1)
        elif atmosphere == "cherry_blossom":
            # Pink/green tones
            return (1.1, 1.05, 0.95)
        else:
            return (1.0, 1.0, 1.0)
    
    def render_ambient_lighting(self, screen: pg.Surface):
        """Apply subtle ambient lighting overlay."""
        return  # COMPLETELY DISABLED TO DEBUG WHITE FLASH
        
        if not self.lighting_effects_enabled or self.ambient_lighting >= 0.9:
            return  # Skip if disabled or nearly full brightness
        
        # Calculate subtle darkness level
        darkness = 1.0 - self.ambient_lighting
        alpha = int(darkness * 60)  # Much lighter overlay (was 120)
        
        if alpha > 5:  # Only render if noticeable
            # Create darkness overlay
            overlay = pg.Surface((self.screen_width, self.screen_height))
            overlay.set_alpha(alpha)
            overlay.fill((0, 0, 20))  # Very dark blue-black
            screen.blit(overlay, (0, 0))
    
    def render_combat_contrast(self, screen: pg.Surface):
        """Render combat contrast effect when enemies are nearby."""
        if not self.combat_contrast_active or self.combat_contrast_timer <= 0:
            return
            
        # Smooth fade in/out
        intensity = min(1.0, self.combat_contrast_timer)
        
        # Enhanced contrast overlay with subtle color shift
        overlay = pg.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(int(30 * intensity))  # Subtle effect
        
        # Very slight red tint for danger feeling
        overlay.fill((255, 240, 240))
        screen.blit(overlay, (0, 0), special_flags=pg.BLEND_MULT)
        
        # Add slight brightness boost
        bright_overlay = pg.Surface((self.screen_width, self.screen_height))
        bright_overlay.set_alpha(int(20 * intensity))
        bright_overlay.fill((255, 255, 255))
        screen.blit(bright_overlay, (0, 0), special_flags=pg.BLEND_ADD)
    
    def render_hit_border(self, screen: pg.Surface):
        """Render red border effect when player is hit."""
        if self.hit_border_duration <= 0:
            return
            
        # Calculate pulsing intensity
        progress = self.hit_border_timer / self.hit_border_duration
        fade_intensity = 1.0 - progress  # Fade out over time
        
        # Pulsing effect
        pulse = 0.5 + 0.5 * math.sin(self.hit_border_timer * 15)  # Fast pulse
        final_intensity = fade_intensity * pulse
        
        if final_intensity > 0.1:
            # Red border overlay
            alpha = int(final_intensity * 100)
            border_thickness = 20
            
            # Create border surfaces
            top_border = pg.Surface((self.screen_width, border_thickness))
            bottom_border = pg.Surface((self.screen_width, border_thickness))
            left_border = pg.Surface((border_thickness, self.screen_height))
            right_border = pg.Surface((border_thickness, self.screen_height))
            
            # Set color and alpha
            border_color = (255, 100, 100)  # Red
            for border in [top_border, bottom_border, left_border, right_border]:
                border.set_alpha(alpha)
                border.fill(border_color)
            
            # Blit borders
            screen.blit(top_border, (0, 0))
            screen.blit(bottom_border, (0, self.screen_height - border_thickness))
            screen.blit(left_border, (0, 0))
            screen.blit(right_border, (self.screen_width - border_thickness, 0))
    
    def render_vignette_effect(self, screen: pg.Surface):
        """Render subtle vignette effect around screen edges."""
        if not self.vignette_enabled or self.vignette_intensity <= 0:
            return
            
        # Create vignette surface
        vignette_surface = pg.Surface((self.screen_width, self.screen_height), pg.SRCALPHA)
        
        # Calculate vignette parameters
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        max_distance = math.sqrt(center_x**2 + center_y**2)
        
        # Create radial gradient
        for radius in range(int(max_distance), 0, -10):
            # Calculate alpha based on distance from center
            alpha_factor = (radius / max_distance) ** 2
            alpha = int(self.vignette_intensity * 255 * alpha_factor)
            
            if alpha > 5:  # Skip very transparent circles
                pg.draw.circle(vignette_surface, (0, 0, 0, alpha), 
                             (center_x, center_y), radius)
        
        # Apply vignette
        screen.blit(vignette_surface, (0, 0), special_flags=pg.BLEND_MULT)
    
    def apply_color_grading(self, screen: pg.Surface, atmospheric_effects):
        """Apply atmospheric color grading to the entire screen."""
        color_factors = self.get_atmospheric_color_grading(atmospheric_effects)
        
        if color_factors == (1.0, 1.0, 1.0):
            return  # No grading needed
        
        # Create color grading overlay
        grading_surface = pg.Surface((self.screen_width, self.screen_height))
        grading_surface.set_alpha(30)  # Subtle effect
        
        # Apply color factors
        red_factor, green_factor, blue_factor = color_factors
        color = (
            int(255 * red_factor) if red_factor > 1.0 else 255,
            int(255 * green_factor) if green_factor > 1.0 else 255,
            int(255 * blue_factor) if blue_factor > 1.0 else 255
        )
        
        grading_surface.fill(color)
        
        # Use appropriate blend mode based on whether we're adding or subtracting color
        if red_factor >= 1.0 or green_factor >= 1.0 or blue_factor >= 1.0:
            screen.blit(grading_surface, (0, 0), special_flags=pg.BLEND_ADD)
        else:
            screen.blit(grading_surface, (0, 0), special_flags=pg.BLEND_MULT)
    
    def toggle_combat_contrast(self):
        """Toggle combat contrast effect."""
        self.combat_contrast_enabled = not self.combat_contrast_enabled
        if not self.combat_contrast_enabled:
            self.combat_contrast_active = False
            self.combat_contrast_timer = 0.0
    
    def toggle_lighting_effects(self):
        """Toggle lighting effects."""
        self.lighting_effects_enabled = not self.lighting_effects_enabled

class EffectsManager:
    """Manages creation, update, and rendering of visual effects."""
    
    def __init__(self):
        """Initialize the effects manager."""
        self.effects = []
        
        # Initialize consolidated weapon effects systems
        self.weapon_effects = BaseWeaponEffectsManager()
        self.impact_effects = WeaponImpactEffectsManager()
        
        # Initialize consolidated explosion system
        self.explosion_manager = ExplosionManager()
    
    def add_effect(self, effect):
        """Add a new effect to the manager."""
        self.effects.append(effect)
    
    def update(self, dt: float, player_pos: pg.Vector2 = None):
        """Update all active effects."""
        # Use a list comprehension for efficient removal of dead effects
        self.effects = [effect for effect in self.effects if not self._update_effect(effect, dt, player_pos)]
        
        # Update consolidated weapon effects
        self.weapon_effects.update(dt)
        self.impact_effects.update(dt)
        
        # Update consolidated explosion system
        self.explosion_manager.update(dt)

    def _update_effect(self, effect, dt: float, player_pos: pg.Vector2) -> bool:
        """Helper to update a single effect and handle different update signatures."""
        if isinstance(effect, ComicDashLine):
            if player_pos:
                return effect.update(dt, player_pos)
            return effect.update(dt, pg.Vector2(0, 0))  # Fallback
        elif isinstance(effect, MysticalBeamEffect):
            return effect.update(dt)
        else:
            return effect.update(dt)

    def render(self, screen: pg.Surface, offset: Tuple[float, float]):
        """Render all active effects."""
        for effect in self.effects:
            effect.render(screen, offset)
        
        # Render consolidated weapon effects
        self.weapon_effects.render_muzzle_flashes(screen, offset)
        self.weapon_effects.render_shell_casings(screen, offset)
        self.impact_effects.render(screen, offset)
        
        # Render consolidated explosion system
        self.explosion_manager.render(screen, offset)
    
    def clear_effects(self):
        """Remove all active effects."""
        self.effects.clear()

    # --- Effect Creation Methods ---

    def add_comic_dash_effect(self, player_pos: pg.Vector2, player_angle: float, speed: float):
        """Create comic-style dash lines for high-speed movement."""
        if speed > 250:  # Only for high speed
            num_lines = 3
            for i in range(num_lines):
                angle_offset = (i - 1) * 25  # -25, 0, 25 degrees
                line_angle = math.radians(player_angle + 180 + angle_offset) # Opposite to movement
                
                start_dist = 30 + i * 10
                end_dist = 60 + i * 15
                
                start_x = start_dist * math.cos(line_angle)
                start_y = start_dist * math.sin(line_angle)
                end_x = end_dist * math.cos(line_angle)
                end_y = end_dist * math.sin(line_angle)
                
                thickness = 4 - i
                alpha = 120 - i * 20
                
                self.add_effect(ComicDashLine(start_x, start_y, end_x, end_y, thickness, (255, 255, 255, alpha)))

    def add_particle_effect(self, x: float, y: float, color: Tuple[int, int, int], 
                            particle_count: int = 10, speed: float = 120):
        """Create a simple particle burst."""
        self.add_effect(ParticleEffect(x, y, color, particle_count, speed))

    def add_enhanced_explosion(self, x: float, y: float, explosion_type: str, 
                               color: Tuple[int, int, int] = (255, 100, 0),
                               direction_angle: float = None, spread_angle: float = 360):
        """Create a more complex, multi-layered explosion."""
        # Core flash
        if explosion_type == "normal":
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 255, 200), 15, 250, (4, 8), "core", direction_angle, spread_angle))
            # Fiery parts
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 150, 0), 25, 180, (3, 7), "fire", direction_angle, spread_angle))
            # Smoke
            self.add_effect(EnhancedExplosionEffect(x, y, (80, 80, 80), 20, 80, (5, 10), "smoke", direction_angle, spread_angle))
            # Sparks
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 255, 255), 15, 350, (1, 3), "sparks", direction_angle, spread_angle))
        elif explosion_type == "muzzle_flash":
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 220, 180), 8, 400, (2, 5), "muzzle_flash", direction_angle, 45))
        elif explosion_type == "shotgun_blast":
            # Core flash
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 255, 220), 10, 500, (3, 6), "pellet_core", direction_angle, 30))
            # Sparks
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 200, 100), 15, 600, (1, 3), "pellet_sparks", direction_angle, 35))
        elif explosion_type == "energy_weapon":
            # Energy wisps
            self.add_effect(EnhancedExplosionEffect(x, y, (150, 200, 255), 12, 300, (2, 4), "energy_wisps", direction_angle, 60))
            # Energy residue
            self.add_effect(EnhancedExplosionEffect(x, y, (100, 150, 200), 8, 100, (3, 5), "energy_residue", direction_angle, 90))
        elif explosion_type == "tactical_grenade":
            # Bright flash
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 255, 255), 5, 600, (10, 15), "tactical_flash", direction_angle, 360))
            # Anime-style sharp flash
            self.add_effect(EnhancedExplosionEffect(x, y, (200, 220, 255), 8, 800, (2, 4), "anime_flash", direction_angle, 360))
            # Dense smoke
            self.add_effect(EnhancedExplosionEffect(x, y, (150, 150, 150), 25, 120, (8, 15), "tactical_smoke", direction_angle, 360))
            # High-velocity sparks
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 230, 200), 20, 450, (1, 3), "tactical_sparks", direction_angle, 360))
            # Debris
            self.add_effect(EnhancedExplosionEffect(x, y, (100, 80, 60), 15, 200, (2, 5), "tactical_debris", direction_angle, 360))
        elif explosion_type == "bullet_impact":
            # Small, sharp flash
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 255, 220), 5, 250, (2, 4), "impact_flash", direction_angle, 90))
            # Tiny sparks
            self.add_effect(EnhancedExplosionEffect(x, y, (200, 200, 200), 8, 350, (1, 2), "sparks", direction_angle, 90))
        elif explosion_type == "cyber_sword_clash":
            # Neon burst
            self.add_effect(EnhancedExplosionEffect(x, y, (0, 255, 255), 10, 900, (2, 4), "neon_burst", direction_angle, 45))
            # Digital fragments
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 0, 255), 15, 700, (1, 3), "digital_fragments", direction_angle, 60))
            # Holographic glow
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 255, 255), 5, 200, (5, 8), "holographic_glow", direction_angle, 90))
        elif explosion_type == "anime_dash":
            # Energy burst
            self.add_effect(EnhancedExplosionEffect(x, y, (200, 200, 255), 12, 400, (3, 5), "anime_energy_burst", direction_angle, 120))
            # Skid marks
            self.add_effect(EnhancedExplosionEffect(x, y, (100, 100, 100), 8, 80, (4, 6), "skid_mark", direction_angle, 60))
        elif explosion_type == "v_shaped_blast":
            # CLEAN bright red V-shaped blast - single layer for clarity
            self.add_effect(EnhancedExplosionEffect(x, y, (255, 0, 0), 80, 400, (8, 15), "v_blast_clean", direction_angle, spread_angle))

    def add_mystical_beam_effect(self, player_ref, relative_angle: float, beam_range: float, 
                                 width: float, duration: float, color: list, damage: float):
        """Create a mystical beam effect."""
        beam = MysticalBeamEffect(player_ref, relative_angle, beam_range, width, duration, color, damage)
        self.add_effect(beam)
        return beam
    
    # --- Additional Methods Required by main.py ---
    
    def check_beam_damage(self, enemies):
        """Check for beam damage against enemies and return damage events."""
        damage_events = []
        
        for effect in self.effects:
            if isinstance(effect, MysticalBeamEffect):
                for enemy in enemies:
                    if effect.check_enemy_collision(enemy):
                        damage_events.append({
                            'enemy': enemy,
                            'damage': effect.damage,
                            'beam': effect
                        })
        
        return damage_events
    
    def add_explosion(self, x: float, y: float, color: Tuple[int, int, int] = (255, 150, 0), small: bool = False):
        """Add a generic explosion effect."""
        if small:
            # Use new consolidated explosion system
            self.explosion_manager.create_simple_explosion(x, y, "small", color, particle_count=8, speed=150)
            # Keep legacy for compatibility
            self.add_enhanced_explosion(x, y, "bullet_impact", color)
        else:
            # Use new consolidated explosion system  
            self.explosion_manager.create_simple_explosion(x, y, "basic", color, particle_count=15, speed=200)
            # Keep legacy for compatibility
            self.add_enhanced_explosion(x, y, "normal", color)
    
    def add_assault_rifle_muzzle_flash(self, x: float, y: float, angle: float):
        """Add muzzle flash for assault rifle."""
        # Use consolidated weapon effects system
        self.weapon_effects.create_muzzle_flash(x, y, angle, "Assault Rifle")
        # Also keep legacy explosion effect for compatibility
        self.add_enhanced_explosion(x, y, "muzzle_flash", (255, 220, 180), angle, 45)
    
    def add_shotgun_muzzle_flash(self, x: float, y: float, angle: float):
        """Add muzzle flash for shotgun."""
        # Use consolidated weapon effects system
        self.weapon_effects.create_muzzle_flash(x, y, angle, "Shotgun")
        # Also keep legacy explosion effect for compatibility  
        self.add_enhanced_explosion(x, y, "shotgun_blast", (255, 200, 100), angle, 35)
    
    def add_smg_muzzle_flash(self, x: float, y: float, angle: float):
        """Add muzzle flash for SMG."""
        # Use consolidated weapon effects system
        self.weapon_effects.create_muzzle_flash(x, y, angle, "SMG")
        # Also keep legacy explosion effect for compatibility
        self.add_enhanced_explosion(x, y, "muzzle_flash", (200, 220, 255), angle, 30)
    
    def add_mystical_slash_sparkles(self, x: float, y: float, angle: float, range_val: float):
        """Add sparkle effects for mystical slash."""
        self.add_enhanced_explosion(x, y, "anime_energy_burst", (200, 200, 255), angle, 90)
    
    def add_mystical_thrust_sparkles(self, x: float, y: float, angle: float, range_val: float):
        """Add sparkle effects for mystical thrust."""
        self.add_enhanced_explosion(x, y, "energy_weapon", (150, 200, 255), angle, 60)
    
    def add_sword_impact_effect(self, x: float, y: float):
        """Add impact effect for sword attacks."""
        self.add_enhanced_explosion(x, y, "cyber_sword_clash", (0, 255, 255))
    
    def add_mystical_beam(self, player_ref, relative_angle: float, beam_range: float, 
                          width: float, duration: float, color: list, damage: float):
        """Create a mystical beam effect (alias for add_mystical_beam_effect)."""
        return self.add_mystical_beam_effect(player_ref, relative_angle, beam_range, width, duration, color, damage)
    
    def add_mystical_impact_effect(self, x: float, y: float):
        """Add impact effect for mystical attacks."""
        self.add_enhanced_explosion(x, y, "neon_burst", (255, 0, 255))
    
    def add_pellet_impact_effect(self, x: float, y: float):
        """Add pellet impact effect for shotgun energy balls."""
        self.add_enhanced_explosion(x, y, "pellet_core", (255, 200, 100))
    
    def add_tracer_impact_effect(self, x: float, y: float):
        """Add tracer impact effect for assault rifle rounds."""
        self.add_enhanced_explosion(x, y, "impact_flash", (255, 255, 220))
    
    def add_neon_impact_effect(self, x: float, y: float):
        """Add neon impact effect for SMG cyberpunk rounds."""
        self.add_enhanced_explosion(x, y, "neon_burst", (0, 255, 255))

    def create_bullet_impact(self, x: float, y: float):
        """Create generic bullet impact effect for network synchronization."""
        # Use a generic weapon impact effect for networked bullet hits
        self.add_weapon_impact_effect(x, y, "generic", "enemy")
    
    # Consolidated weapon effects methods
    def add_weapon_impact_effect(self, x: float, y: float, weapon_type: str, target_type: str = "enemy"):
        """Add weapon-specific impact effect using consolidated system."""
        self.impact_effects.create_impact_effect(x, y, weapon_type, target_type)
    
    def add_shell_casing_effect(self, x: float, y: float, angle: float, weapon_type: str):
        """Add shell casing effect using consolidated system."""
        self.weapon_effects.create_shell_casing(x, y, angle, weapon_type)
    
    def add_minigun_muzzle_flash(self, x: float, y: float, angle: float):
        """Add muzzle flash for minigun using consolidated system."""
        self.weapon_effects.create_muzzle_flash(x, y, angle, "Minigun")
    
    # Consolidated explosion system methods
    def add_rocket_explosion(self, x: float, y: float, radius: float = 150):
        """Add large rocket explosion using consolidated system."""
        self.explosion_manager.create_complex_explosion(x, y, "rocket", radius, damage=100)
    
    def add_grenade_explosion(self, x: float, y: float, radius: float = 120):
        """Add grenade explosion using consolidated system."""
        self.explosion_manager.create_complex_explosion(x, y, "grenade", radius, damage=75)
    
    def add_weapon_specific_explosion(self, x: float, y: float, weapon_type: str):
        """Add weapon-specific explosion effect."""
        self.explosion_manager.create_weapon_explosion(x, y, weapon_type)
    
    def add_v_shaped_blast(self, x: float, y: float, angle: float):
        """Add V-shaped blast visual effect for shotgun special attack."""
        import math
        
        # Convert angle to radians
        blast_angle_rad = math.radians(angle)
        
        # Create STRAIGHT V-shaped fire lines (not curved particle explosions)
        # Match damage system: 45° total angle (±22.5°)
        left_arm_angle = angle - 22.5   # Match damage system left arm
        right_arm_angle = angle + 22.5  # Match damage system right arm
        
        print(f"🔥 V-BLAST VISUAL: Creating fire lines at ({x:.1f}, {y:.1f}) - Left: {left_arm_angle}°, Right: {right_arm_angle}°")
        
        # Create straight fire lines along each V-arm - MATCH 400px damage range
        for distance in range(20, 400, 10):  # Match damage system range (400px)
            # LEFT ARM - Straight line of red fire effects
            left_x = x + distance * math.cos(math.radians(left_arm_angle))
            left_y = y + distance * math.sin(math.radians(left_arm_angle))
            
            # Bright red fire core (not explosive particles)
            left_fire = EnhancedExplosionEffect(
                left_x, left_y,
                color=(255, 40, 0),  # Bright red-orange fire
                particle_count=6,   # Fewer particles for straight line effect
                speed=15,           # Very slow for fire beam
                size_range=(4, 8),  # Medium-sized fire particles
                explosion_type="muzzle_flash",  # Short duration, stays in place
                direction_angle=left_arm_angle,  # Along the V-arm
                spread_angle=1      # Very narrow (almost no spread) for straight line
            )
            self.add_effect(left_fire)
            
            # RIGHT ARM - Straight line of red fire effects  
            right_x = x + distance * math.cos(math.radians(right_arm_angle))
            right_y = y + distance * math.sin(math.radians(right_arm_angle))
            
            # Bright red fire core (not explosive particles)
            right_fire = EnhancedExplosionEffect(
                right_x, right_y,
                color=(255, 40, 0),  # Bright red-orange fire
                particle_count=6,   # Fewer particles for straight line effect
                speed=15,           # Very slow for fire beam
                size_range=(4, 8),  # Medium-sized fire particles  
                explosion_type="muzzle_flash",  # Short duration, stays in place
                direction_angle=right_arm_angle,  # Along the V-arm
                spread_angle=1      # Very narrow (almost no spread) for straight line
            )
            self.add_effect(right_fire)
        
        # Fill the STRAIGHT V-area with red fire (not curved fill) - MATCH 400px range
        for distance in range(30, 400, 15):  # Match damage system range (400px)
            # Calculate multiple points between the two straight V-arms
            for fill_step in range(1, 8):  # 7 fill lines between the main arms
                # Interpolate angle between left and right arms (straight interpolation)
                fill_ratio = fill_step / 8.0
                fill_angle = left_arm_angle + (right_arm_angle - left_arm_angle) * fill_ratio
                
                fill_x = x + distance * math.cos(math.radians(fill_angle))
                fill_y = y + distance * math.sin(math.radians(fill_angle))
                
                # Red fire fill effect (smaller than main beams)
                fill_fire = EnhancedExplosionEffect(
                    fill_x, fill_y,
                    color=(200, 60, 0),  # Slightly darker red fire for fill
                    particle_count=4,    # Fewer particles for fill
                    speed=12,            # Very slow
                    size_range=(2, 5),   # Smaller fill particles
                    explosion_type="muzzle_flash",
                    direction_angle=fill_angle,
                    spread_angle=1       # Very narrow for straight fill
                )
                self.add_effect(fill_fire)
        
        # Add MASSIVE bright central flash at blast origin (where beams meet)
        origin_flash = EnhancedExplosionEffect(
            x, y,
            color=(255, 255, 0),  # Bright yellow for maximum visibility
            particle_count=40,  # Many particles
            speed=80,
            size_range=(15, 30),  # HUGE particles for visibility
            explosion_type="fire"  # Longer lasting than muzzle_flash
        )
        self.add_effect(origin_flash)
        
        # Add secondary white flash for even more visibility
        white_flash = EnhancedExplosionEffect(
            x, y,
            color=(255, 255, 255),  # Pure white
            particle_count=30,
            speed=60,
            size_range=(12, 25),  # Large white particles
            explosion_type="smoke"  # Longest duration
        )
        self.add_effect(white_flash)
        
        print(f"🔥 V-BLAST COMPLETE: Created {28 * 7 + 2} fire effects for full V-shaped blast")
    
    def add_dash_effect(self, x: float, y: float, direction):
        """Add dash effect (alias for comic dash effect)."""
        # Convert direction to player position and angle for comic dash effect
        player_pos = pg.Vector2(x, y)
        
        # Handle direction parameter - could be Vector2 or angle
        if hasattr(direction, 'x') and hasattr(direction, 'y'):
            # It's a Vector2 direction from player movement
            player_angle = math.degrees(math.atan2(direction.y, direction.x))
        elif isinstance(direction, (int, float)):
            # It's already an angle in radians, convert to degrees
            player_angle = math.degrees(direction)
        else:
            # Default direction (right)
            player_angle = 0
            
        # Use high speed for dash effect
        self.add_comic_dash_effect(player_pos, player_angle, 300)
    
    def add_hit_effect(self, x: float, y: float, direction: float = 0):
        """Add hit effect when player takes damage."""
        self.add_enhanced_explosion(x, y, "impact_flash", (255, 100, 100), direction, 90)
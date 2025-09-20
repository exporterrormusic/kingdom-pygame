"""
Achievement Integration Guide for Kingdom-Pygame

This guide shows how to connect the achievement system to actual gameplay events
to unlock achievements during gameplay.
"""

# STEP 1: Import the achievement system in your main game files

# In your main game loop or core systems:
from src.systems.achievement_manager import AchievementManager
from src.ui.achievement_ui import AchievementNotification

# STEP 2: Initialize the achievement manager in your game class

class Game:
    def __init__(self):
        # ... existing initialization ...
        self.achievement_manager = AchievementManager()
        self.achievement_notifications = []  # Store active notifications
    
    def show_achievement_notification(self, achievement):
        """Show achievement unlock notification during gameplay."""
        notification = AchievementNotification(achievement)
        self.achievement_notifications.append(notification)
        print(f"Achievement unlocked: {achievement.name}")

# STEP 3: Connect achievements to combat events

def on_enemy_killed(self, enemy_type, kill_count=1):
    """Called when enemies are defeated."""
    # Update kill-related achievements
    newly_unlocked = self.achievement_manager.on_enemy_killed(kill_count)
    
    # Show notifications for newly unlocked achievements
    for achievement in newly_unlocked:
        if achievement:  # Check for None
            self.show_achievement_notification(achievement)

# STEP 4: Connect achievements to wave progression

def on_wave_completed(self, wave_number, time_taken_minutes=None, damage_taken=0):
    """Called when a wave is completed."""
    # Update wave completion achievements
    newly_unlocked = self.achievement_manager.on_wave_completed(wave_number)
    
    # Check for perfect wave (no damage taken)
    if damage_taken == 0:
        perfect_unlocked = self.achievement_manager.on_perfect_wave()
        newly_unlocked.extend(perfect_unlocked)
    
    # Check for speed run achievements
    if time_taken_minutes:
        speed_unlocked = self.achievement_manager.on_speed_run(wave_number, time_taken_minutes)
        newly_unlocked.extend(speed_unlocked)
    
    # Show notifications
    for achievement in newly_unlocked:
        if achievement:
            self.show_achievement_notification(achievement)

# STEP 5: Connect achievements to resource collection

def on_cores_collected(self, cores_amount):
    """Called when rapture cores are collected."""
    newly_unlocked = self.achievement_manager.on_cores_collected(cores_amount)
    
    for achievement in newly_unlocked:
        if achievement:
            self.show_achievement_notification(achievement)

# STEP 6: Connect achievements to character unlocks

def on_character_unlocked(self, character_name):
    """Called when a new character is unlocked."""
    newly_unlocked = self.achievement_manager.on_character_unlocked()
    
    for achievement in newly_unlocked:
        if achievement:
            self.show_achievement_notification(achievement)

# STEP 7: Render achievement notifications during gameplay

def render_achievement_notifications(self, screen):
    """Render achievement notifications over the game."""
    # Remove expired notifications
    self.achievement_notifications = [
        notif for notif in self.achievement_notifications if not notif.is_expired
    ]
    
    # Render active notifications
    for i, notification in enumerate(self.achievement_notifications):
        y_offset = i * 120  # Stack notifications vertically
        self.render_notification_popup(screen, notification, y_offset)

def render_notification_popup(self, screen, notification, y_offset):
    """Render a single achievement notification popup."""
    import pygame
    
    # Create notification surface
    notif_width = 400
    notif_height = 100
    notif_surface = pygame.Surface((notif_width, notif_height), pygame.SRCALPHA)
    
    # Background with rounded corners
    bg_color = (40, 50, 70, 200)  # Semi-transparent dark blue
    pygame.draw.rect(notif_surface, bg_color, (0, 0, notif_width, notif_height), border_radius=15)
    
    # Gold border
    border_color = (255, 215, 0, 255)  # Gold
    pygame.draw.rect(notif_surface, border_color, (0, 0, notif_width, notif_height), 3, border_radius=15)
    
    # "ACHIEVEMENT UNLOCKED!" text
    font = pygame.font.Font(None, 24)
    unlock_text = font.render("ACHIEVEMENT UNLOCKED!", True, (255, 215, 0))
    unlock_rect = unlock_text.get_rect(centerx=notif_width // 2, y=10)
    notif_surface.blit(unlock_text, unlock_rect)
    
    # Achievement name
    name_font = pygame.font.Font(None, 28)
    name_text = name_font.render(notification.achievement.name, True, (100, 255, 100))
    name_rect = name_text.get_rect(centerx=notif_width // 2, y=35)
    notif_surface.blit(name_text, name_rect)
    
    # Trophy icon
    trophy_font = pygame.font.Font(None, 32)
    trophy_text = trophy_font.render("🏆", True, (255, 215, 0))
    trophy_rect = trophy_text.get_rect(x=10, centery=notif_height // 2)
    notif_surface.blit(trophy_text, trophy_rect)
    
    # Cores reward
    if notification.achievement.reward_cores > 0:
        cores_font = pygame.font.Font(None, 20)
        cores_text = cores_font.render(f"+{notification.achievement.reward_cores} Cores", True, (255, 215, 0))
        cores_rect = cores_text.get_rect(centerx=notif_width // 2, y=60)
        notif_surface.blit(cores_text, cores_rect)
    
    # Apply fade effect
    notif_surface.set_alpha(notification.alpha)
    
    # Blit to screen (top-right corner)
    screen.blit(notif_surface, (screen.get_width() - notif_width - 20, 20 + y_offset))

# STEP 8: Integration example for your specific game systems

class CombatSystem:
    def __init__(self, achievement_manager):
        self.achievement_manager = achievement_manager
    
    def handle_enemy_death(self, enemy, player):
        """Called when an enemy dies."""
        # Your existing enemy death logic...
        
        # Update achievements
        newly_unlocked = self.achievement_manager.on_enemy_killed(1)
        for achievement in newly_unlocked:
            if achievement:
                # Notify the game to show achievement notification
                player.game.show_achievement_notification(achievement)

class WaveManager:
    def __init__(self, achievement_manager):
        self.achievement_manager = achievement_manager
        self.wave_start_time = None
        self.player_damage_taken = 0
    
    def start_wave(self, wave_number):
        """Start a new wave."""
        import time
        self.wave_start_time = time.time()
        self.player_damage_taken = 0
    
    def complete_wave(self, wave_number, player):
        """Complete the current wave."""
        import time
        
        # Calculate time taken
        time_taken_seconds = time.time() - self.wave_start_time if self.wave_start_time else 0
        time_taken_minutes = time_taken_seconds / 60.0
        
        # Update achievements
        newly_unlocked = self.achievement_manager.on_wave_completed(wave_number)
        
        # Check for perfect wave
        if self.player_damage_taken == 0:
            perfect_unlocked = self.achievement_manager.on_perfect_wave()
            newly_unlocked.extend(perfect_unlocked)
        
        # Check for speed achievements
        speed_unlocked = self.achievement_manager.on_speed_run(wave_number, time_taken_minutes)
        newly_unlocked.extend(speed_unlocked)
        
        # Show notifications
        for achievement in newly_unlocked:
            if achievement:
                player.game.show_achievement_notification(achievement)
    
    def player_took_damage(self, damage_amount):
        """Track player damage for perfect wave achievement."""
        self.player_damage_taken += damage_amount

# STEP 9: Menu integration (already implemented)

# The achievement system is already integrated into the menu system.
# Players can access achievements through: Main Menu -> ACHIEVEMENTS
# The achievement menu shows:
# - All achievement categories (Combat, Survival, Character, etc.)
# - Progress bars for incomplete achievements
# - Unlock dates and rewards for completed achievements
# - Detailed views for each achievement

# STEP 10: Save system integration

def save_game_with_achievements(self):
    """Save the game including achievement progress."""
    # Achievement manager automatically saves to saves/achievements.json
    # Your existing save logic will work alongside this
    
    # The achievement save file is independent and persistent
    self.achievement_manager.save_achievements()

# ADDITIONAL NOTES:

# 1. Achievement definitions are in AchievementManager._initialize_achievements()
#    You can modify, add, or remove achievements by editing that method.

# 2. Achievement progress is automatically saved to saves/achievements.json

# 3. The system supports different achievement types:
#    - COUNTER: Incremental achievements (kill 100 enemies)
#    - MILESTONE: One-time achievements (reach wave 10)
#    - PROGRESS: Percentage-based achievements

# 4. Hidden achievements are only shown after being unlocked

# 5. Rapture core rewards are automatically tracked and can be used in shops

# 6. All achievements have categories for better organization in the UI
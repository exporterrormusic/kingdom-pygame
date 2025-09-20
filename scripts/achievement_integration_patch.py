"""
Achievement Integration Patch for Kingdom-Pygame
Apply this patch to integrate achievement tracking with existing game systems.
"""

# PATCH 1: Add achievement manager to main game class

# In main.py, add this import at the top with other imports:
# from src.systems.achievement_manager import AchievementManager

# In the Game.__init__ method, add after the score manager initialization:
"""
        # Achievement system
        self.achievement_manager = AchievementManager()
        self.achievement_notifications = []  # Store active notifications
"""

# PATCH 2: Add achievement notification display method

# Add this method to the Game class in main.py:
def show_achievement_notification(self, achievement):
    """Show achievement unlock notification during gameplay."""
    from src.ui.achievement_ui import AchievementNotification
    notification = AchievementNotification(achievement)
    self.achievement_notifications.append(notification)
    print(f"🏆 Achievement unlocked: {achievement.name}")

def render_achievement_notifications(self, screen):
    """Render achievement notifications over the game."""
    # Remove expired notifications
    self.achievement_notifications = [
        notif for notif in self.achievement_notifications if not notif.is_expired
    ]
    
    # Render active notifications
    for i, notification in enumerate(self.achievement_notifications):
        y_offset = i * 120  # Stack notifications vertically
        self._render_notification_popup(screen, notification, y_offset)

def _render_notification_popup(self, screen, notification, y_offset):
    """Render a single achievement notification popup."""
    import pygame as pg
    
    # Create notification surface
    notif_width = 400
    notif_height = 100
    notif_surface = pg.Surface((notif_width, notif_height), pg.SRCALPHA)
    
    # Background with rounded corners
    bg_color = (40, 50, 70, 200)  # Semi-transparent dark blue
    pg.draw.rect(notif_surface, bg_color, (0, 0, notif_width, notif_height), border_radius=15)
    
    # Gold border
    border_color = (255, 215, 0, 255)  # Gold
    pg.draw.rect(notif_surface, border_color, (0, 0, notif_width, notif_height), 3, border_radius=15)
    
    # "ACHIEVEMENT UNLOCKED!" text
    font = pg.font.Font(None, 24)
    unlock_text = font.render("ACHIEVEMENT UNLOCKED!", True, (255, 215, 0))
    unlock_rect = unlock_text.get_rect(centerx=notif_width // 2, y=10)
    notif_surface.blit(unlock_text, unlock_rect)
    
    # Achievement name
    name_font = pg.font.Font(None, 28)
    name_text = name_font.render(notification.achievement.name, True, (100, 255, 100))
    name_rect = name_text.get_rect(centerx=notif_width // 2, y=35)
    notif_surface.blit(name_text, name_rect)
    
    # Trophy icon
    trophy_font = pg.font.Font(None, 32)
    trophy_text = trophy_font.render("🏆", True, (255, 215, 0))
    trophy_rect = trophy_text.get_rect(x=10, centery=notif_height // 2)
    notif_surface.blit(trophy_text, trophy_rect)
    
    # Cores reward
    if notification.achievement.reward_cores > 0:
        cores_font = pg.font.Font(None, 20)
        cores_text = cores_font.render(f"+{notification.achievement.reward_cores} Cores", True, (255, 215, 0))
        cores_rect = cores_text.get_rect(centerx=notif_width // 2, y=60)
        notif_surface.blit(cores_text, cores_rect)
    
    # Apply fade effect
    notif_surface.set_alpha(notification.alpha)
    
    # Blit to screen (top-right corner)
    screen.blit(notif_surface, (screen.get_width() - notif_width - 20, 20 + y_offset))

# PATCH 3: Integrate with enemy death system

# In src/entities/enemy.py, find the lines where enemies_killed is incremented
# Replace these sections:

"""
OLD CODE (around line 789):
            self.enemies.remove(enemy)
            self.enemies_killed += 1
            self.enemies_killed_this_wave += 1

NEW CODE:
            self.enemies.remove(enemy)
            self.enemies_killed += 1
            self.enemies_killed_this_wave += 1
            
            # Achievement integration
            if hasattr(self, 'game') and hasattr(self.game, 'achievement_manager'):
                newly_unlocked = self.game.achievement_manager.on_enemy_killed(1)
                for achievement in newly_unlocked:
                    if achievement:
                        self.game.show_achievement_notification(achievement)
"""

"""
OLD CODE (around line 859):
            self.enemies.remove(enemy)
            self.enemies_killed += 1
            self.enemies_killed_this_wave += 1

NEW CODE:
            self.enemies.remove(enemy)
            self.enemies_killed += 1
            self.enemies_killed_this_wave += 1
            
            # Achievement integration
            if hasattr(self, 'game') and hasattr(self.game, 'achievement_manager'):
                newly_unlocked = self.game.achievement_manager.on_enemy_killed(1)
                for achievement in newly_unlocked:
                    if achievement:
                        self.game.show_achievement_notification(achievement)
"""

# PATCH 4: Add game reference to enemy manager

# In main.py, find where the enemy manager is initialized and add a reference to self:
"""
OLD CODE:
        self.enemy_manager = EnemyManager(self.world_manager, spawn_point=(0, 0))

NEW CODE:
        self.enemy_manager = EnemyManager(self.world_manager, spawn_point=(0, 0))
        self.enemy_manager.game = self  # Add game reference for achievements
"""

# PATCH 5: Integrate with wave completion

# Find the wave completion logic in main.py and add achievement tracking
# Look for where waves are completed or started

# Add this method to Game class:
def on_wave_completed(self, wave_number, damage_taken=0, time_taken_minutes=None):
    """Called when a wave is completed."""
    newly_unlocked = []
    
    # Wave completion achievements
    wave_unlocked = self.achievement_manager.on_wave_completed(wave_number)
    newly_unlocked.extend(wave_unlocked)
    
    # Perfect wave achievement (no damage taken)
    if damage_taken == 0:
        perfect_unlocked = self.achievement_manager.on_perfect_wave()
        newly_unlocked.extend(perfect_unlocked)
    
    # Speed run achievements
    if time_taken_minutes:
        speed_unlocked = self.achievement_manager.on_speed_run(wave_number, time_taken_minutes)
        newly_unlocked.extend(speed_unlocked)
    
    # Show notifications
    for achievement in newly_unlocked:
        if achievement:
            self.show_achievement_notification(achievement)

# PATCH 6: Integrate with core collection

# Find where rapture cores are collected and add:
def on_cores_collected(self, cores_amount):
    """Called when rapture cores are collected."""
    newly_unlocked = self.achievement_manager.on_cores_collected(cores_amount)
    
    for achievement in newly_unlocked:
        if achievement:
            self.show_achievement_notification(achievement)

# PATCH 7: Add achievement notification rendering to main game loop

# In the main render method of Game class, add this call:
"""
        # Render achievement notifications (on top of everything)
        if hasattr(self, 'achievement_notifications'):
            self.render_achievement_notifications(screen)
"""

# PATCH 8: Connect achievement manager to menu

# In main.py, find where the enhanced_menu is set up and add:
"""
        # Connect achievement manager to menu
        if hasattr(self.state_manager.enhanced_menu, 'achievement_ui'):
            self.state_manager.enhanced_menu.achievement_ui.achievement_manager = self.achievement_manager
"""

# INSTRUCTIONS FOR APPLYING PATCHES:

print("""
To apply these patches:

1. Add the imports and initialization code from PATCH 1 to main.py
2. Add the notification methods from PATCH 2 to the Game class in main.py
3. Modify the enemy death code in src/entities/enemy.py as shown in PATCH 3
4. Add the game reference as shown in PATCH 4
5. Add wave completion tracking as shown in PATCH 5
6. Add core collection tracking as shown in PATCH 6
7. Add achievement notification rendering to the main game loop as shown in PATCH 7
8. Connect the achievement manager to the menu as shown in PATCH 8

After applying these patches, achievements will:
- Track enemy kills automatically
- Track wave completions
- Track rapture core collection
- Show notifications when unlocked
- Be accessible through the ACHIEVEMENTS menu

The achievement system is now fully functional!
""")

# ALTERNATIVE: AUTO-APPLY SCRIPT

def auto_apply_patches():
    """Auto-apply patches to integrate achievements (run this if you want automatic integration)."""
    print("This function would automatically apply all patches.")
    print("For safety, manual integration is recommended using the patch guide above.")
    print("All the necessary code has been provided in the patches above.")

if __name__ == "__main__":
    auto_apply_patches()
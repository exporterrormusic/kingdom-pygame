"""
Achievement UI system for Kingdom-Pygame.
Displays achievements, progress, and notifications.
"""

import pygame
import math
from typing import List, Optional, Dict, Tuple
from enum import Enum

from src.systems.achievement_manager import AchievementManager, Achievement, AchievementCategory


class AchievementUIState(Enum):
    """States for achievement UI navigation."""
    OVERVIEW = "overview"
    CATEGORY = "category"
    DETAIL = "detail"


class AchievementNotification:
    """Represents a notification for a newly unlocked achievement."""
    
    def __init__(self, achievement: Achievement):
        self.achievement = achievement
        self.start_time = pygame.time.get_ticks()
        self.duration = 4000  # 4 seconds
        self.fade_in_time = 500
        self.fade_out_time = 500
        
    @property
    def elapsed_time(self) -> int:
        return pygame.time.get_ticks() - self.start_time
    
    @property
    def is_expired(self) -> bool:
        return self.elapsed_time > self.duration
    
    @property
    def alpha(self) -> int:
        elapsed = self.elapsed_time
        if elapsed < self.fade_in_time:
            return int(255 * (elapsed / self.fade_in_time))
        elif elapsed > self.duration - self.fade_out_time:
            remaining = self.duration - elapsed
            return int(255 * (remaining / self.fade_out_time))
        return 255


class AchievementUI:
    """Handles achievement UI rendering and interaction."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.achievement_manager = AchievementManager()
        
        # UI State
        self.current_state = AchievementUIState.OVERVIEW
        self.selected_category = None
        self.selected_achievement = None
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Selection and navigation
        self.selected_index = 0
        self.category_selected_index = 0
        
        # Fonts (initialize lazily)
        self.title_font = None
        self.header_font = None
        self.text_font = None
        self.small_font = None
        self._fonts_initialized = False
        
        # Colors
        self.bg_color = (20, 25, 40)
        self.panel_color = (40, 50, 70)
        self.selected_color = (70, 90, 130)
        self.text_color = (220, 220, 220)
        self.unlocked_color = (100, 200, 100)
        self.locked_color = (150, 150, 150)
        self.progress_bg_color = (60, 60, 80)
        self.progress_fill_color = (100, 150, 255)
        self.gold_color = (255, 215, 0)
        
        # Notifications
        self.notifications: List[AchievementNotification] = []
        
        # Category icons and names
        self.category_display = {
            AchievementCategory.COMBAT: {"name": "Combat", "icon": "⚔️"},
            AchievementCategory.SURVIVAL: {"name": "Survival", "icon": "🛡️"},
            AchievementCategory.CHARACTER: {"name": "Characters", "icon": "👥"},
            AchievementCategory.EXPLORATION: {"name": "Exploration", "icon": "🗺️"},
            AchievementCategory.COLLECTION: {"name": "Collection", "icon": "💎"},
            AchievementCategory.SPECIAL: {"name": "Special", "icon": "⭐"}
        }
    
    def _ensure_fonts_initialized(self):
        """Initialize fonts if not already done."""
        if not self._fonts_initialized:
            try:
                self.title_font = pygame.font.Font(None, 36)
                self.header_font = pygame.font.Font(None, 28)
                self.text_font = pygame.font.Font(None, 24)
                self.small_font = pygame.font.Font(None, 20)
                self._fonts_initialized = True
            except pygame.error:
                # If fonts can't be initialized, use None and handle gracefully
                self.title_font = None
                self.header_font = None
                self.text_font = None
                self.small_font = None
                self._fonts_initialized = False
    
    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events. Returns action to perform or None."""
        self._ensure_fonts_initialized()
        
        if event.type == pygame.KEYDOWN:
            if self.current_state == AchievementUIState.OVERVIEW:
                return self._handle_overview_input(event)
            elif self.current_state == AchievementUIState.CATEGORY:
                return self._handle_category_input(event)
            elif self.current_state == AchievementUIState.DETAIL:
                return self._handle_detail_input(event)
        return None
    
    def _handle_overview_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input in overview state."""
        categories = list(AchievementCategory)
        
        if event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(categories)
        elif event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(categories)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            self.selected_category = categories[self.selected_index]
            self.current_state = AchievementUIState.CATEGORY
            self.category_selected_index = 0
        elif event.key == pygame.K_ESCAPE:
            return "back"
        return None
    
    def _handle_category_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input in category state."""
        achievements = self.achievement_manager.get_visible_achievements()
        category_achievements = [ach for ach in achievements if ach.category == self.selected_category]
        
        if event.key == pygame.K_UP:
            self.category_selected_index = (self.category_selected_index - 1) % len(category_achievements)
        elif event.key == pygame.K_DOWN:
            self.category_selected_index = (self.category_selected_index + 1) % len(category_achievements)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            if category_achievements:
                self.selected_achievement = category_achievements[self.category_selected_index]
                self.current_state = AchievementUIState.DETAIL
        elif event.key == pygame.K_ESCAPE:
            self.current_state = AchievementUIState.OVERVIEW
        return None
    
    def _handle_detail_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input in detail state."""
        if event.key == pygame.K_ESCAPE:
            self.current_state = AchievementUIState.CATEGORY
        return None
    
    def render(self, screen: pygame.Surface):
        """Render the achievement UI."""
        self._ensure_fonts_initialized()
        
        # If fonts still aren't available, show error message
        if not self._fonts_initialized:
            error_text = "Achievement system loading..."
            try:
                font = pygame.font.Font(None, 36)
                text_surface = font.render(error_text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                screen.blit(text_surface, text_rect)
            except:
                pass  # If even this fails, just show nothing
            return
        
        # Clear background
        screen.fill(self.bg_color)
        
        if self.current_state == AchievementUIState.OVERVIEW:
            self._render_overview(screen)
        elif self.current_state == AchievementUIState.CATEGORY:
            self._render_category(screen)
        elif self.current_state == AchievementUIState.DETAIL:
            self._render_detail(screen)
        
        # Render notifications
        self._render_notifications(screen)
    
    def _render_overview(self, screen: pygame.Surface):
        """Render the achievement overview with categories."""
        # Title
        title_text = self.title_font.render("ACHIEVEMENTS", True, self.text_color)
        title_rect = title_text.get_rect(centerx=self.screen_width // 2, y=50)
        screen.blit(title_text, title_rect)
        
        # Overall progress
        completion = self.achievement_manager.get_completion_percentage()
        progress_text = self.text_font.render(f"Overall Progress: {completion:.1f}%", True, self.text_color)
        progress_rect = progress_text.get_rect(centerx=self.screen_width // 2, y=90)
        screen.blit(progress_text, progress_rect)
        
        # Cores earned
        cores_text = self.text_font.render(f"Rapture Cores Earned: {self.achievement_manager.total_cores_earned}", 
                                         True, self.gold_color)
        cores_rect = cores_text.get_rect(centerx=self.screen_width // 2, y=120)
        screen.blit(cores_text, cores_rect)
        
        # Categories
        categories = list(AchievementCategory)
        start_y = 200
        category_height = 80
        
        for i, category in enumerate(categories):
            y = start_y + i * category_height
            
            # Category panel
            panel_rect = pygame.Rect(100, y, self.screen_width - 200, category_height - 10)
            color = self.selected_color if i == self.selected_index else self.panel_color
            pygame.draw.rect(screen, color, panel_rect, border_radius=10)
            
            # Category info
            display_info = self.category_display[category]
            unlocked, total = self.achievement_manager.get_category_completion(category)
            
            # Icon and name
            name_text = self.header_font.render(f"{display_info['icon']} {display_info['name']}", 
                                              True, self.text_color)
            name_rect = name_text.get_rect(x=panel_rect.x + 20, centery=panel_rect.centery - 10)
            screen.blit(name_text, name_rect)
            
            # Progress
            progress_text = self.text_font.render(f"{unlocked}/{total}", True, self.text_color)
            progress_rect = progress_text.get_rect(x=panel_rect.right - 100, centery=panel_rect.centery - 10)
            screen.blit(progress_text, progress_rect)
            
            # Progress bar
            bar_rect = pygame.Rect(panel_rect.x + 20, panel_rect.centery + 10, panel_rect.width - 140, 10)
            pygame.draw.rect(screen, self.progress_bg_color, bar_rect, border_radius=5)
            if total > 0:
                fill_width = int(bar_rect.width * (unlocked / total))
                fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_rect.height)
                pygame.draw.rect(screen, self.progress_fill_color, fill_rect, border_radius=5)
        
        # Instructions
        instructions = "↑↓ Navigate | ENTER Select | ESC Back"
        inst_text = self.small_font.render(instructions, True, self.text_color)
        inst_rect = inst_text.get_rect(centerx=self.screen_width // 2, y=self.screen_height - 30)
        screen.blit(inst_text, inst_rect)
    
    def _render_category(self, screen: pygame.Surface):
        """Render achievements in the selected category."""
        if not self.selected_category:
            return
        
        # Title
        display_info = self.category_display[self.selected_category]
        title_text = self.title_font.render(f"{display_info['icon']} {display_info['name'].upper()}", 
                                          True, self.text_color)
        title_rect = title_text.get_rect(centerx=self.screen_width // 2, y=50)
        screen.blit(title_text, title_rect)
        
        # Get achievements for this category
        achievements = self.achievement_manager.get_visible_achievements()
        category_achievements = [ach for ach in achievements if ach.category == self.selected_category]
        
        # Achievement list
        start_y = 120
        achievement_height = 100
        visible_count = (self.screen_height - 200) // achievement_height
        
        # Calculate scroll
        if self.category_selected_index >= visible_count:
            scroll_start = self.category_selected_index - visible_count + 1
        else:
            scroll_start = 0
        
        for i, achievement in enumerate(category_achievements[scroll_start:scroll_start + visible_count]):
            actual_index = scroll_start + i
            y = start_y + i * achievement_height
            
            # Achievement panel
            panel_rect = pygame.Rect(50, y, self.screen_width - 100, achievement_height - 10)
            is_selected = actual_index == self.category_selected_index
            color = self.selected_color if is_selected else self.panel_color
            pygame.draw.rect(screen, color, panel_rect, border_radius=10)
            
            # Trophy icon
            icon_color = self.unlocked_color if achievement.unlocked else self.locked_color
            trophy_text = self.header_font.render("🏆", True, icon_color)
            trophy_rect = trophy_text.get_rect(x=panel_rect.x + 20, centery=panel_rect.centery - 15)
            screen.blit(trophy_text, trophy_rect)
            
            # Achievement name
            name_color = self.unlocked_color if achievement.unlocked else self.text_color
            name_text = self.header_font.render(achievement.name, True, name_color)
            name_rect = name_text.get_rect(x=panel_rect.x + 70, y=panel_rect.y + 15)
            screen.blit(name_text, name_rect)
            
            # Achievement description
            desc_text = self.text_font.render(achievement.description, True, self.text_color)
            desc_rect = desc_text.get_rect(x=panel_rect.x + 70, y=panel_rect.y + 40)
            screen.blit(desc_text, desc_rect)
            
            # Progress
            if not achievement.unlocked:
                progress_text = f"{achievement.current_value}/{achievement.target_value}"
                if achievement.type.value == "counter":
                    progress_text += f" ({achievement.progress_percentage:.1f}%)"
                
                prog_text = self.small_font.render(progress_text, True, self.text_color)
                prog_rect = prog_text.get_rect(x=panel_rect.x + 70, y=panel_rect.y + 65)
                screen.blit(prog_text, prog_rect)
                
                # Progress bar for counter achievements
                if achievement.type.value == "counter":
                    bar_rect = pygame.Rect(prog_rect.right + 20, prog_rect.y + 5, 150, 10)
                    pygame.draw.rect(screen, self.progress_bg_color, bar_rect, border_radius=5)
                    
                    fill_width = int(bar_rect.width * (achievement.progress_percentage / 100))
                    fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_rect.height)
                    pygame.draw.rect(screen, self.progress_fill_color, fill_rect, border_radius=5)
            else:
                # Show unlock date and reward
                unlock_text = f"Unlocked: {achievement.unlock_date}"
                unlock_surface = self.small_font.render(unlock_text, True, self.unlocked_color)
                unlock_rect = unlock_surface.get_rect(x=panel_rect.x + 70, y=panel_rect.y + 65)
                screen.blit(unlock_surface, unlock_rect)
                
                # Reward
                if achievement.reward_cores > 0:
                    reward_text = f"+{achievement.reward_cores} Cores"
                    reward_surface = self.small_font.render(reward_text, True, self.gold_color)
                    reward_rect = reward_surface.get_rect(x=unlock_rect.right + 20, y=unlock_rect.y)
                    screen.blit(reward_surface, reward_rect)
        
        # Instructions
        instructions = "↑↓ Navigate | ENTER Details | ESC Back"
        inst_text = self.small_font.render(instructions, True, self.text_color)
        inst_rect = inst_text.get_rect(centerx=self.screen_width // 2, y=self.screen_height - 30)
        screen.blit(inst_text, inst_rect)
    
    def _render_detail(self, screen: pygame.Surface):
        """Render detailed view of selected achievement."""
        if not self.selected_achievement:
            return
        
        achievement = self.selected_achievement
        
        # Background panel
        panel_rect = pygame.Rect(100, 100, self.screen_width - 200, self.screen_height - 200)
        pygame.draw.rect(screen, self.panel_color, panel_rect, border_radius=15)
        
        # Trophy icon (large)
        icon_color = self.unlocked_color if achievement.unlocked else self.locked_color
        trophy_size = 72
        trophy_font = pygame.font.Font(None, trophy_size)
        trophy_text = trophy_font.render("🏆", True, icon_color)
        trophy_rect = trophy_text.get_rect(centerx=panel_rect.centerx, y=panel_rect.y + 30)
        screen.blit(trophy_text, trophy_rect)
        
        # Achievement name
        name_color = self.unlocked_color if achievement.unlocked else self.text_color
        name_text = self.title_font.render(achievement.name, True, name_color)
        name_rect = name_text.get_rect(centerx=panel_rect.centerx, y=trophy_rect.bottom + 20)
        screen.blit(name_text, name_rect)
        
        # Category
        display_info = self.category_display[achievement.category]
        category_text = self.text_font.render(f"Category: {display_info['name']}", True, self.text_color)
        category_rect = category_text.get_rect(centerx=panel_rect.centerx, y=name_rect.bottom + 20)
        screen.blit(category_text, category_rect)
        
        # Description
        desc_text = self.header_font.render(achievement.description, True, self.text_color)
        desc_rect = desc_text.get_rect(centerx=panel_rect.centerx, y=category_rect.bottom + 30)
        screen.blit(desc_text, desc_rect)
        
        # Progress or completion info
        if achievement.unlocked:
            # Completion info
            unlock_text = f"Unlocked on {achievement.unlock_date}"
            unlock_surface = self.text_font.render(unlock_text, True, self.unlocked_color)
            unlock_rect = unlock_surface.get_rect(centerx=panel_rect.centerx, y=desc_rect.bottom + 40)
            screen.blit(unlock_surface, unlock_rect)
            
            # Reward
            if achievement.reward_cores > 0:
                reward_text = f"Reward: {achievement.reward_cores} Rapture Cores"
                reward_surface = self.text_font.render(reward_text, True, self.gold_color)
                reward_rect = reward_surface.get_rect(centerx=panel_rect.centerx, y=unlock_rect.bottom + 20)
                screen.blit(reward_surface, reward_rect)
        else:
            # Progress info
            progress_text = f"Progress: {achievement.current_value}/{achievement.target_value}"
            if achievement.type.value == "counter":
                progress_text += f" ({achievement.progress_percentage:.1f}%)"
            
            prog_surface = self.text_font.render(progress_text, True, self.text_color)
            prog_rect = prog_surface.get_rect(centerx=panel_rect.centerx, y=desc_rect.bottom + 40)
            screen.blit(prog_surface, prog_rect)
            
            # Progress bar for counter achievements
            if achievement.type.value == "counter":
                bar_width = 300
                bar_height = 20
                bar_rect = pygame.Rect(panel_rect.centerx - bar_width // 2, prog_rect.bottom + 20, 
                                     bar_width, bar_height)
                pygame.draw.rect(screen, self.progress_bg_color, bar_rect, border_radius=10)
                
                fill_width = int(bar_width * (achievement.progress_percentage / 100))
                fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_height)
                pygame.draw.rect(screen, self.progress_fill_color, fill_rect, border_radius=10)
            
            # Reward preview
            if achievement.reward_cores > 0:
                reward_text = f"Reward: {achievement.reward_cores} Rapture Cores"
                reward_surface = self.text_font.render(reward_text, True, self.gold_color)
                y_pos = prog_rect.bottom + (50 if achievement.type.value == "counter" else 20)
                reward_rect = reward_surface.get_rect(centerx=panel_rect.centerx, y=y_pos)
                screen.blit(reward_surface, reward_rect)
        
        # Instructions
        instructions = "ESC Back"
        inst_text = self.small_font.render(instructions, True, self.text_color)
        inst_rect = inst_text.get_rect(centerx=panel_rect.centerx, y=panel_rect.bottom - 30)
        screen.blit(inst_text, inst_rect)
    
    def _render_notifications(self, screen: pygame.Surface):
        """Render achievement unlock notifications."""
        # Remove expired notifications
        self.notifications = [notif for notif in self.notifications if not notif.is_expired]
        
        # Render active notifications
        for i, notification in enumerate(self.notifications):
            y_offset = i * 120
            self._render_notification(screen, notification, y_offset)
    
    def _render_notification(self, screen: pygame.Surface, notification: AchievementNotification, y_offset: int):
        """Render a single achievement notification."""
        # Create notification surface
        notif_width = 400
        notif_height = 100
        notif_surface = pygame.Surface((notif_width, notif_height), pygame.SRCALPHA)
        
        # Background
        bg_rect = pygame.Rect(0, 0, notif_width, notif_height)
        pygame.draw.rect(notif_surface, (*self.panel_color, 200), bg_rect, border_radius=15)
        
        # Achievement unlocked text
        unlock_text = self.header_font.render("ACHIEVEMENT UNLOCKED!", True, self.gold_color)
        unlock_rect = unlock_text.get_rect(centerx=notif_width // 2, y=10)
        notif_surface.blit(unlock_text, unlock_rect)
        
        # Achievement name
        name_text = self.text_font.render(notification.achievement.name, True, self.unlocked_color)
        name_rect = name_text.get_rect(centerx=notif_width // 2, y=35)
        notif_surface.blit(name_text, name_rect)
        
        # Trophy icon
        trophy_text = self.text_font.render("🏆", True, self.gold_color)
        trophy_rect = trophy_text.get_rect(x=10, centery=notif_height // 2)
        notif_surface.blit(trophy_text, trophy_rect)
        
        # Cores reward
        if notification.achievement.reward_cores > 0:
            cores_text = self.small_font.render(f"+{notification.achievement.reward_cores} Cores", 
                                              True, self.gold_color)
            cores_rect = cores_text.get_rect(centerx=notif_width // 2, y=60)
            notif_surface.blit(cores_text, cores_rect)
        
        # Apply alpha and blit to screen
        notif_surface.set_alpha(notification.alpha)
        screen.blit(notif_surface, (self.screen_width - notif_width - 20, 20 + y_offset))
    
    def show_achievement_notification(self, achievement: Achievement):
        """Show a notification for a newly unlocked achievement."""
        notification = AchievementNotification(achievement)
        self.notifications.append(notification)
    
    def update(self):
        """Update achievement UI (for animations, etc.)."""
        # Update notifications (they handle their own timing)
        pass
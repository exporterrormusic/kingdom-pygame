"""
Achievement system for Kingdom-Pygame.
Tracks player accomplishments and unlocks rewards.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class AchievementCategory(Enum):
    """Categories for organizing achievements."""
    COMBAT = "combat"
    SURVIVAL = "survival"
    CHARACTER = "character"
    EXPLORATION = "exploration"
    COLLECTION = "collection"
    SPECIAL = "special"


class AchievementType(Enum):
    """Types of achievement conditions."""
    COUNTER = "counter"  # Reach a certain number
    MILESTONE = "milestone"  # Achieve something once
    PROGRESS = "progress"  # Percentage-based progress


@dataclass
class Achievement:
    """Represents a single achievement."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    type: AchievementType
    target_value: int
    current_value: int = 0
    unlocked: bool = False
    unlock_date: Optional[str] = None
    reward_cores: int = 0
    reward_description: str = ""
    icon: str = "trophy"  # Icon identifier
    hidden: bool = False  # Hidden until unlocked
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.target_value == 0:
            return 100.0 if self.unlocked else 0.0
        return min(100.0, (self.current_value / self.target_value) * 100.0)
    
    @property
    def is_completed(self) -> bool:
        """Check if achievement is completed."""
        return self.current_value >= self.target_value or self.unlocked


class AchievementManager:
    """Manages all achievements in the game."""
    
    def __init__(self, save_file: str = "saves/achievements.json"):
        self.save_file = save_file
        self.achievements: Dict[str, Achievement] = {}
        self.total_cores_earned = 0
        self.total_achievements_unlocked = 0
        
        # Ensure save directory exists
        os.makedirs(os.path.dirname(save_file), exist_ok=True)
        
        # Initialize achievement definitions
        self._initialize_achievements()
        
        # Load saved progress
        self.load_achievements()
    
    def _initialize_achievements(self):
        """Initialize all achievement definitions."""
        achievement_defs = [
            # COMBAT achievements
            {
                "id": "first_kill",
                "name": "First Blood",
                "description": "Defeat your first enemy",
                "category": AchievementCategory.COMBAT,
                "type": AchievementType.MILESTONE,
                "target_value": 1,
                "reward_cores": 5,
                "reward_description": "5 Rapture Cores"
            },
            {
                "id": "kill_100",
                "name": "Centurion",
                "description": "Defeat 100 enemies",
                "category": AchievementCategory.COMBAT,
                "type": AchievementType.COUNTER,
                "target_value": 100,
                "reward_cores": 25,
                "reward_description": "25 Rapture Cores"
            },
            {
                "id": "kill_1000",
                "name": "Legendary Warrior",
                "description": "Defeat 1000 enemies",
                "category": AchievementCategory.COMBAT,
                "type": AchievementType.COUNTER,
                "target_value": 1000,
                "reward_cores": 100,
                "reward_description": "100 Rapture Cores"
            },
            {
                "id": "kill_5000",
                "name": "Rapture's Bane",
                "description": "Defeat 5000 enemies",
                "category": AchievementCategory.COMBAT,
                "type": AchievementType.COUNTER,
                "target_value": 5000,
                "reward_cores": 500,
                "reward_description": "500 Rapture Cores",
                "hidden": True
            },
            
            # SURVIVAL achievements
            {
                "id": "wave_5",
                "name": "Rookie Survivor",
                "description": "Survive to Wave 5",
                "category": AchievementCategory.SURVIVAL,
                "type": AchievementType.MILESTONE,
                "target_value": 5,
                "reward_cores": 10,
                "reward_description": "10 Rapture Cores"
            },
            {
                "id": "wave_10",
                "name": "Veteran Survivor",
                "description": "Survive to Wave 10",
                "category": AchievementCategory.SURVIVAL,
                "type": AchievementType.MILESTONE,
                "target_value": 10,
                "reward_cores": 50,
                "reward_description": "50 Rapture Cores"
            },
            {
                "id": "wave_20",
                "name": "Elite Survivor",
                "description": "Survive to Wave 20",
                "category": AchievementCategory.SURVIVAL,
                "type": AchievementType.MILESTONE,
                "target_value": 20,
                "reward_cores": 150,
                "reward_description": "150 Rapture Cores"
            },
            {
                "id": "wave_50",
                "name": "Legendary Survivor",
                "description": "Survive to Wave 50",
                "category": AchievementCategory.SURVIVAL,
                "type": AchievementType.MILESTONE,
                "target_value": 50,
                "reward_cores": 1000,
                "reward_description": "1000 Rapture Cores",
                "hidden": True
            },
            
            # CHARACTER achievements
            {
                "id": "character_5",
                "name": "Squad Leader",
                "description": "Unlock 5 different characters",
                "category": AchievementCategory.CHARACTER,
                "type": AchievementType.COUNTER,
                "target_value": 5,
                "reward_cores": 50,
                "reward_description": "50 Rapture Cores"
            },
            {
                "id": "character_all",
                "name": "Commander",
                "description": "Unlock all characters",
                "category": AchievementCategory.CHARACTER,
                "type": AchievementType.COUNTER,
                "target_value": 11,  # Assuming 11 characters
                "reward_cores": 200,
                "reward_description": "200 Rapture Cores"
            },
            
            # COLLECTION achievements
            {
                "id": "cores_100",
                "name": "Core Collector",
                "description": "Collect 100 Rapture Cores",
                "category": AchievementCategory.COLLECTION,
                "type": AchievementType.COUNTER,
                "target_value": 100,
                "reward_cores": 10,
                "reward_description": "10 Bonus Rapture Cores"
            },
            {
                "id": "cores_1000",
                "name": "Core Hoarder",
                "description": "Collect 1000 Rapture Cores",
                "category": AchievementCategory.COLLECTION,
                "type": AchievementType.COUNTER,
                "target_value": 1000,
                "reward_cores": 100,
                "reward_description": "100 Bonus Rapture Cores"
            },
            
            # SPECIAL achievements
            {
                "id": "perfect_wave",
                "name": "Flawless Victory",
                "description": "Complete a wave without taking damage",
                "category": AchievementCategory.SPECIAL,
                "type": AchievementType.MILESTONE,
                "target_value": 1,
                "reward_cores": 75,
                "reward_description": "75 Rapture Cores"
            },
            {
                "id": "speedrun_wave_10",
                "name": "Speed Demon",
                "description": "Reach Wave 10 in under 10 minutes",
                "category": AchievementCategory.SPECIAL,
                "type": AchievementType.MILESTONE,
                "target_value": 1,
                "reward_cores": 100,
                "reward_description": "100 Rapture Cores",
                "hidden": True
            }
        ]
        
        # Create Achievement objects
        for ach_def in achievement_defs:
            achievement = Achievement(**ach_def)
            self.achievements[achievement.id] = achievement
    
    def load_achievements(self):
        """Load achievement progress from file."""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                
                # Load individual achievement progress
                for ach_id, ach_data in data.get('achievements', {}).items():
                    if ach_id in self.achievements:
                        ach = self.achievements[ach_id]
                        ach.current_value = ach_data.get('current_value', 0)
                        ach.unlocked = ach_data.get('unlocked', False)
                        ach.unlock_date = ach_data.get('unlock_date', None)
                
                # Load totals
                self.total_cores_earned = data.get('total_cores_earned', 0)
                self.total_achievements_unlocked = data.get('total_achievements_unlocked', 0)
                
        except Exception as e:
            print(f"Error loading achievements: {e}")
    
    def save_achievements(self):
        """Save achievement progress to file."""
        try:
            data = {
                'achievements': {},
                'total_cores_earned': self.total_cores_earned,
                'total_achievements_unlocked': self.total_achievements_unlocked
            }
            
            # Save individual achievement progress
            for ach_id, ach in self.achievements.items():
                if ach.current_value > 0 or ach.unlocked:
                    data['achievements'][ach_id] = {
                        'current_value': ach.current_value,
                        'unlocked': ach.unlocked,
                        'unlock_date': ach.unlock_date
                    }
            
            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving achievements: {e}")
    
    def update_achievement(self, achievement_id: str, value: int = 1) -> Optional[Achievement]:
        """Update an achievement's progress and return it if newly unlocked."""
        if achievement_id not in self.achievements:
            return None
        
        achievement = self.achievements[achievement_id]
        
        # Don't update if already unlocked
        if achievement.unlocked:
            return None
        
        # Update progress
        if achievement.type == AchievementType.COUNTER:
            achievement.current_value += value
        else:  # MILESTONE or PROGRESS
            achievement.current_value = max(achievement.current_value, value)
        
        # Check if unlocked
        if achievement.current_value >= achievement.target_value and not achievement.unlocked:
            achievement.unlocked = True
            achievement.unlock_date = self._get_current_date()
            self.total_achievements_unlocked += 1
            self.total_cores_earned += achievement.reward_cores
            self.save_achievements()
            return achievement  # Return newly unlocked achievement
        
        # Save progress
        self.save_achievements()
        return None
    
    def _get_current_date(self) -> str:
        """Get current date as string."""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def get_achievements_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """Get all achievements in a specific category."""
        return [ach for ach in self.achievements.values() if ach.category == category]
    
    def get_visible_achievements(self) -> List[Achievement]:
        """Get all achievements that should be visible (not hidden or unlocked hidden ones)."""
        return [ach for ach in self.achievements.values() if not ach.hidden or ach.unlocked]
    
    def get_completion_percentage(self) -> float:
        """Get overall achievement completion percentage."""
        total_achievements = len(self.achievements)
        if total_achievements == 0:
            return 0.0
        return (self.total_achievements_unlocked / total_achievements) * 100.0
    
    def get_category_completion(self, category: AchievementCategory) -> tuple:
        """Get completion stats for a category (unlocked, total)."""
        category_achievements = self.get_achievements_by_category(category)
        unlocked = sum(1 for ach in category_achievements if ach.unlocked)
        total = len(category_achievements)
        return unlocked, total
    
    # Convenience methods for common achievement updates
    def on_enemy_killed(self, count: int = 1):
        """Called when enemies are killed."""
        return [
            self.update_achievement("first_kill", count),
            self.update_achievement("kill_100", count),
            self.update_achievement("kill_1000", count),
            self.update_achievement("kill_5000", count)
        ]
    
    def on_wave_completed(self, wave_number: int):
        """Called when a wave is completed."""
        return [
            self.update_achievement("wave_5", wave_number),
            self.update_achievement("wave_10", wave_number),
            self.update_achievement("wave_20", wave_number),
            self.update_achievement("wave_50", wave_number)
        ]
    
    def on_cores_collected(self, count: int):
        """Called when rapture cores are collected."""
        return [
            self.update_achievement("cores_100", count),
            self.update_achievement("cores_1000", count)
        ]
    
    def on_character_unlocked(self):
        """Called when a character is unlocked."""
        # Count unlocked characters from save data
        from src.utils.save_manager import GameSaveManager
        save_manager = GameSaveManager()
        unlocked_count = len([char for char, data in save_manager.player_data.get('characters', {}).items() 
                             if data.get('unlocked', False)])
        
        return [
            self.update_achievement("character_5", unlocked_count),
            self.update_achievement("character_all", unlocked_count)
        ]
    
    def on_perfect_wave(self):
        """Called when a wave is completed without taking damage."""
        return [self.update_achievement("perfect_wave")]
    
    def on_speed_run(self, wave_number: int, time_minutes: float):
        """Called to check speed run achievements."""
        if wave_number >= 10 and time_minutes < 10:
            return [self.update_achievement("speedrun_wave_10")]
        return []
"""
Score Management System for Kingdom-Pygame
Handles match scores, rapture core currency, and persistent character-specific leaderboards.
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SurvivalRecord:
    """Represents a single survival run record."""
    score: int
    waves_survived: int
    enemies_killed: int
    survival_time_seconds: int
    date: str
    character_name: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'score': self.score,
            'waves_survived': self.waves_survived,
            'enemies_killed': self.enemies_killed,
            'survival_time_seconds': self.survival_time_seconds,
            'date': self.date,
            'character_name': self.character_name
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SurvivalRecord':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            score=data['score'],
            waves_survived=data['waves_survived'],
            enemies_killed=data['enemies_killed'],
            survival_time_seconds=data['survival_time_seconds'],
            date=data['date'],
            character_name=data['character_name']
        )

class ScoreManager:
    """Manages scoring, currency, and persistent leaderboards."""
    
    def __init__(self, save_file: str = "saves/scores_and_leaderboard.json"):
        """Initialize the score manager."""
        self.save_file = save_file
        self.current_match_score = 0
        self.current_match_kills = 0
        self.current_match_waves = 0
        self.current_match_start_time = 0.0
        
        # Persistent data
        self.player_rapture_cores = 0  # Currency that persists between games
        self.character_leaderboards: Dict[str, List[SurvivalRecord]] = {}  # Character -> top records
        self.max_records_per_character = 10  # Top 10 records per character
        
        # Load existing data
        self.load_data()
    
    def start_new_match(self, game_time: float):
        """Start tracking a new survival match."""
        self.current_match_score = 0
        self.current_match_kills = 0
        self.current_match_waves = 1
        self.current_match_start_time = game_time
        print(f"Started new survival match. Player has {self.player_rapture_cores} rapture cores")
    
    def add_kill_score(self, points_per_kill: int = 10):
        """Add score for killing an enemy."""
        self.current_match_score += points_per_kill
        self.current_match_kills += 1
    
    def update_wave(self, current_wave: int):
        """Update the current wave number."""
        if current_wave > self.current_match_waves:
            self.current_match_waves = current_wave
            print(f"Wave {current_wave} reached! Score: {self.current_match_score}")
    
    def add_rapture_cores(self, amount: int):
        """Add rapture cores to player's persistent currency."""
        self.player_rapture_cores += amount
        print(f"Collected {amount} rapture cores. Total: {self.player_rapture_cores}")
    
    def spend_rapture_cores(self, amount: int) -> bool:
        """Spend rapture cores if player has enough. Returns True if successful."""
        if self.player_rapture_cores >= amount:
            self.player_rapture_cores -= amount
            print(f"Spent {amount} rapture cores. Remaining: {self.player_rapture_cores}")
            return True
        else:
            print(f"Cannot spend {amount} rapture cores. Only have {self.player_rapture_cores}")
            return False
    
    def end_match(self, character_name: str, game_time: float) -> SurvivalRecord:
        """End the current match and record the result."""
        survival_time = int(game_time - self.current_match_start_time)
        
        # Create survival record
        record = SurvivalRecord(
            score=self.current_match_score,
            waves_survived=self.current_match_waves,
            enemies_killed=self.current_match_kills,
            survival_time_seconds=survival_time,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            character_name=character_name
        )
        
        # Add to character leaderboard
        self.add_to_leaderboard(character_name, record)
        
        # Save data
        self.save_data()
        
        print(f"Match ended! Score: {record.score}, Waves: {record.waves_survived}, Time: {survival_time}s")
        return record
    
    def add_to_leaderboard(self, character_name: str, record: SurvivalRecord):
        """Add a record to character's leaderboard."""
        if character_name not in self.character_leaderboards:
            self.character_leaderboards[character_name] = []
        
        # Add the record
        self.character_leaderboards[character_name].append(record)
        
        # Sort by score (descending) then by waves survived (descending)
        self.character_leaderboards[character_name].sort(
            key=lambda r: (r.score, r.waves_survived, r.enemies_killed), 
            reverse=True
        )
        
        # Keep only top records
        self.character_leaderboards[character_name] = \
            self.character_leaderboards[character_name][:self.max_records_per_character]
    
    def get_character_best_score(self, character_name: str) -> Optional[int]:
        """Get character's best score."""
        if character_name in self.character_leaderboards and self.character_leaderboards[character_name]:
            return self.character_leaderboards[character_name][0].score
        return None
    
    def get_character_best_waves(self, character_name: str) -> Optional[int]:
        """Get character's best wave survival."""
        if character_name in self.character_leaderboards and self.character_leaderboards[character_name]:
            # Sort by waves survived to get the best wave record
            wave_sorted = sorted(self.character_leaderboards[character_name], 
                               key=lambda r: r.waves_survived, reverse=True)
            return wave_sorted[0].waves_survived
        return None
    
    def get_character_leaderboard(self, character_name: str) -> List[SurvivalRecord]:
        """Get full leaderboard for a character."""
        return self.character_leaderboards.get(character_name, [])
    
    def get_all_character_stats(self) -> Dict[str, Dict[str, int]]:
        """Get summary stats for all characters."""
        stats = {}
        for char_name, records in self.character_leaderboards.items():
            if records:
                stats[char_name] = {
                    'best_score': max(r.score for r in records),
                    'best_waves': max(r.waves_survived for r in records),
                    'total_runs': len(records),
                    'total_kills': sum(r.enemies_killed for r in records)
                }
        return stats
    
    def get_overall_leaderboard(self, limit: int = 20) -> List[SurvivalRecord]:
        """Get overall leaderboard across all characters."""
        all_records = []
        for records in self.character_leaderboards.values():
            all_records.extend(records)
        
        # Sort by score, then by waves, then by kills
        all_records.sort(
            key=lambda r: (r.score, r.waves_survived, r.enemies_killed), 
            reverse=True
        )
        
        return all_records[:limit]
    
    def get_current_match_stats(self) -> Dict[str, int]:
        """Get current match statistics."""
        return {
            'score': self.current_match_score,
            'kills': self.current_match_kills,
            'waves': self.current_match_waves
        }
    
    def load_data(self):
        """Load persistent data from file."""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                
                # Load rapture cores
                self.player_rapture_cores = data.get('player_rapture_cores', 0)
                
                # Load character leaderboards
                leaderboards_data = data.get('character_leaderboards', {})
                self.character_leaderboards = {}
                
                for char_name, records_data in leaderboards_data.items():
                    self.character_leaderboards[char_name] = [
                        SurvivalRecord.from_dict(record_data) 
                        for record_data in records_data
                    ]
                
                print(f"Loaded player data: {self.player_rapture_cores} rapture cores, "
                      f"{len(self.character_leaderboards)} character records")
            else:
                print("No existing save data found, starting fresh")
                
        except Exception as e:
            print(f"Error loading score data: {e}")
            # Reset to defaults on error
            self.player_rapture_cores = 0
            self.character_leaderboards = {}
    
    def save_data(self):
        """Save persistent data to file."""
        try:
            # Ensure save directory exists
            os.makedirs(os.path.dirname(self.save_file), exist_ok=True)
            
            # Prepare data for JSON
            leaderboards_data = {}
            for char_name, records in self.character_leaderboards.items():
                leaderboards_data[char_name] = [record.to_dict() for record in records]
            
            data = {
                'player_rapture_cores': self.player_rapture_cores,
                'character_leaderboards': leaderboards_data,
                'last_saved': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"Saved player data: {self.player_rapture_cores} rapture cores")
            
        except Exception as e:
            print(f"Error saving score data: {e}")
    
    def reset_character_data(self, character_name: str):
        """Reset all data for a specific character (for testing/debugging)."""
        if character_name in self.character_leaderboards:
            del self.character_leaderboards[character_name]
            self.save_data()
            print(f"Reset all data for character: {character_name}")
    
    def reset_all_data(self):
        """Reset all persistent data (for testing/debugging)."""
        self.player_rapture_cores = 0
        self.character_leaderboards = {}
        self.save_data()
        print("Reset all player data")
        
    def get_performance_rating(self, waves_survived: int) -> Tuple[str, tuple]:
        """Get performance rating and color based on waves survived."""
        if waves_survived >= 15:
            return "LEGENDARY SURVIVOR!", (255, 215, 0)  # Gold
        elif waves_survived >= 12:
            return "Master Warrior", (255, 100, 255)  # Purple
        elif waves_survived >= 10:
            return "Elite Fighter", (255, 150, 50)  # Orange
        elif waves_survived >= 7:
            return "Skilled Survivor", (100, 255, 100)  # Green
        elif waves_survived >= 5:
            return "Decent Fighter", (100, 200, 255)  # Blue
        elif waves_survived >= 3:
            return "Novice Survivor", (255, 255, 100)  # Yellow
        else:
            return "Keep Training", (255, 200, 200)  # Light red
"""
Multiplayer Game State Synchronizer for Kingdom-Pygame.
Handles synchronization of players, bullets, enemies, and effects across clients.
"""

import time
import pygame as pg
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, replace
from .network_manager import NetworkManager, MessageType, NetworkMessage


@dataclass
class PlayerState:
    """Player state data for synchronization."""
    player_id: str
    position: tuple  # (x, y)
    angle: float
    velocity: tuple  # (x, y)
    health: int
    max_health: int
    character_id: str
    weapon_type: str
    is_dashing: bool
    is_alive: bool
    player_name: str = "Player"
    animation_state: str = "idle"
    ammo: int = 0
    burst_gauge: float = 0.0


@dataclass 
class BulletState:
    """Bullet state data for synchronization."""
    bullet_id: str
    position: tuple  # (x, y)
    velocity: tuple  # (x, y)
    damage: int
    owner_id: str
    weapon_type: str
    special_attack: bool = False
    lifetime_remaining: float = 1.0
    creation_time: float = 0.0
    # Visual effect properties
    shape: str = "standard"
    size_multiplier: float = 1.0
    color: tuple = (255, 255, 255)  # RGB color tuple
    penetration: int = 1
    bounce_enabled: bool = False
    max_bounces: int = 0
    bounce_range: Optional[float] = None
    enemy_targeting: bool = False
    trail_enabled: bool = False
    trail_duration: float = 0.0
    range_limit: Optional[float] = None


@dataclass
class EnemyState:
    """Enemy state data for synchronization."""
    enemy_id: str
    position: tuple  # (x, y)
    health: int
    max_health: int
    enemy_type: str
    is_alive: bool
    target_player_id: Optional[str] = None


@dataclass
class EffectState:
    """Effect state data for synchronization."""
    effect_id: str
    effect_type: str  # "explosion", "muzzle_flash", "dash", etc.
    position: tuple  # (x, y)
    data: Dict[str, Any]  # Effect-specific parameters
    duration_remaining: float


class GameStateSynchronizer:
    """Synchronizes game state across multiplayer clients."""
    
    def __init__(self, network_manager: NetworkManager, is_host: bool = False):
        self.network_manager = network_manager
        self.is_host = is_host
        
        # Game state storage
        self.players = {}  # player_id -> PlayerState
        self.bullets = {}  # bullet_id -> BulletState
        self.enemies = {}  # enemy_id -> EnemyState (host authoritative)
        self.effects = {}  # effect_id -> EffectState
        
        # Local references
        self.local_player_id = None
        self.local_player = None
        self.bullet_manager = None
        self.enemy_manager = None
        self.effects_manager = None
        
        # Synchronization timing
        self.last_update_time = 0.0
        self.update_interval = 1/60.0  # 60 FPS sync rate
        
        # Message throttling to prevent network flooding
        self.last_muzzle_flash_time = 0.0
        self.last_explosion_time = 0.0
        self.last_bullet_hit_time = 0.0
        self.muzzle_flash_throttle = 0.05  # Max 20 muzzle flashes per second
        self.explosion_throttle = 0.1     # Max 10 explosions per second  
        self.bullet_hit_throttle = 0.02   # Max 50 bullet hits per second
        
        # Network interpolation
        self.player_interpolation = {}  # player_id -> interpolation data
        self.interpolation_speed = 10.0  # How fast to interpolate
        
        # Bullet tracking
        self.next_bullet_id = 1
        
        self._setup_message_handlers()
    
    def _setup_message_handlers(self):
        """Set up network message handlers."""
        # Core multiplayer handlers
        self.network_manager.register_message_handler(
            MessageType.PLAYER_UPDATE, self._handle_player_update
        )
        self.network_manager.register_message_handler(
            MessageType.BULLET_FIRE, self._handle_bullet_fire
        )
        self.network_manager.register_message_handler(
            MessageType.PLAYER_DAMAGE, self._handle_player_damage
        )
        self.network_manager.register_message_handler(
            MessageType.EXPLOSION, self._handle_explosion
        )
        self.network_manager.register_message_handler(
            MessageType.MUZZLE_FLASH, self._handle_muzzle_flash
        )
        self.network_manager.register_message_handler(
            MessageType.DASH_EFFECT, self._handle_dash_effect
        )
        self.network_manager.register_message_handler(
            MessageType.BULLET_HIT, self._handle_bullet_hit
        )
        self.network_manager.register_message_handler(
            MessageType.ENEMY_DAMAGE, self._handle_enemy_damage
        )
        self.network_manager.register_message_handler(
            MessageType.WAVE_UPDATE, self._handle_wave_update
        )
        self.network_manager.register_message_handler(
            MessageType.SCORE_UPDATE, self._handle_score_update
        )
        self.network_manager.register_message_handler(
            MessageType.WORLD_EVENT, self._handle_world_event
        )
        
        # Register enemy bullet handler
        self.network_manager.register_message_handler(
            MessageType.ENEMY_BULLET_FIRE, self._handle_enemy_bullet_fire
        )
        
        if not self.is_host:
            # Client-only handlers
            self.network_manager.register_message_handler(
                MessageType.ENEMY_SPAWN, self._handle_enemy_spawn
            )
            self.network_manager.register_message_handler(
                MessageType.ENEMY_UPDATE, self._handle_enemy_update
            )
            self.network_manager.register_message_handler(
                MessageType.ENEMY_DEATH, self._handle_enemy_death
            )
    
    def set_local_player_id(self, player_id: str):
        """Set the local player ID."""
        self.local_player_id = player_id
    
    def set_game_references(self, player, bullet_manager, enemy_manager, effects_manager):
        """Set references to local game objects."""
        self.local_player = player
        self.bullet_manager = bullet_manager
        self.enemy_manager = enemy_manager
        self.effects_manager = effects_manager
    
    def update(self, dt: float):
        """Update synchronization state."""
        current_time = time.time()
        
        # Process incoming network messages
        self.network_manager.process_messages()
        
        if current_time - self.last_update_time >= self.update_interval:
            self._send_player_update()
            self.last_update_time = current_time
        
        # Update player position interpolation
        self._update_player_interpolation(dt)
        
        # Clean up old network bullets periodically
        if hasattr(self, '_last_cleanup_time'):
            if current_time - self._last_cleanup_time > 2.0:  # Clean up every 2 seconds
                self.cleanup_old_bullets()
                self._last_cleanup_time = current_time
        else:
            self._last_cleanup_time = current_time
    
    def _update_player_interpolation(self, dt: float):
        """Smooth player position interpolation."""
        for player_id, interpolation_data in self.player_interpolation.items():
            if player_id in self.players:
                current = interpolation_data["current"]
                target = interpolation_data["target"]
                
                # Interpolate towards target
                current_vec = pg.Vector2(current)
                target_vec = pg.Vector2(target)
                
                diff = target_vec - current_vec
                if diff.length() > 1.0:  # Only interpolate if significant distance
                    move_amount = min(diff.length(), self.interpolation_speed * diff.length() * dt)
                    if diff.length() > 0:
                        direction = diff.normalize()
                        new_pos = current_vec + (direction * move_amount)
                        interpolation_data["current"] = (new_pos.x, new_pos.y)
                        
                        # Update player state position with interpolated value
                        self.players[player_id] = replace(
                            self.players[player_id],
                            position=interpolation_data["current"]
                        )
    
    def _send_player_update(self):
        """Send local player state to other clients."""
        if not self.local_player or not self.local_player_id:
            print(f"[GAME_SYNC] Cannot send player update - local_player: {self.local_player is not None}, local_player_id: {self.local_player_id}")
            return
        
        # Get character ID from local player
        character_id = getattr(self.local_player, 'character_id', 'Cecil')
        if not character_id:
            character_id = 'Cecil'  # Default fallback
        
        # Rate-limited debug for character ID (only on first few sends)
        player_state = PlayerState(
            player_id=self.local_player_id,
            position=(self.local_player.pos.x, self.local_player.pos.y),
            angle=self.local_player.angle,
            velocity=(self.local_player.velocity.x, self.local_player.velocity.y),
            health=self.local_player.health,
            max_health=self.local_player.max_health,
            character_id=character_id,
            weapon_type=getattr(self.local_player, 'weapon_type', 'Assault Rifle'),
            is_dashing=getattr(self.local_player, 'is_dashing', False),
            is_alive=self.local_player.is_alive(),
            ammo=getattr(self.local_player, 'current_ammo', 0),
            burst_gauge=getattr(self.local_player, 'burst_gauge', 0.0)
        )
        
        # Debug velocity being sent (rate limited)
        if not hasattr(self, '_velocity_send_debug'):
            self._velocity_send_debug = 0
        self.network_manager.send_message(
            MessageType.PLAYER_UPDATE,
            asdict(player_state)
        )
    
    def on_bullet_fired(self, bullet, owner_player_id: str):
        """Called when local player fires a bullet."""
        bullet_id = f"{owner_player_id}_{self.next_bullet_id}"
        self.next_bullet_id += 1
        
        # Debug logging for special attacks only to reduce spam
        special_attack = getattr(bullet, 'special_attack', False)
        weapon_type = bullet.weapon_type
        if special_attack:
            print(f"[BULLET_SYNC] Sending special attack: {weapon_type}")
        # Removed normal bullet logging to reduce spam
        
        bullet_state = BulletState(
            bullet_id=bullet_id,
            position=(bullet.pos.x, bullet.pos.y),
            velocity=(bullet.velocity.x, bullet.velocity.y),
            damage=bullet.damage,
            owner_id=owner_player_id,
            weapon_type=bullet.weapon_type,
            special_attack=getattr(bullet, 'special_attack', False),
            lifetime_remaining=getattr(bullet, 'lifetime_remaining', 1.0),
            creation_time=time.time(),  # Set creation time to current time
            # Capture all visual effect properties
            shape=getattr(bullet, 'shape', 'standard'),
            size_multiplier=getattr(bullet, 'size_multiplier', 1.0),
            color=getattr(bullet, 'color', (255, 255, 255)),
            penetration=getattr(bullet, 'penetration', 1),
            bounce_enabled=getattr(bullet, 'bounce_enabled', False),
            max_bounces=getattr(bullet, 'max_bounces', 0),
            bounce_range=getattr(bullet, 'bounce_range', None),
            enemy_targeting=getattr(bullet, 'enemy_targeting', False),
            trail_enabled=getattr(bullet, 'trail_enabled', False),
            trail_duration=getattr(bullet, 'trail_duration', 0.0),
            range_limit=getattr(bullet, 'range_limit', None)
        )
        
        self.network_manager.send_message(
            MessageType.BULLET_FIRE,
            asdict(bullet_state)
        )
    
    def on_player_damaged(self, player_id: str, damage: int, attacker_id: str):
        """Called when a player takes damage."""
        if self.is_host:
            self.network_manager.send_message(
                MessageType.PLAYER_DAMAGE,
                {
                    "player_id": player_id,
                    "damage": damage,
                    "attacker_id": attacker_id
                }
            )
    
    def on_explosion(self, x: float, y: float, radius: float, damage: float):
        """Called when an explosion occurs."""
        current_time = time.time()
        
        # Throttle explosion messages to prevent network flooding
        if current_time - self.last_explosion_time < self.explosion_throttle:
            return  # Skip this explosion to reduce network traffic
        
        self.last_explosion_time = current_time
        # Send explosion effect from any player
        self.network_manager.send_message(
            MessageType.EXPLOSION,
            {
                "position": (x, y),
                "radius": radius,
                "damage": damage,
                "timestamp": time.time()
            }
        )
    
    def on_muzzle_flash(self, x: float, y: float, angle: float, weapon_type: str):
        """Called when a muzzle flash should be shown."""
        current_time = time.time()
        
        # Throttle muzzle flash messages to prevent network flooding
        if current_time - self.last_muzzle_flash_time < self.muzzle_flash_throttle:
            return  # Skip this muzzle flash to reduce network traffic
        
        self.last_muzzle_flash_time = current_time
        self.network_manager.send_message(
            MessageType.MUZZLE_FLASH,
            {
                "position": (x, y),
                "angle": angle,
                "weapon_type": weapon_type,
                "timestamp": time.time()
            }
        )
    
    def on_bullet_hit(self, x: float, y: float):
        """Called when a bullet hits an enemy."""
        current_time = time.time()
        
        # Throttle bullet hit messages to prevent network flooding
        if current_time - self.last_bullet_hit_time < self.bullet_hit_throttle:
            return  # Skip this bullet hit to reduce network traffic
        
        self.last_bullet_hit_time = current_time
        self.network_manager.send_message(
            MessageType.BULLET_HIT,
            {
                "position": (x, y),
                "timestamp": time.time()
            }
        )

    def send_enemy_update(self, enemy):
        """Send enemy position update to clients (host only)."""
        if not self.is_host:
            return
        
        self.network_manager.send_message(
            MessageType.ENEMY_UPDATE,
            {
                "enemy_id": enemy.enemy_id,
                "position": (enemy.pos.x, enemy.pos.y),
                "velocity": (enemy.velocity.x, enemy.velocity.y),
                "health": enemy.health,
                "max_health": enemy.max_health,
                "timestamp": time.time()
            }
        )
    
    def on_dash_effect(self, player_id: str, start_pos: tuple, end_pos: tuple):
        """Called when a dash effect should be shown."""
        self.network_manager.send_message(
            MessageType.DASH_EFFECT,
            {
                "player_id": player_id,
                "start_position": start_pos,
                "end_position": end_pos,
                "timestamp": time.time()
            }
        )
    
    def on_enemy_damaged(self, enemy_id: str, damage: int, attacker_id: str):
        """Called when an enemy takes damage."""
        if self.is_host:
            self.network_manager.send_message(
                MessageType.ENEMY_DAMAGE,
                {
                    "enemy_id": enemy_id,
                    "damage": damage,
                    "attacker_id": attacker_id
                }
            )
    
    def on_wave_update(self, wave_number: int, enemies_remaining: int, wave_timer: float):
        """Called when wave information updates (host only)."""
        if self.is_host:
            self.network_manager.send_message(
                MessageType.WAVE_UPDATE,
                {
                    "wave_number": wave_number,
                    "enemies_remaining": enemies_remaining,
                    "wave_timer": wave_timer
                }
            )
    
    def on_score_update(self, player_id: str, score: int, cores: int, kills: int):
        """Called when player score updates."""
        if self.is_host:
            self.network_manager.send_message(
                MessageType.SCORE_UPDATE,
                {
                    "player_id": player_id,
                    "score": score,
                    "cores": cores,
                    "kills": kills
                }
            )
    
    def on_world_event(self, event_type: str, event_data: dict):
        """Called when a world event occurs (host only)."""
        if self.is_host:
            self.network_manager.send_message(
                MessageType.WORLD_EVENT,
                {
                    "event_type": event_type,
                    "event_data": event_data
                }
            )
    
    # Message Handlers
    def _handle_player_update(self, message: NetworkMessage):
        """Handle incoming player update."""
        import time  # Import time at the beginning
        data = message.data
        player_id = data['player_id']
        character_id = data.get('character_id', 'Cecil')
        position = data['position']
        
        # Temporarily increase debug for movement troubleshooting
        # Only log new player connections or every 3 seconds (increased frequency)
        if player_id not in self.players or (hasattr(self, '_last_player_log') and time.time() - self._last_player_log > 3):
            self._last_player_log = time.time()
            print(f"[GAME_SYNC] Player update from {player_id} at pos=({position[0]:.1f}, {position[1]:.1f}), character={character_id}")
        
        # Don't update our own player from network
        if player_id == self.local_player_id:
            return
        
        # Create or update player state
        player_state = PlayerState(**data)
        
        # Initialize interpolation data for new players
        if player_id not in self.player_interpolation:
            self.player_interpolation[player_id] = {
                "current": player_state.position,
                "target": player_state.position
            }
        else:
            # Update target position for interpolation
            self.player_interpolation[player_id]["target"] = player_state.position
        
        # Store the raw network state (position will be updated by interpolation)
        self.players[player_id] = player_state
        
        # Debug: Log current network players
        if len(self.players) > 0:
            # Reduced debug spam - only log network player updates occasionally
            if hasattr(self, '_last_network_log') and time.time() - self._last_network_log > 15:
                self._last_network_log = time.time()
                print(f"[GAME_SYNC] Current network players: {list(self.players.keys())}")
    
    def _handle_bullet_fire(self, message: NetworkMessage):
        """Handle incoming bullet fire."""
        data = message.data
        bullet_id = data['bullet_id']
        owner_id = data['owner_id']
        
        # Don't create bullets from ourselves
        if owner_id == self.local_player_id:
            return
        
        # Debug logging for received bullets - reduced spam
        special_attack = data.get('special_attack', False)
        weapon_type = data.get('weapon_type', 'unknown')
        if special_attack:
            print(f"[BULLET_SYNC] Received special attack: {weapon_type}")
        # Removed normal bullet reception logging to reduce spam
        
        bullet_state = BulletState(**data)
        # Set creation time for cleanup
        bullet_state.creation_time = time.time()
        self.bullets[bullet_id] = bullet_state
        
        # Create visual bullet in local bullet manager
        if self.bullet_manager:
            self.bullet_manager.create_network_bullet(
                bullet_state.position[0],
                bullet_state.position[1],
                bullet_state.velocity[0],
                bullet_state.velocity[1],
                bullet_state.damage,
                bullet_state.weapon_type,
                bullet_state.special_attack,
                bullet_state.owner_id,
                # Pass all visual effect properties
                shape=bullet_state.shape,
                size_multiplier=bullet_state.size_multiplier,
                color=bullet_state.color,
                penetration=bullet_state.penetration,
                bounce_enabled=bullet_state.bounce_enabled,
                max_bounces=bullet_state.max_bounces,
                bounce_range=bullet_state.bounce_range,
                enemy_targeting=bullet_state.enemy_targeting,
                trail_enabled=bullet_state.trail_enabled,
                trail_duration=bullet_state.trail_duration,
                range_limit=bullet_state.range_limit
            )
    
    def _handle_player_damage(self, message: NetworkMessage):
        """Handle incoming player damage."""
        data = message.data
        player_id = data['player_id']
        damage = data['damage']
        
        if player_id == self.local_player_id and self.local_player:
            self.local_player.take_damage(damage)
    
    def _handle_explosion(self, message: NetworkMessage):
        """Handle incoming explosion."""
        data = message.data
        position = data['position']
        radius = data['radius']
        
        if self.effects_manager:
            self.effects_manager.create_explosion(position[0], position[1], radius)
    
    def _handle_muzzle_flash(self, message: NetworkMessage):
        """Handle incoming muzzle flash."""
        data = message.data
        position = data['position']
        angle = data['angle']
        weapon_type = data['weapon_type']
        
        if self.effects_manager and hasattr(self.effects_manager, 'weapon_effects'):
            self.effects_manager.weapon_effects.create_muzzle_flash(position[0], position[1], angle, weapon_type)
    
    def _handle_dash_effect(self, message: NetworkMessage):
        """Handle incoming dash effect."""
        data = message.data
        player_id = data['player_id']
        start_pos = data['start_position']
        end_pos = data['end_position']
        
        if self.effects_manager and player_id != self.local_player_id:
            self.effects_manager.create_dash_trail(start_pos, end_pos)
    
    def _handle_bullet_hit(self, message: NetworkMessage):
        """Handle incoming bullet hit effect."""
        data = message.data
        position = data['position']
        
        if self.effects_manager:
            self.effects_manager.create_bullet_impact(position[0], position[1])
    
    def _handle_enemy_damage(self, message: NetworkMessage):
        """Handle incoming enemy damage from clients."""
        # Process enemy damage (host authoritative)
        # Reduced debug logging frequency
        
        if self.is_host and self.enemy_manager:
            data = message.data
            enemy_id = data.get('enemy_id', 'unknown')
            damage = data.get('damage', 0)
            player_id = data.get('player_id', 'unknown')
            position = data.get('position', (0, 0))
            
            # Log damage events only occasionally to reduce spam
            if hasattr(self, '_damage_log_count'):
                self._damage_log_count += 1
            else:
                self._damage_log_count = 1
            
            if self._damage_log_count % 10 == 1:  # Log every 10th damage event
                print(f"[ENEMY_DAMAGE_HOST] Processing damage {damage} to enemy {enemy_id} from client {player_id}")
            
            # Find the enemy and apply damage
            enemies_found = 0
            for enemy in self.enemy_manager.get_enemies():
                enemies_found += 1
                if enemy.enemy_id == enemy_id and enemy.is_alive():
                    # Only log damage application occasionally
                    if self._damage_log_count % 10 == 1:
                        print(f"[ENEMY_DAMAGE_HOST] Applying {damage} damage to enemy {enemy_id} (health: {enemy.health})")
                    enemy.take_damage(damage)
                    
                    # Send enemy state update to clients after damage is applied
                    if enemy.is_alive():
                        self.network_manager.send_message(
                            MessageType.ENEMY_UPDATE,
                            {
                                "enemy_id": enemy.enemy_id,
                                "position": (enemy.pos.x, enemy.pos.y),
                                "velocity": (enemy.velocity.x, enemy.velocity.y),
                                "health": enemy.health,
                                "max_health": enemy.max_health,
                                "timestamp": time.time()
                            }
                        )
                    
                    # If enemy died, handle it by calling remove_enemy which will send ENEMY_DEATH message
                    if not enemy.is_alive():
                        # Log enemy kills (important event) 
                        print(f"[ENEMY_DAMAGE_HOST] Enemy {enemy_id} killed by client {player_id}")
                        # Use remove_enemy to properly handle death, send network messages, and drop cores
                        self.enemy_manager.remove_enemy(enemy)
                        return
            
            # Reduce debug spam for missing enemies - only log occasionally
            if hasattr(self, '_enemy_not_found_count'):
                self._enemy_not_found_count += 1 
            else:
                self._enemy_not_found_count = 1
                
            if self._enemy_not_found_count % 5 == 1:  # Log every 5th miss
                print(f"[ENEMY_DAMAGE_HOST] Enemy {enemy_id} not found among {enemies_found} enemies")
        else:
            # Remove client-side damage message spam
            pass  # Clients should ignore damage messages
            pass
    
    def _handle_wave_update(self, message: NetworkMessage):
        """Handle wave information updates."""
        if not self.is_host:
            data = message.data
            # Store wave information for UI display
            if not hasattr(self, 'network_wave_info'):
                self.network_wave_info = {}
            
            self.network_wave_info.update(data)
    
    def _handle_score_update(self, message: NetworkMessage):
        """Handle score updates from other players."""
        data = message.data
        player_id = data['player_id']
        
        # Store network score information
        if not hasattr(self, 'network_scores'):
            self.network_scores = {}
        
        self.network_scores[player_id] = {
            'score': data['score'],
            'cores': data['cores'], 
            'kills': data['kills']
        }
    
    def _handle_world_event(self, message: NetworkMessage):
        """Handle world events from host."""
        if not self.is_host:
            data = message.data
            event_type = data['event_type']
            event_data = data['event_data']
            
            # Handle different world events
            if event_type == "core_drop" and hasattr(self, 'world_manager'):
                # Add core to world
                core_pos = event_data.get('position', (0, 0))
                core_value = event_data.get('value', 1)
                if hasattr(self.world_manager, 'core_manager'):
                    self.world_manager.core_manager.add_network_core(core_pos, core_value)
            
            elif event_type == "atmosphere_change":
                # Update atmospheric effects
                atmosphere_type = event_data.get('type', 'clear')
                if hasattr(self, 'atmospheric_effects'):
                    self.atmospheric_effects.set_atmosphere(atmosphere_type)
    
    def _handle_enemy_spawn(self, message: NetworkMessage):
        """Handle enemy spawn (host authoritative)."""
        if not self.is_host and self.enemy_manager:
            data = message.data
            print(f"[ENEMY_SYNC] Client spawning enemy {data.get('enemy_id', 'unknown')} at {data.get('position', 'unknown')}")
            self.enemy_manager.spawn_network_enemy(data)
    
    def _handle_enemy_update(self, message: NetworkMessage):
        """Handle enemy update (host authoritative)."""
        if not self.is_host and self.enemy_manager:
            data = message.data
            enemy_id = data.get('enemy_id', 'unknown')
            position = data.get('position', (0, 0))
            
            # Rate limit enemy update debug messages
            if hasattr(self, '_enemy_update_count'):
                self._enemy_update_count += 1
            else:
                self._enemy_update_count = 1
                
            # Only log every 50th enemy update to reduce spam
            if self._enemy_update_count % 50 == 1:
                print(f"[ENEMY_SYNC] Client received enemy update for enemy {enemy_id} at {position}")
            
            # Apply the update to the enemy (this should happen for EVERY update, not just logged ones)
            self.enemy_manager.update_network_enemy(data)
    
    def _handle_enemy_death(self, message: NetworkMessage):
        """Handle enemy death (host authoritative)."""
        print(f"[ENEMY_DEATH_CLIENT] Received enemy death message: {message.data}")
        if not self.is_host and self.enemy_manager:
            data = message.data
            enemy_id = data['enemy_id']
            print(f"[ENEMY_DEATH_CLIENT] Attempting to remove enemy {enemy_id} on client")
            self.enemy_manager.remove_network_enemy(enemy_id)
            print(f"[ENEMY_DEATH_CLIENT] Remove call completed for enemy {enemy_id}")
        else:
            print(f"[ENEMY_DEATH_CLIENT] Not processing death - is_host={self.is_host}, has_enemy_mgr={self.enemy_manager is not None}")
    
    def _handle_enemy_bullet_fire(self, message: NetworkMessage):
        """Handle enemy bullet fire (host authoritative)."""
        if not self.is_host and self.bullet_manager:
            data = message.data
            enemy_id = data.get('enemy_id', 'unknown')
            position = data.get('position', (0, 0))
            angle = data.get('angle', 0)
            
            print(f"[ENEMY_BULLET] Client creating enemy bullet from {enemy_id} at {position}")
            
            # Create enemy bullet on client
            self.bullet_manager.shoot_enemy_laser(
                position[0],
                position[1], 
                angle,
                data.get('timestamp', 0)
            )
    
    def _apply_network_state(self):
        """Apply network state to local game objects."""
        # This would be called to update visual representations of network players
        # For now, we'll store the state and let the render system handle it
        pass
    
    def get_network_players(self) -> Dict[str, PlayerState]:
        """Get all network players (excluding local player)."""
        return {pid: state for pid, state in self.players.items() 
                if pid != self.local_player_id}
    
    def get_network_bullets(self) -> Dict[str, BulletState]:
        """Get all network bullets."""
        return self.bullets.copy()
    
    def get_network_enemies(self) -> Dict[str, EnemyState]:
        """Get all network enemies."""
        return self.enemies.copy()
    
    def cleanup_old_bullets(self, max_age: float = 5.0):
        """Remove network bullets older than max_age seconds."""
        current_time = time.time()
        bullets_to_remove = []
        
        for bullet_id, bullet_state in self.bullets.items():
            # Check if bullet has a creation time, if not assume it's old
            if hasattr(bullet_state, 'creation_time'):
                age = current_time - bullet_state.creation_time
                if age > max_age:
                    bullets_to_remove.append(bullet_id)
            else:
                # If no creation time, remove it (legacy bullet)
                bullets_to_remove.append(bullet_id)
        
        for bullet_id in bullets_to_remove:
            del self.bullets[bullet_id]
            print(f"[BULLET_CLEANUP] Removed old network bullet: {bullet_id}")
    
    def remove_network_bullet(self, bullet_id: str):
        """Remove a specific network bullet."""
        if bullet_id in self.bullets:
            del self.bullets[bullet_id]
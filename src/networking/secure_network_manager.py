"""
Enhanced Network Manager with secure P2P, relay servers, and join code support.
Provides IP masking, encrypted connections, and modern multiplayer features.
"""

import socket
import threading
import json
import time
import uuid
import hashlib
import base64
import ssl
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class NetworkMode(Enum):
    """Network connection modes."""
    DIRECT = "direct"           # Direct IP connection
    RELAY = "relay"            # Through relay server
    JOIN_CODE = "join_code"    # Using lobby codes


class ConnectionSecurity(Enum):
    """Security levels for connections."""
    BASIC = "basic"            # No encryption (local only)
    ENCRYPTED = "encrypted"    # End-to-end encryption
    RELAY_SECURE = "relay_secure"  # Relay with encryption


@dataclass
class PeerInfo:
    """Information about a network peer."""
    peer_id: str
    display_name: str
    public_key: Optional[str] = None
    last_ping: float = 0.0
    ping_ms: int = 0
    connection_quality: str = "Unknown"  # Good, Fair, Poor, Connecting
    is_host: bool = False
    joined_time: float = 0.0
    character: str = "Not selected"  # Selected character
    ready: bool = False  # Ready status


@dataclass
class RelayServerInfo:
    """Information about available relay servers."""
    server_id: str
    hostname: str
    port: int
    region: str
    load_percentage: int
    ping_ms: int = 999
    is_available: bool = True
    
    def get_quality_rating(self) -> str:
        """Get connection quality rating."""
        if self.ping_ms < 50 and self.load_percentage < 70:
            return "Excellent"
        elif self.ping_ms < 100 and self.load_percentage < 85:
            return "Good"
        elif self.ping_ms < 200:
            return "Fair"
        else:
            return "Poor"


@dataclass
class LobbyRegistration:
    """Lobby registration for code-based joining."""
    lobby_code: str
    host_name: str
    host_peer_id: str
    created_time: float
    max_players: int
    current_players: int
    game_mode: str
    is_private: bool
    region: str
    relay_server: str
    host_ip: str = None  # Optional IP for direct connection


class SecureNetworkManager:
    """Enhanced network manager with security and modern features."""
    
    # Default relay servers (in production, these would be distributed globally)
    DEFAULT_RELAY_SERVERS = [
        RelayServerInfo("relay-us-west", "relay-usw.kingdom-game.com", 8443, "US West", 45, 25),
        RelayServerInfo("relay-us-east", "relay-use.kingdom-game.com", 8443, "US East", 32, 18),
        RelayServerInfo("relay-eu", "relay-eu.kingdom-game.com", 8443, "Europe", 67, 42),
        RelayServerInfo("relay-asia", "relay-asia.kingdom-game.com", 8443, "Asia", 58, 78)
    ]
    
    def __init__(self, mode: NetworkMode = NetworkMode.RELAY, 
                 security: ConnectionSecurity = ConnectionSecurity.ENCRYPTED):
        self.mode = mode
        self.security = security
        
        # Network state
        self.is_host = False
        self.local_peer_id = str(uuid.uuid4())[:8].upper()
        self.session_key = None
        self.peers = {}  # peer_id -> PeerInfo
        
        # Direct connection
        self.server_socket = None
        self.client_socket = None
        self.client_connections = {}  # peer_id -> client_socket mapping for host
        
        # Relay connection
        self.relay_connection = None
        self.current_relay = None
        self.available_relays = self.DEFAULT_RELAY_SERVERS.copy()
        
        # Lobby system
        self.registered_lobbies = {}  # code -> LobbyRegistration
        self.current_lobby_code = None
        
        # Security
        self.encryption_key = None
        self.cipher_suite = None
        
        # Message handling
        self.message_handlers = {}
        self.message_queue = []
        self.network_thread = None
        self.running = False
        
        # Connection stats
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
        self.connection_start_time = 0.0
        
        # Broadcast listener for lobby discovery
        self.broadcast_listener_thread = None
        self.start_broadcast_listener()
        
        print(f"SecureNetworkManager initialized - Mode: {mode.value}, Security: {security.value}")
    
    def register_message_handler(self, message_type, handler_func):
        """Register a message handler for a specific message type."""
        self.message_handlers[message_type] = handler_func
    
    def process_messages(self):
        """Process any queued messages by calling their registered handlers."""
        while self.message_queue:
            message_dict = self.message_queue.pop(0)
            message_type = message_dict.get('type')
            
            # First try direct string lookup
            handler = self.message_handlers.get(message_type)
            
            # If not found, try enum lookup (convert string to enum)
            if handler is None:
                # Import here to avoid circular imports
                from .network_manager import MessageType, NetworkMessage
                try:
                    enum_type = MessageType(message_type)
                    handler = self.message_handlers.get(enum_type)
                    
                    # Convert dict to NetworkMessage object for handler
                    if handler:
                        network_message = NetworkMessage(
                            message_type=enum_type,
                            data=message_dict.get('data', {}),
                            timestamp=message_dict.get('timestamp'),
                            sender_id=message_dict.get('sender', message_dict.get('sender_id'))
                        )
                        try:
                            handler(network_message)
                        except Exception as e:
                            # Reduce debug spam - only show errors occasionally
                            if not hasattr(self, '_last_error_time') or (time.time() - self._last_error_time) > 5.0:
                                print(f"[ERROR] Message handler failed for type {message_type}: {e}")
                                self._last_error_time = time.time()
                        continue
                        
                except (ValueError, AttributeError):
                    pass
            
            if handler:
                try:
                    # Try to call with NetworkMessage object first
                    from .network_manager import MessageType, NetworkMessage
                    network_message = NetworkMessage(
                        message_type=MessageType(message_type),
                        data=message_dict.get('data', {}),
                        timestamp=message_dict.get('timestamp'),
                        sender_id=message_dict.get('sender', message_dict.get('sender_id'))
                    )
                    handler(network_message)
                except Exception as e:
                    # Reduce debug spam - only show errors occasionally  
                    if not hasattr(self, '_last_error_time') or (time.time() - self._last_error_time) > 5.0:
                        print(f"[ERROR] Message handler failed for type {message_type}: {e}")
                        self._last_error_time = time.time()
            else:
                # Reduce debug spam - only show missing handlers occasionally
                if not hasattr(self, '_last_missing_handler_time') or (time.time() - self._last_missing_handler_time) > 10.0:
                    self._last_missing_handler_time = time.time()
    
    def initialize_encryption(self, password: str = None) -> str:
        """Initialize encryption for secure communication."""
        if self.security == ConnectionSecurity.BASIC:
            return "No encryption"
        
        try:
            if password is None:
                # Generate session password
                password = secrets.token_urlsafe(32)
            
            # Create key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'kingdom_cleanup_salt_2024',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Initialize cipher
            self.cipher_suite = Fernet(key)
            self.encryption_key = password
            
            return f"Encryption initialized with {len(key)*8}-bit key"
            
        except Exception as e:
            print(f"Encryption initialization failed: {e}")
            self.security = ConnectionSecurity.BASIC
            return f"Fallback to basic security: {e}"
    
    def discover_relay_servers(self) -> List[RelayServerInfo]:
        """Discover and ping available relay servers."""
        print("Discovering relay servers...")
        
        # In production, this would query a master server list
        # For now, simulate by testing ping to default servers
        available_servers = []
        
        for server in self.DEFAULT_RELAY_SERVERS:
            # Simulate ping test (in production, actually ping the servers)
            server.ping_ms = self._simulate_ping(server.region)
            server.is_available = server.ping_ms < 500
            
            if server.is_available:
                available_servers.append(server)
                print(f"✓ {server.server_id}: {server.ping_ms}ms ({server.get_quality_rating()})")
            else:
                print(f"✗ {server.server_id}: Timeout")
        
        self.available_relays = available_servers
        return available_servers
    
    def _simulate_ping(self, region: str) -> int:
        """Simulate ping to relay server based on region."""
        import random
        base_ping = {
            "US West": random.randint(15, 40),
            "US East": random.randint(20, 50),
            "Europe": random.randint(80, 120),
            "Asia": random.randint(150, 200)
        }.get(region, random.randint(100, 300))
        
        # Add some variance
        return base_ping + random.randint(-10, 25)
    
    def select_best_relay(self) -> Optional[RelayServerInfo]:
        """Select the best available relay server."""
        if not self.available_relays:
            self.discover_relay_servers()
        
        if not self.available_relays:
            return None
        
        # Sort by ping and load
        def relay_score(relay: RelayServerInfo) -> float:
            # Lower is better - weighted scoring
            ping_score = relay.ping_ms / 10.0  # 10ms = 1 point
            load_score = relay.load_percentage / 10.0  # 10% = 1 point
            return ping_score + load_score
        
        best_relay = min(self.available_relays, key=relay_score)
        print(f"Selected relay: {best_relay.server_id} ({best_relay.get_quality_rating()})")
        return best_relay
    
    def create_lobby(self, lobby_name: str, max_players: int = 4, 
                    game_mode: str = "Survival", is_private: bool = False,
                    lobby_code: Optional[str] = None) -> Tuple[bool, str]:
        """Create a new lobby and return success status and lobby code."""
        try:
            # Use provided lobby code or generate unique one
            if lobby_code:
                # Validate custom code format (should be alphanumeric, 4-12 chars)
                if not lobby_code.replace("-", "").replace("_", "").isalnum() or not (4 <= len(lobby_code.replace("-", "").replace("_", "")) <= 12):
                    return False, "Invalid lobby code format"
                final_lobby_code = lobby_code.upper()
            else:
                final_lobby_code = self._generate_lobby_code()
            
            if self.mode == NetworkMode.RELAY:
                # Use relay server
                relay = self.select_best_relay()
                if not relay:
                    return False, "No relay servers available"
                
                success = self._create_relay_lobby(final_lobby_code, lobby_name, max_players, 
                                                 game_mode, is_private, relay)
                if success:
                    return True, final_lobby_code
                else:
                    return False, "Failed to create relay lobby"
                    
            elif self.mode == NetworkMode.DIRECT:
                # Direct hosting
                success = self._create_direct_lobby(final_lobby_code, lobby_name, max_players, 
                                                  game_mode, is_private)
                if success:
                    return True, final_lobby_code
                else:
                    return False, "Failed to create direct lobby"
            
            else:
                return False, f"Unsupported mode: {self.mode.value}"
                
        except Exception as e:
            print(f"Error creating lobby: {e}")
            return False, f"Error: {str(e)}"
    
    def join_lobby_by_code(self, lobby_code: str, player_name: str) -> Tuple[bool, str]:
        """Join a lobby using its code."""
        try:
            # Look up lobby registration
            lobby = self._lookup_lobby_code(lobby_code)
            if not lobby:
                return False, "Invalid or expired lobby code"
            
            if lobby.current_players >= lobby.max_players:
                return False, "Lobby is full"
            
            # Connect based on lobby type
            if lobby.relay_server:
                # Relay connection
                success = self._join_relay_lobby(lobby, player_name)
                if success:
                    return True, f"Connected via relay ({lobby.relay_server})"
                else:
                    return False, "Failed to connect to relay"
            else:
                # Direct connection - connect to host IP
                if hasattr(lobby, 'host_ip') and lobby.host_ip:
                    success = self._join_direct_lobby(lobby.host_ip, 7777, player_name)
                    if success:
                        self.current_lobby_code = lobby_code
                        return True, f"Connected directly to {lobby.host_name}"
                    else:
                        return False, "Failed to connect to host"
                else:
                    return False, "Host IP not available for direct connection"
                
        except Exception as e:
            print(f"Error joining lobby: {e}")
            return False, f"Connection error: {str(e)}"
    
    def join_lobby_direct(self, host_ip: str, port: int, player_name: str) -> Tuple[bool, str]:
        """Join a lobby using direct IP connection."""
        try:
            if self.security != ConnectionSecurity.BASIC:
                return False, "Direct IP requires basic security mode"
            
            # Create client socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10.0)  # 10 second timeout
            
            # Connect to host
            self.client_socket.connect((host_ip, port))
            self.is_host = False
            
            # Send join request
            join_msg = {
                "type": "join_request",
                "player_name": player_name,
                "peer_id": self.local_peer_id
            }
            
            self._send_direct_message(join_msg)
            
            # Wait for response
            response = self._receive_direct_message(timeout=5.0)
            if response and response.get("type") == "join_accepted":
                print(f"Successfully joined lobby at {host_ip}:{port}")
                self._start_network_thread()
                return True, f"Connected to {host_ip}:{port}"
            else:
                self.client_socket.close()
                return False, "Join request rejected"
                
        except socket.timeout:
            return False, "Connection timeout"
        except ConnectionRefusedError:
            return False, "Connection refused - host not available"
        except Exception as e:
            print(f"Direct join error: {e}")
            return False, f"Connection error: {str(e)}"
    
    def _generate_lobby_code(self) -> str:
        """Generate a unique lobby code."""
        # Use timestamp and random data for uniqueness
        timestamp = int(time.time())
        random_data = secrets.token_hex(8)
        raw_code = f"{timestamp}_{random_data}_{self.local_peer_id}"
        
        # Create hash and encode as alphanumeric
        code_hash = hashlib.sha256(raw_code.encode()).hexdigest()[:12].upper()
        
        # Format as readable code (XXXX-XXXX-XXXX)
        return f"{code_hash[:4]}-{code_hash[4:8]}-{code_hash[8:12]}"
    
    def _create_relay_lobby(self, lobby_code: str, lobby_name: str, max_players: int,
                          game_mode: str, is_private: bool, relay: RelayServerInfo) -> bool:
        """Create lobby using relay server."""
        print(f"Creating relay lobby on {relay.server_id}...")
        
        try:
            # In production, connect to actual relay server
            # For now, simulate successful creation
            
            # Register lobby
            registration = LobbyRegistration(
                lobby_code=lobby_code,
                host_name=lobby_name,
                host_peer_id=self.local_peer_id,
                created_time=time.time(),
                max_players=max_players,
                current_players=1,
                game_mode=game_mode,
                is_private=is_private,
                region=relay.region,
                relay_server=relay.server_id
            )
            
            # Store registration (in production, this would be on relay server)
            self.registered_lobbies[lobby_code] = registration
            self.current_lobby_code = lobby_code
            self.current_relay = relay
            self.is_host = True
            
            # Initialize encryption
            encryption_status = self.initialize_encryption()
            print(f"Relay lobby created: {encryption_status}")
            
            return True
            
        except Exception as e:
            print(f"Relay lobby creation failed: {e}")
            return False
    
    def _create_direct_lobby(self, lobby_code: str, lobby_name: str, max_players: int,
                           game_mode: str, is_private: bool) -> bool:
        """Create lobby using direct connection."""
        print("Creating direct lobby...")
        
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to available port (all interfaces for network access)
            self.server_socket.bind(("0.0.0.0", 7777))  # Allow external connections
            self.server_socket.listen(max_players - 1)  # Host counts as 1
            
            # Register lobby locally
            registration = LobbyRegistration(
                lobby_code=lobby_code,
                host_name=lobby_name,
                host_peer_id=self.local_peer_id,
                created_time=time.time(),
                max_players=max_players,
                current_players=1,
                game_mode=game_mode,
                is_private=is_private,
                region="Local",
                relay_server=""
            )
            
            self.registered_lobbies[lobby_code] = registration
            self.current_lobby_code = lobby_code
            self.is_host = True
            
            # Initialize encryption for direct lobbies
            encryption_status = self.initialize_encryption()
            print(f"Direct lobby encryption: {encryption_status}")
            
            # Start accepting connections
            self._start_network_thread()
            
            print(f"Direct lobby created on port 7777")
            return True
            
        except Exception as e:
            print(f"Direct lobby creation failed: {e}")
            return False
    
    def _lookup_lobby_code(self, lobby_code: str) -> Optional[LobbyRegistration]:
        """Look up lobby registration by code."""
        # Check local registrations first
        if lobby_code in self.registered_lobbies:
            lobby = self.registered_lobbies[lobby_code]
            
            # Check if expired (4 hours)
            if time.time() - lobby.created_time > 4 * 60 * 60:
                del self.registered_lobbies[lobby_code]
                return None
                
            return lobby
        
        # Broadcast query on local network to find lobby
        found_lobby = self._broadcast_lobby_query(lobby_code)
        if found_lobby:
            return found_lobby
            
        print(f"Lobby code {lobby_code} not found")
        return None
    
    def _broadcast_lobby_query(self, lobby_code: str) -> Optional[LobbyRegistration]:
        """Broadcast query on local network to find lobby with given code."""
        try:
            import socket
            import json
            
            # Create UDP socket for broadcasting
            query_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            query_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            query_socket.settimeout(2.0)  # 2 second timeout
            
            # Broadcast lobby query
            query_msg = json.dumps({
                "type": "lobby_query",
                "lobby_code": lobby_code,
                "requester": self.local_peer_id
            })
            
            query_socket.sendto(query_msg.encode(), ('<broadcast>', 12347))
            
            # Listen for responses
            try:
                while True:
                    data, addr = query_socket.recvfrom(1024)
                    response = json.loads(data.decode())
                    
                    if response.get("type") == "lobby_response" and response.get("lobby_code") == lobby_code:
                        # Found lobby! Create registration object
                        lobby_info = response.get("lobby_info", {})
                        registration = LobbyRegistration(
                            lobby_code=lobby_code,
                            host_name=lobby_info.get("host_name", "Unknown"),
                            host_peer_id=lobby_info.get("host_peer_id", ""),
                            created_time=lobby_info.get("created_time", time.time()),
                            max_players=lobby_info.get("max_players", 4),
                            current_players=lobby_info.get("current_players", 1),
                            game_mode=lobby_info.get("game_mode", "Survival"),
                            is_private=lobby_info.get("is_private", False),
                            region=lobby_info.get("region", "local"),
                            relay_server=lobby_info.get("relay_server", None),
                            host_ip=addr[0]  # Store IP for direct connection
                        )
                        query_socket.close()
                        return registration
            except socket.timeout:
                pass
            
            query_socket.close()
            
        except Exception as e:
            print(f"Error broadcasting lobby query: {e}")
            
        return None
    
    def start_broadcast_listener(self):
        """Start background thread to listen for lobby broadcast queries."""
        try:
            import threading
            self.broadcast_listener_thread = threading.Thread(target=self._broadcast_listener_loop, daemon=True)
            self.broadcast_listener_thread.start()
        except Exception as e:
            print(f"Error starting broadcast listener: {e}")
    
    def _broadcast_listener_loop(self):
        """Background thread that listens for lobby discovery broadcasts."""
        try:
            import socket
            import json
            
            # Create UDP socket for listening
            listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener_socket.bind(('', 12347))  # Listen on port 12347
            listener_socket.settimeout(1.0)
            
            while True:
                try:
                    data, addr = listener_socket.recvfrom(1024)
                    query = json.loads(data.decode())
                    
                    if query.get("type") == "lobby_query":
                        lobby_code = query.get("lobby_code")
                        requester = query.get("requester")
                        
                        # Don't respond to our own queries
                        if requester == self.local_peer_id:
                            continue
                        
                        # Check if we have this lobby
                        if lobby_code in self.registered_lobbies:
                            lobby = self.registered_lobbies[lobby_code]
                            
                            # Send response
                            response = {
                                "type": "lobby_response",
                                "lobby_code": lobby_code,
                                "lobby_info": {
                                    "host_name": lobby.host_name,
                                    "host_peer_id": lobby.host_peer_id,
                                    "created_time": lobby.created_time,
                                    "max_players": lobby.max_players,
                                    "current_players": lobby.current_players,
                                    "game_mode": lobby.game_mode,
                                    "is_private": lobby.is_private,
                                    "region": lobby.region,
                                    "relay_server": lobby.relay_server
                                }
                            }
                            
                            response_msg = json.dumps(response)
                            listener_socket.sendto(response_msg.encode(), addr)
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    # Ignore individual packet errors, keep listening
                    pass
                    
        except Exception as e:
            print(f"Error in broadcast listener: {e}")
    
    def cleanup(self):
        """Clean up network resources."""
        if self.broadcast_listener_thread:
            # In a full implementation, we'd properly signal the thread to stop
            pass
    
    def _join_relay_lobby(self, lobby: LobbyRegistration, player_name: str) -> bool:
        """Join a lobby through relay server."""
        print(f"Joining relay lobby via {lobby.relay_server}...")
        
        try:
            # In production, connect to the actual relay server
            # For now, simulate successful connection
            
            # Update lobby registration
            lobby.current_players += 1
            self.current_lobby_code = lobby.lobby_code
            
            # Add host as peer
            host_peer = PeerInfo(
                peer_id=lobby.host_peer_id,
                display_name=lobby.host_name,
                is_host=True,
                joined_time=lobby.created_time,
                connection_quality="Good"
            )
            self.peers[lobby.host_peer_id] = host_peer
            
            print(f"Successfully joined relay lobby")
            return True
            
        except Exception as e:
            print(f"Relay join failed: {e}")
            return False
    
    def _join_direct_lobby(self, host_ip: str, port: int, player_name: str) -> bool:
        """Join a direct lobby with encryption support."""
        try:
            # Create client socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10.0)  # 10 second timeout
            
            # Connect to host
            print(f"Connecting to {host_ip}:{port}...")
            self.client_socket.connect((host_ip, port))
            self.is_host = False
            
            # Note: Client encryption initialization moved to after join_accepted
            # to use shared key from host
            
            # Send join request using framed message
            join_msg = {
                "type": "join_request",
                "player_name": player_name,
                "peer_id": self.local_peer_id,
                "character": "Cecil",  # Default character for now
                "timestamp": time.time()
            }
            
            # Send join request with length prefix
            msg_data = json.dumps(join_msg).encode()
            msg_length = len(msg_data)
            length_prefix = msg_length.to_bytes(4, 'big')
            framed_message = length_prefix + msg_data
            
            self.client_socket.send(framed_message)
            print(f"Sent framed join request ({len(framed_message)} bytes total, payload {len(msg_data)})")
            
            # Wait for response
            response = self._receive_direct_socket_message(timeout=5.0)
            if response and response.get("type") == "join_accepted":
                print(f"Successfully joined direct lobby at {host_ip}:{port}")
                
                # Initialize encryption with shared key from host
                if self.security == ConnectionSecurity.ENCRYPTED:
                    encryption_key = response.get("encryption_key")
                    if encryption_key:
                        encryption_status = self.initialize_encryption(encryption_key)
                        print(f"Client encryption: {encryption_status}")
                    else:
                        print("Warning: No encryption key received from host")
                
                # Store host information
                host_peer = PeerInfo(
                    peer_id=response.get("host_peer_id", "HOST"),
                    display_name=response.get("host_name", "Host"),
                    is_host=True,
                    joined_time=time.time(),
                    connection_quality="Good"
                )
                self.peers[host_peer.peer_id] = host_peer
                
                # Start network processing
                self._start_network_thread()
                return True
            else:
                error_msg = response.get("error", "Join request rejected") if response else "No response from host"
                print(f"Join failed: {error_msg}")
                self.client_socket.close()
                self.client_socket = None
                return False
                
        except Exception as e:
            print(f"Direct join failed: {e}")
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
            return False
    
    def _start_network_thread(self):
        """Start the network processing thread."""
        if not self.running:
            self.running = True
            self.connection_start_time = time.time()
            self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
            self.network_thread.start()
            print("Network thread started")
    
    def _network_loop(self):
        """Main network processing loop."""
        last_status = None
        while self.running:
            try:
                # Debug output only when status changes to avoid spam
                current_status = (self.is_host, self.server_socket is not None, self.client_socket is not None, self.relay_connection is not None)
                if current_status != last_status:
                    last_status = current_status
                
                if self.is_host and self.server_socket:
                    self._handle_host_networking()
                elif self.client_socket:
                    self._handle_client_networking()
                elif self.relay_connection:
                    self._handle_relay_networking()
                
                time.sleep(0.016)  # ~60 FPS
                
            except Exception as e:
                print(f"Network loop error: {e}")
                time.sleep(0.1)
    
    def _handle_host_networking(self):
        """Handle networking for host."""
        # Accept new connections
        try:
            self.server_socket.settimeout(0.1)  # Non-blocking
            client_socket, address = self.server_socket.accept()
            print(f"New connection from {address}")
            
            # Handle new client in separate thread
            client_thread = threading.Thread(
                target=self._handle_client_connection,
                args=(client_socket, address),
                daemon=True
            )
            client_thread.start()
            
        except socket.timeout:
            pass  # No new connections
        except Exception as e:
            print(f"Error accepting connections: {e}")
    
    def _handle_client_connection(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle a client connection."""
        try:
            # Receive join request using framed messages
            messages = self._receive_framed_messages(client_socket)
            
            if messages:
                message_data = messages[0]  # Get first message
                message = json.loads(message_data.decode())
                
                if message.get("type") == "join_request":
                    player_name = message.get("player_name", "Unknown")
                    peer_id = message.get("peer_id", str(uuid.uuid4())[:8])
                    character = message.get("character", "Not selected")
                    
                    # Add peer
                    peer = PeerInfo(
                        peer_id=peer_id,
                        display_name=player_name,
                        joined_time=time.time(),
                        connection_quality="Good",
                        character=character,
                        ready=False
                    )
                    self.peers[peer_id] = peer
                    
                    # Store client connection for message broadcasting
                    self.client_connections[peer_id] = client_socket
                    
                    # Important: Notify about new player connection
                    print(f"[CONNECTION] New player joined lobby: {player_name} ({peer_id})")
                    
                    # Send acceptance - include host name for proper display
                    lobby_registration = self.registered_lobbies.get(self.current_lobby_code)
                    host_name = lobby_registration.host_name if lobby_registration else "Host"
                    
                    response = {
                        "type": "join_accepted",
                        "peer_id": peer_id,
                        "lobby_code": self.current_lobby_code,
                        "host_name": host_name,
                        "encryption_key": self.encryption_key if self.security == ConnectionSecurity.ENCRYPTED else None
                    }
                    
                    # Send response using framed messages
                    response_data = json.dumps(response).encode()
                    msg_length = len(response_data)
                    length_prefix = msg_length.to_bytes(4, 'big')
                    framed_response = length_prefix + response_data
                    
                    client_socket.send(framed_response)
                    print(f"Accepted connection from {player_name} ({peer_id})")
                    
                    # Start a separate thread to handle ongoing messages from this client
                    message_thread = threading.Thread(
                        target=self._handle_client_messages,
                        args=(client_socket, peer_id),
                        daemon=True
                    )
                    message_thread.start()
        
        except Exception as e:
            print(f"Client connection error: {e}")
            # Don't close the socket here - let the message thread handle it
            if 'client_socket' in locals():
                client_socket.close()
            
    def _handle_client_messages(self, client_socket: socket.socket, peer_id: str):
        """Handle ongoing messages from a connected client."""
        try:
            client_socket.settimeout(1.0)  # Set timeout for non-blocking receive
            
            last_debug_time = 0
            
            while True:
                try:
                    # Rate-limited debug (every 10 seconds)
                    current_time = time.time()
                    if current_time - last_debug_time > 10.0:
                        last_debug_time = current_time
                    
                    # Use framed message receiving
                    messages = self._receive_framed_messages(client_socket)
                    
                    for message_data in messages:
                        try:
                            message = json.loads(message_data.decode())
                            
                            # Decrypt if the message is encrypted
                            if 'encrypted' in message and self.cipher_suite:
                                try:
                                    encrypted_data = base64.b64decode(message['encrypted'])
                                    decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                                    message = json.loads(decrypted_data.decode())
                                    # Reduce spam - only log important messages
                                    if message.get('type') not in ['player_update', 'wave_update']:
                                        pass
                                except Exception as e:
                                    # Don't rate limit decrypt errors - they indicate real connection/security issues
                                    print(f"[ERROR] Failed to decrypt message from {peer_id}: {e}")
                                    continue
                            
                            # Process the message (ready state updates, etc.)
                            self._process_client_message(message, peer_id)
                            
                        except json.JSONDecodeError as e:
                            # Don't rate limit JSON decode errors - they indicate message corruption
                            print(f"[ERROR] Host JSON decode error from {peer_id}: {e}")
                            print(f"[ERROR] Problematic data (first 200 chars): {message_data[:200]}")
                            continue
                        
                except socket.timeout:
                    # Continue waiting for messages
                    continue
                except Exception as e:
                    print(f"Error receiving from client {peer_id}: {e}")
                    break
                    
        except Exception as e:
            print(f"Client message handler error: {e}")
        finally:
            # Clean up when message thread exits
            print(f"Cleaning up client {peer_id}")
            if peer_id in self.client_connections:
                del self.client_connections[peer_id]
            if peer_id in self.peers:
                del self.peers[peer_id]
            try:
                client_socket.close()
            except:
                pass
            
    def _process_client_message(self, message: dict, sender_peer_id: str):
        """Process a message received from a client."""
        message_type = message.get('type', '')
        
        # Add message to queue for game synchronizer processing
        self.message_queue.append(message)
        
        if message_type == 'lobby_ready_state':
            # Update the peer's ready state
            data = message.get('data', {})
            is_ready = data.get('is_ready', False)
            
            if sender_peer_id in self.peers:
                self.peers[sender_peer_id].ready = is_ready
                print(f"Updated peer {sender_peer_id} ready state to {is_ready}")
                
                # Broadcast this ready state update to all other clients
                # (but not back to the sender)
                self._broadcast_to_clients(message, exclude_peer=sender_peer_id)
                
                # IMPORTANT: Also notify the lobby about this message
                if hasattr(self, 'message_handler') and self.message_handler:
                    self.message_handler(message)
        
        # Add handling for other message types as needed
    
    def _handle_client_networking(self):
        """Handle networking for client."""
        if not self.client_socket:
            return
            
        try:
            # Use framed message receiving to avoid JSON parsing errors
            messages = self._receive_framed_messages(self.client_socket)
            
            for message_data in messages:
                try:
                    message = json.loads(message_data.decode())
                    
                    # Decrypt if the message is encrypted
                    if 'encrypted' in message and self.cipher_suite:
                        try:
                            encrypted_data = base64.b64decode(message['encrypted'])
                            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                            message = json.loads(decrypted_data.decode())
                            
                            # Only log important messages
                            important_messages = ['lobby_setting_change', 'game_start', 'lobby_ready_state', 'join_request']
                            if message.get('type') in important_messages:
                                pass
                        except Exception as e:
                            # Don't rate limit client decrypt errors - they indicate real connection issues
                            print(f"[ERROR] Client failed to decrypt message from host: {e}")
                            continue
                    
                    # Process the message (setting changes, ready states, etc.)
                    self._process_host_message(message)
                    
                except json.JSONDecodeError as e:
                    # Don't rate limit client JSON decode errors - they indicate message corruption  
                    print(f"[ERROR] Client JSON decode error: {e}")
                    print(f"[ERROR] Problematic data (first 200 chars): {message_data[:200]}")
                    continue
                
        except socket.timeout:
            # Continue waiting for messages
            pass
        except ConnectionResetError:
            # Host disconnected
            print(f"Host disconnected")
            self.client_socket.close()
            self.client_socket = None
        except Exception as e:
            if "10035" not in str(e):  # Ignore non-blocking socket errors
                print(f"Client networking error: {e}")
    
    def _process_host_message(self, message: dict):
        """Process a message received from the host."""
        message_type = message.get('type', '')
        
        # Add message to queue for game synchronizer processing
        self.message_queue.append(message)
        
        # Also notify the lobby about this message
        if hasattr(self, 'message_handler') and self.message_handler:
            self.message_handler(message)
    
    def _receive_framed_messages(self, socket):
        """Receive length-prefixed messages from socket."""
        messages = []
        
        try:
            # Check if we have any partial data from previous receive
            if not hasattr(self, '_receive_buffer'):
                self._receive_buffer = b''
            
            # Receive new data
            data = socket.recv(4096)
            if not data:
                return messages
            
            self._receive_buffer += data
            
            # Process complete messages from buffer
            while len(self._receive_buffer) >= 4:  # Need at least 4 bytes for length prefix
                # Read message length (first 4 bytes, big endian)
                msg_length = int.from_bytes(self._receive_buffer[:4], 'big')
                
                # Check if we have the complete message
                if len(self._receive_buffer) >= 4 + msg_length:
                    # Extract the message
                    message_data = self._receive_buffer[4:4 + msg_length]
                    messages.append(message_data)
                    
                    # Remove processed message from buffer
                    self._receive_buffer = self._receive_buffer[4 + msg_length:]
                else:
                    # Not enough data for complete message yet
                    break
                    
        except Exception as e:
            # Handle timeout exceptions gracefully - they're expected when no messages are pending
            if "timed out" not in str(e).lower():
                print(f"[ERROR] Message framing error: {e}")
            # Clear the buffer on non-timeout errors to prevent corruption
            if hasattr(self, '_receive_buffer') and "timed out" not in str(e).lower():
                self._receive_buffer = b''
            
        return messages
    
    def _handle_relay_networking(self):
        """Handle networking through relay server."""
        # Relay-specific networking would go here
        pass
    
    def _send_direct_message(self, message: dict):
        """Send a message via direct connection."""
        
        if self.is_host:
            # Host broadcasts to all connected clients
            self._broadcast_to_clients(message)
        elif self.client_socket:
            # Client sends to host using length-prefixed framing
            try:
                data = json.dumps(message).encode()
                
                # Create length-prefixed message
                msg_length = len(data)
                length_prefix = msg_length.to_bytes(4, 'big')
                framed_message = length_prefix + data
                
                self.client_socket.send(framed_message)
                self.bytes_sent += len(framed_message)
                self.packets_sent += 1
            except Exception as e:
                # Don't rate limit connection errors - they indicate real problems
                print(f"Error sending message to host: {e}")
        else:
            # Don't rate limit - connection status is important
            print("No connection available - message not sent")
    
    def _broadcast_to_clients(self, message: dict, exclude_peer: str = None):
        """Broadcast a message to all connected clients (host only)."""
        if not self.is_host:
            return
            
        data = json.dumps(message).encode()
        
        # Create length-prefixed message
        msg_length = len(data)
        length_prefix = msg_length.to_bytes(4, 'big')
        framed_message = length_prefix + data
        
        disconnected_peers = []
        
        # Only log important message types
        msg_type = message.get('type', 'unknown')
        important_messages = ['lobby_setting_change', 'game_start', 'lobby_ready_state', 'join_request']
        
        # Create a copy of client_connections to avoid dictionary changed size during iteration
        for peer_id, client_socket in list(self.client_connections.items()):
            if exclude_peer and peer_id == exclude_peer:
                continue
                
            try:
                if msg_type in important_messages:
                    pass  # Important message handling
                
                client_socket.send(framed_message)
                self.bytes_sent += len(framed_message)
                self.packets_sent += 1
            except Exception as e:
                disconnected_peers.append(peer_id)
        
        # Clean up disconnected peers
        for peer_id in disconnected_peers:
            if peer_id in self.client_connections:
                del self.client_connections[peer_id]
            if peer_id in self.peers:
                del self.peers[peer_id]
    
    def _receive_direct_message(self, timeout: float = 1.0) -> Optional[dict]:
        """Receive a message - during join use socket, otherwise use queue."""
        # During initial join, read directly from socket
        if not self.network_thread or not self.network_thread.is_alive():
            return self._receive_direct_socket_message(timeout)
        
        # After network thread is running, use message queue  
        if self.message_queue:
            message = self.message_queue.pop(0)
            return message
        return None
    
    def _receive_direct_socket_message(self, timeout: float = 1.0) -> Optional[dict]:
        """Receive a message directly from socket (used during join process)."""
        if not self.client_socket:
            return None
            
        try:
            self.client_socket.settimeout(timeout)
            messages = self._receive_framed_messages(self.client_socket)
            
            if messages:
                message_data = messages[0]  # Get first message
                message = json.loads(message_data.decode())
                
                # Decrypt if the message is encrypted
                if 'encrypted' in message and self.cipher_suite:
                    try:
                        encrypted_data = base64.b64decode(message['encrypted'])
                        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                        message = json.loads(decrypted_data.decode())
                    except Exception as e:
                        print(f"[ERROR] Failed to decrypt join response: {e}")
                        return None
                
                return message
                
        except socket.timeout:
            return None
        except Exception as e:
            print(f"[ERROR] Error receiving join response: {e}")
            return None
            
        return None
    
    def get_pending_messages(self) -> list:
        """Get all pending messages from the queue."""
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages
    
    def send_message(self, message_type, data: dict, target_peer: str = None):
        """Send a message to peers."""
        # Reduce debug spam - only log important messages
        important_messages = ['lobby_setting_change', 'game_start', 'lobby_ready_state', 'join_request']
        if str(message_type) in important_messages:
            pass
        
        # Convert MessageType enum to string if needed
        if hasattr(message_type, 'value'):
            message_type_str = message_type.value
        else:
            message_type_str = str(message_type)
        
        message = {
            "type": message_type_str,
            "data": data,
            "sender": self.local_peer_id,
            "timestamp": time.time()
        }
        
        if str(message_type) in important_messages:
            pass
        
        # Encrypt if enabled
        if self.cipher_suite:
            try:
                encrypted_data = self.cipher_suite.encrypt(json.dumps(message).encode())
                message = {"encrypted": base64.b64encode(encrypted_data).decode()}
                if str(message_type) in important_messages:
                    pass
            except Exception as e:
                print(f"Encryption error: {e}")
        
        # Route message based on connection type
        if self.mode == NetworkMode.DIRECT:
            if str(message_type) in important_messages:
                pass
            self._send_direct_message(message)
        elif self.mode == NetworkMode.RELAY:
            self._send_relay_message(message, target_peer)
        
        self.packets_sent += 1
    
    def _send_relay_message(self, message: dict, target_peer: str = None):
        """Send message through relay server."""
        # In production, send to actual relay server
        print(f"Relay message: {message['type']} -> {target_peer or 'all'}")
    
    def get_connection_info(self) -> dict:
        """Get detailed connection information."""
        uptime = time.time() - self.connection_start_time if self.connection_start_time > 0 else 0
        
        return {
            "mode": self.mode.value,
            "security": self.security.value,
            "peer_id": self.local_peer_id,
            "is_host": self.is_host,
            "lobby_code": self.current_lobby_code,
            "connected_peers": len(self.peers),
            "relay_server": self.current_relay.server_id if self.current_relay else None,
            "uptime_seconds": uptime,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "encryption_enabled": self.cipher_suite is not None
        }
    
    def get_peer_list(self) -> List[PeerInfo]:
        """Get list of connected peers."""
        return list(self.peers.values())
    
    def disconnect(self):
        """Disconnect from network."""
        print("Disconnecting from network...")
        
        self.running = False
        
        # Close connections
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            
        if self.relay_connection:
            self.relay_connection.close()
            self.relay_connection = None
        
        # Clear state
        self.peers.clear()
        self.current_lobby_code = None
        self.is_host = False
        
        print("Network disconnected")
    
    def get_lobby_share_info(self) -> Optional[dict]:
        """Get information for sharing the lobby."""
        if not self.current_lobby_code:
            return None
        
        lobby = self.registered_lobbies.get(self.current_lobby_code)
        if not lobby:
            return None
        
        return {
            "lobby_code": lobby.lobby_code,
            "display_name": lobby.host_name,
            "game_mode": lobby.game_mode,
            "players": f"{lobby.current_players}/{lobby.max_players}",
            "region": lobby.region,
            "discord_message": f"🎮 **Kingdom Cleanup Lobby**\\n🔹 Code: `{lobby.lobby_code}`\\n🔹 Mode: {lobby.game_mode}\\n🔹 Players: {lobby.current_players}/{lobby.max_players}\\n🔹 Region: {lobby.region}",
            "quick_join_url": f"kingdom://join/{lobby.lobby_code}"
        }

"""
Network Manager for Kingdom-Pygame multiplayer.
Handles client-server communication, message routing, and connection management.
"""

import socket
import threading
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import pygame as pg


class MessageType(Enum):
    """Types of network messages."""
    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    
    # Player synchronization
    PLAYER_UPDATE = "player_update"
    PLAYER_JOIN = "player_join"
    PLAYER_LEAVE = "player_leave"
    
    # Game events
    BULLET_FIRE = "bullet_fire"
    BULLET_HIT = "bullet_hit"
    WEAPON_SWITCH = "weapon_switch"
    PLAYER_DAMAGE = "player_damage"
    PLAYER_DEATH = "player_death"
    ENEMY_DAMAGE = "enemy_damage"
    
    # Effects synchronization
    EXPLOSION = "explosion"
    MUZZLE_FLASH = "muzzle_flash"
    DASH_EFFECT = "dash_effect"
    
    # Enemy synchronization
    ENEMY_SPAWN = "enemy_spawn"
    ENEMY_UPDATE = "enemy_update"
    ENEMY_DEATH = "enemy_death"
    ENEMY_BULLET_FIRE = "enemy_bullet_fire"
    
    # Game state
    GAME_START = "game_start"
    GAME_END = "game_end"
    LEVEL_UPDATE = "level_update"
    WAVE_UPDATE = "wave_update"
    SCORE_UPDATE = "score_update"
    WORLD_EVENT = "world_event"


@dataclass
class NetworkMessage:
    """A network message with type and data."""
    message_type: MessageType
    data: Dict[str, Any]
    timestamp: float = None
    sender_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_bytes(self) -> bytes:
        """Convert message to bytes for transmission."""
        message_dict = {
            'type': self.message_type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'sender_id': self.sender_id
        }
        json_str = json.dumps(message_dict)
        # Prefix with message length for proper packet boundaries
        message_bytes = json_str.encode('utf-8')
        length_prefix = len(message_bytes).to_bytes(4, byteorder='big')
        return length_prefix + message_bytes
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'NetworkMessage':
        """Create message from bytes."""
        message_dict = json.loads(data.decode('utf-8'))
        return cls(
            message_type=MessageType(message_dict['type']),
            data=message_dict['data'],
            timestamp=message_dict.get('timestamp'),
            sender_id=message_dict.get('sender_id')
        )


class NetworkManager:
    """Manages network connections and message handling."""
    
    def __init__(self, is_server: bool = False):
        self.is_server = is_server
        self.socket = None
        self.running = False
        self.connected_clients = {}  # client_id -> (socket, address)
        self.message_handlers = {}  # MessageType -> callback function
        self.player_id = None
        
        # Server-specific
        self.server_socket = None
        self.server_thread = None
        
        # Client-specific
        self.client_thread = None
        self.server_address = None
        
        # Message queues
        self.incoming_messages = []
        self.outgoing_messages = []
        self.message_lock = threading.Lock()
        
        # Connection state
        self.connected = False
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 5.0  # seconds
        
        # Performance monitoring
        self.bytes_sent = 0
        self.bytes_received = 0
        self.messages_sent = 0
        self.messages_received = 0
    
    def start_server(self, host: str = "localhost", port: int = 7777):
        """Start as a server."""
        if self.is_server and not self.running:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((host, port))
                self.server_socket.listen(8)  # Support up to 8 players
                
                self.running = True
                self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
                self.server_thread.start()
                
                print(f"Server started on {host}:{port}")
                return True
            except Exception as e:
                print(f"Failed to start server: {e}")
                return False
        return False
    
    def connect_to_server(self, host: str, port: int, player_name: str):
        """Connect to a server as a client."""
        if not self.is_server and not self.connected:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((host, port))
                self.server_address = (host, port)
                
                # Send connection request
                connect_msg = NetworkMessage(
                    MessageType.CONNECT,
                    {"player_name": player_name}
                )
                self._send_message(connect_msg, self.socket)
                
                self.running = True
                self.connected = True
                self.client_thread = threading.Thread(target=self._client_loop, daemon=True)
                self.client_thread.start()
                
                print(f"Connected to server {host}:{port}")
                return True
            except Exception as e:
                print(f"Failed to connect to server: {e}")
                if self.socket:
                    self.socket.close()
                    self.socket = None
                return False
        return False
    
    def disconnect(self):
        """Disconnect from server or stop server."""
        if self.running:
            self.running = False
            
            if self.is_server:
                # Close all client connections
                for client_id, (client_socket, _) in self.connected_clients.items():
                    try:
                        client_socket.close()
                    except:
                        pass
                self.connected_clients.clear()
                
                if self.server_socket:
                    self.server_socket.close()
                    self.server_socket = None
                
                if self.server_thread:
                    self.server_thread.join(timeout=1.0)
                    
                print("Server stopped")
            else:
                # Send disconnect message
                if self.connected and self.socket:
                    try:
                        disconnect_msg = NetworkMessage(MessageType.DISCONNECT, {})
                        self._send_message(disconnect_msg, self.socket)
                    except:
                        pass
                    
                    self.socket.close()
                    self.socket = None
                
                if self.client_thread:
                    self.client_thread.join(timeout=1.0)
                
                self.connected = False
                print("Disconnected from server")
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a callback for a specific message type."""
        self.message_handlers[message_type] = handler
    
    def send_message(self, message_type: MessageType, data: Dict[str, Any]):
        """Send a message to connected peers."""
        message = NetworkMessage(message_type, data, sender_id=self.player_id)
        
        with self.message_lock:
            self.outgoing_messages.append(message)
    
    def process_messages(self):
        """Process incoming messages (call from main game loop)."""
        messages_to_process = []
        
        with self.message_lock:
            messages_to_process = self.incoming_messages.copy()
            self.incoming_messages.clear()
        
        for message in messages_to_process:
            if message.message_type in self.message_handlers:
                try:
                    self.message_handlers[message.message_type](message)
                except Exception as e:
                    print(f"Error handling message {message.message_type}: {e}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            "is_server": self.is_server,
            "connected": self.connected,
            "running": self.running,
            "connected_clients": len(self.connected_clients) if self.is_server else 0,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received
        }
    
    def _server_loop(self):
        """Main server loop for handling connections."""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Server loop error: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket, client_address):
        """Handle individual client connection."""
        client_id = f"{client_address[0]}:{client_address[1]}"
        self.connected_clients[client_id] = (client_socket, client_address)
        
        try:
            while self.running:
                message = self._receive_message(client_socket)
                if message is None:
                    break
                
                message.sender_id = client_id
                
                # Handle connection messages specially
                if message.message_type == MessageType.CONNECT:
                    self._handle_client_connect(message, client_id)
                elif message.message_type == MessageType.DISCONNECT:
                    break
                else:
                    # Add to incoming messages for processing
                    with self.message_lock:
                        self.incoming_messages.append(message)
                    
                    # Broadcast to other clients (except sender)
                    self._broadcast_message(message, exclude_client=client_id)
        
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            # Clean up client connection
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            try:
                client_socket.close()
            except:
                pass
            
            # Notify other clients of disconnection
            disconnect_msg = NetworkMessage(
                MessageType.PLAYER_LEAVE,
                {"player_id": client_id}
            )
            self._broadcast_message(disconnect_msg)
    
    def _client_loop(self):
        """Main client loop for receiving messages and processing outgoing queue."""
        import time
        last_send_time = 0
        send_interval = 0.01  # Send outgoing messages every 10ms to prevent flooding
        
        while self.running and self.connected:
            try:
                # Process outgoing messages with rate limiting
                current_time = time.time()
                if current_time - last_send_time >= send_interval:
                    messages_to_send = []
                    with self.message_lock:
                        messages_to_send = self.outgoing_messages.copy()
                        self.outgoing_messages.clear()
                    
                    # Send up to 10 messages per batch to prevent flooding
                    for message in messages_to_send[:10]:
                        try:
                            self._send_message(message, self.socket)
                        except Exception as e:
                            print(f"Error sending message: {e}")
                            break
                    
                    # Re-queue remaining messages if we hit the batch limit
                    if len(messages_to_send) > 10:
                        with self.message_lock:
                            self.outgoing_messages = messages_to_send[10:] + self.outgoing_messages
                    
                    last_send_time = current_time
                
                # Receive incoming messages
                try:
                    self.socket.settimeout(0.1)  # Short timeout to allow outgoing processing
                    message = self._receive_message(self.socket)
                    if message is None:
                        continue
                    
                    with self.message_lock:
                        self.incoming_messages.append(message)
                        
                except socket.timeout:
                    continue  # Timeout is normal, just continue the loop
                
            except Exception as e:
                if self.running:
                    print(f"Client loop error: {e}")
                break
        
        self.connected = False
    
    def _handle_client_connect(self, message: NetworkMessage, client_id: str):
        """Handle a new client connection."""
        player_name = message.data.get("player_name", f"Player_{client_id}")
        
        # Send welcome message to new client
        welcome_msg = NetworkMessage(
            MessageType.CONNECT,
            {
                "player_id": client_id,
                "player_name": player_name,
                "connected_players": [
                    {"id": cid, "name": f"Player_{cid}"}
                    for cid in self.connected_clients.keys()
                ]
            }
        )
        
        client_socket, _ = self.connected_clients[client_id]
        self._send_message(welcome_msg, client_socket)
        
        # Notify other clients of new player
        join_msg = NetworkMessage(
            MessageType.PLAYER_JOIN,
            {"player_id": client_id, "player_name": player_name}
        )
        self._broadcast_message(join_msg, exclude_client=client_id)
    
    def _broadcast_message(self, message: NetworkMessage, exclude_client: str = None):
        """Broadcast message to all connected clients."""
        if not self.is_server:
            return
        
        clients_to_remove = []
        for client_id, (client_socket, _) in self.connected_clients.items():
            if client_id == exclude_client:
                continue
            
            try:
                self._send_message(message, client_socket)
            except Exception as e:
                print(f"Failed to send to client {client_id}: {e}")
                clients_to_remove.append(client_id)
        
        # Remove disconnected clients
        for client_id in clients_to_remove:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
    
    def _send_message(self, message: NetworkMessage, target_socket: socket.socket):
        """Send a single message to a socket with error handling."""
        try:
            message_bytes = message.to_bytes()
            
            # Set a short send timeout to prevent blocking
            target_socket.settimeout(0.5)  # 500ms timeout
            target_socket.sendall(message_bytes)
            
            self.bytes_sent += len(message_bytes)
            self.messages_sent += 1
            
        except socket.timeout:
            print(f"[NETWORK] Send timeout - message dropped")
            raise
        except Exception as e:
            print(f"[NETWORK] Send error: {e}")
            raise
    
    def _receive_message(self, source_socket: socket.socket) -> Optional[NetworkMessage]:
        """Receive a single message from a socket."""
        try:
            # First, read the message length (4 bytes)
            length_bytes = self._receive_exact(source_socket, 4)
            if not length_bytes:
                return None
            
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Then read the message data
            message_bytes = self._receive_exact(source_socket, message_length)
            if not message_bytes:
                return None
            
            self.bytes_received += len(message_bytes) + 4
            self.messages_received += 1
            
            return NetworkMessage.from_bytes(message_bytes)
        
        except Exception as e:
            return None
    
    def _receive_exact(self, source_socket: socket.socket, num_bytes: int) -> Optional[bytes]:
        """Receive exactly num_bytes from socket."""
        data = b''
        while len(data) < num_bytes:
            chunk = source_socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
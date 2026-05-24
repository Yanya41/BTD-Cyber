import socket
import pickle
import json
import struct


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1"
        self.port = 5555
        self.addr = (self.server, self.port)

        # Connect immediately, but do NOT expect pickle data yet!
        self.connect()

        # These remain empty until the lobby launches the game
        self.player_id = None
        self.initial_state = None

    def connect(self):
        try:
            self.client.connect(self.addr)
            print("Successfully connected to the server!")
        except Exception as e:
            print(f"Connection Error: {e}")

    # ==========================================
    # TCP FRAMING HELPERS (Match server.py)
    # ==========================================
    def _send_msg(self, data: bytes):
        """Send data with a 4-byte length header (matches server)"""
        try:
            header = struct.pack('>I', len(data))
            self.client.sendall(header + data)
        except Exception as e:
            print(f"Send Error: {e}")

    def _recv_msg(self):
        """Receive data with a 4-byte length header (matches server)"""
        try:
            raw_header = self._recv_exactly(4)
            if not raw_header:
                return None
            length = struct.unpack('>I', raw_header)[0]
            return self._recv_exactly(length)
        except Exception as e:
            print(f"Receive Error: {e}")
            return None

    def _recv_exactly(self, n: int):
        """Receive exactly n bytes"""
        buf = b""
        while len(buf) < n:
            try:
                chunk = self.client.recv(n - len(buf))
                if not chunk:
                    return None
                buf += chunk
            except Exception as e:
                print(f"Recv Exactly Error: {e}")
                return None
        return buf

    # ==========================================
    # PHASE 1 & 2: JSON (Menus & Lobbies)
    # ==========================================
    def send_json(self, data):
        """Sends a dict to server as JSON and returns the JSON response."""
        try:
            self._send_msg(json.dumps(data).encode('utf-8'))
            response = self._recv_msg()
            if response:
                return json.loads(response.decode('utf-8'))
            return None
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response from server: {e}")
            return None
        except Exception as e:
            print(f"Network JSON Error: {e}")
            return None

    # ==========================================
    # PHASE 3: PICKLE (Actual Gameplay)
    # ==========================================
    def wait_for_game_start(self):
        """
        Called right after a lobby is successfully joined/created.
        It catches the initial pickle state the server sends.
        """
        try:
            data = self._recv_msg()
            if not data:
                return False
            init_data = pickle.loads(data)
            self.player_id = init_data["id"]
            self.initial_state = init_data["state"]
            print(f"Game Initialized! I am Player {self.player_id}")
            return True
        except Exception as e:
            print(f"Error loading initial game state: {e}")
            return False

    def send_action(self, data):
        """Send an action and receive game state response"""
        try:
            self._send_msg(pickle.dumps(data))
            response = self._recv_msg()
            if response:
                return pickle.loads(response)
            return None
        except Exception as e:
            print(f"Send Action Error: {e}")
            return None

    def get_state(self):
        """Requests the current game state from the server."""
        try:
            self._send_msg(pickle.dumps({"type": "get_state"}))
            response = self._recv_msg()
            if response:
                return pickle.loads(response)
            return None
        except Exception as e:
            print(f"Get State Error: {e}")
            return None

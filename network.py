import socket
import pickle
import json


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
    # PHASE 1 & 2: JSON (Menus & Lobbies)
    # ==========================================
    def send_json(self, data):
        """Sends a dict to server as JSON and returns the JSON response."""
        try:
            self.client.send(json.dumps(data).encode('utf-8'))
            response = self.client.recv(4096).decode('utf-8')
            if response:
                return json.loads(response)
            return None
        except socket.error as e:
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
            init_data = pickle.loads(self.client.recv(65536))
            self.player_id = init_data["id"]
            self.initial_state = init_data["state"]
            print(f"Game Initialized! I am Player {self.player_id}")
            return True
        except Exception as e:
            print(f"Error loading initial game state: {e}")
            return False

    def send_action(self, action_data):
        """
        Sends an action to the server and receives the updated game state.
        action_data: dict like {"type": "place_tower", "tower_data": {...}}
        """
        try:
            self.client.send(pickle.dumps(action_data))
            return pickle.loads(self.client.recv(65536))
        except socket.error as e:
            print(f"Socket Error: {e}")

    def get_state(self):
        """Requests the current game state from the server."""
        try:
            self.client.send(pickle.dumps({"type": "get_state"}))
            return pickle.loads(self.client.recv(65536))
        except socket.error as e:
            print(f"Socket Error: {e}")
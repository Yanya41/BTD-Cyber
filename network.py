import socket
import pickle


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1"  # Change this to the Server's IP if playing on different PCs
        self.port = 5555
        self.addr = (self.server, self.port)

        # Initial connection data
        init_data = self.connect()
        self.player_id = init_data["id"]
        self.initial_state = init_data["state"]

    def connect(self):
        try:
            self.client.connect(self.addr)
            return pickle.loads(self.client.recv(4096))
        except Exception as e:
            print(f"Connection Error: {e}")

    def send(self, data):
        """
        Sends data to server and receives the latest game state back.
        """
        try:
            self.client.send(pickle.dumps(data))
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print(f"Socket Error: {e}")
import socket
import threading
import pickle
import time
import pygame
import game_logic  # Assuming game_logic is a separate module you have


server = "0.0.0.0"  # Listen on all available network interfaces
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(2)
print("Server Started. Waiting for connections...")

# The global game state that both players will see
game_state = {
    "towers": [],  # List of dicts: {"type": "goku", "x": 100, "y": 200, "owner": 1, "id": 0}
    "enemies": [],  # Shared enemy positions as dicts
    "projectiles": [],  # Projectiles as dicts
    "explosions": [],  # Explosions as dicts
    "cash": 1000,  # You can make this separate per player if you prefer
    "tower_id_counter": 0,
    "current_round": 1,
    "round_started": False,
    "last_spawn_time": 0,
    "spawn_queue": [],  # List of (enemy_dict, delay)
    "current_hp": 100,
    "abilities": {"ubw_cooldown": 0}
}


def threaded_client(conn, player_id):
    global game_state
    # Send the player their ID and the starting state
    conn.send(pickle.dumps({"id": player_id, "state": game_state}))

    while True:
        try:
            # Receive data from client
            data = pickle.loads(conn.recv(4096))

            if not data:
                print("Disconnected")
                break

            # Handle different request types
            if data["type"] == "place_tower":
                new_tower = data["tower_data"]
                new_tower["id"] = game_state["tower_id_counter"]
                game_state["towers"].append(new_tower)
                game_state["tower_id_counter"] += 1
                game_state["cash"] -= 150  # Basic cost logic

            elif data["type"] == "upgrade":
                t_id = data["tower_id"]
                for t in game_state["towers"]:
                    if t["id"] == t_id:
                        t["level"] = t.get("level", 1) + 1
                        game_state["cash"] -= 100

            elif data["type"] == "start_round":
                # Handle start round
                if not game_state["round_started"] and not game_state["enemies"]:
                    game_state["round_started"] = True
                    game_state["last_spawn_time"] = pygame.time.get_ticks()
                    # Prepare spawn_queue based on round
                    # This is simplified; need to implement prepare_round logic
                    game_state["spawn_queue"] = []  # Add enemies

            elif data["type"] == "ubw":
                if game_state["abilities"]["ubw_cooldown"] == 0:
                    game_state["abilities"]["ubw_cooldown"] = 60 * 60
                    # Create explosions on all enemies
                    for e in game_state["enemies"]:
                        game_state["explosions"].append({
                            'x': e['x'], 'y': e['y'], 'owner_id': None, 'dmg': 50,
                            'timer': 10, 'max_radius': 50, 'particles': [], 
                            'explosion_radius': 1, 'ubw': True, 'explosion': False
                        })

            # Always send back the latest state
            conn.sendall(pickle.dumps(game_state))

        except Exception as e:
            print(f"Error: {e}")
            break

    print("Lost connection")
    conn.close()


def game_loop():
    global game_state
    while True:
        game_logic.update_game_state(game_state)
        time.sleep(1/60)  # 60 FPS


# Start the game loop in a separate thread
threading.Thread(target=game_loop, daemon=True).start()

player_count = 1
while True:
    conn, addr = s.accept()
    print("Connected to:", addr)

    threading.Thread(target=threaded_client, args=(conn, player_count)).start()
    player_count += 1
import socket
import threading
import pickle
import time
import pygame
import game_logic  # Assuming game_logic is a separate module you have
import random

pygame.init()

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
            data = pickle.loads(conn.recv(65536))

            if not data:
                print("Disconnected")
                break

            # Handle different request types
            if data["type"] == "place_tower":
                new_tower = data["tower_data"]
                cost = new_tower.get("cost", 150)

                # --- NEW: Server strictly verifies you have enough cash! ---
                if game_state["cash"] >= cost:
                    new_tower["id"] = game_state["tower_id_counter"]
                    new_tower["owner"] = player_id
                    game_state["towers"].append(new_tower)
                    game_state["tower_id_counter"] += 1
                    game_state["cash"] -= cost
                else:
                    print(f"Player {player_id} attempted to buy a tower they couldn't afford!")



            elif data["type"] == "sync_upgrade":

                # 1. Sync the cash balance if it was included

                if "new_cash" in data:
                    game_state["cash"] = data["new_cash"]

                # 2. Find the tower and apply the specific updates

                for t in game_state["towers"]:

                    # --- NEW: Only allow the update if the requesting player is the owner! ---

                    if t["id"] == data["tower_id"] and t.get("owner") == player_id:

                        if "path_left" in data:
                            t["path_left"] = data["path_left"]

                        if "path_right" in data:
                            t["path_right"] = data["path_right"]

                        if "target_mode" in data:
                            t["target_mode"] = data["target_mode"]


            elif data["type"] == "start_round":

                if not game_state["round_started"] and not game_state["enemies"]:
                    game_state["round_started"] = True
                    game_state["last_spawn_time"] = pygame.time.get_ticks()
                    # --- NEW: Generate actual enemies! ---
                    round_num = game_state["current_round"]
                    num_enemies = 5 + (round_num * 2)  # Example scaling: 7 enemies on round 1, 9 on round 2...
                    new_queue = []
                    for i in range(num_enemies):
                        enemy_dict = {
                            "type": "Skeleton",
                            "x": 0, "y": 300,  # Matches the start of your Data().path_points
                            "hp": 1 + (round_num * 0.5),
                            "dmg": 1,
                            "speed": 2,
                            "target_index": 1,
                            "cash_price": 1,
                            "id": random.randint(1, 1000000)  # Give each a unique ID
                        }
                        delay = 1000  # Wait 1000ms (1 second) between spawns
                        new_queue.append((enemy_dict, delay))
                    game_state["spawn_queue"] = new_queue

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
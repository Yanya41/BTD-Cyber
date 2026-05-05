import socket
import threading
import database_manager
import pickle
import json
import time
import pygame
import game_logic
import random
import string

pygame.init()
database_manager.init_db()

server = "0.0.0.0"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(10)
print("Server Started. Waiting for connections...")

# --- LOBBY STORAGE ---
# Dictionary holding all active matches.
# Format: {"CODE": {"password": "123", "players": [conn1, conn2], "state": game_state_dict}}
active_lobbies = {}
online_users = {}

def generate_lobby_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def get_initial_game_state():
    """Returns a fresh, clean game state for a new lobby."""
    from game_data import Data

    # We grab the starting numbers from Data, but we put them in a
    # separate dictionary so this specific lobby has its own isolated health!
    return {
        "towers": [],
        "enemies": [],
        "projectiles": [],
        "explosions": [],
        "cash": Data().starting_cash,  # <--- Now grabs 10,000!
        "tower_id_counter": 0,
        "current_round": 1,
        "round_started": False,
        "last_spawn_time": 0,
        "spawn_queue": [],
        "current_hp": Data().starting_hp,  # <--- Now grabs 150!
        "abilities": {"ubw_cooldown": 0}
    }

def threaded_client(conn):
    authenticated = False
    in_lobby = False
    my_lobby_code = None
    player_id = None
    username = None

    # ==========================================
    # PHASE 1: AUTHENTICATION (JSON)
    # ==========================================
    while not authenticated:
        try:
            data = conn.recv(1024).decode('utf-8')
            if not data: break

            packet = json.loads(data)

            # Existing Login logic
            if packet.get('action') == 'login':
                user = packet.get('user')
                pwd = packet.get('password')

                if database_manager.verify_login(user, pwd):
                    if user in online_users:
                        conn.send(json.dumps({"status": "failed", "msg": "Account already online!"}).encode('utf-8'))
                    else:
                        authenticated = True
                        username = user
                        online_users[user] = conn
                        conn.send(json.dumps({"status": "success"}).encode('utf-8'))
                else:
                    conn.send(json.dumps({"status": "failed", "msg": "Invalid credentials"}).encode('utf-8'))


            # --- NEW: Register Logic ---
            elif packet.get('action') == 'register':
                user = packet.get('user')
                pwd = packet.get('password')

                # Check if registration works (fails if username already exists)
                if database_manager.register_user(user, pwd):
                    authenticated = True  # Auto-login after registering
                    username = user
                    conn.send(json.dumps({"status": "success"}).encode('utf-8'))
                    online_users[user] = conn
                else:
                    conn.send(json.dumps({"status": "failed", "msg": "Username already taken!"}).encode('utf-8'))

        except Exception as e:
            print("Auth Error:", e)
            break

    # ==========================================
    # PHASE 2: LOBBY SELECTION & WAITING ROOM (JSON)
    # ==========================================
    game_started = False

    # We stay in this JSON loop while they browse lobbies OR sit in the waiting room
    while authenticated and not game_started:
        try:
            data = conn.recv(1024).decode('utf-8')
            if not data: break

            packet = json.loads(data)
            action = packet.get('action')

            # --- 1. SEND SERVER LIST ---
            if action == 'get_lobbies':
                lobby_info = []
                for code, lobby in active_lobbies.items():
                    lobby_info.append({
                        "code": code,
                        "players": len(lobby['players']),
                        "locked": bool(lobby['password'])
                    })
                conn.send(json.dumps({"status": "success", "lobbies": lobby_info}).encode('utf-8'))

            # --- 2. CREATE A NEW LOBBY ---
            elif action == 'create_lobby':
                code = generate_lobby_code()
                active_lobbies[code] = {
                    "password": packet.get('password', ''),
                    "players": [conn],
                    "usernames": [username],  # Using the name saved during Phase 1 login!
                    "state": get_initial_game_state(),
                    "started": False
                }
                my_lobby_code = code
                player_id = 1  # Host is Player 1
                conn.send(json.dumps({"status": "success", "code": code}).encode('utf-8'))

            # --- 3. JOIN AN EXISTING LOBBY ---
            elif action == 'join_lobby':
                code = packet.get('code', '')
                pwd = packet.get('password', '')

                if code in active_lobbies and active_lobbies[code]['password'] == pwd:
                    if len(active_lobbies[code]['players']) < 4:  # Allow up to 4 players in a lobby
                        active_lobbies[code]['players'].append(conn)
                        active_lobbies[code]['usernames'].append(username)

                        my_lobby_code = code
                        player_id = len(active_lobbies[code]['players'])  # Guest is Player 2
                        conn.send(json.dumps({"status": "success", "code": code}).encode('utf-8'))
                    else:
                        conn.send(json.dumps({"status": "failed", "msg": "Lobby Full"}).encode('utf-8'))
                else:
                    conn.send(json.dumps({"status": "failed", "msg": "Invalid Code/Password"}).encode('utf-8'))

            # --- 4. THE HEARTBEAT (Update the waiting room) ---
            elif action == 'lobby_ping':
                if my_lobby_code in active_lobbies:
                    lobby = active_lobbies[my_lobby_code]

                    # If the host clicked start, tell the client to break out of the lobby menu
                    if lobby["started"]:
                        conn.send(json.dumps({"status": "success", "action": "launch_game"}).encode('utf-8'))
                        game_started = True
                    else:
                        # Otherwise, just send back the current list of names in the room
                        conn.send(json.dumps({"status": "success", "players": lobby["usernames"]}).encode('utf-8'))

            # --- 5. HOST CLICKS "START GAME" ---
            elif action == 'start_game':
                if my_lobby_code in active_lobbies:
                    lobby = active_lobbies[my_lobby_code]
                    lobby["started"] = True

                    # NEW: Split starting cash evenly based on player count
                    num_players = len(lobby['players'])
                    starting_pool = lobby["state"]["cash"]
                    # Create a dictionary mapping Player ID -> Wallet
                    lobby["state"]["player_cash"] = {i + 1: starting_pool // num_players for i in range(num_players)}

                    conn.send(json.dumps({"status": "success", "action": "launch_game"}).encode('utf-8'))
                    game_started = True

        except Exception as e:
            print("Lobby Error:", e)
            break

    # ==========================================
    # PHASE 3: THE GAME LOOP (PICKLE)
    # ==========================================
    if game_started:

        time.sleep(0.1)  # Short delay to ensure the client is ready to receive the pickle data
        # 1. Send the Pickle payload so the client's wait_for_game_start() succeeds!
        my_game_state = active_lobbies[my_lobby_code]["state"]
        conn.send(pickle.dumps({"id": player_id, "state": my_game_state}))
        # 2. Enter the actual BTD-Cyber gameplay loop
        while True:
            try:
                # Now we expect massive pickle bytes, not JSON
                data = pickle.loads(conn.recv(65536))
                if not data:
                    break
                # Pointer to this specific lobby's game state
                game_state = active_lobbies[my_lobby_code]["state"]
                # --- YOUR TOWER DEFENSE LOGIC GOES HERE ---
                if data["type"] == "place_tower":
                    new_tower = data["tower_data"]
                    cost = new_tower.get("cost", 150)
                    if game_state.get("player_cash", {}).get(player_id, 0) >= cost:
                        new_tower["id"] = game_state["tower_id_counter"]
                        new_tower["owner"] = player_id
                        game_state["towers"].append(new_tower)
                        game_state["tower_id_counter"] += 1
                        game_state["player_cash"][player_id] -= cost

                elif data["type"] == "sell_tower":
                    if "new_cash" in data:
                        game_state["player_cash"][player_id] = data["new_cash"]
                    for t in game_state["towers"]:
                        if t["id"] == data["tower_id"] and t.get("owner") == player_id:
                            game_state["towers"].remove(t)
                            break

                elif data["type"] == "sync_upgrade":
                    if "new_cash" in data:
                        game_state["player_cash"][player_id] = data["new_cash"]
                    for t in game_state["towers"]:
                        if t["id"] == data["tower_id"] and t.get("owner") == player_id:
                            if "path_left" in data: t["path_left"] = data["path_left"]
                            if "path_right" in data: t["path_right"] = data["path_right"]
                            if "target_mode" in data: t["target_mode"] = data["target_mode"]
                # ... (Paste any other game logic you have here like start_round, ubw, etc...) ...
                # Send back the newly updated lobby state to the client 60 times a second
                elif data["type"] == "start_round":
                    # Only allow starting if a round isn't already happening
                    if not game_state["round_started"] and len(game_state["enemies"]) == 0:
                        from rounds import Round
                        # Use your existing rounds.py logic to get the enemy list
                        r = Round()
                        r.current_round = game_state["current_round"]
                        r.prepare_round()
                        # Convert your Skeleton objects into pure data dicts for the server!
                        game_state["spawn_queue"] = [(enemy_obj.to_dict(), delay) for enemy_obj, delay in r.spawn_queue]
                        game_state["round_started"] = True
                        game_state["last_spawn_time"] = pygame.time.get_ticks()

                elif data["type"] == "ubw":
                    if game_state["abilities"]["ubw_cooldown"] == 0:
                        game_state["abilities"]["ubw_cooldown"] = 900  # 15 second cooldown
                        for e in game_state["enemies"]:
                            e["hp"] -= 100
                            game_state["explosions"].append({"x": e["x"], "y": e["y"], "timer": 10, "dmg":0, "max_radius":70})  # Add explosion effect
                conn.sendall(pickle.dumps(game_state))
            except Exception as e:
                print(f"Game Loop Error: {e}")
                break
    print(f"Lost connection. (Lobby: {my_lobby_code})")
    # Clean up the lobby if someone disconnects so it disappears from the server list
    if my_lobby_code in active_lobbies:
        if conn in active_lobbies[my_lobby_code]['players']:
            active_lobbies[my_lobby_code]['players'].remove(conn)
        if len(active_lobbies[my_lobby_code]['players']) == 0:
            del active_lobbies[my_lobby_code]
            print(f"Closed empty lobby {my_lobby_code}")

    if username in online_users:
        del online_users[username]
        print(f"{username} has gone offline.")
    conn.close()


# ==========================================
# MASTER GAME LOGIC THREAD
# ==========================================
def master_game_loop():
    """Runs continuously, updating the state of ALL active lobbies."""
    while True:
        # Create a list of keys to safely iterate while the dictionary might change
        for lobby_code in list(active_lobbies.keys()):
            lobby = active_lobbies.get(lobby_code)
            if lobby:
                # Update this specific lobby's game state
                old_global_cash = lobby["state"]["cash"]

                game_logic.update_game_state(lobby["state"])
                if lobby.get("started") and "player_cash" in lobby["state"]:
                    new_global_cash = lobby["state"]["cash"]
                    # If game_logic.py increased the global cash...
                    if new_global_cash > old_global_cash:
                        gained = new_global_cash - old_global_cash
                        num_players = len(lobby["players"])
                        split_amount = gained / num_players

                        # Divide it out to all players in the lobby!
                        for pid in lobby["state"]["player_cash"]:
                            lobby["state"]["player_cash"][pid] += split_amount

        time.sleep(1 / 60)


threading.Thread(target=master_game_loop, daemon=True).start()

# Accept connections
while True:
    conn, addr = s.accept()
    print("Connected to:", addr)
    threading.Thread(target=threaded_client, args=(conn,)).start()
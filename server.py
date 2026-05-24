import socket
import threading
import database_manager
import pickle
import json
import time
import struct
import random
import string
import game_logic

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

active_lobbies = {}
online_users = {}

TOWER_COSTS = {"goku": 550, "archer": 600, "ayanokoji": 1000}


def generate_lobby_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def get_initial_game_state():
    from game_data import Data
    return {
        "towers": [],
        "enemies": [],
        "projectiles": [],
        "explosions": [],
        "turned_enemies": [],
        "cash": Data().starting_cash,
        "tower_id_counter": 0,
        "current_round": 1,
        "round_started": False,
        "last_spawn_time": 0,
        "spawn_queue": [],
        "current_hp": Data().starting_hp,
        "abilities": {"ubw_cooldown": 0}
    }


# ==========================================
# TCP FRAMING HELPERS
# ==========================================

def send_msg(conn, data: bytes):
    header = struct.pack('>I', len(data))
    conn.sendall(header + data)


def recv_msg(conn):
    raw_header = _recv_exactly(conn, 4)
    if not raw_header:
        return None
    length = struct.unpack('>I', raw_header)[0]
    return _recv_exactly(conn, length)


def _recv_exactly(conn, n: int):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def send_json(conn, payload: dict):
    send_msg(conn, json.dumps(payload).encode('utf-8'))


def recv_json(conn):
    data = recv_msg(conn)
    if not data:
        return None
    return json.loads(data.decode('utf-8'))


def send_pickle(conn, payload):
    send_msg(conn, pickle.dumps(payload))


def recv_pickle(conn):
    data = recv_msg(conn)
    if not data:
        return None
    return pickle.loads(data)


# ==========================================
# CLIENT THREAD
# ==========================================

def threaded_client(conn):
    authenticated = False
    my_lobby_code = None
    player_id = None
    username = None

    # ==========================================
    # PHASE 1: AUTHENTICATION
    # ==========================================
    while not authenticated:
        try:
            packet = recv_json(conn)
            if not packet:
                break

            if packet.get('action') == 'login':
                user = packet.get('user')
                pwd = packet.get('password')

                if database_manager.verify_login(user, pwd):
                    if user in online_users:
                        send_json(conn, {"status": "failed", "msg": "Account already online!"})
                    else:
                        authenticated = True
                        username = user
                        online_users[user] = conn
                        send_json(conn, {"status": "success"})
                else:
                    send_json(conn, {"status": "failed", "msg": "Invalid credentials"})

            elif packet.get('action') == 'register':
                user = packet.get('user')
                pwd = packet.get('password')

                if database_manager.register_user(user, pwd):
                    authenticated = True
                    username = user
                    online_users[user] = conn
                    send_json(conn, {"status": "success"})
                else:
                    send_json(conn, {"status": "failed", "msg": "Username already taken!"})

        except Exception as e:
            print("Auth Error:", e)
            break

    # ==========================================
    # PHASE 2: LOBBY SELECTION & WAITING ROOM
    # ==========================================
    game_started = False

    while authenticated and not game_started:
        try:
            packet = recv_json(conn)
            if not packet:
                break

            action = packet.get('action')

            if action == 'get_lobbies':
                lobby_info = [
                    {
                        "code": code,
                        "players": len(lobby['players']),
                        "locked": bool(lobby['password'])
                    }
                    for code, lobby in active_lobbies.items()
                ]
                send_json(conn, {"status": "success", "lobbies": lobby_info})

            elif action == 'create_lobby':
                code = generate_lobby_code()
                active_lobbies[code] = {
                    "password": packet.get('password', ''),
                    "players": [conn],
                    "usernames": [username],
                    "state": get_initial_game_state(),
                    "started": False,
                    "last_tick": time.time()
                }
                my_lobby_code = code
                player_id = 1
                send_json(conn, {"status": "success", "code": code})

            elif action == 'join_lobby':
                code = packet.get('code', '')
                pwd = packet.get('password', '')

                if code in active_lobbies and active_lobbies[code]['password'] == pwd:
                    if len(active_lobbies[code]['players']) < 4:
                        active_lobbies[code]['players'].append(conn)
                        active_lobbies[code]['usernames'].append(username)
                        my_lobby_code = code
                        player_id = len(active_lobbies[code]['players'])
                        send_json(conn, {"status": "success", "code": code})
                    else:
                        send_json(conn, {"status": "failed", "msg": "Lobby Full"})
                else:
                    send_json(conn, {"status": "failed", "msg": "Invalid Code/Password"})

            elif action == 'lobby_ping':
                if my_lobby_code in active_lobbies:
                    lobby = active_lobbies[my_lobby_code]
                    if lobby["started"]:
                        send_json(conn, {"status": "success", "action": "launch_game"})
                        game_started = True
                    else:
                        send_json(conn, {"status": "success", "players": lobby["usernames"]})

            elif action == 'start_game':
                if my_lobby_code in active_lobbies:
                    lobby = active_lobbies[my_lobby_code]
                    lobby["started"] = True

                    num_players = len(lobby['players'])
                    starting_pool = lobby["state"]["cash"]
                    lobby["state"]["player_cash"] = {
                        i + 1: starting_pool // num_players for i in range(num_players)
                    }

                    send_json(conn, {"status": "success", "action": "launch_game"})
                    game_started = True

        except Exception as e:
            print("Lobby Error:", e)
            break

    # ==========================================
    # PHASE 3: THE GAME LOOP
    # ==========================================
    if game_started:
        time.sleep(0.1)
        my_game_state = active_lobbies[my_lobby_code]["state"]
        send_pickle(conn, {"id": player_id, "state": my_game_state})

        while True:
            try:
                data = recv_pickle(conn)
                if not data:
                    break

                game_state = active_lobbies[my_lobby_code]["state"]

                if data["type"] == "place_tower":
                    new_tower = data["tower_data"]
                    tower_type = new_tower.get("tower_type")

                    # Server looks up cost — client cannot spoof this
                    cost = TOWER_COSTS.get(tower_type, 999999)

                    if game_state.get("player_cash", {}).get(player_id, 0) >= cost:
                        new_tower["id"] = game_state["tower_id_counter"]
                        new_tower["owner"] = player_id
                        new_tower["cost"] = cost  # Overwrite with real value
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

                elif data["type"] == "start_round":
                    if not game_state["round_started"] and len(game_state["enemies"]) == 0:
                        from rounds import Round
                        r = Round()
                        r.current_round = game_state["current_round"]
                        r.prepare_round()
                        game_state["spawn_queue"] = [
                            (enemy_obj.to_dict(), delay) for enemy_obj, delay in r.spawn_queue
                        ]
                        game_state["round_started"] = True
                        game_state["last_spawn_time"] = time.time() * 1000

                elif data["type"] == "ubw":
                    if game_state["abilities"]["ubw_cooldown"] == 0:
                        game_state["abilities"]["ubw_cooldown"] = 900
                        for e in game_state["enemies"]:
                            e["hp"] -= 100
                            game_state["explosions"].append({
                                "x": e["x"], "y": e["y"],
                                "timer": 10, "dmg": 0, "max_radius": 70
                            })

                send_pickle(conn, game_state)

            except Exception as e:
                print(f"Game Loop Error: {e}")
                break

    print(f"Lost connection. (Lobby: {my_lobby_code})")

    # Clean up
    if my_lobby_code in active_lobbies:
        lobby = active_lobbies[my_lobby_code]
        if conn in lobby['players']:
            lobby['players'].remove(conn)
        if len(lobby['players']) == 0:
            del active_lobbies[my_lobby_code]
            print(f"Closed empty lobby {my_lobby_code}")

    # FIX: Only delete from online_users if the connection matches
    # so a reconnect doesn't accidentally wipe the new session
    if username and online_users.get(username) == conn:
        del online_users[username]
        print(f"{username} has gone offline.")

    conn.close()


# ==========================================
# MASTER GAME LOGIC THREAD
# ==========================================

def master_game_loop():
    """
    Runs continuously, updating ALL active lobbies.
    FIX: Each lobby tracks its own last_tick so the loop stays
    fair regardless of how many lobbies are running.
    """
    TICK_RATE = 1 / 60  # 60 fps target

    while True:
        now = time.time()

        for lobby_code in list(active_lobbies.keys()):
            lobby = active_lobbies.get(lobby_code)
            if not lobby or not lobby.get("started"):
                continue

            # Only tick this lobby if enough time has passed
            if now - lobby.get("last_tick", 0) < TICK_RATE:
                continue

            lobby["last_tick"] = now
            old_cash = lobby["state"]["cash"]

            game_logic.update_game_state(lobby["state"])

            if "player_cash" in lobby["state"]:
                new_cash = lobby["state"]["cash"]
                if new_cash > old_cash:
                    gained = new_cash - old_cash
                    num_players = len(lobby["players"])
                    if num_players > 0:
                        split = gained / num_players
                        for pid in lobby["state"]["player_cash"]:
                            lobby["state"]["player_cash"][pid] += split

        # Small sleep to avoid hammering the CPU between checks
        time.sleep(0.001)

threading.Thread(target=master_game_loop, daemon=True).start()

while True:
    conn, addr = s.accept()
    print("Connected to:", addr)
    threading.Thread(target=threaded_client, args=(conn,)).start()

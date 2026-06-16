import math
import time
import random

# Global instance reference for game data
from game_data import Data

_data = Data()

TOWER_COSTS = {"goku": 550, "archer": 600, "ayanokoji": 1000}
WINNING_ROUND = 3


def update_round(game_state):
    """Update round spawning logic."""
    if game_state.get("game_won", False):
        return

    if not game_state["round_started"]:
        return

    now = time.time() * 1000

    if game_state["spawn_queue"]:
        enemy_dict, delay = game_state["spawn_queue"][0]
        if now - game_state["last_spawn_time"] >= delay:
            game_state["enemies"].append(enemy_dict)
            game_state["spawn_queue"].pop(0)
            game_state["last_spawn_time"] = now

    if not game_state["spawn_queue"] and not game_state["enemies"]:
        game_state["round_started"] = False

        if game_state["current_round"] == WINNING_ROUND:
            game_state["game_won"] = True

        game_state["current_round"] += 1
        game_state["cash"] += 100


def update_enemies(game_state):
    """Update enemy positions and handle leaks."""
    for e in game_state["enemies"][:]:
        if e["target_index"] >= len(_data.path_points):
            game_state["current_hp"] -= e["dmg"]
            game_state["enemies"].remove(e)
            continue

        target_x, target_y = _data.path_points[e["target_index"]]
        dx = target_x - e["x"]
        dy = target_y - e["y"]
        dist = math.hypot(dx, dy)

        if dist != 0:
            e["x"] += (dx / dist) * e["speed"]
            e["y"] += (dy / dist) * e["speed"]

        if dist < e["speed"]:
            e["target_index"] += 1


def update_towers(game_state):
    """Scan targets and trigger tower attacks based on current upgrade states."""
    now = time.time() * 1000

    for t in game_state["towers"]:
        # --- FIX: Fallback wrapper to catch any variation of client upgrade keys ---
        p_left = t.get("upgrade_left", t.get("path_left", t.get("left_path", 0)))
        p_right = t.get("upgrade_right", t.get("path_right", t.get("right_path", 0)))

        if t["tower_type"] == "goku":
            cooldown = t.get("base_speed", 1500) - (200 if p_left >= 1 else 0)
            attack_range = t.get("base_range", 250)

        elif t["tower_type"] == "ayanokoji":
            # Upgrades dynamically adjust attack speed and range
            cooldown = t.get("base_speed", 2000) - (p_right * 150)
            attack_range = t.get("base_range", 300) + (p_right * 50)

        else:  # archer
            cooldown = t.get("base_speed", 1000) - (200 if p_left >= 1 else 0)
            attack_range = t.get("base_range", 1000)

        target = None
        if game_state["enemies"]:
            in_range = [
                e for e in game_state["enemies"]
                if math.hypot(t["x"] - e["x"], t["y"] - e["y"]) <= attack_range
            ]

            if in_range:
                if t.get("target_mode", "first") == "strong":
                    target = max(in_range, key=lambda e: e.get("hp", 0))
                else:
                    target = max(in_range, key=lambda e: e.get("target_index", 0))

        if target:
            dx, dy = target["x"] - t["x"], target["y"] - t["y"]
            t["angle"] = math.degrees(math.atan2(-dy, dx))

            if now - t.get("last_shot_time", 0) > cooldown:
                t["last_shot_time"] = now
                t["just_shot"] = True
                spawn_attack(game_state, t, target)
            else:
                t["just_shot"] = False
        else:
            t["just_shot"] = False


def spawn_attack(game_state, tower, target):
    """Instantiate attacks and pass upgrade flags directly down to projectiles."""
    # --- FIX: Robust lookup for upgrade properties on spawn ---
    p_left = tower.get("upgrade_left", tower.get("path_left", tower.get("left_path", 0)))
    p_right = tower.get("upgrade_right", tower.get("path_right", tower.get("right_path", 0)))

    if tower["tower_type"] == "goku":
        dx, dy = target["x"] - tower["x"], target["y"] - tower["y"]
        angle = math.degrees(math.atan2(-dy, dx))
        rad = math.radians(-angle)

        base_dmg = tower.get("base_dmg", 2)
        base_pierce = tower.get("base_pierce", 2)
        base_size = tower.get("base_size", 10)

        proj = {
            "tower_id": tower["id"],
            "x": tower["x"], "y": tower["y"],
            "vx": math.cos(rad) * 8, "vy": math.sin(rad) * 8,
            "dmg": base_dmg + (5 if p_right >= 2 else 0),
            "pierce": base_pierce + (2 if p_right >= 1 else 0),
            "size": base_size + (10 if p_left >= 2 else 0),
            "seeking": True if p_right >= 3 else False,
            "returns": True if p_left >= 3 else False,
            "has_returned": False,
            "speed": 8,
            "hit_enemies": [],
            "proj_type": "normal"
        }
        game_state["projectiles"].append(proj)

    elif tower["tower_type"] == "ayanokoji":
        dx, dy = target["x"] - tower["x"], target["y"] - tower["y"]
        angle = math.degrees(math.atan2(-dy, dx))
        rad = math.radians(-angle)

        turned_pierce = (
                3 +
                (2 if p_left >= 1 else 0) +
                (3 if p_left >= 2 else 0) +
                (5 if p_left >= 3 else 0)
        )
        proj_speed = 8 + (2 if p_right >= 1 else 0)

        proj = {
            "tower_id": tower["id"],
            "x": tower["x"], "y": tower["y"],
            "vx": math.cos(rad) * proj_speed,
            "vy": math.sin(rad) * proj_speed,
            "dmg": 0,
            "pierce": 1,
            "size": 8,
            "seeking": False,
            "returns": False,
            "has_returned": False,
            "speed": proj_speed,
            "hit_enemies": [],
            "proj_type": "manipulation",
            "turned_pierce": turned_pierce,
            "upgrade_left": p_left,
            "upgrade_right": p_right
        }
        game_state["projectiles"].append(proj)

    elif tower["tower_type"] == "archer":
        base_dmg = tower.get("base_dmg", 5)
        exp_dmg = base_dmg + (5 if p_left >= 1 else 0) + (10 if p_left >= 2 else 0)
        exp_radius = 50 + (25 if p_right >= 3 else 0)

        game_state["explosions"].append({
            "tower_id": tower["id"],
            "x": target["x"], "y": target["y"],
            "timer": 10,
            "dmg": exp_dmg,
            "max_radius": exp_radius
        })


def update_projectiles(game_state):
    """Update projectile movements and manage scaled collision damage tracking."""
    for p in game_state["projectiles"][:]:

        if p.get("seeking") and game_state["enemies"]:
            target = min(
                game_state["enemies"],
                key=lambda e: math.hypot(p["x"] - e["x"], p["y"] - e["y"])
            )
            dx, dy = target["x"] - p["x"], target["y"] - p["y"]
            dist = math.hypot(dx, dy)
            if dist > 0:
                p["vx"] += (dx / dist) * 0.6
                p["vy"] += (dy / dist) * 0.6
                mag = math.hypot(p["vx"], p["vy"])
                p["vx"] = (p["vx"] / mag) * p.get("speed", 8)
                p["vy"] = (p["vy"] / mag) * p.get("speed", 8)

        p["x"] += p["vx"]
        p["y"] += p["vy"]

        if p.get("returns") and not p.get("has_returned"):
            if p["x"] < -50 or p["x"] > 1970 or p["y"] < -50 or p["y"] > 1130:
                p["vx"] *= -1
                p["vy"] *= -1
                p["has_returned"] = True

        # --- MANIPULATION PROJECTILE (Ayanokoji) ---
        if p.get("proj_type") == "manipulation":
            hit = False
            p_left = p.get("upgrade_left", 0)
            p_right = p.get("upgrade_right", 0)

            for e in game_state["enemies"][:]:
                if math.hypot(p["x"] - e["x"], p["y"] - e["y"]) < 45:
                    # --- FIX: Concrete conditions for progressive conversions ---
                    can_manipulate = False
                    if e.get("type") == "Skeleton":
                        can_manipulate = True
                    elif e.get("type") == "ShieldedSkeleton" and p_left >= 1:
                        can_manipulate = True
                    elif e.get("type") == "SkeletonBarrel" and p_left >= 3:
                        can_manipulate = True

                    if can_manipulate:
                        turned = {
                            "id": _next_id(),
                            "tower_id": p.get("tower_id"),
                            "x": e["x"],
                            "y": e["y"],
                            "speed": e["speed"] * (1.5 if p_right >= 1 else 1.0),
                            "target_index": e["target_index"],
                            "pierce": p.get("turned_pierce", 3),
                            "hit_enemies": [],
                            "type": "TurnedSkeleton",
                            "can_hit_barrel": p_right >= 3
                        }
                        game_state["turned_enemies"].append(turned)
                        game_state["enemies"].remove(e)
                        if p in game_state["projectiles"]:
                            game_state["projectiles"].remove(p)
                        hit = True
                        break
            if hit:
                continue

            if p["x"] < -100 or p["x"] > 2020 or p["y"] < -100 or p["y"] > 1180:
                if p in game_state["projectiles"]:
                    game_state["projectiles"].remove(p)
            continue

        # NORMAL COLLISION LOGIC
        hit_occurred = False
        for e in game_state["enemies"]:
            if e["id"] not in p.get("hit_enemies", []) and math.hypot(p["x"] - e["x"], p["y"] - e["y"]) < 45:

                # --- FIX: Cap damage credit to the exact health remaining ---
                actual_dmg = max(0, min(p["dmg"], e["hp"]))
                e["hp"] -= p["dmg"]

                if "tower_id" in p and actual_dmg > 0:
                    for t in game_state["towers"]:
                        if t["id"] == p["tower_id"]:
                            t["damage_dealt"] += actual_dmg

                p["hit_enemies"].append(e["id"])
                p["pierce"] -= 1
                hit_occurred = True
                if p["pierce"] <= 0:
                    if p in game_state["projectiles"]:
                        game_state["projectiles"].remove(p)
                break

        if hit_occurred:
            continue

        if not p.get("returns") or p.get("has_returned"):
            if p["x"] < -100 or p["x"] > 2020 or p["y"] < -100 or p["y"] > 1180:
                if p in game_state["projectiles"]:
                    game_state["projectiles"].remove(p)


def update_turned_skeletons(game_state):
    """Move turned skeletons backwards, tracking non-excess damage profiles."""
    for ts in game_state["turned_enemies"][:]:
        target_index = ts["target_index"] - 1

        if target_index < 0:
            game_state["turned_enemies"].remove(ts)
            continue

        target_x, target_y = _data.path_points[target_index]
        dx = target_x - ts["x"]
        dy = target_y - ts["y"]
        dist = math.hypot(dx, dy)

        if dist != 0:
            ts["x"] += (dx / dist) * ts["speed"]
            ts["y"] += (dy / dist) * ts["speed"]

        if dist < ts["speed"]:
            ts["target_index"] -= 1

        for e in game_state["enemies"][:]:
            if e["id"] not in ts["hit_enemies"]:
                if math.hypot(ts["x"] - e["x"], ts["y"] - e["y"]) < 40:
                    if e.get("type") == "SkeletonBarrel" and not ts.get("can_hit_barrel"):
                        continue

                    # --- FIX: Max damage tracking for converted minions ---
                    actual_dmg = max(0, min(1, e["hp"]))
                    e["hp"] -= 1

                    if "tower_id" in ts and actual_dmg > 0:
                        for t in game_state["towers"]:
                            if t["id"] == ts["tower_id"]:
                                t["damage_dealt"] += actual_dmg

                    ts["hit_enemies"].append(e["id"])
                    ts["pierce"] -= 1
                    if ts["pierce"] <= 0:
                        if ts in game_state["turned_enemies"]:
                            game_state["turned_enemies"].remove(ts)
                        break


def update_explosions(game_state):
    """Process area explosions and register non-excess combat data."""
    for ex in game_state["explosions"][:]:
        ex["timer"] -= 1
        if ex["timer"] == 5:
            for e in game_state["enemies"]:
                if math.hypot(e["x"] - ex["x"], e["y"] - ex["y"]) < ex["max_radius"]:

                    # --- FIX: Prevent excess damage additions from AoE bursts ---
                    actual_dmg = max(0, min(ex["dmg"], e["hp"]))
                    e["hp"] -= ex["dmg"]

                    if "tower_id" in ex and actual_dmg > 0:
                        for t in game_state["towers"]:
                            if t["id"] == ex["tower_id"]:
                                t["damage_dealt"] += actual_dmg
        if ex["timer"] <= 0:
            game_state["explosions"].remove(ex)


def remove_dead_enemies(game_state):
    """Clean up dead targets and manage split logic."""
    surviving = []
    new_spawns = []

    for e in game_state["enemies"]:
        if e["hp"] > 0:
            surviving.append(e)
        else:
            game_state["cash"] += e.get("cash_price", 1)

            if e.get("type") == "SkeletonBarrel":
                for _ in range(3):
                    new_skel = {
                        "x": e["x"] + random.randint(-15, 15),
                        "y": e["y"] + random.randint(-15, 15),
                        "speed": 3,
                        "target_index": e["target_index"],
                        "hp": 1,
                        "dmg": 1,
                        "cash_price": 1,
                        "type": "Skeleton",
                        "id": _next_id()
                    }
                    new_spawns.append(new_skel)

    game_state["enemies"] = surviving + new_spawns


def update_game_state(game_state):
    """Main core engine update tick loop."""
    update_round(game_state)
    update_enemies(game_state)
    update_towers(game_state)
    update_projectiles(game_state)
    update_explosions(game_state)
    update_turned_skeletons(game_state)
    remove_dead_enemies(game_state)
    game_state["abilities"]["ubw_cooldown"] = max(0, game_state["abilities"]["ubw_cooldown"] - 1)


_id_counter = 0


def _next_id():
    global _id_counter
    _id_counter += 1
    return _id_counter
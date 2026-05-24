import math
import time
import random

# --- FIX: One instance, reused forever. No more Data() in the hot path ---
from game_data import Data
_data = Data()

# --- FIX: Server-side authoritative costs ---
TOWER_COSTS = {"goku": 550, "archer": 600, "ayanokoji": 1000}


def update_round(game_state):
    """Update round spawning logic."""
    if not game_state["round_started"]:
        return

    # --- FIX: Use time.time() instead of pygame.time.get_ticks() ---
    now = time.time() * 1000

    if game_state["spawn_queue"]:
        enemy_dict, delay = game_state["spawn_queue"][0]
        if now - game_state["last_spawn_time"] >= delay:
            game_state["enemies"].append(enemy_dict)
            game_state["spawn_queue"].pop(0)
            game_state["last_spawn_time"] = now

    if not game_state["spawn_queue"] and not game_state["enemies"]:
        game_state["round_started"] = False
        game_state["current_round"] += 1
        game_state["cash"] += 100


def update_enemies(game_state):
    """Update enemy positions and handle leaks."""
    # --- FIX: Use the module-level _data, not Data() every frame ---
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
    # --- FIX: Use time.time() instead of pygame.time.get_ticks() ---
    now = time.time() * 1000

    for t in game_state["towers"]:
        if t["tower_type"] == "goku":
            cooldown = 1500 - (t.get("path_left", 0) * 200)
            attack_range = 250

        elif t["tower_type"] == "ayanokoji":
            cooldown = 2000 - (t.get("path_right", 0) * 150)
            attack_range = 300 + (t.get("path_right", 0) * 50)

        else:  # archer
            cooldown = 1000 - (t.get("path_left", 0) * 100)
            attack_range = 1000

        # Scan for enemies in range
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
    p_left = tower.get("path_left", 0)
    p_right = tower.get("path_right", 0)

    if tower["tower_type"] == "goku":
        dx, dy = target["x"] - tower["x"], target["y"] - tower["y"]
        angle = math.degrees(math.atan2(-dy, dx))
        rad = math.radians(-angle)

        base_dmg = tower.get("base_dmg", 2)
        base_pierce = tower.get("base_pierce", 2)
        base_size = tower.get("base_size", 10)

        proj = {
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

        # --- FIX: Use max_radius correctly so upgraded explosions damage the right area ---
        exp_radius = 50 + (25 if p_right >= 3 else 0)

        game_state["explosions"].append({
            "x": target["x"], "y": target["y"],
            "timer": 10,
            "dmg": exp_dmg,
            "max_radius": exp_radius
        })


def update_projectiles(game_state):
    """Update projectiles, handle collisions, seeking, and returning."""
    for p in game_state["projectiles"][:]:

        # SEEKING LOGIC
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

        # Move
        p["x"] += p["vx"]
        p["y"] += p["vy"]

        # RETURN LOGIC
        if p.get("returns") and not p.get("has_returned"):
            if p["x"] < -50 or p["x"] > 1970 or p["y"] < -50 or p["y"] > 1130:
                p["vx"] *= -1
                p["vy"] *= -1
                p["has_returned"] = True

        # --- MANIPULATION PROJECTILE (Ayanokoji) ---
        if p.get("proj_type") == "manipulation":
            hit = False
            for e in game_state["enemies"][:]:
                if math.hypot(p["x"] - e["x"], p["y"] - e["y"]) < 45:
                    can_manipulate = (
                        e.get("type") == "Skeleton" or
                        (p.get("upgrade_left", 0) >= 3 and e.get("type") == "ShieldedSkeleton")
                    )
                    if can_manipulate:
                        turned = {
                            "id": _next_id(),
                            "x": e["x"],
                            "y": e["y"],
                            "speed": e["speed"] * (1.5 if p.get("upgrade_right", 0) >= 1 else 1.0),
                            "target_index": e["target_index"],
                            "pierce": p.get("turned_pierce", 3),
                            "hit_enemies": [],
                            "type": "TurnedSkeleton",
                            "can_hit_barrel": p.get("upgrade_right", 0) >= 3
                        }
                        game_state["turned_enemies"].append(turned)  # CHANGED
                        game_state["enemies"].remove(e)
                        if p in game_state["projectiles"]:
                            game_state["projectiles"].remove(p)
                        hit = True
                        break
            if hit:
                continue

            # Remove off-screen manipulation projectile
            if p["x"] < -100 or p["x"] > 2020 or p["y"] < -100 or p["y"] > 1180:
                if p in game_state["projectiles"]:
                    game_state["projectiles"].remove(p)
            continue

        # NORMAL COLLISION LOGIC
        hit_occurred = False
        for e in game_state["enemies"]:
            if e["id"] not in p.get("hit_enemies", []) and math.hypot(p["x"] - e["x"], p["y"] - e["y"]) < 45:
                e["hp"] -= p["dmg"]
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
    """Move turned skeletons backwards along the path, damaging enemies they collide with."""
    for ts in game_state["turned_enemies"][:]:  # CHANGED

        target_index = ts["target_index"] - 1

        if target_index < 0:
            game_state["turned_enemies"].remove(ts)  # CHANGED
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

        # Collision with enemies
        for e in game_state["enemies"][:]:
            if e["id"] not in ts["hit_enemies"]:
                if math.hypot(ts["x"] - e["x"], ts["y"] - e["y"]) < 40:
                    if e.get("type") == "SkeletonBarrel" and not ts.get("can_hit_barrel"):
                        continue
                    e["hp"] -= 1
                    ts["hit_enemies"].append(e["id"])
                    ts["pierce"] -= 1
                    if ts["pierce"] <= 0:
                        if ts in game_state["turned_enemies"]:  # CHANGED
                            game_state["turned_enemies"].remove(ts)  # CHANGED
                        break


def update_explosions(game_state):
    """Update explosions and damage enemies."""
    for ex in game_state["explosions"][:]:
        ex["timer"] -= 1
        if ex["timer"] == 5:
            for e in game_state["enemies"]:
                # --- FIX: Use max_radius for damage check, not hardcoded 50 ---
                if math.hypot(e["x"] - ex["x"], e["y"] - ex["y"]) < ex["max_radius"]:
                    e["hp"] -= ex["dmg"]
        if ex["timer"] <= 0:
            game_state["explosions"].remove(ex)


def remove_dead_enemies(game_state):
    """Remove dead enemies, give cash, and handle Barrel splitting."""
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
                        # --- FIX: Use the safe incrementing ID counter ---
                        "id": _next_id()
                    }
                    new_spawns.append(new_skel)

    game_state["enemies"] = surviving + new_spawns


def update_game_state(game_state):
    """Main update function."""
    update_round(game_state)
    update_enemies(game_state)
    update_towers(game_state)
    update_projectiles(game_state)
    update_explosions(game_state)
    update_turned_skeletons(game_state)
    remove_dead_enemies(game_state)
    game_state["abilities"]["ubw_cooldown"] = max(0, game_state["abilities"]["ubw_cooldown"] - 1)


# --- FIX: Safe server-side ID counter, no more random collision risk ---
_id_counter = 0

def _next_id():
    global _id_counter
    _id_counter += 1
    return _id_counter
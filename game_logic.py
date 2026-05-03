import math
import random
import pygame
from game_data import Data

# Assuming we have the classes imported or recreated as dicts
# For now, we'll simulate logic with dicts

def update_round(game_state):
    """Update round spawning logic."""
    if not game_state["round_started"]:
        return

    now = pygame.time.get_ticks()

    # Spawn enemies from queue
    if game_state["spawn_queue"]:
        enemy_dict, delay = game_state["spawn_queue"][0]
        if now - game_state["last_spawn_time"] >= delay:
            game_state["enemies"].append(enemy_dict)
            game_state["spawn_queue"].pop(0)
            game_state["last_spawn_time"] = now

    # Check if round is over
    if not game_state["spawn_queue"] and not game_state["enemies"]:
        game_state["round_started"] = False
        game_state["current_round"] += 1
        game_state["cash"] += 100

def update_enemies(game_state):
    """Update enemy positions and handle leaks."""
    data = Data()
    for e in game_state["enemies"][:]:
        if e["target_index"] >= len(data.path_points):
            game_state["current_hp"] -= e["dmg"]
            game_state["enemies"].remove(e)
            continue

        target_x, target_y = data.path_points[e["target_index"]]
        dx = target_x - e["x"]
        dy = target_y - e["y"]
        dist = math.hypot(dx, dy)

        if dist != 0:
            dx_norm = dx / dist
            dy_norm = dy / dist
            e["x"] += dx_norm * e["speed"]
            e["y"] += dy_norm * e["speed"]

        if dist < e["speed"]:
            e["target_index"] += 1


# In game_logic.py
def update_towers(game_state):
    now = pygame.time.get_ticks()

    for t in game_state["towers"]:
        # Set stats based on tower type
        if t["tower_type"] == "goku":
            cooldown = 1500 - (t.get("path_left", 0) * 200)
            attack_range = 250
        else:  # archer
            cooldown = 1000 - (t.get("path_left", 0) * 100)
            attack_range = 1000

        # 1. Scan for enemies in range
        target = None
        if game_state["enemies"]:
            in_range_enemies = [e for e in game_state["enemies"] if
                                math.hypot(t["x"] - e["x"], t["y"] - e["y"]) <= attack_range]

            if in_range_enemies:
                # Apply First vs Strong targeting logic
                if t.get("target_mode", "first") == "strong":
                    target = max(in_range_enemies, key=lambda e: e.get("hp", 0))
                else:
                    target = max(in_range_enemies, key=lambda e: e.get("target_index", 0))

        # 2. Look at the target and shoot!
        if target:
            dx, dy = target["x"] - t["x"], target["y"] - t["y"]
            t["angle"] = math.degrees(math.atan2(-dy, dx))  # Update the tower's angle in the master state!

            # Check cooldown
            if now - t.get("last_shot_time", 0) > cooldown:
                t["last_shot_time"] = now
                t["just_shot"] = True  # Send a signal to the client to play the animation!
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

        # --- FIXED: Pull the base stats dynamically from the blueprint! ---
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
            "hit_enemies": []
        }
        game_state["projectiles"].append(proj)

    elif tower["tower_type"] == "archer":
        # --- FIXED: Pull the base damage dynamically! ---
        base_dmg = tower.get("base_dmg", 5)

        exp_dmg = base_dmg + (5 if p_left >= 1 else 0) + (10 if p_left >= 2 else 0)
        exp_radius = 50 + (25 if p_right >= 3 else 0)

        game_state["explosions"].append({
            "x": target["x"], "y": target["y"],
            "timer": 10,
            "dmg": exp_dmg,
            "max_radius": exp_radius
        })

    elif tower["tower_type"] == "archer":
        # Calculate Archer upgrades from towers.py
        exp_dmg = 5 + (5 if p_left >= 1 else 0) + (10 if p_left >= 2 else 0)
        exp_radius = 50 + (25 if p_right >= 3 else 0)  # "EXPLOSION" upgrade makes it 50% bigger

        game_state["explosions"].append({
            "x": target["x"], "y": target["y"],
            "timer": 10,
            "dmg": exp_dmg,
            "max_radius": exp_radius  # Tell the client how big to draw it!
        })


def update_projectiles(game_state):
    """Update projectiles, handle collisions, seeking, and returning."""
    for p in game_state["projectiles"][:]:

        # 1. SEEKING LOGIC (Right Path Lvl 3)
        if p.get("seeking") and game_state["enemies"]:
            target = min(game_state["enemies"], key=lambda e: math.hypot(p["x"] - e["x"], p["y"] - e["y"]))
            dx, dy = target["x"] - p["x"], target["y"] - p["y"]
            dist = math.hypot(dx, dy)
            if dist > 0:
                p["vx"] += (dx / dist) * 0.6
                p["vy"] += (dy / dist) * 0.6
                mag = math.hypot(p["vx"], p["vy"])
                p["vx"] = (p["vx"] / mag) * p.get("speed", 8)
                p["vy"] = (p["vy"] / mag) * p.get("speed", 8)

        # Move projectile
        p["x"] += p["vx"]
        p["y"] += p["vy"]

        # 2. RETURN LOGIC (Left Path Lvl 3)
        if p.get("returns") and not p.get("has_returned"):
            if p["x"] < -50 or p["x"] > 1970 or p["y"] < -50 or p["y"] > 1130:
                p["vx"] *= -1
                p["vy"] *= -1
                p["has_returned"] = True

        # 3. COLLISION LOGIC
        hit_occurred = False
        for e in game_state["enemies"]:
            # Make sure we don't hit the same enemy twice with a returning projectile
            if e["id"] not in p.get("hit_enemies", []) and math.hypot(p["x"] - e["x"], p["y"] - e["y"]) < 45:
                e["hp"] -= p["dmg"]
                p["hit_enemies"].append(e["id"])  # Mark as hit!
                p["pierce"] -= 1
                hit_occurred = True
                if p["pierce"] <= 0:
                    game_state["projectiles"].remove(p)
                break

        if hit_occurred:
            continue

        # Remove off-screen ONLY if it's not a returning projectile that hasn't returned yet
        if not p.get("returns") or p.get("has_returned"):
            if p["x"] < -100 or p["x"] > 2020 or p["y"] < -100 or p["y"] > 1180:
                if p in game_state["projectiles"]:
                    game_state["projectiles"].remove(p)

def update_explosions(game_state):
    """Update explosions and damage enemies."""
    for ex in game_state["explosions"][:]:
        ex["timer"] -= 1
        if ex["timer"] == 5:
            for e in game_state["enemies"]:
                if math.hypot(e["x"] - ex["x"], e["y"] - ex["y"]) < 50:
                    e["hp"] -= ex["dmg"]
        if ex["timer"] <= 0:
            game_state["explosions"].remove(ex)


def remove_dead_enemies(game_state):
    """Remove dead enemies, give cash, and handle Barrel splitting."""
    surviving = []
    new_spawns = []  # Store enemies spawned from deaths (like the barrel popping)

    for e in game_state["enemies"]:
        if e["hp"] > 0:
            surviving.append(e)
        else:
            game_state["cash"] += e.get("cash_price", 1)

            # --- FIXED: Handle SkeletonBarrel Death manually on the Server ---
            if e.get("type") == "SkeletonBarrel":
                import random
                for _ in range(3):
                    # Create a raw Skeleton dictionary directly on the server
                    new_skel = {
                        "x": e["x"] + random.randint(-15, 15),
                        "y": e["y"] + random.randint(-15, 15),
                        "speed": 3,
                        "target_index": e["target_index"],
                        "hp": 1,
                        "dmg": 1,
                        "cash_price": 1,
                        "type": "Skeleton",
                        "id": random.randint(1, 1000000)  # Give it a unique network ID
                    }
                    new_spawns.append(new_skel)

    # Combine the survivors with the newly spawned skeletons
    game_state["enemies"] = surviving + new_spawns

def update_game_state(game_state):
    """Main update function."""
    update_round(game_state)
    update_enemies(game_state)
    update_towers(game_state)
    update_projectiles(game_state)
    update_explosions(game_state)
    remove_dead_enemies(game_state)
    # Update cooldowns
    game_state["abilities"]["ubw_cooldown"] = max(0, game_state["abilities"]["ubw_cooldown"] - 1)

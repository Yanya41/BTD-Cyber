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

def update_towers(game_state):
    """Update towers: shooting, etc."""
    # Simplified: for each tower, if can shoot, create projectile or explosion
    for t in game_state["towers"]:
        # Assume towers have last_shot_time, etc.
        # This is placeholder; need to implement based on tower type
        pass

def update_projectiles(game_state):
    """Update projectiles and handle collisions."""
    for p in game_state["projectiles"][:]:
        # Move projectile
        p["x"] += p["vx"]
        p["y"] += p["vy"]

        # Check collisions with enemies
        for e in game_state["enemies"]:
            if math.hypot(p["x"] - e["x"], p["y"] - e["y"]) < 45:
                e["hp"] -= p["dmg"]
                p["pierce"] -= 1
                if p["pierce"] <= 0:
                    game_state["projectiles"].remove(p)
                break

        # Remove off-screen
        if p["x"] < -50 or p["x"] > 1970 or p["y"] < -50 or p["y"] > 1130:
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
    """Remove dead enemies and give cash."""
    surviving = []
    for e in game_state["enemies"]:
        if e["hp"] > 0:
            surviving.append(e)
        else:
            game_state["cash"] += e.get("cash_price", 1)
            # Handle on_death if applicable
    game_state["enemies"] = surviving

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

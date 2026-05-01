from load_assets import load_image, screen
import math
from rounds import Round
from towers import TowerManager, Explosion
from game_data import Data
from network import Network
import os
from skeleton_rounds import Skeleton

MineFont = os.path.join('Images', 'MineFont.ttf')
goku_icon_path = os.path.join("Cards", "goku.png")
goku_idle_path = "goku_idle.png"
goku_shoot_path = "goku_shoot.png"

archer_icon_path = os.path.join("Cards", "wizard.png")
archer_idle_path = "archer_idle.png"
archer_shoot_path = "archer_shoot.png"
ubw_icon_path = "unlimited_blade_works.png"

# the map
import pygame
import random


class MapBackground:
    def __init__(self):
        # We grab the path directly from your Data class logic
        from game_data import Data
        self.path_points = Data().path_points

        # --- ENHANCED COLOR PALETTE ---
        self.grass_base = (44, 149, 44)
        self.grass_dark = (34, 120, 34)
        self.grass_light = (54, 170, 54)
        self.shadow_color = (25, 90, 25)

        self.stone_edge = (120, 120, 125)
        self.dirt_base = (170, 120, 80)
        self.wagon_rut = (140, 95, 60)

        # Create a blank "canvas" the size of the screen to draw the map on ONCE
        self.bg_surface = pygame.Surface((1920, 1080))
        self.render_static_background()

    def render_static_background(self):
        """Draws the complex map once to save FPS."""
        # 1. Fill base grass
        self.bg_surface.fill(self.grass_base)

        # 2. Add Grass Detail (Procedural Noise)
        # Draws thousands of tiny dots to make it look like a textured field
        for _ in range(8000):
            x = random.randint(0, 1920)
            y = random.randint(0, 1080)
            color = random.choice([self.grass_dark, self.grass_light])
            radius = random.randint(1, 3)
            pygame.draw.circle(self.bg_surface, color, (x, y), radius)

        # 3. Draw Drop Shadow (Offset slightly down and right)
        shadow_offset = 15
        shadow_points = [(x + shadow_offset, y + shadow_offset) for x, y in self.path_points]

        pygame.draw.lines(self.bg_surface, self.shadow_color, False, shadow_points, 60)
        # Draw circles at the joints so the shadows have smooth corners
        for pt in shadow_points:
            pygame.draw.circle(self.bg_surface, self.shadow_color, pt, 30)

        # 4. Draw the Detailed Road (Layered from thickest to thinnest)
        layers = [
            (self.stone_edge, 60),  # Layer 1: Outer rocky border
            (self.dirt_base, 50),  # Layer 2: Main dirt surface
            (self.wagon_rut, 30),  # Layer 3: Dark wheel tracks
            (self.dirt_base, 14)  # Layer 4: Center dirt ridge
        ]

        # Loop through our layers and draw them on top of each other
        for color, width in layers:
            pygame.draw.lines(self.bg_surface, color, False, self.path_points, width)
            for pt in self.path_points:
                pygame.draw.circle(self.bg_surface, color, pt, width // 2)

    def draw(self):
        # Instead of doing all that math every frame, just paste the finished picture!
        screen.blit(self.bg_surface, (0, 0))



class Abilities:
    def __init__(self, font, towers):
        self.font = font
        self.tower = towers
        self.ubw_icon = load_image(ubw_icon_path, alpha=True)
        self.btn_ubw = None
        self.ubw_cooldown = 0
    def draw(self):
        if any(t for t in self.tower if t.tower_type == "archer" and t.path_left == 3):
            self.btn_ubw = screen.blit(self.ubw_icon, (10, 1000))
        else:
            self.btn_ubw = None



class UpgradePanel: #this is the upgrade panel that is in the bottom left
    def __init__(self, font):
        self.font = font
        self.panel_upgrade = pygame.Rect(1520, 0, 400, 200)  # Bottom left corner panel
        self.gray = (50, 50, 50)
        self.red = (200, 100, 100)

        self.btn_left = pygame.Rect(1540, 10, 150, 50) # the left upgrade button path
        self.btn_right = pygame.Rect(1750, 10, 150, 50)# the right upgrade button path
        self.btn_target = pygame.Rect(1750, 100, 120, 50)# the targeting mode button

    def draw(self, tower, placed_towers):
        if not tower:
            return  # Don't draw anything if no tower is selected

        pygame.draw.rect(screen, self.gray, self.panel_upgrade) # Draw the upgrade panel background

        # Title aka "Goku Upgrades" or "Archer Upgrades" etc...
        title = self.font.render(f"{tower.tower_type.upper()} Upgrades", True, (255, 255, 255))
        screen.blit(title, (1630, 170))

        # Damage Dealt
        dmg_text = self.font.render(f"Damage: {getattr(tower, 'damage_dealt')}", True, (255, 255, 255))
        screen.blit(dmg_text, (1550, 100))  # Placed bottom center of the panel

        # Left Path Button
        pygame.draw.rect(screen, (50, 100, 200), self.btn_left)
        if (tower.path_left < 3 and tower.path_right < 3) or (tower.path_left < 2 and tower.path_right == 3):
            if tower.path_left == 2 and any(t for t in placed_towers if t != tower and t.tower_type == tower.tower_type and t.path_left == 3):
                text_l = self.font.render("BOUGHT", True, self.red)
            else:
                cost_l = tower.left_costs[tower.path_left]
                text_l = self.font.render(f"Left: ${cost_l}", True, (255, 255, 255))
            name_l = tower.left_names[tower.path_left]
            name_text_l = self.font.render(name_l, True, (255, 255, 255))
            screen.blit(name_text_l, (self.btn_left.x + 10, self.btn_left.y + 30))
            screen.blit(text_l, (self.btn_left.x + 10, self.btn_left.y + 10))

        elif tower.path_right == 3 and tower.path_left == 2:
            text_l = self.font.render("LOCKED", True, self.red)
            screen.blit(text_l, (self.btn_left.x + 10, self.btn_left.y + 10))

        else:
            text_l = self.font.render("MAXED", True, self.red)
            screen.blit(text_l, (self.btn_left.x + 10, self.btn_left.y + 10))

        # Right Path Button
        pygame.draw.rect(screen, (50, 100, 200), self.btn_right)
        if (tower.path_right < 3 and tower.path_left < 3) or (tower.path_right < 2 and tower.path_left == 3):
            if tower.path_right == 2 and any(t for t in placed_towers if t != tower and t.tower_type == tower.tower_type and t.path_right == 3):
                text_r = self.font.render("BOUGHT", True, self.red)
            else:
                cost_r = tower.right_costs[tower.path_right]
                text_r = self.font.render(f"Right: ${cost_r}", True, (255, 255, 255))
            name_r = tower.right_names[tower.path_right]
            name_text_r = self.font.render(name_r, True, (255, 255, 255))
            screen.blit(name_text_r, (self.btn_right.x + 10, self.btn_right.y + 30))

        elif tower.path_left == 3 and tower.path_right == 2:
            text_r = self.font.render("LOCKED", True, self.red)
            screen.blit(text_r, (self.btn_right.x + 10, self.btn_right.y + 10))

        else:
            text_r = self.font.render("MAXED", True, self.red)
        screen.blit(text_r, (self.btn_right.x + 10, self.btn_right.y + 10))

        # Targeting Mode Button
        target_mode_text = "Target: " + tower.target_mode.capitalize()
        text_t = self.font.render(target_mode_text, True, (255, 0, 0))
        screen.blit(text_t, (self.btn_target.x, self.btn_target.y))



class SideMenu: #this is the right side menu where you can purchase towers
    def __init__(self, width):
        self.width = width
        self.rect = pygame.Rect(1920 - width, 0, width, 1080)
        self.color = (200, 200, 200)

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        # Fix: Ensure path matches your folder structure
        goku_icon = load_image(goku_icon_path, scale_to=(100, 100), alpha=True)
        archer_icon = load_image(archer_icon_path, scale_to=(100, 100), alpha=True)
        screen.blit(goku_icon, (1920 - self.width + 100, 200))
        screen.blit(archer_icon, (1920 - self.width + 100, 350))


class UiManager:
    def __init__(self, font):
        self.font = font
        self.buttons = []  # List to hold button data (rect, color, text)
        self.buttons.append((pygame.Rect(1670, 950, 200, 50), (0, 255, 0), "Start Round", (0, 0, 0)))  # start round button
        self.buttons.append((pygame.Rect(100, 50, 200, 50), (34, 139, 34), str(Data().current_hp) + " Health", (255, 0, 0)))  # health
        self.buttons.append((pygame.Rect(350, 50, 200, 50), (34, 139, 34), str(Data().starting_cash) + " Cash", (239, 191, 4)))  # cash
        self.buttons.append((pygame.Rect(600, 50, 200, 50), (34, 139, 34), "Round " + str(Round().current_round), (0, 0, 0)))  # round number

    def draw(self, data, rounds):
        for button in self.buttons:
            pygame.draw.rect(screen, button[1], button[0])
            label = button[2]
            if "Health" in label:
                text_surface = self.font.render(f"{data.current_hp} Health", True, button[3])
            elif "Cash" in label:
                text_surface = self.font.render(f"{data.current_cash} Cash", True, button[3])
            elif "Round " in label:
                text_surface = self.font.render("Round " f"{rounds.current_round}", True, button[3])
            else:
                text_surface = self.font.render(label, True, button[3])
            text_rect = text_surface.get_rect(center=button[0].center)
            screen.blit(text_surface, text_rect)


def is_on_path(px, py, path_points, minimum_distance):
    """
    Checks if a point (px, py) is within 'minimum_distance' of any line segment in path_points.
    """
    for i in range(len(path_points) - 1):
        x1, y1 = path_points[i]
        x2, y2 = path_points[i + 1]

        # Calculate the distance from the point to the line segment
        line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if line_len_sq == 0:
            dist = math.hypot(px - x1, py - y1)
        else:
            # Find the closest point on the line segment
            t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq
            t = max(0, min(1, t))  # Clamp t to the 0 to 1 range

            proj_x = x1 + t * (x2 - x1)
            proj_y = y1 + t * (y2 - y1)

            dist = math.hypot(px - proj_x, py - proj_y)

        if dist < minimum_distance:
            return True  # It's too close to the path!

    return False


def is_overlapping_tower(px, py, placed_towers, min_distance):
    """
    Checks if a point (px, py) is within 'min_distance' of any already placed tower.
    """
    for t in placed_towers:
        # Calculate the distance between the mouse and the center of the existing tower
        dist = math.hypot(px - t.x, py - t.y)

        if dist < min_distance:
            return True  # It's too close to another tower!

    return False

def get_tower (tower_type):
    if tower_type == "goku":
        return goku_idle_path, 250
    if tower_type == "archer":
        return archer_idle_path, 1000




# execution starts here
pygame.init()
clock = pygame.time.Clock()

game_data = Data()

draw_map = MapBackground()
side_menu = SideMenu(400)
ui = UiManager(pygame.font.Font(MineFont, 25))
upgrade_panel = UpgradePanel(pygame.font.Font(MineFont, 20))
round_manager = Round()
tower_manager = TowerManager()
network = Network()
player_id = network.player_id
placed_towers, projectiles = [], []
dragging_tower, selected_tower = None, None
abilities = Abilities(pygame.font.Font(MineFont, 20), placed_towers)

explosions = []

# Main Game Loop
# Main Game Loop
running = True
while running:
    # ==========================================
    # 1. NETWORK SYNC (The Server is Boss)
    # ==========================================
    current_game_state = network.get_state()

    if current_game_state:
        # Sync Game Stats
        game_data.current_cash = current_game_state["cash"]
        game_data.current_hp = current_game_state["current_hp"]
        round_manager.current_round = current_game_state["current_round"]

        # --- SYNC TOWERS ---
        local_tower_ids = [t.id for t in placed_towers]
        for server_tower in current_game_state["towers"]:
            if server_tower["id"] not in local_tower_ids:
                # We found a new tower from the server! Spawn it locally.
                new_t = tower_manager.create_tower(server_tower["tower_type"], server_tower["x"], server_tower["y"])
                new_t.id = server_tower["id"]
                new_t.owner = server_tower.get("owner")  # <-- Save the owner!
                placed_towers.append(new_t)
            else:
                # Update existing towers
                for local_t in placed_towers:
                    if local_t.id == server_tower["id"]:
                        local_t.path_left = server_tower.get("path_left", 0)
                        local_t.path_right = server_tower.get("path_right", 0)
                        local_t.damage_dealt = server_tower.get("damage_dealt", 0)
                        local_t.target_mode = server_tower.get("target_mode", "first")
                        local_t.angle = server_tower.get("angle", 270)
                        local_t.owner = server_tower.get("owner")  # <-- Keep owner updated!

                        if server_tower.get("just_shot"):
                            local_t.last_shot_time = pygame.time.get_ticks()

        # --- SYNC ENEMIES ---
        from skeleton_rounds import Skeleton

        local_enemy_ids = [e.id for e in round_manager.enemies]
        active_server_ids = [se["id"] for se in current_game_state["enemies"]]

        # 1. Remove dead/leaked enemies from the local screen
        round_manager.enemies = [e for e in round_manager.enemies if e.id in active_server_ids]

        # 2. Add new enemies or update existing ones
        for s_enemy in current_game_state["enemies"]:
            if s_enemy["id"] not in local_enemy_ids:
                visual_enemy = Skeleton()
                visual_enemy.id = s_enemy["id"]
                visual_enemy.x = s_enemy["x"]
                visual_enemy.y = s_enemy["y"]
                visual_enemy.hp = s_enemy["hp"]
                round_manager.enemies.append(visual_enemy)
            else:
                for local_e in round_manager.enemies:
                    if local_e.id == s_enemy["id"]:
                        if s_enemy["x"] < local_e.x:
                            local_e.flip_image = True
                        elif s_enemy["x"] > local_e.x:
                            local_e.flip_image = False

                        local_e.x = s_enemy["x"]
                        local_e.y = s_enemy["y"]
                        local_e.hp = s_enemy["hp"]

    # ==========================================
    # 2. EVENT HANDLING (Player Inputs)
    # ==========================================
    m_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = m_pos

            # Upgrade panel buttons
            if selected_tower and upgrade_panel.panel_upgrade.collidepoint(mx, my):
                if upgrade_panel.btn_left.collidepoint(mx, my):
                    # If the upgrade succeeds locally (returns True)
                    if selected_tower.upgrade_left(game_data, placed_towers):
                        # Tell the server to save the new path level and our new cash balance!
                        network.send({
                            "type": "sync_upgrade",
                            "tower_id": selected_tower.id,
                            "path_left": selected_tower.path_left,
                            "new_cash": game_data.current_cash
                        })

                elif upgrade_panel.btn_right.collidepoint(mx, my):
                    if selected_tower.upgrade_right(game_data, placed_towers):
                        network.send({
                            "type": "sync_upgrade",
                            "tower_id": selected_tower.id,
                            "path_right": selected_tower.path_right,
                            "new_cash": game_data.current_cash
                        })

                elif upgrade_panel.btn_target.collidepoint(mx, my):
                    # Toggle targeting locally
                    selected_tower.target_mode = "strong" if selected_tower.target_mode == "first" else "first"
                    # Tell the server about the change
                    network.send({
                        "type": "sync_upgrade",
                        "tower_id": selected_tower.id,
                        "target_mode": selected_tower.target_mode
                    })

            # Start round button
            elif 1670 <= mx <= 1870 and 950 <= my <= 1000:
                network.send({"type": "start_round"})

            # The "Shop"
            elif 1620 <= mx <= 1920 and 200 <= my <= 300:
                if game_data.current_cash >= 550: dragging_tower = "goku"

            elif 1620 <= mx <= 1920 and 350 <= my <= 450:
                if game_data.current_cash >= 600: dragging_tower = "archer"

            # UBW Ability
            elif abilities.btn_ubw and abilities.btn_ubw.collidepoint(mx, my):
                network.send({"type": "ubw"})  # Ask server to cast ability!

                # Deselect tower
            else:
                # --- NEW: Only select towers that belong to YOU! ---
                selected_tower = next((t for t in placed_towers if
                                       getattr(t, 'owner', None) == player_id and math.hypot(mx - t.x, my - t.y) < 40),None)

        if event.type == pygame.MOUSEBUTTONUP:
            if dragging_tower and m_pos[0] < 1620:
                if not is_on_path(m_pos[0], m_pos[1], game_data.path_points, 50) and not is_overlapping_tower(m_pos[0],
                                                                                                              m_pos[1],
                                                                                                              placed_towers,
                                                                                                              50):
                    new_t = tower_manager.create_tower(dragging_tower, m_pos[0], m_pos[1])
                    network.send({
                        "type": "place_tower",
                        "tower_data": new_t.to_dict()
                    })
                dragging_tower = None
            elif dragging_tower and m_pos[0] >= 1620:
                dragging_tower = None  # Cancel drag if dropped back in shop

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                network.send({"type": "start_round"})

    # ==========================================
    # 3. DRAWING SECTION
    # ==========================================
    draw_map.draw()

    # Draw Enemies and animate them
    now = pygame.time.get_ticks()
    for e in round_manager.enemies:
        if e.frames and (now - e.last_update > e.frame_time):
            e.current_frame = (e.current_frame + 1) % len(e.frames)
            e.last_update = now
        e.draw(screen)

    # Draw Towers
    for t in placed_towers:
        t.draw(screen, 1)

    # Draw Server-Side Projectiles & Explosions
    if current_game_state:
        # Draw Kamehamehas
        for p in current_game_state.get("projectiles", []):
            size = p.get("size", 10)
            pygame.draw.circle(screen, (173, 216, 230), (int(p["x"]), int(p["y"])), size)
            pygame.draw.circle(screen, (255, 255, 255), (int(p["x"]), int(p["y"])), size // 2)

        # Draw Explosions
        for ex in current_game_state.get("explosions", []):
            timer = ex.get("timer", 10)
            max_radius = ex.get("max_radius", 50)
            # Calculate radius based on timer for an expanding/fading effect
            radius = max_radius * (1 - (timer / 10))
            if radius > 0:
                pygame.draw.circle(screen, (255, 165, 0), (int(ex["x"]), int(ex["y"])), int(radius))
                pygame.draw.circle(screen, (255, 255, 255), (int(ex["x"]), int(ex["y"])), int(radius // 2))

    # UI & Menus
    side_menu.draw()
    ui.draw(game_data, round_manager)
    abilities.draw()

    # Dragging and Selected Tower Overlays
    if selected_tower:
        pygame.draw.circle(screen, (255, 255, 0), (selected_tower.x, selected_tower.y), selected_tower.range, 2)
        range_surface_0 = pygame.Surface((selected_tower.range * 2, selected_tower.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(range_surface_0, (255, 255, 0, 50), (selected_tower.range, selected_tower.range),
                           selected_tower.range)
        screen.blit(range_surface_0, (selected_tower.x - selected_tower.range, selected_tower.y - selected_tower.range))
        upgrade_panel.draw(selected_tower, placed_towers)

    if dragging_tower:
        radius = get_tower(dragging_tower)[1]
        range_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        if not is_on_path(m_pos[0], m_pos[1], game_data.path_points, 50) and not is_overlapping_tower(m_pos[0],
                                                                                                      m_pos[1],
                                                                                                      placed_towers,
                                                                                                      50):
            pygame.draw.circle(range_surface, (0, 0, 255, 100), (radius, radius), radius)
        else:
            pygame.draw.circle(range_surface, (255, 0, 0, 100), (radius, radius), radius)

        pygame.draw.circle(range_surface, (255, 0, 255, 255), (radius, radius), radius, 2)
        screen.blit(range_surface, (m_pos[0] - radius, m_pos[1] - radius))

        icon = load_image(get_tower(dragging_tower)[0], alpha=True)
        if icon:
            rect = icon.get_rect(center=m_pos)
            screen.blit(icon, rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
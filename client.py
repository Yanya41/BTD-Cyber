import pygame
import sys
import math
import os

# Menus
from main_menu import MainMenu
from login_menu import LoginMenu
from lobby_menu import LobbyMenu
from in_lobby_menu import InLobbyMenu
import load_assets
from network import Network

# --- NEW: Import all your actual game assets and logic ---
from map import MapBackground, SideMenu, UiManager, UpgradePanel, Abilities, get_tower, is_on_path, is_overlapping_tower
from game_data import Data
from rounds import Round
from towers import TowerManager
from skeleton_rounds import Skeleton, ShieldedSkeleton, SkeletonBarrel

if load_assets.check_files_exist():
    print("Missing assets, exiting.")
    sys.exit()

pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((1920, 1080))
pygame.display.set_caption("Royal TD")

load_assets.load_all_assets()

# Initialize Menus
main_menu = MainMenu(screen)
login_menu = LoginMenu(screen)
lobby_menu = LobbyMenu(screen)
in_lobby_menu = InLobbyMenu(screen)

# Initialize Network
n = Network()

# --- NEW: Initialize your Game UI & Data ---
MineFont = os.path.join('Images', 'MineFont.ttf')
game_data = Data()
draw_map = MapBackground()
side_menu = SideMenu(400)
ui = UiManager(pygame.font.Font(MineFont, 25))
upgrade_panel = UpgradePanel(pygame.font.Font(MineFont, 20))
round_manager = Round()
tower_manager = TowerManager()

placed_towers = []
dragging_tower = None
selected_tower = None
abilities = Abilities(pygame.font.Font(MineFont, 20), placed_towers)

current_state = "MAIN_MENU"
running = True
username = ""
last_ping_time = 0


class ErrorPopup:
    def __init__(self):
        self.message = ""
        self.active = False
        self.start_time = 0
        self.duration = 3000

        # --- FIXED: Load the font ONLY ONCE when the game starts! ---
        self.font = pygame.font.SysFont("comicsans", 40)
        self.text_surface = None
        self.box_width = 0
        self.box_height = 0

    def trigger(self, msg):
        """Call this to make the popup appear."""
        self.message = msg
        self.active = True
        self.start_time = pygame.time.get_ticks()

        # --- FIXED: Render the text ONLY ONCE when the error happens! ---
        self.text_surface = self.font.render(self.message, True, (255, 255, 255))
        self.box_width = self.text_surface.get_width() + 40
        self.box_height = self.text_surface.get_height() + 40

    def draw(self, screen):
        """Call this every frame in your draw loop."""
        if self.active:
            if pygame.time.get_ticks() - self.start_time > self.duration:
                self.active = False
                return

            # Math for perfectly centering the box
            x = (1920 // 2) - (self.box_width // 2)
            y = 150

            # Draw the background and border
            pygame.draw.rect(screen, (150, 0, 0), (x, y, self.box_width, self.box_height), border_radius=10)
            pygame.draw.rect(screen, (255, 50, 50), (x, y, self.box_width, self.box_height), 3, border_radius=10)

            # Draw the pre-rendered text surface (super fast!)
            screen.blit(self.text_surface, (x + 20, y + 20))

error_popup = ErrorPopup()
while running:
    # ==========================================
    # 1. EVENT HANDLING
    # ==========================================
    m_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_state == "MAIN_MENU":
            action = main_menu.handle_event(event)
            if action == "Start Game":
                current_state = "LOGIN"
            elif action == "Exit":
                running = False

        elif current_state == "LOGIN":
            action = login_menu.handle_event(event)
            if action:
                if action.get("action") == "go_back":
                    current_state = "MAIN_MENU"
                elif action.get("action") in ["login", "register"]:
                    if action.get("user") != '' and action.get("password") != '':
                        response = n.send_json(action)
                        if response and response.get("status") == "success":
                            username = action.get("user")
                            current_state = "LOBBY_SELECT"
                        else:
                            error_msg = response.get("msg") if response else "Server offline."
                            print(f"Failed: {error_msg}")
                            error_popup.trigger(error_msg)

        elif current_state == "LOBBY_SELECT":
            action = lobby_menu.handle_event(event)
            if action:
                if action.get("action") == "refresh_lobbies":
                    response = n.send_json({"action": "get_lobbies"})
                    if response and response.get("status") == "success":
                        lobby_menu.update_server_list(response.get("lobbies", []))

                elif action.get("action") == "create_lobby":
                    response = n.send_json(action)
                    if response and response.get("status") == "success":
                        in_lobby_menu.update_players([{"username": username, "admin": True}], is_admin=True)
                        current_state = "IN_LOBBY"

                elif action.get("action") == "join_lobby":
                    response = n.send_json(action)
                    if response and response.get("status") == "success":
                        in_lobby_menu.update_players([{"username": username, "admin": False}], is_admin=False)
                        current_state = "IN_LOBBY"

        elif current_state == "IN_LOBBY":
            action = in_lobby_menu.handle_event(event)
            if action:
                if action.get("action") == "leave_lobby":
                    current_state = "LOBBY_SELECT"
                elif action.get("action") == "start_game":
                    response = n.send_json({"action": "start_game"})
                    if response and response.get("action") == "launch_game":
                        n.wait_for_game_start()
                        current_state = "PLAYING_GAME"

        # --- NEW: YOUR ACTUAL GAMEPLAY EVENTS ---
        elif current_state == "PLAYING_GAME":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = m_pos

                # Upgrade panel buttons
                if selected_tower and upgrade_panel.panel_upgrade.collidepoint(mx, my):
                    if upgrade_panel.btn_left.collidepoint(mx, my):
                        if selected_tower.upgrade_left(game_data, placed_towers):
                            n.send_action({"type": "sync_upgrade", "tower_id": selected_tower.id,
                                           "path_left": selected_tower.path_left, "new_cash": game_data.current_cash})
                    elif upgrade_panel.btn_right.collidepoint(mx, my):
                        if selected_tower.upgrade_right(game_data, placed_towers):
                            n.send_action({"type": "sync_upgrade", "tower_id": selected_tower.id,
                                           "path_right": selected_tower.path_right, "new_cash": game_data.current_cash})
                    elif upgrade_panel.btn_target.collidepoint(mx, my):
                        selected_tower.target_mode = "strong" if selected_tower.target_mode == "first" else "first"
                        n.send_action({"type": "sync_upgrade", "tower_id": selected_tower.id,
                                       "target_mode": selected_tower.target_mode})

                # Start round button
                elif 1670 <= mx <= 1870 and 950 <= my <= 1000:
                    n.send_action({"type": "start_round"})

                # The "Shop"
                elif 1620 <= mx <= 1920 and 200 <= my <= 300:
                    if game_data.current_cash >= 550: dragging_tower = "goku"
                elif 1620 <= mx <= 1920 and 350 <= my <= 450:
                    if game_data.current_cash >= 600: dragging_tower = "archer"

                # UBW Ability
                elif abilities.btn_ubw and abilities.btn_ubw.collidepoint(mx, my):
                    n.send_action({"type": "ubw"})

                    # Select a tower you own
                else:
                    selected_tower = next((t for t in placed_towers if
                                           getattr(t, 'owner', None) == n.player_id and math.hypot(mx - t.x, my - t.y) < 40),None)

            if event.type == pygame.MOUSEBUTTONUP:
                if dragging_tower and m_pos[0] < 1620:
                    if not is_on_path(m_pos[0], m_pos[1], game_data.path_points, 50) and not is_overlapping_tower(
                            m_pos[0], m_pos[1], placed_towers, 50):
                        new_t = tower_manager.create_tower(dragging_tower, m_pos[0], m_pos[1])
                        new_t.owner = n.player_id  # claim it locally
                        n.send_action({"type": "place_tower", "tower_data": new_t.to_dict()})
                    dragging_tower = None
                elif dragging_tower and m_pos[0] >= 1620:
                    dragging_tower = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    n.send_action({"type": "start_round"})

    # ==========================================
    # 2. CONTINUOUS LOGIC & SYNCING
    # ==========================================
    if current_state == "IN_LOBBY":
        current_time = pygame.time.get_ticks()
        if current_time - last_ping_time > 1000:
            response = n.send_json({"action": "lobby_ping"})
            if response:
                if response.get("action") == "launch_game":
                    n.wait_for_game_start()
                    current_state = "PLAYING_GAME"
                elif response.get("players"):
                    player_list = [{"username": name, "admin": (i == 0)} for i, name in enumerate(response["players"])]
                    in_lobby_menu.update_players(player_list, is_admin=(player_list[0]["username"] == username))
            last_ping_time = current_time

    elif current_state == "PLAYING_GAME":
        current_game_state = n.get_state()

        if current_game_state:
            # Sync Game Stats
            game_data.current_cash = current_game_state["cash"]
            game_data.current_hp = current_game_state["current_hp"]
            round_manager.current_round = current_game_state["current_round"]

            # Sync Towers
            local_tower_ids = [t.id for t in placed_towers]
            for server_tower in current_game_state["towers"]:
                if server_tower["id"] not in local_tower_ids:
                    new_t = tower_manager.create_tower(server_tower["tower_type"], server_tower["x"], server_tower["y"])
                    new_t.id = server_tower["id"]
                    new_t.owner = server_tower.get("owner")
                    placed_towers.append(new_t)
                else:
                    for local_t in placed_towers:
                        if local_t.id == server_tower["id"]:
                            local_t.path_left = server_tower.get("path_left", 0)
                            local_t.path_right = server_tower.get("path_right", 0)
                            local_t.damage_dealt = server_tower.get("damage_dealt", 0)
                            local_t.target_mode = server_tower.get("target_mode", "first")
                            local_t.angle = server_tower.get("angle", 270)
                            local_t.owner = server_tower.get("owner")
                            if server_tower.get("just_shot"):
                                local_t.last_shot_time = pygame.time.get_ticks()

            # Sync Enemies
            local_enemy_ids = [e.id for e in round_manager.enemies]
            active_server_ids = [se["id"] for se in current_game_state["enemies"]]

            round_manager.enemies = [e for e in round_manager.enemies if e.id in active_server_ids]

            for s_enemy in current_game_state["enemies"]:
                if s_enemy["id"] not in local_enemy_ids:

                    # --- FIXED: Check the enemy type and spawn the correct class! ---
                    e_type = s_enemy.get("type", "Skeleton")
                    if e_type == "SkeletonBarrel":
                        visual_enemy = SkeletonBarrel()
                    elif e_type == "ShieldedSkeleton":
                        visual_enemy = ShieldedSkeleton()
                    else:
                        visual_enemy = Skeleton()

                    visual_enemy.id = s_enemy["id"]
                    visual_enemy.x = s_enemy["x"]
                    visual_enemy.y = s_enemy["y"]
                    visual_enemy.hp = s_enemy["hp"]
                    round_manager.enemies.append(visual_enemy)
                else:
                    for local_e in round_manager.enemies:
                        if local_e.id == s_enemy["id"]:
                            local_e.flip_image = s_enemy["x"] < local_e.x
                            local_e.x = s_enemy["x"]
                            local_e.y = s_enemy["y"]
                            local_e.hp = s_enemy["hp"]

    # ==========================================
    # 3. DRAW CALLS
    # ==========================================
    if current_state == "MAIN_MENU":
        main_menu.draw()
    elif current_state == "LOGIN":
        login_menu.draw()
    elif current_state == "LOBBY_SELECT":
        lobby_menu.draw()
    elif current_state == "IN_LOBBY":
        in_lobby_menu.draw()

    elif current_state == "PLAYING_GAME":
        draw_map.draw()

        # Enemies
        now = pygame.time.get_ticks()
        for e in round_manager.enemies:
            if e.frames and (now - e.last_update > e.frame_time):
                e.current_frame = (e.current_frame + 1) % len(e.frames)
                e.last_update = now
            e.draw(screen)

        # Towers
        for t in placed_towers:
            t.draw(screen, n.player_id)

        # Server-Side Particles
        if 'current_game_state' in locals() and current_game_state:
            for p in current_game_state.get("projectiles", []):
                size = p.get("size", 10)
                pygame.draw.circle(screen, (173, 216, 230), (int(p["x"]), int(p["y"])), size)
                pygame.draw.circle(screen, (255, 255, 255), (int(p["x"]), int(p["y"])), size // 2)

            for ex in current_game_state.get("explosions", []):
                timer = ex.get("timer", 10)
                max_radius = ex.get("max_radius", 50)
                radius = max_radius * (1 - (timer / 10))
                if radius > 0:
                    pygame.draw.circle(screen, (255, 165, 0), (int(ex["x"]), int(ex["y"])), int(radius))
                    pygame.draw.circle(screen, (255, 255, 255), (int(ex["x"]), int(ex["y"])), int(radius // 2))

        # UI Overlay
        side_menu.draw()
        ui.draw(game_data, round_manager)
        abilities.draw()

        if selected_tower:
            pygame.draw.circle(screen, (255, 255, 0), (selected_tower.x, selected_tower.y), selected_tower.range, 2)
            range_surface_0 = pygame.Surface((selected_tower.range * 2, selected_tower.range * 2), pygame.SRCALPHA)
            pygame.draw.circle(range_surface_0, (255, 255, 0, 50), (selected_tower.range, selected_tower.range),
                               selected_tower.range)
            screen.blit(range_surface_0,
                        (selected_tower.x - selected_tower.range, selected_tower.y - selected_tower.range))
            upgrade_panel.draw(selected_tower, placed_towers)

        if dragging_tower:
            radius = get_tower(dragging_tower)[1]
            range_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            if not is_on_path(m_pos[0], m_pos[1], game_data.path_points, 50) and not is_overlapping_tower(m_pos[0],m_pos[1],placed_towers,50):
                pygame.draw.circle(range_surface, (0, 0, 255, 100), (radius, radius), radius)
            else:
                pygame.draw.circle(range_surface, (255, 0, 0, 100), (radius, radius), radius)
            pygame.draw.circle(range_surface, (255, 0, 255, 255), (radius, radius), radius, 2)
            screen.blit(range_surface, (m_pos[0] - radius, m_pos[1] - radius))

            from load_assets import load_image

            icon = load_image(get_tower(dragging_tower)[0], alpha=True)
            if icon:
                rect = icon.get_rect(center=m_pos)
                screen.blit(icon, rect)

    error_popup.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
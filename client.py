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
from towers import TowerManager, ManipulationProjectile, Kamehameha, Explosion
from skeleton_rounds import Skeleton, ShieldedSkeleton, SkeletonBarrel, TurnedSkeleton

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
MineFont = os.path.join('Fonts', 'MineFont.ttf')
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
turned_enemies = []
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
        self.message = msg
        self.active = True
        self.start_time = pygame.time.get_ticks()

        # --- FIXED: Render the text ONLY ONCE when the error happens! ---
        self.text_surface = self.font.render(self.message, True, (255, 255, 255))
        self.box_width = self.text_surface.get_width() + 40
        self.box_height = self.text_surface.get_height() + 40

    def draw(self, screen):
        if self.active:
            if pygame.time.get_ticks() - self.start_time > self.duration:
                self.active = False
                return

            x = (1920 // 2) - (self.box_width // 2)
            y = 150

            # Draw the background and border
            pygame.draw.rect(screen, (150, 0, 0), (x, y, self.box_width, self.box_height), border_radius=10)
            pygame.draw.rect(screen, (255, 50, 50), (x, y, self.box_width, self.box_height), 3, border_radius=10)

            screen.blit(self.text_surface, (x + 20, y + 20))

error_popup = ErrorPopup()
while running:
    m_pos = pygame.mouse.get_pos()

    # 1. EVENT HANDLING (All inputs MUST live inside this loop)
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
                        try:
                            response = n.send_json(action)
                            if response and response.get("status") == "success":
                                username = action.get("user")
                                current_state = "LOBBY_SELECT"
                            else:
                                error_msg = response.get("msg") if response else "Server offline."
                                print(f"Failed: {error_msg}")
                                error_popup.trigger(error_msg)
                        except Exception as e:
                            print(f"Login Error: {e}")
                            error_popup.trigger(f"Login Error: {str(e)}")
                    else:
                        error_popup.trigger("Username and password required!")

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

        elif current_state == "PLAYING_GAME":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = m_pos

                # Upgrade panel buttons
                if selected_tower and upgrade_panel.panel_upgrade.collidepoint(mx, my):
                    if getattr(selected_tower, 'owner', None) == n.player_id:
                        if upgrade_panel.btn_left.collidepoint(mx, my):
                            if selected_tower.upgrade_left(game_data, placed_towers):
                                n.send_action({"type": "sync_upgrade", "tower_id": selected_tower.id,
                                               "path_left": selected_tower.path_left,
                                               "new_cash": game_data.current_cash})
                        elif upgrade_panel.btn_right.collidepoint(mx, my):
                            if selected_tower.upgrade_right(game_data, placed_towers):
                                n.send_action({"type": "sync_upgrade", "tower_id": selected_tower.id,
                                               "path_right": selected_tower.path_right,
                                               "new_cash": game_data.current_cash})
                        elif upgrade_panel.btn_target.collidepoint(mx, my):
                            selected_tower.target_mode = "strong" if selected_tower.target_mode == "first" else "first"
                            n.send_action({"type": "sync_upgrade", "tower_id": selected_tower.id,
                                           "target_mode": selected_tower.target_mode})
                        elif upgrade_panel.btn_sell.collidepoint(mx, my):
                            game_data.current_cash += selected_tower.get_sell_value()
                            n.send_action({"type": "sell_tower", "tower_id": selected_tower.id,
                                           "new_cash": game_data.current_cash})
                            placed_towers.remove(selected_tower)
                            selected_tower = None

                # Start round button
                elif 1670 <= mx <= 1870 and 950 <= my <= 1000:
                    n.send_action({"type": "start_round"})

                # The "Shop"
                elif 1620 <= mx <= 1920 and 200 <= my <= 300:
                    if game_data.current_cash >= 550: dragging_tower = "goku"
                elif 1620 <= mx <= 1920 and 350 <= my <= 450:
                    if game_data.current_cash >= 600: dragging_tower = "archer"
                elif 1620 <= mx <= 1920 and 500 <= my <= 600:
                    if game_data.current_cash >= 1000: dragging_tower = "ayanokoji"

                # UBW Ability
                elif abilities.btn_ubw and abilities.btn_ubw.collidepoint(mx, my):
                    n.send_action({"type": "ubw"})

                # Select a tower you own
                else:
                    selected_tower = next((t for t in placed_towers if math.hypot(mx - t.x, my - t.y) < 40), None)

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

        elif current_state == "WIN_SCREEN":
            return_btn_rect = pygame.Rect(1920 // 2 - 200, 650, 400, 80)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and return_btn_rect.collidepoint(m_pos):
                    # Request server routing back to the lobby list phase
                    response = n.send_action({"type": "return_to_lobby"})
                    # Flush local instances from last playthrough
                    placed_towers = []
                    dragging_tower = None
                    selected_tower = None
                    turned_enemies = []
                    current_state = "LOBBY_SELECT"  # Fixed: Now routes straight back to lobby select menu

    # ==========================================
    # 2. CONTINUOUS LOGIC & NETWORK SYNCING
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
            # Check if server packet explicitly intercepted a return instruction
            if isinstance(current_game_state, dict) and current_game_state.get("action") == "back_to_lobby":
                placed_towers = []
                dragging_tower = None
                selected_tower = None
                turned_enemies = []
                current_state = "LOBBY_SELECT"  # Fixed: Sync routing back to lobby list
                continue

            # Switch client display mode to Victory screen if the server reports the round limit is reached
            if isinstance(current_game_state, dict) and current_game_state.get("game_won", False):
                current_state = "WIN_SCREEN"
                continue

            # Sync player wallet currency stats
            if "player_cash" in current_game_state and n.player_id in current_game_state["player_cash"]:
                game_data.current_cash = current_game_state["player_cash"][n.player_id]
            else:
                game_data.current_cash = current_game_state.get("cash", 0)
            game_data.current_hp = current_game_state["current_hp"]
            round_manager.current_round = current_game_state["current_round"]

            # Sync Towers
            active_server_tower_ids = [st["id"] for st in current_game_state["towers"]]
            for local_t in placed_towers[:]:
                if local_t.id not in active_server_tower_ids:
                    if selected_tower == local_t: selected_tower = None
                    placed_towers.remove(local_t)

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
                            if server_tower.get("just_shot"): local_t.last_shot_time = pygame.time.get_ticks()

            # Sync Enemies
            local_enemy_ids = [e.id for e in round_manager.enemies]
            active_server_ids = [se["id"] for se in current_game_state["enemies"]]
            round_manager.enemies = [e for e in round_manager.enemies if e.id in active_server_ids]
            for s_enemy in current_game_state["enemies"]:
                if s_enemy["id"] not in local_enemy_ids:
                    from skeleton_rounds import Skeleton, ShieldedSkeleton, SkeletonBarrel

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

            # Sync Manipulated/Turned Enemies
            server_turned = current_game_state.get("turned_enemies", [])
            server_turned_ids = [ts["id"] for ts in server_turned]
            turned_enemies = [ts for ts in turned_enemies if ts.id in server_turned_ids]
            local_turned_ids = [ts.id for ts in turned_enemies]
            for s_ts in server_turned:
                if s_ts["id"] not in local_turned_ids:
                    from skeleton_rounds import TurnedSkeleton

                    visual_ts = TurnedSkeleton()
                    visual_ts.id = s_ts["id"]
                    visual_ts.x = s_ts["x"]
                    visual_ts.y = s_ts["y"]
                    turned_enemies.append(visual_ts)
                else:
                    for local_ts in turned_enemies:
                        if local_ts.id == s_ts["id"]:
                            local_ts.x = s_ts["x"]
                            local_ts.y = s_ts["y"]

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
        now = pygame.time.get_ticks()

        for e in round_manager.enemies:
            if e.frames and (now - e.last_update > e.frame_time):
                e.current_frame = (e.current_frame + 1) % len(e.frames)
                e.last_update = now
            e.draw(screen)

        for te in turned_enemies:
            if te.frames and (now - te.last_update > te.frame_time):
                te.current_frame = (te.current_frame + 1) % len(te.frames)
                te.last_update = now
            te.draw(screen)

        for t in placed_towers:
            t.draw(screen, n.player_id)

        if 'current_game_state' in locals() and current_game_state:
            from towers import ManipulationProjectile, Kamehameha, Explosion

            for p in current_game_state.get("projectiles", []):
                if p.get("proj_type") == "manipulation":
                    projectile = ManipulationProjectile(p["x"], p["y"], 0, 0, 0, 0, 0)
                else:
                    projectile = Kamehameha(p["x"], p["y"], 0, 0, 0, p["size"], False, False)
                projectile.draw(screen)
            for ex_data in current_game_state.get("explosions", []):
                ex = Explosion(ex_data['x'], ex_data['y'], None, 0, ex_data['max_radius'], 0, 0)
                ex.timer = ex_data.get('timer', 10)
                ex.draw(screen)

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
            if not is_on_path(m_pos[0], m_pos[1], game_data.path_points, 50) and not is_overlapping_tower(m_pos[0],
                                                                                                          m_pos[1],
                                                                                                          placed_towers,
                                                                                                          50):
                pygame.draw.circle(range_surface, (0, 0, 255, 100), (radius, radius), radius)
            else:
                pygame.draw.circle(range_surface, (255, 0, 0, 100), (radius, radius), radius)
            pygame.draw.circle(range_surface, (255, 0, 255, 255), (radius, radius), radius, 2)
            screen.blit(range_surface, (m_pos[0] - radius, m_pos[1] - radius))

            from load_assets import load_image

            icon = load_image(get_tower(dragging_tower)[0], alpha=True)
            icon = pygame.transform.scale(icon, (60, 60))
            if icon: screen.blit(icon, icon.get_rect(center=m_pos))

    elif current_state == "WIN_SCREEN":
        screen.fill((15, 35, 15))  # Dark green victory landscape theme
        win_title_font = pygame.font.Font(MineFont, 90)
        win_btn_font = pygame.font.Font(MineFont, 35)

        title_surf = win_title_font.render("VICTORY!", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(1920 // 2, 400))
        screen.blit(title_surf, title_rect)

        # "Return to Lobby List" button interface bounds
        return_btn_rect = pygame.Rect(1920 // 2 - 200, 650, 400, 80)
        pygame.draw.rect(screen, (50, 180, 50), return_btn_rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), return_btn_rect, 3, border_radius=12)

        btn_text = win_btn_font.render("Return to Lobbies", True, (255, 255, 255))
        screen.blit(btn_text, btn_text.get_rect(center=return_btn_rect.center))

    error_popup.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
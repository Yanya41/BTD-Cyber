from load_assets import load_image, screen
import math
from rounds import Round
from towers import TowerManager, Explosion
from game_data import Data
from network import Network

MineFont = r'Images\MineFont.ttf'
goku_icon_path = r"Cards\goku.png"
goku_idle_path = r"goku_idle.png"
goku_shoot_path = r"goku_shoot.png"

archer_icon_path = r"Cards\wizard.png"
archer_idle_path = r"archer_idle.png"
archer_shoot_path = r"archer_shoot.png"
ubw_icon_path = r"unlimited_blade_works.png"

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
placed_towers, projectiles = [], []
dragging_tower, selected_tower = None, None
abilities = Abilities(pygame.font.Font(MineFont, 20), placed_towers)

explosions = []

# Main Game Loop
running = True
while running:
    m_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

        if event.type == pygame.MOUSEBUTTONDOWN: #handle all mouse button presses here
            mx, my = m_pos
            # upgrade panel
            if selected_tower and upgrade_panel.panel_upgrade.collidepoint(mx, my):
                if upgrade_panel.btn_left.collidepoint(mx, my):
                    selected_tower.upgrade_left(game_data, placed_towers)
                elif upgrade_panel.btn_right.collidepoint(mx, my):
                    selected_tower.upgrade_right(game_data, placed_towers)
                elif upgrade_panel.btn_target.collidepoint(mx, my):
                    selected_tower.target_mode = "strong" if selected_tower.target_mode == "first" else "first"

            # start round button
            elif 1670 <= mx <= 1870 and 950 <= my <= 1000:
                round_manager.start_next_round()

            # the "shop"
            elif 1620 <= mx <= 1920 and 200 <= my <= 300:
                if game_data.current_cash >= 550:
                    dragging_tower = "goku"

            elif 1620 <= mx <= 1920 and 350 <= my <= 450:
                if game_data.current_cash >= 350:
                    dragging_tower = "archer"

            elif abilities.btn_ubw and abilities.btn_ubw.collidepoint(mx, my):
                if abilities.ubw_cooldown == 0:
                    abilities.ubw_cooldown = 60 * 60  # 60 seconds at 60 fps
                    ubw_owner = next((t for t in placed_towers if t.tower_type == "archer" and t.path_left == 3), None)
                    for e in round_manager.enemies:
                        explosions.append(Explosion(e.x, e.y, ubw_owner, 50, 1, True, False))

            #deselect tower if clicking on something else
            else:
                selected_tower = next((t for t in placed_towers if math.hypot(mx - t.x, my - t.y) < 40), None)

        if event.type == pygame.MOUSEBUTTONUP:
            if dragging_tower and m_pos[0] < 1620:
                if not is_on_path(m_pos[0], m_pos[1], game_data.path_points, 50) and not is_overlapping_tower(m_pos[0], m_pos[1], placed_towers, 50):
                    new_t = tower_manager.create_tower(dragging_tower, m_pos[0], m_pos[1])
                    placed_towers.append(new_t)
                    game_data.current_cash -= new_t.cost
                dragging_tower = None
            elif dragging_tower and m_pos[0] > 1620:
                dragging_tower = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                round_manager.start_next_round()
    # logic section
    round_manager.update()

    # Move Skeletons & Handle Leaks
    for e in round_manager.enemies[:]:
        if e.move(e.dmg):
            round_manager.enemies.remove(e)
            game_data.current_hp -= e.dmg  # Damage the player

    # towers shooting
    for t in placed_towers:
        if t.tower_type == "archer":
            if t.charging:
                if t.charge_target.hp <= 0 or math.hypot(t.charge_target.x - t.x, t.charge_target.y - t.y) > t.range:
                    t.charging = False  # Cancel charge if target dies or moves out of range
                elif pygame.time.get_ticks() - t.charge_start > 3000:
                    # shoot explosion
                    dmg, _, _, exp_radius, ubw, explode = t.get_stats()
                    if explode:
                        # Create multiple explosions around the target
                        num_explosions = 5
                        for i in range(num_explosions):
                            angle = i * (360 / num_explosions)
                            rad = math.radians(angle)
                            ex = t.charge_target.x + math.cos(rad) * 50  # Spread around target
                            ey = t.charge_target.y + math.sin(rad) * 50
                            explosions.append(Explosion(ex, ey, t, dmg, exp_radius, ubw, explode))
                    else:
                        result = t.shoot(t.charge_target)
                        explosions.append(result)
                    t.charging = False
                    t.last_shot_time = pygame.time.get_ticks()
                else:
                    # Update angle to follow the target
                    dx = t.charge_target.x - t.x
                    dy = t.charge_target.y - t.y
                    t.angle = math.degrees(math.atan2(-dy, dx))
            else:
                # check if he can shoot and start charging
                if t.can_shoot():
                    if t.target_mode == "strong":
                        target = max((e for e in round_manager.enemies if math.hypot(e.x - t.x, e.y - t.y) <= t.range), key=lambda e: e.hp, default=None)
                    else:
                        target = max((e for e in round_manager.enemies if math.hypot(e.x - t.x, e.y - t.y) <= t.range), key=lambda e: e.target_index, default=None)
                    if target:
                        t.charging = True
                        t.charge_target = target
                        t.charge_start = pygame.time.get_ticks()
                        # set initial angle
                        dx = target.x - t.x
                        dy = target.y - t.y
                        t.angle = math.degrees(math.atan2(-dy, dx))
        else:
            # goku shooting
            if t.can_shoot():
                if t.target_mode == "strong":
                    target = max((e for e in round_manager.enemies if math.hypot(e.x - t.x, e.y - t.y) <= t.range), key=lambda e: e.hp, default=None)
                else:
                    target = max((e for e in round_manager.enemies if math.hypot(e.x - t.x, e.y - t.y) <= t.range), key=lambda e: e.target_index, default=None)
                if target:
                    result = t.shoot(target)
                    if t.tower_type == "goku":
                        result.owner = t
                        projectiles.append(result)

    # projectile damage & collision
    for p in projectiles[:]:
        p.move(round_manager.enemies)

        for e in round_manager.enemies:
            # Check if this projectile already hit this enemy
            if id(e) not in p.hit_enemies:
                # Increased collision distance to 45 for better reliability
                if math.hypot(p.x - e.x, p.y - e.y) < 45:
                    e.hp -= p.dmg
                    if hasattr(p,'owner'):
                        if e.hp < 0:
                            p.owner.damage_dealt += (p.dmg + e.hp) # Track damage for the tower that shot this projectile
                        else:
                            p.owner.damage_dealt += p.dmg
                    p.hit_enemies.append(id(e))
                    p.pierce -= 1
                    if p.pierce <= 0:
                        if p in projectiles: projectiles.remove(p)
                        break

        # Remove off-screen orbs
        if p.x < -50 or p.x > 1970 or p.y < -50 or p.y > 1130:
            if p in projectiles: projectiles.remove(p)

    # Remove dead enemies and trigger death spawns
    surviving_enemies = []
    for e in round_manager.enemies:
        if e.hp > 0:
            surviving_enemies.append(e)
        else:
            # Enemy died! Give the player cash
            game_data.current_cash += getattr(e, 'cash_price', 1)

            # Check if this enemy drops things when it dies (like the Barrel)
            if hasattr(e, 'on_death'):
                new_skeletons = e.on_death()
                surviving_enemies.extend(new_skeletons)

    # Update the official enemy list
    round_manager.enemies = surviving_enemies

    # drawing section
    draw_map.draw()
    for e in round_manager.enemies: e.draw(screen)
    for p in projectiles: p.draw(screen)
    # Draw explosions
    for ex in explosions[:]:
        ex.draw(screen)
        if ex.timer == 5:  # At the peak of the explosion, damage enemies in area
            for e in round_manager.enemies:
                if math.hypot(e.x - ex.x, e.y - ex.y) < 50:  # Within 50 pixels of explosion center
                    damage = ex.dmg  # Use the explosion's damage value
                    actual_damage = min(damage, e.hp)
                    e.hp -= actual_damage
                    ex.owner.damage_dealt += actual_damage  # Update the tower's damage counter
        if ex.timer <= 0:
            explosions.remove(ex)
    for t in placed_towers: t.draw(screen, 1)

    side_menu.draw()
    ui.draw(game_data, round_manager)
    if selected_tower:
        pygame.draw.circle(screen, (255, 255, 0), (selected_tower.x, selected_tower.y), selected_tower.range,2)  # Show range
        range_surface_0 = pygame.Surface((selected_tower.range*2, selected_tower.range*2), pygame.SRCALPHA)
        pygame.draw.circle(range_surface_0, (255, 255, 0, 50), (selected_tower.range, selected_tower.range), selected_tower.range)
        screen.blit(range_surface_0, (selected_tower.x - selected_tower.range, selected_tower.y - selected_tower.range))
        upgrade_panel.draw(selected_tower, placed_towers)

    if dragging_tower:
        radius = get_tower(dragging_tower)[1]
        range_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        if not is_on_path(m_pos[0], m_pos[1], game_data.path_points, 50) and not is_overlapping_tower(m_pos[0], m_pos[1], placed_towers, 50):
            pygame.draw.circle(range_surface, (0, 0, 255, 100), (radius, radius), radius)
        else:
            pygame.draw.circle(range_surface, (255, 0, 0, 100), (radius, radius), radius)

        pygame.draw.circle(range_surface, (255, 0, 255, 255), (radius, radius), radius, 2)
        screen.blit(range_surface, (m_pos[0] - radius, m_pos[1] - radius))

        icon = load_image(get_tower(dragging_tower)[0], alpha=True)
        if icon:
            rect = icon.get_rect(center=m_pos)
            screen.blit(icon, rect)
    abilities.draw()

    pygame.display.flip()
    clock.tick(60)

    # Update cooldowns
    for t in placed_towers:
        if hasattr(t, 'ubw_cooldown'):
            t.ubw_cooldown = max(0, t.ubw_cooldown - 16)

    abilities.ubw_cooldown = max(0, abilities.ubw_cooldown - 1)

pygame.quit()
from load_assets import load_image, screen
import pygame, math
from game_data import Data
from rounds import Round
from towers import Tower

MineFont = r'Images\MineFont.ttf'
goku_icon_path = r"Cards\goku.png"
goku_idle_path = r"goku_idle.png"
goku_shoot_path = r"goku_shoot.png"

# the map
class Map_Background:
    def __init__(self):
        self.path_points = Data().path_points
        self.color = (34, 139, 34)
        self.road_color = (139, 69, 19)

    def draw(self, screen):
        screen.fill(self.color)
        if len(self.path_points) > 1:
            pygame.draw.lines(screen, self.road_color, False, self.path_points, 50)
            for pt in self.path_points:
                pygame.draw.circle(screen, self.road_color, pt, 25)




class Upgrade_Panel: #this is the upgrade panel that is in the bottom left
    def __init__(self, font):
        self.font = font
        self.rect = pygame.Rect(0, 880, 400, 200)  # Bottom left corner panel
        self.color = (50, 50, 50)

        # Buttons relative to the panel
        self.btn_left = pygame.Rect(20, 920, 150, 50)
        self.btn_right = pygame.Rect(200, 920, 150, 50)

    def draw(self, screen, tower):
        if not tower:
            return  # Don't draw anything if no tower is selected

        pygame.draw.rect(screen, self.color, self.rect)

        # Title
        title = self.font.render(f"{tower.tower_type.upper()} Upgrades", True, (255, 255, 255))
        screen.blit(title, (120, 890))

        # Left Path Button
        pygame.draw.rect(screen, (0, 100, 200), self.btn_left)
        if tower.path_left < 3:
            cost_L = tower.left_costs[tower.path_left]
            text_L = self.font.render(f"Left: ${cost_L}", True, (255, 255, 255))
        else:
            text_L = self.font.render("MAXED", True, (200, 0, 0))
        screen.blit(text_L, (self.btn_left.x + 10, self.btn_left.y + 10))

        # Right Path Button
        pygame.draw.rect(screen, (200, 100, 0), self.btn_right)
        if tower.path_right < 3:
            cost_R = tower.right_costs[tower.path_right]
            text_R = self.font.render(f"Right: ${cost_R}", True, (255, 255, 255))
        else:
            text_R = self.font.render("MAXED", True, (200, 0, 0))
        screen.blit(text_R, (self.btn_right.x + 10, self.btn_right.y + 10))


class Side_Menu: #this is the right side menu where you can purchase towers
    def __init__(self, width):
        self.width = width
        self.rect = pygame.Rect(1920 - width, 0, width, 1080)
        self.color = (200, 200, 200)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        # Fix: Ensure path matches your folder structure
        goku_icon = load_image(goku_icon_path, scale_to=(100, 100), alpha=True)
        if goku_icon:
            screen.blit(goku_icon, (1920 - self.width + 100, 200))


class UI_Manager:
    def __init__(self, font):
        self.font = font
        self.buttons = []  # List to hold button data (rect, color, text)
        self.buttons.append((pygame.Rect(1670, 950, 200, 50), (0, 255, 0), "Start Round", (0, 0, 0)))  # start round button
        self.buttons.append((pygame.Rect(100, 50, 200, 50), (34, 139, 34), str(Data().current_hp) + " Health", (255, 0, 0)))  # health
        self.buttons.append((pygame.Rect(350, 50, 200, 50), (34, 139, 34), str(Data().starting_cash) + " Cash", (239, 191, 4)))  # cash
        self.buttons.append((pygame.Rect(600, 50, 200, 50), (34, 139, 34), str(Round().current_round), (0, 0, 0)))  # round number

    def draw(self, screen, data):
        for button in self.buttons:
            pygame.draw.rect(screen, button[1], button[0])
            label = button[2]
            if "Health" in label:
                text_surface = self.font.render(f"{data.current_hp} Health", True, button[3])
            elif "Cash" in label:
                text_surface = self.font.render(f"{data.current_cash} Cash", True, button[3])
            else:
                text_surface = self.font.render(label, True, button[3])

            text_rect = text_surface.get_rect(center=button[0].center)
            screen.blit(text_surface, text_rect)


# execution starts here
pygame.init()
clock = pygame.time.Clock()

game_data = Data()

draw_map = Map_Background()
side_menu = Side_Menu(300)
ui = UI_Manager(pygame.font.Font(MineFont, 25))
upgrade_panel = Upgrade_Panel(pygame.font.Font(MineFont, 20))
round_manager = Round()
tower_manager = Tower()
placed_towers, projectiles = [], []
dragging_tower, selected_tower = None, None

# Main Game Loop
running = True
while running:
    m_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

        if event.type == pygame.MOUSEBUTTONDOWN: #handle all mouse button presses here
            mx, my = m_pos
            # upgrade panel
            if selected_tower and upgrade_panel.rect.collidepoint(mx, my):
                if upgrade_panel.btn_left.collidepoint(mx, my):
                    selected_tower.upgrade_left(game_data)
                elif upgrade_panel.btn_right.collidepoint(mx, my):
                    selected_tower.upgrade_right(game_data)

            # start round button
            elif 1670 <= mx <= 1870 and 950 <= my <= 1000:
                round_manager.start_next_round()

            # the "shop"
            elif 1620 <= mx <= 1920 and 200 <= my <= 300:
                if game_data.current_cash >= 550:
                    dragging_tower = "goku"

            #deselect tower if clicking on something else
            else:
                selected_tower = next((t for t in placed_towers if math.hypot(mx - t.x, my - t.y) < 40), None)

        if event.type == pygame.MOUSEBUTTONUP:
            if dragging_tower and m_pos[0] < 1620:
                new_t = tower_manager.create_tower(dragging_tower, m_pos[0], m_pos[1])
                placed_towers.append(new_t)
                game_data.current_cash -= 550
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
        if t.can_shoot():
            for e in round_manager.enemies:
                if math.hypot(e.x - t.x, e.y - t.y) <= t.range:
                    projectiles.append(t.shoot(e))
                    break

    # projectile damage & collision
    for p in projectiles[:]:
        p.move(round_manager.enemies)

        for e in round_manager.enemies:
            # Check if this projectile already hit this enemy
            if id(e) not in p.hit_enemies:
                # Increased collision distance to 45 for better reliability
                if math.hypot(p.x - e.x, p.y - e.y) < 45:
                    e.hp -= p.dmg
                    p.hit_enemies.append(id(e))
                    p.pierce -= 1
                    if p.pierce <= 0:
                        if p in projectiles: projectiles.remove(p)
                        break

        # Remove off-screen orbs
        if p.x < -50 or p.x > 1970 or p.y < -50 or p.y > 1130:
            if p in projectiles: projectiles.remove(p)

    # Remove dead enemies
    round_manager.enemies = [e for e in round_manager.enemies if e.hp > 0]

    # drawing section
    draw_map.draw(screen)
    for e in round_manager.enemies: e.draw(screen)
    for p in projectiles: p.draw(screen)
    for t in placed_towers: t.draw(screen, 1)

    side_menu.draw(screen)
    ui.draw(screen, game_data)
    if selected_tower:
        pygame.draw.circle(screen, (255, 255, 0), (selected_tower.x, selected_tower.y), selected_tower.range,2)  # Show range
        upgrade_panel.draw(screen, selected_tower)

    if dragging_tower:
        icon = load_image(goku_idle_path, scale_to=(60, 60), alpha=True)
        if icon: screen.blit(icon, (m_pos[0] - 30, m_pos[1] - 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
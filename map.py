#the base configuration for the skeleton frames are 2, and frame rate is 0.1
from load_assets import load_image, background_image, screen
import pygame
from game_data import Data
from rounds import Round
import math
from towers import Tower
MineFont = r'Images\MineFont.ttf'
path_width = 40


# file names
image_folder = "Images"
background_filename = "map1.png"


#the gray side menu on the right
class Side_Menu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rect = pygame.Rect(1920 - width, 0, width, height)
        self.color = (200, 200, 200)  # Light gray
    def side_menu_text(self):
        pass


    #drawing things onto the side menu
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        wizard = load_image(r"Cards\wizard.png", scale_to=(100, 100), alpha=True)
        goku = load_image(r"Cards\goku.png", scale_to=(100, 100), alpha=True)
        screen.blit(goku, (1920 - self.width + 150, 200))
        screen.blit(wizard, (1920 - self.width + 20, 200))


class Buttons:
    def __init__(self):
        self.font = pygame.font.Font(MineFont, 25)
        self.buttons = []  # List to hold button data (rect, color, text)
        self.buttons.append((pygame.Rect(1670,950,200,50), (0, 255, 0), "Start Round", (0,0,0))) #start round button
        self.buttons.append((pygame.Rect(100,50,200,50), (34, 139, 34), str(Data().current_hp) + " Health",(255,0,0))) #health
        self.buttons.append((pygame.Rect(350,50,200,50), (34, 139, 34), str(Data().starting_cash) + " Cash",(239,191,4))) #cash

    def draw(self, screen, button):
        pygame.draw.rect(screen, button[1], button[0])
        label = button[2]

        # Check if this is the health button
        if "Health" in label:
            text_surface = self.font.render(f"{Data().current_hp} Health", True, button[3])
        elif "Cash" in label:
            text_surface = self.font.render(f"{Data().current_cash} Cash", True, button[3])
        else:
            text_surface = self.font.render(label, True, button[3])

        text_rect = text_surface.get_rect(center=button[0].center)
        screen.blit(text_surface, text_rect)

#the map background
class Map_Background:
    def __init__(self, color=(34, 139, 34)): # Default to Grass Green
        self.color = color
        # These are your specific path points
        self.path_points = [
            (0,168), (513,418), (611,184), (1358,350), (709,425), (700, 586), (758, 1080)
        ]
        self.road_color = (139, 69, 19) # Dirt Brown

    def draw(self, screen):
        # 1. Fill the screen with the grass color
        # This is where your error was; it needs an RGB tuple like (34, 139, 34)
        screen.fill(self.color)

        # 2. Draw the dirt road using your path points
        # Width 40 makes it a nice thick road for the skeletons
        if len(self.path_points) > 1:
            pygame.draw.lines(screen, self.road_color, False, self.path_points, 50)

            # 3. Smooth out the "joints" of the road with circles
            for pt in self.path_points:
                pygame.draw.circle(screen, self.road_color, pt, 25)


if __name__ == '__main__':
    #setup pygame and the screen
    pygame.init()
    clock = pygame.time.Clock()
    #create instances of the classes
    side_menu = Side_Menu(300, 1080)
    draw_map = Map_Background((34, 139, 34)) # Passing a Green RGB tuple
    draw_buttons = Buttons()
    round_manager = Round()
    enemies = round_manager.enemies

    projectiles = []
    tower_manager = Tower()
    placed_towers = []
    dragging_tower = None  # Holds the type string (e.g., "goku")

    #the main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if 1670 <= mx <= 1870 and 950 <= my <= 1000: # Check if the "Start Round" button is clicked
                    round_manager.start_next_round()
                    # Goku Icon
                elif (1920 - side_menu.width + 150) <= mx <= (1920 - side_menu.width + 250) and 200 <= my <= 300:
                    if Data().current_cash >= 550:
                        dragging_tower = "goku"

            if event.type == pygame.MOUSEBUTTONUP:
                if dragging_tower:
                    mx, my = pygame.mouse.get_pos()
                    # Check if the mouse is released within the map area (not on the side menu)
                    if mx < 1920 - side_menu.width:
                        new_tower = tower_manager.create_tower(dragging_tower,mx,my)
                        new_tower.x, new_tower.y = mx, my
                        placed_towers.append(new_tower)
                        Data().current_cash -= new_tower.cost
                    dragging_tower = None  # Stop dragging after placing

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: # Start the next round when space is pressed
                    round_manager.start_next_round()
        round_manager.update()
        round_manager.enemies = [e for e in round_manager.enemies if e.move(e.dmg) == False] #if enemy doesn't move, it means it reached the end and is removed and deals dmg

        #draw everything
        draw_map.draw(screen)
        side_menu.draw(screen)
        for btn in draw_buttons.buttons:
            draw_buttons.draw(screen, btn)
        for enemy in round_manager.enemies:
            enemy.draw(screen)

        for tower in placed_towers:
            # Use your load_image logic here to draw the tower at tower.x, tower.y
            pass

        # Draw the "Ghost" tower attached to mouse
        if dragging_tower:
            mx, my = pygame.mouse.get_pos()
            # Draw a semi-transparent range circle
            range_val = 200 if dragging_tower == "goku" else 150
            surface = pygame.Surface((range_val * 2, range_val * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (0, 0, 255, 50), (range_val, range_val), range_val)
            screen.blit(surface, (mx - range_val, my - range_val))

            # Draw the actual icon following the mouse
            icon_path = r"Cards\goku.png" if dragging_tower == "goku" else r"Cards\wizard.png"
            icon = load_image(icon_path, scale_to=(60, 60), alpha=True)
            screen.blit(icon, (mx - 30, my - 30))

        for tower in placed_towers:
            if tower.tower_type == "goku" and tower.can_shoot():
                # Find the first skeleton in range
                for enemy in round_manager.enemies:
                    dist = math.hypot(enemy.x - tower.x, enemy.y - tower.y)
                    if dist <= tower.range:
                        new_ball = tower.shoot(enemy)
                        projectiles.append(new_ball)
                        break  # Shoot only one skeleton per cooldown

        # Update and Draw Projectiles
        for p in projectiles[:]:
            p.move()
            p.draw(screen)
            # Remove projectile if it hit or if target is dead
            if p.reached_target or p.target.hp <= 0:
                if p in projectiles:
                    projectiles.remove(p)

        # Update Skeletons (clean up dead ones)
        round_manager.enemies = [e for e in round_manager.enemies if e.hp > 0]

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
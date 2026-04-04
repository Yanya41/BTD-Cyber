#the base configuration for the skeleton frames are 2, and frame rate is 0.1

from load_assets import load_image, background_image, screen
import pygame
import os
from game_data import Data
from rounds import Round

from pygame import MOUSEBUTTONDOWN


path_width = 40

# where the path goes through
path_points = [
    (0,168), (513,418), (611,184), (1358,350), (709,425), (700, 586), (758, 1080)
]

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
        archer = load_image(r"Cards\archer.png", scale_to=(100, 100), alpha=True)
        screen.blit(archer, (1920 - self.width + 150, 200))
        screen.blit(wizard, (1920 - self.width + 20, 200))


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



    side_menu = Side_Menu(300, 1080)
    draw_map = Map_Background((34, 139, 34)) # Passing a Green RGB tuple

    round_manager = Round()
    #main game loop
    enemies = round_manager.enemies
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update Spawning
        round_manager.update()

        # Update Movement and DESPAWN
        # This line says: "Keep the enemy in the list ONLY IF enemy.move() is False"
        round_manager.enemies = [e for e in round_manager.enemies if e.move() == False]

        # Draw everything
        draw_map.draw(screen)
        side_menu.draw(screen)
        for enemy in round_manager.enemies:
            enemy.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
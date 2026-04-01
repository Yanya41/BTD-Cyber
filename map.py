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
    def __init__(self, image):
        self.image = image
        screen.blit(self.image, (0, 0))

    # draw the map background
    def draw(self, screen):
        screen.blit(self.image, (0, 0))


if __name__ == '__main__':
    #setup pygame and the screen
    pygame.init()
    clock = pygame.time.Clock()



    side_menu = Side_Menu(300, 1080)
    draw_map = Map_Background(background_image)


    #main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                print(pygame.mouse.get_pos())
            if event.type == pygame.QUIT:
                running = False

        enemies = Round().enemies
        for i in range(len(enemies)):
            enemies[i-1].move()
        draw_map.draw(screen)
        side_menu.draw(screen)
        for i in range(len(enemies)):
            enemies[i-1].draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
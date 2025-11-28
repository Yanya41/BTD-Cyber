import pygame
import math

path_color = (180, 120, 60)  # Brown color for the path

path = [
    (50, 100),
    (500, 100),
    (500, 400),
    (300, 400),
    (300, 700),
    (800, 700),
    (800, 200),
    (1200, 200),
    (1200, 800),
    (1500, 800),
    (1500, 100),
]
class Map:
    class Map1:
        pass
    class Map2
        pass

class Bloon:
    def __init__(self, path, speed=2):
        self.path = path
        self.x, self.y = path[0]
        self.speed = speed
        self.target_index = 1

    def move(self):
        if self.target_index >= len(self.path):
            return  # bloon reached the end

        target_x, target_y = self.path[self.target_index]

        # direction vector
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist != 0:
            dx /= dist
            dy /= dist

        # move toward the target
        self.x += dx * self.speed
        self.y += dy * self.speed

        # if close enough, move to next waypoint
        if dist < self.speed:
            self.target_index += 1

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 12)

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    clock = pygame.time.Clock()

    bloon = Bloon(path)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(pygame.mouse.get_pos())
            if event.type == pygame.QUIT:
                running = False

        bloon.move()
        screen.fill((0, 0, 0))

        #draw path
        for i in range(len(path) - 1):
            rect = pygame.Rect(path[i][0] - 20, path[i][1] - 20, 100, 20)

            if path[i][0] == path[i + 1][0]:  # vertical
                rect.width = 40
                # Add 40 to length (20 for start cap, 20 for end cap)
                rect.height = abs(path[i + 1][1] - path[i][1]) + 40
                # Subtract 20 to start drawing from the top edge, not the center
                rect.y = min(path[i][1], path[i + 1][1]) - 20
            else:  # horizontal
                # Add 40 to length
                rect.width = abs(path[i + 1][0] - path[i][0]) + 40
                rect.height = 40
                # Subtract 20 to start drawing from the left edge, not the center
                rect.x = min(path[i][0], path[i + 1][0]) - 20

            pygame.draw.rect(screen, path_color, rect, 0, border_radius=4)

        bloon.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

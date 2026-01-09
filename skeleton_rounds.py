import math
import pygame
from game_data import Data
data = Data()
class Skeleton:
    def __init__(self, speed, frames=None, frame_time=0.1):
        self.path_points = data.path_points
        self.x, self.y = data.path_points[0]
        self.speed = speed
        self.target_index = 1
        self.path_points = data.path_points
        self.frames = frames if frames else []
        self.current_frame = 0
        self.frame_time = frame_time * 1000
        self.last_update = pygame.time.get_ticks()

        self.flip_image = False

    def move(self):
        if self.target_index >= len(self.path_points):
            return

        target_x, target_y = self.path_points[self.target_index]
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if self.frames:
            now = pygame.time.get_ticks()
            if now - self.last_update > self.frame_time:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.last_update = now

        if dist != 0:
            dx_norm = dx / dist
            dy_norm = dy / dist
            self.x += dx_norm * self.speed
            self.y += dy_norm * self.speed

            self.flip_image = dx_norm < -0.1

        if dist < self.speed:
            self.target_index += 1

    def draw(self, screen):
        if self.frames:
            image = self.frames[self.current_frame]
            image = pygame.transform.flip(image, self.flip_image, False)
            rect = image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(image, rect)
        else:
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 12)


class Round:
    def __init__(self):
        self.enemies = {}
        self.current_round = 1
        self.round_in_progress = False
        self.enemy_id = 1


    def rounds_spawns(self):
        if self.current_round == 1:
            enemy = Skeleton()


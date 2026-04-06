from load_assets import skeleton_frames, shielded_skeleton_frames
import math
import pygame
from game_data import Data
data = Data()
class Enemy:
    def __init__(self, speed, frame_time=0.1):
        self.path_points = data.path_points
        self.x, self.y = data.path_points[0]
        self.speed = speed
        self.target_index = 1
        self.current_frame = 0
        self.frame_time = frame_time * 1000
        self.last_update = pygame.time.get_ticks()
        self.flip_image = False
        self.frames = []  # To be set by subclasses

    def move(self,dmg):
        if self.target_index >= len(self.path_points):
            # This now refers to the same global data object
            Data().update_hp(dmg)
            return True

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

        return False

    def draw(self, screen):
        if self.frames:
            image = self.frames[self.current_frame]
            image = pygame.transform.flip(image, self.flip_image, False)
            rect = image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(image, rect)
        else:
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 12)

class Skeleton(Enemy):
    def __init__(self, speed=2, frame_time=(1000//60)):
        super().__init__(speed)
        self.frames = skeleton_frames
        self.frame_time = frame_time
        self.dmg = 1
        self.hp = 1

class ShieldedSkeleton(Enemy):
    def __init__(self, speed=1.5, frame_time=1000//60):
        super().__init__(speed)
        self.frames = shielded_skeleton_frames
        self.frame_time = frame_time
        self.dmg = 2
        self.hp = 3

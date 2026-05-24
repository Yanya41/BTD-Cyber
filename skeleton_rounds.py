from load_assets import skeleton_frames, shielded_skeleton_frames
import math
import random
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
        self.frames = []

        self.width = 24
        self.height = 24
        self.id = random.randint(1, 1000000)

    def get_hurtbox(self):
        return pygame.Rect(
            int(self.x - self.width / 2),
            int(self.y - self.height / 2),
            self.width, self.height
        )

    def move(self, dmg):
        if self.target_index >= len(self.path_points):
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

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'speed': self.speed,
            'target_index': self.target_index,
            'current_frame': self.current_frame,
            'frame_time': self.frame_time,
            'last_update': self.last_update,
            'flip_image': self.flip_image,
            'width': self.width,
            'height': self.height,
            'id': self.id,
            'type': self.__class__.__name__
        }


class Skeleton(Enemy):
    def __init__(self, speed=2, frame_time=(1000 // 60)):
        super().__init__(speed)
        self.frames = skeleton_frames
        self.frame_time = frame_time
        self.dmg = 1
        self.hp = 1
        self.cash_price = 1

    def to_dict(self):
        d = super().to_dict()
        d.update({'dmg': self.dmg, 'hp': self.hp, 'cash_price': self.cash_price})
        return d


class ShieldedSkeleton(Enemy):
    def __init__(self, speed=1.5, frame_time=1000 // 60):
        super().__init__(speed)
        self.frames = shielded_skeleton_frames
        self.frame_time = frame_time
        self.dmg = 2
        self.hp = 2
        self.cash_price = 2

    def to_dict(self):
        d = super().to_dict()
        d.update({'dmg': self.dmg, 'hp': self.hp, 'cash_price': self.cash_price})
        return d


class SkeletonBarrel(Enemy):
    def __init__(self, speed=1.2, frame_time=1000 // 60):
        super().__init__(speed)
        self.frames = []
        self.frame_time = frame_time
        self.dmg = 3
        self.hp = 8
        self.cash_price = 5

    def on_death(self):
        spawned = []
        for _ in range(3):
            skel = Skeleton(speed=3)
            skel.x = self.x + random.randint(-15, 15)
            skel.y = self.y + random.randint(-15, 15)
            skel.target_index = self.target_index
            spawned.append(skel)
        return spawned

    def draw(self, screen):
        x, y = int(self.x), int(self.y)

        pygame.draw.line(screen, (210, 180, 140), (x - 5, y - 10), (x - 15, y - 40), 2)
        pygame.draw.line(screen, (210, 180, 140), (x + 5, y - 10), (x + 15, y - 45), 2)

        pygame.draw.circle(screen, (220, 50, 50), (x - 15, y - 50), 12)
        pygame.draw.polygon(screen, (220, 50, 50), [(x - 15, y - 38), (x - 19, y - 34), (x - 11, y - 34)])

        pygame.draw.circle(screen, (50, 100, 220), (x + 15, y - 57), 14)
        pygame.draw.polygon(screen, (50, 100, 220), [(x + 15, y - 43), (x + 11, y - 39), (x + 19, y - 39)])

        barrel_rect = pygame.Rect(x - 22, y - 18, 44, 36)
        pygame.draw.ellipse(screen, (100, 65, 35), barrel_rect)
        pygame.draw.ellipse(screen, (130, 130, 135), pygame.Rect(x - 22, y - 18, 44, 36), 3)
        pygame.draw.line(screen, (130, 130, 135), (x - 14, y - 16), (x - 14, y + 16), 4)
        pygame.draw.line(screen, (130, 130, 135), (x + 14, y - 16), (x + 14, y + 16), 4)

        pygame.draw.circle(screen, (240, 240, 240), (x, y - 3), 7)
        pygame.draw.rect(screen, (240, 240, 240), (x - 4, y + 2, 8, 6))
        pygame.draw.circle(screen, (100, 65, 35), (x - 3, y - 3), 2)
        pygame.draw.circle(screen, (100, 65, 35), (x + 3, y - 3), 2)
        pygame.draw.line(screen, (100, 65, 35), (x - 1, y + 3), (x - 1, y + 7), 1)
        pygame.draw.line(screen, (100, 65, 35), (x + 1, y + 3), (x + 1, y + 7), 1)

    def to_dict(self):
        d = super().to_dict()
        d.update({'dmg': self.dmg, 'hp': self.hp, 'cash_price': self.cash_price})
        return d


class TurnedSkeleton(Enemy):
    """
    A friendly unit that walks backwards along the path.
    Real logic lives on the server — this class is rendering only.
    """
    def __init__(self, speed=2, frame_time=1000 // 60):
        super().__init__(speed)
        self.frames = skeleton_frames
        self.frame_time = frame_time
        self.dmg = 0
        self.hp = 1
        self.cash_price = 0

    def draw(self, screen):
        # Green glow underneath to distinguish from enemies
        pygame.draw.circle(screen, (0, 220, 80), (int(self.x), int(self.y)), 14, 3)

        if self.frames:
            image = self.frames[self.current_frame]
            # Always flipped — walking backwards
            image = pygame.transform.flip(image, True, False)
            rect = image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(image, rect)
        else:
            pygame.draw.circle(screen, (0, 255, 0), (int(self.x), int(self.y)), 12)

    def to_dict(self):
        d = super().to_dict()
        d.update({
            'dmg': self.dmg,
            'hp': self.hp,
            'cash_price': self.cash_price,
            'type': 'TurnedSkeleton'
        })
        return d

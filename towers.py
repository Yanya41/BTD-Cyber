import math
import pygame

class Projectile:
    def __init__(self, x, y, target, damage):
        self.x = x
        self.y = y
        self.target = target  # The specific Skeleton object
        self.damage = damage
        self.speed = 10
        self.radius = 8
        self.reached_target = False

    def move(self):
        # Calculate distance to target skeleton
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.speed:
            # Hit the skeleton
            self.target.hp -= self.damage
            self.reached_target = True
        else:
            # Move toward the skeleton
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def draw(self, screen):
        # Draw the light blue sphere
        pygame.draw.circle(screen, (173, 216, 230), (int(self.x), int(self.y)), self.radius)
        # Add a small white glow in the center
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius // 2)


class Tower:
    def __init__(self):
        self.tower_count = {}
        self.id = 1

    def create_tower(self, tower_type, x, y):
        if tower_type == "wizard":
            tower = Tower.Wizard(self.id, x, y)
        elif tower_type == "goku":
            tower = Tower.Goku(self.id, x, y)
        else:
            raise ValueError("Unknown tower type")

        self.tower_count[tower.id] = tower
        self.id += 1
        return tower

    class Wizard:
        def __init__(self, tower_id,x,y):
            self.id = tower_id
            self.x = x
            self.y = y
            self.tower_type = "wizard"
            self.damage = 2
            self.attack_speed = 1.5
            self.range = 150
            self.cost = 150

    class Goku:
        def __init__(self, tower_id, x, y):
            self.id = tower_id
            self.x = x
            self.y = y
            self.tower_type = "goku"
            self.damage = 3
            self.attack_speed = 3.0  # Seconds between shots
            self.range = 200
            self.last_shot_time = 0
            self.cost = 300

        def can_shoot(self):
            now = pygame.time.get_ticks()
            if now - self.last_shot_time > (self.attack_speed * 1000):
                return True
            return False

        def shoot(self, target):
            self.last_shot_time = pygame.time.get_ticks()
            return Projectile(self.x, self.y, target, self.damage)





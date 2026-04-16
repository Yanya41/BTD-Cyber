import pygame
import math


class Projectile:
    def __init__(self, x, y, angle, dmg, pierce, size, seeking, returns):
        self.x, self.y = x, y
        self.dmg = dmg
        self.pierce = pierce
        self.size = size
        self.seeking = seeking
        self.returns = returns

        self.speed = 8
        self.hit_enemies = []  # Stores IDs of enemies already hit to prevent double-damage
        self.has_returned = False

        # Initial Velocity calculation
        rad = math.radians(-angle)
        self.vx = math.cos(rad) * self.speed
        self.vy = math.sin(rad) * self.speed

    def move(self, enemies):
        # 1. SEEKING LOGIC (Right Path Lvl 3)
        if self.seeking and enemies:
            # Find the closest skeleton
            target = min(enemies, key=lambda e: math.hypot(self.x - e.x, self.y - e.y))
            dx, dy = target.x - self.x, target.y - self.y
            dist = math.hypot(dx, dy)

            if dist > 0:
                # Turn strength 0.6 keeps it from being "too" perfect, makes it look natural
                self.vx += (dx / dist) * 0.6
                self.vy += (dy / dist) * 0.6

                # Normalize so speed stays at exactly 12
                mag = math.hypot(self.vx, self.vy)
                self.vx = (self.vx / mag) * self.speed
                self.vy = (self.vy / mag) * self.speed

        # 2. UPDATE POSITION
        self.x += self.vx
        self.y += self.vy

        # 3. RETURN LOGIC (Left Path Lvl 3)
        if self.returns and not self.has_returned:
            # Check screen boundaries (1920x1080)
            if self.x < 0 or self.x > 1920 or self.y < 0 or self.y > 1080:
                self.vx *= -1
                self.vy *= -1
                self.has_returned = True  # Can only return once

    def draw(self, screen):
        # Draw the orb based on the 'size' upgrade
        pygame.draw.circle(screen, (173, 216, 230), (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.size // 2)


class Goku:
    def __init__(self, tower_id, x, y):
        self.id = tower_id
        self.x, self.y = x, y
        self.tower_type = "goku"
        self.cost = 550

        # Upgrade Path Levels (0 to 3)
        self.path_left = 0
        self.path_right = 0

        # Base Stats
        self.base_dmg = 2
        self.base_speed = 1500  # ms
        self.base_pierce = 2
        self.base_size = 10
        self.base_range = 250

        self.angle = 270
        self.last_shot_time = 0

        self.left_costs = [200, 450, 1200]
        self.right_costs = [150, 400, 1000]

        # Sprite Loading
        try:
            self.idle_img = pygame.image.load(r"Images\goku_idle.png").convert_alpha()
            self.shoot_img = pygame.image.load(r"Images\goku_shoot.png").convert_alpha()
        except:
            # Error fallback
            self.idle_img = pygame.Surface((60, 60))
            self.idle_img.fill((255, 0, 255))
            self.shoot_img = self.idle_img

    def upgrade_left(self, game_data):
        if self.path_left == 2 and self.path_right == 3:
            return False
        if self.path_left < 3 and game_data.current_cash >= self.left_costs[self.path_left]:
            game_data.current_cash -= self.left_costs[self.path_left]
            self.path_left += 1
            return True
        return False

    def upgrade_right(self, game_data):
        if self.path_left == 3 and self.path_right == 2:
            return False
        if self.path_right < 3 and game_data.current_cash >= self.right_costs[self.path_right]:
            game_data.current_cash -= self.right_costs[self.path_right]
            self.path_right += 1
            return True
        return False

    @property
    def range(self):
        # Range can stay static or increase with upgrades here if you want
        return self.base_range

    def get_stats(self):
        """Calculates current stats based on upgrade paths."""
        # LEFT PATH: Speed -> Size -> Returns
        speed = self.base_speed - (200 if self.path_left >= 1 else 0)  # -0.2s (200ms) per level
        size = self.base_size + (10 if self.path_left >= 2 else 0)
        returns = True if self.path_left == 3 else False

        # RIGHT PATH: Pierce -> Damage -> Seeking
        pierce = self.base_pierce + (2 if self.path_right >= 1 else 0)
        dmg = self.base_dmg + (5 if self.path_right >= 2 else 0)
        seeking = True if self.path_right == 3 else False

        return dmg, speed, pierce, size, seeking, returns

    def can_shoot(self):
        _, speed, _, _, _, _ = self.get_stats()
        return pygame.time.get_ticks() - self.last_shot_time > speed

    def shoot(self, target):
        self.last_shot_time = pygame.time.get_ticks()
        dmg, _, pierce, size, seeking, returns = self.get_stats()

        # Update angle to face enemy
        dx = target.x - self.x
        dy = target.y - self.y
        self.angle = math.degrees(math.atan2(-dy, dx))

        return Projectile(self.x, self.y, self.angle, dmg, pierce, size, seeking, returns)

    def draw(self, screen, my_id):
        # Pick Sprite based on shooting state
        img = self.shoot_img if pygame.time.get_ticks() - self.last_shot_time < 200 else self.idle_img

        # Rotate and Re-center
        rotated_img = pygame.transform.rotate(img, self.angle + 90)
        rect = rotated_img.get_rect(center=(self.x, self.y))
        screen.blit(rotated_img, rect)


class Tower:
    """Helper class to spawn towers."""

    def create_tower(self, tower_type, x, y):
        if tower_type == "goku":
            return Goku(0, x, y)
        return None
import pygame
import math
import random
import os



class Explosion:
    def __init__(self, x, y, owner, dmg, explosion_radius, ubw, explode):
        self.x, self.y = x, y
        self.owner = owner
        self.dmg = dmg
        self.timer = 10  # How many frames the explosion lasts
        self.max_radius = 50
        self.particles = []
        self.explosion_radius = explosion_radius
        self.ubw = ubw
        self.explosion = explode
        
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 4)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append({'x': self.x, 'y': self.y, 'vx': vx, 'vy': vy, 'life': 15})

    def draw(self, screen):
        # Calculate radius based on timer for an expanding/fading effect
        radius = self.max_radius * (1 - (self.timer / 10))
        pygame.draw.circle(screen, (255, 165, 0), (int(self.x), int(self.y)), int(radius)) # Orange
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), int(radius // 2)) # White core
        
        # Update and draw particles
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)
            else:
                size = max(1, p['life'] // 3)
                pygame.draw.circle(screen, (255, 100, 0), (int(p['x']), int(p['y'])), size)
        
        self.timer -= 1

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'owner_id': self.owner.id if self.owner else None,
            'dmg': self.dmg,
            'timer': self.timer,
            'max_radius': self.max_radius,
            'particles': self.particles,
            'explosion_radius': self.explosion_radius,
            'ubw': self.ubw,
            'explosion': self.explosion
        }


class Kamehameha:
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
            target = min(enemies, key=lambda e: math.hypot(self.x - e.x, self.y - e.y))
            dx, dy = target.x - self.x, target.y - self.y
            dist = math.hypot(dx, dy)

            if dist > 0:
                self.vx += (dx / dist) * 0.6
                self.vy += (dy / dist) * 0.6

                mag = math.hypot(self.vx, self.vy)
                self.vx = (self.vx / mag) * self.speed
                self.vy = (self.vy / mag) * self.speed

        # 2. UPDATE POSITION
        self.x += self.vx
        self.y += self.vy

        # 3. RETURN LOGIC (Left Path Lvl 3)
        if self.returns and not self.has_returned:
            if self.x < 0 or self.x > 1920 or self.y < 0 or self.y > 1080:
                self.vx *= -1
                self.vy *= -1
                self.has_returned = True

    def draw(self, screen):
        pygame.draw.circle(screen, (173, 216, 230), (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.size // 2)

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'dmg': self.dmg,
            'pierce': self.pierce,
            'size': self.size,
            'seeking': self.seeking,
            'returns': self.returns,
            'speed': self.speed,
            'hit_enemies': self.hit_enemies,
            'has_returned': self.has_returned,
            'vx': self.vx,
            'vy': self.vy
        }


class Tower:
    """The base class that all towers will inherit from."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.damage_dealt = 0  # Now every tower automatically gets a damage counter!
        self.target_mode = "first"


class Archer(Tower):
    def __init__(self, tower_id, x, y):
        super().__init__(x, y)
        self.id = tower_id
        self.tower_type = "archer"
        self.cost = 600
        self.path_left = 0
        self.path_right = 0

        # Base Stats
        self.base_dmg = 5
        self.base_speed = 1000  # Archer shoots faster than Goku
        self.base_range = 1000

        self.angle = 270
        self.last_shot_time = 0
        self.charging = False
        self.charge_target = None
        self.charge_start = 0

        self.left_costs = [200, 450, 1200]
        self.right_costs = [150, 400, 1000]
        self.left_names = ["Stronger", "Powerful", "UBW"]
        self.right_names = ["Faster", "Bigger", "EXPLOSION"]

        self.idle_img = pygame.image.load(os.path.join("Images", "archer_idle.png")).convert_alpha()
        self.shoot_img = pygame.image.load(os.path.join("Images", "archer_shoot.png")).convert_alpha()

    def upgrade_left(self, game_data, placed_towers):
        if self.path_left == 2 and self.path_right == 3:
            return False
        if self.path_left < 3 and game_data.current_cash >= self.left_costs[self.path_left]:
            if self.path_left == 2:  # upgrading to UBW
                if any(t for t in placed_towers if t != self and t.tower_type == "archer" and t.path_left == 3):
                    return False
            game_data.current_cash -= self.left_costs[self.path_left]
            self.path_left += 1
            return True
        return False

    def upgrade_right(self, game_data, placed_towers):
        if self.path_left == 3 and self.path_right == 2:
            return False
        if self.path_right < 3 and game_data.current_cash >= self.right_costs[self.path_right]:
            if self.path_right == 2:  # upgrading to EXPLOSION
                if any(t for t in placed_towers if t != self and t.tower_type == "archer" and t.path_right == 3):
                    return False
            game_data.current_cash -= self.right_costs[self.path_right]
            self.path_right += 1
            return True
        return False

    def get_stats(self):
        dmg = self.base_dmg + (5 if self.path_left >= 1 else 0) + (10 if self.path_left >= 2 else 0)
        speed = self.base_speed - (200 if self.path_left >= 1 else 0)
        range_ = self.base_range
        exp_radius = 0
        ubw = True if self.path_left == 3 else False
        explode = True if self.path_right == 3 else False
        return dmg, speed, range_, exp_radius, ubw, explode

    @property
    def range(self):
        _, _, range_, _, _, _ = self.get_stats()
        return range_

    def can_shoot(self):
        _, speed, _, _, _, _ = self.get_stats()
        return pygame.time.get_ticks() - self.last_shot_time > speed

    def shoot(self, target):
        """Explosion Shooting Logic"""
        self.last_shot_time = pygame.time.get_ticks()

        # Calculate angle for rotation
        dx = target.x - self.x
        dy = target.y - self.y
        self.angle = math.degrees(math.atan2(-dy, dx))

        # Return an explosion at the target's location
        dmg, _, _, exp_radius, ubw, explode = self.get_stats()
        return Explosion(target.x, target.y, self, dmg, exp_radius, ubw, explode)  # Pass self as the owner

    def draw(self, screen, my_id):
        if self.charging:
            img = self.shoot_img
        else:
            img = self.shoot_img if pygame.time.get_ticks() - self.last_shot_time < 150 else self.idle_img
        rotated_img = pygame.transform.rotate(img, self.angle + 90)
        rect = rotated_img.get_rect(center=(self.x, self.y))
        screen.blit(rotated_img, rect)

    def to_dict(self):
        return {
            'id': self.id,
            'tower_type': self.tower_type,
            'x': self.x,
            'y': self.y,
            'damage_dealt': self.damage_dealt,
            'target_mode': self.target_mode,
            'cost': self.cost,
            'path_left': self.path_left,
            'path_right': self.path_right,
            'base_dmg': self.base_dmg,
            'base_speed': self.base_speed,
            'base_range': self.base_range,
            'angle': self.angle,
            'last_shot_time': self.last_shot_time,
            'charging': self.charging,
            'charge_target_id': self.charge_target.id if self.charge_target else None,
            'charge_start': self.charge_start,
            'left_costs': self.left_costs,
            'right_costs': self.right_costs,
            'left_names': self.left_names,
            'right_names': self.right_names
        }


class Goku(Tower):
    def __init__(self, tower_id, x, y):
        super().__init__(x, y)

        self.id = tower_id
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
        self.left_names = ["sonic", "gigantic", "boomerang"]
        self.right_names = ["piercing", "powerful", "seeking"]

        # Sprite Loading
        self.idle_img = pygame.image.load(os.path.join("Images", "goku_idle.png")).convert_alpha()
        self.shoot_img = pygame.image.load(os.path.join("Images", "goku_shoot.png")).convert_alpha()



    def upgrade_left(self, game_data, placed_towers):
        if self.path_left == 2 and self.path_right == 3:
            return False
        if self.path_left < 3 and game_data.current_cash >= self.left_costs[self.path_left]:
            if self.path_left == 2:  # upgrading to boomerang
                if any(t for t in placed_towers if t != self and t.tower_type == "goku" and t.path_left == 3):
                    return False
            game_data.current_cash -= self.left_costs[self.path_left]
            self.path_left += 1
            return True
        return False

    def upgrade_right(self, game_data, placed_towers):
        if self.path_left == 3 and self.path_right == 2:
            return False
        if self.path_right < 3 and game_data.current_cash >= self.right_costs[self.path_right]:
            if self.path_right == 2:  # upgrading to seeking
                if any(t for t in placed_towers if t != self and t.tower_type == "goku" and t.path_right == 3):
                    return False
            game_data.current_cash -= self.right_costs[self.path_right]
            self.path_right += 1
            return True
        return False

    @property
    def range(self):
        return self.base_range

    def get_stats(self):
        speed = self.base_speed - (200 if self.path_left >= 1 else 0)
        size = self.base_size + (10 if self.path_left >= 2 else 0)
        returns = True if self.path_left == 3 else False

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

        dx = target.x - self.x
        dy = target.y - self.y
        self.angle = math.degrees(math.atan2(-dy, dx))

        return Kamehameha(self.x, self.y, self.angle, dmg, pierce, size, seeking, returns)

    def draw(self, screen, my_id):
        img = self.shoot_img if pygame.time.get_ticks() - self.last_shot_time < 200 else self.idle_img
        rotated_img = pygame.transform.rotate(img, self.angle + 90)
        rect = rotated_img.get_rect(center=(self.x, self.y))
        screen.blit(rotated_img, rect)

    def to_dict(self):
        return {
            'id': self.id,
            'tower_type': self.tower_type,
            'x': self.x,
            'y': self.y,
            'damage_dealt': self.damage_dealt,
            'target_mode': self.target_mode,
            'cost': self.cost,
            'path_left': self.path_left,
            'path_right': self.path_right,
            'base_dmg': self.base_dmg,
            'base_speed': self.base_speed,
            'base_pierce': self.base_pierce,
            'base_size': self.base_size,
            'base_range': self.base_range,
            'angle': self.angle,
            'last_shot_time': self.last_shot_time,
            'left_costs': self.left_costs,
            'right_costs': self.right_costs,
            'left_names': self.left_names,
            'right_names': self.right_names
        }


class TowerManager:
    """Helper class to handle spawning towers."""
    def __init__(self):
        pass
    def create_tower(self, tower_type, x, y):
        if tower_type == "goku":
            return Goku(0, x, y)
        elif tower_type == "archer":
            return Archer(0, x, y)
        return None
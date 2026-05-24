from load_assets import load_image, screen
import math
from rounds import Round
from towers import TowerManager, Explosion
from game_data import Data
from network import Network
import os
from skeleton_rounds import Skeleton

MineFont = os.path.join('Images', 'MineFont.ttf')
goku_icon_path = os.path.join("Cards", "goku.png")
goku_idle_path = "goku_idle.png"
goku_shoot_path = "goku_shoot.png"

archer_icon_path = os.path.join("Cards", "archer.png")
archer_idle_path = "archer_idle.png"
archer_shoot_path = "archer_shoot.png"
ubw_icon_path = "unlimited_blade_works.png"

ayanokoji_icon_path = os.path.join("Cards", "ayanokoji.png")
ayanokoji_idle_path = "ayanokoji_idle.png"

import pygame
import random


class MapBackground:
    def __init__(self):
        from game_data import Data
        self.path_points = Data().path_points

        self.grass_base = (44, 149, 44)
        self.grass_dark = (34, 120, 34)
        self.grass_light = (54, 170, 54)
        self.shadow_color = (25, 90, 25)

        self.stone_edge = (120, 120, 125)
        self.dirt_base = (170, 120, 80)
        self.wagon_rut = (140, 95, 60)

        self.bg_surface = pygame.Surface((1920, 1080))
        self.render_static_background()

    def render_static_background(self):
        self.bg_surface.fill(self.grass_base)

        for _ in range(8000):
            x = random.randint(0, 1920)
            y = random.randint(0, 1080)
            color = random.choice([self.grass_dark, self.grass_light])
            radius = random.randint(1, 3)
            pygame.draw.circle(self.bg_surface, color, (x, y), radius)

        shadow_offset = 15
        shadow_points = [(x + shadow_offset, y + shadow_offset) for x, y in self.path_points]
        pygame.draw.lines(self.bg_surface, self.shadow_color, False, shadow_points, 60)
        for pt in shadow_points:
            pygame.draw.circle(self.bg_surface, self.shadow_color, pt, 30)

        layers = [
            (self.stone_edge, 60),
            (self.dirt_base, 50),
            (self.wagon_rut, 30),
            (self.dirt_base, 14)
        ]

        for color, width in layers:
            pygame.draw.lines(self.bg_surface, color, False, self.path_points, width)
            for pt in self.path_points:
                pygame.draw.circle(self.bg_surface, color, pt, width // 2)

    def draw(self):
        screen.blit(self.bg_surface, (0, 0))


class Abilities:
    def __init__(self, font, towers):
        self.font = font
        self.tower = towers
        self.ubw_icon = load_image(ubw_icon_path, alpha=True)
        self.btn_ubw = None
        self.ubw_cooldown = 0

    def draw(self):
        if any(t for t in self.tower if t.tower_type == "archer" and t.path_left == 3):
            self.btn_ubw = screen.blit(self.ubw_icon, (10, 1000))
        else:
            self.btn_ubw = None


class UpgradePanel:
    def __init__(self, font):
        self.font = font
        self.panel_upgrade = pygame.Rect(1520, 0, 400, 200)
        self.gray = (50, 50, 50)
        self.red = (200, 100, 100)

        self.btn_left = pygame.Rect(1540, 10, 150, 50)
        self.btn_right = pygame.Rect(1750, 10, 150, 50)
        self.btn_target = pygame.Rect(1750, 100, 120, 50)
        self.btn_sell = pygame.Rect(1850, 150, 120, 50)

    def draw(self, tower, placed_towers):
        if not tower:
            return

        pygame.draw.rect(screen, self.gray, self.panel_upgrade)

        title = self.font.render(f"{tower.tower_type.upper()} Upgrades", True, (255, 255, 255))
        screen.blit(title, (1630, 170))

        sell_btn_text = self.font.render("Sell", True, (255, 255, 255))
        screen.blit(sell_btn_text, (self.btn_sell.x, self.btn_sell.y))

        dmg_text = self.font.render(f"Damage: {getattr(tower, 'damage_dealt')}", True, (255, 255, 255))
        screen.blit(dmg_text, (1550, 100))

        # --- Left Path Button ---
        pygame.draw.rect(screen, (50, 100, 200), self.btn_left)
        if (tower.path_left < 3 and tower.path_right < 3) or (tower.path_left < 2 and tower.path_right == 3):
            if tower.path_left == 2 and any(
                t for t in placed_towers
                if t != tower and t.tower_type == tower.tower_type and t.path_left == 3
            ):
                text_l = self.font.render("BOUGHT", True, self.red)
            else:
                cost_l = tower.left_costs[tower.path_left]
                text_l = self.font.render(f"Left: ${cost_l}", True, (255, 255, 255))
            name_l = tower.left_names[tower.path_left]
            name_text_l = self.font.render(name_l, True, (255, 255, 255))
            screen.blit(name_text_l, (self.btn_left.x + 10, self.btn_left.y + 30))
            screen.blit(text_l, (self.btn_left.x + 10, self.btn_left.y + 10))

        elif tower.path_right == 3 and tower.path_left == 2:
            text_l = self.font.render("LOCKED", True, self.red)
            screen.blit(text_l, (self.btn_left.x + 10, self.btn_left.y + 10))

        else:
            text_l = self.font.render("MAXED", True, self.red)
            screen.blit(text_l, (self.btn_left.x + 10, self.btn_left.y + 10))

        # --- Right Path Button ---
        pygame.draw.rect(screen, (50, 100, 200), self.btn_right)
        if (tower.path_right < 3 and tower.path_left < 3) or (tower.path_right < 2 and tower.path_left == 3):
            if tower.path_right == 2 and any(
                t for t in placed_towers
                if t != tower and t.tower_type == tower.tower_type and t.path_right == 3
            ):
                text_r = self.font.render("BOUGHT", True, self.red)
            else:
                cost_r = tower.right_costs[tower.path_right]
                text_r = self.font.render(f"Right: ${cost_r}", True, (255, 255, 255))
            name_r = tower.right_names[tower.path_right]
            name_text_r = self.font.render(name_r, True, (255, 255, 255))
            screen.blit(name_text_r, (self.btn_right.x + 10, self.btn_right.y + 30))

        elif tower.path_left == 3 and tower.path_right == 2:
            text_r = self.font.render("LOCKED", True, self.red)
            screen.blit(text_r, (self.btn_right.x + 10, self.btn_right.y + 10))

        else:
            text_r = self.font.render("MAXED", True, self.red)

        screen.blit(text_r, (self.btn_right.x + 10, self.btn_right.y + 10))

        # --- Targeting Mode Button ---
        target_mode_text = "Target: " + tower.target_mode.capitalize()
        text_t = self.font.render(target_mode_text, True, (255, 0, 0))
        screen.blit(text_t, (self.btn_target.x, self.btn_target.y))


class SideMenu:
    def __init__(self, width):
        self.width = width
        self.rect = pygame.Rect(1920 - width, 0, width, 1080)
        self.color = (200, 200, 200)

        # FIX: Load images once in __init__, not every frame in draw()
        self.goku_icon = load_image(goku_icon_path, scale_to=(100, 100), alpha=True)
        self.archer_icon = load_image(archer_icon_path, scale_to=(100, 100), alpha=True)
        self.ayanokoji_icon = load_image(ayanokoji_icon_path, scale_to=(100, 100), alpha=True)

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.goku_icon, (1920 - self.width + 100, 200))
        screen.blit(self.archer_icon, (1920 - self.width + 100, 350))
        screen.blit(self.ayanokoji_icon, (1920 - self.width + 100, 500))


class UiManager:
    def __init__(self, font):
        self.font = font
        self.buttons = []
        self.buttons.append((pygame.Rect(1670, 950, 200, 50), (0, 255, 0), "Start Round", (0, 0, 0)))
        self.buttons.append((pygame.Rect(100, 50, 200, 50), (34, 139, 34), str(Data().current_hp) + " Health", (255, 0, 0)))
        self.buttons.append((pygame.Rect(350, 50, 200, 50), (34, 139, 34), str(Data().starting_cash) + " Cash", (239, 191, 4)))
        self.buttons.append((pygame.Rect(600, 50, 200, 50), (34, 139, 34), "Round " + str(Round().current_round), (0, 0, 0)))

    def draw(self, data, rounds):
        for button in self.buttons:
            pygame.draw.rect(screen, button[1], button[0])
            label = button[2]
            if "Health" in label:
                text_surface = self.font.render(f"{data.current_hp} Health", True, button[3])
            elif "Cash" in label:
                text_surface = self.font.render(f"{data.current_cash} Cash", True, button[3])
            elif "Round " in label:
                text_surface = self.font.render(f"Round {rounds.current_round}", True, button[3])
            else:
                text_surface = self.font.render(label, True, button[3])
            text_rect = text_surface.get_rect(center=button[0].center)
            screen.blit(text_surface, text_rect)


def is_on_path(px, py, path_points, minimum_distance):
    for i in range(len(path_points) - 1):
        x1, y1 = path_points[i]
        x2, y2 = path_points[i + 1]

        line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if line_len_sq == 0:
            dist = math.hypot(px - x1, py - y1)
        else:
            t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq
            t = max(0, min(1, t))
            proj_x = x1 + t * (x2 - x1)
            proj_y = y1 + t * (y2 - y1)
            dist = math.hypot(px - proj_x, py - proj_y)

        if dist < minimum_distance:
            return True

    return False


def is_overlapping_tower(px, py, placed_towers, min_distance):
    for t in placed_towers:
        if math.hypot(px - t.x, py - t.y) < min_distance:
            return True
    return False


def get_tower(tower_type):
    if tower_type == "goku":
        return goku_idle_path, 250
    if tower_type == "archer":
        return archer_idle_path, 1000
    if tower_type == "ayanokoji":
        return ayanokoji_idle_path, 300
    return None, 0

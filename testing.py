import pygame
import random


class Map_Background:
    def __init__(self):
        # We grab the path directly from your Data class logic
        from game_data import Data
        self.path_points = Data().path_points

        # --- ENHANCED COLOR PALETTE ---
        self.grass_base = (44, 149, 44)
        self.grass_dark = (34, 120, 34)
        self.grass_light = (54, 170, 54)
        self.shadow_color = (25, 90, 25)

        self.stone_edge = (120, 120, 125)
        self.dirt_base = (170, 120, 80)
        self.wagon_rut = (140, 95, 60)

        # Create a blank "canvas" the size of the screen to draw the map on ONCE
        self.bg_surface = pygame.Surface((1920, 1080))
        self.render_static_background()

    def render_static_background(self):
        """Draws the complex map once to save FPS."""
        # 1. Fill base grass
        self.bg_surface.fill(self.grass_base)

        # 2. Add Grass Detail (Procedural Noise)
        # Draws thousands of tiny dots to make it look like a textured field
        for _ in range(8000):
            x = random.randint(0, 1920)
            y = random.randint(0, 1080)
            color = random.choice([self.grass_dark, self.grass_light])
            radius = random.randint(1, 3)
            pygame.draw.circle(self.bg_surface, color, (x, y), radius)

        # 3. Draw Drop Shadow (Offset slightly down and right)
        shadow_offset = 15
        shadow_points = [(x + shadow_offset, y + shadow_offset) for x, y in self.path_points]

        pygame.draw.lines(self.bg_surface, self.shadow_color, False, shadow_points, 60)
        # Draw circles at the joints so the shadows have smooth corners
        for pt in shadow_points:
            pygame.draw.circle(self.bg_surface, self.shadow_color, pt, 30)

        # 4. Draw the Detailed Road (Layered from thickest to thinnest)
        layers = [
            (self.stone_edge, 60),  # Layer 1: Outer rocky border
            (self.dirt_base, 50),  # Layer 2: Main dirt surface
            (self.wagon_rut, 30),  # Layer 3: Dark wheel tracks
            (self.dirt_base, 14)  # Layer 4: Center dirt ridge
        ]

        # Loop through our layers and draw them on top of each other
        for color, width in layers:
            pygame.draw.lines(self.bg_surface, color, False, self.path_points, width)
            for pt in self.path_points:
                pygame.draw.circle(self.bg_surface, color, pt, width // 2)

    def draw(self, screen):
        # Instead of doing all that math every frame, just paste the finished picture!
        screen.blit(self.bg_surface, (0, 0))
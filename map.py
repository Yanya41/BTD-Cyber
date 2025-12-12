import pygame
import math
import os

from pygame import MOUSEBUTTONDOWN

# --- CONFIGURATION ---
PATH_WIDTH = 40
SPEED = 3

# === ANIMATION SETTINGS (CRITICAL) ===
FRAME_RATE = 0.1  # Time in seconds each frame is displayed (e.g., 0.1s = 10 frames per second)
FRAME_COUNT = 2  # <<< CRITICAL: Set this to the exact number of frame files you extracted (e.g., 4)
SKELETON_FRAME_PREFIX = "skeleton_frame"  # <<< Update this if your files are named differently (e.g., "enemy_walk")
# =====================================


# Define your path waypoints
path_points = [
    (0,168), (513,418), (611,184), (1358,350), (709,425), (700, 586), (758, 1080)
]

# --- ASSET FILE NAMES ---
IMAGE_FOLDER = "Images"
BG_FILENAME = "map1.png"

class Side_Menu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rect = pygame.Rect(1920 - width, 0, width, height)
        self.color = (200, 200, 200)  # Light gray
    def side_menu_text(self):
        pass
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        wizard = load_image(r"Cards\wizard.png", scale_to=(100, 100), alpha=True)
        archer = load_image(r"Cards\archer.png", scale_to=(100, 100), alpha=True)
        screen.blit(archer, (1920 - self.width + 150, 200))
        screen.blit(wizard, (1920 - self.width + 20, 200))

class Map_Background:
    def __init__(self, image):
        self.image = image
        screen.blit(self.image, (0, 0))

    def draw(self, screen):
        screen.blit(self.image, (0, 0))

class Skeleton:
    def __init__(self, path_points, speed=2, frames=None, frame_time=0.1):
        self.path_points = path_points
        self.x, self.y = path_points[0]
        self.speed = speed
        self.target_index = 1

        # Animation properties
        self.frames = frames if frames else []
        self.current_frame = 0
        self.frame_time = frame_time * 1000  # Convert to milliseconds
        self.last_update = pygame.time.get_ticks()

        self.flip_image = False

    def move(self):
        if self.target_index >= len(self.path_points):
            return

        target_x, target_y = self.path_points[self.target_index]
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        # --- Update Animation Frame (Safe Check) ---
        if self.frames:  # Only animate if frames were loaded
            now = pygame.time.get_ticks()
            if now - self.last_update > self.frame_time:
                # Cycle frame index
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.last_update = now
        # ------------------------------------------

        if dist != 0:
            dx_norm = dx / dist
            dy_norm = dy / dist
            self.x += dx_norm * self.speed
            self.y += dy_norm * self.speed

            # Check for horizontal direction to flip the sprite
            if dx_norm < -0.1:
                self.flip_image = True
            elif dx_norm > 0.1:
                self.flip_image = False

        if dist < self.speed:
            self.target_index += 1

    def draw(self, screen):
        if self.frames:
            current_image = self.frames[self.current_frame]

            # Flip the image based on movement direction
            display_image = pygame.transform.flip(current_image, self.flip_image, False)

            new_rect = display_image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(display_image, new_rect.topleft)
        else:
            # Draw a simple red circle fallback if no images loaded
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 12)


def load_image(filename, scale_to=None, alpha=False):
    path = os.path.join(IMAGE_FOLDER, filename)
    try:
        image = pygame.image.load(path)

        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()

        if scale_to:
            image = pygame.transform.scale(image, scale_to)
        return image
    except FileNotFoundError:
        print(f"ERROR: Image file not found: {path}")
        return None


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    clock = pygame.time.Clock()

    # --- LOAD ASSETS ---
    bg_image = load_image(BG_FILENAME, scale_to=(1920, 1080))
    if bg_image is None:
        bg_image = pygame.Surface((1920, 1080))
        bg_image.fill((34, 139, 34))  # Fallback: Dark Green

    # --- Load ALL Skeleton Frames ---
    skeleton_frames = []
    for i in range(FRAME_COUNT):
        frame_filename = f"{SKELETON_FRAME_PREFIX}_{i}.png"
        frame_image = load_image(frame_filename, scale_to=(60, 60), alpha=True)

        if frame_image:
            # Assuming the skeleton has a black background to remove
            frame_image.set_colorkey((0, 0, 0))
            skeleton_frames.append(frame_image)
        else:
            print(f"Warning: Could not load {frame_filename}. Animation may be incomplete.")
    # -----------------------------------

    # Initialize Skeleton
    skeleton = Skeleton(path_points, speed=SPEED, frames=skeleton_frames, frame_time=FRAME_RATE)
    side_menu = Side_Menu(300, 1080)
    draw_map = Map_Background(bg_image)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                print(pygame.mouse.get_pos())
            if event.type == pygame.QUIT:
                running = False

        skeleton.move()
        draw_map.draw(screen)
        side_menu.draw(screen)
        skeleton.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
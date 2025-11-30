import pygame
import math
import os

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
    (0, 100), (500, 100), (500, 400), (300, 400),
    (300, 700), (800, 700), (800, 200), (1000, 200),
    (1000, 800), (1200, 800), (1200, 100), (1400, 100), (1400, 1080)
]

# --- ASSET FILE NAMES ---
IMAGE_FOLDER = "Images"
BG_FILENAME = "background_map1.png"
PATH_TILE_FILENAME = "brick_path.png"


# CORNER FILE IS NOW REMOVED
# SKELETON_FILENAME is replaced by the frame prefix

class Side_Menu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rect = pygame.Rect(1920 - width, 0, width, height)
        self.color = (200, 200, 200)  # Light gray

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
class Path:
    # Removed corner_texture from __init__
    def __init__(self, points, width, tile_texture):
        self.points = points
        self.width = width
        self.half_width = width // 2
        self.tile = tile_texture
        self.TILE_STEP = self.half_width

    def _draw_tiles(self, screen):
        """
        Draws the path tiles using aggressive tiling to cover all gaps,
        including corners, with the straight path texture.
        """
        TILE_STEP = self.half_width

        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.hypot(dx, dy)

            if dist == 0: continue
            dx_norm = dx / dist
            dy_norm = dy / dist

            # Segment length is distance + half_width (to account for the tile placed at p2).
            segment_length = dist + self.half_width

            # Start tiling 20px BEFORE p1
            start_x = p1[0] - (dx_norm * self.half_width)
            start_y = p1[1] - (dy_norm * self.half_width)

            steps = int(segment_length // TILE_STEP)

            # === FIX: Start the loop from index 1 instead of 0 ===
            # Index 0 covers the space from p1-20 to p1. By starting at 1,
            # we start drawing from the p1 to p1+20 section.
            for s in range(1, steps + 1):
                cur_x = start_x + (dx_norm * (TILE_STEP * s))
                cur_y = start_y + (dy_norm * (TILE_STEP * s))

                draw_pos_x = int(round(cur_x) - self.half_width)
                draw_pos_y = int(round(cur_y) - self.half_width)

                screen.blit(self.tile, (draw_pos_x, draw_pos_y))


    def draw(self, screen):
        """Draws the path."""
        self._draw_tiles(screen)

        # Draw a single tile at each point to ensure corners are fully filled
        for p in self.points:
            draw_rect = pygame.Rect(p[0] - self.half_width, p[1] - self.half_width, self.width, self.width)
            screen.blit(self.tile, draw_rect.topleft)


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

    path_texture = load_image(PATH_TILE_FILENAME, scale_to=(PATH_WIDTH, PATH_WIDTH))
    if path_texture is None:
        path_texture = pygame.Surface((PATH_WIDTH, PATH_WIDTH))
        path_texture.fill((160, 82, 45))  # Fallback: Brown

    # --- Load ALL Skeleton Frames ---
    skeleton_frames = []
    for i in range(FRAME_COUNT):
        frame_filename = f"{SKELETON_FRAME_PREFIX}_{i}.png"
        frame_image = load_image(frame_filename, scale_to=(40, 40), alpha=True)

        if frame_image:
            # Assuming the skeleton has a black background to remove
            frame_image.set_colorkey((0, 0, 0))
            skeleton_frames.append(frame_image)
        else:
            print(f"Warning: Could not load {frame_filename}. Animation may be incomplete.")
    # -----------------------------------

    # Initialize Path (only takes tile texture)
    game_path = Path(path_points, PATH_WIDTH, path_texture)

    # Initialize Skeleton
    skeleton = Skeleton(path_points, speed=SPEED, frames=skeleton_frames, frame_time=FRAME_RATE)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        skeleton.move()

        screen.blit(bg_image, (0, 0))
        game_path.draw(screen)
        skeleton.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
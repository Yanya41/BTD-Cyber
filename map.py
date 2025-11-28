import pygame
import math
import os

# --- CONFIGURATION ---
PATH_WIDTH = 40
SPEED = 3

# Define your path waypoints
path = [
    (50, 100), (500, 100), (500, 400), (300, 400),
    (300, 700), (800, 700), (800, 200), (1200, 200),
    (1200, 800), (1700, 800), (1700, 100),
]

# --- ASSET FILE NAMES ---
IMAGE_FOLDER = "Images"
BG_FILENAME = "background_map1.png"
PATH_TILE_FILENAME = "brick_path.png"
CORNER_FILENAME = "brick_path_corner.png"
SKELETON_FILENAME = "skeleton.png"


class Skeleton:
    def __init__(self, path, speed=2, image=None):
        self.path = path
        self.x, self.y = path[0]
        self.speed = speed
        self.target_index = 1
        self.image = image
        self.flip_image = False  # Use horizontal flip instead of 360 rotation

    def move(self):
        if self.target_index >= len(self.path):
            return

        target_x, target_y = self.path[self.target_index]
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist != 0:
            dx_norm = dx / dist
            dy_norm = dy / dist

            self.x += dx_norm * self.speed
            self.y += dy_norm * self.speed

            # --- SKELETON FIX 3: Horizontal Flip Logic ---
            # Flip the image if moving significantly left (negative dx)
            if dx_norm < -0.1:
                self.flip_image = True
            elif dx_norm > 0.1:  # Flip back if moving right (positive dx)
                self.flip_image = False
            # -----------------------------------------------------------

        if dist < self.speed:
            self.target_index += 1

    def draw(self, screen):
        if self.image:
            # --- SKELETON FIX 3: Use pygame.transform.flip ---
            # Flip the original image horizontally based on the flag
            display_image = pygame.transform.flip(self.image, self.flip_image, False)

            # Center the image on the skeleton's position
            new_rect = display_image.get_rect(center=(int(self.x), int(self.y)))

            screen.blit(display_image, new_rect.topleft)
        else:
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 12)


def draw_textured_path(screen, path, texture):
    half_width = PATH_WIDTH // 2
    # Aggressively overlap tiles by 50% (stepping 20px for a 40px tile)
    TILE_STEP = half_width

    for i in range(len(path) - 1):
        p1 = path[i]
        p2 = path[i + 1]

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dist = math.hypot(dx, dy)

        # Segment length to tile: Stop exactly half a tile width (20px) before p2.
        segment_length = dist - half_width

        if segment_length <= 0:
            continue

        dx_norm = dx / dist
        dy_norm = dy / dist

        # Calculate steps based on the aggressive overlap (stepping every 20px)
        steps = int(segment_length // TILE_STEP)

        # Draw 2 extra steps to ensure full coverage up to the corner gap
        for s in range(steps + 2):
            cur_x = p1[0] + (dx_norm * (TILE_STEP * s))
            cur_y = p1[1] + (dy_norm * (TILE_STEP * s))

            # Crucially, still rely on rounding for the draw position
            draw_pos_x = int(round(cur_x) - half_width)
            draw_pos_y = int(round(cur_y) - half_width)

            screen.blit(texture, (draw_pos_x, draw_pos_y))

            screen.blit(texture, (draw_pos_x, draw_pos_y))


def draw_rounded_joints(screen, path, path_corner):
    """
    FIX 2: Uses simplified coordinate-based checks for rotation, correcting the corner placement.
    Assumes path_corner.png is oriented for a RIGHT -> UP turn (Top-Right quadrant).
    """

    for i in range(1, len(path) - 1):
        p_prev = path[i - 1]
        p_current = path[i]
        p_next = path[i + 1]

        # Determine the change in direction using coordinate comparison
        x_turn = (p_next[0] > p_current[0])  # Is the path going RIGHT?
        x_in = (p_current[0] > p_prev[0])  # Was the path coming from the LEFT?

        y_turn = (p_next[1] > p_current[1])  # Is the path going DOWN?
        y_in = (p_current[1] > p_prev[1])  # Was the path coming from UP?

        # Skip if the path is straight
        if (p_prev[0] == p_current[0] and p_current[0] == p_next[0]) or \
                (p_prev[1] == p_current[1] and p_current[1] == p_next[1]):
            continue

        # --- Determine Rotation based on TOP-RIGHT Corner Asset (0 degrees) ---
        rotation = 0

        # 1. Turn: RIGHT -> UP (Asset base orientation)
        if x_in and not y_turn:
            rotation = 0

            # 2. Turn: UP -> LEFT
        elif not y_in and not x_turn:
            rotation = 90

        # 3. Turn: LEFT -> DOWN
        elif not x_in and y_turn:
            rotation = 180

        # 4. Turn: DOWN -> RIGHT
        elif y_in and x_turn:
            rotation = 270

        else:
            continue

        # --- Draw the Rotated Corner ---
        sprite = path_corner
        rotated_image = pygame.transform.rotate(sprite, rotation)

        # Center the corner sprite EXACTLY on the path point
        new_rect = rotated_image.get_rect(center=(int(p_current[0]), int(p_current[1])))

        screen.blit(rotated_image, new_rect.topleft)


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    clock = pygame.time.Clock()


    def load_image(filename, scale_to=None, alpha=False):
        # Use os.path.join to handle file paths across different operating systems
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


    # --- LOAD ALL GAME ASSETS ---

    # Background Image
    bg_image = load_image(BG_FILENAME, scale_to=(1920, 1080))
    if bg_image is None:
        bg_image = pygame.Surface((1920, 1080))
        bg_image.fill((34, 139, 34))  # Fallback color

    # Path Tile
    path_texture = load_image(PATH_TILE_FILENAME, scale_to=(PATH_WIDTH, PATH_WIDTH))
    if path_texture is None:
        path_texture = pygame.Surface((PATH_WIDTH, PATH_WIDTH))
        path_texture.fill((160, 82, 45))  # Fallback color

    # Corner Sprite
    path_corner = load_image(CORNER_FILENAME, scale_to=(PATH_WIDTH, PATH_WIDTH), alpha=True)
    if path_corner is None:
        path_corner = path_texture  # Fallback to square tile

    # Skeleton Sprite
    skeleton_image = load_image(SKELETON_FILENAME, scale_to=(64, 64), alpha=True)

    skeleton = Skeleton(path, speed=SPEED, image=skeleton_image)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        skeleton.move()

        # --- DRAWING ---
        screen.blit(bg_image, (0, 0))

        # 1. Draw the main path body (with gap fix)
        draw_textured_path(screen, path, path_texture)

        # 2. Draw the rounded corners on top (with rotation fix)
        draw_rounded_joints(screen, path, path_corner)

        # 3. Draw the skeleton (with flip fix)
        skeleton.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
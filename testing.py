import pygame
import os

# --- CONFIGURATION ---
PATH_WIDTH = 40
CORNER_FILENAME = "brick_path_corner.png"
IMAGE_FOLDER = "Images"
WINDOW_SIZE = (200, 200)


def load_corner_image():
    """Safely loads the corner image with transparency."""
    path = os.path.join(IMAGE_FOLDER, CORNER_FILENAME)
    try:
        # Load the image and use convert_alpha for transparency
        image = pygame.image.load(path).convert_alpha()
        # Scale it to the correct size
        image = pygame.transform.scale(image, (PATH_WIDTH, PATH_WIDTH))
        return image
    except FileNotFoundError:
        print(f"ERROR: Image file not found at: {path}")
        return None
    except pygame.error as e:
        print(f"ERROR loading image: {e}")
        return None


def test_corner_transparency():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Corner Transparency Test")
    clock = pygame.time.Clock()

    corner_image = load_corner_image()

    if corner_image is None:
        print("Cannot run test: Corner image failed to load.")
        pygame.quit()
        return

    # Center the corner image on the screen
    x = (WINDOW_SIZE[0] // 2) - (PATH_WIDTH // 2)
    y = (WINDOW_SIZE[1] // 2) - (PATH_WIDTH // 2)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Drawing ---
        # Draw a solid, contrasting color background (e.g., dark blue)
        # The transparent areas of the corner image should show this color.
        screen.fill((50, 50, 150))

        # Blit the corner image
        screen.blit(corner_image, (x, y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == '__main__':
    test_corner_transparency()
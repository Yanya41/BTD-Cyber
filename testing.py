
def draw_styled_text(surface, text, font, color, pos, shadow_color=(155, 155, 0)):
    # Draw the shadow first (offset by 2-3 pixels)
    shadow_surf = font.render(text, True, shadow_color)
    surface.blit(shadow_surf, (pos[0] + 2, pos[1] + 2))

    # Draw the main text
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, pos)

if __name__ == "__main__":
    import pygame
    pygame.init()
    import os
    MineFont = os.path.join('Images', 'MineFont.ttf')
    screen = pygame.display.set_mode((800, 600))
    font = pygame.font.Font(MineFont, 48)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((255, 255, 255))
        draw_styled_text(screen, "Hello, World!", font, (255, 0, 0), (100, 100))
        pygame.display.flip()

    pygame.quit()
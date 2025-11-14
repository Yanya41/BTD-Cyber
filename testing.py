import pygame

pygame.init()

screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Main Menu")

font = pygame.font.SysFont(None, 50)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

def main_menu():
    while True:
        screen.fill((0, 0, 0))  # Black background

        draw_text("My Awesome Game", font, (255, 255, 255), screen, screen_width // 2, 100)

        # Play Button
        play_button_rect = pygame.Rect(screen_width // 2 - 100, 250, 200, 50)
        pygame.draw.rect(screen, (0, 150, 0), play_button_rect) # Green button
        draw_text("Play", font, (255, 255, 255), screen, play_button_rect.centerx, play_button_rect.centery)

        # Options Button
        options_button_rect = pygame.Rect(screen_width // 2 - 100, 350, 200, 50)
        pygame.draw.rect(screen, (0, 0, 150), options_button_rect) # Blue button
        draw_text("Options", font, (255, 255, 255), screen, options_button_rect.centerx, options_button_rect.centery)

        # Exit Button
        exit_button_rect = pygame.Rect(screen_width // 2 - 100, 450, 200, 50)
        pygame.draw.rect(screen, (150, 0, 0), exit_button_rect) # Red button
        draw_text("Exit", font, (255, 255, 255), screen, exit_button_rect.centerx, exit_button_rect.centery)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button_rect.collidepoint(event.pos):
                    print("Play button pressed!")
                    # Add code to start the game
                elif options_button_rect.collidepoint(event.pos):
                    print("Options button pressed!")
                    # Add code to open options menu
                elif exit_button_rect.collidepoint(event.pos):
                    pygame.quit()
                    quit()

        pygame.display.update()

main_menu()
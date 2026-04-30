import pygame
import load_assets
import os

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 74)
        self.options = ["Start Game", "Options", "Exit"]
        self.selected_option = -1
        self.option_rects = []

        # hover intensity per option for smooth fade
        self.hover_levels = [100 for _ in self.options]  # baseline dim value

        # Title
        self.title_font = pygame.font.Font(None, 110)
        self.title = "Royal TD"
        self.title_color = (255, 215, 0)  # gold-like

        # retro beep sounds
        self.hover_sound = pygame.mixer.Sound(os.path.join("SoundEffects", "hover_menu.wav"))
        self.click_sound = pygame.mixer.Sound(os.path.join("SoundEffects", "click_menu.wav"))
        self.last_hover = -1  # used to avoid repeating hover sounds

        #background picture
        self.background = pygame.image.load(os.path.join("Images", "background.jpg")).convert()
        self.background = pygame.transform.scale(self.background, (1920, 1080))

    def draw(self):
        screen.blit(self.background, (0, 0))
        self.option_rects = []

        # --- Title ---
        title_surface = self.title_font.render(self.title, True, self.title_color)
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(title_surface, title_rect)

        # --- Menu Options ---
        for index, option in enumerate(self.options):
            if index == self.selected_option:
                self.hover_levels[index] = min(255, self.hover_levels[index] + 10)
            else:
                self.hover_levels[index] = max(160, self.hover_levels[index] - 10)

            color_value = self.hover_levels[index]
            color = (color_value, color_value, color_value)
            text = self.font.render(option, True, color)
            rect = text.get_rect(center=(self.screen.get_width() // 2,350 + index * 110))
            self.option_rects.append(rect)
            self.screen.blit(text, rect)

        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            new_hover = -1

            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(mouse_pos):
                    new_hover = i
                    break

            # play hover sound only when entering a new item
            if new_hover != self.last_hover and new_hover != -1:
                self.hover_sound.play()

            self.selected_option = new_hover
            self.last_hover = new_hover

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mouse_pos):
                        self.click_sound.play()
                        return self.options[i]

        return None


if __name__ == "__main__":
    if load_assets.check_files_exist():
        print("Missing assets, exiting.")
        pygame.quit()
        exit()
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((1920, 1080))
    pygame.display.set_caption("Royal TD - Main Menu")

    menu = MainMenu(screen)
    running = True

    while running:
        menu.draw()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            action = menu.handle_event(event)

            if action == "Exit":
                running = False
            elif action == "Start Game":
                print("Starting Game...")
            elif action == "Options":
                print("Opening Options...")

    pygame.quit()
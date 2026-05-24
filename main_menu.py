import pygame
import os


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.MineFont = os.path.join('Fonts', 'MineFont.ttf')
        self.font = pygame.font.Font(self.MineFont, 74)
        self.options = ["Start Game", "Options", "Exit"]
        self.selected_option = -1
        self.option_rects = []
        self.hover_levels = [100 for _ in self.options]

        # Title setup
        self.title_font = pygame.font.Font(self.MineFont, 110)
        self.title = "Royal TD"
        self.title_color = (255, 215, 0)

        # Hover over sound effects
        self.hover_sound = pygame.mixer.Sound(os.path.join("SoundEffects", "hover_menu.wav"))
        self.click_sound = pygame.mixer.Sound(os.path.join("SoundEffects", "click_menu.wav"))
        self.last_hover = -1

        # Background setup
        self.background = pygame.image.load(os.path.join("Images", "background.jpg")).convert()
        self.background = pygame.transform.scale(self.background, (1920, 1080))

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.option_rects = []

        self.draw_styled_text(self.title, self.title_font, self.title_color, (self.screen.get_width() // 2, 150), shadow_color=(100, 100, 0))

        for index, option in enumerate(self.options):
            if index == self.selected_option:
                self.hover_levels[index] = min(255, self.hover_levels[index] + 10)
            else:
                self.hover_levels[index] = max(160, self.hover_levels[index] - 10)

            color_value = self.hover_levels[index]
            color = (color_value, color_value, color_value)
            text = self.font.render(option, True, color)
            rect = text.get_rect(center=(self.screen.get_width() // 2, 350 + index * 110))
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

    def draw_styled_text(self, text, font, color, pos, shadow_color): # Changed shadow to black so it shows up against the white!
        shadow_surf = font.render(text, True, shadow_color)
        shadow_rect = shadow_surf.get_rect(center=(pos[0] + 4, pos[1] + 4))
        self.screen.blit(shadow_surf, shadow_rect)

        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=pos)
        self.screen.blit(text_surf, text_rect)
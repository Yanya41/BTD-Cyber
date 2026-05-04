import pygame
import os


class LoginMenu:
    def __init__(self, screen):
        self.screen = screen
        self.MineFont = os.path.join('Fonts', 'MineFont.ttf')
        self.ProjectFont = os.path.join('Fonts', 'ProjectFont.otf')
        self.user_font = pygame.font.Font(self.ProjectFont, 50)
        self.font = pygame.font.Font(self.MineFont, 50)
        self.title_font = pygame.font.Font(self.MineFont, 80)

        self.username = ""
        self.password = ""
        self.active_box = 0

        self.background = pygame.image.load(os.path.join("Images", "background.jpg")).convert()
        self.background = pygame.transform.scale(self.background, (1920, 1080))

        # UI Rectangles: Centered on a 1920x1080 screen
        center_x = self.screen.get_width() // 2
        self.user_rect = pygame.Rect(center_x - 200, 400, 400, 60)
        self.pass_rect = pygame.Rect(center_x - 200, 550, 400, 60)
        self.btn_login_rect = pygame.Rect(center_x - 220, 700, 200, 70)
        self.btn_register_rect = pygame.Rect(center_x + 20, 700, 200, 70)

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        # Title
        title_surf = self.title_font.render("User Login", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(title_surf, title_rect)

        # Determine box colors based on which one is active
        color_active = (255, 215, 0)
        color_inactive = (150, 150, 150)
        user_color = color_active if self.active_box == 1 else color_inactive
        pass_color = color_active if self.active_box == 2 else color_inactive

        #go back button
        go_back_text = self.font.render("Go Back", True, (255, 255, 255))
        self.go_back_rect = go_back_text.get_rect(center=(self.screen.get_width() // 4, 200))
        self.screen.blit(go_back_text, self.go_back_rect)


        # Draw Input Boxes
        pygame.draw.rect(self.screen, user_color, self.user_rect, 3)
        pygame.draw.rect(self.screen, pass_color, self.pass_rect, 3)

        # Draw Submit Button
        pygame.draw.rect(self.screen, (50, 200, 50), self.btn_login_rect)
        pygame.draw.rect(self.screen, (50, 100, 200), self.btn_register_rect)

        # Button Text
        login_text = self.user_font.render("Login", True, (0, 0, 0))
        reg_text = self.user_font.render("Register", True, (255, 255, 255))

        self.screen.blit(login_text, login_text.get_rect(center=self.btn_login_rect.center))
        self.screen.blit(reg_text, reg_text.get_rect(center=self.btn_register_rect.center))

        # Labels
        user_label = self.font.render("Username:", True, (255, 255, 255))
        pass_label = self.font.render("Password", True, (255, 255, 255))
        self.screen.blit(user_label, (self.user_rect.x, self.user_rect.y - 40))
        self.screen.blit(pass_label, (self.pass_rect.x, self.pass_rect.y - 40))

        # Text inside boxes
        user_text_surf = self.user_font.render(self.username, True, (255, 255, 255))
        pass_text_surf = self.font.render("*" * len(self.password), True, (255, 255, 255))

        self.screen.blit(user_text_surf, (self.user_rect.x + 10, self.user_rect.y))
        self.screen.blit(pass_text_surf, (self.pass_rect.x + 10, self.pass_rect.y + 15))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.user_rect.collidepoint(mouse_pos):
                self.active_box = 1
            elif self.pass_rect.collidepoint(mouse_pos):
                self.active_box = 2
            elif self.go_back_rect.collidepoint(mouse_pos):
                return {"action": "go_back"}

            # --- NEW: Handle both clicks ---
            elif self.btn_login_rect.collidepoint(mouse_pos):
                return {"action": "login", "user": self.username, "password": self.password}
            elif self.btn_register_rect.collidepoint(mouse_pos):
                return {"action": "register", "user": self.username, "password": self.password}
            else:
                self.active_box = 0

        elif event.type == pygame.KEYDOWN:
            # 1. Handle Enter Key (Submit form)
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                return {"action": "login", "user": self.username, "password": self.password}

            # 2. Handle Tab Key (Switch between input boxes)
            elif event.key == pygame.K_TAB:
                if self.active_box == 1:
                    self.active_box = 2
                else:
                    self.active_box = 1

            # 3. Handle Typing in Username Box
            elif self.active_box == 1:
                if event.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                elif event.unicode.isprintable():  # <-- The fix!
                    self.username += event.unicode

            # 4. Handle Typing in Password Box
            elif self.active_box == 2:
                if event.key == pygame.K_BACKSPACE:
                    self.password = self.password[:-1]
                elif event.unicode.isprintable():  # <-- The fix!
                    self.password += event.unicode

        return None
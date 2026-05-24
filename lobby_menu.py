import pygame
import os


class LobbyMenu:
    def __init__(self, screen):
        self.screen = screen
        self.MineFont = os.path.join('Fonts', 'MineFont.ttf')
        self.ProjectFont = os.path.join('Fonts', 'ProjectFont.otf')
        self.font = pygame.font.Font(None, 50)
        self.title_font = pygame.font.Font(self.MineFont, 80)
        self.small_font = pygame.font.Font(self.ProjectFont, 35)

        self.code = ""
        self.password = ""
        self.active_box = 0

        self.server_list = []
        self.server_rects = []

        self.background = pygame.image.load(os.path.join("Images", "background.jpg")).convert()
        self.background = pygame.transform.scale(self.background, (1920, 1080))

        self.code_rect = pygame.Rect(200, 350, 400, 60)
        self.pass_rect = pygame.Rect(200, 500, 400, 60)
        self.btn_create_rect = pygame.Rect(200, 650, 180, 70)
        self.btn_join_rect = pygame.Rect(400, 650, 180, 70)
        self.btn_refresh_rect = pygame.Rect(1000, 185, 200, 35)

    def update_server_list(self, lobbies):
        """Safely extract the list regardless of what the client passes."""
        if isinstance(lobbies, dict):
            # If client passed the raw JSON dict, grab the lobbies list
            self.server_list = lobbies.get("lobbies", [])
        elif isinstance(lobbies, list):
            self.server_list = lobbies
        else:
            self.server_list = []

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        title_surf = self.title_font.render("Multiplayer Lobbies", True, (255, 215, 0))
        self.screen.blit(title_surf, (self.screen.get_width() // 2 - title_surf.get_width() // 2, 100))

        color_active = (255, 215, 0)
        color_inactive = (150, 150, 150)

        pygame.draw.rect(self.screen, color_active if self.active_box == 1 else color_inactive, self.code_rect, 3)
        pygame.draw.rect(self.screen, color_active if self.active_box == 2 else color_inactive, self.pass_rect, 3)
        pygame.draw.rect(self.screen, (50, 150, 200), self.btn_create_rect)
        pygame.draw.rect(self.screen, (50, 200, 50), self.btn_join_rect)

        self.screen.blit(self.font.render("Lobby Code:", True, (255, 255, 255)),
                         (self.code_rect.x, self.code_rect.y - 40))
        self.screen.blit(self.font.render("Password:", True, (255, 255, 255)),
                         (self.pass_rect.x, self.pass_rect.y - 40))

        self.screen.blit(self.font.render(self.code, True, (255, 255, 255)),
                         (self.code_rect.x + 10, self.code_rect.y + 15))
        self.screen.blit(self.font.render("*" * len(self.password), True, (255, 255, 255)),
                         (self.pass_rect.x + 10, self.pass_rect.y + 15))

        self.screen.blit(self.font.render("Create", True, (0, 0, 0)),
                         (self.btn_create_rect.x + 40, self.btn_create_rect.y + 15))
        self.screen.blit(self.font.render("Join", True, (0, 0, 0)),
                         (self.btn_join_rect.x + 60, self.btn_join_rect.y + 15))

        list_x = 1000
        list_y = 300

        self.screen.blit(self.font.render("Active Servers", True, (255, 255, 255)), (list_x, list_y - 60))
        pygame.draw.rect(self.screen, (100, 100, 100), self.btn_refresh_rect)
        self.screen.blit(self.small_font.render("Refresh List", True, (255, 255, 255)),
                         (self.btn_refresh_rect.x + 5, self.btn_refresh_rect.y - 2))

        self.server_rects = []

        if not self.server_list:
            self.screen.blit(self.small_font.render("No active lobbies found. Create one!", True, (200, 200, 200)),
                             (list_x, list_y))
        else:
            for i, server in enumerate(self.server_list):
                # Extra layer of defense in case the array accidentally contains a string
                if isinstance(server, dict):
                    row_rect = pygame.Rect(list_x, list_y + (i * 70), 650, 60)
                    pygame.draw.rect(self.screen, (40, 40, 40), row_rect)
                    pygame.draw.rect(self.screen, (255, 215, 0), row_rect, 2)

                    lock_text = "[LOCKED] " if server.get("locked") else ""
                    code_val = server.get('code', '???')
                    players_val = server.get('players', '?')

                    display_text = f"{lock_text}Lobby: {code_val}  |  Players: {players_val}/4"

                    self.screen.blit(self.small_font.render(display_text, True, (255, 255, 255)),
                                     (row_rect.x + 20, row_rect.y + 10))

                    self.server_rects.append((row_rect, code_val))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.code_rect.collidepoint(mouse_pos):
                self.active_box = 1
            elif self.pass_rect.collidepoint(mouse_pos):
                self.active_box = 2
            elif self.btn_create_rect.collidepoint(mouse_pos):
                if self.code == "":
                    return {"action": "create_lobby", "password": self.password}
            elif self.btn_join_rect.collidepoint(mouse_pos):
                return {"action": "join_lobby", "code": self.code, "password": self.password}
            elif self.btn_refresh_rect.collidepoint(mouse_pos):
                return {"action": "refresh_lobbies"}
            else:
                self.active_box = 0
                for rect, clicked_code in self.server_rects:
                    if rect.collidepoint(mouse_pos):
                        self.code = clicked_code
                        self.active_box = 2
                        break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.active_box = 2 if self.active_box == 1 else 1
            elif self.active_box == 1:
                if event.key == pygame.K_BACKSPACE:
                    self.code = self.code[:-1]
                elif event.unicode.isprintable() and len(self.code) < 5:
                    self.code += event.unicode.upper()
            elif self.active_box == 2:
                if event.key == pygame.K_BACKSPACE:
                    self.password = self.password[:-1]
                elif event.unicode.isprintable():
                    self.password += event.unicode

        return None
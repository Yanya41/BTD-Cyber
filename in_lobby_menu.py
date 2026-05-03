import pygame


class InLobbyMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 80)

        # Center the button near the bottom of a 1080p screen
        self.start_button_rect = pygame.Rect(screen.get_width() // 2 - 100, 800, 200, 100)

        # This will hold a list of dictionaries: [{"username": "Player1", "admin": True}]
        self.players = []
        self.is_admin = False

    def update_players(self, player_list, is_admin=False):
        """Call this from client.py whenever the server sends a new player list."""
        self.players = player_list
        self.is_admin = is_admin

    def draw(self):
        self.screen.fill((50, 50, 50))  # Dark background

        # Draw Title
        title_surf = self.title_font.render("Lobby Players", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(title_surf, title_rect)

        # Draw the Player List
        start_y = 300
        for index, player in enumerate(self.players):
            name = player.get("username", "Unknown")

            # Add a "(Host)" tag if they are the admin
            if player.get("admin"):
                name += " (Host)"

            text_surf = self.font.render(name, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(self.screen.get_width() // 2, start_y + (index * 70)))
            self.screen.blit(text_surf, text_rect)

        # Draw start button
        if self.is_admin:
            pygame.draw.rect(self.screen, (0, 128, 255), self.start_button_rect)
            button_text = self.font.render("Start Game", True, (255, 255, 255))
            button_rect = button_text.get_rect(center=self.start_button_rect.center)
            self.screen.blit(button_text, button_rect)

        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_admin and self.start_button_rect.collidepoint(event.pos):
                return {"action": "start_game"}
        return None
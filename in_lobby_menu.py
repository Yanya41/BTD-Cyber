import pygame
import os


class InLobbyMenu:
    def __init__(self, screen):
        self.screen = screen

        # --- FIX: Match the custom fonts used in your other menus ---
        self.MineFont = os.path.join('Fonts', 'MineFont.ttf')
        self.ProjectFont = os.path.join('Fonts', 'ProjectFont.otf')

        # We load them gracefully. If they fail for some reason, we'll crash nicely.
        self.font = pygame.font.Font(self.ProjectFont, 50)
        self.title_font = pygame.font.Font(self.MineFont, 80)

        # --- FIX: Use os.path.join for cross-platform compatibility ---
        self.background = pygame.image.load(os.path.join("Images", "background.jpg")).convert()
        self.background = pygame.transform.scale(self.background, (1920, 1080))

        # Center the button near the bottom of a 1080p screen
        self.start_button_rect = pygame.Rect(0,0, 400, 100)
        self.start_button_rect.center = (screen.get_width() // 2, 850)

        # This will hold a list of dictionaries: [{"username": "Player1", "admin": True}]
        self.players = []
        self.is_admin = False

    def update_players(self, player_list, is_admin=False):
        """Call this from client.py whenever the server sends a new player list."""
        # --- FIX: Safely extract the list regardless of what the client passes ---
        if isinstance(player_list, dict):
            self.players = player_list.get("players", [])
        elif isinstance(player_list, list):
            self.players = player_list
        else:
            self.players = []

        self.is_admin = is_admin

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        # Draw Title
        title_surf = self.title_font.render("Lobby Players", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(title_surf, title_rect)

        # Draw the Player List
        start_y = 300
        for index, player in enumerate(self.players):
            # --- FIX: Extra defense in case the list contains corrupted data ---
            if isinstance(player, dict):
                name = player.get("username", "Unknown")
                # Add a "(Host)" tag if they are the admin
                if player.get("admin"):
                    name += " (Host)"
            else:
                name = str(player)

            text_surf = self.font.render(name, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(self.screen.get_width() // 2, start_y + (index * 70)))
            self.screen.blit(text_surf, text_rect)

        # Draw start button
        if self.is_admin:
            # Made it green (50, 200, 50) to match your other positive action buttons!
            pygame.draw.rect(self.screen, (50, 200, 50), self.start_button_rect)
            button_text = self.font.render("Start Game", True, (255, 255, 255))
            button_rect = button_text.get_rect(center=self.start_button_rect.center)
            self.screen.blit(button_text, button_rect)



    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_admin and self.start_button_rect.collidepoint(event.pos):
                return {"action": "start_game"}
        return None
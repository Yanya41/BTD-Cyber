import pygame


def split_and_transparent():
    pygame.init()

    # 1. Create a tiny hidden window so .convert() works
    pygame.display.set_mode((1, 1), pygame.HIDDEN)

    # 2. Now you can load and convert
    sheet = pygame.image.load("goku_sheet.png").convert()

    sheet.set_colorkey((254, 254, 254))

    # Define the two frames (Adjust coordinates as needed)
    idle_surf = sheet.subsurface((362, 330, 300, 300))
    shoot_surf = sheet.subsurface((110, 0, 100, 100))

    # Save them
    pygame.image.save(idle_surf, "goku_idle.png")
    pygame.image.save(shoot_surf, "goku_shoot.png")
    print("Files saved successfully!")


if __name__ == "__main__":
    split_and_transparent()
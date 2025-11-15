from player import Player
towers_count = 0
class Towers:
    def __init__(self):
        self.towers_id = 1

    class Wizard:
        def __init__(self):
            self.tower_type = "wizard"
            self.damage = 2
            self.attack_speed = 1.5
            self.range = 150

    class Archer:
        def __init__(self):
            self.tower_type = "archer"
            self.damage = 1
            self.attack_speed = 1.0
            self.range = 200


Player().towers_add(1, "wizard")
print(Player().towers_owned)
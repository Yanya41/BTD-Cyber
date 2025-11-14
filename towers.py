from player import Player
towers_count = 0
class Towers:
    def __init__(self):
        self.towers_id = 1

    class Wizard:
        def __init__(self):
            self.tower_type = "wizard"

    class Archer:
        def __init__(self):
            self.tower_type = "archer"


Player().towers_add(1, "wizard")
print(Player().towers_owned)
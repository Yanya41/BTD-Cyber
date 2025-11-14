from player import Player
class Towers:
    def __init__(self):
        self.towers_id = 1
    class Wizard:
        def __init__(self):
            self.tower_type = "wizard"

p = Player()
p.towers_add(1, "wizard")
print(p.towers_owned)
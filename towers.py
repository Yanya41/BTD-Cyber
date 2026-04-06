class Tower:
    def __init__(self):
        self.tower_count = {}
        self.id = 1

    def create_tower(self, tower_type):
        if tower_type == "wizard":
            tower = Tower.Wizard(self.id)
        elif tower_type == "goku":
            tower = Tower.Goku(self.id)
        else:
            raise ValueError("Unknown tower type")

        self.tower_count[tower.id] = tower
        self.id += 1
        return tower

    class Wizard:
        def __init__(self, tower_id):
            self.id = tower_id
            self.tower_type = "wizard"
            self.damage = 2
            self.attack_speed = 1.5
            self.range = 150
            self.cost = 150

    class Goku:
        def __init__(self, tower_id):
            self.id = tower_id
            self.tower_type = "goku"
            self.damage = 3
            self.attack_speed = 3.0
            self.range = 200
            self.cost = 550



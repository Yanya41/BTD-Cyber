class Player:
    def __init__(self):
        self.name = ""
        self.money = 500
        self.health = 100
        self.towers_owned = {}

    def set_name(self, name):
        self.name = name

    def money_change(self, attacker_value,player_count):
        self.money = self.money +attacker_value/player_count
        return self.money

    def health_change(self, attacker_value):
        self.health = self.health - attacker_value
        return self.health

    def towers_add(self, tower_id, tower_type):
        self.towers_owned[tower_id] = tower_type

from skeleton_rounds import Enemy,Skeleton,ShieldedSkeleton
class Round:
    def __init__(self):
        self.enemies = []
        self.current_round = 1
        self.round_in_progress = False
        self.enemy_id = 1
        self.rounds_spawns()
    def rounds_spawns(self):
        if self.current_round == 1:
            skeleton = Skeleton(speed=3)
            self.enemies = [skeleton]
            return
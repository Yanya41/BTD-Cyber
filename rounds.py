from skeleton_rounds import Skeleton, ShieldedSkeleton
import pygame
from game_data import Data
class Round:
    def __init__(self):
        self.enemies = []  # Enemies currently on screen
        self.spawn_queue = []  # Enemies waiting to spawn
        self.current_round = 1
        self.last_spawn_time = 0
        self.spawn_delay = 1000  # Delay in milliseconds (1 second)
        self.round_started = False
        self.prepare_round()

    def start_next_round(self):
        # Only start if the current round is totally finished
        if not self.round_started and not self.enemies:
            self.prepare_round()
            self.round_started = True
            print(f"Starting Round {self.current_round}")

    def prepare_round(self):
        """Decide which enemies belong in the current round"""
        if self.current_round == 1:
            # Create a list of 5 skeletons waiting to enter the map
            self.spawn_queue = [Skeleton(speed=3) for _ in range(5)]

        elif self.current_round == 2:
            # Mix of skeletons and shielded ones
            self.spawn_queue = [Skeleton(speed=3) for _ in range(3)] + \
                               [ShieldedSkeleton(speed=2) for _ in range(2)]

    def update(self):
        if not self.round_started:
            return

        now = pygame.time.get_ticks()
        if self.spawn_queue and (now - self.last_spawn_time > self.spawn_delay):
            new_enemy = self.spawn_queue.pop(0)
            self.enemies.append(new_enemy)
            self.last_spawn_time = now

        # If everything is dead and nothing is left to spawn, round is over
        if not self.spawn_queue and not self.enemies:
            self.round_started = False
            self.current_round += 1
            Data().current_cash += 100
from skeleton_rounds import Skeleton, ShieldedSkeleton, SkeletonBarrel
import pygame
from game_data import Data


class Round:
    def __init__(self):
        self.enemies = []  # Enemies currently on screen
        self.spawn_queue = []  # Enemies waiting to spawn
        self.current_round = 1
        self.last_spawn_time = 0
        self.round_started = False
        self.prepare_round()

    def start_next_round(self):
        # Only start if the current round is totally finished
        if not self.round_started and not self.enemies:
            self.prepare_round()
            self.round_started = True
            # Reset the spawn timer so the first enemy spawns immediately
            self.last_spawn_time = pygame.time.get_ticks()
            print(f"Starting Round {self.current_round}")

    def prepare_round(self):
        """Decide which enemies belong in the current round and their spawn delays"""
        self.spawn_queue = []

        if self.current_round == 1:
            # Format: (Enemy_Object, Milliseconds_to_wait)
            self.spawn_queue = [
                (Skeleton(speed=3), 0),  # 1st skeleton spawns immediately (0ms wait)
                (Skeleton(speed=3), 1000),  # 2nd skeleton waits 1 second
                (Skeleton(speed=3), 500),  # 3rd skeleton rushes in after 0.5 seconds!
                (Skeleton(speed=3), 500),  # 4th skeleton also rushes in 0.5 seconds later
                (Skeleton(speed=3), 3000)  # 5th skeleton waits 3 long seconds
            ]

        elif self.current_round == 2:
            self.spawn_queue = [
                (Skeleton(speed=3), 0),
                (Skeleton(speed=3), 800),
                (ShieldedSkeleton(speed=2), 1500),
                (Skeleton(speed=3), 500),
                (SkeletonBarrel(), 4000)  # Big boss waits 4 seconds before appearing
            ]

    def update(self):
        if not self.round_started:
            return

        now = pygame.time.get_ticks()

        # If we have enemies in the queue, check if it's time to spawn the next one
        if self.spawn_queue:
            next_enemy, delay_needed = self.spawn_queue[0]

            if now - self.last_spawn_time >= delay_needed:
                # Time is up! Remove from queue and add to screen
                self.enemies.append(next_enemy)
                self.spawn_queue.pop(0)
                self.last_spawn_time = now

        # If everything is dead and nothing is left to spawn, round is over
        if not self.spawn_queue and not self.enemies:
            self.round_started = False
            self.current_round += 1
            Data().current_cash += 100
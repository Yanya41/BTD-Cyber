from skeleton_rounds import Skeleton, ShieldedSkeleton
import pygame


class Round:
    def __init__(self):
        self.enemies = []  # Enemies currently on screen
        self.spawn_queue = []  # Enemies waiting to spawn
        self.current_round = 1
        self.last_spawn_time = 0
        self.spawn_delay = 1000  # Delay in milliseconds (1 second)

        self.prepare_round()

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
        """Call this every frame in your main loop"""
        now = pygame.time.get_ticks()

        # Check if we have enemies left to spawn AND if enough time has passed
        if self.spawn_queue and (now - self.last_spawn_time > self.spawn_delay):
            new_enemy = self.spawn_queue.pop(0)  # Take the first enemy out of line
            self.enemies.append(new_enemy)  # Put them on the map
            self.last_spawn_time = now  # Reset the timer
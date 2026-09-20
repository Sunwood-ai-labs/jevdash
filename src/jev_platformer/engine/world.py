"""Level creation, procedural obstacles, and collision world management."""

import pygame
from typing import List, Tuple
from jev_platformer.engine.constants import (
    TILE_SIZE, GAME_VIEW_HEIGHT, COLOR_GROUND, COLOR_OBSTACLE, COLOR_PIPE
)
from jev_platformer.engine.entities import Player, Enemy, Coin, Goal


class Level:
    """Manages the platformer level geometry and dynamic actors."""

    def __init__(self, level_num: int = 1):
        self.level_num = level_num
        self.width_tiles = 140  # ~4,480 pixels length
        self.height_tiles = GAME_VIEW_HEIGHT // TILE_SIZE  # 22 tiles
        
        self.tiles: List[pygame.Rect] = []
        self.tile_types: dict[Tuple[int, int], str] = {}
        self.enemies: List[Enemy] = []
        self.coins: List[Coin] = []
        self.goal: Goal = None
        self.start_pos = (96, 480)
        
        self._build_level()

    def _build_level(self):
        """Construct a balanced, classic side-scrolling level layout."""
        self.tiles.clear()
        self.tile_types.clear()
        self.enemies.clear()
        self.coins.clear()

        ground_y = self.height_tiles - 4  # Tile row 18 (y=576)

        # 1. Base ground with strategic pits (gaps)
        # Strategic gaps with clear landing zones:
        # Gap 1: col 32..34 (width 3)
        # Gap 2: col 66..68 (width 3)
        # Gap 3: col 98..100 (width 3)
        gap_ranges = [(32, 34), (66, 68), (98, 100)]

        for col in range(self.width_tiles):
            in_gap = any(start <= col <= end for start, end in gap_ranges)
            if not in_gap:
                for row in range(ground_y, self.height_tiles):
                    rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    self.tiles.append(rect)
                    self.tile_types[(col, row)] = "ground"

        # 2. Obstacles / Pipes with clear runways
        pipes = [
            (16, 2),  # x=16, h=2
            (25, 3),  # x=25, h=3
            (44, 2),  # x=44, h=2
            (54, 3),  # x=54, h=3
            (78, 2),  # x=78, h=2
            (88, 3),  # x=88, h=3
        ]
        for col, h in pipes:
            for dy in range(h):
                row = ground_y - 1 - dy
                rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.tiles.append(rect)
                self.tile_types[(col, row)] = "pipe"

        # 3. Floating platforms (with collectibles)
        platforms = [
            (20, ground_y - 4, 3),  # above ground
            (48, ground_y - 4, 4),  # mid-stage island
            (72, ground_y - 4, 4),  # post-gap platform
            (84, ground_y - 4, 3),
            (106, ground_y - 4, 5),
        ]
        for col, row, length in platforms:
            for c in range(col, col + length):
                rect = pygame.Rect(c * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.tiles.append(rect)
                self.tile_types[(c, row)] = "platform"
                # Add coin above platform
                self.coins.append(Coin(c * TILE_SIZE + 8, (row - 1) * TILE_SIZE + 8))

        # 4. Staircase pyramid before goal
        stairs_start = 118
        for step in range(5):
            c = stairs_start + step
            for r in range(ground_y - 1 - step, ground_y):
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.tiles.append(rect)
                self.tile_types[(c, r)] = "stair"

        # 5. Enemies (Goombas and Patrols)
        enemy_placements = [
            (21 * TILE_SIZE, ground_y * TILE_SIZE - 28, "goomba", 100),
            (38 * TILE_SIZE, ground_y * TILE_SIZE - 28, "goomba", 90),
            (48 * TILE_SIZE, (ground_y - 5) * TILE_SIZE - 28, "goomba", 60),
            (58 * TILE_SIZE, ground_y * TILE_SIZE - 28, "patrol", 120),
            (74 * TILE_SIZE, ground_y * TILE_SIZE - 28, "goomba", 80),
            (92 * TILE_SIZE, ground_y * TILE_SIZE - 28, "patrol", 110),
            (112 * TILE_SIZE, ground_y * TILE_SIZE - 28, "goomba", 100),
        ]
        for x, y, kind, patrol in enemy_placements:
            self.enemies.append(Enemy(x, y, kind=kind, patrol_distance=patrol))

        # 6. Goal Flag
        goal_x = 132 * TILE_SIZE
        goal_y = (ground_y - 5) * TILE_SIZE
        self.goal = Goal(goal_x, goal_y)

    def is_tile_solid(self, col: int, row: int) -> bool:
        return (col, row) in self.tile_types

    def get_ground_level(self) -> int:
        return (self.height_tiles - 4) * TILE_SIZE

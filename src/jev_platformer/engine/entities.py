"""Entities for the platformer game: Player, Enemies, Coins, Goal with rock-solid ground checking and coyote time."""

import pygame
from typing import Optional, List
from jev_platformer.engine.constants import (
    PLAYER_WIDTH, PLAYER_HEIGHT, ENEMY_WIDTH, ENEMY_HEIGHT,
    GRAVITY, MAX_FALL_SPEED, WALK_SPEED, RUN_SPEED,
    JUMP_STRENGTH, RUN_JUMP_STRENGTH, DECELERATION, ACCELERATION
)


class Player:
    """The player character with responsive jump physics, robust grounding, and air control."""

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        
        self.grounded = False
        self.jumping = False
        self.airborne_frames = 0
        self.coyote_frames = 0
        self.facing_right = True
        self.running = False
        
        # Gameplay stats
        self.lives = 3
        self.score = 0
        self.coins = 0
        self.is_dead = False
        self.has_won = False
        self.stalled_frames = 0
        self.max_x = self.x

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(round(self.x)), int(round(self.y)), self.width, self.height)

    def apply_action(self, action_name: str):
        """Translate Jev / human action into velocity updates."""
        target_speed = RUN_SPEED if "run" in action_name else WALK_SPEED
        
        # Horizontal control
        if "right" in action_name:
            if not self.grounded:
                # Direct responsive air control with full run speed
                self.vx = RUN_SPEED
            else:
                if self.vx < 0:
                    self.vx = ACCELERATION * 2.0
                else:
                    self.vx += ACCELERATION * (2.2 if "run" in action_name else 1.2)
                if self.vx > target_speed:
                    self.vx = target_speed
            self.facing_right = True
            self.running = "run" in action_name
        elif "left" in action_name:
            if not self.grounded and self.airborne_frames > 2:
                self.vx = -WALK_SPEED
            else:
                if self.vx > 0:
                    self.vx = -ACCELERATION * 2.0
                else:
                    self.vx -= ACCELERATION * 1.2
                if self.vx < -WALK_SPEED:
                    self.vx = -WALK_SPEED
            self.facing_right = False
            self.running = False
        else:
            if self.grounded:
                self.vx *= DECELERATION
                if abs(self.vx) < 0.1:
                    self.vx = 0.0
            self.running = False

        # Jump control (supports coyote time for 6 frames after leaving a ledge)
        can_jump = self.grounded or (self.coyote_frames > 0 and not self.jumping)
        if "jump" in action_name and can_jump:
            jump_power = RUN_JUMP_STRENGTH if "run" in action_name else JUMP_STRENGTH
            self.vy = jump_power
            self.grounded = False
            self.jumping = True
            self.airborne_frames = 1
            self.coyote_frames = 0

    def update_physics(self, tiles: List[pygame.Rect]):
        """Update position and resolve AABB collisions against terrain."""
        if self.is_dead:
            self.vy += GRAVITY
            self.y += self.vy
            return

        # 1. Apply gravity
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # 2. Vertical movement
        self.y += self.vy
        was_grounded = self.grounded
        self.grounded = False

        p_rect = self.rect
        for tile in tiles:
            # Check horizontal overlap with tile
            if (p_rect.right > tile.left + 2) and (p_rect.left < tile.right - 2):
                if self.vy >= 0:
                    # Landing on top of tile
                    feet_y = self.y + self.height
                    if tile.top - 8 <= feet_y <= tile.top + 14:
                        self.y = float(tile.top - self.height)
                        self.vy = 0.0
                        self.grounded = True
                        self.jumping = False
                        self.airborne_frames = 0
                        self.coyote_frames = 6
                        p_rect = self.rect
                        break
                elif self.vy < 0:
                    # Head bonk on bottom of tile
                    head_y = self.y
                    if tile.bottom - 12 <= head_y <= tile.bottom:
                        self.y = float(tile.bottom)
                        self.vy = 0.0
                        p_rect = self.rect
                        break

        if not self.grounded:
            self.airborne_frames += 1
            if self.coyote_frames > 0:
                self.coyote_frames -= 1

        # 3. Horizontal movement
        self.x += self.vx
        p_rect = self.rect
        for tile in tiles:
            if p_rect.colliderect(tile):
                # Check if it's a step-up ledge (feet close to top)
                feet_depth = (self.y + self.height) - tile.top
                if 0 < feet_depth <= 10 and self.vy >= 0:
                    self.y = float(tile.top - self.height)
                    self.vy = 0.0
                    self.grounded = True
                    self.jumping = False
                    self.airborne_frames = 0
                    p_rect = self.rect
                else:
                    # Side collision
                    if self.vx > 0:
                        self.x = float(tile.left - self.width)
                    elif self.vx < 0:
                        self.x = float(tile.right)
                    self.vx = 0.0
                    p_rect = self.rect

        # 4. Pit death
        if self.y > 800:
            self.is_dead = True

        # 5. Progress tracking
        if self.x > self.max_x:
            self.max_x = self.x
            self.stalled_frames = 0
        else:
            self.stalled_frames += 1


class Enemy:
    """An enemy creature that patrols platforms."""

    def __init__(self, x: float, y: float, kind: str = "goomba", patrol_distance: float = 120.0):
        self.x = float(x)
        self.y = float(y)
        self.start_x = float(x)
        self.patrol_distance = patrol_distance
        self.kind = kind
        self.width = ENEMY_WIDTH
        self.height = ENEMY_HEIGHT
        
        self.speed = 1.4 if kind == "goomba" else 2.2
        self.vx = -self.speed
        self.vy = 0.0
        self.alive = True
        self.squish_timer = 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(round(self.x)), int(round(self.y)), self.width, self.height)

    def update(self, tiles: List[pygame.Rect]):
        if not self.alive:
            if self.squish_timer > 0:
                self.squish_timer -= 1
            return

        self.x += self.vx
        if self.x < self.start_x - self.patrol_distance:
            self.vx = self.speed
        elif self.x > self.start_x + self.patrol_distance:
            self.vx = -self.speed

        r = self.rect
        for tile in tiles:
            if r.colliderect(tile):
                if self.vx > 0:
                    self.x = float(tile.left - self.width)
                    self.vx = -self.speed
                elif self.vx < 0:
                    self.x = float(tile.right)
                    self.vx = self.speed
                r = self.rect

    def stomp(self):
        self.alive = False
        self.squish_timer = 30


class Coin:
    """Collectible score orb."""

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.width = 16
        self.height = 16
        self.collected = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(round(self.x)), int(round(self.y)), self.width, self.height)


class Goal:
    """Stage endpoint flag/portal."""

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.width = 32
        self.height = 180

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(round(self.x)), int(round(self.y)), self.width, self.height)

"""Tests for player physics, terrain collision, and enemy interactions."""

import pytest
from jev_platformer.engine.constants import TILE_SIZE
from jev_platformer.engine.entities import Player, Enemy
from jev_platformer.engine.world import Level


def test_player_initialization():
    player = Player(100, 200)
    assert player.x == 100
    assert player.y == 200
    assert player.vx == 0.0
    assert player.vy == 0.0
    assert not player.grounded
    assert not player.is_dead


def test_player_horizontal_movement():
    player = Player(100, 200)
    player.apply_action("right")
    assert player.vx > 0
    assert player.facing_right

    player.apply_action("left")
    assert player.vx < 0
    assert not player.facing_right


def test_player_jump_only_when_grounded():
    player = Player(100, 200)
    # When airborne, jump action should not apply jump strength
    player.grounded = False
    player.apply_action("jump")
    assert player.vy == 0.0

    # When grounded, jump action applies vertical impulse
    player.grounded = True
    player.apply_action("jump")
    assert player.vy < 0
    assert not player.grounded


def test_terrain_collision_and_grounding():
    level = Level(1)
    # Spawn player right above ground
    ground_y = level.get_ground_level()
    player = Player(100, ground_y - 60)
    
    # Update physics multiple frames until landing
    for _ in range(30):
        player.update_physics(level.tiles)

    assert player.grounded
    assert player.y == ground_y - player.height
    assert player.vy == 0.0


def test_enemy_stomp_and_defeat():
    level = Level(1)
    enemy = Enemy(150, 400)
    player = Player(150, 360)
    
    assert enemy.alive
    enemy.stomp()
    assert not enemy.alive
    assert enemy.squish_timer > 0

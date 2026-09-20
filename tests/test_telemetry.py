"""Tests for telemetry extraction and Jev observation schemas."""

import json
import pytest
from jev_platformer.engine.entities import Player, Enemy
from jev_platformer.engine.world import Level
from jev_platformer.telemetry.extractor import TelemetryExtractor
from jev_platformer.telemetry.models import JevObservation


def test_telemetry_extraction_schema():
    level = Level(1)
    player = Player(level.start_pos[0], level.start_pos[1])
    obs = TelemetryExtractor.extract(player, level)

    assert isinstance(obs, JevObservation)
    assert obs.player.x == level.start_pos[0]
    assert obs.player.y == level.start_pos[1]
    assert obs.player.grounded == player.grounded
    assert len(obs.local_grid) == 7
    assert len(obs.local_grid[0]) == 11

    # Verify JSON serialization works without issues
    json_str = obs.model_dump_json()
    assert "objective" in json_str
    assert "player" in json_str
    assert "hazard" in json_str
    assert "terrain" in json_str


def test_telemetry_hazard_detection():
    level = Level(1)
    player = Player(100, 500)
    player.grounded = True
    # Place enemy 50 pixels ahead of player
    enemy = Enemy(150, 500)
    level.enemies = [enemy]

    obs = TelemetryExtractor.extract(player, level)
    assert obs.hazard.enemy_ahead
    assert obs.hazard.nearest_enemy is not None
    assert obs.hazard.nearest_enemy.distance_pixels == pytest.approx(50.0, abs=1.0)
    assert obs.hazard.in_danger_zone
    assert obs.hazard.jump_must_start_now


def test_telemetry_gap_detection():
    level = Level(1)
    # Spawn player 2 tiles before the first pit (at col 30, col 32 is gap)
    player = Player(30 * 32, 540)
    player.grounded = True
    obs = TelemetryExtractor.extract(player, level)

    assert obs.terrain.gap_ahead
    assert obs.terrain.gap_distance_tiles is not None
    assert obs.terrain.gap_distance_tiles <= 3.0

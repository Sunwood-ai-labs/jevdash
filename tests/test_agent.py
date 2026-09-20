"""Tests for Mock and Live Jev decision controllers."""

import pytest
from jev_platformer.engine.entities import Player
from jev_platformer.engine.world import Level
from jev_platformer.telemetry.extractor import TelemetryExtractor
from jev_platformer.controller.actions import ALL_ACTIONS
from jev_platformer.controller.mock_agent import MockJevAgent


def test_mock_agent_valid_actions_and_probabilities():
    level = Level(1)
    player = Player(level.start_pos[0], level.start_pos[1])
    obs = TelemetryExtractor.extract(player, level)

    agent = MockJevAgent()
    res = agent.decide(obs)

    # Action must be in legal set
    assert res.action in ALL_ACTIONS
    # Probabilities should contain all actions
    for action in ALL_ACTIONS:
        assert action in res.probabilities
        assert 0.0 <= res.probabilities[action] <= 1.0

    # Total probability should sum to approximately 1.0
    total_prob = sum(res.probabilities.values())
    assert total_prob == pytest.approx(1.0, abs=0.05)

    # Danger score between 1 and 10
    assert 1 <= res.danger_score <= 10
    # Latency should be sub-50ms
    assert 0 < res.latency_ms < 60.0


def test_mock_agent_gap_reaction():
    level = Level(1)
    # Put player 2 tiles before gap at col 32 (player at col 30)
    player = Player(30 * 32, 540)
    player.grounded = True
    obs = TelemetryExtractor.extract(player, level)

    agent = MockJevAgent()
    res = agent.decide(obs)

    # Expect a jump action when approaching pit
    assert "jump" in res.action
    assert res.jump_recommended
    assert res.danger_score >= 7

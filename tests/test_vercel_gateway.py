"""Integration test for Vercel AI Gateway Jev client."""

import pytest
from jev_platformer.controller.vercel_gateway import VercelGatewayJevClient
from jev_platformer.telemetry.models import JevObservation, PlayerTelemetry, HazardTelemetry, TerrainTelemetry


from jev_platformer.engine.entities import Player
from jev_platformer.engine.world import Level
from jev_platformer.telemetry.extractor import TelemetryExtractor


def test_vercel_gateway_connectivity_and_inference():
    client = VercelGatewayJevClient()
    if not client.is_configured:
        pytest.skip("AI_GATEWAY_API_KEY is not configured.")

    level = Level(1)
    player = Player(level.start_pos[0], level.start_pos[1])
    obs = TelemetryExtractor.extract(player, level)

    result = client.evaluate(obs)
    print(f"\n[Test Result] Action: {result.action}, Latency: {result.latency_ms}ms, Danger: {result.danger_score}, is_mock: {result.is_mock}")
    assert result.is_mock is False
    assert result.action in ["right_run", "right_run_jump", "right_jump", "right", "jump", "noop", "left"]
    assert 1 <= result.danger_score <= 10
    assert result.latency_ms > 0


def test_vercel_gateway_pipe_jump_reaction():
    """Confirms Jev chooses a jump action when stalled against a pipe obstacle."""
    client = VercelGatewayJevClient()
    if not client.is_configured:
        pytest.skip("AI_GATEWAY_API_KEY is not configured.")

    level = Level(1)
    # Position player right before the col 16 pipe (x=485.0)
    player = Player(485.0, 500.0)
    player.grounded = True
    player.vx = 0.0
    obs = TelemetryExtractor.extract(player, level)
    obs.episode.stalled_frames = 4  # Blocked against wall

    result = client.evaluate(obs)
    print(f"\n[Obstacle Test Result] Action: {result.action}, Latency: {result.latency_ms}ms, Danger: {result.danger_score}")
    assert result.action in ["right_run_jump", "right_jump", "jump"]

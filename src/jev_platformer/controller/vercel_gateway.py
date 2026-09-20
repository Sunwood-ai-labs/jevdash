"""Vercel AI Gateway client for TypeSafe Jev (typesafe-ai/jev)."""

import os
import json
import time
import urllib.request
from typing import Optional, Dict, Any

from jev_platformer.controller.actions import ALL_ACTIONS, Action
from jev_platformer.controller.mock_agent import DecisionResult
from jev_platformer.telemetry.models import JevObservation


class VercelGatewayJevClient:
    """Invokes typesafe-ai/jev via Vercel AI Gateway endpoint."""

    GATEWAY_ENDPOINT = "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
    MODEL_ID = "typesafe-ai/jev"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AI_GATEWAY_API_KEY")
        if not self.api_key:
            # Attempt to auto-load from c:/Prj/vercel-ai-gateway-jev/.env
            env_path = "c:/Prj/vercel-ai-gateway-jev/.env"
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("AI_GATEWAY_API_KEY="):
                                self.api_key = line.strip().split("=", 1)[1]
                                os.environ["AI_GATEWAY_API_KEY"] = self.api_key
                                break
                except Exception:
                    pass

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def evaluate(self, obs: JevObservation) -> DecisionResult:
        """Sends structured game state to Vercel AI Gateway Jev and returns DecisionResult."""
        if not self.api_key:
            raise ValueError("AI_GATEWAY_API_KEY is not configured.")

        # Build comprehensive semantic state string
        nearest_enemy_str = "None"
        if obs.hazard.nearest_enemy:
            nearest_enemy_str = (
                f"{obs.hazard.nearest_enemy.kind} at {obs.hazard.nearest_enemy.distance_pixels:.1f}px ahead "
                f"(contact in {obs.hazard.nearest_enemy.estimated_contact_frames} frames)"
            )

        gap_str = (
            f"Pit gap edge is {obs.terrain.gap_distance_tiles:.1f} tiles ahead (width: {obs.terrain.gap_width_tiles} tiles)"
            if obs.terrain.gap_ahead and obs.terrain.gap_distance_tiles is not None
            else "No gap ahead"
        )

        obstacle_str = (
            f"Solid pipe/block obstacle is {obs.terrain.obstacle_distance_tiles:.1f} tiles ahead (height: {obs.terrain.obstacle_height_tiles} tiles)"
            if obs.terrain.obstacle_ahead and obs.terrain.obstacle_distance_tiles is not None
            else "No obstacle ahead"
        )

        stalled_str = (
            f"BLOCKED AGAINST WALL! Player has made zero forward progress for {obs.episode.stalled_frames} frames!"
            if obs.episode.stalled_frames > 2
            else "Moving smoothly forward"
        )

        radar_str = "\n".join(obs.local_grid)

        state_summary = (
            f"=== PLAYER STATE ===\n"
            f"Position: x={obs.player.x:.1f}, y={obs.player.y:.1f}\n"
            f"Velocity: vx={obs.player.vx:.2f}, vy={obs.player.vy:.2f}\n"
            f"Grounded: {obs.player.grounded}, Jumping: {obs.player.jumping}\n"
            f"Progress: {obs.episode.progress_pixels:.1f}px, Goal Distance: {obs.episode.goal_distance_pixels:.1f}px\n"
            f"Status: {stalled_str}\n\n"
            f"=== SURROUNDINGS & HAZARDS ===\n"
            f"Obstacle Ahead: {obstacle_str}\n"
            f"Pit Gap Ahead: {gap_str}\n"
            f"Enemy Ahead: {nearest_enemy_str}\n"
            f"Jump Must Start Now: {obs.hazard.jump_must_start_now}\n\n"
            f"=== LOCAL RADAR (P=Player, E=Enemy, #=Solid Block, .=Air) ===\n"
            f"{radar_str}"
        )

        payload = {
            "state": state_summary,
            "questions": {
                "action": {
                    "type": "choice",
                    "instructions": (
                        "Select the optimal action macro to reach the goal flag safely. "
                        "RULES: "
                        "1. If an obstacle pipe or gap is within 3.0 tiles ahead, or if the player is BLOCKED/STALLED against a block, "
                        "you MUST choose 'right_run_jump' or 'right_jump' to jump over it! "
                        "2. If an enemy is approaching, choose 'right_run_jump' to stomp or jump over it. "
                        "3. Otherwise, when path is clear, choose 'right_run' to dash forward at maximum speed."
                    ),
                    "criteria": {
                        "right_run_jump": "Running leap forward over pipes, obstacles, gaps, or enemies.",
                        "right_jump": "Jump right to clear an immediate low obstacle.",
                        "right_run": "Sprint forward across flat open ground.",
                        "right": "Walk right cautiously.",
                        "jump": "Jump straight up to gain height.",
                        "noop": "Coast / wait for timing.",
                        "left": "Backtrack away from danger."
                    }
                },
                "jump_urgency": {
                    "type": "boolean",
                    "instructions": (
                        "Must the player jump right now because of an upcoming pipe/obstacle, "
                        "pit gap, enemy collision, or being blocked against a wall?"
                    )
                },
                "threat_level": {
                    "type": "score",
                    "instructions": "Assess the immediate collision danger from 1 (completely safe open ground) to 10 (deadly pit/enemy/wall collision).",
                    "criteria": ["safe", "caution", "danger", "critical"]
                }
            },
            "providerOptions": {}
        }

        req = urllib.request.Request(
            self.GATEWAY_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "ai-model-id": self.MODEL_ID,
                "ai-evaluation-model-specification-version": "4",
                "ai-gateway-auth-method": "api-key",
                "ai-gateway-protocol-version": "0.0.1",
                "content-type": "application/json",
                "user-agent": "jevdash/1.0.0 python-urllib"
            },
            method="POST"
        )

        start_time = time.perf_counter()
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        answers = data.get("answers", {})

        # Parse Choice
        action_obj = answers.get("action", {})
        chosen_action = action_obj.get("choice", Action.RIGHT_RUN.value)
        probs = action_obj.get("probabilities", {a: 0.14 for a in ALL_ACTIONS})
        
        # Ensure all actions exist in probs dictionary
        for a in ALL_ACTIONS:
            if a not in probs:
                probs[a] = 0.0

        # Parse Boolean
        jump_obj = answers.get("jump_urgency", {})
        jump_prob = jump_obj.get("probability", 0.0)
        jump_rec = jump_prob >= 0.5

        # If Jev flags high jump urgency or if player is stalled against a pipe, commit to jumping forward
        if (jump_rec or obs.episode.stalled_frames >= 3 or (obs.terrain.obstacle_ahead and (obs.terrain.obstacle_distance_tiles or 99) <= 2.5)) and obs.player.grounded:
            if chosen_action not in (Action.RIGHT_RUN_JUMP.value, Action.RIGHT_JUMP.value, Action.JUMP.value):
                chosen_action = Action.RIGHT_RUN_JUMP.value
                probs[Action.RIGHT_RUN_JUMP.value] = max(probs.get(Action.RIGHT_RUN_JUMP.value, 0.0), 0.75)

        # Parse Score
        threat_obj = answers.get("threat_level", {})
        raw_score = threat_obj.get("score", 1.0)
        danger_score = max(1, min(10, int(round(float(raw_score) * 2.5 + 1.0))))

        return DecisionResult(
            action=chosen_action,
            probabilities=probs,
            danger_score=danger_score,
            jump_recommended=jump_rec,
            latency_ms=round(elapsed_ms, 1),
            is_mock=False
        )

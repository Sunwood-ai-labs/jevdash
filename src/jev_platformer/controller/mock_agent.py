"""High-performance mock heuristic decision agent simulating Jev's output format."""

import time
import random
from typing import Dict
from dataclasses import dataclass

from jev_platformer.controller.actions import ALL_ACTIONS, Action
from jev_platformer.telemetry.models import JevObservation


@dataclass
class DecisionResult:
    action: str
    probabilities: Dict[str, float]
    danger_score: int          # 1 to 10
    jump_recommended: bool     # Noul boolean judgment
    latency_ms: float          # Simulated inference time in ms
    is_mock: bool = True


class MockJevAgent:
    """Calculates tactical actions with simulated probability distributions using nearest threat evaluation."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def decide(self, obs: JevObservation) -> DecisionResult:
        start_time = time.perf_counter()
        
        player = obs.player
        hazard = obs.hazard
        terrain = obs.terrain

        probs: Dict[str, float] = {a: 0.02 for a in ALL_ACTIONS}
        danger_score = 1
        jump_recommended = False

        # 1. Evaluate imminent enemy threat using Time-to-Collision
        enemy_threat_imminent = False
        if hazard.enemy_ahead and hazard.nearest_enemy is not None:
            enemy = hazard.nearest_enemy
            dist_px = enemy.distance_pixels
            contact_f = enemy.estimated_contact_frames
            
            # If enemy is within 140px or collision is under 18 frames, take off!
            if dist_px <= 140 or (contact_f is not None and contact_f <= 18) or hazard.jump_must_start_now:
                enemy_threat_imminent = True
                danger_score = max(danger_score, 8)
                if player.grounded:
                    probs[Action.RIGHT_RUN_JUMP.value] = 0.85
                    probs[Action.RIGHT_JUMP.value] = 0.10
                    jump_recommended = True
                else:
                    probs[Action.RIGHT_RUN.value] = 0.80

        if not enemy_threat_imminent:
            # 2. Compare distances of upcoming terrain threats (Obstacle vs Pit Gap)
            obs_dist = terrain.obstacle_distance_tiles if terrain.obstacle_ahead else 999.0
            gap_dist = terrain.gap_distance_tiles if terrain.gap_ahead else 999.0

            if obs_dist < gap_dist and obs_dist <= 3.6:
                # Obstacle is closer and within jump takeoff range
                h = terrain.obstacle_height_tiles
                danger_score = max(danger_score, 4 + min(4, h))
                if player.grounded:
                    probs[Action.RIGHT_RUN_JUMP.value] = 0.90
                    probs[Action.RIGHT_JUMP.value] = 0.08
                    jump_recommended = True
                else:
                    probs[Action.RIGHT_RUN.value] = 0.80

            elif gap_dist <= obs_dist and gap_dist <= 4.0:
                # Pit gap is closer and within takeoff range
                danger_score = 9
                if player.grounded:
                    probs[Action.RIGHT_RUN_JUMP.value] = 0.92
                    probs[Action.RIGHT_JUMP.value] = 0.06
                    jump_recommended = True
                else:
                    probs[Action.RIGHT_RUN.value] = 0.80

            else:
                # Path ahead is clear or threats are distant -> Fast dash!
                probs[Action.RIGHT_RUN.value] = 0.85
                probs[Action.RIGHT.value] = 0.10

        # Normalize probabilities so sum = 1.0
        total = sum(probs.values())
        normalized_probs = {k: round(v / total, 3) for k, v in probs.items()}
        
        # Select action with highest probability
        chosen_action = max(normalized_probs, key=normalized_probs.get)

        # Simulate Jev's ultra-low latency (18ms to 32ms)
        elapsed_real = (time.perf_counter() - start_time) * 1000.0
        simulated_latency = round(self.rng.uniform(18.5, 34.2) + elapsed_real, 1)

        return DecisionResult(
            action=chosen_action,
            probabilities=normalized_probs,
            danger_score=danger_score,
            jump_recommended=jump_recommended,
            latency_ms=simulated_latency,
            is_mock=True,
        )

    def decide_initial(self) -> DecisionResult:
        """Returns a default safe forward action for initial state."""
        probs = {a: 0.02 for a in ALL_ACTIONS}
        probs[Action.RIGHT_RUN.value] = 0.88
        total = sum(probs.values())
        return DecisionResult(
            action=Action.RIGHT_RUN.value,
            probabilities={k: round(v / total, 3) for k, v in probs.items()},
            danger_score=1,
            jump_recommended=False,
            latency_ms=25.0,
            is_mock=True,
        )


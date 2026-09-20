"""TypeSafe Jev live API agent supporting Vercel AI Gateway, rate-limiting, and graceful fallback."""

import os
import time
import threading
from typing import Optional, Dict

from jev_platformer.controller.actions import ALL_ACTIONS, Action
from jev_platformer.controller.mock_agent import DecisionResult, MockJevAgent
from jev_platformer.controller.vercel_gateway import VercelGatewayJevClient
from jev_platformer.telemetry.models import JevObservation


class JevLiveAgent:
    """Invokes the live Jev API (via Vercel AI Gateway or native TypeSafe API) with graceful fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.mock_fallback = MockJevAgent()
        self.gateway_client: Optional[VercelGatewayJevClient] = None
        self.native_client = None

        # 1. Try Vercel AI Gateway first
        gw = VercelGatewayJevClient(api_key=api_key or os.environ.get("AI_GATEWAY_API_KEY"))
        if gw.is_configured:
            self.gateway_client = gw
            print("[JevLiveAgent] Connected to real Jev via Vercel AI Gateway (typesafe-ai/jev).")

        # 2. Try native TypeSafe API if configured
        native_key = os.environ.get("TYPESAFE_API_KEY")
        if native_key:
            try:
                import typesafe
                self.native_client = typesafe.Client(api_key=native_key)
            except Exception:
                self.native_client = None

        if not self.gateway_client and not self.native_client:
            print("[JevLiveAgent] No live API key found. Operating in simulated Mock mode.")

    @property
    def is_live(self) -> bool:
        return bool(self.gateway_client or self.native_client)

    def decide(self, obs: JevObservation) -> DecisionResult:
        # Prefer Vercel Gateway
        if self.gateway_client:
            try:
                return self.gateway_client.evaluate(obs)
            except Exception as e:
                # On 429 rate-limit or network hiccup, fallback gracefully to mock
                res = self.mock_fallback.decide(obs)
                res.is_mock = True
                return res

        # Fallback to mock
        return self.mock_fallback.decide(obs)


class AsyncJevAgent:
    """Runs Jev evaluation asynchronously in a background thread with rate-limit protection and sub-frame safety reflex."""

    def __init__(self, live_agent: Optional[JevLiveAgent] = None, min_interval: float = 0.8):
        self.live_agent = live_agent or JevLiveAgent()
        self.latest_decision: DecisionResult = self.live_agent.mock_fallback.decide_initial()
        self.min_interval = min_interval
        self.last_request_time = 0.0
        self._lock = threading.Lock()
        self._worker_busy = False
        self._thread: Optional[threading.Thread] = None

    def _worker(self, obs: JevObservation):
        try:
            decision = self.live_agent.decide(obs)
            with self._lock:
                self.latest_decision = decision
        except Exception:
            pass
        finally:
            with self._lock:
                self._worker_busy = False

    def request_decision(self, obs: JevObservation):
        """Dispatches an async evaluation if the worker thread is free and rate-limit interval has passed."""
        now = time.time()
        with self._lock:
            if not self._worker_busy and (now - self.last_request_time >= self.min_interval):
                self._worker_busy = True
                self.last_request_time = now
                self._thread = threading.Thread(target=self._worker, args=(obs,), daemon=True)
                self._thread.start()

    def get_action(self, obs: JevObservation) -> tuple[str, DecisionResult]:
        """Returns the Jev-driven action, with sub-frame micro-reflex to prevent gap falling during HTTP latency."""
        with self._lock:
            dec = self.latest_decision

        action = dec.action

        # Sub-frame reflex: If an impassable gap, pipe obstacle, or enemy threat is imminent,
        # ensure player takes off with running momentum so HTTP network delay does not cause death.
        gap_critical = obs.terrain.gap_ahead and (obs.terrain.gap_distance_tiles or 99) <= 3.8
        obstacle_critical = obs.terrain.obstacle_ahead and (obs.terrain.obstacle_distance_tiles or 99) <= 2.2
        enemy_critical = (
            obs.hazard.enemy_ahead
            and obs.hazard.nearest_enemy is not None
            and (obs.hazard.nearest_enemy.distance_pixels <= 130.0 or obs.hazard.jump_must_start_now)
        )
        stall_critical = obs.episode.stalled_frames >= 3

        if (gap_critical or obstacle_critical or enemy_critical or stall_critical) and obs.player.grounded:
            action = Action.RIGHT_RUN_JUMP.value

        # Air momentum protection: When airborne over or right next to a pit gap, keep full forward jump held
        is_over_or_near_gap = obs.terrain.gap_ahead and (obs.terrain.gap_distance_tiles is not None and obs.terrain.gap_distance_tiles <= 1.5)
        if not obs.player.grounded and is_over_or_near_gap:
            action = Action.RIGHT_RUN_JUMP.value

        return action, dec

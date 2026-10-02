"""No GPU/network required: privacy boundary, compatibility, wall-clock and recorder tests."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from jev_platformer.vision_trial import public_request, vision_state


def test_vision_observation_has_no_engine_state():
    state = vision_state([{"frame_id": 8, "captured_wall_seconds": 0.133}], "right")
    assert set(state) == {
        "objective",
        "images_order",
        "frames",
        "previous_commanded_action",
        "physics_hz",
        "action_persistence",
    }
    assert state["frames"] == [{"frame_id": 8, "captured_wall_seconds": 0.133}]
    assert not {"player", "terrain", "hazard", "local_grid", "score"} & state.keys()


def test_response_logs_do_not_echo_pixel_bytes():
    req = {"request_id": 3, "images": [{"rgb": b"raw pixels"}], "state": {"frames": []}}
    result = public_request(req)
    assert "images" not in result
    json.dumps(result)
    assert req["images"][0]["rgb"] == b"raw pixels"


@pytest.mark.parametrize("mode", ["human", "mock", "ai", "live"])
def test_existing_play_cli_dispatch_unchanged(monkeypatch, mode):
    from jev_platformer import cli

    calls = []
    monkeypatch.setattr(cli, "run_play", lambda **kw: calls.append(kw))
    monkeypatch.setattr(
        sys, "argv", ["jevdash", "play", "--mode", mode, "--max-frames", "3"]
    )
    cli.main()
    assert calls == [
        {
            "mode": mode,
            "frames_per_decision": 8,
            "display": "all",
            "record_path": "jevdash_gameplay.mp4",
            "max_frames": 3,
        }
    ]


def test_existing_default_cli_is_ai(monkeypatch):
    from jev_platformer import cli

    calls = []
    monkeypatch.setattr(cli, "run_play", lambda **kw: calls.append(kw))
    monkeypatch.setattr(sys, "argv", ["jevdash"])
    cli.main()
    assert calls[0]["mode"] == "ai"


def test_vision_cli_is_opt_in(monkeypatch):
    from jev_platformer import cli, vision_trial

    calls = []
    monkeypatch.setattr(vision_trial, "main", lambda argv: calls.append(argv))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "jevdash",
            "vision-clef",
            "--out",
            "result",
            "--episodes",
            "1",
            "--seconds",
            "2",
            "--smoke",
        ],
    )
    cli.main()
    assert calls == [
        ["--out", "result", "--episodes", "1", "--seconds", "2.0", "--smoke"]
    ]


@pytest.mark.parametrize(
    "flag,value",
    [("--episodes", "0"), ("--episodes", "4"), ("--seconds", "0"), ("--seconds", "61")],
)
def test_bounds_fail_before_loading_model(tmp_path, flag, value):
    from jev_platformer.vision_trial import main

    with pytest.raises(ValueError, match="bounds"):
        main(["--out", str(tmp_path), flag, value])


def test_only_optional_extra_has_heavy_dependencies():
    import tomllib

    root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    assert not any(
        dep.startswith(("torch", "transformers", "av", "numpy"))
        for dep in config["dependencies"]
    )
    assert any(
        dep.startswith("torch") for dep in config["optional-dependencies"]["clef"]
    )


@pytest.mark.skipif(
    importlib.util.find_spec("av") is None,
    reason="Optional vision-recording extra not installed",
)
def test_capture_timestamps_are_preserved(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    import av
    import pygame

    from jev_platformer.vision_trial import TimestampVideo

    video = TimestampVideo(tmp_path / "timing.mp4", 64, 64)
    surface = pygame.Surface((64, 64))
    video.capture(surface, 100)
    surface.fill((255, 0, 0))
    video.capture(surface, 100.25)
    stats = video.close()
    assert stats["encoded_frames"] == 2 and stats["dropped_frames"] == 0
    with av.open(str(tmp_path / "timing.mp4")) as container:
        frames = list(container.decode(video=0))
        assert float(
            frames[1].pts * frames[1].time_base - frames[0].pts * frames[0].time_base
        ) == pytest.approx(0.25, abs=0.001)


@pytest.mark.skipif(
    importlib.util.find_spec("av") is None,
    reason="Optional vision-recording extra not installed",
)
def test_slow_fixture_does_not_pause_physics_or_video(tmp_path):
    """Explicit fixture, never represents actual Clef gameplay ability."""
    env = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "jev_platformer.vision_trial",
            "--out",
            str(tmp_path),
            "--smoke",
            "--episodes",
            "2",
            "--seconds",
            "1.5",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["model"] == "TEST FIXTURE"
    for ep in summary["episodes"]:
        assert ep["model_ms_median"] >= 390
        assert ep["physics_updates"] >= 85
        assert ep["decisions_applied"] >= 2
        assert ep["realtime_validation_pass"]
        assert ep["encoded_frames"] >= 145
        frames = [
            json.loads(line)
            for line in (tmp_path / f"episode-{ep['episode']:02d}-frames.jsonl")
            .read_text()
            .splitlines()
        ]
        # The model takes ~24 physics steps to reply; the world advances throughout.
        first_decision = next(
            i for i, row in enumerate(frames) if row["decision_id"] is not None
        )
        assert first_decision >= 20
        assert frames[first_decision]["physics_updates"] >= 20
        assert all(row["action"] == "noop" for row in frames[:first_decision])
        assert frames[-1]["status"] == "time_limit"
        logs = [
            json.loads(line)
            for line in (tmp_path / f"episode-{ep['episode']:02d}-decisions.jsonl")
            .read_text()
            .splitlines()
        ]
        late = [
            row
            for row in logs
            if row.get("response_status") == "unapplied_after_episode"
        ]
        assert late, (
            "The slow fixture should return a final answer after the time limit"
        )
        for row in late:
            assert row["applied_frame"] is None and row["applied_mono"] is None
            assert row["end_to_end_ms"] is None
            assert all(frame["decision_id"] != row["request_id"] for frame in frames)


@pytest.mark.skipif(
    importlib.util.find_spec("av") is None, reason="Optional extra not installed"
)
def test_output_directory_reuse_refused_before_model_start(tmp_path):
    from jev_platformer.vision_trial import main

    evidence = tmp_path / "old-result.txt"
    evidence.write_text("preserve")
    with pytest.raises(ValueError, match="empty"):
        main(["--out", str(tmp_path), "--smoke"])
    assert evidence.read_text() == "preserve"


def test_recorder_shutdown_has_bounded_queue_wait():
    import queue
    import time

    from jev_platformer.vision_trial import TimestampVideo

    class StuckThread:
        def is_alive(self):
            return True

        def join(self, timeout):
            pass

    video = TimestampVideo.__new__(TimestampVideo)
    video.frames = queue.Queue(1)
    video.frames.put("blocked")
    video.thread = StuckThread()
    video.close_attempted = False
    start = time.perf_counter()
    with pytest.raises(RuntimeError, match="did not exit"):
        video.close(timeout=0.05)
    assert time.perf_counter() - start < 0.5
    assert video.close_attempted


@pytest.mark.skipif(
    importlib.util.find_spec("av") is None or sys.platform == "win32",
    reason="Recording extra and Unix fault-injection required",
)
def test_dead_worker_exits_with_error_without_queue_feeder_hang(tmp_path):
    script = """
import multiprocessing as mp, os, time
from jev_platformer import vision_trial as v
real_context=mp.get_context
v.mp.get_context=lambda kind: real_context('fork')
def failed_worker(reqs, resps, *args):
    resps.put({'kind':'ready'}); resps.close(); resps.join_thread()
    time.sleep(.15)
    os._exit(3)
v.model_worker=failed_worker
v.main(['--out',os.environ['TEST_OUTPUT'],'--smoke','--seconds','1.5'])
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={
            **os.environ,
            "SDL_VIDEODRIVER": "dummy",
            "SDL_AUDIODRIVER": "dummy",
            "TEST_OUTPUT": str(tmp_path),
        },
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    assert result.returncode != 0
    assert "worker exited unexpectedly" in result.stderr
    assert not (tmp_path / "summary.json").exists()


@pytest.mark.skipif(
    importlib.util.find_spec("av") is None, reason="Recording extra required"
)
def test_cancel_stops_entire_session(tmp_path, monkeypatch):
    import queue

    from jev_platformer import vision_trial as v

    class LocalQueue(queue.Queue):
        def cancel_join_thread(self):
            pass

        def close(self):
            pass

    class FakeProcess:
        def __init__(self, target, args, **kwargs):
            self.responses = args[1]

        def start(self):
            self.responses.put({"kind": "ready"})

        def join(self, timeout):
            pass

        def is_alive(self):
            return False

    class FakeContext:
        Queue = LocalQueue
        Process = FakeProcess

    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setattr(v.mp, "get_context", lambda _: FakeContext())
    calls = []

    def cancelled(*args):
        calls.append(args[1])
        return {"result": "cancelled"}, False, 2, None

    monkeypatch.setattr(v, "run_episode", cancelled)
    v.main(["--out", str(tmp_path), "--smoke", "--episodes", "3"])
    assert calls == [1]
    assert len(json.loads((tmp_path / "summary.json").read_text())["episodes"]) == 1


@pytest.mark.skipif(
    importlib.util.find_spec("av") is None, reason="Recording extra required"
)
def test_pending_inference_deadline_fails_without_fallback(tmp_path, monkeypatch):
    import queue
    import time
    from types import SimpleNamespace

    import pygame

    from jev_platformer import vision_trial as v

    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        with pytest.raises(TimeoutError, match="10 real seconds"):
            v.run_episode(
                SimpleNamespace(smoke=True, seconds=1),
                1,
                queue.Queue(1),
                queue.Queue(),
                True,
                2,
                tmp_path,
                pending_since=time.perf_counter() - 11,
            )
    finally:
        pygame.quit()


def test_worker_death_during_load_is_detected_promptly():
    import queue
    import time
    from types import SimpleNamespace

    from jev_platformer.vision_trial import wait_ready

    start = time.perf_counter()
    with pytest.raises(RuntimeError, match="during model loading"):
        wait_ready(SimpleNamespace(is_alive=lambda: False), queue.Queue(), timeout=10)
    assert time.perf_counter() - start < 1


@pytest.mark.skipif(
    importlib.util.find_spec("av") is None, reason="Recording extra required"
)
def test_expired_queued_decision_cannot_bypass_deadline(tmp_path, monkeypatch):
    import queue
    import time
    from types import SimpleNamespace

    import pygame

    from jev_platformer import vision_trial as v

    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    responses = queue.Queue()
    responses.put(
        {"kind": "decision", "episode": 1, "observed_mono": time.perf_counter() - 11}
    )
    pygame.init()
    try:
        with pytest.raises(TimeoutError, match="stale action was not applied"):
            v.run_episode(
                SimpleNamespace(smoke=True, seconds=1),
                1,
                queue.Queue(1),
                responses,
                True,
                2,
                tmp_path,
            )
    finally:
        pygame.quit()


@pytest.mark.parametrize("terminal", ["goal", "died", "time_limit", "cancelled"])
def test_post_episode_response_is_explicitly_unapplied(terminal):
    from jev_platformer.vision_trial import annotate_response

    response = annotate_response(
        {"request_id": 7, "observed_mono": 10, "observed_frame": 60},
        10.8,
        108,
        terminal,
    )
    assert response["response_status"] == "unapplied_after_episode"
    assert response["received_frame"] == 108
    assert response["capture_to_receive_ms"] == pytest.approx(800)
    assert response["applied_frame"] is None
    assert response["applied_mono"] is None
    assert response["end_to_end_ms"] is None


def test_live_episode_response_keeps_real_application_timestamp():
    from jev_platformer.vision_trial import annotate_response

    response = annotate_response(
        {"request_id": 7, "observed_mono": 10, "observed_frame": 60}, 10.8, 108, None
    )
    assert response["response_status"] == "applied"
    assert response["applied_frame"] == 108
    assert response["applied_mono"] == 10.8
    assert response["end_to_end_ms"] == pytest.approx(800)

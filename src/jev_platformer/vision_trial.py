"""Optional screenshot-only Clef controller with unmodified JevDash physics and wall-clock video.
The --smoke path is a marked test fixture, never a model-performance result.
"""

import argparse
import hashlib
import importlib.metadata
import json
import math
import multiprocessing as mp
import os
import queue
import statistics
import sys
import threading
import time
import traceback
from fractions import Fraction
from pathlib import Path

GAME_COMMIT = "eb2f92617bab5d5021a5e3cf5ef2bdaf8207d480"
MODEL = "Cloudflare/clef-flash"
REVISION = "17f0b0ad64efb65d273590632833508766b2aae6"
CODE_SHA = "0e304cf7c6500e8bb59bef7e2afd2c6373f82596dfb3b57d1aa93c175e2dc3a3"
ACTIONS = ["noop", "right", "right_run", "right_jump", "right_run_jump", "jump", "left"]
QUESTIONS = {
    "action": {
        "type": "choice",
        "instructions": "Select the best next control to reach the goal flag without dying. This is a live 60 Hz platformer. "
        "Time continues during inference. Your action will be held until your next decision arrives. "
        "Look at the attached game images, oldest first and newest last. The cyan figure is your player; "
        "green blocks are solid obstacles, dark ground gaps are pits, and red figures are enemies. "
        "Choose using the newest image rather than blindly repeating the previous action.",
        "criteria": {
            "noop": "Release all movement and jump buttons.",
            "right": "Hold right to walk forward.",
            "right_run": "Hold right and run to dash forward.",
            "right_jump": "Hold right and jump to move forward and jump.",
            "right_run_jump": "Hold right, run and jump for a forward running jump.",
            "jump": "Hold jump without horizontal direction.",
            "left": "Hold left to move backward.",
        },
    }
}


def save(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(path)


def vision_state(frame_metadata, last_action):
    """Only image timestamps and prior commanded action; never engine telemetry."""
    return {
        "objective": "Reach the goal at the right without dying.",
        "images_order": "oldest first, newest last",
        "frames": frame_metadata,
        "previous_commanded_action": last_action,
        "physics_hz": 60,
        "action_persistence": "Held until a new inference completes. The game never waits.",
    }


def public_request(req):
    return {k: v for k, v in req.items() if k != "images"}


def annotate_response(result, now, frame, terminal):
    """Distinguish receiving an answer from actually applying it to a live episode."""
    applied = terminal is None
    delay_ms = (now - result["observed_mono"]) * 1000
    return {
        **result,
        "response_status": "applied" if applied else "unapplied_after_episode",
        "received_mono": now,
        "received_frame": frame,
        "capture_to_receive_ms": delay_ms,
        "applied_mono": now if applied else None,
        "applied_frame": frame if applied else None,
        "end_to_end_ms": delay_ms if applied else None,
        "observation_age_frames": frame - result["observed_frame"],
    }


def wait_ready(worker, responses, timeout=1500):
    """Bound load time while detecting a process killed before it can report an error."""
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        try:
            return responses.get(
                timeout=min(0.5, max(0, deadline - time.perf_counter()))
            )
        except queue.Empty:
            if not worker.is_alive():
                raise RuntimeError(
                    "Clef inference worker exited during model loading"
                ) from None
    raise TimeoutError("Clef model loading exceeded its readiness deadline")


def model_worker(requests, responses, warmup, smoke, outdir):
    try:
        if smoke:
            responses.put(
                {"kind": "ready", "model": "TEST FIXTURE, NOT CLEF", "smoke": True}
            )
            while True:
                req = requests.get()
                if req is None:
                    break
                begun = time.perf_counter()
                time.sleep(0.4)
                # Deliberately slow fixed action used solely to test non-blocking loop.
                probs = {a: float(a == "right_run_jump") for a in ACTIONS}
                responses.put(
                    {
                        **public_request(req),
                        "kind": "decision",
                        "action": "right_run_jump",
                        "probabilities": probs,
                        "model_ms": (time.perf_counter() - begun) * 1000,
                        "worker_received_mono": begun,
                        "worker_finished_mono": time.perf_counter(),
                        "input_tokens": 0,
                        "smoke": True,
                    }
                )
            return
        os.environ.update(
            HF_HUB_DISABLE_TELEMETRY="1",
            TOKENIZERS_PARALLELISM="false",
            HF_HUB_DISABLE_PROGRESS_BARS="1",
        )
        import torch

        torch.set_num_threads(1)
        from huggingface_hub import snapshot_download

        if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError("Approved L4 CUDA BF16 required; CPU fallback disabled")
        gpu = torch.cuda.get_device_name()
        if "L4" not in gpu:
            raise RuntimeError("Unexpected GPU: " + gpu)
        start = time.perf_counter()
        path = snapshot_download(MODEL, revision=REVISION)
        code_hash = hashlib.sha256(
            (Path(path) / "joint_schema_model.py").read_bytes()
        ).hexdigest()
        if code_hash != CODE_SHA:
            raise RuntimeError("Unreviewed model code hash")
        sys.path.insert(0, path)
        from joint_schema_model import (
            collate_records,
            encode_record,
            load_release_model,
        )

        model, processor = load_release_model(
            path, device="cuda", dtype=torch.bfloat16, attn_implementation="sdpa"
        )
        torch.manual_seed(0)

        def infer(req):
            received = time.perf_counter()
            from PIL import Image

            images = [
                Image.frombytes("RGB", tuple(f["size"]), f["rgb"])
                for f in req["images"]
            ]
            paths = []
            for metadata, im in zip(req["state"]["frames"], images):
                fp = (
                    Path(outdir)
                    / "observations"
                    / f"episode-{req['episode']:02d}-frame-{metadata['frame_id']:06d}.png"
                )
                fp.parent.mkdir(exist_ok=True)
                if not fp.exists():
                    im.save(fp)
                paths.append(
                    {
                        "path": str(fp.relative_to(outdir)),
                        "sha256": hashlib.sha256(fp.read_bytes()).hexdigest(),
                        **metadata,
                    }
                )
            record = {
                "id": str(req["request_id"]),
                "state": req["state"],
                "images": images,
                "questions": QUESTIONS,
            }
            enc = encode_record(
                processor.tokenizer, record, processor=processor, max_length=1000000
            )
            if len(enc.input_ids) > 2048:
                raise RuntimeError("Input exceeds reviewed 2048-token budget")
            pad = processor.tokenizer.pad_token_id
            if pad is None:
                pad = processor.tokenizer.eos_token_id
            batch = collate_records([enc], pad, torch.device("cuda"))
            torch.cuda.synchronize()
            begin = time.perf_counter()
            with torch.inference_mode():
                logits = model(batch)[0]
            torch.cuda.synchronize()
            end = time.perf_counter()
            probs = dict(
                zip(enc.questions[0].option_ids, logits[0].float().softmax(-1).tolist())
            )
            if (
                set(probs) != set(ACTIONS)
                or not all(math.isfinite(p) and 0 <= p <= 1 for p in probs.values())
                or abs(sum(probs.values()) - 1) > 1e-5
            ):
                raise RuntimeError("Invalid output probabilities")
            return {
                **public_request(req),
                "kind": "decision",
                "action": max(probs, key=probs.get),
                "probabilities": probs,
                "model_ms": (end - begin) * 1000,
                "worker_received_mono": received,
                "worker_finished_mono": time.perf_counter(),
                "input_tokens": len(enc.input_ids),
                "input_frames": paths,
                "smoke": False,
            }

        infer(warmup)
        env = {
            "model": MODEL,
            "revision": REVISION,
            "source_sha256": code_hash,
            "gpu": gpu,
            "precision": "BF16",
            "attn_implementation": "sdpa",
            "setup_and_warmup_seconds": time.perf_counter() - start,
            "torch": torch.__version__,
            "transformers": importlib.metadata.version("transformers"),
            "allocated_after_load_bytes": torch.cuda.memory_allocated(),
            "observation_mode": "rendered game viewport pixels only; 2 most recent decision frames; no engine telemetry",
            "questions": QUESTIONS,
            "max_input_tokens": 2048,
        }
        save(Path(outdir) / "model-environment.json", env)
        responses.put({"kind": "ready", **env})
        while True:
            req = requests.get()
            if req is None:
                break
            responses.put(infer(req))
    except BaseException as e:  # noqa: BLE001 - child-process boundary; propagate failure
        responses.put(
            {
                "kind": "error",
                "error": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
            }
        )


class TimestampVideo:
    """Records only captured frames, preserving monotonic capture timestamps as MP4 PTS."""

    def __init__(self, path, width, height):
        self.path = str(path)
        self.width = width
        self.height = height
        self.frames = queue.Queue(maxsize=8)
        self.dropped = 0
        self.error = None
        self.encoded = 0
        self.capture_times = []
        self.close_attempted = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def capture(self, surface, at):
        import pygame

        raw = pygame.image.tobytes(surface, "RGB")
        try:
            self.frames.put_nowait((at, raw))
        except queue.Full:
            self.dropped += 1

    def _run(self):
        try:
            import av
            import numpy as np

            with av.open(self.path, "w") as container:
                stream = container.add_stream("libx264", rate=60)
                stream.width = self.width
                stream.height = self.height
                stream.pix_fmt = "yuv420p"
                stream.time_base = Fraction(1, 1000000)
                stream.codec_context.time_base = Fraction(1, 1000000)
                stream.codec_context.options = {
                    "preset": "ultrafast",
                    "crf": "22",
                    "tune": "zerolatency",
                }
                stream.codec_context.thread_count = 1
                first = None
                previous = -1
                while True:
                    item = self.frames.get()
                    if item is None:
                        break
                    at, raw = item
                    if first is None:
                        first = at
                    frame = av.VideoFrame.from_ndarray(
                        np.frombuffer(raw, dtype=np.uint8).reshape(
                            self.height, self.width, 3
                        ),
                        format="rgb24",
                    )
                    frame.pts = max(previous + 1, round((at - first) * 1000000))
                    previous = frame.pts
                    frame.time_base = Fraction(1, 1000000)
                    for packet in stream.encode(frame):
                        container.mux(packet)
                    self.capture_times.append(at)
                    self.encoded += 1
                for packet in stream.encode():
                    container.mux(packet)
        except BaseException:  # noqa: BLE001 - recording thread boundary; propagate failure
            self.error = traceback.format_exc()

    def close(self, timeout=20):
        self.close_attempted = True
        deadline = time.perf_counter() + timeout
        while self.thread.is_alive() and time.perf_counter() < deadline:
            try:
                self.frames.put(
                    None, timeout=min(0.2, max(0, deadline - time.perf_counter()))
                )
                break
            except queue.Full:
                pass
        self.thread.join(timeout=max(0, deadline - time.perf_counter()))
        if self.thread.is_alive():
            raise RuntimeError("Video writer did not exit")
        if self.error:
            raise RuntimeError(self.error)
        gaps = [
            (b - a) * 1000 for a, b in zip(self.capture_times, self.capture_times[1:])
        ]
        return {
            "encoded_frames": self.encoded,
            "dropped_frames": self.dropped,
            "max_capture_gap_ms": max(gaps, default=0),
            "timing": "actual capture timestamps, no fabricated frames",
            "first_capture_mono": self.capture_times[0] if self.capture_times else None,
            "last_capture_mono": self.capture_times[-1] if self.capture_times else None,
        }


def draw_hud(
    screen,
    font,
    small,
    obs,
    action,
    decision,
    elapsed,
    frame,
    lag,
    episode,
    smoke,
    status,
):
    import pygame

    x = 900
    pygame.draw.rect(screen, (15, 18, 28), (880, 0, 400, 720))
    label = "TEST FIXTURE / NOT CLEF" if smoke else "CLEF-FLASH 9B / LIVE"
    lines = [
        label,
        "JevDash / real-time trial",
        f"Episode {episode}  |  {status}",
        f"Wall clock: {elapsed:7.3f} s",
        f"Physics: {frame / 60:7.3f} s  /  60 Hz",
        f"Loop lateness: {lag * 1000:6.1f} ms",
        f"Action: {action}",
        f"Progress: {obs.episode.progress_pixels:.1f} px",
        f"Score: {obs.episode.score}   Coins: {obs.episode.coins}",
        f"End-to-end: {decision.get('end_to_end_ms', 0):.1f} ms",
        f"Model: {decision.get('model_ms', 0):.1f} ms",
        "Screen pixels only (2 frames)",
        "No mock fallback / no reflexes",
    ]
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, (226, 234, 245)), (x, 20 + 27 * i))
    y = 382
    for a in ACTIONS:
        p = decision.get("probabilities", {}).get(a, 0)
        col = (56, 189, 248) if a == action else (125, 145, 170)
        screen.blit(small.render(f"{a:16s} {p:5.1%}", True, col), (x, y))
        y += 19
        pygame.draw.rect(screen, col, (x, y, max(1, int(p * 335)), 5))
        y += 10
    screen.blit(
        small.render("AI inference does not stop the game", True, (125, 211, 160)),
        (x, 604),
    )
    screen.blit(
        small.render("Video PTS = real capture timestamps", True, (125, 211, 160)),
        (x, 625),
    )
    screen.blit(
        small.render("Model setup/warmup excluded", True, (148, 163, 184)), (x, 646)
    )
    screen.blit(
        small.render("Original game physics and Level 1", True, (148, 163, 184)),
        (x, 667),
    )


def run_episode(
    args,
    episode,
    reqs,
    resps,
    pending,
    next_id,
    output,
    worker=None,
    pending_since=None,
):
    import pygame

    from jev_platformer.engine.entities import Player
    from jev_platformer.engine.world import Level
    from jev_platformer.telemetry.extractor import TelemetryExtractor
    from jev_platformer.ui.renderer import GameRenderer

    level = Level(1)
    player = Player(*level.start_pos)
    screen = pygame.display.set_mode((1280, 720))
    renderer = GameRenderer(screen)
    font = pygame.font.SysFont("DejaVu Sans Mono", 16)
    small = pygame.font.SysFont("DejaVu Sans Mono", 13)
    video = TimestampVideo(output / f"episode-{episode:02d}.mp4", 1280, 720)
    trace = (output / f"episode-{episode:02d}-frames.jsonl").open("w")
    logs = (output / f"episode-{episode:02d}-decisions.jsonl").open("w")
    action = "noop"
    decision = {}
    frame = 0
    stalls = []
    decisions = []
    updates = 0
    terminal = None
    start = time.perf_counter()
    epoch = time.time()
    end = None
    terminal_at = None
    previous_image = None
    previous_metadata = None
    try:
        while True:
            planned = start + frame / 60
            remaining = planned - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
            now = time.perf_counter()
            elapsed = now - start
            lag = max(0, now - planned)
            stalls.append(lag)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminal = "cancelled"
                    terminal_at = now
            while True:
                try:
                    result = resps.get_nowait()
                except queue.Empty:
                    break
                if result["kind"] == "error":
                    raise RuntimeError(result)
                if result["kind"] != "decision":
                    continue
                pending = False
                pending_since = None
                if result["episode"] != episode:
                    logs.write(json.dumps({"discarded_old_episode": result}) + "\n")
                    continue
                if terminal is None and now - result["observed_mono"] > 10:
                    raise TimeoutError(
                        "Clef decision exceeded 10 real seconds; stale action was not applied"
                    )
                result = annotate_response(result, now, frame, terminal)
                logs.write(json.dumps(result) + "\n")
                logs.flush()
                if terminal is None:
                    decision = result
                    action = result["action"]
                    decisions.append(result)
            if terminal is None:
                if worker is not None and not worker.is_alive():
                    raise RuntimeError(
                        "Clef inference worker exited unexpectedly; no fallback action applied"
                    )
                if pending and pending_since is not None and now - pending_since > 10:
                    raise TimeoutError(
                        "Clef decision exceeded 10 real seconds; aborting without a mock fallback"
                    )
            obs = TelemetryExtractor.extract(player, level)
            if terminal is None:
                # Exact world update sequence from upstream CLI, with original Player/Enemy methods.
                player.apply_action(action)
                player.update_physics(level.tiles)
                for enemy in level.enemies:
                    enemy.update(level.tiles)
                    if enemy.alive and player.rect.colliderect(enemy.rect):
                        if player.y + player.height <= enemy.y + enemy.height * 0.65:
                            enemy.stomp()
                            player.vy = -11.0
                            player.score += 100
                        else:
                            player.is_dead = True
                for coin in level.coins:
                    if not coin.collected and player.rect.colliderect(coin.rect):
                        coin.collected = True
                        player.coins += 1
                        player.score += 50
                if level.goal and player.rect.colliderect(level.goal.rect):
                    player.has_won = True
                updates += 1
                if player.has_won:
                    terminal = "goal"
                elif player.is_dead:
                    terminal = "died"
                elif elapsed >= args.seconds:
                    terminal = "time_limit"
                if terminal:
                    terminal_at = time.perf_counter()
                    end = terminal_at
            obs = TelemetryExtractor.extract(player, level)
            renderer.render(player, level)
            draw_hud(
                screen,
                font,
                small,
                obs,
                action,
                decision,
                elapsed,
                updates,
                lag,
                episode,
                args.smoke,
                terminal or "RUNNING",
            )
            pygame.display.flip()
            captured = time.perf_counter()
            video.capture(screen, captured)
            if terminal is None and not pending:
                # Crop pixels from this actual displayed frame BEFORE the diagnostic sidebar.
                viewport = pygame.transform.smoothscale(
                    screen.subsurface((0, 0, 880, 720)), (704, 576)
                )
                image = {
                    "size": [704, 576],
                    "rgb": pygame.image.tobytes(viewport, "RGB"),
                }
                metadata = {
                    "frame_id": frame,
                    "captured_wall_seconds": captured - start,
                }
                images = ([previous_image] if previous_image else []) + [image]
                metadata_list = ([previous_metadata] if previous_metadata else []) + [
                    metadata
                ]
                payload = {
                    "request_id": next_id,
                    "episode": episode,
                    "observed_frame": frame,
                    "observed_mono": captured,
                    "state": vision_state(metadata_list, action),
                    "images": images,
                }
                reqs.put_nowait(payload)
                pending = True
                pending_since = captured
                next_id += 1
                previous_image = image
                previous_metadata = metadata
            trace.write(
                json.dumps(
                    {
                        "frame": frame,
                        "physics_updates": updates,
                        "elapsed_s": captured - start,
                        "capture_mono": captured,
                        "scheduled_mono": planned,
                        "loop_lag_ms": lag * 1000,
                        "action": action,
                        "decision_id": decision.get("request_id"),
                        "player": obs.player.model_dump(),
                        "episode": obs.episode.model_dump(),
                        "status": terminal or "running",
                    }
                )
                + "\n"
            )
            frame += 1
            if terminal and time.perf_counter() - terminal_at >= 1.0:
                break
        stats = video.close()
    finally:
        trace.close()
        logs.close()
        if video.thread.is_alive() and not video.close_attempted:
            video.close()
    elapsed = (end or time.perf_counter()) - start
    stats.update(
        episode=episode,
        result=terminal,
        wall_seconds=elapsed,
        physics_updates=updates,
        physics_seconds=updates / 60,
        physics_wall_ratio=updates / 60 / elapsed,
        score=player.score,
        coins=player.coins,
        progress_pixels=player.max_x,
        net_progress_pixels=player.max_x - level.start_pos[0],
        goal_x=level.goal.x,
        decisions_applied=len(decisions),
        start_epoch=epoch,
        max_loop_lag_ms=max(stalls) * 1000,
        model_ms_median=statistics.median([d["model_ms"] for d in decisions])
        if decisions
        else None,
        end_to_end_ms_median=statistics.median([d["end_to_end_ms"] for d in decisions])
        if decisions
        else None,
        end_to_end_ms_p95=sorted([d["end_to_end_ms"] for d in decisions])[
            min(len(decisions) - 1, math.ceil(len(decisions) * 0.95) - 1)
        ]
        if decisions
        else None,
        action_counts={a: sum(d["action"] == a for d in decisions) for a in ACTIONS},
        smoke=args.smoke,
    )
    stats["realtime_validation_pass"] = (
        abs(stats["physics_wall_ratio"] - 1) <= 0.05
        and stats["max_loop_lag_ms"] < 100
        and stats["dropped_frames"] == 0
    )
    save(output / f"episode-{episode:02d}-summary.json", stats)
    print(json.dumps({"stage": "episode_complete", **stats}), flush=True)
    return stats, pending, next_id, pending_since


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--episodes", type=int, default=3)
    p.add_argument("--seconds", type=float, default=60)
    p.add_argument("--smoke", action="store_true")
    a = p.parse_args(argv)
    if not 1 <= a.episodes <= 3 or not 0 < a.seconds <= 60:
        raise ValueError("Trial bounds exceeded")
    required = (
        ("av", "numpy")
        if a.smoke
        else ("av", "numpy", "PIL", "torch", "transformers", "huggingface_hub")
    )
    import importlib.util

    missing = [name for name in required if importlib.util.find_spec(name) is None]
    if missing:
        extra = "vision-recording" if a.smoke else "clef"
        raise RuntimeError(
            f"Missing optional dependencies {missing}. Install jevdash[{extra}]."
        )
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError(
            "Output directory must be empty: choose a fresh --out path to preserve prior evidence"
        )
    # A window on desktop; direct offscreen game-surface capture on display-less Colab.
    if (
        sys.platform.startswith("linux")
        and not os.environ.get("DISPLAY")
        and not os.environ.get("WAYLAND_DISPLAY")
    ):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame

    from jev_platformer.engine.entities import Player
    from jev_platformer.engine.world import Level

    pygame.init()
    level = Level(1)
    player = Player(*level.start_pos)
    from jev_platformer.ui.renderer import GameRenderer

    warm_screen = pygame.display.set_mode((1280, 720))
    GameRenderer(warm_screen).render(player, level)
    warm_image = pygame.transform.smoothscale(
        warm_screen.subsurface((0, 0, 880, 720)), (704, 576)
    )
    warmup = {
        "request_id": "warmup",
        "episode": 0,
        "observed_frame": 0,
        "observed_mono": time.perf_counter(),
        "state": vision_state([{"frame_id": 0, "captured_wall_seconds": 0}], "noop"),
        "images": [
            {"size": [704, 576], "rgb": pygame.image.tobytes(warm_image, "RGB")}
        ],
    }
    ctx = mp.get_context("spawn")
    reqs = ctx.Queue(1)
    resps = ctx.Queue(4)
    worker = ctx.Process(
        target=model_worker, args=(reqs, resps, warmup, a.smoke, str(out)), daemon=True
    )
    worker.start()
    print(json.dumps({"stage": "loading_model", "smoke": a.smoke}), flush=True)
    try:
        ready = wait_ready(worker, resps)
        if ready["kind"] != "ready":
            raise RuntimeError(ready)
        save(out / "ready.json", ready)
        print(json.dumps({"stage": "ready", "smoke": a.smoke}), flush=True)
        results = []
        pending = False
        pending_since = None
        next_id = 1
        for episode in range(1, a.episodes + 1):
            r, pending, next_id, pending_since = run_episode(
                a, episode, reqs, resps, pending, next_id, out, worker, pending_since
            )
            results.append(r)
            if r["result"] == "cancelled":
                break
        save(
            out / "summary.json",
            {
                "game_commit": GAME_COMMIT,
                "model": MODEL if not a.smoke else "TEST FIXTURE",
                "episodes": results,
                "limits": {"episodes": a.episodes, "seconds_per_episode": a.seconds},
                "semantics": {
                    "physics": "upstream fixed 60 Hz updates scheduled against monotonic wall time",
                    "no_model_wait_in_physics": True,
                    "controller_reflexes": False,
                    "mock_fallback": False,
                    "game_engine_changes": False,
                    "video": "actual rendered frames with capture-time PTS",
                    "terminal_display_seconds": 1,
                    "audio": "none; upstream game contains no audio",
                    "seed": "not applicable; Level(1) is fixed geometry, no randomized level generator",
                    "observation": "screen pixels only; 704x576 viewport from actual 880x720 game render; previous and current decision images; no engine telemetry",
                },
            },
        )
    finally:
        try:
            reqs.put(None, timeout=1)
        except queue.Full:
            pass
        worker.join(timeout=5)
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=5)
        reqs.cancel_join_thread()
        resps.cancel_join_thread()
        reqs.close()
        resps.close()
        pygame.quit()


if __name__ == "__main__":
    main()

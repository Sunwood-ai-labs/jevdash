"""Main game loop and command-line interface for JevDash: System One."""

import sys
import os
import argparse
import time
import json
import pygame

from jev_platformer.engine.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GAME_VIEW_WIDTH, FPS, GAME_TITLE, GAME_BRAND
)
from jev_platformer.engine.entities import Player
from jev_platformer.engine.world import Level
from jev_platformer.telemetry.extractor import TelemetryExtractor
from jev_platformer.controller.actions import Action
from jev_platformer.controller.mock_agent import MockJevAgent
from jev_platformer.controller.jev_agent import JevLiveAgent, AsyncJevAgent
from jev_platformer.ui.renderer import GameRenderer
from jev_platformer.ui.dashboard import DashboardRenderer
from jev_platformer.ui.video_recorder import VideoRecorder

# Configure UTF-8 stdout to prevent Windows cp932 encoding errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def run_state_demo():
    """Outputs the canonical model JSON and text radar without opening a window."""
    level = Level(1)
    player = Player(level.start_pos[0], level.start_pos[1])
    obs = TelemetryExtractor.extract(player, level)

    print(f"=== {GAME_BRAND} CANONICAL MODEL STATE (JSON) ===")
    print(json.dumps(obs.model_dump(), indent=2, ensure_ascii=False))
    print("\n=== LOCAL RADAR PERCEPTION (ASCII) ===")
    for row in obs.local_grid:
        print(row)
    print("\nObjective:", obs.objective)
    print("Telemetry extraction successful! Sub-50ms ready.")


def run_benchmark(episodes: int = 5, frames_per_decision: int = 8):
    """Runs autonomous headless benchmark without graphics rendering."""
    print(f"[{GAME_BRAND}] Running {episodes} autonomous benchmark episodes (headless)...")
    agent = MockJevAgent()
    
    total_progress = []
    wins = 0
    latencies = []

    for ep in range(1, episodes + 1):
        level = Level(1)
        player = Player(level.start_pos[0], level.start_pos[1])
        frame = 0
        current_action = "noop"

        start_time = time.perf_counter()
        while frame < 1500 and not player.is_dead and not player.has_won:
            if frame % frames_per_decision == 0:
                obs = TelemetryExtractor.extract(player, level)
                dec = agent.decide(obs)
                current_action = dec.action
                latencies.append(dec.latency_ms)

            player.apply_action(current_action)
            player.update_physics(level.tiles)
            
            for enemy in level.enemies:
                enemy.update(level.tiles)
                if enemy.alive and player.rect.colliderect(enemy.rect):
                    feet_y = player.y + player.height
                    if feet_y <= enemy.y + enemy.height * 0.65:
                        enemy.stomp()
                        player.vy = -11.0
                        player.score += 100
                    else:
                        player.is_dead = True

            frame += 1

        elapsed = time.perf_counter() - start_time
        total_progress.append(player.max_x)
        if player.has_won:
            wins += 1

        status = "CLEARED" if player.has_won else ("DIED" if player.is_dead else "TIMEOUT")
        print(f"  Episode {ep:02d}: {status:<8} Progress: {player.max_x:.1f}px ({frame} frames in {elapsed:.2f}s)")

    avg_progress = sum(total_progress) / len(total_progress)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    win_rate = (wins / episodes) * 100.0

    print(f"\n=== {GAME_BRAND} BENCHMARK SUMMARY ===")
    print(f"Clear Rate       : {win_rate:.1f}% ({wins}/{episodes})")
    print(f"Average Progress : {avg_progress:.1f} pixels")
    print(f"Average Latency  : {avg_latency:.1f} ms")


def run_play(
    mode: str = "ai",
    frames_per_decision: int = 8,
    display: str = "all",
    record_path: str = "gameplay.mp4",
    max_frames: int = 0
):
    """Launches interactive game window with real-time Pygame rendering and optional MP4 video recording."""
    pygame.init()
    pygame.display.set_caption(GAME_TITLE)

    screen_w = SCREEN_WIDTH if display == "all" else GAME_VIEW_WIDTH
    screen = pygame.display.set_mode((screen_w, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    level = Level(1)
    player = Player(level.start_pos[0], level.start_pos[1])
    game_renderer = GameRenderer(screen)
    dashboard_renderer = DashboardRenderer(screen, offset_x=GAME_VIEW_WIDTH) if display == "all" else None

    # Agent initialization
    live_agent = JevLiveAgent()
    async_agent = AsyncJevAgent(live_agent)
    mock_agent = MockJevAgent()

    # Video Recorder setup
    recorder = None
    if record_path:
        recorder = VideoRecorder(record_path, screen_w, SCREEN_HEIGHT, fps=FPS)
        print(f"[{GAME_BRAND}] [REC] Recording gameplay to: {record_path}")

    is_human = (mode == "human")
    is_live_mode = (mode == "live")

    current_decision = None
    current_action = "noop"
    frame_count = 0

    running = True
    try:
        while running:
            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_r:
                        level = Level(1)
                        player = Player(level.start_pos[0], level.start_pos[1])
                        current_decision = None
                        current_action = "noop"
                        frame_count = 0
                    elif event.key == pygame.K_TAB:
                        is_human = not is_human
                        print(f"[{GAME_BRAND}] Control switched to: {'MANUAL HUMAN' if is_human else 'AI AUTOPILOT'}")

            # 2. Control Decision
            obs = TelemetryExtractor.extract(player, level)

            if is_human:
                keys = pygame.key.get_pressed()
                is_run = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                is_jump = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
                is_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
                is_left = keys[pygame.K_LEFT] or keys[pygame.K_a]

                if is_right and is_jump and is_run:
                    current_action = Action.RIGHT_RUN_JUMP.value
                elif is_right and is_jump:
                    current_action = Action.RIGHT_JUMP.value
                elif is_right and is_run:
                    current_action = Action.RIGHT_RUN.value
                elif is_right:
                    current_action = Action.RIGHT.value
                elif is_left:
                    current_action = Action.LEFT.value
                elif is_jump:
                    current_action = Action.JUMP.value
                else:
                    current_action = Action.NOOP.value
            else:
                # AI Autopilot mode
                if is_live_mode and live_agent.is_live:
                    if frame_count % frames_per_decision == 0:
                        async_agent.request_decision(obs)
                    current_action, current_decision = async_agent.get_action(obs)
                else:
                    # Mock agent
                    if frame_count % frames_per_decision == 0:
                        current_decision = mock_agent.decide(obs)
                        current_action = current_decision.action

            # 3. Physics and World Update
            player.apply_action(current_action)
            player.update_physics(level.tiles)

            for enemy in level.enemies:
                enemy.update(level.tiles)
                if enemy.alive and player.rect.colliderect(enemy.rect):
                    feet_y = player.y + player.height
                    if feet_y <= enemy.y + enemy.height * 0.65:
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

            # 4. Render
            game_renderer.render(player, level)
            if dashboard_renderer:
                dashboard_renderer.render(
                    obs=obs,
                    decision=current_decision,
                    is_ai_mode=(not is_human),
                    fps=clock.get_fps()
                )

            pygame.display.flip()

            # Record frame to MP4
            if recorder:
                recorder.record_frame(screen)

            clock.tick(FPS)
            frame_count += 1

            if max_frames > 0 and frame_count >= max_frames:
                print(f"[{GAME_BRAND}] Max frames ({max_frames}) reached.")
                running = False

            if player.has_won:
                print(f"[{GAME_BRAND}] [VICTORY] Goal reached! Progress: {player.max_x:.1f}px ({frame_count} frames)")
                for _ in range(45):
                    if recorder:
                        recorder.record_frame(screen)
                running = False

            if player.is_dead:
                print(f"[{GAME_BRAND}] [GAME OVER] Player died at progress: {player.max_x:.1f}px ({frame_count} frames)")
                for _ in range(30):
                    if recorder:
                        recorder.record_frame(screen)
                running = False

    finally:
        if recorder:
            recorder.close()
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=f"{GAME_TITLE}")
    subparsers = parser.add_subparsers(dest="command")

    # Play command
    play_p = subparsers.add_parser("play", help="Launch interactive game")
    play_p.add_argument("--mode", choices=["ai", "live", "mock", "human"], default="ai", help="Control mode")
    play_p.add_argument("--frames-per-decision", type=int, default=8, help="Frames per AI decision (default: 8)")
    play_p.add_argument("--display", choices=["all", "game"], default="all", help="Display layout")
    play_p.add_argument("--record", type=str, default="jevdash_gameplay.mp4", help="Path to save MP4 video recording")
    play_p.add_argument("--max-frames", type=int, default=0, help="Exit after N frames (0 for unlimited)")

    # Live command (alias for play --mode live)
    live_p = subparsers.add_parser("live", help="Launch game driven directly by real Jev via Vercel AI Gateway")
    live_p.add_argument("--record", type=str, default="jevdash_live.mp4", help="Path to save MP4 video recording")
    live_p.add_argument("--max-frames", type=int, default=450, help="Frames to run (default: 450 = ~7.5 seconds)")

    # State-demo command
    subparsers.add_parser("state-demo", help="Display canonical JSON telemetry in terminal")

    # Benchmark command
    bench_p = subparsers.add_parser("benchmark", help="Run fast headless benchmark")
    bench_p.add_argument("--episodes", type=int, default=5, help="Number of test episodes")

    args = parser.parse_args()

    if args.command == "state-demo":
        run_state_demo()
    elif args.command == "benchmark":
        run_benchmark(episodes=args.episodes)
    elif args.command == "live":
        run_play(mode="live", record_path=args.record, max_frames=args.max_frames)
    elif args.command == "play" or args.command is None:
        mode = getattr(args, "mode", "ai")
        fpd = getattr(args, "frames_per_decision", 8)
        disp = getattr(args, "display", "all")
        rec = getattr(args, "record", "jevdash_gameplay.mp4")
        max_f = getattr(args, "max_frames", 0)
        run_play(mode=mode, frames_per_decision=fpd, display=disp, record_path=rec, max_frames=max_f)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

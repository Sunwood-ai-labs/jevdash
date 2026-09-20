"""Extracts high-level, structured telemetry from raw game objects for Jev AI."""

import math
from typing import List, Optional
import pygame

from jev_platformer.engine.constants import TILE_SIZE
from jev_platformer.engine.entities import Player, Enemy, Goal
from jev_platformer.engine.world import Level
from jev_platformer.telemetry.models import (
    PlayerTelemetry, EnemyObservation, HazardTelemetry,
    TerrainTelemetry, EpisodeTelemetry, JevObservation
)


class TelemetryExtractor:
    """Translates Pygame level and actor state into JevObservation JSON."""

    @staticmethod
    def extract(player: Player, level: Level) -> JevObservation:
        # 1. Player Telemetry
        player_tel = PlayerTelemetry(
            x=round(player.x, 1),
            y=round(player.y, 1),
            vx=round(player.vx, 2),
            vy=round(player.vy, 2),
            grounded=player.grounded,
            jumping=player.jumping,
            airborne_frames=player.airborne_frames,
            running=player.running,
        )

        # 2. Hazard Telemetry (Enemies ahead)
        player_col = int(player.x // TILE_SIZE)
        player_row = int(player.y // TILE_SIZE)
        
        nearest_enemy_obs: Optional[EnemyObservation] = None
        min_dist = float("inf")

        for e in level.enemies:
            if not e.alive:
                continue
            dx = e.x - player.x
            # Consider enemies ahead within 350 pixels
            if 0 < dx < 350:
                dy = e.y - player.y
                if dx < min_dist:
                    min_dist = dx
                    rel_vx = player.vx - e.vx
                    contact_frames = None
                    if rel_vx > 0:
                        contact_frames = int(dx / rel_vx)
                    
                    nearest_enemy_obs = EnemyObservation(
                        kind=e.kind,
                        distance_pixels=round(dx, 1),
                        vertical_offset_pixels=round(dy, 1),
                        relative_velocity_x=round(rel_vx, 2),
                        estimated_contact_frames=contact_frames,
                    )

        enemy_ahead = nearest_enemy_obs is not None
        jump_must_start_now = False
        in_danger_zone = False

        if nearest_enemy_obs is not None:
            dist = nearest_enemy_obs.distance_pixels
            if dist < 120:
                in_danger_zone = True
            # If enemy is close (30..80px) and player is grounded, jumping now clears it
            if 25 <= dist <= 85 and player.grounded:
                jump_must_start_now = True

        hazard_tel = HazardTelemetry(
            enemy_ahead=enemy_ahead,
            nearest_enemy=nearest_enemy_obs,
            jump_must_start_now=jump_must_start_now,
            in_danger_zone=in_danger_zone,
        )

        # 3. Terrain Telemetry (Gaps and Obstacles ahead)
        ground_row = level.height_tiles - 4
        clear_tiles = 0
        gap_ahead = False
        gap_dist: Optional[float] = None
        gap_width = 0

        obstacle_ahead = False
        obstacle_dist: Optional[float] = None
        obstacle_height = 0

        # Scan 12 tiles forward
        for dc in range(1, 13):
            scan_col = player_col + dc
            is_ground = level.is_tile_solid(scan_col, ground_row)
            
            # Check for Gap (Pit)
            if not is_ground:
                if not gap_ahead:
                    gap_ahead = True
                    gap_dist = float(dc)
                gap_width += 1
            else:
                if gap_ahead:
                    break  # Found other side of gap
                clear_tiles += 1

            # Check for Obstacle / Pipe blocking the path
            # An obstacle is solid tiles above the ground line
            h_count = 0
            for r in range(ground_row - 4, ground_row):
                if level.is_tile_solid(scan_col, r):
                    h_count += 1
            
            if h_count > 0 and not obstacle_ahead:
                obstacle_ahead = True
                obstacle_dist = float(dc)
                obstacle_height = h_count

        terrain_tel = TerrainTelemetry(
            obstacle_ahead=obstacle_ahead,
            obstacle_distance_tiles=obstacle_dist,
            obstacle_height_tiles=obstacle_height,
            gap_ahead=gap_ahead,
            gap_distance_tiles=gap_dist,
            gap_width_tiles=gap_width,
            clear_forward_tiles=clear_tiles,
        )

        # 4. Episode Telemetry
        goal_dist = max(0.0, level.goal.x - player.x)
        has_won = player.rect.colliderect(level.goal.rect)
        if has_won:
            player.has_won = True

        episode_tel = EpisodeTelemetry(
            score=player.score,
            coins=player.coins,
            lives=player.lives,
            progress_pixels=round(player.max_x, 1),
            goal_distance_pixels=round(goal_dist, 1),
            stalled_frames=player.stalled_frames,
            is_dead=player.is_dead,
            has_won=player.has_won,
        )

        # 5. Local Radar Grid (7 rows x 11 cols around player)
        grid_lines = []
        center_col = player_col
        center_row = player_row

        for r_offset in range(-3, 4):
            r = center_row + r_offset
            row_chars = []
            for c_offset in range(-2, 9):
                c = center_col + c_offset
                if c_offset == 0 and r_offset == 0:
                    row_chars.append("P")  # Player
                else:
                    # Check enemy presence in this tile
                    tile_has_enemy = False
                    for e in level.enemies:
                        if e.alive and int(e.x // TILE_SIZE) == c and int(e.y // TILE_SIZE) == r:
                            row_chars.append("E")
                            tile_has_enemy = True
                            break
                    if not tile_has_enemy:
                        if level.is_tile_solid(c, r):
                            row_chars.append("#")
                        else:
                            row_chars.append(".")
            grid_lines.append("".join(row_chars))

        return JevObservation(
            player=player_tel,
            hazard=hazard_tel,
            terrain=terrain_tel,
            episode=episode_tel,
            local_grid=grid_lines,
        )

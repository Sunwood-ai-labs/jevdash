"""Pydantic schemas for Jev AI telemetry inputs."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PlayerTelemetry(BaseModel):
    x: float = Field(..., description="Player horizontal position in pixels")
    y: float = Field(..., description="Player vertical position in pixels")
    vx: float = Field(..., description="Horizontal velocity in px/frame")
    vy: float = Field(..., description="Vertical velocity in px/frame")
    grounded: bool = Field(..., description="True if player is on ground")
    jumping: bool = Field(..., description="True if currently ascending in jump")
    airborne_frames: int = Field(..., description="Number of frames continuously airborne")
    running: bool = Field(..., description="True if running dash speed")


class EnemyObservation(BaseModel):
    kind: str = Field(..., description="Enemy type (goomba, patrol)")
    distance_pixels: float = Field(..., description="Horizontal distance from player front in pixels")
    vertical_offset_pixels: float = Field(..., description="Vertical difference from player in pixels")
    relative_velocity_x: float = Field(..., description="Relative horizontal approach speed")
    estimated_contact_frames: Optional[int] = Field(None, description="Frames until collision if neither jumps")


class HazardTelemetry(BaseModel):
    enemy_ahead: bool = Field(..., description="True if any active enemy is in forward view")
    nearest_enemy: Optional[EnemyObservation] = Field(None, description="Closest active enemy ahead")
    jump_must_start_now: bool = Field(..., description="True if player must take off this decision to clear hazard")
    in_danger_zone: bool = Field(..., description="True if within 120px of approaching enemy")


class TerrainTelemetry(BaseModel):
    obstacle_ahead: bool = Field(..., description="True if pipe/wall blocks forward path")
    obstacle_distance_tiles: Optional[float] = Field(None, description="Distance to upcoming obstacle in tiles")
    obstacle_height_tiles: int = Field(0, description="Height of obstacle in tiles")
    gap_ahead: bool = Field(..., description="True if a pit/gap lies ahead")
    gap_distance_tiles: Optional[float] = Field(None, description="Distance to edge of upcoming pit in tiles")
    gap_width_tiles: int = Field(0, description="Width of upcoming pit in tiles")
    clear_forward_tiles: int = Field(..., description="Tiles of safe flat ground immediately ahead")


class EpisodeTelemetry(BaseModel):
    score: int = Field(..., description="Current game score")
    coins: int = Field(..., description="Coins collected")
    lives: int = Field(..., description="Remaining lives")
    progress_pixels: float = Field(..., description="Current maximum horizontal progress")
    goal_distance_pixels: float = Field(..., description="Remaining distance to goal flag")
    stalled_frames: int = Field(..., description="Frames without forward progress")
    is_dead: bool = Field(..., description="True if dead")
    has_won: bool = Field(..., description="True if goal reached")


class JevObservation(BaseModel):
    """Canonical model-facing structured observation sent to TypeSafe Jev."""
    objective: str = "Reach the goal flag in Level 1-1 without dying."
    player: PlayerTelemetry
    hazard: HazardTelemetry
    terrain: TerrainTelemetry
    episode: EpisodeTelemetry
    local_grid: List[str] = Field(..., description="7x11 ASCII radar grid of immediate surroundings")

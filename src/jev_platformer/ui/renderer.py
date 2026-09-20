"""Game viewport renderer with smooth scrolling and cyber-minimalist graphics."""

import pygame
import math
from typing import List

from jev_platformer.engine.constants import (
    GAME_VIEW_WIDTH, GAME_VIEW_HEIGHT, TILE_SIZE,
    ENEMY_WIDTH, ENEMY_HEIGHT,
    COLOR_BG, COLOR_GRID, COLOR_GROUND, COLOR_GROUND_BORDER,
    COLOR_OBSTACLE, COLOR_PIPE, COLOR_PLATFORM,
    COLOR_PLAYER, COLOR_PLAYER_CORE, COLOR_ENEMY_GOOMBA,
    COLOR_COIN, COLOR_GOAL
)
from jev_platformer.engine.entities import Player, Enemy, Coin, Goal
from jev_platformer.engine.world import Level


class GameRenderer:
    """Renders the side-scrolling platformer world inside the left viewport."""

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.camera_x = 0.0
        self.font = pygame.font.SysFont("Consolas, Menlo, monospace", 14, bold=True)
        self.large_font = pygame.font.SysFont("Arial, sans-serif", 32, bold=True)

    def render(self, player: Player, level: Level):
        # 1. Update Camera (Smooth horizontal tracking)
        target_cam_x = player.x - GAME_VIEW_WIDTH * 0.35
        if target_cam_x < 0:
            target_cam_x = 0
        self.camera_x += (target_cam_x - self.camera_x) * 0.12

        # 2. Draw Background with Parallax grid
        self.surface.fill(COLOR_BG)
        
        # Parallax background grid lines
        grid_offset = int(self.camera_x * 0.25) % 64
        for x in range(-grid_offset, GAME_VIEW_WIDTH, 64):
            pygame.draw.line(self.surface, COLOR_GRID, (x, 0), (x, GAME_VIEW_HEIGHT), 1)
        for y in range(0, GAME_VIEW_HEIGHT, 64):
            pygame.draw.line(self.surface, COLOR_GRID, (0, y), (GAME_VIEW_WIDTH, y), 1)

        # 3. Draw Tiles
        cam_x_int = int(self.camera_x)
        for tile in level.tiles:
            # Frustum culling
            screen_x = tile.x - cam_x_int
            if -TILE_SIZE <= screen_x <= GAME_VIEW_WIDTH:
                col = tile.x // TILE_SIZE
                row = tile.y // TILE_SIZE
                tile_type = level.tile_types.get((col, row), "ground")
                
                rect_on_screen = pygame.Rect(screen_x, tile.y, tile.width, tile.height)
                
                if tile_type == "ground":
                    pygame.draw.rect(self.surface, COLOR_GROUND, rect_on_screen)
                    # Top luminous border
                    pygame.draw.line(
                        self.surface, COLOR_GROUND_BORDER,
                        (screen_x, tile.y), (screen_x + tile.width, tile.y), 2
                    )
                elif tile_type == "pipe":
                    pygame.draw.rect(self.surface, COLOR_PIPE, rect_on_screen, border_radius=4)
                    pygame.draw.rect(self.surface, (5, 150, 105), rect_on_screen, 2, border_radius=4)
                elif tile_type == "platform":
                    pygame.draw.rect(self.surface, COLOR_PLATFORM, rect_on_screen, border_radius=3)
                    pygame.draw.line(
                        self.surface, (165, 180, 252),
                        (screen_x, tile.y), (screen_x + tile.width, tile.y), 2
                    )
                else:
                    pygame.draw.rect(self.surface, COLOR_OBSTACLE, rect_on_screen)

        # 4. Draw Coins
        for coin in level.coins:
            if not coin.collected:
                cx = int(coin.x - cam_x_int + coin.width // 2)
                cy = int(coin.y + coin.height // 2)
                if -16 <= cx <= GAME_VIEW_WIDTH + 16:
                    pygame.draw.circle(self.surface, COLOR_COIN, (cx, cy), 7)
                    pygame.draw.circle(self.surface, (254, 240, 138), (cx, cy), 4)

        # 5. Draw Goal Gate
        if level.goal:
            gx = level.goal.x - cam_x_int
            if -50 <= gx <= GAME_VIEW_WIDTH + 50:
                # Goal pillars
                pygame.draw.rect(self.surface, (147, 51, 234), (gx, level.goal.y, 8, level.goal.height))
                pygame.draw.rect(self.surface, (147, 51, 234), (gx + 24, level.goal.y, 8, level.goal.height))
                # Goal Energy Field
                energy_rect = pygame.Rect(gx + 8, level.goal.y, 16, level.goal.height)
                pygame.draw.rect(self.surface, COLOR_GOAL, energy_rect)
                pygame.draw.rect(self.surface, (216, 180, 254), energy_rect, 1)

        # 6. Draw Enemies
        for enemy in level.enemies:
            if enemy.alive:
                ex = int(enemy.x - cam_x_int)
                if -ENEMY_WIDTH <= ex <= GAME_VIEW_WIDTH + ENEMY_WIDTH:
                    erect = pygame.Rect(ex, int(enemy.y), enemy.width, enemy.height)
                    pygame.draw.rect(self.surface, COLOR_ENEMY_GOOMBA, erect, border_radius=6)
                    # Enemy eye
                    eye_x = ex + (6 if enemy.vx < 0 else 16)
                    pygame.draw.circle(self.surface, (255, 255, 255), (eye_x, int(enemy.y) + 10), 4)
                    pygame.draw.circle(self.surface, (0, 0, 0), (eye_x, int(enemy.y) + 10), 2)
            elif enemy.squish_timer > 0:
                # Squished visual
                ex = int(enemy.x - cam_x_int)
                erect = pygame.Rect(ex, int(enemy.y) + 18, enemy.width, 10)
                pygame.draw.rect(self.surface, (159, 18, 57), erect, border_radius=2)

        # 7. Draw Player
        px = int(player.x - cam_x_int)
        py = int(player.y)
        if not player.is_dead:
            p_rect = pygame.Rect(px, py, player.width, player.height)
            # Body
            pygame.draw.rect(self.surface, COLOR_PLAYER, p_rect, border_radius=6)
            # Core energy visor
            visor_x = px + (12 if player.facing_right else 4)
            pygame.draw.rect(self.surface, COLOR_PLAYER_CORE, (visor_x, py + 8, 10, 6), border_radius=2)
            # Running dust trail
            if player.running and player.grounded and abs(player.vx) > 3.0:
                trail_x = px + (0 if player.facing_right else player.width)
                pygame.draw.circle(self.surface, (125, 211, 252), (trail_x, py + player.height - 4), 3)
        else:
            # Dead animation
            p_rect = pygame.Rect(px, py, player.width, player.height)
            pygame.draw.rect(self.surface, (239, 68, 68), p_rect, border_radius=6)

        # 8. Overlay State (Stage Clear / Game Over banner)
        if player.has_won:
            banner = self.large_font.render("STAGE CLEAR!", True, (34, 197, 94))
            self.surface.blit(banner, (GAME_VIEW_WIDTH // 2 - banner.get_width() // 2, 200))
        elif player.is_dead:
            banner = self.large_font.render("GAME OVER (PRESS R)", True, (239, 68, 68))
            self.surface.blit(banner, (GAME_VIEW_WIDTH // 2 - banner.get_width() // 2, 200))

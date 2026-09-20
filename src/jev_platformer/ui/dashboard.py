"""HUD Dashboard rendering live Jev AI choice probabilities, latency, and telemetry."""

import pygame
from typing import Optional, Dict

from jev_platformer.engine.constants import (
    HUD_WIDTH, HUD_HEIGHT,
    COLOR_HUD_BG, COLOR_HUD_BORDER, COLOR_HUD_CARD,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED, COLOR_ACCENT,
    COLOR_DANGER, COLOR_SUCCESS
)
from jev_platformer.controller.mock_agent import DecisionResult
from jev_platformer.telemetry.models import JevObservation


class DashboardRenderer:
    """Renders the Keynote/Apple HIG style live telemetry and decision HUD."""

    def __init__(self, surface: pygame.Surface, offset_x: int):
        self.surface = surface
        self.offset_x = offset_x
        self.font_xs = pygame.font.SysFont("Consolas, Menlo, monospace", 11)
        self.font_sm = pygame.font.SysFont("Consolas, Menlo, monospace", 13)
        self.font_base = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 15, bold=True)
        self.font_large = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 22, bold=True)

    def render(
        self,
        obs: JevObservation,
        decision: Optional[DecisionResult],
        is_ai_mode: bool,
        fps: float
    ):
        hud_rect = pygame.Rect(self.offset_x, 0, HUD_WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.surface, COLOR_HUD_BG, hud_rect)
        pygame.draw.line(self.surface, COLOR_HUD_BORDER, (self.offset_x, 0), (self.offset_x, HUD_HEIGHT), 2)

        x = self.offset_x + 20
        y = 20

        # 1. Header Banner
        mode_badge = "AI AUTOPILOT" if is_ai_mode else "MANUAL HUMAN"
        badge_color = COLOR_ACCENT if is_ai_mode else (245, 158, 11)
        
        title_surf = self.font_large.render("JevDash: System One", True, COLOR_TEXT_PRIMARY)
        self.surface.blit(title_surf, (x, y))
        y += 32

        badge_rect = pygame.Rect(x, y, 130, 22)
        pygame.draw.rect(self.surface, COLOR_HUD_CARD, badge_rect, border_radius=4)
        pygame.draw.rect(self.surface, badge_color, badge_rect, 1, border_radius=4)
        badge_txt = self.font_xs.render(mode_badge, True, badge_color)
        self.surface.blit(badge_txt, (x + 8, y + 4))

        # Engine mode badge
        engine_str = "SIMULATED JEV"
        engine_col = COLOR_TEXT_MUTED
        if decision and not decision.is_mock:
            engine_str = "VERCEL JEV (LIVE)"
            engine_col = COLOR_SUCCESS
        eng_txt = self.font_xs.render(engine_str, True, engine_col)
        self.surface.blit(eng_txt, (x + 145, y + 4))
        y += 36

        # 2. Key Metrics Row (Latency, Danger, FPS)
        card_metrics = pygame.Rect(x, y, HUD_WIDTH - 40, 68)
        pygame.draw.rect(self.surface, COLOR_HUD_CARD, card_metrics, border_radius=8)
        pygame.draw.rect(self.surface, COLOR_HUD_BORDER, card_metrics, 1, border_radius=8)

        # Latency metric
        lat_val = f"{decision.latency_ms:.1f} ms" if decision else "--"
        l1 = self.font_xs.render("INFERENCE DELAY", True, COLOR_TEXT_MUTED)
        l2 = self.font_large.render(lat_val, True, COLOR_ACCENT)
        self.surface.blit(l1, (x + 12, y + 10))
        self.surface.blit(l2, (x + 12, y + 28))

        # Danger Score metric
        d_val = f"{decision.danger_score}/10" if decision else "--"
        d_col = COLOR_SUCCESS if (decision and decision.danger_score <= 3) else (
            (245, 158, 11) if (decision and decision.danger_score <= 6) else COLOR_DANGER
        )
        d1 = self.font_xs.render("DANGER SCORE", True, COLOR_TEXT_MUTED)
        d2 = self.font_large.render(d_val, True, d_col)
        self.surface.blit(d1, (x + 150, y + 10))
        self.surface.blit(d2, (x + 150, y + 28))

        # Progress / Score
        p1 = self.font_xs.render("PROGRESS", True, COLOR_TEXT_MUTED)
        p2 = self.font_large.render(f"{int(obs.episode.progress_pixels)}px", True, COLOR_TEXT_PRIMARY)
        self.surface.blit(p1, (x + 265, y + 10))
        self.surface.blit(p2, (x + 265, y + 28))
        y += 82

        # 3. Choice Probability Distribution (Bar Chart)
        sec_title = self.font_base.render("Choice Probability Distribution", True, COLOR_TEXT_PRIMARY)
        self.surface.blit(sec_title, (x, y))
        y += 26

        chart_card = pygame.Rect(x, y, HUD_WIDTH - 40, 200)
        pygame.draw.rect(self.surface, COLOR_HUD_CARD, chart_card, border_radius=8)
        pygame.draw.rect(self.surface, COLOR_HUD_BORDER, chart_card, 1, border_radius=8)

        if decision and decision.probabilities:
            bar_y = y + 12
            sorted_actions = sorted(decision.probabilities.items(), key=lambda item: item[1], reverse=True)
            for action_name, prob in sorted_actions:
                is_chosen = (action_name == decision.action)
                text_col = COLOR_ACCENT if is_chosen else COLOR_TEXT_MUTED
                
                # Action label
                lbl = self.font_xs.render(f"{action_name:<14}", True, text_col)
                self.surface.blit(lbl, (x + 14, bar_y))
                
                # Progress bar background
                bar_bg = pygame.Rect(x + 130, bar_y + 2, 160, 10)
                pygame.draw.rect(self.surface, (30, 36, 54), bar_bg, border_radius=3)
                
                # Progress bar fill
                fill_w = int(160 * prob)
                fill_col = COLOR_ACCENT if is_chosen else (71, 85, 105)
                if fill_w > 0:
                    pygame.draw.rect(self.surface, fill_col, (x + 130, bar_y + 2, fill_w, 10), border_radius=3)
                
                # Probability text
                pct_str = f"{prob * 100:.1f}%"
                pct_surf = self.font_xs.render(pct_str, True, text_col)
                self.surface.blit(pct_surf, (x + 300, bar_y))
                
                bar_y += 26
        y += 214

        # 4. Local Radar Grid
        radar_title = self.font_base.render("Local Radar Perception (7x11)", True, COLOR_TEXT_PRIMARY)
        self.surface.blit(radar_title, (x, y))
        y += 24

        radar_card = pygame.Rect(x, y, HUD_WIDTH - 40, 130)
        pygame.draw.rect(self.surface, COLOR_HUD_CARD, radar_card, border_radius=8)
        pygame.draw.rect(self.surface, COLOR_HUD_BORDER, radar_card, 1, border_radius=8)

        grid_y = y + 10
        for line in obs.local_grid:
            # Colorize characters
            radar_surf = self.font_xs.render(line, True, (94, 234, 212))
            self.surface.blit(radar_surf, (x + 16, grid_y))
            grid_y += 16
        y += 144

        # 5. Keybindings Reference
        y = HUD_HEIGHT - 90
        info_card = pygame.Rect(x, y, HUD_WIDTH - 40, 75)
        pygame.draw.rect(self.surface, (15, 23, 42), info_card, border_radius=6)
        pygame.draw.rect(self.surface, (30, 41, 59), info_card, 1, border_radius=6)

        k1 = self.font_xs.render("[TAB] Toggle AI / Manual Play", True, (226, 232, 240))
        k2 = self.font_xs.render("[R] Restart Episode    [Q/ESC] Quit", True, (148, 163, 184))
        k3 = self.font_xs.render("Manual: Arrows/WASD + Shift(Run) + Space(Jump)", True, (100, 116, 139))
        self.surface.blit(k1, (x + 12, y + 10))
        self.surface.blit(k2, (x + 12, y + 30))
        self.surface.blit(k3, (x + 12, y + 50))

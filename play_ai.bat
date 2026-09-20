@echo off
title Jev Platformer (AI Autopilot Mode)
cd /d "%~dp0"
echo Starting Jev Platformer in AI Autopilot Mode...
echo Controls:
echo   - Tab: Toggle Human Manual Control
echo   - R: Restart Episode
echo   - Q / Esc: Quit
echo.
uv run jev-runner play --mode ai
pause

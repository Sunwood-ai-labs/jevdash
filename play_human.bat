@echo off
title JevDash: System One (Manual Human Mode)
cd /d "%~dp0"
echo ===================================================
echo   JevDash: System One - Manual Human Play
echo ===================================================
echo Controls:
echo   - Left/Right (or A/D): Walk/Dash
echo   - Space (or W / Up): Jump (hold for high jump)
echo   - Shift: Run / Dash
echo   - Tab: Toggle AI Autopilot on the fly
echo   - R: Restart Level
echo   - Q / Esc: Quit
echo.
echo Recording gameplay video to jevdash_human.mp4...
echo.
uv run jevdash play --mode human --record jevdash_human.mp4
pause

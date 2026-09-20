@echo off
title JevDash: System One (Live Jev Mode via Vercel AI Gateway)
cd /d "%~dp0"
echo ===================================================
echo   JevDash: System One - Live Jev AI Autopilot
echo ===================================================
echo Connecting to real Jev model via Vercel AI Gateway...
echo Recording gameplay video to jevdash_live.mp4...
echo.
uv run jevdash play --mode live --record jevdash_live.mp4
pause

"""Game engine constants and configurations."""

# Display settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
GAME_TITLE = "JevDash: System One - Real-Time Autonomous AI Benchmark"
GAME_BRAND = "JevDash: System One"

# Layout split
GAME_VIEW_WIDTH = 880
GAME_VIEW_HEIGHT = 720
HUD_WIDTH = SCREEN_WIDTH - GAME_VIEW_WIDTH  # 400px
HUD_HEIGHT = 720

# Tile and physics dimensions
TILE_SIZE = 32
PLAYER_WIDTH = 26
PLAYER_HEIGHT = 36
ENEMY_WIDTH = 28
ENEMY_HEIGHT = 28

# Physics parameters
GRAVITY = 0.75
MAX_FALL_SPEED = 12.0
WALK_SPEED = 4.0
RUN_SPEED = 6.6
JUMP_STRENGTH = -13.5
RUN_JUMP_STRENGTH = -15.5
DECELERATION = 0.82
ACCELERATION = 0.60

# Colors (Apple HIG / Neon Pro Theme)
COLOR_BG = (10, 12, 18)             # Ultra dark blue/black
COLOR_GRID = (25, 30, 45)
COLOR_GROUND = (30, 41, 59)         # Slate 800
COLOR_GROUND_BORDER = (56, 189, 248) # Cyan highlight
COLOR_OBSTACLE = (51, 65, 85)       # Slate 700
COLOR_PIPE = (16, 185, 129)         # Emerald 500
COLOR_PLATFORM = (99, 102, 241)     # Indigo 500

# Entity colors
COLOR_PLAYER = (56, 189, 248)       # Cyan 400
COLOR_PLAYER_CORE = (255, 255, 255)
COLOR_ENEMY_GOOMBA = (244, 63, 94)  # Rose 500
COLOR_ENEMY_PATROL = (249, 115, 22) # Amber 500
COLOR_COIN = (251, 191, 36)         # Amber 400
COLOR_GOAL = (168, 85, 247)         # Purple 500

# HUD Colors
COLOR_HUD_BG = (15, 18, 28)
COLOR_HUD_BORDER = (38, 45, 66)
COLOR_HUD_CARD = (22, 27, 42)
COLOR_TEXT_PRIMARY = (248, 250, 252)
COLOR_TEXT_MUTED = (148, 163, 184)
COLOR_ACCENT = (56, 189, 248)
COLOR_DANGER = (239, 68, 68)
COLOR_SUCCESS = (34, 197, 94)

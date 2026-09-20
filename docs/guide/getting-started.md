# Getting Started with JevDash

Welcome to **JevDash: System One**, the high-performance 2D platformer AI benchmark.

## Prerequisites

- **Python**: 3.12 or newer (3.13 recommended)
- **uv**: Modern, ultra-fast Python package manager ([Installation Guide](https://docs.astral.sh/uv/))
- **FFmpeg**: Optional, required only for video recording (`uv run jevdash play --record ...`)

## Installation

Clone the repository and sync all dependencies in one command:

```bash
git clone https://github.com/Sunwood-ai-labs/jevdash.git
cd jevdash

# Sync virtual environment and dependencies using uv
uv sync --extra dev
```

## Running the Game

### 1. Manual Human Play Mode

Play the platformer manually using your keyboard. Press `Tab` at any time to hand over control to the AI!

```bash
uv run jevdash play --mode human
```

#### Controls:
- **Left / Right** (or **A / D**): Walk horizontally
- **Shift** (Hold): Sprint at top dash speed
- **Space** (or **W / Up**): Jump (hold for maximum leap height)
- **Tab**: **Toggle AI Autopilot ⇄ Manual control instantly**
- **R**: Restart level
- **Q / Esc**: Exit

### 2. Autonomous Simulated AI Mode (No API Key Required)

Run the autonomous AI autopilot using the built-in deterministic analytical engine:

```bash
uv run jevdash play --mode mock
```

### 3. Live Jev Model via Vercel AI Gateway (Free Tier)

::: tip Vercel Free Tier Supported
TypeSafe Jev is accessible through Vercel AI Gateway's free tier (Hobby plan). You can experiment with the real live model without requiring paid subscriptions or expensive GPU servers.
:::

To play with the real, live **TypeSafe Jev** model (`typesafe-ai/jev`):

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Insert your Vercel AI Gateway API key into `.env`:
   ```env
   AI_GATEWAY_API_KEY=vck_your_api_key_here
   ```
3. Run the live game:
   ```bash
   uv run jevdash play --mode live --record jevdash_live.mp4
   ```

## Running the Tests

Ensure everything is configured and functioning properly:

```bash
uv run pytest -v
```

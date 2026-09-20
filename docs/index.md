---
layout: home

hero:
  name: "JevDash: System One"
  text: "Autonomous AI 2D Platformer"
  tagline: "100% Clean-Room, Copyright-Free 60 FPS Benchmark for TypeSafe Jev AI"
  image:
    src: /gameplay.gif
    alt: JevDash Live Gameplay
  actions:
    - theme: brand
      text: Getting Started
      link: /guide/getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/Sunwood-ai-labs/jevdash

features:
  - icon: 🛡️
    title: 100% Clean-Room & Legal
    details: Zero proprietary game ROMs or copyrighted assets. Safe for commercial evaluation, open-source demos, and academia.
  - icon: ⚡
    title: Live TypeSafe Jev Model (Free Tier)
    details: Direct single forward-pass integration via Vercel AI Gateway (typesafe-ai/jev) available on Vercel's free tier with Choice, Boolean, and Score primitives.
  - icon: 🎥
    title: Real-Time MP4 Recording
    details: Integrated FFmpeg video pipeline captures smooth 1280x720 60 FPS H.264 gameplay videos automatically.
  - icon: 📊
    title: Apple HIG / Keynote HUD
    details: Beautiful live dashboard displaying probability bar charts, danger meters, latency timers, and 7x11 ASCII radar.
---

## 🎮 Live AI Gameplay Showcase

<div style="text-align: center; margin: 1.5rem 0 2rem 0;">
  <img src="/gameplay.gif" alt="JevDash Live Gameplay Demo" style="border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 100%;">
</div>

### Real-Time Telemetry & Perception
- **Asynchronous Decision Pipeline**: Sub-frame AI queries without stuttering the 60 FPS physics loop.
- **Physical HUD**: Real-time Choice probability distribution, Danger Score (1–10), latency monitor, and 7×11 ASCII local radar.
- **Continuous Recording**: Auto-captures gameplay to high-definition H.264 MP4 videos.

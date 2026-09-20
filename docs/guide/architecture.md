# Architecture & Design

**JevDash: System One** is built around a decoupled dual-loop architecture designed to benchmark LLMs and autonomous agents in real-time physical control environments.

```
┌─────────────────────────────────────────────────────────────┐
│                    Outer Loop (Asynchronous)                │
│                                                             │
│   ┌────────────────┐      HTTP/JSON       ┌─────────────┐   │
│   │  JevAgent /    │ ───────────────────> │  Jev Model  │   │
│   │  MockAgent     │ <─────────────────── │  (Gateway)  │   │
│   └────────────────┘   Structured Action  └─────────────┘   │
│           │                                                 │
│   State   │ Actuator Queue (Thread-Safe Buffer)             │
│   Capture │                                                 │
│           ▼                                                 │
├─────────────────────────────────────────────────────────────┤
│                    Inner Loop (Synchronous 60 FPS)          │
│                                                             │
│   ┌────────────────┐   Integration Step   ┌─────────────┐   │
│   │ Pygame Canvas  │ <─────────────────── │   Physics   │   │
│   │ & Live HUD     │                      │   Engine    │   │
│   └────────────────┘                      └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Dual-Loop Decoupling

In high-speed 2D platformers, physics must evaluate strictly at fixed delta times (60 Hz) to avoid tunneling, clipping, or frame drops. However, network round-trips to foundation models vary from 50ms to 500ms.

To overcome this impedance mismatch, JevDash implements two concurrent loops:

### Fast Inner Loop (60 FPS)
- Handles player kinematic equations:
  $$x_{t+\Delta t} = x_t + v_x \Delta t$$
  $$v_{y, t+\Delta t} = v_{y, t} + g \Delta t$$
- Resolves AABB (Axis-Aligned Bounding Box) platform collisions.
- Smoothly executes the latest action buffer committed by the agent.
- Captures gameplay frames and encodes them into H.264 MP4 streams if recording is enabled.

### Asynchronous Outer Loop (Agent Thread)
- Samples an abstract sensory snapshot of the game state:
  - Agent position and velocity vectors.
  - Distances to the nearest gap, high barrier, or hazard.
  - Feasibility of jumping given current momentum.
- Submits this structured payload to the Jev model via OpenAI-compatible endpoints or evaluates it via the deterministic mock engine.
- Pushes the resulting action command into a thread-safe atomic buffer.

---

## 2. Structured State & Action Spaces

JevDash uses strict type definitions to prevent hallucination in physical actions:

### Observation Space
```json
{
  "player": {
    "x": 340.5,
    "y": 480.0,
    "vx": 4.8,
    "vy": 0.0,
    "is_grounded": true
  },
  "upcoming_obstacles": [
    {
      "type": "gap",
      "distance": 85.0,
      "width": 110.0
    }
  ],
  "can_jump": true
}
```

### Action Space
The model selects actions conforming to discrete physical triggers:
- `MOVE_RIGHT`: Apply horizontal acceleration.
- `JUMP`: Engage jump impulses; sustained hold increases jump apex.
- `SPRINT`: Increase maximum velocity threshold.
- `IDLE`: Decelerate via friction.

---

## 3. Clean-Room Implementation

JevDash uses **zero copyrighted sprites or proprietary level designs**:
- All tiles, obstacles, and player avatars are procedurally drawn with vector primitives (neon glow outlines, high-contrast flat surfaces).
- Level generation is mathematically procedural, allowing reproducible algorithmic benchmarks across varying difficulty tiers.
- The engine runs cross-platform on Windows, macOS, and Linux without native binary dependencies outside standard Pygame.

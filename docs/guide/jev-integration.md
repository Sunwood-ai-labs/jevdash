# Jev AI Integration

**JevDash** is engineered to evaluate the physical reaction speed, spatial reasoning, and decision latency of **TypeSafe Jev** (`typesafe-ai/jev`).

---

## 1. Overview of TypeSafe Jev

TypeSafe Jev is an emerging reasoning architecture designed for strict schema compliance, low-latency actuation, and deterministic tool/action generation. In JevDash, Jev acts as an autonomous motor-cortex agent navigating dynamic physical platform challenges.

---

## 2. Gateway Connection

JevDash communicates with Jev via the **Vercel AI Gateway** using an OpenAI-compatible interface:

- **Base URL**: `https://ai-gateway.vercel.sh/v1`
- **Model Identifier**: `typesafe-ai/jev`
- **Authentication**: Bearer token (`AI_GATEWAY_API_KEY`)

### Configuration (.env)

```env
AI_GATEWAY_API_KEY=vck_your_secret_token_here
AI_GATEWAY_BASE_URL=https://ai-gateway.vercel.sh/v1
JEV_MODEL_NAME=typesafe-ai/jev
```

---

## 3. Decision Pipeline

At every observation tick:

1. **State Serialization**: The game engine compiles spatial coordinates into a concise markdown or JSON prompt.
2. **Kinematic Hinting**: The prompt includes computed time-to-impact (TTI) for imminent pits and barriers:
   ```text
   Current Velocity: vx=6.2 px/frame
   Next Hazard: Pit at distance 95.0 px (Est. 15 frames to edge)
   Jump Range at current speed: 140.0 px
   ```
3. **Structured Response**: Jev returns a structured JSON payload indicating immediate motor actions:
   ```json
   {
     "action": "JUMP_AND_SPRINT",
     "reasoning": "Approaching gap of 110px. Sprint velocity ensures clean landing across 140px leap window."
   }
   ```
4. **Actuation Queue**: The engine buffers the decision and executes it across subsequent 60 FPS physics ticks.

---

## 4. Fallback: Analytical Mock Agent

When developing offline or running fast automated CI tests, JevDash includes a zero-latency **Deterministic Mock Agent**:

```bash
uv run jevdash play --mode mock
```

The mock agent uses pure geometric raycasting and parabolic trajectory prediction to achieve consistent, 100% reproducible stage clears.

---

## 5. Telemetry & Benchmark Metrics

JevDash records real-time agent telemetry during every run:
- **Decision Frequency**: Agent decisions per second (Hz).
- **Inference Round-Trip Time**: Network latency vs. token processing duration.
- **Traversal Velocity**: Average horizontal speed through the level.
- **Stage Completion Time**: Total elapsed seconds from spawn to goal portal.

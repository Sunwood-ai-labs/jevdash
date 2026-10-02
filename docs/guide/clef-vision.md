# Optional Clef vision controller

`vision-clef` is an **additional** experimental controller. Existing `play` modes
(`human`, `mock`, `ai`, `live`), the `live` alias, `state-demo`, `benchmark`, Vercel
integration, keyboard controls, and the original MP4 recorder are unchanged.
The original Level 1 geometry, movement, gravity, collisions, enemies, and goal
are used without modification.

## What the model sees

Only real game-viewport images are passed to Cloudflare Clef-Flash 9B. The two
most recent decision frames are cropped from the 880×720 game viewport and
resized to 704×576. The first decision has one image. The model also gets the
objective, action definitions, frame timestamps, and its last commanded action.
It does **not** get world coordinates, velocity, grounded state, terrain/enemy
telemetry, radar, the diagnostic sidebar, or a hand-written jump recommendation.
The sidebar and result logs may show engine state for human evaluation; that
state is not sent to Clef.

Each of the seven original actions is selected directly by the model's typed
choice head. The new mode does not use the original mock fallback, safety
reflex, or a scripted action policy. Those features remain intact for existing
modes. The last model action remains held while inference runs. Before the first
answer, the action is `noop`. An inference error fails the trial visibly; it does
not silently switch to another controller. A dead worker is detected promptly;
a decision older than 10 real seconds is rejected without applying it. Closing
the window cancels the entire session, including remaining episodes.

## Install and run

The heavyweight model dependencies are optional. The default installation does
not download PyTorch, Transformers, model weights, or GPU packages.

```bash
uv sync --extra clef
uv run jevdash vision-clef --out clef-vision-output --episodes 3 --seconds 60
```

The current reproducibility profile requires an NVIDIA L4 with BF16 support.
Model setup downloads the pinned public checkpoint
`Cloudflare/clef-flash@17f0b0ad64efb65d273590632833508766b2aae6` and checks the
reviewed `joint_schema_model.py` SHA256 before importing it. Model setup and
warmup happen before each recorded session starts. Run only on compute you
have authorized; this command does not allocate or release a cloud runtime.
The wrapper operating the runtime must enforce any spending/time budget.

On a desktop the game opens a Pygame window. On display-less Linux/Colab it
captures the original rendered game surface directly with SDL's dummy display.
This is a real-time render, not the accelerated `benchmark` command. No browser
or public inference endpoint is needed.

## Real-time and recording contract

- Physics has an independent main process, scheduled at 60 Hz against a
  monotonic clock; model inference runs in a separate process
- Only one inference is in flight. A new observation is captured when that
  request completes, avoiding an ever-growing stale-input queue
- Video encoding runs independently and receives actual rendered RGB frames
- MP4 presentation timestamps come from actual capture time, rather than
  assuming every render took exactly 1/60 second
- There is no intentional pause, step-through simulation, replay rendering,
  time scaling, fabricated missing frame, or heuristic recovery
- Each episode ends at death, goal, or its real-wall-clock limit (at most
  60 seconds). A separately identified one-second end screen is also captured
- Runtime slowdown and dropped frames remain visible in the logs. A
  `realtime_validation_pass` requires physics/wall-clock ratio within 5%,
  maximum scheduling lateness below 100 ms, and no recorder drops; it is not
  a claim that operating systems can guarantee hard real-time execution

The source game contains no sound, so recordings are deliberately silent.

## Evidence

Each run requires an empty output directory, so previous captures and hashes cannot
be overwritten or accidentally reused. The output directory contains per-episode MP4 files, frame-level action/world
logs, inference logs, model environment and checkpoint identity, image inputs,
and summaries. Decisions identify their source frame, input-image hashes,
model-only latency, and full capture-to-action delay. Model-input PNGs are saved
under `observations/`; episode 00 is warmup and is not scored. Gameplay videos
include a live wall-clock counter, physics time, model choices/probabilities,
latency, and score/progress.

Do not infer general model ability from three episodes of one fixed level.
Report failed and successful episodes, frame timing, and observation mode.

## CPU-only infrastructure check

```bash
uv sync --extra dev --extra vision-recording
uv run jevdash vision-clef --out timing-fixture --episodes 2 --seconds 3 --smoke
uv run pytest -v
```

`--smoke` deliberately uses a fixed test action with a 400 ms delay. Every video
and summary labels it `TEST FIXTURE / NOT CLEF`. This verifies asynchronous
physics and capture plumbing only; it must never be presented as Clef gameplay.
The live API integration tests still require their original external API key.

---
name: spritelet-generator
description: "Generate and manage Spritelet mascot avatars from a base reference image plus state metadata, with low-cost publish signaling. Use when an AI agent needs to: (1) set up a Spritelet state store, (2) generate new spritelet images with Nano Banana Pro on Google APIs, (3) publish which image is currently active, (4) maintain a simple current-state pointer with timestamp, or (5) reuse existing state images from a catalog before generating new ones."
---

# Spritelet Generator

Initialize and run a low-cost avatar pipeline that keeps mascot identity stable while updating expression states.

## What This Is For

Use this skill to let an AI agent communicate non-verbally with a human via a visual avatar state.

Typical uses:
- Show current work mode (for example: coding, reviewing, debugging, planning).
- Show current emotional tone (for example: focused, excited, calm, concerned).
- Reflect context shifts during long tasks without changing core identity.
- Keep a live "current spritelet" image that any UI can display.
- Reuse existing state images to reduce cost and generation latency.

## Project Layout

Keep skill code and generated identity data in sibling folders:
- Skill folder: `<workspace>/spritelet-generator`
- Identity folder: `<workspace>/spritelet-identity`

Use the identity folder as `--root` for all operational scripts.

Example:

```bash
scripts/publish_spritelet_state.py \
  --root /Users/aurialloop/Projects/SpriteExpressionSystem/spritelet-identity \
  --simple-name "focused coding" \
  --description "Focused and heads-down while coding."
```

## Primary Workflow

Use one command for end-to-end behavior:

```bash
scripts/publish_spritelet_state.py \
  --root <spritelet-root> \
  --simple-name "focused coding" \
  --description "Focused and heads-down while coding."
```

This command does:
1. Check catalog for exact `simple_name` reuse.
2. Reuse existing state image or call Nano Banana Pro API.
3. Save image under `states/` when generated.
4. Upsert catalog entry.
5. Publish `signals/current.json`.
6. Write event log entry.

## Publish Internals

When `scripts/publish_spritelet_state.py` runs, it executes this order:

1. Load store configuration:
`load_json()` reads `spritelet.json` for base image path and style guidance.
2. Resolve state identity:
`resolve_catalog_state()` normalizes `simple_name` and checks `states/catalog.json` for an existing state entry.
3. Reuse-or-generate decision:
If a matching catalog entry exists and file is present, reuse that `spritelet_path`.
4. Build generation prompt:
If no reusable entry exists (or `--force-generate`), `build_prompt()` composes prompt text from `simple_name`, `description`, and `prompt_style`.
5. Request image generation:
`call_generation_api()` sends the multimodal request to Nano Banana Pro using the base reference image.
6. Decode image payload:
`extract_image_bytes()` reads image bytes from API response (`inline_data`/`inlineData`).
7. Save state image:
Script writes bytes to `states/<simple-name>.png` (or timestamped variant if needed).
8. Persist state atomically:
Inside `store_lock(...)`, script updates `states/catalog.json`, then updates `signals/current.json`, then appends a publish event to `signals/events.jsonl`.
9. Return publish result:
Script prints JSON summary containing `published`, `simple_name`, `spritelet_path`, and `reused`.

## Initialize Store

Run:

```bash
scripts/init_spritelet_store.py --root <spritelet-root> --base-image assets/base.png
```

This creates:
- `spritelet.json`
- `signals/current.json`
- `signals/events.jsonl`
- `assets/`
- `states/`
- `states/catalog.json`

## Base Prompt And Identity Base Image

- Update `<spritelet-root>/spritelet.json` field `prompt_style` to change the reusable base prompt style applied to generated states.
- Update `<spritelet-root>/spritelet.json` field `base_image_path` to attach or switch the reference identity image.

Bootstrap the first base image with:

```bash
scripts/optional-tools/generate_initial_base_image.py \
  --root <spritelet-root> \
  --identity-prompt "A cute fox robot mascot with round eyes and teal scarf." \
  --output-path "assets/base.png"
```

This generates the first identity image, saves it, and updates `spritelet.json.base_image_path`.

## State Catalog Schema

Each state entry in `states/catalog.json` must include:
- `simple_name`
- `spritelet_path`
- `created_at`
- `description`

## Optional Tools

- Build request JSON only:

```bash
scripts/optional-tools/build_nano_banana_request.py --root <spritelet-root> --simple-name "focused coding" --description "Focused and heads-down while coding." --output request.json
```

- Lookup catalog:

```bash
scripts/optional-tools/find_state_in_catalog.py --root <spritelet-root> --simple-name "focused coding"
```

- Register state directly:

```bash
scripts/optional-tools/register_state_in_catalog.py --root <spritelet-root> --simple-name "focused coding" --spritelet-path "states/focused-coding.png" --description "Focused and heads-down while coding."
```

- Publish current path directly:

```bash
scripts/optional-tools/set_spritelet_signal.py --root <spritelet-root> --spritelet-path "states/focused-coding.png"
```

- Generate first base identity image:

```bash
scripts/optional-tools/generate_initial_base_image.py --root <spritelet-root> --identity-prompt "A cute fox robot mascot with round eyes and teal scarf."
```

## Safety Rules

- Keep `signals/current.json` minimal: only `spritelet_path` and `updated_at`.
- Keep metadata (`simple_name`, `description`) in catalog only.
- Require all published and cataloged paths to stay inside `states/`.
- Require published file path to exist.
- Use file locking for concurrent writers.

## Recommended Update Rates

- Prefer reuse over generation whenever `simple_name` already exists in catalog.
- For routine work, generate at most once every 10-20 minutes.
- Generate immediately for meaningful state shifts (new task mode or clear emotional change).
- For minor wording changes only, reuse the existing state image and just republish if needed.
- During long sessions, target 3-6 generated states per hour maximum.

## References

- `references/state-and-signals.md`: current-state and catalog schema
- `references/nano-banana-api.md`: request pattern and cost controls

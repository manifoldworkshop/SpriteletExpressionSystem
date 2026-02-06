# Spritelet State and Signals

Use a minimal current-state file plus a state catalog for reuse decisions.

Assume these files live under the identity root (recommended: `<workspace>/spritelet-identity`).

## Files

- `spritelet.json`: base profile (base image path and style)
- `signals/current.json`: current published spritelet pointer
- `signals/events.jsonl`: append-only change history
- `assets/`: location for base identity reference image
- `states/`: generated image files
- `states/catalog.json`: known state-to-image mappings

## `spritelet.json` Schema

```json
{
  "base_image_path": "assets/base.png",
  "prompt_style": "cute animal mascot, clean lines, expressive face, transparent background",
  "created_at": "2026-02-06T09:30:04Z"
}
```

Required fields:
- `base_image_path`: reference image path used for identity lock
- `prompt_style`: reusable style guidance appended to prompts
- `created_at`: UTC timestamp when the store was initialized

## `signals/current.json` Schema

```json
{
  "spritelet_path": "states/2026-02-06-focused.png",
  "updated_at": "2026-02-06T09:30:04Z"
}
```

Required fields:
- `spritelet_path`: path to the image currently shown to the user
- `updated_at`: UTC timestamp of when the current spritelet was published

## `states/catalog.json` Schema

```json
{
  "states": {
    "focused-coding": {
      "simple_name": "focused-coding",
      "spritelet_path": "states/focused-coding.png",
      "created_at": "2026-02-06T09:30:04Z",
      "description": "Focused and heads-down while coding."
    }
  }
}
```

Required fields for each state entry:
- `simple_name`: simple normalized state name
- `spritelet_path`: file name/path for the state image
- `created_at`: UTC timestamp when this state entry was first created
- `description`: short human-readable description of the state

## `signals/events.jsonl` Schema

`signals/events.jsonl` is newline-delimited JSON. Each line is one event object.

Common required fields on each event:
- `type`: event type string
- `updated_at`: UTC timestamp when the event occurred

### Event: `state_initialized`

```json
{
  "type": "state_initialized",
  "spritelet_path": "",
  "updated_at": "2026-02-06T09:30:04Z"
}
```

### Event: `state_catalog_upserted`

```json
{
  "type": "state_catalog_upserted",
  "simple_name": "focused-coding",
  "spritelet_path": "states/focused-coding.png",
  "updated_at": "2026-02-06T09:31:10Z"
}
```

### Event: `current_spritelet_updated`

```json
{
  "type": "current_spritelet_updated",
  "spritelet_path": "states/focused-coding.png",
  "updated_at": "2026-02-06T09:31:12Z"
}
```

### Event: `state_published`

```json
{
  "type": "state_published",
  "simple_name": "focused-coding",
  "spritelet_path": "states/focused-coding.png",
  "reused": true,
  "updated_at": "2026-02-06T09:31:12Z"
}
```

### Event: `base_image_initialized`

```json
{
  "type": "base_image_initialized",
  "spritelet_path": "assets/base.png",
  "updated_at": "2026-02-06T09:31:12Z"
}
```

## Reuse-First Rule

Before generating a new image:
1. Check catalog with `scripts/optional-tools/find_state_in_catalog.py`
2. If found, reuse `spritelet_path` and publish via `signals/current.json`
3. If not found, run `scripts/publish_spritelet_state.py` to generate, upsert catalog, and publish in one step
4. Use `scripts/optional-tools/register_state_in_catalog.py` only for direct/manual catalog edits

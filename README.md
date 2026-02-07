# Spritelet Expression System

Spritelet Expression System provides a reusable AI skill (`spritelet-generator`) and a separate identity data store (`spritelet-identity`) for generating and publishing expressive mascot states.

## Project Structure

- `spritelet-generator/`: Skill definition, references, and scripts
- `spritelet-identity/`: Generated identity/state data (JSON + image paths)

## Key Concepts

- **Skill code** stays in `spritelet-generator`
- **State/memory data** stays in `spritelet-identity`
- `signals/current.json` is the active pointer for what to display now
- `states/catalog.json` is the reusable state catalog

## Quick Start

1. Initialize identity store:

```bash
spritelet-generator/scripts/init_spritelet_store.py \
  --root /Users/aurialloop/Projects/SpriteExpressionSystem/spritelet-identity \
  --base-image assets/base.png
```

2. (Optional) Generate first base identity image:

```bash
spritelet-generator/scripts/optional-tools/generate_initial_base_image.py \
  --root /Users/aurialloop/Projects/SpriteExpressionSystem/spritelet-identity \
  --identity-prompt "A cute fox robot mascot with round eyes and teal scarf." \
  --output-path "assets/base.png"
```

3. Publish or reuse a state:

```bash
spritelet-generator/scripts/publish_spritelet_state.py \
  --root /Users/aurialloop/Projects/SpriteExpressionSystem/spritelet-identity \
  --simple-name "focused coding" \
  --description "Focused and heads-down while coding."
```

## Environment

Set your API key before generation calls:

```bash
export SPRITELET_GOOGLE_API_KEY="<your-key>"
```

Recommended local setup:

```bash
cat > .env.local <<'EOF'
export SPRITELET_GOOGLE_API_KEY="<your-key>"
EOF
source .env.local
```

## Image API Defaults

- Default model: `models/gemini-3-pro-image-preview`
- Default API key env var: `SPRITELET_GOOGLE_API_KEY`
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/{model}:generateContent`

Both generation scripts support overrides with:
- `--model`
- `--api-key-env`
- `--endpoint`

## License

MIT (see `LICENSE`).

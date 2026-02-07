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
- State reuse is base-image-aware: if `assets/base.png` was modified after a state's `created_at`, that state is regenerated before publish.

## Quick Start

1. Initialize identity store:

```bash
spritelet-generator/scripts/init_spritelet_store.py \
  --root spritelet-identity \
  --base-image assets/base.png
```

2. (Optional) Generate first base identity image:

```bash
spritelet-generator/scripts/optional-tools/generate_initial_base_image.py \
  --root spritelet-identity \
  --identity-prompt "A cute fox robot mascot with round eyes and teal scarf." \
  --output-path "assets/base.png"
```

3. Publish or reuse a state:

```bash
spritelet-generator/scripts/publish_spritelet_state.py \
  --root spritelet-identity \
  --simple-name "focused coding" \
  --description "Focused and heads-down while coding."
```

4. Reset identity store to clean start (useful before commits):

```bash
spritelet-generator/scripts/optional-tools/reinit_spritelet_store.py \
  --root spritelet-identity
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

## TLS / Certificate Troubleshooting

If generation calls fail with an SSL error like:

`ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]`

your local Python trust store is likely missing a CA bundle.

Use `certifi` for the current shell session before running generation scripts:

```bash
export SSL_CERT_FILE="$(python3 -c 'import certifi; print(certifi.where())')"
```

Then run the normal script command again.

If `certifi` is missing:

```bash
python3 -m pip install certifi
```

## Image API Defaults

- Default model: `models/gemini-3-pro-image-preview`
- Default API key env var: `SPRITELET_GOOGLE_API_KEY`
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/{model}:generateContent`
- Default aspect ratio: `1:1`
- Default image size: `1K`

Both generation scripts support overrides with:
- `--model`
- `--api-key-env`
- `--endpoint`
- `--aspect-ratio`
- `--image-size`

Background behavior:
- Background is intentionally model-chosen from state context (no forced transparency by default).
- Keep emotional/work context in `--description` to influence scene and mood.

## License

MIT (see `LICENSE`).

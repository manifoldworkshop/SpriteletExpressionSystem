# Nano Banana Pro API Notes

Use Google Gemini-style multimodal request format with one reference image and one text prompt.

## Request Shape

- `model`: set by environment, default `models/nano-banana-pro`
- `contents[0].parts`: include image `inline_data` and prompt text
- `generation_config.response_modalities`: include `IMAGE`

## Minimal cURL Pattern

```bash
curl -sS "https://generativelanguage.googleapis.com/v1beta/models/nano-banana-pro:generateContent?key=${GOOGLE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @request.json
```

Build `request.json` with `scripts/optional-tools/build_nano_banana_request.py`.
For first-time identity setup, use `scripts/optional-tools/generate_initial_base_image.py`.

## Prompt Inputs

Use schema-aligned state metadata:
- `--simple-name`
- `--description`

Do not store these in `signals/current.json`; keep current file minimal.

## Response Handling

Expect image bytes under candidate parts in either:
- `inline_data.data`
- `inlineData.data`

Decode base64 and write bytes to a file under `states/`.

`scripts/publish_spritelet_state.py` already does this end to end.

## Cost Controls

- Reuse same base image unless identity intentionally changes
- Check catalog before generating

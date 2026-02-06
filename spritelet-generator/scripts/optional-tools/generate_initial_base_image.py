#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from store_utils import append_jsonl, atomic_write_json, store_lock, utc_now


def call_generation_api(model: str, api_key: str, endpoint: str, request_payload: dict) -> dict:
    url = endpoint
    if "{model}" in endpoint:
        url = endpoint.replace("{model}", urllib.parse.quote(model, safe="/"))
    if "key=" not in url:
        joiner = "&" if "?" in url else "?"
        url = f"{url}{joiner}key={urllib.parse.quote(api_key)}"

    req = urllib.request.Request(
        url=url,
        data=json.dumps(request_payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Generation API failed: {e.code} {body}") from e


def extract_image_bytes(response_payload: dict) -> bytes:
    candidates = response_payload.get("candidates", [])
    for candidate in candidates:
        parts = candidate.get("content", {}).get("parts", [])
        for part in parts:
            inline = part.get("inline_data") or part.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise SystemExit("No image bytes found in generation API response")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the first base Spritelet image and attach it to spritelet.json")
    parser.add_argument("--root", required=True, help="Spritelet identity root")
    parser.add_argument("--identity-prompt", required=True, help="Identity prompt for the first base image")
    parser.add_argument("--output-path", default="assets/base.png", help="Relative output path for the base image")
    parser.add_argument("--model", default="models/nano-banana-pro")
    parser.add_argument("--endpoint", default="https://generativelanguage.googleapis.com/v1beta/{model}:generateContent")
    parser.add_argument("--api-key-env", default="GOOGLE_API_KEY")
    args = parser.parse_args()

    root = Path(args.root)
    spritelet_path = root / "spritelet.json"
    if not spritelet_path.exists():
        raise SystemExit("Missing spritelet.json; run init_spritelet_store.py first")

    spritelet = json.loads(spritelet_path.read_text(encoding="utf-8"))
    style = spritelet.get("prompt_style", "")
    prompt = f"Create a mascot base avatar. Identity brief: {args.identity_prompt}. Style: {style}."

    request_payload = {
        "model": args.model,
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generation_config": {"response_modalities": ["IMAGE"]},
    }

    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        raise SystemExit(f"Missing API key env var: {args.api_key_env}")

    response_payload = call_generation_api(args.model, api_key, args.endpoint, request_payload)
    image_bytes = extract_image_bytes(response_payload)

    out_rel = args.output_path
    out_abs = (root / out_rel).resolve()
    out_abs.parent.mkdir(parents=True, exist_ok=True)
    out_abs.write_bytes(image_bytes)

    now = utc_now()
    with store_lock(root):
        spritelet = json.loads(spritelet_path.read_text(encoding="utf-8"))
        spritelet["base_image_path"] = out_rel
        atomic_write_json(spritelet_path, spritelet)
        append_jsonl(
            root / "signals" / "events.jsonl",
            {
                "type": "base_image_initialized",
                "spritelet_path": out_rel,
                "updated_at": now,
            },
        )

    print(
        json.dumps(
            {
                "initialized": True,
                "base_image_path": out_rel,
                "updated_at": now,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

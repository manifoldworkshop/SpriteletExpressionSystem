#!/usr/bin/env python3
import argparse
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from store_utils import (
    append_jsonl,
    atomic_write_json,
    normalize_simple_name,
    resolve_store_path,
    store_lock,
    utc_now,
)


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_catalog_state(root: Path, simple_name: str) -> tuple[str, dict | None]:
    catalog = load_json(root / "states" / "catalog.json", {"states": {}})
    states = catalog.get("states", {})
    key = normalize_simple_name(simple_name)
    return key, states.get(key)


def build_prompt(profile: dict, simple_name: str, description: str) -> str:
    return (
        "Use the provided reference image as identity lock for this mascot. "
        f"State name: {simple_name}. "
        f"State description: {description}. "
        f"Style: {profile.get('prompt_style', '')}."
    )


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
    parser = argparse.ArgumentParser(description="Reuse or generate and publish a Spritelet state")
    parser.add_argument("--root", required=True, help="Spritelet identity root")
    parser.add_argument("--simple-name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--model", default="models/nano-banana-pro")
    parser.add_argument("--endpoint", default="https://generativelanguage.googleapis.com/v1beta/{model}:generateContent")
    parser.add_argument("--api-key-env", default="GOOGLE_API_KEY")
    parser.add_argument("--force-generate", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    profile = load_json(root / "spritelet.json", {})
    if not profile:
        raise SystemExit("Missing spritelet.json; run init_spritelet_store.py first")

    key, state = resolve_catalog_state(root, args.simple_name)
    reused = False
    spritelet_path = ""

    if state and not args.force_generate:
        spritelet_path = state["spritelet_path"]
        if not resolve_store_path(root, spritelet_path).exists():
            raise SystemExit(f"Catalog points to missing file: {spritelet_path}")
        reused = True
    else:
        base_image = Path(profile["base_image_path"])
        if not base_image.is_absolute():
            base_image = (root / base_image).resolve()
        if not base_image.exists():
            raise SystemExit(f"Base image not found: {base_image}")

        prompt = build_prompt(profile, args.simple_name, args.description)
        request_payload = {
            "model": args.model,
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64.b64encode(base_image.read_bytes()).decode("ascii"),
                            }
                        },
                        {"text": prompt},
                    ],
                }
            ],
            "generation_config": {"response_modalities": ["IMAGE"]},
        }
        api_key = os.environ.get(args.api_key_env, "")
        if not api_key:
            raise SystemExit(f"Missing API key env var: {args.api_key_env}")

        response_payload = call_generation_api(args.model, api_key, args.endpoint, request_payload)
        image_bytes = extract_image_bytes(response_payload)

        target_name = normalize_simple_name(args.simple_name)
        out_rel = f"states/{target_name}.png"
        out_abs = resolve_store_path(root, out_rel)
        if out_abs.exists():
            out_rel = f"states/{target_name}-{utc_now().replace(':', '').replace('-', '')}.png"
            out_abs = resolve_store_path(root, out_rel)
        out_abs.parent.mkdir(parents=True, exist_ok=True)
        out_abs.write_bytes(image_bytes)
        spritelet_path = out_rel

    now = utc_now()
    with store_lock(root):
        catalog_path = root / "states" / "catalog.json"
        catalog = load_json(catalog_path, {"states": {}})
        created_at = catalog.get("states", {}).get(key, {}).get("created_at", now)
        catalog.setdefault("states", {})[key] = {
            "simple_name": key,
            "spritelet_path": spritelet_path,
            "created_at": created_at,
            "description": args.description,
        }
        atomic_write_json(catalog_path, catalog)

        atomic_write_json(
            root / "signals" / "current.json",
            {"spritelet_path": spritelet_path, "updated_at": now},
        )
        append_jsonl(
            root / "signals" / "events.jsonl",
            {
                "type": "state_published",
                "simple_name": key,
                "spritelet_path": spritelet_path,
                "reused": reused,
                "updated_at": now,
            },
        )

    print(
        json.dumps(
            {
                "published": True,
                "simple_name": key,
                "spritelet_path": spritelet_path,
                "reused": reused,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

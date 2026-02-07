#!/usr/bin/env python3
import argparse
import base64
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an image generation API request JSON from Spritelet state")
    parser.add_argument("--root", required=True, help="Spritelet identity root")
    parser.add_argument("--simple-name", required=True, help="Simple state name")
    parser.add_argument("--description", required=True, help="State description")
    parser.add_argument("--base-image", help="Override base image path")
    parser.add_argument("--model", default="models/gemini-3-pro-image-preview", help="Model name")
    parser.add_argument("--output", default="-", help="Write JSON to file path or '-' for stdout")
    args = parser.parse_args()

    root = Path(args.root)
    profile = json.loads((root / "spritelet.json").read_text(encoding="utf-8"))

    base_image_path = Path(args.base_image) if args.base_image else Path(profile["base_image_path"])
    if not base_image_path.is_absolute():
        base_image_path = (root / base_image_path).resolve()
    if not base_image_path.exists():
        raise SystemExit(f"Base image not found: {base_image_path}")

    prompt = (
        "Use the provided reference image as identity lock for this mascot. "
        f"State name: {args.simple_name}. "
        f"State description: {args.description}. "
        f"Style: {profile.get('prompt_style', '')}."
    )

    image_bytes = base_image_path.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    request = {
        "model": args.model,
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_b64,
                        }
                    },
                    {"text": prompt},
                ],
            }
        ],
        "generation_config": {
            "response_modalities": ["IMAGE"],
        },
    }

    if args.output == "-":
        print(json.dumps(request, indent=2))
    else:
        Path(args.output).write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

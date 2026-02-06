#!/usr/bin/env python3
import argparse
from pathlib import Path

from store_utils import atomic_write_json, append_jsonl, store_lock, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a Spritelet state store")
    parser.add_argument("--root", required=True, help="Spritelet identity root directory")
    parser.add_argument("--base-image", default="assets/base.png", help="Path to base reference image")
    args = parser.parse_args()

    root = Path(args.root)
    (root / "states").mkdir(parents=True, exist_ok=True)
    (root / "signals").mkdir(parents=True, exist_ok=True)
    base_image_path = Path(args.base_image)
    if not base_image_path.is_absolute():
        (root / base_image_path).parent.mkdir(parents=True, exist_ok=True)

    with store_lock(root):
        profile = {
            "base_image_path": args.base_image,
            "prompt_style": "cute animal mascot, clean lines, expressive face, transparent background",
            "created_at": utc_now(),
        }
        atomic_write_json(root / "spritelet.json", profile)

        current = {
            "spritelet_path": "",
            "updated_at": utc_now(),
        }
        atomic_write_json(root / "signals" / "current.json", current)
        atomic_write_json(root / "states" / "catalog.json", {"states": {}})
        event_line = {
            "type": "state_initialized",
            "spritelet_path": current["spritelet_path"],
            "updated_at": current["updated_at"],
        }
        append_jsonl(root / "signals" / "events.jsonl", event_line)

    print(f"Initialized Spritelet store at {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from store_utils import (
    append_jsonl,
    atomic_write_json,
    resolve_store_path,
    store_lock,
    utc_now,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update current published Spritelet image")
    parser.add_argument("--root", required=True, help="Spritelet identity root")
    parser.add_argument("--spritelet-path", required=True, help="Path to the image currently shown to users")
    args = parser.parse_args()

    root = Path(args.root)
    current_path = root / "signals" / "current.json"
    events_path = root / "signals" / "events.jsonl"
    if not current_path.exists():
        raise SystemExit(f"Missing {current_path}; run init_spritelet_store.py first")
    spritelet_abs = resolve_store_path(root, args.spritelet_path)
    if not spritelet_abs.exists():
        raise SystemExit(f"spritelet_path does not exist: {args.spritelet_path}")

    updated_at = utc_now()
    current = {"spritelet_path": args.spritelet_path, "updated_at": updated_at}
    with store_lock(root):
        atomic_write_json(current_path, current)
        append_jsonl(
            events_path,
            {
                "type": "current_spritelet_updated",
                "spritelet_path": args.spritelet_path,
                "updated_at": updated_at,
            },
        )

    print(json.dumps(current, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

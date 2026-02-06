#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from store_utils import (
    append_jsonl,
    atomic_write_json,
    normalize_simple_name,
    resolve_store_path,
    store_lock,
    utc_now,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Register or update a state image in Spritelet catalog")
    parser.add_argument("--root", required=True, help="Spritelet identity root")
    parser.add_argument("--simple-name", required=True, help="Simple state name, for example 'focused coding'")
    parser.add_argument("--spritelet-path", required=True, help="Path to state image, for example states/focused-coding.png")
    parser.add_argument("--description", required=True, help="Short description of the state")
    args = parser.parse_args()

    root = Path(args.root)
    catalog_path = root / "states" / "catalog.json"
    events_path = root / "signals" / "events.jsonl"
    if not catalog_path.exists():
        raise SystemExit(f"Missing {catalog_path}; run init_spritelet_store.py first")
    spritelet_abs = resolve_store_path(root, args.spritelet_path)
    if not spritelet_abs.exists():
        raise SystemExit(f"spritelet_path does not exist: {args.spritelet_path}")

    with store_lock(root):
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        key = normalize_simple_name(args.simple_name)
        now = utc_now()

        existing = catalog.setdefault("states", {}).get(key, {})
        created_at = existing.get("created_at", now)

        entry = {
            "simple_name": key,
            "spritelet_path": args.spritelet_path,
            "created_at": created_at,
            "description": args.description,
        }
        catalog["states"][key] = entry
        atomic_write_json(catalog_path, catalog)

        append_jsonl(
            events_path,
            {
                "type": "state_catalog_upserted",
                "simple_name": key,
                "spritelet_path": args.spritelet_path,
                "updated_at": now,
            },
        )

    print(json.dumps(entry, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from store_utils import normalize_simple_name


def main() -> int:
    parser = argparse.ArgumentParser(description="Find a state in Spritelet catalog")
    parser.add_argument("--root", required=True, help="Spritelet identity root")
    parser.add_argument("--simple-name", required=True, help="Simple state name, for example 'focused coding'")
    args = parser.parse_args()

    root = Path(args.root)
    catalog_path = root / "states" / "catalog.json"
    if not catalog_path.exists():
        raise SystemExit(f"Missing {catalog_path}; run init_spritelet_store.py first")

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    key = normalize_simple_name(args.simple_name)
    states = catalog.get("states", {})
    found = states.get(key)

    if not found:
        print(json.dumps({"found": False, "simple_name": key}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "found": True,
                "simple_name": key,
                "state": found,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

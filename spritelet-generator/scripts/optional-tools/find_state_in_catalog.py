#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from store_utils import normalize_simple_name


def parse_utc_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


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

    base_image_rel = (
        json.loads((root / "spritelet.json").read_text(encoding="utf-8")).get("base_image_path", "")
        if (root / "spritelet.json").exists()
        else ""
    )
    base_image_abs = Path(base_image_rel)
    if base_image_rel and not base_image_abs.is_absolute():
        base_image_abs = (root / base_image_abs).resolve()

    state_created_at = parse_utc_timestamp(found.get("created_at", ""))
    base_image_mtime = None
    if base_image_rel and base_image_abs.exists():
        base_image_mtime = datetime.fromtimestamp(base_image_abs.stat().st_mtime, tz=timezone.utc)

    base_image_is_newer = bool(
        base_image_mtime is not None and state_created_at is not None and base_image_mtime > state_created_at
    )
    state_is_stale = base_image_is_newer or state_created_at is None
    would_reuse_on_publish = not state_is_stale

    print(
        json.dumps(
            {
                "found": True,
                "simple_name": key,
                "base_image_path": base_image_rel,
                "base_image_mtime": base_image_mtime.isoformat().replace("+00:00", "Z") if base_image_mtime else None,
                "state_created_at": found.get("created_at"),
                "base_image_is_newer": base_image_is_newer,
                "state_is_stale": state_is_stale,
                "would_reuse_on_publish": would_reuse_on_publish,
                "state": found,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

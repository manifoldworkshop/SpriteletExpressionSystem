#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from store_utils import atomic_write_json, store_lock, utc_now


def remove_tree_contents(root: Path, relative_dir: str) -> tuple[int, int]:
    target = root / relative_dir
    target.mkdir(parents=True, exist_ok=True)

    files_removed = 0
    dirs_removed = 0

    for path in sorted(target.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink()
            files_removed += 1
        elif path.is_dir():
            try:
                path.rmdir()
                dirs_removed += 1
            except OSError:
                # Non-empty directories are left in place.
                pass

    return files_removed, dirs_removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset a Spritelet identity store to clean starting conditions")
    parser.add_argument("--root", required=True, help="Spritelet identity root directory")
    parser.add_argument("--base-image", default="assets/base.png", help="Default base image path for reset profile")
    parser.add_argument(
        "--prompt-style",
        default="cute animal mascot, clean lines, expressive face",
        help="Default prompt style for reset profile",
    )
    args = parser.parse_args()

    root = Path(args.root)
    (root / "assets").mkdir(parents=True, exist_ok=True)
    (root / "states").mkdir(parents=True, exist_ok=True)
    (root / "signals").mkdir(parents=True, exist_ok=True)

    now = utc_now()
    with store_lock(root):
        assets_files_removed, assets_dirs_removed = remove_tree_contents(root, "assets")
        states_files_removed, states_dirs_removed = remove_tree_contents(root, "states")

        profile = {
            "base_image_path": args.base_image,
            "prompt_style": args.prompt_style,
            "created_at": now,
        }
        atomic_write_json(root / "spritelet.json", profile)
        atomic_write_json(root / "signals" / "current.json", {"spritelet_path": "", "updated_at": now})
        atomic_write_json(root / "states" / "catalog.json", {"states": {}})

        events_path = root / "signals" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(
            json.dumps(
                {
                    "type": "state_initialized",
                    "spritelet_path": "",
                    "updated_at": now,
                }
            )
            + "\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "reinitialized": True,
                "root": str(root),
                "files_removed": {
                    "assets": assets_files_removed,
                    "states": states_files_removed,
                    "total": assets_files_removed + states_files_removed,
                },
                "dirs_removed": {
                    "assets": assets_dirs_removed,
                    "states": states_dirs_removed,
                    "total": assets_dirs_removed + states_dirs_removed,
                },
                "reset_files": [
                    "spritelet.json",
                    "signals/current.json",
                    "signals/events.jsonl",
                    "states/catalog.json",
                ],
                "updated_at": now,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import fcntl


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def normalize_simple_name(name: str) -> str:
    return "-".join(name.strip().lower().split())


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def ensure_state_relative_path(path_str: str) -> None:
    if Path(path_str).is_absolute():
        raise SystemExit("spritelet_path must be relative, not absolute")
    normalized = path_str.replace('\\', '/')
    if not normalized.startswith("states/"):
        raise SystemExit("spritelet_path must stay inside states/")


def resolve_store_path(root: Path, relative_path: str) -> Path:
    ensure_state_relative_path(relative_path)
    abs_path = (root / relative_path).resolve()
    states_root = (root / "states").resolve()
    if states_root not in abs_path.parents and abs_path != states_root:
        raise SystemExit("spritelet_path escapes states/")
    return abs_path


@contextmanager
def store_lock(root: Path):
    lock_dir = root / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "store.lock"
    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

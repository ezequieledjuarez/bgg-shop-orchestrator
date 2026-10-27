#!/usr/bin/env python3
"""Load and print the orchestrator agent->task mapping.

Usage:
  python "0. Orchestrator/load_agent_mapping.py" --print
  python "0. Orchestrator/load_agent_mapping.py" --path "0. Orchestrator/agent_task_mapping.json"

This script is intentionally minimal so the orchestrator can import `load_mapping()`.
"""
import json
import argparse
import threading
import time
from pathlib import Path

# Module-level cache for mapping and mtime
_cached_mapping = None
_cached_path = None
_cached_mtime = None
_cache_lock = threading.Lock()


def _read_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_mapping(path: str = None, use_cache: bool = True):
    """Load mapping JSON with optional hot-reload by checking mtime.

    - If use_cache is True, returns cached mapping and reloads when file mtime changes.
    - If use_cache is False, reads from disk every call.
    """
    global _cached_mapping, _cached_path, _cached_mtime
    base = Path(__file__).parent
    json_path = Path(path) if path else base / "agent_task_mapping.json"
    if not json_path.exists():
        # Try alternate location (space in folder)
        alt = base / "agent_task_mapping.json"
        json_path = alt

    if not use_cache:
        return _read_json(json_path)

    with _cache_lock:
        try:
            mtime = json_path.stat().st_mtime
        except Exception:
            # If the file disappears, return cached mapping if available
            if _cached_mapping is not None:
                return _cached_mapping
            raise

        if _cached_mapping is None or _cached_path != str(json_path) or _cached_mtime != mtime:
            # reload
            mapping = _read_json(json_path)
            _cached_mapping = mapping
            _cached_path = str(json_path)
            _cached_mtime = mtime

    return _cached_mapping


def reload_mapping(path: str = None):
    """Force reload the mapping from disk ignoring cache."""
    return load_mapping(path=path, use_cache=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--path", help="Custom path to mapping JSON", default=None)
    p.add_argument("--print", help="Pretty-print mapping to stdout", action="store_true")
    p.add_argument("--no-cache", help="Do not use cache; read file from disk", action="store_true")
    args = p.parse_args()
    mapping = load_mapping(args.path, use_cache=not args.no_cache)
    if args.print:
        print(json.dumps(mapping, indent=2, ensure_ascii=False))
    else:
        # default: print short summary
        print(f"Agent mapping version: {mapping.get('version')}")
        for proj, info in mapping.get("projects", {}).items():
            print(f"- {proj}: {', '.join(info.get('tasks', {}).keys())}")


if __name__ == "__main__":
    main()

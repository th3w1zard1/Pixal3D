#!/usr/bin/env python3
"""Validate a pixal3d-generation-run/1 JSON manifest file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "pixal3d-generation-run/1"
REQUIRED_KEYS = (
    "schema_version",
    "run_id",
    "finished_at",
    "git_head",
    "session_id",
    "glb_path",
    "extract_available",
    "preview_available",
    "rembg_model",
    "requested_resolution",
    "effective_resolution",
)


def validate_generation_run(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required field: {key}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    if "run_id" in data and not isinstance(data.get("run_id"), str):
        errors.append("run_id must be a string")

    for nullable_str in ("git_head", "glb_path", "rembg_model", "session_id", "finished_at"):
        if nullable_str in data and data[nullable_str] is not None and not isinstance(
            data[nullable_str], str
        ):
            errors.append(f"{nullable_str} must be a string or null")

    for nullable_bool in ("extract_available", "preview_available"):
        if nullable_bool in data and data[nullable_bool] is not None and not isinstance(
            data[nullable_bool], bool
        ):
            errors.append(f"{nullable_bool} must be a boolean or null")

    for nullable_int in ("requested_resolution", "effective_resolution"):
        if nullable_int in data and data[nullable_int] is not None and not isinstance(
            data[nullable_int], int
        ):
            errors.append(f"{nullable_int} must be an integer or null")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pixal3d-generation-run/1 JSON manifest.")
    parser.add_argument("path", type=Path, help="Generation run manifest JSON file")
    args = parser.parse_args(argv)

    try:
        raw = args.path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except FileNotFoundError:
        print(f"file not found: {args.path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2

    errors = validate_generation_run(data)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"OK: {args.path} ({SCHEMA_VERSION})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

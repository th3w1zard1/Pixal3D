#!/usr/bin/env python3
"""Validate a pixal3d-generation-smoke/1 JSON manifest file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "pixal3d-generation-smoke/1"
REQUIRED_KEYS = (
    "schema_version",
    "checked_at",
    "git_head",
    "url",
    "generate_ok",
    "glb_path",
    "extract_available",
    "warmup_skipped",
    "generate_error",
)


def validate_generation_manifest(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required field: {key}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    if "generate_ok" in data and not isinstance(data["generate_ok"], bool):
        errors.append("generate_ok must be a boolean")

    if "warmup_skipped" in data and data["warmup_skipped"] is not None and not isinstance(
        data["warmup_skipped"], bool
    ):
        errors.append("warmup_skipped must be a boolean or null")

    for nullable_str in ("git_head", "glb_path", "generate_error"):
        if nullable_str in data and data[nullable_str] is not None and not isinstance(
            data[nullable_str], str
        ):
            errors.append(f"{nullable_str} must be a string or null")

    if "extract_available" in data and data["extract_available"] is not None and not isinstance(
        data["extract_available"], bool
    ):
        errors.append("extract_available must be a boolean or null")

    if "checked_at" in data and not isinstance(data.get("checked_at"), str):
        errors.append("checked_at must be a string")

    if "url" in data and not isinstance(data.get("url"), str):
        errors.append("url must be a string")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pixal3d-generation-smoke/1 JSON manifest.")
    parser.add_argument("path", type=Path, help="Generation manifest JSON file")
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

    errors = validate_generation_manifest(data)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"OK: {args.path} ({SCHEMA_VERSION})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

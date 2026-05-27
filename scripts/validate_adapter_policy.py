#!/usr/bin/env python3
"""Validate a pixal3d-adapter-policy/1 JSON policy file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "pixal3d-adapter-policy/1"
REQUIRED_ROOT_KEYS = ("schema_version", "adapters")
ADAPTER_KEYS = ("id", "license_spdx", "enabled")


def validate_adapter_policy(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    for key in REQUIRED_ROOT_KEYS:
        if key not in data:
            errors.append(f"missing required field: {key}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    adapters = data.get("adapters")
    if adapters is not None and not isinstance(adapters, list):
        errors.append("adapters must be an array")
        return errors

    if isinstance(adapters, list):
        for index, entry in enumerate(adapters):
            prefix = f"adapters[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be an object")
                continue
            for key in ADAPTER_KEYS:
                if key not in entry:
                    errors.append(f"{prefix} missing required field: {key}")
            if "id" in entry and not isinstance(entry["id"], str):
                errors.append(f"{prefix}.id must be a string")
            if "license_spdx" in entry and entry["license_spdx"] is not None and not isinstance(
                entry["license_spdx"], str
            ):
                errors.append(f"{prefix}.license_spdx must be a string or null")
            if "enabled" in entry and not isinstance(entry["enabled"], bool):
                errors.append(f"{prefix}.enabled must be a boolean")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pixal3d-adapter-policy/1 JSON policy.")
    parser.add_argument("path", type=Path, help="Adapter policy JSON file")
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

    errors = validate_adapter_policy(data)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"OK: {args.path} ({SCHEMA_VERSION})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

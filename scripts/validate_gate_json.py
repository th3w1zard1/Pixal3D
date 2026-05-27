#!/usr/bin/env python3
"""Validate a pixal3d-agent-gate/3 JSON summary file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "pixal3d-agent-gate/3"
REQUIRED_KEYS = (
    "schema_version",
    "checked_at",
    "git_head",
    "url",
    "parity_ok",
    "health_ok",
    "browser_ran",
    "browser_exit",
    "space_repo_git_head",
    "repo_git_head_match",
    "adapter_policy_ok",
    "adapter_policy_enabled_count",
    "overall_ok",
)


def validate_gate_summary(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required field: {key}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    for bool_key in ("parity_ok", "health_ok", "browser_ran", "overall_ok"):
        if bool_key in data and not isinstance(data[bool_key], bool):
            errors.append(f"{bool_key} must be a boolean")

    if "browser_exit" in data:
        be = data["browser_exit"]
        if be is not None and not isinstance(be, int):
            errors.append("browser_exit must be an integer or null")

    if "git_head" in data and data["git_head"] is not None and not isinstance(data["git_head"], str):
        errors.append("git_head must be a string or null")

    if "checked_at" in data and not isinstance(data.get("checked_at"), str):
        errors.append("checked_at must be a string")

    if "url" in data and not isinstance(data.get("url"), str):
        errors.append("url must be a string")

    if "space_repo_git_head" in data and data["space_repo_git_head"] is not None and not isinstance(
        data["space_repo_git_head"], str
    ):
        errors.append("space_repo_git_head must be a string or null")

    if "repo_git_head_match" in data and data["repo_git_head_match"] is not None and not isinstance(
        data["repo_git_head_match"], bool
    ):
        errors.append("repo_git_head_match must be a boolean or null")

    if "adapter_policy_ok" in data and data["adapter_policy_ok"] is not None and not isinstance(
        data["adapter_policy_ok"], bool
    ):
        errors.append("adapter_policy_ok must be a boolean or null")

    if "adapter_policy_enabled_count" in data and data[
        "adapter_policy_enabled_count"
    ] is not None and not isinstance(data["adapter_policy_enabled_count"], int):
        errors.append("adapter_policy_enabled_count must be an integer or null")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pixal3d-agent-gate/3 JSON summary.")
    parser.add_argument("path", type=Path, help="Gate summary JSON file")
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

    errors = validate_gate_summary(data)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"OK: {args.path} ({SCHEMA_VERSION})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

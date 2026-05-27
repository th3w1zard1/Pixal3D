#!/usr/bin/env python3
"""Check adapter policy file shape and enabled-adapter license requirements."""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from validate_adapter_policy import validate_adapter_policy

DEFAULT_POLICY = Path(__file__).resolve().parents[1] / "docs" / "adapters" / "policy.example.json"
CHECK_SCHEMA_VERSION = "pixal3d-adapter-policy-check/1"


def _git_short_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def evaluate_policy(data: dict[str, Any]) -> tuple[bool, list[str]]:
    violations: list[str] = []
    adapters = data.get("adapters")
    if not isinstance(adapters, list):
        return False, ["adapters must be an array"]

    for index, entry in enumerate(adapters):
        if not isinstance(entry, dict):
            violations.append(f"adapters[{index}] must be an object")
            continue
        adapter_id = entry.get("id", f"adapters[{index}]")
        if entry.get("enabled") is True:
            license_spdx = entry.get("license_spdx")
            if not license_spdx or not str(license_spdx).strip():
                violations.append(f"{adapter_id}: enabled adapter missing license_spdx")

    return len(violations) == 0, violations


def build_check_summary(policy_path: Path, policy_ok: bool, violations: list[str]) -> dict[str, Any]:
    checked_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "schema_version": CHECK_SCHEMA_VERSION,
        "checked_at": checked_at,
        "git_head": _git_short_head(),
        "policy_path": str(policy_path),
        "policy_ok": policy_ok,
        "violations": violations,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check pixal3d-adapter-policy/1 file and print a JSON summary on stdout.",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=DEFAULT_POLICY,
        help="Adapter policy JSON path (default: docs/adapters/policy.example.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    policy_path = args.policy.expanduser().resolve()

    try:
        data = json.loads(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(json.dumps({"error": f"file not found: {policy_path}"}))
        return 2
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid JSON: {exc}"}))
        return 2

    schema_errors = validate_adapter_policy(data)
    if schema_errors:
        summary = build_check_summary(policy_path, False, schema_errors)
        print(json.dumps(summary, indent=2))
        return 1

    policy_ok, violations = evaluate_policy(data)
    summary = build_check_summary(policy_path, policy_ok, violations)
    print(json.dumps(summary, indent=2))
    return 0 if policy_ok else 1


if __name__ == "__main__":
    sys.exit(main())

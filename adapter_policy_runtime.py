"""Runtime adapter policy evaluation for rembg Hub model selection."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from scripts.validate_adapter_policy import validate_adapter_policy

_DEFAULT_POLICY = Path(__file__).resolve().parent / "docs" / "adapters" / "policy.example.json"

_POLICY_STATUS: dict[str, Any] = {
    "adapter_policy_path": None,
    "adapter_policy_ok": True,
    "adapter_policy_enforced": False,
    "adapter_policy_violations": [],
    "adapter_policy_enabled_count": 0,
}


def default_policy_path() -> Path:
    return _DEFAULT_POLICY


def _policy_enforced(env: dict[str, str]) -> bool:
    return env.get("PIXAL3D_ADAPTER_POLICY_ENFORCE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def resolve_policy_path(env: dict[str, str]) -> Path:
    explicit = env.get("PIXAL3D_ADAPTER_POLICY", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return default_policy_path()


def _enabled_hub_repos(policy: dict[str, Any]) -> list[str]:
    adapters = policy.get("adapters")
    if not isinstance(adapters, list):
        return []
    repos: list[str] = []
    for entry in adapters:
        if not isinstance(entry, dict) or entry.get("enabled") is not True:
            continue
        hub_repo = entry.get("hub_repo")
        if isinstance(hub_repo, str) and hub_repo.strip():
            repos.append(hub_repo.strip())
    return repos


def evaluate_rembg_models(
    env: dict[str, str],
    rembg_models: list[str],
) -> dict[str, Any]:
    path = resolve_policy_path(env)
    enforced = _policy_enforced(env)
    violations: list[str] = []
    enabled_count = 0
    policy_ok = True

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except FileNotFoundError:
        violations = [f"policy file not found: {path}"]
        policy_ok = not enforced
        status = {
            "adapter_policy_path": str(path),
            "adapter_policy_ok": policy_ok,
            "adapter_policy_enforced": enforced,
            "adapter_policy_violations": violations,
            "adapter_policy_enabled_count": 0,
        }
        _POLICY_STATUS.update(status)
        if enforced:
            raise RuntimeError("; ".join(violations))
        return status

    schema_errors = validate_adapter_policy(data)
    if schema_errors:
        violations = schema_errors
        policy_ok = False
    else:
        allowed = _enabled_hub_repos(data)
        enabled_count = len(allowed)
        if allowed:
            for model in rembg_models:
                if model and model not in allowed:
                    violations.append(
                        f"rembg model {model!r} not in enabled adapter hub_repo list"
                    )
            policy_ok = len(violations) == 0

    status = {
        "adapter_policy_path": str(path),
        "adapter_policy_ok": policy_ok,
        "adapter_policy_enforced": enforced,
        "adapter_policy_violations": violations,
        "adapter_policy_enabled_count": enabled_count,
    }
    _POLICY_STATUS.update(status)
    if enforced and enabled_count > 0 and not policy_ok:
        raise RuntimeError(
            "adapter policy enforcement failed: " + "; ".join(violations)
        )
    return status


def policy_status_snapshot() -> dict[str, Any]:
    return dict(_POLICY_STATUS)

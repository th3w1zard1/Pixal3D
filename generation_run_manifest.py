"""Build pixal3d-generation-run/1 manifests for successful /generate_3d responses."""

from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any

GENERATION_RUN_SCHEMA = "pixal3d-generation-run/1"


def _git_short_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def build_generation_run_manifest(
    session_id: str,
    result: dict[str, Any],
    *,
    rembg_model: str | None = None,
) -> dict[str, Any]:
    finished_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    glb_path = result.get("glb_path")
    return {
        "schema_version": GENERATION_RUN_SCHEMA,
        "run_id": str(uuid.uuid4()),
        "finished_at": finished_at,
        "git_head": _git_short_head(),
        "session_id": session_id,
        "glb_path": glb_path if isinstance(glb_path, str) else None,
        "extract_available": result.get("extract_available")
        if isinstance(result.get("extract_available"), bool)
        else None,
        "preview_available": result.get("preview_available")
        if isinstance(result.get("preview_available"), bool)
        else None,
        "rembg_model": rembg_model,
        "requested_resolution": result.get("requested_resolution"),
        "effective_resolution": result.get("effective_resolution"),
    }


def attach_generation_run_manifest(
    session_id: str,
    result: dict[str, Any],
    *,
    rembg_model: str | None = None,
) -> dict[str, Any]:
    if result.get("error"):
        return result
    if not result.get("glb_path") and not result.get("render_paths"):
        return result
    result = dict(result)
    result["generation_run"] = build_generation_run_manifest(
        session_id, result, rembg_model=rembg_model
    )
    return result

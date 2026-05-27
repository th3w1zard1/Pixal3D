#!/usr/bin/env python3
"""Smoke checks for the hosted Pixal3D Hugging Face Space."""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

GENERATION_MANIFEST_SCHEMA = "pixal3d-generation-smoke/1"

DEFAULT_SPACE_URL = "https://th3w1zard1-pixal3d.hf.space/"
DEFAULT_SAMPLE = Path(__file__).resolve().parents[1] / "assets" / "images" / "0_img.png"
SMOKE_SESSION_ID = "space-smoke"
# Match hosted ZeroGPU caps and the UI fast export profile (512 texture path).
ZEROGPU_SMOKE_RESOLUTION = 512
ZEROGPU_SMOKE_STAGE_STEPS = 5
SMOKE_REQUIREMENTS = Path(__file__).resolve().parent / "smoke-requirements.txt"
HTML_MARKERS = (
    "runtime-signin-link",
    "GPU slice ended early",
    "lastRuntimeReady",
    "ZeroGPU cold start",
    "512 (Fast / ZeroGPU)",
    'data-smoke-default-sample="assets/images/0_img.png"',
)


def _fetch_json(url: str, timeout: float) -> tuple[int, dict[str, Any] | None, str | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, json.loads(body), None
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")
            payload = json.loads(body) if body.strip() else None
        except json.JSONDecodeError:
            payload = None
        return exc.code, payload, str(exc)
    except Exception as exc:  # noqa: BLE001 - smoke script surfaces all transport errors
        return 0, None, str(exc)


def _fetch_text(url: str, timeout: float) -> tuple[int, str | None, str | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace"), None
    except Exception as exc:  # noqa: BLE001
        return 0, None, str(exc)


def check_health(base_url: str, timeout: float) -> dict[str, Any]:
    base = base_url.rstrip("/") + "/"
    health_status, health_body, health_err = _fetch_json(base + "health", timeout)
    ready_status, ready_body, ready_err = _fetch_json(base + "ready", timeout)
    return {
        "health_status": health_status,
        "health": health_body,
        "health_error": health_err,
        "ready_status": ready_status,
        "ready": ready_body,
        "ready_error": ready_err,
    }


def zerogpu_health_ok(health: dict[str, Any] | None) -> tuple[bool, str | None]:
    """Assert recovery-critical fields when the hosted Space reports ZeroGPU mode."""
    if not isinstance(health, dict) or health.get("runtime_mode") != "zerogpu":
        return True, None
    rembg = health.get("rembg_model") or ""
    if "BiRefNet_lite" not in rembg:
        return False, f"rembg_model expected BiRefNet_lite, got {rembg!r}"
    prefetch = health.get("hub_prefetch_state")
    if prefetch not in ("ready", "running"):
        return False, f"hub_prefetch_state expected ready|running, got {prefetch!r}"
    if health.get("cuda_mesh_operators") is not True:
        return False, "cuda_mesh_operators is not true"
    budgets = health.get("zerogpu_gpu_budgets")
    if not isinstance(budgets, dict):
        return False, "zerogpu_gpu_budgets missing"
    cold = budgets.get("cold_generation_max_seconds")
    if cold != 120:
        return False, f"cold_generation_max_seconds expected 120, got {cold!r}"
    return True, None


def adapter_policy_health_ok(health: dict[str, Any] | None) -> tuple[bool, str | None]:
    if not isinstance(health, dict) or "adapter_policy_ok" not in health:
        return True, None
    if health.get("adapter_policy_ok") is True:
        return True, None
    return False, f"adapter_policy_ok false ({health.get('adapter_policy_violations')!r})"


def check_html(base_url: str, timeout: float) -> dict[str, Any]:
    status, html, err = _fetch_text(base_url.rstrip("/") + "/", timeout)
    if err or not html:
        return {"html_status": status, "html_error": err, "markers": {}, "markers_ok": False}
    markers = {marker: marker in html for marker in HTML_MARKERS}
    return {
        "html_status": status,
        "html_error": err,
        "markers": markers,
        "markers_ok": all(markers.values()),
    }


def gradio_client_install_hint() -> str:
    req_path = SMOKE_REQUIREMENTS
    return (
        "gradio_client is required for --generate. On PEP 668 hosts, use a venv:\n"
        "  python3 -m venv .venv\n"
        f"  .venv/bin/pip install -r {req_path}\n"
        "  .venv/bin/python scripts/space_smoke.py --generate"
    )


def gradio_client_import_error(exc: ImportError) -> dict[str, Any]:
    return {
        "warmup_ok": False,
        "warmup_error": f"gradio_client not installed: {exc}\n{gradio_client_install_hint()}",
        "generate_ok": False,
    }


def run_warmup(client: Any, session_id: str) -> dict[str, Any]:
    try:
        result = client.predict(api_name="/warmup_runtime", session_id=session_id)
    except Exception as exc:  # noqa: BLE001
        return {"warmup_ok": False, "warmup_error": str(exc)}
    if isinstance(result, dict) and result.get("error"):
        return {
            "warmup_ok": False,
            "warmup_error": str(result["error"]),
            "warmup_result": result,
        }
    return {"warmup_ok": True, "warmup_result": result}


def format_client_error(exc: Exception) -> str:
    message = str(exc).strip()
    if message and message not in {"RuntimeError", "Error"}:
        return message
    return f"{type(exc).__name__}: {message or 'no message from upstream (check /progress)'}"


def fetch_progress_snapshot(base_url: str, session_id: str, timeout: float) -> dict[str, Any] | None:
    status, body, _err = _fetch_json(
        f"{base_url.rstrip('/')}/progress?session_id={session_id}",
        timeout,
    )
    if status == 200 and isinstance(body, dict):
        return body
    return None


def generation_has_deliverable(payload: Any) -> bool:
    if not isinstance(payload, dict) or payload.get("error"):
        return False
    if payload.get("glb_path"):
        return True
    render_paths = payload.get("render_paths")
    return isinstance(render_paths, dict) and bool(render_paths)


def generation_run_manifest_ok(payload: Any) -> tuple[bool, str | None]:
    if not isinstance(payload, dict):
        return False, "generate result is not a dict"
    manifest = payload.get("generation_run")
    if not isinstance(manifest, dict):
        return False, "missing generation_run manifest on generate result"
    if manifest.get("schema_version") != "pixal3d-generation-run/1":
        return False, f"unexpected generation_run schema: {manifest.get('schema_version')!r}"
    if not manifest.get("run_id"):
        return False, "generation_run.run_id is empty"
    return True, None


def run_generate(client: Any, sample: Path, session_id: str, base_url: str = DEFAULT_SPACE_URL) -> dict[str, Any]:
    if not sample.is_file():
        return {"generate_ok": False, "generate_error": f"sample not found: {sample}"}
    try:
        from gradio_client import handle_file
    except ImportError as exc:
        return {
            "generate_ok": False,
            "generate_error": f"gradio_client not installed: {exc}\n{gradio_client_install_hint()}",
        }

    try:
        result = client.predict(
            handle_file(str(sample)),
            42,
            ZEROGPU_SMOKE_RESOLUTION,
            7.5,
            0.7,
            ZEROGPU_SMOKE_STAGE_STEPS,
            5.0,
            7.5,
            0.5,
            ZEROGPU_SMOKE_STAGE_STEPS,
            3.0,
            1.0,
            0.0,
            ZEROGPU_SMOKE_STAGE_STEPS,
            3.0,
            -1.0,
            "deg",
            session_id,
            api_name="/generate_3d",
        )
    except Exception as exc:  # noqa: BLE001
        progress = fetch_progress_snapshot(base_url, session_id, 30.0)
        error = format_client_error(exc)
        if progress:
            stage = progress.get("stage")
            if stage:
                error = f"{error} (progress stage: {stage})"
        return {"generate_ok": False, "generate_error": error, "progress": progress}

    if isinstance(result, dict) and result.get("error"):
        return {"generate_ok": False, "generate_error": str(result["error"]), "generate_result": result}
    if not generation_has_deliverable(result):
        return {
            "generate_ok": False,
            "generate_error": "generate_3d returned no glb_path or render_paths",
            "generate_result": result,
        }
    if (
        isinstance(result, dict)
        and result.get("glb_path")
        and result.get("extract_available") is False
    ):
        return {
            "generate_ok": False,
            "generate_error": "generate_3d returned glb_path but extract_available=false",
            "generate_result": result,
        }
    mr_ok, mr_err = generation_run_manifest_ok(result)
    if not mr_ok:
        return {
            "generate_ok": False,
            "generate_error": mr_err,
            "generate_result": result,
        }
    return {"generate_ok": True, "generate_result": result}


def should_skip_warmup(health: dict[str, Any] | None) -> bool:
    return bool(health and health.get("runtime_mode") == "zerogpu")


def _git_short_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def build_generation_manifest(url: str, generate_check: dict[str, Any]) -> dict[str, Any]:
    result = generate_check.get("generate_result")
    glb_path: str | None = None
    extract_available: bool | None = None
    if isinstance(result, dict):
        raw_glb = result.get("glb_path")
        if isinstance(raw_glb, str):
            glb_path = raw_glb
        raw_extract = result.get("extract_available")
        if isinstance(raw_extract, bool):
            extract_available = raw_extract

    generate_error = generate_check.get("generate_error")
    if not isinstance(generate_error, str):
        generate_error = None

    warmup_skipped = generate_check.get("warmup_skipped")
    if warmup_skipped is not None and not isinstance(warmup_skipped, bool):
        warmup_skipped = None

    checked_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "schema_version": GENERATION_MANIFEST_SCHEMA,
        "checked_at": checked_at,
        "git_head": _git_short_head(),
        "url": url.rstrip("/") + "/",
        "generate_ok": bool(generate_check.get("generate_ok")),
        "glb_path": glb_path,
        "extract_available": extract_available,
        "warmup_skipped": warmup_skipped,
        "generate_error": generate_error,
    }


def write_generation_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def validate_generation_manifest_file(path: Path) -> int:
    validator = Path(__file__).resolve().parent / "validate_generation_manifest.py"
    return subprocess.call([sys.executable, str(validator), str(path)])


def run_warmup_and_generate(base_url: str, sample: Path, session_id: str) -> dict[str, Any]:
    try:
        from gradio_client import Client
    except ImportError as exc:
        return gradio_client_import_error(exc)

    base = base_url.rstrip("/") + "/"
    client = Client(base)
    health_status, health_body, _health_err = _fetch_json(base + "health", 30.0)
    skip_warmup = should_skip_warmup(health_body if health_status == 200 else None)
    warmup: dict[str, Any] = {
        "warmup_skipped": skip_warmup,
        "warmup_skip_reason": "runtime_mode=zerogpu matches hosted UI flow",
    }
    if not skip_warmup:
        warmup = run_warmup(client, session_id)
        if not warmup.get("warmup_ok"):
            return {**warmup, "generate_ok": False}
    generate = run_generate(client, sample, session_id, base_url=base)
    return {**warmup, **generate}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-check the hosted Pixal3D Space (health, ready, HTML markers, optional generate).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/space_smoke.py --health-only --html-check
  python scripts/space_smoke.py --url https://th3w1zard1-pixal3d.hf.space/ --generate
  python scripts/space_smoke.py --generate --write-manifest docs/generation-manifests/latest.json

`--generate` uses ZeroGPU-safe defaults (512 resolution, 5 stage steps). On hosted
ZeroGPU it skips `/warmup_runtime` and calls `/generate_3d` directly, matching the
browser UI. Other runtimes still warm up first. Requires gradio_client — see
scripts/smoke-requirements.txt. Anonymous cold runs typically take ~2–3 minutes and return a
geometry-only GLB on ZeroGPU; sign in on the Space for preview frames and textured extract.
        """.strip(),
    )
    parser.add_argument("--url", default=DEFAULT_SPACE_URL, help="Space base URL")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout seconds")
    parser.add_argument("--health-only", action="store_true", help="Skip optional generate")
    parser.add_argument("--html-check", action="store_true", help="Verify served index.html markers")
    parser.add_argument("--generate", action="store_true", help="Run sample generate via gradio_client")
    parser.add_argument(
        "--sample",
        type=Path,
        default=DEFAULT_SAMPLE,
        help="Sample image for --generate",
    )
    parser.add_argument(
        "--generate-timeout",
        type=float,
        default=600.0,
        help="Unused when using blocking predict; kept for future queue polling",
    )
    parser.add_argument(
        "--write-manifest",
        type=Path,
        metavar="PATH",
        help="Write pixal3d-generation-smoke/1 JSON after --generate (requires --generate)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.write_manifest is not None and not args.generate:
        parser.error("--write-manifest requires --generate")
    summary: dict[str, Any] = {"url": args.url.rstrip("/") + "/"}

    health = check_health(args.url, args.timeout)
    summary["health_check"] = health
    health_ok = health["health_status"] == 200 and health["health"] is not None
    if not health_ok:
        print(json.dumps(summary, indent=2))
        return 1

    z_ok, z_err = zerogpu_health_ok(health.get("health"))
    summary["zerogpu_health_ok"] = z_ok
    if z_err:
        summary["zerogpu_health_error"] = z_err
    if not z_ok:
        print(json.dumps(summary, indent=2))
        return 1

    ap_ok, ap_err = adapter_policy_health_ok(health.get("health"))
    summary["adapter_policy_health_ok"] = ap_ok
    if ap_err:
        summary["adapter_policy_health_error"] = ap_err
    if not ap_ok:
        print(json.dumps(summary, indent=2))
        return 1

    if args.html_check:
        html = check_html(args.url, args.timeout)
        summary["html_check"] = html
        if not html.get("markers_ok"):
            print(json.dumps(summary, indent=2))
            return 1

    if args.generate and not args.health_only:
        generate = run_warmup_and_generate(args.url, args.sample, SMOKE_SESSION_ID)
        summary["generate_check"] = generate
        if args.write_manifest is not None:
            manifest = build_generation_manifest(summary["url"], generate)
            write_generation_manifest(args.write_manifest, manifest)
            manifest_rc = validate_generation_manifest_file(args.write_manifest.expanduser().resolve())
            if manifest_rc != 0:
                return manifest_rc
        print(json.dumps(summary, indent=2, default=str))
        return 0 if generate.get("generate_ok") else 2

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

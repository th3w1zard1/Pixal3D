#!/usr/bin/env python3
"""Smoke checks for the hosted Pixal3D Hugging Face Space."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

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


def run_generate(client: Any, sample: Path, session_id: str) -> dict[str, Any]:
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
        return {"generate_ok": False, "generate_error": str(exc)}

    if isinstance(result, dict) and result.get("error"):
        return {"generate_ok": False, "generate_error": str(result["error"]), "generate_result": result}
    return {"generate_ok": True, "generate_result": result}


def should_skip_warmup(health: dict[str, Any] | None) -> bool:
    return bool(health and health.get("runtime_mode") == "zerogpu")


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
    generate = run_generate(client, sample, session_id)
    return {**warmup, **generate}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-check the hosted Pixal3D Space (health, ready, HTML markers, optional generate).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/space_smoke.py --health-only --html-check
  python scripts/space_smoke.py --url https://th3w1zard1-pixal3d.hf.space/ --generate

`--generate` uses ZeroGPU-safe defaults (512 resolution, 5 stage steps). On hosted
ZeroGPU it skips `/warmup_runtime` and calls `/generate_3d` directly, matching the
browser UI. Other runtimes still warm up first. Requires gradio_client — see
scripts/smoke-requirements.txt. Anonymous cold runs may still hit GPU slice limits;
sign in on the Space for reliable checks.
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary: dict[str, Any] = {"url": args.url.rstrip("/") + "/"}

    health = check_health(args.url, args.timeout)
    summary["health_check"] = health
    health_ok = health["health_status"] == 200 and health["health"] is not None
    if not health_ok:
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
        print(json.dumps(summary, indent=2, default=str))
        return 0 if generate.get("generate_ok") else 2

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

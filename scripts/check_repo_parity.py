#!/usr/bin/env python3
"""Compare github/main and origin/main to detect GitHub↔Hugging Face Space drift."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any


DEFAULT_GITHUB_REMOTE = "github"
DEFAULT_HF_REMOTE = "origin"
DEFAULT_BRANCH = "main"


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _fetch_remotes(*remotes: str) -> None:
    for remote in remotes:
        result = _run_git(["fetch", remote, DEFAULT_BRANCH, "--quiet"])
        if result.returncode != 0:
            raise RuntimeError(
                f"git fetch {remote} {DEFAULT_BRANCH} failed: {result.stderr.strip() or result.stdout.strip()}"
            )


def _rev_parse(ref: str) -> str:
    result = _run_git(["rev-parse", ref])
    if result.returncode != 0:
        raise RuntimeError(f"git rev-parse {ref} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def _log_oneline(ref: str, limit: int) -> list[str]:
    result = _run_git(["log", "--oneline", f"-{limit}", ref])
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def check_parity(
    github_remote: str,
    hf_remote: str,
    branch: str,
    preview_limit: int,
) -> dict[str, Any]:
    github_ref = f"refs/remotes/{github_remote}/{branch}"
    hf_ref = f"refs/remotes/{hf_remote}/{branch}"

    _fetch_remotes(github_remote, hf_remote)
    github_sha = _rev_parse(github_ref)
    hf_sha = _rev_parse(hf_ref)
    in_sync = github_sha == hf_sha

    ahead_of_hf = _log_oneline(f"{hf_ref}..{github_ref}", preview_limit) if not in_sync else []
    ahead_of_github = _log_oneline(f"{github_ref}..{hf_ref}", preview_limit) if not in_sync else []

    return {
        "github_remote": github_remote,
        "hf_remote": hf_remote,
        "branch": branch,
        "github_sha": github_sha,
        "hf_sha": hf_sha,
        "in_sync": in_sync,
        "github_ahead_of_hf": ahead_of_hf,
        "hf_ahead_of_github": ahead_of_github,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect drift between GitHub (github remote) and Hugging Face Space (origin remote).",
    )
    parser.add_argument(
        "--github-remote",
        default=DEFAULT_GITHUB_REMOTE,
        help=f"Git remote for GitHub (default: {DEFAULT_GITHUB_REMOTE})",
    )
    parser.add_argument(
        "--hf-remote",
        default=DEFAULT_HF_REMOTE,
        help=f"Git remote for Hugging Face Space (default: {DEFAULT_HF_REMOTE})",
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Branch to compare (default: {DEFAULT_BRANCH})",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=10,
        help="Max commits to list on each side when drift is detected",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON only",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = check_parity(args.github_remote, args.hf_remote, args.branch, args.preview)
    except RuntimeError as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}))
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"GitHub ({args.github_remote}/{args.branch}): {summary['github_sha']}")
        print(f"HF Space ({args.hf_remote}/{args.branch}): {summary['hf_sha']}")
        if summary["in_sync"]:
            print("Parity OK: remotes match.")
        else:
            print("Parity drift detected.")
            if summary["github_ahead_of_hf"]:
                print(f"\nCommits on {args.github_remote} not on {args.hf_remote}:")
                for line in summary["github_ahead_of_hf"]:
                    print(f"  {line}")
            if summary["hf_ahead_of_github"]:
                print(f"\nCommits on {args.hf_remote} not on {args.github_remote}:")
                for line in summary["hf_ahead_of_github"]:
                    print(f"  {line}")
            print(
                "\nRemedy: add HF_TOKEN to GitHub Actions for auto-sync, or run "
                f"`git push {args.hf_remote} {args.branch}` when local HF auth is available."
            )

    return 0 if summary["in_sync"] else 1


if __name__ == "__main__":
    sys.exit(main())

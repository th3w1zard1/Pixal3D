from __future__ import annotations

import os
from typing import Any, Mapping

from scripts.resolve_hf_space_config import resolve_space_config


def _env_flag(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _error_status_code(error: Exception) -> int | None:
    response = getattr(error, "response", None)
    return getattr(response, "status_code", None)


def ensure_space(
    api: Any,
    repo_id: str,
    sdk: str,
    *,
    private: bool = False,
    create_if_missing: bool = True,
) -> bool:
    try:
        api.repo_info(repo_id=repo_id, repo_type="space")
        print(f"Space exists: {repo_id}")
        return False
    except Exception as error:
        status_code = _error_status_code(error)
        if status_code not in {401, 403, 404}:
            raise
        if status_code in {401, 403}:
            raise RuntimeError(
                f"Unable to access Hugging Face Space {repo_id}; verify HF_TOKEN permissions."
            ) from error
        if not create_if_missing:
            raise RuntimeError(f"Space does not exist: {repo_id}") from error

    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        private=private,
        exist_ok=True,
        space_sdk=sdk,
    )
    print(f"Space created or confirmed: {repo_id}")
    return True


def resolve_ensure_settings(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    config = resolve_space_config(env)
    token = (env.get("HF_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("HF_TOKEN is required.")

    return {
        "token": token,
        "repo_id": config.repo_id,
        "sdk": config.space_sdk,
        "private": _env_flag(env.get("HF_SPACE_PRIVATE"), False),
        "create_if_missing": _env_flag(
            env.get("HF_SPACE_CREATE_IF_MISSING"),
            True,
        ),
    }


def main() -> int:
    settings = resolve_ensure_settings()

    from huggingface_hub import HfApi

    api = HfApi(token=settings["token"])
    api.whoami(token=settings["token"])
    ensure_space(
        api,
        settings["repo_id"],
        settings["sdk"],
        private=settings["private"],
        create_if_missing=settings["create_if_missing"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

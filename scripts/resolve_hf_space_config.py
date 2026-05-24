from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


DEFAULT_SPACE_NAMESPACE = "th3w1zard1"
DEFAULT_SPACE_NAME = "Pixal3D"
DEFAULT_SPACE_SDK = "gradio"


@dataclass(frozen=True)
class SpaceConfig:
    repo_id: str
    repo_name: str
    repo_namespace: str
    space_sdk: str


def _split_repo_id(repo_id: str) -> tuple[str, str]:
    namespace, separator, name = repo_id.partition("/")
    if not separator or not namespace.strip() or not name.strip():
        raise ValueError("HF_SPACE_REPO_ID must be in '<namespace>/<name>' format.")
    return namespace.strip(), name.strip()


def resolve_space_config(env: Mapping[str, str] | None = None) -> SpaceConfig:
    env = env or os.environ
    repo_id_override = (env.get("HF_SPACE_REPO_ID") or "").strip()

    if repo_id_override:
        repo_namespace, repo_name = _split_repo_id(repo_id_override)
    else:
        repo_namespace = (
            env.get("HF_SPACE_NAMESPACE") or ""
        ).strip() or DEFAULT_SPACE_NAMESPACE
        repo_name = (env.get("HF_SPACE_NAME") or "").strip() or DEFAULT_SPACE_NAME

    space_sdk = (env.get("HF_SPACE_SDK") or "").strip() or DEFAULT_SPACE_SDK
    repo_id = f"{repo_namespace}/{repo_name}"

    return SpaceConfig(
        repo_id=repo_id,
        repo_name=repo_name,
        repo_namespace=repo_namespace,
        space_sdk=space_sdk,
    )


def space_public_url(config: SpaceConfig) -> str:
    slug = config.repo_id.lower().replace("/", "-")
    return f"https://{slug}.hf.space/"


def write_github_outputs(
    config: SpaceConfig,
    output_path: str | None = None,
) -> None:
    output_path = output_path or os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return

    with open(output_path, "a", encoding="utf-8") as output_file:
        output_file.write(f"repo_id={config.repo_id}\n")
        output_file.write(f"repo_name={config.repo_name}\n")
        output_file.write(f"repo_namespace={config.repo_namespace}\n")
        output_file.write(f"space_sdk={config.space_sdk}\n")
        output_file.write(f"space_url={space_public_url(config)}\n")


def main() -> int:
    config = resolve_space_config()
    write_github_outputs(config)

    print(f"repo_id={config.repo_id}")
    print(f"repo_name={config.repo_name}")
    print(f"repo_namespace={config.repo_namespace}")
    print(f"space_sdk={config.space_sdk}")
    print(f"space_url={space_public_url(config)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

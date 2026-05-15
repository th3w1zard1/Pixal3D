import copy
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


DEFAULT_REMBG_MODEL = "ZhengPeng7/BiRefNet"
DEFAULT_REMBG_FALLBACKS = ("ZhengPeng7/BiRefNet_lite",)


@dataclass(frozen=True)
class RuntimeConfig:
    hf_token: str | None = None
    hf_cache_dir: str | None = None
    pipeline_revision: str | None = None
    rembg_model: str = DEFAULT_REMBG_MODEL
    rembg_fallback_models: tuple[str, ...] = DEFAULT_REMBG_FALLBACKS
    rembg_trust_remote_code: bool = True
    warmup_on_start: bool = True


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def build_runtime_config(env: dict[str, str] | None = None) -> RuntimeConfig:
    env = env or os.environ
    fallback_models = tuple(
        value.strip()
        for value in env.get("PIXAL3D_REMBG_FALLBACKS", "").split(",")
        if value.strip()
    )

    return RuntimeConfig(
        hf_token=env.get("HF_TOKEN") or None,
        hf_cache_dir=env.get("PIXAL3D_HF_CACHE_DIR") or None,
        pipeline_revision=env.get("PIXAL3D_PIPELINE_REVISION") or None,
        rembg_model=env.get("PIXAL3D_REMBG_MODEL") or DEFAULT_REMBG_MODEL,
        rembg_fallback_models=fallback_models or DEFAULT_REMBG_FALLBACKS,
        rembg_trust_remote_code=_as_bool(
            env.get("PIXAL3D_REMBG_TRUST_REMOTE_CODE"), True
        ),
        warmup_on_start=_as_bool(env.get("PIXAL3D_WARMUP_ON_START"), True),
    )


def build_hf_hub_kwargs(
    runtime_config: RuntimeConfig,
    include_revision: bool = True,
) -> dict[str, str]:
    kwargs = {}
    if runtime_config.hf_token:
        kwargs["token"] = runtime_config.hf_token
    if runtime_config.hf_cache_dir:
        kwargs["cache_dir"] = runtime_config.hf_cache_dir
    if include_revision and runtime_config.pipeline_revision:
        kwargs["revision"] = runtime_config.pipeline_revision
    return kwargs


def candidate_rembg_models(runtime_config: RuntimeConfig) -> list[str]:
    candidates = [runtime_config.rembg_model, *runtime_config.rembg_fallback_models]
    seen = set()
    ordered = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            ordered.append(candidate)
            seen.add(candidate)
    return ordered


def is_gated_model_reference(model_name: str | None) -> bool:
    if not model_name:
        return False
    normalized = model_name.strip().lower()
    return normalized.startswith("briaai/")


def apply_pipeline_overrides(config: dict, runtime_config: RuntimeConfig) -> dict:
    patched = copy.deepcopy(config)
    args = patched.setdefault("args", {})
    rembg_model = args.setdefault("rembg_model", {})
    rembg_args = rembg_model.setdefault("args", {})
    rembg_model["name"] = "BiRefNet"
    rembg_args["model_name"] = runtime_config.rembg_model
    rembg_args["fallback_model_names"] = list(
        candidate_rembg_models(runtime_config)[1:]
    )
    rembg_args["trust_remote_code"] = runtime_config.rembg_trust_remote_code
    return patched


def prepare_pipeline_directory(
    repo_id: str,
    runtime_config: RuntimeConfig,
    download_file: Callable[..., str] | None = None,
) -> str:
    if download_file is None:
        from huggingface_hub import hf_hub_download

        download_file = hf_hub_download

    pipeline_path = download_file(
        repo_id,
        "pipeline.json",
        **build_hf_hub_kwargs(runtime_config),
    )
    config = json.loads(Path(pipeline_path).read_text(encoding="utf-8"))
    patched_config = apply_pipeline_overrides(config, runtime_config)

    temp_dir = Path(tempfile.mkdtemp(prefix="pixal3d-pipeline-"))
    (temp_dir / "pipeline.json").write_text(
        json.dumps(patched_config),
        encoding="utf-8",
    )
    return str(temp_dir)

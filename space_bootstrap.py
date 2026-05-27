import copy
import json
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


DEFAULT_REMBG_MODEL = "ZhengPeng7/BiRefNet"
DEFAULT_REMBG_FALLBACKS = ("ZhengPeng7/BiRefNet_lite",)
ZEROGPU_REMBG_MODEL = "ZhengPeng7/BiRefNet_lite"
ZEROGPU_REMBG_FALLBACKS = ("ZhengPeng7/BiRefNet",)
DEFAULT_IMAGE_COND_MODEL = "camenduru/dinov3-vitl16-pretrain-lvd1689m"
DEFAULT_MOGE_MODEL = "Ruicheng/moge-2-vitl"
DEFAULT_PIPELINE_REPO = "TencentARC/Pixal3D-T"


class HubPrefetchState:
    def __init__(self) -> None:
        self.state = "pending"
        self.message = "Hub artifacts have not started prefetching."
        self.updated_at = time.time()
        self._lock = threading.Lock()

    def mark_running(self, message: str = "Prefetching Hub artifacts on CPU."):
        with self._lock:
            self.state = "running"
            self.message = message
            self.updated_at = time.time()

    def mark_ready(self, message: str = "Hub artifacts prefetched."):
        with self._lock:
            self.state = "ready"
            self.message = message
            self.updated_at = time.time()

    def mark_error(self, error: Exception | str):
        with self._lock:
            self.state = "error"
            self.message = str(error)
            self.updated_at = time.time()

    def mark_skipped(self, message: str = "Hub prefetch not enabled for this runtime."):
        with self._lock:
            self.state = "skipped"
            self.message = message
            self.updated_at = time.time()

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "hub_prefetch_state": self.state,
                "hub_prefetch_message": self.message,
                "hub_prefetch_updated_at": self.updated_at,
            }


hub_prefetch_state = HubPrefetchState()


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


def _is_zerogpu_hosted_space(env: dict[str, str]) -> bool:
    if not env.get("SPACE_ID"):
        return False
    accelerator = (env.get("ACCELERATOR") or "").strip().lower()
    return accelerator.startswith("zero")


def _is_hosted_space(env: dict[str, str]) -> bool:
    return bool(env.get("SPACE_ID"))


def apply_hosted_space_env_defaults(env: dict[str, str] | None = None) -> None:
    env = env or os.environ
    if _is_zerogpu_hosted_space(env):
        env.setdefault("PIXAL3D_LOW_VRAM", "1")


def _should_prefetch_hub_artifacts(env: dict[str, str]) -> bool:
    if not _is_hosted_space(env):
        return False
    return env.get("PIXAL3D_HUB_PREFETCH", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _download_trellis_model_weights(model_path: str, runtime_config: RuntimeConfig) -> None:
    from huggingface_hub import hf_hub_download

    if os.path.exists(f"{model_path}.json") and os.path.exists(f"{model_path}.safetensors"):
        return

    path_parts = model_path.split("/")
    if len(path_parts) < 2:
        return
    repo_id = f"{path_parts[0]}/{path_parts[1]}"
    model_name = "/".join(path_parts[2:]) if len(path_parts) > 2 else ""
    hub_kwargs = build_hf_hub_kwargs(runtime_config)
    if model_name:
        hf_hub_download(repo_id, f"{model_name}.json", **hub_kwargs)
        hf_hub_download(repo_id, f"{model_name}.safetensors", **hub_kwargs)


def _snapshot_download_repo(repo_id: str, runtime_config: RuntimeConfig) -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(repo_id, **build_hf_hub_kwargs(runtime_config, include_revision=False))


def prefetch_hub_artifacts(
    runtime_config: RuntimeConfig | None = None,
    env: dict[str, str] | None = None,
) -> str | None:
    env = env or os.environ
    runtime_config = runtime_config or build_runtime_config(env)
    hub_prefetch_state.mark_running()
    try:
        pipeline_dir = prepare_pipeline_directory(DEFAULT_PIPELINE_REPO, runtime_config)
        config = json.loads((Path(pipeline_dir) / "pipeline.json").read_text(encoding="utf-8"))
        for model_path in config.get("args", {}).get("models", {}).values():
            if isinstance(model_path, str):
                _download_trellis_model_weights(model_path, runtime_config)

        for repo_id in (
            runtime_config.rembg_model,
            *runtime_config.rembg_fallback_models,
            DEFAULT_IMAGE_COND_MODEL,
            DEFAULT_MOGE_MODEL,
        ):
            if repo_id:
                _snapshot_download_repo(repo_id, runtime_config)

        hub_prefetch_state.mark_ready()
        return pipeline_dir
    except Exception as exc:
        hub_prefetch_state.mark_error(exc)
        raise


def start_hub_prefetch_thread(
    runtime_config: RuntimeConfig | None = None,
    env: dict[str, str] | None = None,
    on_pipeline_dir: Callable[[str], None] | None = None,
) -> threading.Thread | None:
    env = env or os.environ
    runtime_config = runtime_config or build_runtime_config(env)
    if not _should_prefetch_hub_artifacts(env):
        hub_prefetch_state.mark_skipped()
        return None

    def _run() -> None:
        try:
            pipeline_dir = prefetch_hub_artifacts(runtime_config, env)
            if pipeline_dir and on_pipeline_dir:
                on_pipeline_dir(pipeline_dir)
        except Exception:
            pass

    thread = threading.Thread(target=_run, daemon=True, name="hub-prefetch")
    thread.start()
    return thread


def _default_rembg_model(env: dict[str, str]) -> str:
    override = env.get("PIXAL3D_REMBG_MODEL")
    if override:
        return override
    if _is_zerogpu_hosted_space(env):
        return ZEROGPU_REMBG_MODEL
    return DEFAULT_REMBG_MODEL


def _default_rembg_fallbacks(env: dict[str, str]) -> tuple[str, ...]:
    explicit = tuple(
        value.strip()
        for value in env.get("PIXAL3D_REMBG_FALLBACKS", "").split(",")
        if value.strip()
    )
    if explicit:
        return explicit
    if _is_zerogpu_hosted_space(env):
        return ZEROGPU_REMBG_FALLBACKS
    return DEFAULT_REMBG_FALLBACKS


def build_runtime_config(env: dict[str, str] | None = None) -> RuntimeConfig:
    env = env or os.environ
    warmup_default = not bool(env.get("SPACE_ID"))
    warmup_override = env.get("PIXAL3D_WARMUP_ON_START")

    config = RuntimeConfig(
        hf_token=env.get("HF_TOKEN") or None,
        hf_cache_dir=env.get("PIXAL3D_HF_CACHE_DIR") or None,
        pipeline_revision=env.get("PIXAL3D_PIPELINE_REVISION") or None,
        rembg_model=_default_rembg_model(env),
        rembg_fallback_models=_default_rembg_fallbacks(env),
        rembg_trust_remote_code=_as_bool(
            env.get("PIXAL3D_REMBG_TRUST_REMOTE_CODE"), True
        ),
        warmup_on_start=_as_bool(warmup_override, warmup_default),
    )

    from adapter_policy_runtime import evaluate_rembg_models

    evaluate_rembg_models(env, candidate_rembg_models(config))
    return config


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


def qualify_relative_model_paths(config: dict, repo_id: str) -> dict:
    patched = copy.deepcopy(config)
    models = patched.setdefault("args", {}).get("models", {})
    for key, value in list(models.items()):
        if isinstance(value, str) and value.startswith("ckpts/"):
            models[key] = f"{repo_id}/{value}"
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
    patched_config = qualify_relative_model_paths(config, repo_id)
    patched_config = apply_pipeline_overrides(patched_config, runtime_config)

    temp_dir = Path(tempfile.mkdtemp(prefix="pixal3d-pipeline-"))
    (temp_dir / "pipeline.json").write_text(
        json.dumps(patched_config),
        encoding="utf-8",
    )
    return str(temp_dir)

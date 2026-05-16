from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Mapping


@dataclass(frozen=True)
class RuntimeRule:
    key: str
    label: str
    branch: str
    execution_device: str
    activation: str
    why: str
    fallback_on_failure: str | None


RUNTIME_FALLBACK_ORDER = (
    "zerogpu",
    "space_cpu",
    "local_gpu",
    "local_cpu",
)

RUNTIME_POLICY_SUMMARY = (
    "Prefer the highest-fidelity runtime that is available on the current host, "
    "then step down toward the broadest-compatibility path."
)

RUNTIME_POLICY_BOUNDARY_NOTE = (
    "Hosted and local stages are both part of the same policy, but they are "
    "different branches. A Hugging Face Space cannot automatically execute code "
    "on a developer workstation, so local_gpu and local_cpu apply to duplicated "
    "or self-hosted runs rather than in-browser failover from the hosted Space."
)

PRIMARY_GENERATION_ENDPOINT = "/generate_3d"
CPU_FALLBACK_GENERATION_ENDPOINT = "/generate_3d_cpu_fallback"
PRIMARY_EXTRACTION_ENDPOINT = "/extract_glb_api"
CPU_FALLBACK_EXTRACTION_ENDPOINT = "/extract_glb_api_cpu_fallback"

RUNTIME_RULES = {
    "zerogpu": RuntimeRule(
        key="zerogpu",
        label="ZeroGPU primary",
        branch="space",
        execution_device="cuda",
        activation=("Use the @spaces.GPU path first on the hosted Hugging Face Space."),
        why=(
            "This is the primary production path because it preserves full Pixal3D "
            "quality and follows Hugging Face's ZeroGPU model-loading guidance."
        ),
        fallback_on_failure="space_cpu",
    ),
    "space_cpu": RuntimeRule(
        key="space_cpu",
        label="Hosted CPU fallback",
        branch="space",
        execution_device="cpu",
        activation=(
            "Use the hosted CPU endpoints when ZeroGPU quota is exhausted or the "
            "decorated GPU path cannot be obtained."
        ),
        why=(
            "This keeps the hosted UX alive without requiring a second service, but "
            "it is intentionally degraded because parts of the Pixal3D stack still "
            "depend on GPU-only sparse and rendering kernels."
        ),
        fallback_on_failure=None,
    ),
    "local_gpu": RuntimeRule(
        key="local_gpu",
        label="Local GPU primary",
        branch="local",
        execution_device="cuda",
        activation=(
            "Use local CUDA execution first when the app is running outside Hugging "
            "Face Spaces on a machine with a real GPU."
        ),
        why=(
            "This is the best non-hosted path for development, duplication, and "
            "self-hosting because it avoids ZeroGPU quotas while preserving the full "
            "GPU feature set."
        ),
        fallback_on_failure="local_cpu",
    ),
    "local_cpu": RuntimeRule(
        key="local_cpu",
        label="Local CPU last resort",
        branch="local",
        execution_device="cpu",
        activation=(
            "Use local CPU only when no CUDA device is available locally or local GPU "
            "execution fails during bring-up."
        ),
        why=(
            "This is the broadest-compatibility option and the lowest-fidelity path. "
            "It keeps preprocessing, debugging, and geometry-only export possible on "
            "CPU-only machines."
        ),
        fallback_on_failure=None,
    ),
}


def is_hosted_space(env: Mapping[str, str] | None = None) -> bool:
    env = env or os.environ
    return bool(env.get("SPACE_ID"))


def active_runtime_branch(env: Mapping[str, str] | None = None) -> str:
    return "space" if is_hosted_space(env) else "local"


def active_runtime_order(env: Mapping[str, str] | None = None) -> tuple[str, ...]:
    if is_hosted_space(env):
        return ("zerogpu", "space_cpu")
    return ("local_gpu", "local_cpu")


def primary_runtime_rule_key(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> str:
    if is_hosted_space(env):
        return "zerogpu"
    return "local_gpu" if bool(cuda_available) else "local_cpu"


def fallback_runtime_rule_key(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> str | None:
    primary_rule = primary_runtime_rule_key(env, cuda_available)
    return RUNTIME_RULES[primary_rule].fallback_on_failure


def primary_execution_device(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> str:
    primary_rule = primary_runtime_rule_key(env, cuda_available)
    return RUNTIME_RULES[primary_rule].execution_device


def generation_supports_preview(rule_key: str) -> bool:
    return rule_key in {"zerogpu", "local_gpu"}


def resolve_generation_plan(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
    use_fallback: bool = False,
) -> dict[str, object]:
    primary_rule = primary_runtime_rule_key(env, cuda_available)
    fallback_rule = fallback_runtime_rule_key(env, cuda_available)
    selected_rule = primary_rule
    if use_fallback and fallback_rule is not None:
        selected_rule = fallback_rule
    return {
        "primary_rule_key": primary_rule,
        "selected_rule_key": selected_rule,
        "fallback_rule_key": fallback_rule,
        "execution_device": RUNTIME_RULES[selected_rule].execution_device,
        "render_preview": generation_supports_preview(selected_rule),
        "primary_endpoint": PRIMARY_GENERATION_ENDPOINT,
        "fallback_endpoint": CPU_FALLBACK_GENERATION_ENDPOINT if fallback_rule else None,
    }


def resolve_extraction_plan(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
    use_fallback: bool = False,
) -> dict[str, object]:
    primary_rule = primary_runtime_rule_key(env, cuda_available)
    fallback_rule = fallback_runtime_rule_key(env, cuda_available)
    selected_rule = primary_rule
    if use_fallback and fallback_rule is not None:
        selected_rule = fallback_rule
    return {
        "primary_rule_key": primary_rule,
        "selected_rule_key": selected_rule,
        "fallback_rule_key": fallback_rule,
        "execution_device": RUNTIME_RULES[selected_rule].execution_device,
        "primary_endpoint": PRIMARY_EXTRACTION_ENDPOINT,
        "fallback_endpoint": CPU_FALLBACK_EXTRACTION_ENDPOINT if fallback_rule else None,
    }


def runtime_rulebook() -> list[dict[str, str | None]]:
    return [asdict(RUNTIME_RULES[key]) for key in RUNTIME_FALLBACK_ORDER]


def runtime_rule_reason(rule_key: str) -> str:
    return RUNTIME_RULES[rule_key].why


def build_runtime_policy_payload(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> dict[str, object]:
    env = env or os.environ
    branch = active_runtime_branch(env)
    active_order = active_runtime_order(env)
    primary_rule = primary_runtime_rule_key(env, cuda_available)
    fallback_rule = fallback_runtime_rule_key(env, cuda_available)
    generation_plan = resolve_generation_plan(env, cuda_available)
    extraction_plan = resolve_extraction_plan(env, cuda_available)
    return {
        "runtime_policy_summary": RUNTIME_POLICY_SUMMARY,
        "runtime_policy_boundary_note": RUNTIME_POLICY_BOUNDARY_NOTE,
        "runtime_fallback_order": list(RUNTIME_FALLBACK_ORDER),
        "runtime_policy_branch": branch,
        "runtime_policy_active_order": list(active_order),
        "primary_runtime_key": primary_rule,
        "fallback_runtime_key": fallback_rule,
        "primary_execution_device": generation_plan["execution_device"],
        "generation_primary_endpoint": generation_plan["primary_endpoint"],
        "generation_fallback_endpoint": generation_plan["fallback_endpoint"],
        "generation_primary_preview_available": generation_plan["render_preview"],
        "extraction_primary_endpoint": extraction_plan["primary_endpoint"],
        "extraction_fallback_endpoint": extraction_plan["fallback_endpoint"],
        "space_id": env.get("SPACE_ID") or "",
        "accelerator": env.get("ACCELERATOR") or "unknown",
        "cuda_available": cuda_available,
        "rules": runtime_rulebook(),
    }

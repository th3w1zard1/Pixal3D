# Runtime Fallback Policy

This rulebook applies to ImageEZGen3D, which is a modified derivative of the upstream TencentARC Pixal3D workspace and `TencentARC/Pixal3D-T` pipeline.

Pixal3D follows a single canonical runtime order:

1. `zerogpu`
2. `space_cpu`
3. `local_gpu`
4. `local_cpu`

That order is represented in code by [runtime_policy.py](runtime_policy.py) and exposed at the `/runtime-policy` endpoint.

## Why this order exists

The policy is designed to prefer the highest-fidelity runtime that is available on the current host, then step down toward the broadest-compatibility path.

It also matches the broader goal of this repository: keep the workflow dependable, inspectable, and deployable before expanding into heavier model integration.

- `zerogpu` comes first because the deployed Hugging Face Space is built around `@spaces.GPU`, which is the intended production path for full Pixal3D quality.
- `space_cpu` comes second because a ZeroGPU quota miss should degrade inside the same hosted app instead of surfacing as a dead-end browser error.
- `local_gpu` comes third because duplicated or self-hosted runs should prefer real local CUDA over any CPU-only path.
- `local_cpu` comes last because it is the widest-compatibility option, but also the slowest and lowest-fidelity path.

## Important boundary

All four stages are part of the same rule set, but they belong to two different branches:

- Hosted Space branch: `zerogpu -> space_cpu`
- Local branch: `local_gpu -> local_cpu`

A Hugging Face Space cannot automatically fall through into a developer workstation, so `local_gpu` and `local_cpu` are the rule order for duplicated or self-hosted runs, not remote failover from the public Space.

## Stage-by-stage rationale

| Stage | Host branch | Device | Why we do it this way | Current limitation |
| --- | --- | --- | --- | --- |
| `zerogpu` | Hosted Space | CUDA | Keeps full Pixal3D fidelity on the public deployment and matches Hugging Face ZeroGPU guidance for `@spaces.GPU`. | Subject to queueing and per-user quota. |
| `space_cpu` | Hosted Space | CPU | Prevents quota exhaustion from becoming a raw user-facing failure and keeps the hosted UX alive. | Experimental and degraded because parts of the stack still depend on GPU-only sparse/render kernels. |
| `local_gpu` | Local | CUDA | Best path for maintainers, duplicates, and self-hosting when a real GPU is available. | Requires local CUDA setup and dependencies. |
| `local_cpu` | Local | CPU | Keeps preprocessing, debugging, and geometry export possible on CPU-only systems. | Lowest fidelity and slowest path. |

## Documentation basis

This policy follows the current Hugging Face Spaces guidance used during implementation:

- `@spaces.GPU` requests a GPU for the decorated function and is effect-free outside ZeroGPU environments.
- ZeroGPU quota is enforced at request time, so browser-side retry and non-decorated hosted CPU endpoints are required.
- Hugging Face recommends placing models on `cuda` at module scope for ZeroGPU workloads.
- Duplicated Spaces default to CPU hardware unless the owner upgrades them, which is why the hosted CPU branch is explicit.

## Operational notes

- The policy is returned by `/runtime-policy` and included in `/health`.
- The browser currently retries from `zerogpu` to `space_cpu` when it detects a ZeroGPU quota error.
- CPU branches are currently treated as geometry-first fallback paths rather than full-fidelity equivalents.

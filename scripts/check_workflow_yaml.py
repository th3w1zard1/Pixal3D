from __future__ import annotations

from pathlib import Path
import sys

try:
    import yaml  # type: ignore[import-untyped]
except ImportError as error:  # pragma: no cover - exercised as a CLI guard
    raise SystemExit(
        "PyYAML is required to validate GitHub workflow files. Install it with 'python -m pip install PyYAML'."
    ) from error


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def iter_workflow_files() -> list[Path]:
    files = {
        path for pattern in ("*.yml", "*.yaml") for path in WORKFLOWS_DIR.glob(pattern)
    }
    return sorted(files)


def validate_workflow_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as workflow_file:
        try:
            list(yaml.safe_load_all(workflow_file))
        except yaml.YAMLError as error:
            relative_path = path.relative_to(REPO_ROOT)
            raise RuntimeError(
                f"Invalid workflow YAML in {relative_path}: {error}"
            ) from error


def main() -> int:
    workflow_files = iter_workflow_files()
    if not workflow_files:
        print("No GitHub workflow files found.")
        return 0

    failures: list[str] = []
    for workflow_path in workflow_files:
        try:
            validate_workflow_file(workflow_path)
            print(f"OK {workflow_path.relative_to(REPO_ROOT)}")
        except RuntimeError as error:
            failures.append(str(error))

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(f"Validated {len(workflow_files)} GitHub workflow file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

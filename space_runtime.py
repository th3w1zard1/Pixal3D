import importlib.util
import subprocess
import threading
import time


UTILS3D_WHEEL_URL = (
    "https://github.com/LDYang694/Storages/releases/download/20260430/"
    "utils3d-0.0.2-py3-none-any.whl"
)


class ModelInitState:
    def __init__(self):
        self.state = "pending"
        self.message = "Models have not started initializing."
        self.updated_at = time.time()

    def mark_initializing(self, message: str = "Model initialization in progress."):
        self.state = "initializing"
        self.message = message
        self.updated_at = time.time()

    def mark_ready(self, message: str = "Models are ready."):
        self.state = "ready"
        self.message = message
        self.updated_at = time.time()

    def mark_error(self, error: Exception | str):
        self.state = "error"
        self.message = str(error)
        self.updated_at = time.time()

    def snapshot(self) -> dict[str, object]:
        return {
            "ready": self.state == "ready",
            "state": self.state,
            "message": self.message,
            "updated_at": self.updated_at,
        }


def ensure_utils3d_installed():
    if importlib.util.find_spec("utils3d") is not None:
        return False

    subprocess.run(
        [
            "pip",
            "install",
            "--force-reinstall",
            "--no-deps",
            UTILS3D_WHEEL_URL,
        ],
        check=True,
    )
    return True


def build_launch_options(env: dict[str, str] | None = None) -> dict[str, bool]:
    env = env or {}
    share_value = env.get("GRADIO_SHARE", "")
    share = share_value.strip().lower() in {"1", "true", "yes", "on"}
    return {"show_error": True, "share": share}


def run_initialization(
    state: ModelInitState,
    init_models,
    prepare_runtime=ensure_utils3d_installed,
):
    state.mark_initializing()
    try:
        prepare_runtime()
        init_models()
    except Exception as exc:
        state.mark_error(exc)
        raise
    state.mark_ready()


def start_background_initialization(
    state: ModelInitState,
    init_models,
    prepare_runtime=ensure_utils3d_installed,
    enabled: bool = True,
):
    if not enabled:
        return None

    thread = threading.Thread(
        target=run_initialization,
        args=(state, init_models, prepare_runtime),
        daemon=True,
    )
    thread.start()
    return thread

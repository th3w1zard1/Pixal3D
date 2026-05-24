from __future__ import annotations

import json
import math
import os
import threading
import time
import traceback
from contextlib import contextmanager
from typing import *
from typing import Mapping, Union, cast

import cv2
import numpy as np
import torch
from PIL import Image

try:
    import nest_asyncio

    nest_asyncio.apply()
except ImportError:
    pass

# Lock for model initialization
init_lock = threading.Lock()
# Lock for serializing inference requests
inference_lock = threading.Lock()
# Queue tracking
_queue_lock = threading.Lock()
_queue_running_session = ""
_queue_start_time = 0.0
_pending_sessions: list[str] = []
_pending_times: dict[str, float] = {}
_PENDING_TIMEOUT = 600

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ.setdefault("ATTN_BACKEND", "flash_attn_2")
os.environ["FLEX_GEMM_AUTOTUNE_CACHE_PATH"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "autotune_cache.json"
)
os.environ["FLEX_GEMM_AUTOTUNER_VERBOSE"] = "1"

try:
    import spaces
except ImportError:

    class _FakeSpaces:
        @staticmethod
        def GPU(*args, **kwargs):
            def decorator(fn):
                return fn

            return decorator

    spaces = _FakeSpaces()
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from gradio import Server
from gradio.data_classes import FileData

from api_payload_utils import resolve_file_path
from space_bootstrap import build_runtime_config, prepare_pipeline_directory
from space_runtime import (
    ModelInitState,
    build_launch_options,
    run_initialization,
    start_background_initialization,
)

# ============================================================================
# Constants & Defaults
# ============================================================================

MAX_SEED = np.iinfo(np.int32).max
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

MODES = [
    {"name": "Normal", "icon": "assets/app/normal.png", "render_key": "normal"},
    {"name": "Clay render", "icon": "assets/app/clay.png", "render_key": "clay"},
    {
        "name": "Base color",
        "icon": "assets/app/basecolor.png",
        "render_key": "base_color",
    },
    {
        "name": "HDRI forest",
        "icon": "assets/app/hdri_forest.png",
        "render_key": "shaded_forest",
    },
    {
        "name": "HDRI sunset",
        "icon": "assets/app/hdri_sunset.png",
        "render_key": "shaded_sunset",
    },
    {
        "name": "HDRI courtyard",
        "icon": "assets/app/hdri_courtyard.png",
        "render_key": "shaded_courtyard",
    },
]
STEPS = 8
ZEROGPU_MAX_DURATION_SECONDS = 120
# Keep per-call reservations small so one cold generate fits typical free quota.
ZEROGPU_WARMUP_DURATION_SECONDS = 50
ZEROGPU_GENERATION_MAX_DURATION_SECONDS = 40
ZEROGPU_EXTRACT_DURATION_SECONDS = 40
ZEROGPU_MAX_RESOLUTION = 1024
ZEROGPU_MAX_STAGE_STEPS = 5
ZEROGPU_MAX_DECIMATION_TARGET = 500000
ZEROGPU_MAX_TEXTURE_SIZE = 512
DEFAULT_ZEROGPU_HARDWARE = "zero-a10g"

# Cascade parameters
CASCADE_LR_RESOLUTION = 512
CASCADE_MAX_NUM_TOKENS = 49152

# MoGe defaults
MOGE_MODEL_NAME = "Ruicheng/moge-2-vitl"
WILD_MESH_SCALE = 1.0
WILD_EXTEND_PIXEL = 0
WILD_IMAGE_RESOLUTION = 512
CPU_AUTO_FOV_RADIANS = 0.2

# Image Cond Model configs
IMAGE_COND_CONFIGS = {
    "ss": {
        "model_name": "camenduru/dinov3-vitl16-pretrain-lvd1689m",
        "image_size": 512,
        "grid_resolution": 16,
    },
    "shape_512": {
        "model_name": "camenduru/dinov3-vitl16-pretrain-lvd1689m",
        "image_size": 512,
        "grid_resolution": 32,
        "use_naf_upsample": True,
        "naf_target_size": 512,
    },
    "shape_1024": {
        "model_name": "camenduru/dinov3-vitl16-pretrain-lvd1689m",
        "image_size": 1024,
        "grid_resolution": 64,
        "use_naf_upsample": True,
        "naf_target_size": 512,
    },
    "tex_1024": {
        "model_name": "camenduru/dinov3-vitl16-pretrain-lvd1689m",
        "image_size": 1024,
        "grid_resolution": 64,
        "use_naf_upsample": True,
        "naf_target_size": 1024,
    },
}

# ============================================================================
# Model Loading
# ============================================================================


def build_image_cond_model(config: dict):
    from trellis2.trainers.flow_matching.mixins.image_conditioned_proj import (
        DinoV3ProjFeatureExtractor,
    )

    model = DinoV3ProjFeatureExtractor(**config)
    model.eval()
    return model


def load_moge_model(device="cuda", model_name=MOGE_MODEL_NAME):
    from moge.model.v2 import MoGeModel

    moge_model = MoGeModel.from_pretrained(model_name).to(device)
    moge_model.eval()
    return moge_model


# Global instances (lazy loaded or loaded at start)
pipeline = None
moge_model = None
envmap = None
preprocess_model = None
runtime_config = build_runtime_config()
resolved_pipeline_dir = None
runtime_state = ModelInitState()
warmup_thread = None
preprocess_lock = threading.Lock()
current_runtime_device = "cuda" if torch.cuda.is_available() else "cpu"


def _default_dense_attn_backend() -> str:
    configured = os.environ.get("ATTN_BACKEND", "flash_attn")
    mapping = {
        "flash_attn": "flash_attn",
        "flash_attn_2": "flash_attn",
        "flash_attn_3": "flash_attn_3",
        "flash_attn_4": "flash_attn_4",
        "xformers": "xformers",
        "sdpa": "sdpa",
        "naive": "naive",
    }
    return mapping.get(configured, "flash_attn")


def _default_sparse_attn_backend() -> str:
    configured = os.environ.get(
        "SPARSE_ATTN_BACKEND",
        os.environ.get("ATTN_BACKEND", "flash_attn"),
    )
    mapping = {
        "flash_attn": "flash_attn",
        "flash_attn_2": "flash_attn",
        "flash_attn_3": "flash_attn_3",
        "flash_attn_4": "flash_attn_4",
        "xformers": "xformers",
        "naive": "naive",
    }
    return mapping.get(configured, "flash_attn")


DEFAULT_ATTN_BACKEND = _default_dense_attn_backend()
DEFAULT_SPARSE_ATTN_BACKEND = _default_sparse_attn_backend()


def resolve_runtime_mode(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> str:
    env = env or os.environ
    if cuda_available is None:
        cuda_available = torch.cuda.is_available()
    if cuda_available:
        accelerator = (env.get("ACCELERATOR") or "").strip().lower()
        if accelerator.startswith("zero"):
            return "zerogpu"
        return "gpu"
    return "cpu"


def resolve_execution_device(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> str:
    del env
    if cuda_available is None:
        cuda_available = torch.cuda.is_available()
    return "cuda" if cuda_available else "cpu"


def resolve_generation_plan(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> dict[str, object]:
    device = resolve_execution_device(env, cuda_available)
    return {
        "execution_device": device,
        "render_preview": device == "cuda",
        "runtime_mode": resolve_runtime_mode(env, cuda_available),
    }


def resolve_extraction_plan(
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> dict[str, object]:
    return {
        "execution_device": resolve_execution_device(env, cuda_available),
        "runtime_mode": resolve_runtime_mode(env, cuda_available),
    }


def resolve_target_hardware(
    env: Mapping[str, str] | None = None,
) -> str:
    env = env or os.environ
    return (env.get("PIXAL3D_ZEROGPU_HARDWARE") or DEFAULT_ZEROGPU_HARDWARE).strip()


def cpu_runtime_message(
    target_hardware: str,
    auto_request_enabled: bool,
) -> str:
    if auto_request_enabled:
        return (
            f"CPU hardware is active. Requested {target_hardware} so Pixal3D can run "
            "on supported Hugging Face hardware. The Space will restart; reload and retry "
            "once runtime_mode changes from cpu."
        )
    return (
        "CPU hardware is active, but Pixal3D inference still depends on GPU-only operators. "
        "Set the HF_TOKEN secret for this Space to allow automatic switching to ZeroGPU."
    )


def request_supported_hardware(
    target_hardware: str,
) -> dict[str, object]:
    space_id = os.environ.get("SPACE_ID") or ""
    if not space_id:
        return {
            "ok": False,
            "message": "Hardware switching only works on a Hugging Face Space runtime.",
            "requested_hardware": target_hardware,
        }
    if not runtime_config.hf_token:
        return {
            "ok": False,
            "message": "HF_TOKEN secret is missing.",
            "requested_hardware": target_hardware,
        }

    from huggingface_hub import HfApi

    api = HfApi(token=runtime_config.hf_token)
    runtime = api.get_space_runtime(space_id)
    if runtime.hardware != target_hardware and runtime.requested_hardware != target_hardware:
        api.request_space_hardware(repo_id=space_id, hardware=target_hardware)

    return {
        "ok": True,
        "current_hardware": runtime.hardware,
        "requested_hardware": target_hardware,
        "current_stage": runtime.stage,
    }


def cpu_transition_payload(action: str) -> dict[str, object]:
    target_hardware = resolve_target_hardware(os.environ)
    transition = request_supported_hardware(target_hardware)
    auto_request_enabled = bool(transition.get("ok"))
    message = cpu_runtime_message(target_hardware, auto_request_enabled)
    if not auto_request_enabled:
        detail = str(transition.get("message") or "")
        if detail:
            message = f"{message} {detail}".strip()

    return {
        "error": True,
        "action": action,
        "runtime_mode": "cpu",
        "preview_available": False,
        "extract_available": False,
        "hardware_transition_requested": auto_request_enabled,
        "requested_hardware": target_hardware,
        "message": message,
    }


def normalize_generation_request(
    resolution: int,
    ss_sampling_steps: int,
    shape_slat_sampling_steps: int,
    tex_slat_sampling_steps: int,
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> dict[str, object]:
    runtime_mode = resolve_runtime_mode(env, cuda_available)
    normalized_resolution = int(resolution)
    normalized_ss_steps = int(ss_sampling_steps)
    normalized_shape_steps = int(shape_slat_sampling_steps)
    normalized_tex_steps = int(tex_slat_sampling_steps)
    messages: list[str] = []

    if runtime_mode == "zerogpu":
        if normalized_resolution > ZEROGPU_MAX_RESOLUTION:
            normalized_resolution = ZEROGPU_MAX_RESOLUTION
            messages.append(
                "ZeroGPU currently caps hosted generation at 1024 resolution."
            )

        capped_steps = {
            "ss": min(normalized_ss_steps, ZEROGPU_MAX_STAGE_STEPS),
            "shape": min(normalized_shape_steps, ZEROGPU_MAX_STAGE_STEPS),
            "tex": min(normalized_tex_steps, ZEROGPU_MAX_STAGE_STEPS),
        }
        if (
            capped_steps["ss"] != normalized_ss_steps
            or capped_steps["shape"] != normalized_shape_steps
            or capped_steps["tex"] != normalized_tex_steps
        ):
            normalized_ss_steps = capped_steps["ss"]
            normalized_shape_steps = capped_steps["shape"]
            normalized_tex_steps = capped_steps["tex"]
            messages.append(
                "ZeroGPU currently caps sampling at 5 steps per stage to stay inside the hosted runtime window."
            )

    return {
        "runtime_mode": runtime_mode,
        "resolution": normalized_resolution,
        "ss_sampling_steps": normalized_ss_steps,
        "shape_slat_sampling_steps": normalized_shape_steps,
        "tex_slat_sampling_steps": normalized_tex_steps,
        "messages": messages,
    }


def normalize_extraction_request(
    decimation_target: int,
    texture_size: int,
    env: Mapping[str, str] | None = None,
    cuda_available: bool | None = None,
) -> dict[str, int | str]:
    runtime_mode = resolve_runtime_mode(env, cuda_available)
    normalized_decimation_target = int(decimation_target)
    normalized_texture_size = int(texture_size)

    if runtime_mode == "zerogpu":
        normalized_decimation_target = min(
            normalized_decimation_target,
            ZEROGPU_MAX_DECIMATION_TARGET,
        )
        normalized_texture_size = min(
            normalized_texture_size,
            ZEROGPU_MAX_TEXTURE_SIZE,
        )

    return {
        "runtime_mode": runtime_mode,
        "decimation_target": normalized_decimation_target,
        "texture_size": normalized_texture_size,
    }


def _remove_pending_session_locked(session_id: str) -> None:
    if not session_id:
        return
    if session_id in _pending_sessions:
        _pending_sessions.remove(session_id)
    _pending_times.pop(session_id, None)


def _remove_pending_session(session_id: str) -> None:
    with _queue_lock:
        _remove_pending_session_locked(session_id)


@contextmanager
def acquire_inference(session_id: str = ""):
    """Serialize inference and maintain queue state for the browser progress UI."""
    global _queue_running_session, _queue_start_time

    with _queue_lock:
        if session_id and session_id not in _pending_sessions:
            _pending_sessions.append(session_id)
            _pending_times[session_id] = time.time()

    try:
        with inference_lock:
            with _queue_lock:
                _remove_pending_session_locked(session_id)
                _queue_running_session = session_id
                _queue_start_time = time.time()
            try:
                yield
            finally:
                with _queue_lock:
                    _queue_running_session = ""
                    _queue_start_time = 0.0
    except BaseException:
        with _queue_lock:
            _remove_pending_session_locked(session_id)
        raise


def _normalize_device(device: str | torch.device) -> torch.device:
    return device if isinstance(device, torch.device) else torch.device(device)


def _runtime_low_vram_enabled() -> bool:
    return os.environ.get("PIXAL3D_LOW_VRAM") == "1"


def _set_dense_attention_backend(device: str | torch.device) -> None:
    from trellis2.modules.attention import config as attention_config
    from trellis2.modules.sparse import config as sparse_config

    normalized = _normalize_device(device)
    backend = "sdpa" if normalized.type == "cpu" else DEFAULT_ATTN_BACKEND
    sparse_backend = (
        "naive" if normalized.type == "cpu" else DEFAULT_SPARSE_ATTN_BACKEND
    )
    attention_config.set_backend(backend)  # pyright: ignore[reportArgumentType]
    sparse_config.set_attn_backend(sparse_backend)  # pyright: ignore[reportArgumentType]
    print(f"[Runtime] Dense attention backend set to: {backend}")
    print(f"[Runtime] Sparse attention backend set to: {sparse_backend}")


def move_runtime_to(device: str | torch.device) -> None:
    global current_runtime_device, pipeline, moge_model

    normalized = _normalize_device(device)
    target = normalized.type
    if pipeline is None:
        return
    if current_runtime_device == target:
        return

    _set_dense_attention_backend(normalized)
    print(f"[Runtime] Moving runtime to {target}...")

    if target == "cuda":
        pipeline.cuda()
    else:
        pipeline.cpu()

    if not _runtime_low_vram_enabled():
        for attr in [
            "image_cond_model_ss",
            "image_cond_model_shape_512",
            "image_cond_model_shape_1024",
            "image_cond_model_tex_1024",
        ]:
            model = getattr(pipeline, attr, None)
            if model is not None:
                model.to(normalized)

        if moge_model is not None:
            moge_model.to(normalized)

    current_runtime_device = target


def export_basic_glb(mesh, session_id: str = "") -> str:
    import trimesh

    trimesh_mesh = trimesh.Trimesh(
        vertices=mesh.vertices.detach().cpu().numpy(),
        faces=mesh.faces.detach().cpu().numpy(),
        process=False,
    )
    rot = np.array(
        [
            [-1, 0, 0, 0],
            [0, 0, -1, 0],
            [0, -1, 0, 0],
            [0, 0, 0, 1],
        ],
        dtype=np.float64,
    )
    trimesh_mesh.apply_transform(rot)
    suffix = f"_{session_id[:8]}" if session_id else ""
    out_glb = os.path.join(TMP_DIR, f"result_cpu{suffix}_{int(time.time() * 1000)}.glb")
    trimesh_mesh.export(out_glb)
    return out_glb


def resolve_pipeline_source(model_path: str) -> str:
    global resolved_pipeline_dir
    if os.path.exists(os.path.join(model_path, "pipeline.json")):
        return model_path
    if resolved_pipeline_dir is None:
        resolved_pipeline_dir = prepare_pipeline_directory(model_path, runtime_config)
    return resolved_pipeline_dir


def resolve_runtime_init_device(preferred_device: str | None = None) -> str:
    if preferred_device:
        return _normalize_device(preferred_device).type
    return resolve_execution_device(os.environ, torch.cuda.is_available())


def initialize_runtime(preferred_device: str | None = None):
    run_initialization(
        runtime_state,
        lambda: init_models(preferred_device=preferred_device),
    )


def ensure_runtime_ready(preferred_device: str | None = None):
    global warmup_thread
    if runtime_state.snapshot()["ready"]:
        return
    if warmup_thread is not None and warmup_thread.is_alive():
        warmup_thread.join()
        if runtime_state.snapshot()["ready"]:
            return
    initialize_runtime(preferred_device=preferred_device)


def start_runtime_warmup():
    global warmup_thread
    if warmup_thread is not None and warmup_thread.is_alive():
        return warmup_thread
    warmup_thread = start_background_initialization(
        runtime_state,
        init_models,
        enabled=runtime_config.warmup_on_start,
    )
    return warmup_thread


def init_models(preferred_device: str | None = None):
    global pipeline, moge_model, envmap, current_runtime_device
    with init_lock:
        if pipeline is not None:
            return
        initial_device = resolve_runtime_init_device(preferred_device)
        normalized_initial_device = _normalize_device(initial_device)
        cuda_runtime_available = initial_device == "cuda" and torch.cuda.is_available()
        # GPU / CUDA Diagnostics (runs when GPU is allocated)
        import subprocess as _sp

        from trellis2.pipelines import Pixal3DImageTo3DPipeline
        from trellis2.renderers import EnvMap

        print("=" * 60)
        print("[Diagnostics] PyTorch version:", torch.__version__)
        print("[Diagnostics] Runtime init device:", initial_device)
        print("[Diagnostics] CUDA available:", cuda_runtime_available)
        if cuda_runtime_available:
            print("[Diagnostics] CUDA version:", torch.version.cuda)
            print("[Diagnostics] cuDNN version:", torch.backends.cudnn.version())
            for i in range(torch.cuda.device_count()):
                name = torch.cuda.get_device_name(i)
                cap = torch.cuda.get_device_capability(i)
                mem = torch.cuda.get_device_properties(i).total_memory / 1024**3
                print(
                    f"[Diagnostics] GPU {i}: {name}, sm_{cap[0]}{cap[1]}, {mem:.1f} GB"
                )
            try:
                res = _sp.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,compute_cap,memory.total",
                        "--format=csv,noheader",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                print("[Diagnostics] nvidia-smi:", res.stdout.strip())
            except Exception as e:
                print(f"[Diagnostics] nvidia-smi failed: {e}")
        print("=" * 60)

        model_path = "TencentARC/Pixal3D-T"
        print(f"[Pipeline] Loading from {model_path}...")
        pipeline = Pixal3DImageTo3DPipeline.from_pretrained(
            resolve_pipeline_source(model_path)
        )
        _set_dense_attention_backend(initial_device)

        print("[ImageCond] Building DinoV3ProjFeatureExtractor models...")
        pipeline.image_cond_model_ss = build_image_cond_model(IMAGE_COND_CONFIGS["ss"])
        pipeline.image_cond_model_shape_512 = build_image_cond_model(
            IMAGE_COND_CONFIGS["shape_512"]
        )
        pipeline.image_cond_model_shape_1024 = build_image_cond_model(
            IMAGE_COND_CONFIGS["shape_1024"]
        )
        pipeline.image_cond_model_tex_1024 = build_image_cond_model(
            IMAGE_COND_CONFIGS["tex_1024"]
        )

        low_vram_mode = _runtime_low_vram_enabled()
        pipeline.low_vram = low_vram_mode
        if initial_device == "cuda":
            pipeline.cuda()
        else:
            pipeline.cpu()

        if not low_vram_mode:
            for attr in [
                "image_cond_model_ss",
                "image_cond_model_shape_512",
                "image_cond_model_shape_1024",
                "image_cond_model_tex_1024",
            ]:
                model = getattr(pipeline, attr, None)
                if model is not None:
                    model.to(normalized_initial_device)

        print("[NAF] Pre-loading NAF upsampler model...")
        for attr in [
            "image_cond_model_ss",
            "image_cond_model_shape_512",
            "image_cond_model_shape_1024",
            "image_cond_model_tex_1024",
        ]:
            model = getattr(pipeline, attr, None)
            if model is not None and getattr(model, "use_naf_upsample", False):
                model._load_naf()

        print("[MoGe-2] Loading model for camera estimation...")
        moge_model = load_moge_model(device="cpu" if low_vram_mode else initial_device)

        print("[EnvMap] Loading environment maps...")
        _base = os.path.dirname(os.path.abspath(__file__))
        envmap_device = "cpu" if low_vram_mode else initial_device
        envmap = {
            "forest": EnvMap(
                torch.tensor(
                    cv2.cvtColor(
                        cv2.imread(
                            os.path.join(_base, "assets/hdri/forest.exr"),
                            cv2.IMREAD_UNCHANGED,
                        ),
                        cv2.COLOR_BGR2RGB,
                    ),
                    dtype=torch.float32,
                    device=envmap_device,
                )
            ),
            "sunset": EnvMap(
                torch.tensor(
                    cv2.cvtColor(
                        cv2.imread(
                            os.path.join(_base, "assets/hdri/sunset.exr"),
                            cv2.IMREAD_UNCHANGED,
                        ),
                        cv2.COLOR_BGR2RGB,
                    ),
                    dtype=torch.float32,
                    device=envmap_device,
                )
            ),
            "courtyard": EnvMap(
                torch.tensor(
                    cv2.cvtColor(
                        cv2.imread(
                            os.path.join(_base, "assets/hdri/courtyard.exr"),
                            cv2.IMREAD_UNCHANGED,
                        ),
                        cv2.COLOR_BGR2RGB,
                    ),
                    dtype=torch.float32,
                    device=envmap_device,
                )
            ),
        }
        current_runtime_device = initial_device


def get_preprocess_model():
    global preprocess_model
    with preprocess_lock:
        if preprocess_model is None:
            from trellis2.pipelines.rembg import BiRefNet

            preprocess_model = BiRefNet(
                model_name=runtime_config.rembg_model,
                fallback_model_names=runtime_config.rembg_fallback_models,
                trust_remote_code=runtime_config.rembg_trust_remote_code,
            )
        return preprocess_model


def preprocess_image_for_ui(
    input_image: Image.Image, bg_color: tuple = (0, 0, 0)
) -> Image.Image:
    has_alpha = False
    if input_image.mode == "RGBA":
        alpha = np.array(input_image)[:, :, 3]
        if not np.all(alpha == 255):
            has_alpha = True

    max_size = max(input_image.size)
    scale = min(1, 1024 / max_size)
    if scale < 1:
        input_image = input_image.resize(
            (int(input_image.width * scale), int(input_image.height * scale)),
            Image.Resampling.LANCZOS,
        )

    if has_alpha:
        output = input_image
    else:
        output = get_preprocess_model()(input_image.convert("RGB"))

    output_np = np.array(output)
    alpha = output_np[:, :, 3]
    bbox = np.argwhere(alpha > 0.8 * 255)
    bbox = (
        np.min(bbox[:, 1]),
        np.min(bbox[:, 0]),
        np.max(bbox[:, 1]),
        np.max(bbox[:, 0]),
    )
    center = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    size = int(max(bbox[2] - bbox[0], bbox[3] - bbox[1]) * 1.1)
    bbox = (
        center[0] - size // 2,
        center[1] - size // 2,
        center[0] + size // 2,
        center[1] + size // 2,
    )
    output = output.crop(bbox)  # type: ignore[arg-type]
    output = np.array(output).astype(np.float32) / 255
    rgb = output[:, :, :3]
    a = output[:, :, 3:4]
    bg = np.array(bg_color, dtype=np.float32) / 255.0
    composited = rgb * a + bg * (1.0 - a)
    return Image.fromarray((np.clip(composited, 0, 1) * 255).astype(np.uint8))


# ============================================================================
# Utilities
# ============================================================================


def compute_f_pixels(camera_angle_x: float, resolution: int) -> float:
    focal_length = 16.0 / torch.tan(torch.tensor(camera_angle_x / 2.0))
    f_pixels = focal_length * resolution / 32.0
    return float(f_pixels.item())


def distance_from_fov(
    camera_angle_x, grid_point, target_point, mesh_scale, image_resolution
):
    rotation_matrix = torch.tensor([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])
    gp = grid_point.to(torch.float32) @ rotation_matrix.T
    gp = gp / mesh_scale / 2
    xw, yw, zw = gp[0].item(), gp[1].item(), gp[2].item()
    xt, yt = float(target_point[0].item()), float(target_point[1].item())
    f_pixels = compute_f_pixels(camera_angle_x, image_resolution)
    x_ndc = xt - image_resolution / 2.0
    y_ndc = -(yt - image_resolution / 2.0)
    distance_x = f_pixels * xw / x_ndc - yw
    return {"distance_from_x": float(distance_x), "f_pixels": float(f_pixels)}


def get_camera_params_wild_moge(
    image_path, device="cuda", mesh_scale=1.0, extend_pixel=0, image_resolution=512
):
    low_vram_mode = _runtime_low_vram_enabled()
    if low_vram_mode:
        moge_model.to(device)
    pil_image = Image.open(image_path).convert("RGB")
    width, height = pil_image.size
    image_np = np.array(pil_image).astype(np.float32) / 255.0
    image_tensor = torch.from_numpy(image_np).permute(2, 0, 1).to(device)
    with torch.no_grad():
        output = moge_model.infer(image_tensor)
    if low_vram_mode:
        moge_model.cpu()
    intrinsics = output["intrinsics"].squeeze().cpu().numpy()
    fx_normalized = intrinsics[0, 0]
    fx = fx_normalized * width
    camera_angle_x = 2 * math.atan(width / (2 * fx))

    grid_point = torch.tensor([-1.0, 0.0, 0.0])
    distance = distance_from_fov(
        camera_angle_x,
        grid_point,
        torch.tensor([0 - extend_pixel, image_resolution - 1 + extend_pixel]),
        mesh_scale,
        image_resolution,
    )["distance_from_x"]
    return {
        "camera_angle_x": camera_angle_x,
        "distance": distance,
        "mesh_scale": mesh_scale,
    }


def build_camera_params_from_fov(camera_angle_x: float, fov_label: str) -> dict:
    grid_point = torch.tensor([-1.0, 0.0, 0.0])
    distance = distance_from_fov(
        camera_angle_x,
        grid_point,
        torch.tensor(
            [0 - WILD_EXTEND_PIXEL, WILD_IMAGE_RESOLUTION - 1 + WILD_EXTEND_PIXEL]
        ),
        WILD_MESH_SCALE,
        WILD_IMAGE_RESOLUTION,
    )["distance_from_x"]
    print(
        f"[Camera] Using {fov_label}: {math.degrees(camera_angle_x):.2f}° ({camera_angle_x:.4f} rad), distance: {distance:.4f}"
    )
    return {
        "camera_angle_x": camera_angle_x,
        "distance": distance,
        "mesh_scale": WILD_MESH_SCALE,
    }


def pack_state(shape_slat, tex_slat, res):
    state_data = {
        "shape_slat_feats": shape_slat.feats.cpu().numpy(),
        "tex_slat_feats": tex_slat.feats.cpu().numpy(),
        "coords": shape_slat.coords.cpu().numpy(),
        "res": res,
    }
    import random

    state_path = os.path.join(
        TMP_DIR, f"state_{int(time.time() * 1000)}_{random.randint(0, 9999):04d}.npz"
    )
    np.savez_compressed(state_path, **state_data)
    return state_path


def unpack_state(state_path, device: Union[str, torch.device] = "cuda"):
    from trellis2.modules.sparse import SparseTensor

    normalized = _normalize_device(device)
    data = np.load(state_path)
    shape_slat = SparseTensor(
        feats=torch.from_numpy(data["shape_slat_feats"]).to(normalized),
        coords=torch.from_numpy(data["coords"]).to(normalized),
    )
    tex_slat = shape_slat.replace(
        torch.from_numpy(data["tex_slat_feats"]).to(normalized)
    )
    return shape_slat, tex_slat, int(data["res"])


# ============================================================================
# Progress Tracking (file-based, cross-process safe for @spaces.GPU)
# ============================================================================


from fastapi import Request  # noqa: E402

PROGRESS_DIR = os.path.join(TMP_DIR, "_progress")
os.makedirs(PROGRESS_DIR, exist_ok=True)

_thread_local = threading.local()


def _progress_file(session_id: str) -> str:
    """Return path to a session's progress JSON file."""
    return os.path.join(PROGRESS_DIR, f"{session_id}.json")


def _reset_progress(session_id: str):
    _thread_local.active_session = session_id
    _write_progress_file(
        session_id, {"stage": "Initializing...", "step": 0, "total": 0, "done": False}
    )


def _update_progress(stage: str, step: int, total: int):
    session_id = getattr(_thread_local, "active_session", "")
    if session_id:
        _write_progress_file(
            session_id, {"stage": stage, "step": step, "total": total, "done": False}
        )


def _finish_progress():
    session_id = getattr(_thread_local, "active_session", "")
    if session_id:
        _write_progress_file(session_id, {"done": True})


def _fail_progress(stage: str, error: Exception):
    session_id = getattr(_thread_local, "active_session", "")
    if session_id:
        _write_progress_file(
            session_id,
            {
                "stage": stage,
                "step": 0,
                "total": 0,
                "done": True,
                "error": True,
                "message": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(),
            },
        )


def _write_progress_file(session_id: str, data: dict):
    """Atomically write progress JSON to a file (cross-process safe)."""
    path = _progress_file(session_id)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            json.dump(data, f)
        os.replace(tmp_path, path)  # atomic on POSIX
    except Exception:
        pass


# Monkey-patch tqdm to intercept progress
import tqdm as _tqdm_module

_original_tqdm = _tqdm_module.tqdm


class _TqdmProgressInterceptor(_original_tqdm):
    """Wraps tqdm to push progress updates to SSE."""

    def __init__(self, *args, **kwargs):
        self._stage_desc = kwargs.get("desc", "Processing")
        super().__init__(*args, **kwargs)

    def set_description(self, desc=None, refresh=True):
        self._stage_desc = desc or "Processing"
        super().set_description(desc, refresh)

    def update(self, n=1):
        super().update(n)
        _update_progress(self._stage_desc, self.n, self.total or 0)


# Patch tqdm globally
_tqdm_module.tqdm = _TqdmProgressInterceptor

_progress_hooks_installed = False


def install_progress_hooks():
    global _progress_hooks_installed
    if _progress_hooks_installed:
        return
    import o_voxel.postprocess as _ovp_module

    import trellis2.pipelines.samplers.flow_euler as _fe_module
    import trellis2.utils.render_utils as _ru_module

    _fe_module.tqdm = _TqdmProgressInterceptor
    _ru_module.tqdm = _TqdmProgressInterceptor
    _ovp_module.tqdm = _TqdmProgressInterceptor
    _progress_hooks_installed = True


def _build_camera_params(
    temp_processed_path: str,
    manual_fov: float,
    fov_unit: str,
    execution_device: str,
) -> dict:
    if manual_fov > 0:
        if fov_unit == "rad":
            camera_angle_x = float(manual_fov)
        else:
            camera_angle_x = math.radians(manual_fov)
        return build_camera_params_from_fov(camera_angle_x, "manual FOV")

    if _normalize_device(execution_device).type == "cpu":
        print(
            "[Camera] CPU execution detected; skipping MoGe auto-estimation and using the deterministic 0.2 rad default."
        )
        return build_camera_params_from_fov(
            CPU_AUTO_FOV_RADIANS,
            "CPU auto FOV",
        )

    return get_camera_params_wild_moge(
        temp_processed_path,
        device=execution_device,
        mesh_scale=WILD_MESH_SCALE,
        extend_pixel=WILD_EXTEND_PIXEL,
        image_resolution=WILD_IMAGE_RESOLUTION,
    )


def resolve_pipeline_type(hr_resolution: int) -> str:
    return "1024" if hr_resolution <= 1024 else "1536_cascade"


def _generate_3d_impl(
    image: FileData,
    seed: int,
    resolution: int,
    ss_guidance_strength: float,
    ss_guidance_rescale: float,
    ss_sampling_steps: int,
    ss_rescale_t: float,
    shape_slat_guidance_strength: float,
    shape_slat_guidance_rescale: float,
    shape_slat_sampling_steps: int,
    shape_slat_rescale_t: float,
    tex_slat_guidance_strength: float,
    tex_slat_guidance_rescale: float,
    tex_slat_sampling_steps: int,
    tex_slat_rescale_t: float,
    manual_fov: float,
    fov_unit: str,
    session_id: str,
    execution_device: str,
    render_preview: bool,
) -> list[dict[str, Any]]:
    stage = "Preparing runtime"
    _reset_progress(session_id)
    try:
        _update_progress(stage, 0, 2)
        ensure_runtime_ready(preferred_device=execution_device)
        move_runtime_to(execution_device)
        stage = "Installing progress hooks"
        _update_progress(stage, 1, 2)
        install_progress_hooks()
        from trellis2.utils import render_utils
    except Exception as exc:
        _fail_progress(stage, exc)
        raise

    _update_progress("Preprocessing & Camera Estimation", 0, 1)
    torch.manual_seed(seed)
    request_settings = normalize_generation_request(
        resolution=resolution,
        ss_sampling_steps=ss_sampling_steps,
        shape_slat_sampling_steps=shape_slat_sampling_steps,
        tex_slat_sampling_steps=tex_slat_sampling_steps,
        env=os.environ,
        cuda_available=torch.cuda.is_available(),
    )
    hr_resolution = cast(int, request_settings["resolution"])
    ss_sampling_steps = cast(int, request_settings["ss_sampling_steps"])
    shape_slat_sampling_steps = cast(int, request_settings["shape_slat_sampling_steps"])
    tex_slat_sampling_steps = cast(int, request_settings["tex_slat_sampling_steps"])
    runtime_messages = cast(list[str], request_settings["messages"])

    image_path = resolve_file_path(image)
    img = Image.open(image_path)
    image_preprocessed = img
    temp_processed_path = os.path.join(
        TMP_DIR, f"temp_proc_{session_id[:8]}_{int(time.time() * 1000)}.png"
    )
    image_preprocessed.save(temp_processed_path)

    camera_params = _build_camera_params(
        temp_processed_path=temp_processed_path,
        manual_fov=manual_fov,
        fov_unit=fov_unit,
        execution_device=execution_device,
    )
    _update_progress("Preprocessing & Camera Estimation", 1, 1)

    ss_sampler_override = {
        "steps": ss_sampling_steps,
        "guidance_strength": ss_guidance_strength,
        "guidance_rescale": ss_guidance_rescale,
        "rescale_t": ss_rescale_t,
    }
    shape_sampler_override = {
        "steps": shape_slat_sampling_steps,
        "guidance_strength": shape_slat_guidance_strength,
        "guidance_rescale": shape_slat_guidance_rescale,
        "rescale_t": shape_slat_rescale_t,
    }
    tex_sampler_override = {
        "steps": tex_slat_sampling_steps,
        "guidance_strength": tex_slat_guidance_strength,
        "guidance_rescale": tex_slat_guidance_rescale,
        "rescale_t": tex_slat_rescale_t,
    }

    pipeline_type = resolve_pipeline_type(hr_resolution)
    mesh_list, (shape_slat, tex_slat, res) = pipeline.run(
        image_preprocessed,
        camera_params=camera_params,
        seed=seed,
        sparse_structure_sampler_params=ss_sampler_override,
        shape_slat_sampler_params=shape_sampler_override,
        tex_slat_sampler_params=tex_sampler_override,
        preprocess_image=False,
        return_latent=True,
        pipeline_type=pipeline_type,
        max_num_tokens=CASCADE_MAX_NUM_TOKENS,
    )

    mesh = mesh_list[0]
    state_path = pack_state(shape_slat, tex_slat, res)
    result: dict[str, Any] = {
        "state_path": os.path.abspath(state_path),
        "camera_angle_x": camera_params["camera_angle_x"],
        "distance": camera_params["distance"],
        "requested_resolution": int(resolution),
        "effective_resolution": hr_resolution,
        "effective_sampling_steps": {
            "ss": ss_sampling_steps,
            "shape": shape_slat_sampling_steps,
            "tex": tex_slat_sampling_steps,
        },
        "error": False,
    }

    if render_preview:
        _update_progress("Rendering views", 0, 1)
        mesh.simplify(16777216)
        cam_dist = camera_params["distance"]
        near = max(0.01, cam_dist - 2.0)
        far = cam_dist + 10.0
        renders = render_utils.render_proj_aligned_video(
            mesh,
            camera_angle_x=camera_params["camera_angle_x"],
            distance=cam_dist,
            resolution=1024,
            num_frames=STEPS,
            envmap=envmap,
            near=near,
            far=far,
        )
        _update_progress("Rendering views", 1, 1)

        render_files = {}
        for mode_key, frames in renders.items():
            mode_files = []
            for i, frame in enumerate(frames):
                p = os.path.abspath(
                    os.path.join(
                        TMP_DIR, f"render_{mode_key}_{i}_{int(time.time() * 1000)}.jpg"
                    )
                )
                Image.fromarray(frame).save(p, quality=85)
                mode_files.append(p)
            render_files[mode_key] = mode_files

        result.update(
            {
                "render_paths": render_files,
                "preview_available": True,
                "extract_available": True,
            }
        )
    else:
        _update_progress("Exporting CPU GLB", 0, 1)
        glb_path = export_basic_glb(mesh, session_id=session_id)
        _update_progress("Exporting CPU GLB", 1, 1)
        result.update(
            {
                "render_paths": {},
                "preview_available": False,
                "extract_available": False,
                "glb_path": os.path.abspath(glb_path),
                "message": "Generated a geometry-only GLB on CPU hardware.",
            }
        )

    if runtime_messages:
        existing_message = result.get("message")
        message_parts = list(runtime_messages)
        if existing_message:
            message_parts.append(str(existing_message))
        result["message"] = " ".join(message_parts)

    _finish_progress()
    return result


def _extract_glb_impl(
    state_path: str,
    decimation_target: int,
    texture_size: int,
    session_id: str,
    execution_device: str,
) -> FileData:
    stage = "Preparing runtime"
    try:
        ensure_runtime_ready(preferred_device=execution_device)
        move_runtime_to(execution_device)
        install_progress_hooks()
    except Exception as exc:
        _fail_progress(stage, exc)
        raise

    _reset_progress(session_id)
    _update_progress("Decoding latent", 0, 1)

    extraction_settings = normalize_extraction_request(
        decimation_target=decimation_target,
        texture_size=texture_size,
        env=os.environ,
        cuda_available=torch.cuda.is_available(),
    )
    decimation_target = cast(int, extraction_settings["decimation_target"])
    texture_size = cast(int, extraction_settings["texture_size"])

    shape_slat, tex_slat, res = unpack_state(state_path, device=execution_device)
    mesh = pipeline.decode_latent(shape_slat, tex_slat, res)[0]  # pyright: ignore[reportOptionalMemberAccess]
    _update_progress("Decoding latent", 1, 1)

    if execution_device == "cpu":
        _update_progress("Exporting CPU GLB", 0, 1)
        out_glb = export_basic_glb(mesh, session_id=session_id)
        _update_progress("Exporting CPU GLB", 1, 1)
        _finish_progress()
        return FileData(path=out_glb)

    import o_voxel.postprocess as o_voxel_postprocess

    glb = o_voxel_postprocess.to_glb(
        vertices=mesh.vertices,
        faces=mesh.faces,
        attr_volume=mesh.attrs,
        coords=mesh.coords,
        attr_layout=pipeline.pbr_attr_layout,
        grid_size=res,
        aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
        decimation_target=decimation_target,
        texture_size=texture_size,
        remesh=True,
        remesh_band=1,
        remesh_project=0,
        use_tqdm=True,
    )
    rot = np.array(
        [
            [-1, 0, 0, 0],
            [0, 0, -1, 0],
            [0, -1, 0, 0],
            [0, 0, 0, 1],
        ],
        dtype=np.float64,
    )
    glb.apply_transform(rot)

    out_glb = os.path.join(TMP_DIR, f"result_{int(time.time() * 1000)}.glb")
    glb.export(out_glb, extension_webp=True)
    _finish_progress()
    return FileData(path=out_glb)


def generation_gpu_duration(
    image: FileData,
    seed: int,
    resolution: int,
    ss_guidance_strength: float = 7.5,
    ss_guidance_rescale: float = 0.7,
    ss_sampling_steps: int = 12,
    ss_rescale_t: float = 5.0,
    shape_slat_guidance_strength: float = 7.5,
    shape_slat_guidance_rescale: float = 0.5,
    shape_slat_sampling_steps: int = 12,
    shape_slat_rescale_t: float = 3.0,
    tex_slat_guidance_strength: float = 1.0,
    tex_slat_guidance_rescale: float = 0.0,
    tex_slat_sampling_steps: int = 12,
    tex_slat_rescale_t: float = 3.0,
    manual_fov: float = -1.0,
    fov_unit: str = "deg",
    session_id: str = "",
) -> int:
    runtime_mode = resolve_runtime_mode(os.environ, torch.cuda.is_available())
    if runtime_mode == "zerogpu":
        request_settings = normalize_generation_request(
            resolution=resolution,
            ss_sampling_steps=ss_sampling_steps,
            shape_slat_sampling_steps=shape_slat_sampling_steps,
            tex_slat_sampling_steps=tex_slat_sampling_steps,
            env=os.environ,
            cuda_available=torch.cuda.is_available(),
        )
        total_steps = (
            cast(int, request_settings["ss_sampling_steps"])
            + cast(int, request_settings["shape_slat_sampling_steps"])
            + cast(int, request_settings["tex_slat_sampling_steps"])
        )
        return min(
            ZEROGPU_GENERATION_MAX_DURATION_SECONDS,
            max(35, 20 + total_steps * 2),
        )

    # Cold model initialization is handled separately by `warmup_runtime`.
    return 60 if resolution <= 1024 else 180


def extract_glb_gpu_duration(
    state_path: str,
    decimation_target: int,
    texture_size: int,
    session_id: str = "",
) -> int:
    del state_path, decimation_target, texture_size, session_id
    if resolve_runtime_mode(os.environ, torch.cuda.is_available()) == "zerogpu":
        return ZEROGPU_EXTRACT_DURATION_SECONDS
    return 30


# ============================================================================
# API Implementation
# ============================================================================

app = Server()


def runtime_payload() -> dict[str, object]:
    payload = runtime_state.snapshot()
    cuda_available = torch.cuda.is_available()
    runtime_mode = resolve_runtime_mode(os.environ, cuda_available)
    payload["warmup_on_start"] = runtime_config.warmup_on_start
    payload["pipeline_resolved"] = resolved_pipeline_dir is not None
    payload["current_runtime_device"] = current_runtime_device
    payload["runtime_mode"] = runtime_mode
    payload["cuda_available"] = cuda_available
    payload["accelerator"] = os.environ.get("ACCELERATOR") or "unknown"
    payload["space_id"] = os.environ.get("SPACE_ID") or ""
    payload["preview_available"] = cuda_available
    target_hardware = resolve_target_hardware(os.environ)
    payload["target_hardware"] = target_hardware

    if runtime_mode == "zerogpu":
        payload["zerogpu_gpu_budgets"] = {
            "warmup_seconds": ZEROGPU_WARMUP_DURATION_SECONDS,
            "generation_max_seconds": ZEROGPU_GENERATION_MAX_DURATION_SECONDS,
            "extract_seconds": ZEROGPU_EXTRACT_DURATION_SECONDS,
            "max_texture_size": ZEROGPU_MAX_TEXTURE_SIZE,
            "max_stage_steps": ZEROGPU_MAX_STAGE_STEPS,
        }

    if runtime_mode == "cpu":
        payload["ready"] = False
        payload["state"] = "cpu-standby"
        payload["preview_available"] = False
        payload["message"] = cpu_runtime_message(
            target_hardware,
            bool(runtime_config.hf_token and payload["space_id"]),
        )
    return payload


@app.get("/")
async def homepage():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health():
    return JSONResponse(runtime_payload())


@app.get("/ready")
async def ready():
    payload = runtime_payload()
    status_code = 200 if payload["ready"] else 503
    return JSONResponse(payload, status_code=status_code)


@app.get("/progress")
async def progress_poll(request: Request):
    """Polling endpoint for real-time progress updates during generation."""
    session_id = request.query_params.get("session_id", "")
    path = _progress_file(session_id)
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return JSONResponse(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return JSONResponse(
            {"stage": "Waiting...", "step": 0, "total": 0, "done": False}
        )


@app.get("/queue/join")
async def queue_join(request: Request):
    session_id = request.query_params.get("session_id", "")
    if session_id:
        with _queue_lock:
            if (
                session_id not in _pending_sessions
                and session_id != _queue_running_session
            ):
                _pending_sessions.append(session_id)
                _pending_times[session_id] = time.time()
    return JSONResponse({"ok": True})


@app.get("/queue/leave")
async def queue_leave(request: Request):
    session_id = request.query_params.get("session_id", "")
    _remove_pending_session(session_id)
    return JSONResponse({"ok": True})


@app.get("/queue")
async def queue_status(request: Request):
    session_id = request.query_params.get("session_id", "")
    now = time.time()
    with _queue_lock:
        stale = [
            s
            for s in _pending_sessions
            if now - _pending_times.get(s, now) > _PENDING_TIMEOUT
        ]
        for s in stale:
            _pending_sessions.remove(s)
            _pending_times.pop(s, None)

        running_session = _queue_running_session
        pending = list(_pending_sessions)
        gpu_busy = bool(running_session)

    if session_id and session_id == running_session:
        position = 0
    elif session_id and session_id in pending:
        idx = pending.index(session_id)
        running_count = 1 if gpu_busy else 0
        ahead = idx + running_count
        position = ahead if ahead > 0 else -2
    else:
        position = -1

    total_ahead_for_unregistered = len(pending) + (1 if gpu_busy else 0)
    return JSONResponse(
        {
            "position": position,
            "total_waiting": len(pending),
            "gpu_busy": gpu_busy,
            "total_ahead_for_unregistered": total_ahead_for_unregistered,
        }
    )


@app.api()
def preprocess(image: FileData) -> FileData:
    img = Image.open(resolve_file_path(image))
    processed = preprocess_image_for_ui(img)
    out_path = os.path.join(TMP_DIR, f"preprocessed_{int(time.time() * 1000)}.png")
    processed.save(out_path)
    return FileData(path=out_path)


def warmup_gpu_duration(session_id: str = "") -> int:
    del session_id
    if resolve_runtime_mode(os.environ, torch.cuda.is_available()) == "zerogpu":
        return ZEROGPU_WARMUP_DURATION_SECONDS
    return 120


@app.api()
@spaces.GPU(duration=warmup_gpu_duration)
def warmup_runtime(session_id: str = "") -> Dict:
    _reset_progress(session_id)
    stage = "Preparing runtime"
    try:
        if resolve_runtime_mode(os.environ, torch.cuda.is_available()) == "cpu":
            _update_progress("Requesting ZeroGPU hardware", 1, 1)
            response = runtime_payload()
            response.update(cpu_transition_payload("warmup"))
            _finish_progress()
            return response
        _update_progress(stage, 0, 2)
        ensure_runtime_ready()
        stage = "Installing progress hooks"
        _update_progress(stage, 1, 2)
        install_progress_hooks()
        _finish_progress()
        return runtime_state.snapshot()
    except Exception as exc:
        _fail_progress(stage, exc)
        raise


@app.api()
@spaces.GPU(duration=generation_gpu_duration)
def generate_3d(
    image: FileData,
    seed: int,
    resolution: int,
    ss_guidance_strength: float = 7.5,
    ss_guidance_rescale: float = 0.7,
    ss_sampling_steps: int = 12,
    ss_rescale_t: float = 5.0,
    shape_slat_guidance_strength: float = 7.5,
    shape_slat_guidance_rescale: float = 0.5,
    shape_slat_sampling_steps: int = 12,
    shape_slat_rescale_t: float = 3.0,
    tex_slat_guidance_strength: float = 1.0,
    tex_slat_guidance_rescale: float = 0.0,
    tex_slat_sampling_steps: int = 12,
    tex_slat_rescale_t: float = 3.0,
    manual_fov: float = -1.0,
    fov_unit: str = "deg",
    session_id: str = "",
) -> Dict:
    plan = resolve_generation_plan(os.environ, torch.cuda.is_available())
    if plan["runtime_mode"] == "cpu":
        return cpu_transition_payload("generate")
    with acquire_inference(session_id):
        return _generate_3d_impl(
            image=image,
            seed=seed,
            resolution=resolution,
            ss_guidance_strength=ss_guidance_strength,
            ss_guidance_rescale=ss_guidance_rescale,
            ss_sampling_steps=ss_sampling_steps,
            ss_rescale_t=ss_rescale_t,
            shape_slat_guidance_strength=shape_slat_guidance_strength,
            shape_slat_guidance_rescale=shape_slat_guidance_rescale,
            shape_slat_sampling_steps=shape_slat_sampling_steps,
            shape_slat_rescale_t=shape_slat_rescale_t,
            tex_slat_guidance_strength=tex_slat_guidance_strength,
            tex_slat_guidance_rescale=tex_slat_guidance_rescale,
            tex_slat_sampling_steps=tex_slat_sampling_steps,
            tex_slat_rescale_t=tex_slat_rescale_t,
            manual_fov=manual_fov,
            fov_unit=fov_unit,
            session_id=session_id,
            execution_device=cast(str, plan["execution_device"]),
            render_preview=bool(plan["render_preview"]),
        )


@app.api()
@spaces.GPU(duration=extract_glb_gpu_duration)
def extract_glb_api(
    state_path: str, decimation_target: int, texture_size: int, session_id: str = ""
) -> FileData:
    plan = resolve_extraction_plan(os.environ, torch.cuda.is_available())
    if plan["runtime_mode"] == "cpu":
        raise RuntimeError(cpu_transition_payload("extract")["message"])
    with acquire_inference(session_id):
        return _extract_glb_impl(
            state_path=state_path,
            decimation_target=decimation_target,
            texture_size=texture_size,
            session_id=session_id,
            execution_device=cast(str, plan["execution_device"]),
        )


# Mount assets and tmp for direct access
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/tmp", StaticFiles(directory=TMP_DIR), name="tmp")

if __name__ == "__main__":
    start_runtime_warmup()
    app.launch(**build_launch_options(os.environ))

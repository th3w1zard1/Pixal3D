"""
Pixal3D (TRELLIS.2 Backbone) - Gradio App

Image-to-3D generation using Proj-mode Cascade inference (512->1024/1536).

"""

import gradio as gr

import os
import subprocess
subprocess.run([
    "pip", "install", "--force-reinstall", "--no-deps",
    "https://github.com/LDYang694/Storages/releases/download/20260430/utils3d-0.0.2-py3-none-any.whl"
], check=True)

os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import argparse
import math
import time
from datetime import datetime
import shutil
import cv2
from typing import *
import torch
import numpy as np
from PIL import Image
import base64
import io
from trellis2.modules.sparse import SparseTensor
from trellis2.pipelines import Pixal3DImageTo3DPipeline
from trellis2.renderers import EnvMap
from trellis2.utils import render_utils
import o_voxel


# ============================================================================
# Constants & Defaults
# ============================================================================

MAX_SEED = np.iinfo(np.int32).max
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
MODES = [
    {"name": "Normal", "icon": "assets/app/normal.png", "render_key": "normal"},
    {"name": "Clay render", "icon": "assets/app/clay.png", "render_key": "clay"},
    {"name": "Base color", "icon": "assets/app/basecolor.png", "render_key": "base_color"},
    {"name": "HDRI forest", "icon": "assets/app/hdri_forest.png", "render_key": "shaded_forest"},
    {"name": "HDRI sunset", "icon": "assets/app/hdri_sunset.png", "render_key": "shaded_sunset"},
    {"name": "HDRI courtyard", "icon": "assets/app/hdri_courtyard.png", "render_key": "shaded_courtyard"},
]
STEPS = 8
DEFAULT_MODE = 3
DEFAULT_STEP = 0

# Cascade parameters
CASCADE_LR_RESOLUTION = 512
CASCADE_MAX_NUM_TOKENS = 49152

# MoGe defaults
MOGE_MODEL_NAME = "Ruicheng/moge-2-vitl"
WILD_MESH_SCALE = 1.0
WILD_EXTEND_PIXEL = 0
WILD_IMAGE_RESOLUTION = 512

# Image Cond Model configs (extracted from training configs, hardcoded)
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
# CSS & JS
# ============================================================================

css = """
.stepper-wrapper { padding: 0; }
.stepper-container { padding: 0; align-items: center; }
.step-button { flex-direction: row; }
.step-connector { transform: none; }
.step-number { width: 16px; height: 16px; }
.step-label { position: relative; bottom: 0; }
.wrap.center.full { inset: 0; height: 100%; }
.wrap.center.full.translucent { background: var(--block-background-fill); }
.meta-text-center {
    display: block !important; position: absolute !important;
    top: unset !important; bottom: 0 !important; right: 0 !important; transform: unset !important;
}
.previewer-container {
    position: relative;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    width: 100%; height: 722px; margin: 0 auto; padding: 20px;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.previewer-container .tips-icon {
    position: absolute; right: 10px; top: 10px; z-index: 10;
    border-radius: 10px; color: #fff; background-color: var(--color-accent); padding: 3px 6px; user-select: none;
}
.previewer-container .tips-text {
    position: absolute; right: 10px; top: 50px; color: #fff; background-color: var(--color-accent);
    border-radius: 10px; padding: 6px; text-align: left; max-width: 300px; z-index: 10;
    transition: all 0.3s; opacity: 0%; user-select: none;
}
.previewer-container .tips-text p { font-size: 14px; line-height: 1.2; }
.tips-icon:hover + .tips-text { display: block; opacity: 100%; }
.previewer-container .mode-row {
    width: 100%; display: flex; gap: 8px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap;
}
.previewer-container .mode-btn {
    width: 24px; height: 24px; border-radius: 50%; cursor: pointer; opacity: 0.5;
    transition: all 0.2s; border: 2px solid #ddd; object-fit: cover;
}
.previewer-container .mode-btn:hover { opacity: 0.9; transform: scale(1.1); }
.previewer-container .mode-btn.active { opacity: 1; border-color: var(--color-accent); transform: scale(1.1); }
.previewer-container .display-row {
    margin-bottom: 20px; min-height: 400px; width: 100%; flex-grow: 1;
    display: flex; justify-content: center; align-items: center;
}
.previewer-container .previewer-main-image {
    max-width: 100%; max-height: 100%; flex-grow: 1; object-fit: contain; display: none;
}
.previewer-container .previewer-main-image.visible { display: block; }
.previewer-container .slider-row {
    width: 100%; display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 0 10px;
}
.previewer-container input[type=range] { -webkit-appearance: none; width: 100%; max-width: 400px; background: transparent; }
.previewer-container input[type=range]::-webkit-slider-runnable-track {
    width: 100%; height: 8px; cursor: pointer; background: #ddd; border-radius: 5px;
}
.previewer-container input[type=range]::-webkit-slider-thumb {
    height: 20px; width: 20px; border-radius: 50%; background: var(--color-accent);
    cursor: pointer; -webkit-appearance: none; margin-top: -6px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: transform 0.1s;
}
.previewer-container input[type=range]::-webkit-slider-thumb:hover { transform: scale(1.2); }
.gradio-container .padded:has(.previewer-container) { padding: 0 !important; }
.gradio-container:has(.previewer-container) [data-testid="block-label"] { position: absolute; top: 0; left: 0; }
"""

head = """
<script>
    function refreshView(mode, step) {
        const allImgs = document.querySelectorAll('.previewer-main-image');
        for (let i = 0; i < allImgs.length; i++) {
            const img = allImgs[i];
            if (img.classList.contains('visible')) {
                const id = img.id;
                const [_, m, s] = id.split('-');
                if (mode === -1) mode = parseInt(m.slice(1));
                if (step === -1) step = parseInt(s.slice(1));
                break;
            }
        }
        allImgs.forEach(img => img.classList.remove('visible'));
        const targetId = 'view-m' + mode + '-s' + step;
        const targetImg = document.getElementById(targetId);
        if (targetImg) targetImg.classList.add('visible');
        const allBtns = document.querySelectorAll('.mode-btn');
        allBtns.forEach((btn, idx) => {
            if (idx === mode) btn.classList.add('active');
            else btn.classList.remove('active');
        });
    }
    function selectMode(mode) { refreshView(mode, -1); }
    function onSliderChange(val) { refreshView(-1, parseInt(val)); }
</script>
"""

empty_html = f"""
<div class="previewer-container">
    <svg style=" opacity: .5; height: var(--size-5); color: var(--body-text-color);"
    xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-image"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
</div>
"""


# ============================================================================
# Model Loading Utilities
# ============================================================================

def build_image_cond_model(config: dict):
    """Build DinoV3ProjFeatureExtractor."""
    from trellis2.trainers.flow_matching.mixins.image_conditioned_proj import DinoV3ProjFeatureExtractor
    model = DinoV3ProjFeatureExtractor(**config)
    model.eval()
    return model


# ============================================================================
# Camera Parameter Utilities
# ============================================================================

def compute_f_pixels(camera_angle_x: float, resolution: int) -> float:
    focal_length = 16.0 / torch.tan(torch.tensor(camera_angle_x / 2.0))
    f_pixels = focal_length * resolution / 32.0
    return float(f_pixels.item())


def distance_from_fov(camera_angle_x, grid_point, target_point, mesh_scale, image_resolution):
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


def load_moge_model(device="cuda", model_name=MOGE_MODEL_NAME):
    print(f"[MoGe-2] Loading model {model_name}...")
    from moge.model.v2 import MoGeModel
    moge_model = MoGeModel.from_pretrained(model_name).to(device)
    moge_model.eval()
    print("[MoGe-2] Model loaded!")
    return moge_model


def get_camera_params_wild_moge(image, moge_model, device="cuda",
                                 mesh_scale=1.0, extend_pixel=0, image_resolution=512):
    """Estimate camera parameters via MoGe-2."""
    if isinstance(image, str):
        pil_image = Image.open(image).convert("RGB")
    elif isinstance(image, Image.Image):
        pil_image = image.convert("RGB")
    else:
        raise ValueError(f"Unsupported image type: {type(image)}")
    width, height = pil_image.size
    image_np = np.array(pil_image).astype(np.float32) / 255.0
    image_tensor = torch.from_numpy(image_np).permute(2, 0, 1).to(device)
    with torch.no_grad():
        output = moge_model.infer(image_tensor)
    intrinsics = output["intrinsics"].squeeze().cpu().numpy()
    fx_normalized = intrinsics[0, 0]
    fx = fx_normalized * width
    camera_angle_x = 2 * math.atan(width / (2 * fx))

    grid_point = torch.tensor([-1.0, 0.0, 0.0])
    distance = distance_from_fov(
        camera_angle_x, grid_point,
        torch.tensor([0 - extend_pixel, image_resolution - 1 + extend_pixel]),
        mesh_scale, image_resolution
    )["distance_from_x"]
    return {'camera_angle_x': camera_angle_x, 'distance': distance, 'mesh_scale': mesh_scale}


# ============================================================================
# UI Utilities
# ============================================================================

def image_to_base64(image):
    buffered = io.BytesIO()
    image = image.convert("RGB")
    image.save(buffered, format="jpeg", quality=85)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"


def start_session(req: gr.Request):
    user_dir = os.path.join(TMP_DIR, str(req.session_hash))
    os.makedirs(user_dir, exist_ok=True)


def end_session(req: gr.Request):
    user_dir = os.path.join(TMP_DIR, str(req.session_hash))
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)


def preprocess_image(image: Image.Image) -> Image.Image:
    return pipeline.preprocess_image(image)


def pack_state(shape_slat, tex_slat, res):
    return {
        'shape_slat_feats': shape_slat.feats.cpu().numpy(),
        'tex_slat_feats': tex_slat.feats.cpu().numpy(),
        'coords': shape_slat.coords.cpu().numpy(),
        'res': res,
    }


def unpack_state(state):
    shape_slat = SparseTensor(
        feats=torch.from_numpy(state['shape_slat_feats']).cuda(),
        coords=torch.from_numpy(state['coords']).cuda(),
    )
    tex_slat = shape_slat.replace(torch.from_numpy(state['tex_slat_feats']).cuda())
    return shape_slat, tex_slat, state['res']


def get_seed(randomize_seed, seed):
    return np.random.randint(0, MAX_SEED) if randomize_seed else seed


# ============================================================================
# Core Inference
# ============================================================================

def image_to_3d(
    image, seed, resolution,
    ss_guidance_strength, ss_guidance_rescale, ss_sampling_steps, ss_rescale_t,
    shape_slat_guidance_strength, shape_slat_guidance_rescale, shape_slat_sampling_steps, shape_slat_rescale_t,
    tex_slat_guidance_strength, tex_slat_guidance_rescale, tex_slat_sampling_steps, tex_slat_rescale_t,
    req: gr.Request,
    progress=gr.Progress(track_tqdm=True),
):
    device = pipeline.device
    torch.manual_seed(seed)
    hr_resolution = int(resolution)

    total_t0 = time.time()
    print(f"\n{'='*60}")
    print(f"  [Generate] Start | seed={seed}, resolution={hr_resolution}")
    print(f"{'='*60}")

    # Preprocessing
    image_preprocessed = pipeline.preprocess_image(image)

    # Camera estimation via MoGe-2
    camera_params = get_camera_params_wild_moge(
        image_preprocessed, moge_model, device=str(device),
        mesh_scale=WILD_MESH_SCALE, extend_pixel=WILD_EXTEND_PIXEL,
        image_resolution=WILD_IMAGE_RESOLUTION,
    )

    ss_sampler_override = {"steps": ss_sampling_steps, "guidance_strength": ss_guidance_strength,
                           "guidance_rescale": ss_guidance_rescale, "rescale_t": ss_rescale_t}
    shape_sampler_override = {"steps": shape_slat_sampling_steps, "guidance_strength": shape_slat_guidance_strength,
                              "guidance_rescale": shape_slat_guidance_rescale, "rescale_t": shape_slat_rescale_t}
    tex_sampler_override = {"steps": tex_slat_sampling_steps, "guidance_strength": tex_slat_guidance_strength,
                            "guidance_rescale": tex_slat_guidance_rescale, "rescale_t": tex_slat_rescale_t}

    # Run pipeline
    pipeline_type = f"{hr_resolution}_cascade"
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
    state = pack_state(shape_slat, tex_slat, res)
    del shape_slat, tex_slat, mesh_list
    torch.cuda.empty_cache()

    # Render
    mesh.simplify(16777216)
    images = render_utils.render_proj_aligned_video(
        mesh, camera_angle_x=camera_params['camera_angle_x'],
        distance=camera_params['distance'], resolution=1024,
        num_frames=STEPS, envmap=envmap,
    )
    del mesh
    torch.cuda.empty_cache()
    print(f"\n  [Generate] Total time: {time.time()-total_t0:.2f}s")

    # Build HTML
    images_html = ""
    for m_idx, mode in enumerate(MODES):
        for s_idx in range(STEPS):
            unique_id = f"view-m{m_idx}-s{s_idx}"
            is_visible = (m_idx == DEFAULT_MODE and s_idx == DEFAULT_STEP)
            vis_class = "visible" if is_visible else ""
            img_base64 = image_to_base64(Image.fromarray(images[mode['render_key']][s_idx]))
            images_html += f'<img id="{unique_id}" class="previewer-main-image {vis_class}" src="{img_base64}" loading="eager">'

    btns_html = ""
    for idx, mode in enumerate(MODES):
        active_class = "active" if idx == DEFAULT_MODE else ""
        btns_html += f'<img src="{mode["icon_base64"]}" class="mode-btn {active_class}" onclick="selectMode({idx})" title="{mode["name"]}">'

    full_html = f"""
    <div class="previewer-container">
        <div class="tips-wrapper">
            <div class="tips-icon">Tips</div>
            <div class="tips-text">
                <p>Render Mode - Click circular buttons to switch render modes.</p>
                <p>View Angle - Drag the slider to change the view angle.</p>
            </div>
        </div>
        <div class="display-row">{images_html}</div>
        <div class="mode-row" id="btn-group">{btns_html}</div>
        <div class="slider-row">
            <input type="range" id="custom-slider" min="0" max="{STEPS - 1}" value="{DEFAULT_STEP}" step="1" oninput="onSliderChange(this.value)">
        </div>
    </div>
    """
    return state, full_html


def extract_glb(state, decimation_target, texture_size, req: gr.Request, progress=gr.Progress(track_tqdm=True)):
    user_dir = os.path.join(TMP_DIR, str(req.session_hash))
    shape_slat, tex_slat, res = unpack_state(state)
    mesh = pipeline.decode_latent(shape_slat, tex_slat, res)[0]
    glb = o_voxel.postprocess.to_glb(
        vertices=mesh.vertices, faces=mesh.faces, attr_volume=mesh.attrs,
        coords=mesh.coords, attr_layout=pipeline.pbr_attr_layout,
        grid_size=res, aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
        decimation_target=decimation_target, texture_size=texture_size,
        remesh=True, remesh_band=1, remesh_project=0, use_tqdm=True,
    )
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%dT%H%M%S") + f".{now.microsecond // 1000:03d}"
    os.makedirs(user_dir, exist_ok=True)
    glb_path = os.path.join(user_dir, f'sample_{timestamp}.glb')
    glb.export(glb_path, extension_webp=True)
    torch.cuda.empty_cache()
    return glb_path, glb_path


# ============================================================================
# Gradio UI
# ============================================================================

with gr.Blocks(delete_cache=(600, 600)) as demo:
    gr.Markdown("""
    ## Image to 3D Asset with Pixal3D (TRELLIS.2 Backbone)
    * Upload an image and click **Generate** to create a 3D asset using Pixal3D with TRELLIS.2 backbone.
    * Click **Extract GLB** to export and download the generated GLB file.
    * Camera parameters are estimated automatically via MoGe-2.
    """)

    with gr.Row():
        with gr.Column(scale=1, min_width=360):
            image_prompt = gr.Image(label="Image Prompt", format="png", image_mode="RGBA", type="pil", height=400)
            resolution = gr.Radio(["1024", "1536"], label="Resolution", value="1536")
            seed = gr.Slider(0, MAX_SEED, label="Seed", value=42, step=1)
            randomize_seed = gr.Checkbox(label="Randomize Seed", value=True)
            decimation_target = gr.Slider(100000, 1000000, label="Decimation Target", value=1000000, step=10000)
            texture_size = gr.Slider(1024, 4096, label="Texture Size", value=4096, step=1024)
            generate_btn = gr.Button("Generate")

            with gr.Accordion(label="Advanced Settings", open=False):
                gr.Markdown("Stage 1: Sparse Structure Generation")
                with gr.Row():
                    ss_guidance_strength = gr.Slider(1.0, 10.0, label="Guidance Strength", value=7.5, step=0.1)
                    ss_guidance_rescale = gr.Slider(0.0, 1.0, label="Guidance Rescale", value=0.7, step=0.01)
                    ss_sampling_steps = gr.Slider(1, 50, label="Sampling Steps", value=12, step=1)
                    ss_rescale_t = gr.Slider(1.0, 6.0, label="Rescale T", value=5.0, step=0.1)
                gr.Markdown("Stage 2: Shape Generation")
                with gr.Row():
                    shape_slat_guidance_strength = gr.Slider(1.0, 10.0, label="Guidance Strength", value=7.5, step=0.1)
                    shape_slat_guidance_rescale = gr.Slider(0.0, 1.0, label="Guidance Rescale", value=0.5, step=0.01)
                    shape_slat_sampling_steps = gr.Slider(1, 50, label="Sampling Steps", value=12, step=1)
                    shape_slat_rescale_t = gr.Slider(1.0, 6.0, label="Rescale T", value=3.0, step=0.1)
                gr.Markdown("Stage 3: Material Generation")
                with gr.Row():
                    tex_slat_guidance_strength = gr.Slider(1.0, 10.0, label="Guidance Strength", value=1.0, step=0.1)
                    tex_slat_guidance_rescale = gr.Slider(0.0, 1.0, label="Guidance Rescale", value=0.0, step=0.01)
                    tex_slat_sampling_steps = gr.Slider(1, 50, label="Sampling Steps", value=12, step=1)
                    tex_slat_rescale_t = gr.Slider(1.0, 6.0, label="Rescale T", value=3.0, step=0.1)

        with gr.Column(scale=10):
            with gr.Walkthrough(selected=0) as walkthrough:
                with gr.Step("Preview", id=0):
                    preview_output = gr.HTML(empty_html, label="3D Asset Preview", show_label=True, container=True)
                    extract_btn = gr.Button("Extract GLB")
                with gr.Step("Extract", id=1):
                    glb_output = gr.Model3D(label="Extracted GLB", height=724, show_label=True, display_mode="solid", clear_color=(0.25, 0.25, 0.25, 1.0), camera_position=(90, 0, None))
                    download_btn = gr.DownloadButton(label="Download GLB")

        with gr.Column(scale=1, min_width=172):
            examples = gr.Examples(
                examples=[f'assets/example_image/{image}' for image in os.listdir("assets/example_image")],
                inputs=[image_prompt], fn=preprocess_image, outputs=[image_prompt],
                run_on_click=True, examples_per_page=18,
            )

    output_buf = gr.State()

    demo.load(start_session)
    demo.unload(end_session)
    image_prompt.upload(preprocess_image, inputs=[image_prompt], outputs=[image_prompt])

    generate_btn.click(get_seed, inputs=[randomize_seed, seed], outputs=[seed]).then(
        lambda: gr.Walkthrough(selected=0), outputs=walkthrough
    ).then(
        image_to_3d,
        inputs=[image_prompt, seed, resolution,
                ss_guidance_strength, ss_guidance_rescale, ss_sampling_steps, ss_rescale_t,
                shape_slat_guidance_strength, shape_slat_guidance_rescale, shape_slat_sampling_steps, shape_slat_rescale_t,
                tex_slat_guidance_strength, tex_slat_guidance_rescale, tex_slat_sampling_steps, tex_slat_rescale_t],
        outputs=[output_buf, preview_output],
    )

    extract_btn.click(lambda: gr.Walkthrough(selected=1), outputs=walkthrough).then(
        extract_glb, inputs=[output_buf, decimation_target, texture_size], outputs=[glb_output, download_btn],
    )


# ============================================================================
# Launch
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Pixal3D Gradio App")
    parser.add_argument("--model_path", type=str, default="TencentARC/Pixal3D-T",
                        help="HuggingFace repo ID or local path (default: TencentARC/Pixal3D-T)")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true", default=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    os.makedirs(TMP_DIR, exist_ok=True)

    # Construct UI icon base64
    for i in range(len(MODES)):
        icon = Image.open(MODES[i]['icon'])
        MODES[i]['icon_base64'] = image_to_base64(icon)

    # Load pipeline from HuggingFace or local path
    print(f"[Pipeline] Loading from {args.model_path}...")
    pipeline = Pixal3DImageTo3DPipeline.from_pretrained(args.model_path)

    # Load environment maps
    envmap = {
        'forest': EnvMap(torch.tensor(cv2.cvtColor(cv2.imread('assets/hdri/forest.exr', cv2.IMREAD_UNCHANGED), cv2.COLOR_BGR2RGB), dtype=torch.float32, device='cuda')),
        'sunset': EnvMap(torch.tensor(cv2.cvtColor(cv2.imread('assets/hdri/sunset.exr', cv2.IMREAD_UNCHANGED), cv2.COLOR_BGR2RGB), dtype=torch.float32, device='cuda')),
        'courtyard': EnvMap(torch.tensor(cv2.cvtColor(cv2.imread('assets/hdri/courtyard.exr', cv2.IMREAD_UNCHANGED), cv2.COLOR_BGR2RGB), dtype=torch.float32, device='cuda')),
    }

    # Build image cond models and set on pipeline
    print("[ImageCond] Building DinoV3ProjFeatureExtractor models...")
    pipeline.image_cond_model_ss = build_image_cond_model(IMAGE_COND_CONFIGS["ss"])
    pipeline.image_cond_model_shape_512 = build_image_cond_model(IMAGE_COND_CONFIGS["shape_512"])
    pipeline.image_cond_model_shape_1024 = build_image_cond_model(IMAGE_COND_CONFIGS["shape_1024"])
    pipeline.image_cond_model_tex_1024 = build_image_cond_model(IMAGE_COND_CONFIGS["tex_1024"])

    pipeline.cuda()

    # Pre-download NAF model (avoid lazy-loading during inference)
    print("[NAF] Pre-loading NAF upsampler model...")
    for attr in ['image_cond_model_ss', 'image_cond_model_shape_512', 'image_cond_model_shape_1024', 'image_cond_model_tex_1024']:
        model = getattr(pipeline, attr, None)
        if model is not None and getattr(model, 'use_naf_upsample', False):
            model._load_naf()
    print("[NAF] NAF model loaded.")

    # Load MoGe-2
    print("\n[MoGe-2] Loading model for camera estimation...")
    moge_model = load_moge_model(device="cuda")

    print(f"\n{'=' * 60}")
    print(f"  Pixal3D ready! Model loaded from: {args.model_path}")
    print(f"  Cascade: {CASCADE_LR_RESOLUTION} -> 1024/1536")
    print(f"{'=' * 60}\n")

    demo.launch(css=css, head=head, server_port=args.port, share=args.share)

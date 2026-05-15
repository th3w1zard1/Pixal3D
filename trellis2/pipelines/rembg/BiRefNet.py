from typing import *
from transformers import AutoModelForImageSegmentation
import torch
from torchvision import transforms
from PIL import Image
from huggingface_hub.utils import HfHubHTTPError
from space_bootstrap import (
    RuntimeConfig,
    build_hf_hub_kwargs,
    build_runtime_config,
    candidate_rembg_models,
    is_gated_model_reference,
)


class BiRefNet:
    def __init__(
        self,
        model_name: str = "ZhengPeng7/BiRefNet",
        fallback_model_names: list[str] | tuple[str, ...] | None = None,
        trust_remote_code: bool | None = None,
    ):
        runtime_config = build_runtime_config()
        primary_model = (
            runtime_config.rembg_model
            if is_gated_model_reference(model_name)
            else model_name
        )
        fallback_models = (
            tuple(fallback_model_names)
            if fallback_model_names is not None
            else runtime_config.rembg_fallback_models
        )
        candidate_config = RuntimeConfig(
            hf_token=runtime_config.hf_token,
            hf_cache_dir=runtime_config.hf_cache_dir,
            pipeline_revision=runtime_config.pipeline_revision,
            rembg_model=primary_model,
            rembg_fallback_models=fallback_models,
            rembg_trust_remote_code=runtime_config.rembg_trust_remote_code,
            warmup_on_start=runtime_config.warmup_on_start,
        )
        trust_remote_code = (
            runtime_config.rembg_trust_remote_code
            if trust_remote_code is None
            else trust_remote_code
        )
        hub_kwargs = build_hf_hub_kwargs(runtime_config, include_revision=False)
        tried: list[tuple[str, str]] = []
        self.model: Any = None
        self.loaded_model_name = None
        self._device = "cpu"

        for candidate in candidate_rembg_models(candidate_config):
            try:
                self.model = AutoModelForImageSegmentation.from_pretrained(
                    candidate,
                    trust_remote_code=trust_remote_code,
                    **hub_kwargs,
                )
                self.loaded_model_name = candidate
                if candidate != model_name:
                    print(
                        f"[BiRefNet] Using fallback model '{candidate}' instead of '{model_name}'."
                    )
                break
            except (OSError, HfHubHTTPError) as e:
                tried.append((candidate, str(e).splitlines()[0]))
            except Exception as e:
                tried.append((candidate, f"{type(e).__name__}: {e}"))

        if self.model is None:
            details = "\n".join([f"- {name}: {err}" for name, err in tried])
            raise RuntimeError(
                "Failed to load any background-removal model. Tried:\n"
                f"{details}\n"
                "If you need a gated model, set HF_TOKEN with approved access."
            )

        self.model.eval()
        self.transform_image = transforms.Compose(
            [
                transforms.Resize((1024, 1024)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
    
    def to(self, device: str):
        assert self.model is not None
        self._device = device
        self.model.to(device)

    def cuda(self):
        assert self.model is not None
        self._device = "cuda"
        self.model.cuda()

    def cpu(self):
        assert self.model is not None
        self._device = "cpu"
        self.model.cpu()
        
    def __call__(self, image: Image.Image) -> Image.Image:
        assert self.model is not None
        image_size = image.size
        input_images = self.transform_image(image).unsqueeze(0).to(self._device)
        # Prediction
        with torch.no_grad():
            outputs = self.model(input_images)
            if isinstance(outputs, (tuple, list)):
                pred_tensor = outputs[-1]
            elif hasattr(outputs, "logits"):
                pred_tensor = outputs.logits
            elif isinstance(outputs, dict):
                pred_tensor = outputs.get("logits") or outputs.get("pred")
                if pred_tensor is None:
                    raise RuntimeError("Unsupported segmentation output keys.")
            else:
                pred_tensor = outputs
            preds = pred_tensor.sigmoid().cpu()
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(image_size)
        image.putalpha(mask)
        return image
    
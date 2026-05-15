from typing import *
import os
from transformers import AutoModelForImageSegmentation
import torch
from torchvision import transforms
from PIL import Image
from huggingface_hub.utils import HfHubHTTPError


class BiRefNet:
    def __init__(self, model_name: str = "ZhengPeng7/BiRefNet"):
        # Try configured model first, then high-quality public fallbacks.
        fallback_models = [
            model_name,
            "ZhengPeng7/BiRefNet",
            "briaai/RMBG-1.4",
        ]
        tried: list[tuple[str, str]] = []
        self.model: Any = None
        self.loaded_model_name = None
        self._device = "cpu"
        hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")

        for candidate in dict.fromkeys(fallback_models):
            try:
                self.model = AutoModelForImageSegmentation.from_pretrained(
                    candidate,
                    trust_remote_code=True,
                    token=hf_token,
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
            preds = self.model(input_images)[-1].sigmoid().cpu()
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(image_size)
        image.putalpha(mask)
        return image
    
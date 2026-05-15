import importlib

import torch
import utils3d


def _load_utils3d_torch_helper(name: str, module_name: str):
    helper = getattr(utils3d.torch, name, None)
    if callable(helper):
        return helper

    module = getattr(utils3d.torch, module_name, None)
    if module is None:
        module = importlib.import_module(f"utils3d.torch.{module_name}")

    helper = getattr(module, name, None)
    if callable(helper):
        setattr(utils3d.torch, name, helper)
        return helper

    return None


def intrinsics_from_fov_xy_compat(fov_x, fov_y):
    helper = _load_utils3d_torch_helper("intrinsics_from_fov_xy", "transforms")
    if callable(helper):
        return helper(fov_x, fov_y)

    helper = _load_utils3d_torch_helper("intrinsics_from_fov", "transforms")
    if callable(helper):
        return helper(fov_x=fov_x, fov_y=fov_y)

    raise AttributeError(
        "utils3d.torch is missing both intrinsics_from_fov_xy and intrinsics_from_fov"
    )


def get_image_rays_compat(extrinsics, intrinsics, width: int, height: int):
    helper = _load_utils3d_torch_helper("get_image_rays", "nerf")
    if callable(helper):
        return helper(extrinsics, intrinsics, width, height)

    u = torch.linspace(
        0.5 / width,
        (width - 0.5) / width,
        width,
        device=extrinsics.device,
        dtype=extrinsics.dtype,
    )
    v = torch.linspace(
        0.5 / height,
        (height - 0.5) / height,
        height,
        device=extrinsics.device,
        dtype=extrinsics.dtype,
    )
    u, v = torch.meshgrid(u, v, indexing="xy")
    uv = torch.stack([u, v], dim=-1).reshape(-1, 2)
    uvz = torch.cat([uv, torch.ones_like(uv[..., :1])], dim=-1)

    with torch.cuda.amp.autocast(enabled=False):
        inv_transformation = (intrinsics @ extrinsics[..., :3, :3]).inverse()
        inv_extrinsics = extrinsics.inverse()

    rays_d = uvz @ inv_transformation.transpose(-1, -2)
    rays_o = inv_extrinsics[..., None, :3, 3]
    rays_o = rays_o.unflatten(-2, (1, 1))
    rays_d = rays_d.unflatten(-2, (height, width))
    return rays_o, rays_d

import importlib

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

    raise AttributeError("utils3d.torch is missing get_image_rays")

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any


def resolve_file_path(file_ref: Any) -> str:
    """Return a local file path from Gradio-style file payloads.

    Gradio can hand API functions either a dict-like FileData payload, a
    FileData object with a ``path`` attribute, or a plain string path when a
    prior API call already returned the staged file location.
    """
    if isinstance(file_ref, str):
        return file_ref

    if isinstance(file_ref, os.PathLike):
        return os.fspath(file_ref)

    if isinstance(file_ref, Mapping):
        path = file_ref.get("path")
        if isinstance(path, (str, os.PathLike)):
            return os.fspath(path)

    path = getattr(file_ref, "path", None)
    if isinstance(path, (str, os.PathLike)):
        return os.fspath(path)

    raise TypeError(
        "Expected a Gradio file payload with a local path, got "
        f"{type(file_ref).__name__}"
    )
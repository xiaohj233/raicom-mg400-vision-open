from __future__ import annotations

import os
from pathlib import Path


def use_script_dir(file):
    """Change current working directory to the folder containing *file*.

    Kept for compatibility with the original three-file competition version.
    For this open-source repository, prefer running examples from the repo root.
    """
    p = Path(file).resolve().parent
    os.chdir(p)
    return p


def use_repo_root(file, marker="pyproject.toml"):
    """Change current working directory to the repository root.

    The handwrite examples live in ``handwrite/`` while datasets, models and
    runtime images live at the repository root. This helper makes the examples
    runnable from either the root directory or the handwrite directory.
    """
    p = Path(file).resolve()
    for parent in (p.parent, *p.parents):
        if (parent / marker).exists() or (parent / "vision_motion_kit").is_dir():
            os.chdir(parent)
            return parent
    os.chdir(p.parent)
    return p.parent


def project_root():
    return Path.cwd()


def normalize_project_path(path):
    text = str(path).strip().strip('"')
    if not text:
        return Path(text)
    if (text.startswith("\\") or text.startswith("/")) and not (len(text) > 2 and text[1] == ":"):
        return Path.cwd() / text.lstrip("\\/")
    p = Path(text)
    if p.is_absolute():
        return p
    return Path.cwd() / p

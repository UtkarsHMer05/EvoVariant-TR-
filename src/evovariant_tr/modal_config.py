"""Modal setup for EvoVariant-TR (Milestone 51-53).

This module defines the Modal image and app configuration for running
Evo 2 scoring. It is designed to be imported by the Modal CLI.

Usage:
    modal deploy evo2_scorer_app.py
"""

from __future__ import annotations

import os
from typing import Any

PARITY_REQUIREMENTS = {
    "image": "nvidia/cuda:12.4.0-devel-ubuntu22.04",
    "python": "3.12",
    "packages": [
        "torch==2.4.0",
        "evo2",
        "transformer-engine[pytorch]==1.13",
        "flash-attn==2.6.3",
    ],
    "gpu": "A100",
    "min_vram_gb": 24,
}


def get_modal_config() -> dict[str, Any]:
    """Return the Modal deployment configuration."""
    return {
        "app_name": "evovariant-tr",
        "image": os.environ.get("EVO2_IMAGE", PARITY_REQUIREMENTS["image"]),
        "python_version": PARITY_REQUIREMENTS["python"],
        "gpu_type": os.environ.get("EVO2_GPU_TYPE", PARITY_REQUIREMENTS["gpu"]),
        "min_vram_gb": PARITY_REQUIREMENTS["min_vram_gb"],
        "packages": PARITY_REQUIREMENTS["packages"],
    }


def get_modal_secrets() -> list[str]:
    """List required secrets for Modal deployment."""
    return [
        "huggingface-token",
    ]


def get_modal_volumes() -> dict[str, str]:
    """Return volume mount configuration."""
    cache_dir = os.environ.get(
        "HF_CACHE_DIR", "/root/.cache/huggingface"
    )
    return {cache_dir: "hf_cache"}


def check_modal_environment() -> dict[str, Any]:
    """Check if Modal is properly configured."""
    checks: dict[str, Any] = {}

    try:
        import modal  # noqa: F401
        checks["modal_installed"] = True
    except ImportError:
        checks["modal_installed"] = "modal package not installed"
        checks["modal_authenticated"] = "modal not installed"
        return checks

    try:
        import subprocess  # noqa: PLC0415
        result = subprocess.run(
            ["modal", "app", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        checks["modal_authenticated"] = result.returncode == 0
    except Exception as e:
        checks["modal_authenticated"] = f"Check failed: {e}"

    return checks
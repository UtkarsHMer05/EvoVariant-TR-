"""Tests for modal_config.py — Milestones 51-53."""

from __future__ import annotations

from evovariant_tr.modal_config import (
    PARITY_REQUIREMENTS,
    check_modal_environment,
    get_modal_config,
    get_modal_secrets,
    get_modal_volumes,
)


def test_parity_requirements():
    assert PARITY_REQUIREMENTS["image"].startswith("nvidia/cuda")
    assert PARITY_REQUIREMENTS["python"] == "3.12"
    assert "torch==2.4.0" in PARITY_REQUIREMENTS["packages"]
    assert "evo2" in PARITY_REQUIREMENTS["packages"]
    assert PARITY_REQUIREMENTS["gpu"] == "A100"
    assert PARITY_REQUIREMENTS["min_vram_gb"] == 24


def test_get_modal_config():
    config = get_modal_config()
    assert config["app_name"] == "evovariant-tr"
    assert "nvidia/cuda" in config["image"]
    assert config["python_version"] == "3.12"
    assert config["gpu_type"] == "A100"
    assert isinstance(config["packages"], list)
    assert len(config["packages"]) > 0


def test_get_modal_config_environment_override():
    import os
    os.environ["EVO2_GPU_TYPE"] = "H100"
    try:
        config = get_modal_config()
        assert config["gpu_type"] == "H100"
    finally:
        del os.environ["EVO2_GPU_TYPE"]


def test_get_modal_secrets():
    secrets = get_modal_secrets()
    assert "huggingface-token" in secrets


def test_get_modal_volumes():
    volumes = get_modal_volumes()
    assert "hf_cache" in volumes.values()
    assert any("huggingface" in path for path in volumes.keys())


def test_check_modal_environment():
    """Should return a dict with check results."""
    result = check_modal_environment()
    assert "modal_installed" in result
    assert "modal_authenticated" in result


def test_parity_requirements_frozen():
    """Parity requirements should be immutable in intent."""
    assert PARITY_REQUIREMENTS["min_vram_gb"] == 24
    assert PARITY_REQUIREMENTS["gpu"] == "A100"
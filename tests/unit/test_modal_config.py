"""Tests for modal_config.py — Milestones 51-53."""

from __future__ import annotations

import builtins
import subprocess
import sys
from types import SimpleNamespace

import evovariant_tr.modal_config as modal_config_module
from evovariant_tr.modal_config import (
    PARITY_REQUIREMENTS,
    check_modal_environment,
    get_modal_config,
    get_modal_secrets,
    get_modal_volumes,
)


def test_parity_requirements():
    assert PARITY_REQUIREMENTS["image"].startswith("nvcr.io/nvidia/pytorch")
    assert PARITY_REQUIREMENTS["python"] == "3.12"
    assert "torch==2.4.0" in PARITY_REQUIREMENTS["packages"]
    assert "evo2" in PARITY_REQUIREMENTS["packages"]
    assert PARITY_REQUIREMENTS["gpu"] == "H100"
    assert PARITY_REQUIREMENTS["min_vram_gb"] == 80


def test_get_modal_config():
    config = get_modal_config()
    assert config["app_name"] == "evovariant-tr"
    assert "nvcr.io/nvidia/pytorch" in config["image"]
    assert config["python_version"] == "3.12"
    assert config["gpu_type"] == "H100"
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


def test_check_modal_environment_reports_missing_package(monkeypatch):
    real_import = builtins.__import__

    def import_without_modal(name, *args, **kwargs):
        if name == "modal":
            raise ImportError("missing modal")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_modal)
    result = check_modal_environment()
    assert result["modal_installed"] == "modal package not installed"
    assert result["modal_authenticated"] == "modal not installed"


def test_check_modal_environment_authenticated_and_exception(monkeypatch):
    monkeypatch.setitem(sys.modules, "modal", SimpleNamespace())
    monkeypatch.setattr(modal_config_module.shutil, "which", lambda _name: "/bin/modal")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )
    result = check_modal_environment()
    assert result["modal_authenticated"] is True

    def fail_run(*args, **kwargs):
        raise RuntimeError("subprocess unavailable")

    monkeypatch.setattr(subprocess, "run", fail_run)
    failed = check_modal_environment()
    assert "subprocess unavailable" in failed["modal_authenticated"]


def test_parity_requirements_frozen():
    """Parity requirements should be immutable in intent."""
    assert PARITY_REQUIREMENTS["min_vram_gb"] == 80
    assert PARITY_REQUIREMENTS["gpu"] == "H100"

"""Tests for fail-closed model adapter readiness and provenance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from evovariant_tr.model_adapters import (
    AdapterStatus,
    AdapterUnavailable,
    DeferredModelAdapter,
    Evo2Adapter,
    build_default_adapters,
)
from evovariant_tr.model_registry import load_model_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS = REPO_ROOT / "research/ml_extension/models"
SCHEMA = REPO_ROOT / "research/schemas/model_manifest.schema.json"


def _evo2_manifest():
    return next(
        model
        for model in load_model_registry(MODELS, schema_path=SCHEMA)
        if model.model_id == "evo2"
    )


def test_default_adapters_are_non_executing_and_fail_closed() -> None:
    models = load_model_registry(MODELS, schema_path=SCHEMA)
    adapters = build_default_adapters(models)
    assert set(adapters) == {model.model_id for model in models}
    assert isinstance(adapters["evo2"], Evo2Adapter)
    assert isinstance(adapters["cadd"], DeferredModelAdapter)
    assert adapters["cadd"].check_readiness().status is AdapterStatus.DEFERRED
    with pytest.raises(AdapterUnavailable, match="not ready"):
        adapters["cadd"].score_batch([])
    with pytest.raises(AdapterUnavailable, match="no verified embedding"):
        adapters["cadd"].extract_embeddings([])


def test_evo2_readiness_reports_incomplete_and_failed_parity() -> None:
    manifest = _evo2_manifest()
    incomplete = Evo2Adapter(
        manifest,
        parity_checker=lambda: {
            "all_pass": True,
            "checks": [{"name": "torch", "status": "PASS"}, {"name": "cuda", "status": "SKIP"}],
        },
    )
    report = incomplete.check_readiness()
    assert report.status is AdapterStatus.DEFERRED
    assert report.ready is False
    assert report.to_dict()["ready"] is False

    failed = Evo2Adapter(
        manifest,
        parity_checker=lambda: {
            "all_pass": False,
            "checks": [{"name": "cuda", "status": "FAIL"}],
        },
    )
    assert failed.check_readiness().status is AdapterStatus.FAILED


def test_evo2_default_parity_checker_remains_deferred_without_gpu() -> None:
    report = Evo2Adapter(_evo2_manifest()).check_readiness()

    assert report.status is AdapterStatus.DEFERRED
    assert report.checks["torch_available"] == "SKIP"


def test_evo2_adapter_rejects_empty_or_unreadable_remote_evidence() -> None:
    manifest = _evo2_manifest()

    empty = Evo2Adapter(
        manifest,
        parity_checker=lambda: {
            "all_pass": True,
            "checks": [{"name": "torch", "status": "PASS"}],
        },
        remote_smoke_checker=lambda: {"all_pass": True, "checks": []},
    ).check_readiness()
    assert empty.status is AdapterStatus.DEFERRED
    assert empty.checks["remote_smoke"] == "NOT_VERIFIED"

    def raises() -> dict[str, Any]:
        raise RuntimeError("evidence file unavailable")

    unreadable = Evo2Adapter(
        manifest,
        parity_checker=lambda: {
            "all_pass": True,
            "checks": [{"name": "torch", "status": "PASS"}],
        },
        remote_smoke_checker=raises,
    ).check_readiness()
    assert unreadable.status is AdapterStatus.FAILED
    assert unreadable.checks["remote_smoke"] == "ERROR"


def test_evo2_adapter_rejects_nonpassing_remote_check_status() -> None:
    report = Evo2Adapter(
        _evo2_manifest(),
        parity_checker=lambda: {
            "all_pass": True,
            "checks": [{"name": "torch", "status": "PASS"}],
        },
        remote_smoke_checker=lambda: {
            "all_pass": True,
            "checks": [{"name": "real_inference", "status": "SKIP"}],
        },
    ).check_readiness()

    assert report.status is AdapterStatus.DEFERRED
    assert report.checks["remote_real_inference"] == "SKIP"


def test_evo2_ready_adapter_requires_or_uses_injected_scorer() -> None:
    manifest = _evo2_manifest()
    def parity() -> dict[str, Any]:
        return {
            "all_pass": True,
            "checks": [
                {"name": "torch", "status": "PASS"},
                {"name": "evo2", "status": "PASS"},
            ],
        }
    no_scorer = Evo2Adapter(manifest, parity_checker=parity)
    with pytest.raises(AdapterUnavailable, match="not executable"):
        no_scorer.score_batch([])

    class _Scorer:
        def score_batch(self, variants: Any, **kwargs: Any) -> dict[str, Any]:
            return {"variants": variants, "kwargs": kwargs}

    adapter = Evo2Adapter(
        manifest,
        scorer=_Scorer(),
        parity_checker=parity,
        remote_smoke_checker=lambda: {
            "all_pass": True,
            "checks": [{"name": "real_inference", "status": "PASS"}],
        },
    )
    result = adapter.score_batch(["fixture"], orientation="forward")
    assert result == {"variants": ["fixture"], "kwargs": {"orientation": "forward"}}
    provenance = adapter.provenance()
    assert provenance["model_id"] == "evo2"
    assert provenance["provenance_status"] == "VERIFIED"


def test_evo2_adapter_never_promotes_local_parity_to_remote_readiness() -> None:
    manifest = _evo2_manifest()
    adapter = Evo2Adapter(
        manifest,
        parity_checker=lambda: {
            "all_pass": True,
            "checks": [{"name": "torch", "status": "PASS"}],
        },
    )

    report = adapter.check_readiness()

    assert report.status is AdapterStatus.DEFERRED
    assert report.checks["remote_smoke"] == "NOT_RUN"
    assert report.ready is False


def test_evo2_adapter_rejects_malformed_or_failed_remote_evidence() -> None:
    manifest = _evo2_manifest()

    def parity() -> dict[str, Any]:
        return {
            "all_pass": True,
            "checks": [{"name": "torch", "status": "PASS"}],
        }

    malformed = Evo2Adapter(
        manifest,
        parity_checker=parity,
        remote_smoke_checker=lambda: {"all_pass": True, "checks": [{"status": "PASS"}]},
    ).check_readiness()
    assert malformed.status is AdapterStatus.DEFERRED
    assert malformed.checks["remote_smoke"] == "NOT_VERIFIED"

    failed = Evo2Adapter(
        manifest,
        parity_checker=parity,
        remote_smoke_checker=lambda: {
            "all_pass": False,
            "checks": [{"name": "real_inference", "status": "FAIL"}],
        },
    ).check_readiness()
    assert failed.status is AdapterStatus.FAILED
    assert failed.checks["remote_real_inference"] == "FAIL"

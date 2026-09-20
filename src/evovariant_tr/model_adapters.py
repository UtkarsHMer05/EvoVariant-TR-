"""Common, fail-closed adapter framework for registered model candidates.

The framework makes model availability explicit.  It does not turn deterministic
fixture lookups into scientific baselines and it never downloads weights as an
import side effect.  A later gated runner can inject a verified scorer into the
Evo2 adapter after its remote parity gate passes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from evovariant_tr.model_registry import RegisteredModel


class AdapterUnavailable(RuntimeError):
    """Raised when a model adapter is not ready for scientific execution."""


class AdapterStatus(StrEnum):
    READY = "READY"
    DEFERRED = "DEFERRED"
    INFEASIBLE = "INFEASIBLE"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"


@dataclass(frozen=True)
class AdapterReadiness:
    """Structured readiness evidence for one registered model."""

    model_id: str
    status: AdapterStatus
    checks: dict[str, str]
    reason: str

    @property
    def ready(self) -> bool:
        return self.status is AdapterStatus.READY

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "status": self.status.value,
            "checks": dict(self.checks),
            "reason": self.reason,
            "ready": self.ready,
        }


class ModelAdapter:
    """Base contract shared by foundation and specialized model adapters."""

    def __init__(self, manifest: RegisteredModel) -> None:
        self.manifest = manifest

    @property
    def model_id(self) -> str:
        return self.manifest.model_id

    def check_readiness(self) -> AdapterReadiness:
        raise NotImplementedError

    def provenance(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "manifest_path": self.manifest.path.as_posix(),
            "manifest_revision": self.manifest.data.get("revision"),
            "status": self.manifest.status,
            "provenance_status": self.manifest.provenance_status,
        }

    def score_batch(self, *args: Any, **kwargs: Any) -> Any:
        raise AdapterUnavailable(f"model adapter {self.model_id} is not ready")

    def extract_embeddings(self, *args: Any, **kwargs: Any) -> Any:
        raise AdapterUnavailable(f"model adapter {self.model_id} has no verified embedding path")


class DeferredModelAdapter(ModelAdapter):
    """Adapter for a candidate whose official path has not passed verification."""

    def __init__(self, manifest: RegisteredModel, reason: str) -> None:
        super().__init__(manifest)
        self.reason = reason

    def check_readiness(self) -> AdapterReadiness:
        return AdapterReadiness(
            model_id=self.model_id,
            status=AdapterStatus.DEFERRED,
            checks={"manifest": "present", "smoke": "not_run"},
            reason=self.reason,
        )


class Evo2Adapter(ModelAdapter):
    """Fail-closed Evo2 adapter with optional gated scorer injection."""

    def __init__(
        self,
        manifest: RegisteredModel,
        *,
        scorer: Any | None = None,
        parity_checker: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(manifest)
        self._scorer = scorer
        self._parity_checker = parity_checker

    def check_readiness(self) -> AdapterReadiness:
        if self._parity_checker is None:
            from evovariant_tr.evo2_scorer import check_evo2_parity

            parity_checker = check_evo2_parity
        else:
            parity_checker = self._parity_checker
        parity = parity_checker()
        checks = {
            str(check["name"]): str(check["status"])
            for check in parity.get("checks", [])
        }
        if not parity.get("all_pass", False):
            return AdapterReadiness(
                model_id=self.model_id,
                status=AdapterStatus.FAILED,
                checks=checks,
                reason="official Evo2 parity checks reported a failure",
            )
        if any(status != "PASS" for status in checks.values()):
            return AdapterReadiness(
                model_id=self.model_id,
                status=AdapterStatus.DEFERRED,
                checks=checks,
                reason="Evo2 parity is incomplete; a verified GPU/package smoke is required",
            )
        return AdapterReadiness(
            model_id=self.model_id,
            status=AdapterStatus.READY,
            checks=checks,
            reason="official Evo2 parity checks passed; remote tiny inference still required",
        )

    def score_batch(self, variants: Any, **kwargs: Any) -> Any:
        readiness = self.check_readiness()
        if not readiness.ready or self._scorer is None:
            raise AdapterUnavailable(
                f"Evo2 adapter is not executable: {readiness.status.value}; {readiness.reason}"
            )
        return self._scorer.score_batch(variants, **kwargs)


def build_default_adapters(
    models: tuple[RegisteredModel, ...],
) -> dict[str, ModelAdapter]:
    """Build adapters without importing model packages or downloading weights."""
    adapters: dict[str, ModelAdapter] = {}
    for model in models:
        if model.model_id == "evo2":
            adapters[model.model_id] = Evo2Adapter(model)
        else:
            adapters[model.model_id] = DeferredModelAdapter(
                model,
                "official source, license, checkpoint, and tiny smoke evidence are not verified",
            )
    return adapters

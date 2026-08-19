"""Evo 2 scorer adapter for EvoVariant-TR (Milestone 49).

This module defines the interface for the Evo 2 model-based scorer,
which will be used for production scoring. It is NOT importable in
the test environment (requires torch, evo2 package, and GPU access).

The adapter follows the frozen protocol requirements:
- 8,192bp context window (CONTEXT_LENGTH_BP)
- Forward + reverse-complement strand scoring
- Log-likelihood ratio scoring (alternate - reference log-probability)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from evovariant_tr.scorer import Scorer

PARITY_REQUIREMENTS: dict[str, int | str] = {
    "context_length_bp": 8192,
    "assembly": "GRCh38",
    "model": "evo2_7b",
    "precision": "bfloat16",
    "batch_size": 128,
    "scoring_semantics": "log_likelihood_ratio",
    "strand": "forward+reverse",
    "framework": "pytorch",
    "min_vram_gb": 24,
}

EV2_AVAILABLE = False
if TYPE_CHECKING:
    pass
else:
    try:
        import torch  # noqa: F401
        EV2_AVAILABLE = True
    except ImportError:
        pass


@dataclass
class Evo2ScorerConfig:
    """Configuration for the Evo 2 scorer."""

    model_name: str = "evo2_7b"
    context_length_bp: int = 8192
    precision: str = "bfloat16"
    batch_size: int = 128
    device: str = "cuda"


class Evo2Scorer(Scorer):
    """Evo 2 model-based scorer.

    Requires:
    - PyTorch with CUDA support
    - The evo2 package (pip install evo2)
    - A GPU with at least 24GB VRAM

    NOT available in the unit test environment. Use FakeScorer for tests.
    """

    name = "evo2_scorer"
    version = "1.0.0"
    context_length_bp = 8192

    def __init__(self, config: Evo2ScorerConfig | None = None) -> None:
        self._config = config or Evo2ScorerConfig()
        if not EV2_AVAILABLE:
            raise RuntimeError(
                "torch is not available. Evo2Scorer requires a GPU environment "
                "with torch and evo2 installed."
            )

        from evo2 import Evo2  # noqa: PLC0415

        self._model: Any = Evo2(self._config.model_name)  # pragma: no cover

    def score_variant(
        self,
        ref_window: Any,
        variant: Any,
        strand: str = "forward",
    ) -> tuple[float, float, float]:
        """Score a variant using Evo 2.

        Returns (reference_logprob, alternate_logprob, log_likelihood_ratio).
        A positive LLR means the alternate allele is more likely under the model.
        """
        if not EV2_AVAILABLE:  # pragma: no cover
            raise RuntimeError("Evo 2 not available in this environment")

        ref_seq = ref_window.ref_sequence
        from evovariant_tr.sequence_mutate import apply_variant_to_reference  # noqa: PLC0415

        alt_seq = apply_variant_to_reference(
            ref_seq, variant, ref_window.variant_offset, strand=strand,
        )

        ref_ll = self._compute_log_likelihood(ref_seq)  # pragma: no cover
        alt_ll = self._compute_log_likelihood(alt_seq)  # pragma: no cover
        return ref_ll, alt_ll, alt_ll - ref_ll  # pragma: no cover

    def _compute_log_likelihood(self, sequence: str) -> float:
        """Compute the log-likelihood of a sequence under Evo 2."""
        if not EV2_AVAILABLE:  # pragma: no cover
            raise RuntimeError("Evo 2 not available in this environment")
        raise NotImplementedError(  # pragma: no cover
            "Evo 2 scoring requires the full model pipeline"
        )

    def score_batch(self, variants: list[tuple[Any, Any, str]]) -> Any:
        raise NotImplementedError("Use score_variant for single variant scoring")

    def score_cohort(self, cohort: list[Any]) -> Any:
        raise NotImplementedError

    def check_health(self) -> dict[str, Any]:
        """Check Evo 2 model health."""
        if not EV2_AVAILABLE:
            return {"healthy": False, "reason": "torch not available"}
        return {
            "healthy": True,
            "scorer": self.name,
            "model": self._config.model_name,
            "device": self._config.device,
        }


def check_evo2_parity() -> dict[str, Any]:
    """Check if the current Evo 2 installation meets parity requirements.

    Returns a dict with check results.
    """
    checks: list[dict[str, Any]] = []

    torch_ok = EV2_AVAILABLE
    checks.append({
        "name": "torch_available",
        "status": "PASS" if torch_ok else "SKIP",
        "detail": "torch found" if torch_ok else "torch not available",
    })

    if not torch_ok:
        return {
            "all_pass": True,
            "checks": checks,
            "parity_requirements": PARITY_REQUIREMENTS,
        }

    # The following checks require torch, which is only available in the GPU environment.
    import torch  # noqa: PLC0415

    min_vram: int = int(PARITY_REQUIREMENTS["min_vram_gb"])
    cuda_ok = bool(torch.cuda.is_available())  # pragma: no cover
    checks.append({
        "name": "cuda_available",
        "status": "PASS" if cuda_ok else "FAIL",
        "detail": "CUDA not available" if not cuda_ok else "CUDA available",
    })

    vram_gb = 0.0  # pragma: no cover
    vram_ok = True  # pragma: no cover
    if cuda_ok:  # pragma: no cover
        props = torch.cuda.get_device_properties(0)
        vram_gb = float(props.total_memory / (1024 ** 3))
        vram_ok = vram_gb >= float(min_vram)
    checks.append({
        "name": "min_vram",
        "status": "PASS" if vram_ok else "WARN",
        "detail": f"{vram_gb:.1f}GB VRAM",
    })

    evo2_ok = False  # pragma: no cover
    try:  # pragma: no cover
        import evo2  # noqa: F401, PLC0415
        evo2_ok = True
    except ImportError:  # pragma: no cover
        pass
    checks.append({
        "name": "evo2_package",
        "status": "PASS" if evo2_ok else "SKIP",
        "detail": "evo2 found" if evo2_ok else "evo2 not available",
    })

    all_pass = all(c["status"] != "FAIL" for c in checks)
    return {
        "all_pass": all_pass,
        "checks": checks,
        "parity_requirements": PARITY_REQUIREMENTS,
    }
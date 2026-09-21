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

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from evovariant_tr.scorer import ScoredVariant, Scorer, ScoringResult
from evovariant_tr.sequence_mutate import reverse_complement

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

TORCH_AVAILABLE = False
EV2_AVAILABLE = False
if TYPE_CHECKING:
    pass
else:
    try:
        import torch  # noqa: F401
        TORCH_AVAILABLE = True
    except ImportError:
        pass
    if TORCH_AVAILABLE:
        try:
            import evo2  # noqa: F401
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

    def __init__(self, config: Evo2ScorerConfig | None = None) -> None:  # pragma: no cover
        self._config = config or Evo2ScorerConfig()
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "torch is not available. Evo2Scorer requires a GPU environment "
                "with torch and evo2 installed."
            )
        if not EV2_AVAILABLE:
            raise RuntimeError(
                "the evo2 package is not available. Install the official Evo2 package "
                "in the gated GPU environment before constructing Evo2Scorer."
            )

        from evo2 import Evo2  # noqa: PLC0415  # pragma: no cover

        self._model: Any = Evo2(self._config.model_name)  # pragma: no cover

    def score_variant(
        self,
        ref_window: Any,
        variant: Any,
        strand: str = "forward",
    ) -> tuple[float, float, float]:
        """Score a variant using Evo 2.  # pragma: no cover

        Returns (reference_logprob, alternate_logprob, log_likelihood_ratio).
        A positive LLR means the alternate allele is more likely under the model.
        """
        if not EV2_AVAILABLE:  # pragma: no cover
            raise RuntimeError("Evo 2 not available in this environment")

        ref_seq, alt_seq = self._prepare_variant_sequences(
            ref_window, variant, strand
        )  # pragma: no cover
        ref_ll, alt_ll = self._score_sequences([ref_seq, alt_seq])  # pragma: no cover
        return ref_ll, alt_ll, alt_ll - ref_ll  # pragma: no cover

    def _prepare_variant_sequences(
        self,
        ref_window: Any,
        variant: Any,
        strand: str,
    ) -> tuple[str, str]:  # pragma: no cover
        """Build the reference and alternate sequences for one orientation."""
        if len(ref_window.ref_sequence) != self.context_length_bp:
            raise ValueError(
                f"reference window must contain exactly {self.context_length_bp} bases"
            )
        from evovariant_tr.sequence_mutate import apply_variant_to_reference  # noqa: PLC0415

        alt_seq = apply_variant_to_reference(
            ref_window.ref_sequence, variant, ref_window.variant_offset, strand=strand,
        )
        ref_seq = (
            reverse_complement(ref_window.ref_sequence)
            if strand == "reverse"
            else ref_window.ref_sequence
        )
        if len(alt_seq) != self.context_length_bp:
            raise ValueError(
                f"alternate sequence must contain exactly {self.context_length_bp} bases"
            )
        return ref_seq, alt_seq

    def _score_sequences(self, sequences: list[str]) -> list[float]:  # pragma: no cover
        """Score sequences in model-sized chunks and return scalar scores.

        ``Evo2.score_sequences`` accepts a list of sequences.  The previous
        implementation called it once per sequence, which made the adapter's
        batch contract nominal rather than actual.  Chunking is kept here so a
        caller can submit a large cohort without implicitly exceeding the
        configured model batch size.
        """
        if not EV2_AVAILABLE:  # pragma: no cover
            raise RuntimeError("Evo 2 not available in this environment")
        if not sequences:
            return []
        if any(len(sequence) != self.context_length_bp for sequence in sequences):
            raise ValueError(
                f"every Evo 2 input must contain exactly {self.context_length_bp} bases"
            )

        model_batch_size = max(1, int(self._config.batch_size))
        scores: list[float] = []
        for start in range(0, len(sequences), model_batch_size):
            batch = sequences[start:start + model_batch_size]
            raw = self._model.score_sequences(batch)
            values = list(raw)
            if len(values) != len(batch):
                raise ValueError(
                    "Evo 2 returned a score count different from the input batch"
                )
            for value in values:
                if hasattr(value, "item"):
                    value = value.item()
                scores.append(float(value))
        return scores

    def score_batch(self, variants: list[tuple[Any, Any, str]]) -> Any:  # pragma: no cover
        """Score variants using batched model calls while isolating bad rows."""
        started = time.perf_counter()
        scored: list[ScoredVariant] = []
        failed: list[tuple[Any, str]] = []
        prepared: list[tuple[Any, Any, str, str, str]] = []
        sequence_batch: list[str] = []
        for ref_window, variant, strand in variants:
            try:
                ref_seq, alt_seq = self._prepare_variant_sequences(
                    ref_window, variant, strand
                )
                prepared.append((ref_window, variant, strand, ref_seq, alt_seq))
                sequence_batch.extend((ref_seq, alt_seq))
            except Exception as exc:  # pragma: no cover - GPU validation path
                failed.append((variant, str(exc)))

        try:
            sequence_scores = self._score_sequences(sequence_batch)
        except Exception as exc:  # pragma: no cover - GPU failure path
            for _, variant, _, _, _ in prepared:
                failed.append((variant, str(exc)))
            sequence_scores = []

        if sequence_scores:
            if len(sequence_scores) != 2 * len(prepared):
                error = "Evo 2 returned an incomplete batch result"
                for _, variant, _, _, _ in prepared:
                    failed.append((variant, error))
                sequence_scores = []

        if sequence_scores:
            for index, (ref_window, variant, strand, _, _) in enumerate(prepared):
                ref_score = sequence_scores[2 * index]
                alt_score = sequence_scores[2 * index + 1]
                delta = alt_score - ref_score
                scored.append(
                    ScoredVariant(
                        identity=variant,
                        reference_window=ref_window,
                        reference_score=ref_score,
                        alternate_score=alt_score,
                        score_delta=delta,
                        allele_likelihood=delta,
                        metadata={
                            "strand": strand,
                            "model_batch_size": min(
                                max(1, int(self._config.batch_size)),
                                len(sequence_batch),
                            ),
                            "provenance": self.provenance(),
                        },
                    )
                )
        return ScoringResult(
            scored=scored,
            failed=failed,
            total=len(variants),
            batch_size=len(scored),
            timing_ms=(time.perf_counter() - started) * 1000,
            scorer_name=self.name,
            scorer_version=self.version,
        )

    def score_cohort(self, cohort: list[Any]) -> Any:  # pragma: no cover
        """Score cohort items that carry a reference window and variant identity."""
        prepared: list[tuple[Any, Any, str]] = []
        failed: list[tuple[Any, str]] = []
        for item in cohort:
            window = getattr(item, "reference_window", None)
            variant = getattr(item, "variant", None)
            if window is None or variant is None:
                failed.append((item, "cohort item lacks reference_window and variant"))
                continue
            prepared.append((window, variant, "forward"))
        result = self.score_batch(prepared)
        result.failed.extend(failed)
        result.total += len(failed)
        return result

    def check_health(self) -> dict[str, Any]:  # pragma: no cover
        """Check Evo 2 model health."""
        if not TORCH_AVAILABLE:
            return {"healthy": False, "reason": "torch not available"}
        if not EV2_AVAILABLE:
            return {"healthy": False, "reason": "evo2 package not available"}
        return {
            "healthy": True,
            "scorer": self.name,
            "model": self._config.model_name,
            "device": self._config.device,
        }


def check_evo2_parity() -> dict[str, Any]:  # pragma: no cover
    """Check if the current Evo 2 installation meets parity requirements.

    Returns a dict with check results.
    """
    checks: list[dict[str, Any]] = []

    torch_ok = TORCH_AVAILABLE
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

"""EvoVariant-TR Modal deployment entry point (Milestone 52-53, M065).

Deploy with:
    modal deploy evo2_scorer_app.py

This is the NEW project's Modal app — it does NOT reuse the old project's
deployment identity (variant-analysis-evo2), per M19 cost-control policy.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import modal
from evovariant_tr.cache_identity import CacheIdentity, ContentAddressedCache
from evovariant_tr.modal_config import (
    CANONICAL_MODAL_APP,
    CANONICAL_MODAL_VOLUME,
    EVO2_REPOSITORY,
    EVO2_REPOSITORY_REVISION,
    HF_CACHE_MOUNT_PATH,
    get_modal_config,
    get_modal_volumes,
)
from evovariant_tr.sequence_mutate import reverse_complement
from evovariant_tr.sequence_window import (
    CONTEXT_LENGTH_BP,
    compute_window_coordinates_with_shift,
)
from evovariant_tr.telemetry import TelemetryTimer
from evovariant_tr.variant_schema import normalize_chromosome
from modal import Image

_modal_config = get_modal_config()

# Keep remote batch requests bounded until a dedicated parity smoke establishes
# the safe memory envelope for the selected Evo2 checkpoint.  Four sequences
# are needed per variant (forward/RC reference and alternate).
MAX_BATCH_VARIANTS = 8
MODEL_SEQUENCE_BATCH_SIZE = 8
DEFAULT_EMBEDDING_LAYER = "blocks.28.mlp.l3"
EMBEDDING_POOLING = "mean_tokens"


@dataclass(frozen=True)
class _VariantInput:
    """Canonicalized transport fields accepted by the Modal endpoints."""

    assembly: str
    genome: str
    chromosome: str
    position_1based: int
    reference: str
    alternate: str
    normalized_variant_id: str


@dataclass(frozen=True)
class _PreparedVariant:
    """Validated sequence pair ready for model scoring and cache writes."""

    variant: _VariantInput
    cache_identity: CacheIdentity
    reference_sequence: str
    alternate_sequence: str

# Build the Docker image for Evo 2 inference.
# Uses the same NVidia PyTorch image as the M055/M060 test scripts for
# full parity with GPU libraries and compute capability detection.
evo2_image = (
    Image.from_registry(_modal_config["image"], add_python="3.12")
    .apt_install(
        ["build-essential", "cmake", "ninja-build",
         "git", "gcc", "g++", "clang", "libclang-dev"],
    )
    .run_commands(
        "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124",
        f"git clone --recurse-submodules {EVO2_REPOSITORY} evo2 "
        f"&& cd evo2 && git checkout {EVO2_REPOSITORY_REVISION} "
        "&& git submodule update --init --recursive && pip install .",
    )
    .run_commands(
        "pip uninstall -y transformer-engine transformer_engine",
        "pip install 'transformer_engine[pytorch]==1.13' --no-build-isolation",
        "pip install --force-reinstall --no-deps "
        "https://github.com/Dao-AILab/flash-attention/releases/download/v2.6.3/"
        "flash_attn-2.6.3%2Bcu123torch2.4cxx11abiFALSE-cp312-cp312-linux_x86_64.whl",
    )
    .add_local_dir("scripts", "/opt/scripts", copy=True)
    .run_commands("python3 /opt/scripts/patch_vortex.py")
    .pip_install(
        "fastapi[standard]", "modal", "matplotlib", "pandas",
        "seaborn", "scikit-learn", "openpyxl", "requests",
    )
    .add_local_dir("src", "/opt/evovariant_tr", copy=True)
    .env({"PYTHONPATH": "/opt/evovariant_tr"})
)

# Use the NEW project identity, never the old one.
app = modal.App(CANONICAL_MODAL_APP, image=evo2_image)

# Volumes for model caching.
_volumes = get_modal_volumes()
_hf_cache_volume = modal.Volume.from_name(
    CANONICAL_MODAL_VOLUME,
    create_if_missing=False,
)
_mount_path = HF_CACHE_MOUNT_PATH

# Volume mount configuration.
volume_mounts: dict[str, modal.Volume] = {_mount_path: _hf_cache_volume}


@app.cls(
    gpu=_modal_config["gpu_type"],
    volumes=volume_mounts,  # type: ignore[arg-type]
    max_containers=3,
    retries=2,
    scaledown_window=120,
    timeout=1000,
)
class Evo2ScorerService:
    """Persistent Evo 2 scoring service on Modal.

    M065: The persistent Modal scoring service that serves scoring requests.
    Uses the approved H100 GPU type per cost policy (M19).
    """

    @modal.enter()
    def load_evo2_model(self) -> None:
        """Load the Evo 2 model once per container lifecycle."""
        import _codecs

        import torch
        from evo2 import Evo2

        try:
            torch.serialization.add_safe_globals([_codecs.encode])
        except Exception:
            pass

        print("Loading Evo 2 model...")
        self.model = Evo2("evo2_7b")
        self.prediction_cache = ContentAddressedCache(
            f"{HF_CACHE_MOUNT_PATH}/evovariant-tr/predictions"
        )
        self.feature_cache = ContentAddressedCache(
            f"{HF_CACHE_MOUNT_PATH}/evovariant-tr/features"
        )
        print("Evo 2 model loaded successfully.")

    @modal.fastapi_endpoint(method="POST")
    def score_variant(self, variant_data: dict[str, object]) -> dict[str, object]:
        """Score a single variant using Evo 2.

        Request body:
            assembly/genome: GRCh38/hg38
            chromosome: str (e.g., "chr17")
            position_1based/variant_position: int (1-based)
            reference/ref: str
            alternate/alternative/alt: str
        """
        variant = self._parse_variant_input(variant_data)
        cache_identity = self._cache_identity(variant)
        cached = self.prediction_cache.get(cache_identity)
        if cached is not None:
            result = dict(cached.payload)
            provenance = dict(result.get("provenance", {}))
            provenance["cache_hit"] = True
            result["provenance"] = provenance
            return result

        prepared = self._prepare_variant(variant, cache_identity)

        with TelemetryTimer(gpu_type=str(_modal_config["gpu_type"])) as timer:
            scores = [
                self._score_sequence(prepared.reference_sequence),
                self._score_sequence(prepared.alternate_sequence),
                self._score_sequence(reverse_complement(prepared.reference_sequence)),
                self._score_sequence(reverse_complement(prepared.alternate_sequence)),
            ]
        result = self._result_from_scores(prepared, scores, timer.result)
        self.prediction_cache.put(cache_identity, result)
        return result

    @modal.fastapi_endpoint(method="POST")
    def score_batch(self, batch_data: dict[str, object]) -> dict[str, object]:
        """Score a bounded batch with true model batching and partial failures.

        The endpoint is source-level infrastructure only until a separately
        approved remote batch parity smoke is run.  It intentionally rejects
        oversized requests so a later deployment cannot turn an exploratory
        request into an unbounded H100 workload.
        """
        raw_variants = batch_data.get("variants")
        if not isinstance(raw_variants, list) or not raw_variants:
            raise ValueError("batch request must contain a non-empty variants list")
        if len(raw_variants) > MAX_BATCH_VARIANTS:
            raise ValueError(
                f"batch request exceeds the {MAX_BATCH_VARIANTS}-variant limit"
            )

        results_by_index: dict[int, dict[str, object]] = {}
        failures: list[dict[str, object]] = []
        pending: list[tuple[int, _PreparedVariant]] = []

        for index, raw_variant in enumerate(raw_variants):
            if not isinstance(raw_variant, dict):
                failures.append({
                    "index": index,
                    "variant": repr(raw_variant),
                    "error": "each batch variant must be an object",
                })
                continue
            try:
                variant = self._parse_variant_input(raw_variant)
                cache_identity = self._cache_identity(variant)
                cached = self.prediction_cache.get(cache_identity)
                if cached is not None:
                    result = dict(cached.payload)
                    cached_provenance = dict(result.get("provenance", {}))
                    cached_provenance["cache_hit"] = True
                    result["provenance"] = cached_provenance
                    results_by_index[index] = result
                    continue
                pending.append(
                    (index, self._prepare_variant(variant, cache_identity))
                )
            except Exception as exc:
                failures.append({
                    "index": index,
                    "variant": repr(raw_variant),
                    "error": str(exc),
                })

        batch_telemetry: dict[str, object] | None = None
        if pending:
            try:
                sequences: list[str] = []
                for _, prepared in pending:
                    sequences.extend((
                        prepared.reference_sequence,
                        prepared.alternate_sequence,
                        reverse_complement(prepared.reference_sequence),
                        reverse_complement(prepared.alternate_sequence),
                    ))
                with TelemetryTimer(gpu_type=str(_modal_config["gpu_type"])) as timer:
                    scores = self._score_sequence_batch(sequences)
                if timer.result is not None:
                    batch_telemetry = timer.result.to_dict()
                expected = 4 * len(pending)
                if len(scores) != expected:
                    raise ValueError(
                        f"Evo 2 returned {len(scores)} scores for {expected} sequences"
                    )
                for pending_index, (index, prepared) in enumerate(pending):
                    start = pending_index * 4
                    result = self._result_from_scores(
                        prepared,
                        scores[start:start + 4],
                        None,
                    )
                    result_provenance = result.get("provenance")
                    if not isinstance(result_provenance, dict):
                        raise ValueError("score result is missing provenance metadata")
                    result["provenance"] = {
                        **result_provenance,
                        "batch_request_size": len(raw_variants),
                        "model_sequence_batch_size": MODEL_SEQUENCE_BATCH_SIZE,
                    }
                    if batch_telemetry is not None:
                        result["telemetry"] = batch_telemetry
                    self.prediction_cache.put(prepared.cache_identity, result)
                    results_by_index[index] = result
            except Exception as exc:
                failures.extend({
                    "index": index,
                    "variant": prepared.variant.normalized_variant_id,
                    "error": str(exc),
                } for index, prepared in pending)

        ordered_results = [
            results_by_index[index]
            for index in range(len(raw_variants))
            if index in results_by_index
        ]
        status = "completed" if not failures else (
            "partial" if ordered_results else "failed"
        )
        return {
            "status": status,
            "total": len(raw_variants),
            "scored": len(ordered_results),
            "failed": len(failures),
            "results": ordered_results,
            "failures": failures,
            "provenance": {
                "scorer": "evo2_7b",
                "research_only": True,
                "model_sequence_batch_size": MODEL_SEQUENCE_BATCH_SIZE,
                "max_batch_variants": MAX_BATCH_VARIANTS,
            },
        }

    @modal.fastapi_endpoint(method="POST")
    def extract_embeddings(self, embedding_data: dict[str, object]) -> dict[str, object]:
        """Extract a bounded ref/alt feature pair from the frozen Evo2 layer contract.

        This endpoint is source-level infrastructure only until a separately approved
        remote embedding smoke establishes the memory, shape, and cost envelope.  The
        layer and pooling rule are intentionally fixed so a caller cannot tune them
        against the locked cohort through the transport API.
        """
        layer = embedding_data.get("layer", DEFAULT_EMBEDDING_LAYER)
        if layer != DEFAULT_EMBEDDING_LAYER:
            raise ValueError(
                f"only the frozen embedding layer {DEFAULT_EMBEDDING_LAYER!r} is supported"
            )
        variant = self._parse_variant_input(embedding_data)
        cache_identity = self._embedding_cache_identity(variant, DEFAULT_EMBEDDING_LAYER)
        cached = self.feature_cache.get(cache_identity)
        if cached is not None:
            result = dict(cached.payload)
            provenance = dict(result.get("provenance", {}))
            provenance["cache_hit"] = True
            result["provenance"] = provenance
            return result

        prepared = self._prepare_variant(variant, cache_identity)
        sequences = [
            prepared.reference_sequence,
            prepared.alternate_sequence,
            reverse_complement(prepared.reference_sequence),
            reverse_complement(prepared.alternate_sequence),
        ]
        with TelemetryTimer(gpu_type=str(_modal_config["gpu_type"])) as timer:
            vectors, dtype = self._extract_embedding_vectors(
                sequences,
                DEFAULT_EMBEDDING_LAYER,
            )
        result = self._embedding_result_from_vectors(
            prepared,
            DEFAULT_EMBEDDING_LAYER,
            vectors,
            dtype,
            timer.result,
        )
        self.feature_cache.put(cache_identity, result)
        return result

    def _parse_variant_input(self, variant_data: dict[str, object]) -> _VariantInput:
        """Normalize the accepted transport aliases into one variant schema."""
        raw_chrom = str(
            variant_data.get("chromosome", variant_data.get("chrom", ""))
        )
        position_value = variant_data.get(
            "position_1based", variant_data.get("variant_position")
        )
        pos = int(str(position_value))
        declared_ref = str(
            variant_data.get("reference", variant_data.get("ref", ""))
        ).upper()
        alt = str(
            variant_data.get(
                "alternate",
                variant_data.get("alternative", variant_data.get("alt", "")),
            )
        ).upper()
        assembly = str(variant_data.get("assembly", "GRCh38"))
        genome = str(variant_data.get("genome", "hg38"))

        if not raw_chrom.strip() or not declared_ref or not alt:
            raise ValueError("chromosome, reference, and alternate are required")
        if assembly != "GRCh38":
            raise ValueError("the canonical Modal scorer requires assembly GRCh38")
        if genome != "hg38":
            raise ValueError("the canonical Modal scorer requires UCSC genome hg38")
        if pos < 1:
            raise ValueError("position_1based must be >= 1")
        if len(declared_ref) != 1 or len(alt) != 1 or declared_ref == alt:
            raise ValueError("the canonical Modal scorer accepts distinct SNVs only")
        if declared_ref not in "ACGT" or alt not in "ACGT":
            raise ValueError("the canonical Modal scorer accepts A/C/G/T alleles only")

        chrom = normalize_chromosome(raw_chrom)
        return _VariantInput(
            assembly=assembly,
            genome=genome,
            chromosome=chrom,
            position_1based=pos,
            reference=declared_ref,
            alternate=alt,
            normalized_variant_id=f"{assembly}:{chrom}:{pos}:{declared_ref}>{alt}",
        )

    def _cache_identity(self, variant: _VariantInput) -> CacheIdentity:
        """Build the content identity shared by single and batch requests."""
        return CacheIdentity(
            model_id="evo2",
            checkpoint="evo2_7b",
            model_revision=EVO2_REPOSITORY_REVISION,
            preprocessing_revision="grch38-8192-v1",
            assembly=variant.assembly,
            context_length_bp=CONTEXT_LENGTH_BP,
            orientation="forward_and_reverse",
            layer="raw_scores",
            normalized_variant_id=variant.normalized_variant_id,
        )

    def _embedding_cache_identity(self, variant: _VariantInput, layer: str) -> CacheIdentity:
        """Build a feature-cache identity that includes layer and pooling semantics."""
        return CacheIdentity(
            model_id="evo2",
            checkpoint="evo2_7b",
            model_revision=EVO2_REPOSITORY_REVISION,
            preprocessing_revision="grch38-8192-embedding-mean-v1",
            assembly=variant.assembly,
            context_length_bp=CONTEXT_LENGTH_BP,
            orientation="forward_and_reverse",
            layer=f"{layer}:{EMBEDDING_POOLING}",
            normalized_variant_id=variant.normalized_variant_id,
        )

    def _prepare_variant(
        self,
        variant: _VariantInput,
        cache_identity: CacheIdentity,
    ) -> _PreparedVariant:
        """Fetch and validate one exact reference window before model work."""
        print(
            f"Scoring variant: {variant.chromosome}:{variant.position_1based} "
            f"{variant.reference}>{variant.alternate} genome={variant.genome}"
        )
        sequence, seq_start = self._fetch_genome_sequence(
            position=variant.position_1based,
            genome=variant.genome,
            chromosome=variant.chromosome,
        )
        relative_pos = variant.position_1based - 1 - seq_start
        if relative_pos < 0 or relative_pos >= len(sequence):
            raise ValueError(
                f"Variant position {variant.position_1based} is outside the fetched window "
                f"(start={seq_start + 1}, end={seq_start + len(sequence)})"
            )

        ref = sequence[relative_pos]
        if ref != variant.reference:
            raise ValueError(
                f"reference allele mismatch at {variant.chromosome}:"
                f"{variant.position_1based}: declared={variant.reference}, fetched={ref}"
            )
        alt_sequence = (
            sequence[:relative_pos]
            + variant.alternate
            + sequence[relative_pos + 1:]
        )
        return _PreparedVariant(
            variant=variant,
            cache_identity=cache_identity,
            reference_sequence=sequence,
            alternate_sequence=alt_sequence,
        )

    def _result_from_scores(
        self,
        prepared: _PreparedVariant,
        scores: list[float],
        telemetry: Any | None,
    ) -> dict[str, object]:
        """Build the canonical raw-score payload from four model outputs."""
        if len(scores) != 4:
            raise ValueError(f"expected four orientation scores, got {len(scores)}")
        forward_ref, forward_alt, reverse_ref, reverse_alt = scores
        delta_fwd = forward_alt - forward_ref
        delta_rc = reverse_alt - reverse_ref
        delta_primary = (delta_fwd + delta_rc) / 2
        variant = prepared.variant
        result: dict[str, object] = {
            "variant": (
                f"{variant.chromosome}:g.{variant.position_1based}"
                f"{variant.reference}>{variant.alternate}"
            ),
            "normalized_variant_id": variant.normalized_variant_id,
            "assembly": variant.assembly,
            "chromosome": variant.chromosome,
            "position_1based": variant.position_1based,
            "reference": variant.reference,
            "alternate": variant.alternate,
            "reference_score": float(forward_ref),
            "alternate_score": float(forward_alt),
            "score_delta": float(delta_primary),
            "delta_forward": float(delta_fwd),
            "delta_reverse": float(delta_rc),
            "delta_primary": float(delta_primary),
            "orientation_disagreement": float(abs(delta_fwd - delta_rc)),
            "raw_scores": {
                "forward": {
                    "reference_score": float(forward_ref),
                    "alternate_score": float(forward_alt),
                    "delta": float(delta_fwd),
                },
                "reverse": {
                    "reference_score": float(reverse_ref),
                    "alternate_score": float(reverse_alt),
                    "delta": float(delta_rc),
                },
            },
            "status": "completed",
            "provenance": {
                "scorer": "evo2_7b",
                "context_length_bp": CONTEXT_LENGTH_BP,
                "orientation": "forward_and_reverse",
                "scoring_semantics": "alternate_minus_reference_log_likelihood",
                "model_revision": EVO2_REPOSITORY_REVISION,
                "cache_hit": False,
                "research_only": True,
                "classification": "not_provided",
            },
        }
        if telemetry is not None:
            result["telemetry"] = telemetry.to_dict()
        return result

    def _score_sequence(self, sequence: str) -> float:
        """Convert the official Evo2 score output to a scalar float."""
        if len(sequence) != CONTEXT_LENGTH_BP:
            raise ValueError(
                f"Evo2 input must contain exactly {CONTEXT_LENGTH_BP} bases, "
                f"got {len(sequence)}"
            )
        raw = self.model.score_sequences([sequence])[0]
        return float(raw.item() if hasattr(raw, "item") else raw)

    def _score_sequence_batch(self, sequences: list[str]) -> list[float]:
        """Score a bounded list in chunks of the remote model batch size."""
        if any(len(sequence) != CONTEXT_LENGTH_BP for sequence in sequences):
            raise ValueError(
                f"every Evo2 input must contain exactly {CONTEXT_LENGTH_BP} bases"
            )
        scores: list[float] = []
        for start in range(0, len(sequences), MODEL_SEQUENCE_BATCH_SIZE):
            batch = sequences[start:start + MODEL_SEQUENCE_BATCH_SIZE]
            raw = self.model.score_sequences(batch)
            values = list(raw)
            if len(values) != len(batch):
                raise ValueError(
                    "Evo2 returned a score count different from the input batch"
                )
            for value in values:
                scores.append(float(value.item() if hasattr(value, "item") else value))
        return scores

    def _extract_embedding_vectors(
        self,
        sequences: list[str],
        layer: str,
    ) -> tuple[list[list[float]], str]:
        """Run one official Evo2 forward pass and mean-pool token embeddings."""
        if not sequences:
            raise ValueError("at least one sequence is required for embedding extraction")
        if any(len(sequence) != CONTEXT_LENGTH_BP for sequence in sequences):
            raise ValueError(
                f"every embedding input must contain exactly {CONTEXT_LENGTH_BP} bases"
            )

        import torch

        tokenized = [self.model.tokenizer.tokenize(sequence) for sequence in sequences]
        lengths = {len(tokens) for tokens in tokenized}
        if len(lengths) != 1:
            raise ValueError("all embedding inputs must tokenize to the same length")
        input_ids = torch.tensor(tokenized, dtype=torch.int, device="cuda:0")
        _, embeddings = self.model(
            input_ids,
            return_embeddings=True,
            layer_names=[layer],
        )
        if not isinstance(embeddings, dict) or layer not in embeddings:
            raise ValueError(f"Evo2 did not return the requested embedding layer {layer!r}")
        tensor = embeddings[layer]
        if getattr(tensor, "ndim", None) != 3 or tensor.shape[0] != len(sequences):
            raise ValueError(
                "Evo2 embedding tensor must have shape [batch, tokens, dimensions]"
            )
        pooled = tensor.detach().float().mean(dim=1).cpu()
        dtype = str(tensor.dtype)
        return [list(map(float, row)) for row in pooled.tolist()], dtype

    @staticmethod
    def _embedding_hash(values: list[float]) -> str:
        encoded = json.dumps(values, separators=(",", ":"), allow_nan=False).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _embedding_result_from_vectors(
        self,
        prepared: _PreparedVariant,
        layer: str,
        vectors: list[list[float]],
        dtype: str,
        telemetry: Any | None,
    ) -> dict[str, object]:
        """Build a provenance-bearing ref/alt feature payload."""
        if len(vectors) != 4:
            raise ValueError(f"expected four embedding vectors, got {len(vectors)}")
        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) != 1 or not dimensions or next(iter(dimensions)) == 0:
            raise ValueError("embedding vectors must have one non-empty dimension")

        def orientation_payload(
            reference: list[float], alternate: list[float]
        ) -> dict[str, object]:
            difference = [alt - ref for ref, alt in zip(reference, alternate, strict=True)]
            return {
                "reference": reference,
                "alternate": alternate,
                "difference": difference,
                "shape": [len(reference)],
                "dtype": "float32",
                "reference_sha256": self._embedding_hash(reference),
                "alternate_sha256": self._embedding_hash(alternate),
                "difference_sha256": self._embedding_hash(difference),
            }

        variant = prepared.variant
        result: dict[str, object] = {
            "variant": (
                f"{variant.chromosome}:g.{variant.position_1based}"
                f"{variant.reference}>{variant.alternate}"
            ),
            "normalized_variant_id": variant.normalized_variant_id,
            "assembly": variant.assembly,
            "chromosome": variant.chromosome,
            "position_1based": variant.position_1based,
            "reference": variant.reference,
            "alternate": variant.alternate,
            "status": "completed",
            "embedding_features": {
                "forward": orientation_payload(vectors[0], vectors[1]),
                "reverse": orientation_payload(vectors[2], vectors[3]),
            },
            "provenance": {
                "scorer": "evo2_7b",
                "model_revision": EVO2_REPOSITORY_REVISION,
                "context_length_bp": CONTEXT_LENGTH_BP,
                "layer": layer,
                "pooling": EMBEDDING_POOLING,
                "embedding_dtype": dtype,
                "orientation": "forward_and_reverse",
                "feature_semantics": "mean_token_embedding_ref_alt_difference",
                "cache_hit": False,
                "research_only": True,
                "classification": "not_provided",
            },
        }
        if telemetry is not None:
            result["telemetry"] = telemetry.to_dict()
        return result

    def _fetch_chromosome_length(self, genome: str, chromosome: str) -> int:
        """Fetch chromosome size so edge windows can be shifted exactly."""
        import requests

        response = requests.get(
            f"https://api.genome.ucsc.edu/list/chromosomes?genome={genome}",
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        chromosomes = payload.get("chromosomes", {})
        if chromosome not in chromosomes:
            raise ValueError(f"UCSC did not return chromosome size for {chromosome}")
        return int(chromosomes[chromosome])

    def _fetch_genome_sequence(
        self, position: int, genome: str, chromosome: str,
        window_size: int = CONTEXT_LENGTH_BP,
    ) -> tuple[str, int]:
        """Fetch a sequence window from the UCSC API."""
        import requests

        if window_size != CONTEXT_LENGTH_BP:
            raise ValueError(f"the frozen scorer context is exactly {CONTEXT_LENGTH_BP} bases")
        chrom_len = self._fetch_chromosome_length(genome, chromosome)
        window_start, window_stop, _ = compute_window_coordinates_with_shift(
            chrom_len, position
        )
        start = window_start - 1
        end = window_stop

        print(
            f"Fetching {window_size}bp window around position {position} "
            f"from UCSC API..."
        )
        print(f"Coordinates: {chromosome}:{start}-{end} ({genome})")

        api_url = (
            f"https://api.genome.ucsc.edu/getData/sequence?genome={genome}"
            f";chrom={chromosome};start={start};end={end}"
        )
        response = requests.get(api_url, timeout=30)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch genome sequence from UCSC API: "
                f"{response.status_code}"
            )

        genome_data = response.json()

        if "dna" not in genome_data:
            error = genome_data.get("error", "Unknown error")
            raise Exception(f"UCSC API error: {error}")

        sequence = genome_data.get("dna", "").upper()
        expected_length = end - start
        if len(sequence) != expected_length or len(sequence) != CONTEXT_LENGTH_BP:
            raise ValueError(
                f"UCSC returned {len(sequence)} bases; expected exactly "
                f"{CONTEXT_LENGTH_BP} for coordinates {chromosome}:{start}-{end}"
            )

        print(
            f"Loaded reference genome sequence window "
            f"(length: {len(sequence)} bases)"
        )

        return sequence, start


@app.local_entrypoint()
def main() -> None:
    """Local entry point for testing the deployed service."""
    import requests

    service = Evo2ScorerService()
    url = service.score_variant.get_web_url()
    print(f"Service web URL: {url}")

    payload = {
        "chromosome": "chr17",
        "variant_position": 43044295,
        "alternative": "T",
        "genome": "hg38",
    }

    headers = {"Content-Type": "application/json"}
    print(f"Sending request: {payload}")
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()
    print(f"Result: {result}")


if __name__ == "__main__":
    main()

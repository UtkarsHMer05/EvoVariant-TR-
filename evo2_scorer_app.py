"""EvoVariant-TR Modal deployment entry point (Milestone 52-53, M065).

Deploy with:
    modal deploy evo2_scorer_app.py

This is the NEW project's Modal app — it does NOT reuse the old project's
deployment identity (variant-analysis-evo2), per M19 cost-control policy.
"""

from __future__ import annotations

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
        raw_chrom = str(
            variant_data.get("chromosome", variant_data.get("chrom", ""))
        )
        pos = int(str(variant_data.get("position_1based", variant_data.get("variant_position"))))
        declared_ref = str(variant_data.get("reference", variant_data.get("ref", ""))).upper()
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
        if len(declared_ref) != 1 or len(alt) != 1 or declared_ref == alt:
            raise ValueError("the canonical Modal scorer accepts distinct SNVs only")

        chrom = normalize_chromosome(raw_chrom)
        normalized_id = f"GRCh38:{chrom}:{pos}:{declared_ref}>{alt}"
        cache_identity = CacheIdentity(
            model_id="evo2",
            checkpoint="evo2_7b",
            model_revision=EVO2_REPOSITORY_REVISION,
            preprocessing_revision="grch38-8192-v1",
            assembly="GRCh38",
            context_length_bp=CONTEXT_LENGTH_BP,
            orientation="forward_and_reverse",
            layer="raw_scores",
            normalized_variant_id=normalized_id,
        )
        cached = self.prediction_cache.get(cache_identity)
        if cached is not None:
            result = dict(cached.payload)
            provenance = dict(result.get("provenance", {}))
            provenance["cache_hit"] = True
            result["provenance"] = provenance
            return result

        print(f"Scoring variant: {chrom}:{pos} {declared_ref}>{alt} genome={genome}")

        sequence, seq_start = self._fetch_genome_sequence(
            position=pos, genome=genome, chromosome=chrom,
        )

        relative_pos = pos - 1 - seq_start

        if relative_pos < 0 or relative_pos >= len(sequence):
            raise ValueError(
                f"Variant position {pos} is outside the fetched window "
                f"(start={seq_start + 1}, end={seq_start + len(sequence)})"
            )

        ref = sequence[relative_pos]
        if ref != declared_ref:
            raise ValueError(
                f"reference allele mismatch at {chrom}:{pos}: "
                f"declared={declared_ref}, fetched={ref}"
            )

        alt_seq = (
            sequence[:relative_pos] + alt + sequence[relative_pos + 1:]
        )

        with TelemetryTimer(gpu_type=str(_modal_config["gpu_type"])) as timer:
            forward_ref = self._score_sequence(sequence)
            forward_alt = self._score_sequence(alt_seq)
            reverse_ref = self._score_sequence(reverse_complement(sequence))
            reverse_alt = self._score_sequence(reverse_complement(alt_seq))
        delta_fwd = forward_alt - forward_ref
        delta_rc = reverse_alt - reverse_ref
        delta_primary = (delta_fwd + delta_rc) / 2

        result = {
            "variant": f"{chrom}:g.{pos}{ref}>{alt}",
            "normalized_variant_id": normalized_id,
            "assembly": "GRCh38",
            "chromosome": chrom,
            "position_1based": pos,
            "reference": ref,
            "alternate": alt,
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
        if timer.result is not None:
            result["telemetry"] = timer.result.to_dict()
        self.prediction_cache.put(cache_identity, result)
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

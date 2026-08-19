"""EvoVariant-TR Modal deployment entry point (Milestone 52-53, M065).

Deploy with:
    modal deploy evo2_scorer_app.py

This is the NEW project's Modal app — it does NOT reuse the old project's
deployment identity (variant-analysis-evo2), per M19 cost-control policy.
"""

from __future__ import annotations

import modal
from evovariant_tr.modal_config import get_modal_config, get_modal_volumes
from modal import Image

_modal_config = get_modal_config()

# Build the Docker image for Evo 2 inference.
# This mirrors PARITY_REQUIREMENTS in modal_config.py.
evo2_image = (
    Image.from_registry(
        _modal_config["image"],
        add_python=_modal_config["python_version"],
    )
    .apt_install(
        ["build-essential", "cmake", "ninja-build",
         "libcudnn8", "libcudnn8-dev", "git", "gcc", "g++",
         "clang", "libclang-dev"],
    )
    .run_commands(
        "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124",
        "git clone --recurse-submodules https://github.com/ArcInstitute/evo2.git "
        "&& cd evo2 && pip install .",
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
)

# Use the NEW project identity, never the old one.
app = modal.App("evovariant-tr", image=evo2_image)

# Volumes for model caching.
_volumes = get_modal_volumes()
_hf_cache_volume = modal.Volume.from_name("hf_cache", create_if_missing=True)
_mount_path = "/root/.cache/huggingface"

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
        print("Evo 2 model loaded successfully.")

    @modal.fastapi_endpoint(method="POST")
    def score_variant(self, variant_data: dict[str, object]) -> dict[str, object]:
        """Score a single variant using Evo 2.

        Request body:
            chromosome: str (e.g., "chr17")
            variant_position: int (1-based)
            alternative: str (e.g., "T")
            genome: str (e.g., "hg38")
        """
        chrom = str(variant_data["chromosome"])
        pos = int(str(variant_data["variant_position"]))
        alt = str(variant_data["alternative"]).upper()
        genome = str(variant_data.get("genome", "hg38"))

        print(f"Scoring variant: {chrom}:{pos} alt={alt} genome={genome}")

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

        alt_seq = (
            sequence[:relative_pos] + alt + sequence[relative_pos + 1:]
        )

        ref_ll = self.model.score_sequences([sequence])[0]
        alt_ll = self.model.score_sequences([alt_seq])[0]
        delta = alt_ll - ref_ll

        return {
            "variant": f"{chrom}:g.{pos}{ref}>{alt}",
            "reference_score": float(ref_ll),
            "alternate_score": float(alt_ll),
            "score_delta": float(delta),
            "status": "completed",
            "provenance": {
                "scorer": "evo2_7b",
                "context_length": 8192,
                "strand": "forward",
                "scoring_semantics": "log_likelihood_ratio",
            },
        }

    def _fetch_genome_sequence(
        self, position: int, genome: str, chromosome: str,
        window_size: int = 8192,
    ) -> tuple[str, int]:
        """Fetch a sequence window from the UCSC API."""
        import requests

        half_window = window_size // 2
        start = max(0, position - 1 - half_window)
        end = position - 1 + half_window + 1

        print(
            f"Fetching {window_size}bp window around position {position} "
            f"from UCSC API..."
        )
        print(f"Coordinates: {chromosome}:{start}-{end} ({genome})")

        api_url = (
            f"https://api.genome.ucsc.edu/getData/sequence?genome={genome}"
            f";chrom={chromosome};start={start};end={end}"
        )
        response = requests.get(api_url)

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
        if len(sequence) != expected_length:
            print(
                f"Warning: received sequence length ({len(sequence)}) "
                f"differs from expected ({expected_length})"
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

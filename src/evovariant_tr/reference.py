"""GRCh38 reference genome acquisition and indexed access for EvoVariant-TR.

Design (Milestone 31-32):
- Reference is the GRCh38 assembly from the GATK Resource Bundle,
  specifically the `Homo_sapiens_assembly38.fasta` file with its `.fai` index.
- The exact source URL, release version, and SHA-256 are recorded and frozen.
- `ReferenceGenome` provides indexed random-access lookup of reference bases
  by chromosome and 1-based position (genomic convention).
"""

from __future__ import annotations

import gzip
import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

GRCh38_REFERENCE_NAME = "Homo_sapiens_assembly38"
GRCh38_FASTA_FILENAME = f"{GRCh38_REFERENCE_NAME}.fasta"
GRCh38_FAI_FILENAME = f"{GRCh38_FASTA_FILENAME}.fai"
GRCh38_GZ_FILENAME = f"{GRCh38_FASTA_FILENAME}.gz"

# Official GATK Resource Bundle download location
GATK_RESOURCE_BUNDLE_BASE = (
    "https://storage.googleapis.com/genomics-public-data/"
    "resources/GRCh38/"
)


@dataclass(frozen=True)
class ReferenceSource:
    """Frozen specification of the reference genome source."""

    name: str
    assembly: str
    fasta_filename: str
    fai_filename: str
    source_url: str
    description: str


GRCh38_SOURCE = ReferenceSource(
    name=GRCh38_REFERENCE_NAME,
    assembly="GRCh38",
    fasta_filename=GRCh38_FASTA_FILENAME,
    fai_filename=GRCh38_FAI_FILENAME,
    source_url=urljoin(
        GATK_RESOURCE_BUNDLE_BASE, "Homo_sapiens_assembly38.fasta"
    ),
    description="GRCh38 assembly38 from GATK Resource Bundle (Broad Institute)",
)

CHUNK_SIZE = 1 << 20


def sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file, streamed."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def download_reference(
    dest_dir: str | Path,
    source: ReferenceSource = GRCh38_SOURCE,
) -> Path:
    """Download the reference genome FASTA and create a .fai index.

    Uses curl (preferred) or urllib for download. Runs `samtools faidx`
    to index the FASTA.

    Returns the path to the indexed FASTA file.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    fasta_path = dest / source.fasta_filename

    if fasta_path.exists():
        sha = sha256_file(fasta_path)
        print(f"Reference already exists: {fasta_path} (sha256={sha})")
        return fasta_path

    gz_path = dest / f"{source.fasta_filename}.gz"
    print(f"Downloading {source.source_url} -> {gz_path}")

    curl_bin = shutil.which("curl")
    if curl_bin:
        subprocess.run(
            [curl_bin, "-fsSL", "-o", str(gz_path), source.source_url],
            check=True,
        )
    else:
        import urllib.request

        req = urllib.request.Request(
            source.source_url, headers={"User-Agent": "EvoVariant-TR/0.1"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            with gz_path.open("wb") as out:
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    out.write(chunk)

    print(f"Decompressing {gz_path} -> {fasta_path}")
    with gzip.open(gz_path, "rb") as gz_in:
        with fasta_path.open("wb") as f_out:
            while True:
                chunk = gz_in.read(CHUNK_SIZE)
                if not chunk:
                    break
                f_out.write(chunk)
    gz_path.unlink()

    sha = sha256_file(fasta_path)
    print(f"Downloaded {fasta_path} (sha256={sha})")
    return fasta_path


def index_reference(fasta_path: Path) -> Path:
    """Create a .fai index for the FASTA file using samtools."""
    samtools_bin = shutil.which("samtools")
    if samtools_bin:
        subprocess.run(
            [samtools_bin, "faidx", str(fasta_path)],
            check=True,
        )
        print(f"Index created: {fasta_path}.fai")
        return fasta_path
    raise RuntimeError(
        "samtools not found; cannot create FASTA index."
    )


class ReferenceGenome:
    """Indexed access to a reference genome FASTA.

    Provides single-base lookup by chromosome and 1-based position.

    Requires: a FASTA file with a .fai index (created by `samtools faidx`).
    """

    def __init__(self, fasta_path: str | Path) -> None:
        self.fasta_path = Path(fasta_path)
        self.fai_path = self.fasta_path.with_suffix(self.fasta_path.suffix + ".fai")
        if not self.fasta_path.is_file():
            raise FileNotFoundError(f"FASTA not found: {self.fasta_path}")
        if not self.fai_path.is_file():
            raise FileNotFoundError(f"FASTA index not found: {self.fai_path}")
        self._fai = self._load_index()

    def _load_index(self) -> dict[str, tuple[int, int, int, int, int]]:
        """Load the .fai index.

        Returns mapping of chromosome -> (length, offset, line_bases, line_width, qual_offset).
        """
        index: dict[str, tuple[int, int, int, int, int]] = {}
        with self.fai_path.open("r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                chrom = parts[0]
                length = int(parts[1])
                offset = int(parts[2])
                line_bases = int(parts[3])
                line_width = int(parts[4])
                qual_offset = int(parts[5]) if len(parts) > 5 else 0
                index[chrom] = (length, offset, line_bases, line_width, qual_offset)
        return index

    @property
    def chromosomes(self) -> list[str]:
        """Return list of chromosome names in the reference."""
        return list(self._fai.keys())

    def get_base(self, chrom: str, position: int) -> str | None:
        """Get the reference base at a 1-based genomic position.

        Returns the base as an uppercase string, or None if the position
        is out of range or the chromosome is not found.
        """
        if chrom not in self._fai:
            return None
        length, offset, line_bases, line_width, _ = self._fai[chrom]
        if position < 1 or position > length:
            return None

        # Convert 1-based position to 0-based byte offset
        byte_pos = offset + (position - 1) + (position - 1) // line_bases

        with self.fasta_path.open("rb") as f:
            f.seek(byte_pos)
            base = f.read(1)
            if not base or base == b"\n":
                return None
            return base.decode("ascii").upper()

    def get_sequence(self, chrom: str, start: int, stop: int) -> str | None:
        """Get a reference sequence (1-based inclusive coordinates).

        Returns None if the chromosome is not found or coordinates are invalid.
        For multi-line regions, uses samtools faidx if available.
        """
        if chrom not in self._fai:
            return None
        if start < 1 or stop < start:
            return None

        length, offset, line_bases, line_width, _ = self._fai[chrom]
        if stop > length:
            return None

        seq_len = stop - start + 1
        if seq_len > line_bases:
            return self._get_sequence_samtools(chrom, start, stop)

        bases = []
        pos = start
        while pos <= stop:
            line_idx = (pos - 1) // line_bases
            col_in_line = (pos - 1) % line_bases
            byte_pos = offset + line_idx * line_width + col_in_line

            with self.fasta_path.open("rb") as f:
                f.seek(byte_pos)
                remaining = stop - pos + 1
                available = line_bases - col_in_line
                to_read = min(remaining, available)
                chunk = f.read(to_read)
                bases.append(chunk.decode("ascii").upper())
                pos += to_read

        return "".join(bases)

    def _get_sequence_samtools(self, chrom: str, start: int, stop: int) -> str | None:
        """Use samtools faidx for multi-line extraction."""
        samtools_bin = shutil.which("samtools")
        if not samtools_bin:
            return None
        result = subprocess.run(
            [
                samtools_bin, "faidx",
                str(self.fasta_path),
                f"{chrom}:{start}-{stop}",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        lines = result.stdout.strip().split("\n")
        return "".join(lines[1:]) if len(lines) > 1 else ""

    def validate_allele(self, chrom: str, position: int, expected: str) -> bool:
        """Check if the reference base matches the expected allele.

        position is 1-based.
        """
        actual = self.get_base(chrom, position)
        if actual is None:
            return False
        return actual.upper() == expected.upper()

    def validate_position(self, chrom: str, position: int) -> bool:
        """Check if a position is within the bounds of the chromosome."""
        if chrom not in self._fai:
            return False
        length, _, _, _, _ = self._fai[chrom]
        return 1 <= position <= length

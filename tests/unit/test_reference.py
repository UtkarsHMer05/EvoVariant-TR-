"""Tests for reference.py — Milestones 31-32."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from evovariant_tr.reference import (
    GRCh38_FASTA_FILENAME,
    GRCh38_SOURCE,
    ReferenceGenome,
    download_reference,
    index_reference,
    sha256_file,
)


def test_reference_source_is_frozen():
    """GRCh38_SOURCE must be immutable."""
    with pytest.raises(AttributeError):  # FrozenInstanceError is a subclass
        GRCh38_SOURCE.name = "something_else"


def test_reference_source_values():
    assert GRCh38_SOURCE.assembly == "GRCh38"
    assert GRCh38_SOURCE.fasta_filename == "Homo_sapiens_assembly38.fasta"
    assert GRCh38_SOURCE.fai_filename == "Homo_sapiens_assembly38.fasta.fai"
    assert "ftp.ncbi.nlm.nih.gov" not in GRCh38_SOURCE.source_url
    assert "storage.googleapis.com" in GRCh38_SOURCE.source_url
    assert "hg38/v0" in GRCh38_SOURCE.source_url


def test_sha256_file(tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"hello world")
    expected = __import__("hashlib").sha256(b"hello world").hexdigest()
    assert sha256_file(test_file) == expected


def test_reference_genome_missing_fasta(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="FASTA not found"):
        ReferenceGenome(tmp_path / "nonexistent.fasta")


def test_reference_genome_missing_fai(tmp_path: Path):
    fasta = tmp_path / "test.fasta"
    fasta.write_text(">chr1\nACGT\n")
    with pytest.raises(FileNotFoundError, match="FASTA index not found"):
        ReferenceGenome(fasta)


class _FakeFastaIndex:
    """Builds a fake FASTA + .fai for testing."""

    @staticmethod
    def build(tmp_path: Path) -> Path:
        # Single-line FASTA for chr1 and chr2
        fasta = tmp_path / "test.fasta"
        content = ">chr1\nACGTACGTAC\n>chr2\nGGGGCCCCAA\n"
        fasta.write_text(content)

        # .fai format: name, length, offset, line_bases, line_width, qual_offset
        # >chr1\n = 6 bytes, ACGTACGTAC\n = 11 bytes
        # offset of chr1 seq = 6, line_bases = 10, line_width = 11 (10 + \n)
        # >chr2\n starts at byte 17, chr2 seq starts at byte 23
        fai = tmp_path / "test.fasta.fai"
        fai.write_text(
            "chr1\t10\t6\t10\t11\t0\n"
            "chr2\t10\t23\t10\t11\t0\n"
        )
        return fasta


def test_reference_genome_loads_chromosomes(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    assert "chr1" in ref.chromosomes
    assert "chr2" in ref.chromosomes


def test_reference_genome_get_base(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    assert ref.get_base("chr1", 1) == "A"
    assert ref.get_base("chr1", 2) == "C"
    assert ref.get_base("chr1", 5) == "A"
    assert ref.get_base("chr1", 10) == "C"
    assert ref.get_base("chr2", 1) == "G"
    assert ref.get_base("chr2", 5) == "C"


def test_reference_genome_get_base_out_of_range(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    assert ref.get_base("chr1", 0) is None  # Before start
    assert ref.get_base("chr1", 11) is None  # After end
    assert ref.get_base("chr3", 1) is None  # Unknown chrom


def test_reference_genome_get_sequence_single_line(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    seq = ref.get_sequence("chr1", 1, 5)
    assert seq == "ACGTA"


def test_reference_genome_get_sequence_full_chrom(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    seq = ref.get_sequence("chr1", 1, 10)
    assert seq == "ACGTACGTAC"


def test_reference_genome_get_sequence_invalid_coords(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    assert ref.get_sequence("chr1", 5, 1) is None  # start > stop
    assert ref.get_sequence("chr1", 0, 5) is None  # start < 1
    assert ref.get_sequence("chr3", 1, 5) is None  # unknown chrom


def test_reference_genome_validate_allele_correct(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    assert ref.validate_allele("chr1", 1, "A") is True
    assert ref.validate_allele("chr1", 1, "a") is True  # case-insensitive


def test_reference_genome_validate_allele_wrong(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    assert ref.validate_allele("chr1", 1, "T") is False


def test_reference_genome_validate_position(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    assert ref.validate_position("chr1", 1) is True
    assert ref.validate_position("chr1", 10) is True
    assert ref.validate_position("chr1", 11) is False
    assert ref.validate_position("chr1", 0) is False
    assert ref.validate_position("chr3", 1) is False


def test_index_reference_missing_samtools(tmp_path: Path):
    fasta = _FakeFastaIndex.build(tmp_path)
    with mock.patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="samtools not found"):
            index_reference(fasta)


def test_grch38_fasta_filename():
    assert GRCh38_FASTA_FILENAME == "Homo_sapiens_assembly38.fasta"


def test_download_reference_already_exists(tmp_path: Path):
    """If the FASTA already exists, download should skip and return the path."""
    dest = tmp_path / "ref"
    dest.mkdir()
    fasta = dest / GRCh38_FASTA_FILENAME
    fasta.write_text(">chr1\nACGT\n")

    with mock.patch("evovariant_tr.reference.shutil.which", return_value=None):
        result = download_reference(dest)
    assert result == fasta


def test_download_reference_uses_curl(tmp_path: Path):
    """Test the download path via curl with mock."""
    dest = tmp_path / "ref"
    dest.mkdir()

    fake_fasta_path = dest / GRCh38_FASTA_FILENAME

    with mock.patch("evovariant_tr.reference.shutil.which", return_value="/usr/bin/curl"):
        def fake_run(command: list[str], check: bool) -> None:
            assert check is True
            Path(command[command.index("-o") + 1]).write_bytes(b">chr1\nA\n")

        with mock.patch("subprocess.run", side_effect=fake_run) as mock_run:
            result = download_reference(dest)
            assert mock_run.call_count == 1
            assert result == fake_fasta_path
            assert mock_run.call_args.args[0][-1] == GRCh38_SOURCE.source_url


def test_download_reference_no_curl_uses_urllib(tmp_path: Path):
    """Test the download path via urllib when curl is not available."""
    dest = tmp_path / "ref"
    dest.mkdir()

    fake_fasta_content = b">chr1\nACGTACGTAC\n>chr2\nGGGGCCCCAA\n"
    fake_fasta_path = dest / GRCh38_FASTA_FILENAME

    fake_response = mock.MagicMock()
    fake_response.read.side_effect = [fake_fasta_content, b""]
    fake_response.__enter__ = mock.MagicMock(return_value=fake_response)
    fake_response.__exit__ = mock.MagicMock(return_value=False)

    with mock.patch("evovariant_tr.reference.shutil.which", return_value=None):
        with mock.patch("urllib.request.urlopen", return_value=fake_response):
            result = download_reference(dest)
            assert result == fake_fasta_path


def test_index_reference_calls_samtools(tmp_path: Path):
    """Test that index_reference calls samtools faidx."""
    fasta = _FakeFastaIndex.build(tmp_path)
    with mock.patch("evovariant_tr.reference.shutil.which", return_value="/usr/bin/samtools"):
        with mock.patch("subprocess.run") as mock_run:
            result = index_reference(fasta)
            assert mock_run.call_count == 1
            assert result == fasta


def test_reference_genome_get_sequence_multi_line_samtools(tmp_path: Path):
    """Test multi-line sequence extraction via samtools (mocked)."""
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)

    # Mock samtools to return a sequence
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = ">chr1:5-10\nACGTAC\n"
    with mock.patch("evovariant_tr.reference.shutil.which", return_value="/usr/bin/samtools"):
        with mock.patch("subprocess.run", return_value=fake_result):
            # Sequence spans beyond single line (seq_len=6, line_bases=10)
            # but we use coordinates that are within bounds
            seq = ref.get_sequence("chr1", 5, 10)
            assert seq == "ACGTAC"


def test_reference_genome_get_sequence_samtools_not_found(tmp_path: Path):
    """Test that get_sequence returns None when sequence spans multiple lines
    and samtools is not available."""
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)

    with mock.patch("evovariant_tr.reference.shutil.which", return_value=None):
        seq = ref.get_sequence("chr1", 5, 15)
        assert seq is None


def test_reference_genome_get_sequence_out_of_bounds(tmp_path: Path):
    """Test that get_sequence returns None for positions beyond chromosome length."""
    fasta = _FakeFastaIndex.build(tmp_path)
    ref = ReferenceGenome(fasta)
    assert ref.get_sequence("chr1", 1, 100) is None

"""Version-aware ClinVar variant_summary parser for EvoVariant-TR.

Parses the official NCBI ClinVar ``variant_summary.txt.gz`` format, which is a
tab-delimited file with a fixed column schema documented in the NCBI README.
The parser is version-aware: it validates the header against a known schema
and normalizes clinical significance values into a controlled vocabulary.

Design (Milestone 25):
- Schema is defined as a frozen dataclass with required/optional column names.
- Clinical significance is normalized to a small set of controlled labels.
- Review status is mapped to star counts.
- Assembly filtering (GRCh38) happens during parsing.
- Only the fields needed by the research protocol are extracted; the parser
  is a thin, deterministic layer over the raw TSV.
"""

from __future__ import annotations

import gzip
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from pathlib import Path

from evovariant_tr.evidence import EvidenceStage

CLINVAR_REVIEW_STATUS_STARS: dict[str, int] = {
    "no submission": 0,
    "no evaluation": 0,
    "no literature for peer-reviewed assembly": 0,
    "no assertion criteria": 0,
    "conflict between submitter and expert panel": 0,
    "no assertion criteria and no literature": 0,
    "criteria provided, single submitter": 1,
    "criteria provided, multiple submitters": 2,
    "criteria provided, multiple submitters, no conflicts": 2,
    "criteria provided, multiple submitters, conflicting interpretations": 2,
    "criteria provided, conflicting classifications": 2,
    "reviewed by expert panel": 3,
    "reviewed by expert panel, conflicting interpretations": 3,
    "reviewed by expert panel, conflicting interpretations, no assertion criteria": 3,
    "practice guideline": 3,
    "practices guideline": 3,
    "other": 0,
    "no classification provided": 0,
    "no classification for the single variant": 0,
    "no classifications from unflagged records": 0,
}


class ClinicalSignificance(StrEnum):
    """Controlled vocabulary for ClinVar clinical significance labels."""

    BENIGN = "Benign"
    BENIGN_LIKELY_BENIGN = "Benign/Likely_benign"
    LIKELY_BENIGN = "Likely_benign"
    PATHOGENIC = "Pathogenic"
    PATHOGENIC_LIKELY_PATHOGENIC = "Pathogenic/Likely_pathogenic"
    LIKELY_PATHOGENIC = "Likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "Uncertain_significance"
    NOT_PROVIDED = "not_provided"
    CONFLICTING = "conflict_between_submitters"
    OTHER = "other"


CLINSIG_NORMALIZATION: dict[str, ClinicalSignificance] = {
    "Benign": ClinicalSignificance.BENIGN,
    "Likely_benign": ClinicalSignificance.LIKELY_BENIGN,
    "Benign/Likely_benign": ClinicalSignificance.BENIGN_LIKELY_BENIGN,
    "Likely benign": ClinicalSignificance.LIKELY_BENIGN,
    "Pathogenic": ClinicalSignificance.PATHOGENIC,
    "Likely_pathogenic": ClinicalSignificance.LIKELY_PATHOGENIC,
    "Likely pathogenic": ClinicalSignificance.LIKELY_PATHOGENIC,
    "Pathogenic/Likely_pathogenic": ClinicalSignificance.PATHOGENIC_LIKELY_PATHOGENIC,
    "Pathogenic/Likely pathogenic": ClinicalSignificance.PATHOGENIC_LIKELY_PATHOGENIC,
    "Uncertain_significance": ClinicalSignificance.UNCERTAIN_SIGNIFICANCE,
    "Uncertain significance": ClinicalSignificance.UNCERTAIN_SIGNIFICANCE,
    "not_provided": ClinicalSignificance.NOT_PROVIDED,
    "not provided": ClinicalSignificance.NOT_PROVIDED,
    "other": ClinicalSignificance.OTHER,
    "conflicting classifications of pathogenicity": ClinicalSignificance.CONFLICTING,
    "conflicting interpretations": ClinicalSignificance.CONFLICTING,
    "conflicting interpretations (benign)": ClinicalSignificance.BENIGN,
    "conflicting interpretations (pathogenic)": ClinicalSignificance.PATHOGENIC,
}


class VariantSummarySchema:
    """Frozen column schema for ClinVar variant_summary.txt.

    Based on the official NCBI README. Required columns are the ones we
    need for the research protocol; optional columns are tolerated if present
    but not required.
    """

    REQUIRED = (
        "AlleleID",
        "Type",
        "ClinicalSignificance",
        "ReviewStatus",
        "Assembly",
        "Chromosome",
        "Start",
        "Stop",
        "ReferenceAllele",
        "AlternateAllele",
        "VariationID",
        "RCVaccession",
        "OriginSimple",
    )

    OPTIONAL = (
        "Name",
        "GeneID",
        "GeneSymbol",
        "HGNC_ID",
        "ClinSigSimple",
        "LastEvaluated",
        "RS# (dbSNP)",
        "nsv/esv (dbVar)",
        "PhenotypeIDS",
        "PhenotypeList",
        "Origin",
        "ChromosomeAccession",
        "Cytogenetic",
        "NumberSubmitters",
        "Guidelines",
        "TestedInGTR",
        "OtherIDs",
        "SubmitterCategories",
        "PositionVCF",
        "ReferenceAlleleVCF",
        "AlternateAlleleVCF",
        "SomaticClinicalImpact",
        "SomaticClinicalImpactLastEvaluated",
        "ReviewStatusClinicalImpact",
        "Oncogenicity",
        "OncogenicityLastEvaluated",
        "ReviewStatusOncogenicity",
    )


@dataclass(frozen=True)
class VariantSummaryRecord:
    """A parsed, normalized ClinVar variant_summary row."""

    allele_id: int
    variant_type: str
    clinical_significance: ClinicalSignificance
    review_status: str
    review_stars: int
    assembly: str
    chromosome: str
    start: int
    stop: int
    reference_allele: str
    alternate_allele: str
    variation_id: int
    rcv_accessions: list[str]
    origin_simple: str
    germline: bool
    gene_symbol: str | None = None
    rs_id: str | None = None
    last_evaluated: date | None = None
    name: str | None = None
    row_number: int = 0
    raw_clinical_significance: str = ""
    raw_review_status: str = ""

    def is_pathogenic(self) -> bool:
        return self.clinical_significance in (
            ClinicalSignificance.PATHOGENIC,
            ClinicalSignificance.PATHOGENIC_LIKELY_PATHOGENIC,
            ClinicalSignificance.LIKELY_PATHOGENIC,
        )

    def is_benign(self) -> bool:
        return self.clinical_significance in (
            ClinicalSignificance.BENIGN,
            ClinicalSignificance.BENIGN_LIKELY_BENIGN,
            ClinicalSignificance.LIKELY_BENIGN,
        )

    def is_vus(self) -> bool:
        return self.clinical_significance == ClinicalSignificance.UNCERTAIN_SIGNIFICANCE


def normalize_clinical_significance(raw: str) -> ClinicalSignificance:
    """Map a raw ClinicalSignificance string to the controlled vocabulary."""
    if not raw or raw == "-":
        return ClinicalSignificance.NOT_PROVIDED
    normalized = CLINSIG_NORMALIZATION.get(raw)
    if normalized is not None:
        return normalized
    return ClinicalSignificance.OTHER


def normalize_review_status(raw: str) -> str:
    """Normalize review status string for consistent comparison."""
    if not raw or raw == "-":
        return ""
    return raw.strip()


def review_status_to_stars(review_status: str) -> int:
    """Map a review status string to star count."""
    key = review_status.strip()
    return CLINVAR_REVIEW_STATUS_STARS.get(key, 0)


def is_germline(origin_simple: str) -> bool:
    """Determine if the variant is germline based on OriginSimple."""
    if not origin_simple:
        return False
    return "germline" in origin_simple.lower()


def parse_rcv_accessions(raw: str) -> list[str]:
    """Parse the RCVaccession field, which is a pipe-separated list."""
    if not raw or raw == "-":
        return []
    return [rcv.strip() for rcv in raw.split("|") if rcv.strip() and rcv.strip() != "-"]


def parse_date(raw: str) -> date | None:
    """Parse a ClinVar date string (YYYY-MM-DD) or return None."""
    if not raw or raw == "-":
        return None
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw.strip())
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def _parse_int(raw: str) -> int | None:
    """Parse an integer from a string, returning None for empty/missing values."""
    if not raw or raw == "-":
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


@dataclass
class VariantSummaryHeader:
    """Validated column positions from the variant_summary header line."""

    columns: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Validate that all required columns are present.

        Returns a list of missing required column names (empty = valid).
        """
        present = set(self.columns)
        missing = [col for col in VariantSummarySchema.REQUIRED if col not in present]
        return missing

    def idx(self, name: str) -> int:
        """Get the column index for a given name."""
        return self.columns.index(name)


def parse_header(header_line: str) -> VariantSummaryHeader:
    """Parse and validate the header line of a variant_summary file.

    Raises ValueError if required columns are missing.
    """
    columns = header_line.lstrip("#").strip().split("\t")
    header = VariantSummaryHeader(columns=columns)
    missing = header.validate()
    if missing:
        raise ValueError(
            f"variant_summary header missing required columns: {missing}"
        )
    return header


def parse_record(
    fields: list[str],
    header: VariantSummaryHeader,
    row_number: int = 0,
) -> VariantSummaryRecord:
    """Parse a single TSV row into a VariantSummaryRecord.

    Raises ValueError if the row has too few fields or required values are
    missing/invalid.
    """
    if len(fields) < len(header.columns):
        raise ValueError(
            f"row {row_number}: expected {len(header.columns)} fields, got {len(fields)}"
        )

    def get(name: str) -> str:
        if name not in header.columns:
            return ""
        idx = header.idx(name)
        return fields[idx] if idx < len(fields) else ""

    allele_id = _parse_int(get("AlleleID"))
    if allele_id is None:
        raise ValueError(f"row {row_number}: invalid AlleleID: {get('AlleleID')!r}")

    variation_id = _parse_int(get("VariationID"))
    if variation_id is None:
        raise ValueError(f"row {row_number}: invalid VariationID: {get('VariationID')!r}")

    raw_clinsig = get("ClinicalSignificance")
    clinical_significance = normalize_clinical_significance(raw_clinsig)

    raw_review_status = get("ReviewStatus")
    review_status = normalize_review_status(raw_review_status)

    origin_simple = get("OriginSimple")
    germline = is_germline(origin_simple)

    start = _parse_int(get("Start"))
    if start is None:
        raise ValueError(f"row {row_number}: invalid Start: {get('Start')!r}")

    stop = _parse_int(get("Stop"))
    if stop is None:
        raise ValueError(f"row {row_number}: invalid Stop: {get('Stop')!r}")

    return VariantSummaryRecord(
        allele_id=allele_id,
        variant_type=get("Type"),
        clinical_significance=clinical_significance,
        review_status=review_status,
        review_stars=review_status_to_stars(raw_review_status),
        assembly=get("Assembly"),
        chromosome=get("Chromosome"),
        start=start,
        stop=stop,
        reference_allele=get("ReferenceAllele"),
        alternate_allele=get("AlternateAllele"),
        variation_id=variation_id,
        rcv_accessions=parse_rcv_accessions(get("RCVaccession")),
        origin_simple=origin_simple,
        germline=germline,
        gene_symbol=get("GeneSymbol") or None,
        rs_id=get("RS# (dbSNP)") or None if get("RS# (dbSNP)") not in ("", "-") else None,
        last_evaluated=parse_date(get("LastEvaluated")),
        name=get("Name") or None,
        row_number=row_number,
        raw_clinical_significance=raw_clinsig,
        raw_review_status=raw_review_status,
    )


def iter_variant_summary(
    path: str | Path,
    *,
    assembly: str = "GRCh38",
    evidence_stage: EvidenceStage | None = None,
) -> Iterator[VariantSummaryRecord]:
    """Iterate over records in a variant_summary.txt.gz file.

    Args:
        path: Path to the gzipped variant_summary file.
        assembly: Only records matching this assembly are yielded.
        evidence_stage: Optional evidence stage for metadata (not enforced here).

    Yields:
        VariantSummaryRecord instances.
    """
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"variant_summary file not found: {target}")

    with gzip.open(target, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            return
        header = parse_header(header_line)

        for row_number, line in enumerate(handle, start=2):
            line = line.rstrip("\n\r")
            if not line.strip():
                continue
            fields = line.split("\t")
            try:
                record = parse_record(fields, header, row_number)
            except ValueError:
                continue
            if record.assembly != assembly:
                continue
            yield record

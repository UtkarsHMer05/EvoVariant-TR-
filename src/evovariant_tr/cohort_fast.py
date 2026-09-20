"""Optimized cohort construction for EvoVariant-TR.

This module provides `build_cohort_fast`, a memory-efficient two-pass
implementation that processes variant_summary files without creating
dataclass objects for every row.

Pass 1: Load t0 snapshot, collecting only germline SNVs that are VUS
        (Uncertain_significance, >=2 review stars).
Pass 2: Load t1 snapshot, collecting only germline SNVs.
Join:   Match t0 VUS to t1 records by (chrom, start, ref, alt) identity.

This is needed because each variant_summary file has ~6-9 million rows
and creating full record objects for every row is too slow/memory-heavy.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

from evovariant_tr.clinvar_parser import parse_header

MIN_REVIEW_STARS = 2

SNV_TYPES = frozenset({"SNV", "single nucleotide variant"})

CLINSIG_MAP: dict[str, str] = {
    "Uncertain significance": "UNCERTAIN",
    "Uncertain_significance": "UNCERTAIN",
    "Pathogenic": "PATH",
    "Likely pathogenic": "LPATH",
    "Likely_pathogenic": "LPATH",
    "Benign": "BENIGN",
    "Likely benign": "LBENIGN",
    "Likely_benign": "LBENIGN",
    "Pathogenic/Likely pathogenic": "PPATH",
    "Pathogenic/Likely_pathogenic": "PPATH",
    "Benign/Likely benign": "PBENIGN",
    "Benign/Likely_benign": "PBENIGN",
    "Conflicting classifications of pathogenicity": "CONFLICT",
    "conflicting interpretations": "CONFLICT",
    "other": "OTHER",
    "not provided": "NOT_PROVIDED",
    "not_provided": "NOT_PROVIDED",
}

PATH_SIGS = frozenset({"PATH", "LPATH", "PPATH"})
BENIGN_SIGS = frozenset({"BENIGN", "LBENIGN", "PBENIGN"})

REVIEW_STARS: dict[str, int] = {
    "no assertion criteria provided": 0,
    "no classification provided": 0,
    "no classification for the single variant": 0,
    "criteria provided, single submitter": 1,
    "criteria provided, multiple submitters": 2,
    "criteria provided, multiple submitters, no conflicts": 2,
    "criteria provided, multiple submitters, conflicting interpretations": 2,
    "criteria provided, conflicting classifications": 2,
    "reviewed by expert panel": 3,
    "reviewed by expert panel, conflicting interpretations": 3,
    "reviewed by expert panel, conflicting interpretations, no assertion criteria": 3,
    "practice guideline": 3,
}


def _variant_fields(
    parts: list[str],
    col: dict[str, int],
) -> tuple[int, str, str] | None:
    """Use ClinVar's VCF-normalized allele columns when present."""
    position_raw = parts[col["PositionVCF"]] if "PositionVCF" in col else ""
    if position_raw in ("", "-"):
        position_raw = parts[col["Start"]]
    try:
        start = int(position_raw)
    except ValueError:
        return None
    reference = (
        parts[col["ReferenceAlleleVCF"]]
        if "ReferenceAlleleVCF" in col
        else parts[col["ReferenceAllele"]]
    )
    alternate = (
        parts[col["AlternateAlleleVCF"]]
        if "AlternateAlleleVCF" in col
        else parts[col["AlternateAllele"]]
    )
    if reference in ("", "-"):
        reference = parts[col["ReferenceAllele"]]
    if alternate in ("", "-"):
        alternate = parts[col["AlternateAllele"]]
    return start, reference, alternate


class FastOutcome(StrEnum):
    RESOLVED_PATHOGENIC = "resolved_pathogenic"
    RESOLVED_BENIGN = "resolved_benign"
    UNRESOLVED = "unresolved"
    EXCLUDED = "excluded"


@dataclass
class FastVariant:
    chrom: str
    start: int
    ref: str
    alt: str
    t0_significance: str
    t0_stars: int
    t1_significance: str | None
    t1_stars: int
    outcome: str
    gene: str | None
    allele_id_t0: int | None
    allele_id_t1: int | None


@dataclass
class FastCohortFlow:
    total_t0_records: int = 0
    t0_germline_snv: int = 0
    t0_grch38: int = 0
    t0_vus_at_t0: int = 0
    t0_vus_meets_star_gate: int = 0
    t0_unique_variants: int = 0
    t1_definitive_meets_star_gate: int = 0
    t1_resolved_from_t0_vus: int = 0
    t1_pathogenic: int = 0
    t1_benign: int = 0
    t1_unresolved: int = 0
    excluded_no_t1_record: int = 0


def _load_t0_vus(
    path: str | Path,
    min_stars: int | None = None,
) -> tuple[dict[tuple[str, int, str, str], dict[str, Any]], dict[str, int]]:
    """Load t0 snapshot, collecting all VUS germline GRCh38 SNVs by default.

    Returns (vus_dict, counts).
    vus_dict maps identity -> {stars, allele_id, gene, raw_clinsig, review_status}
    """
    target = Path(path)
    t0_vus: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    counts = {"total": 0, "germline_snv": 0, "grch38": 0}

    with gzip.open(target, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            return t0_vus, counts
        header = parse_header(header_line)
        col = {name: header.idx(name) for name in header.columns}

        for line in handle:
            fields = line.rstrip("\n\r")
            if not fields.strip():
                continue
            parts = fields.split("\t")
            if len(parts) < len(col):
                continue
            counts["total"] += 1

            vtype = parts[col["Type"]]
            origin = parts[col["OriginSimple"]]
            is_snv = vtype in SNV_TYPES
            is_germline = "germline" in origin.lower()

            if not is_snv or not is_germline:
                continue

            counts["germline_snv"] += 1
            assembly = parts[col["Assembly"]]
            if assembly != "GRCh38":
                continue
            counts["grch38"] += 1

            clinsig_raw = parts[col["ClinicalSignificance"]]
            clinsig = CLINSIG_MAP.get(clinsig_raw)

            if clinsig != "UNCERTAIN":
                continue

            review_status = parts[col["ReviewStatus"]]
            stars = REVIEW_STARS.get(review_status.strip(), 0)
            if min_stars is not None and stars < min_stars:
                continue

            chrom = parts[col["Chromosome"]]
            variant_fields = _variant_fields(parts, col)
            if variant_fields is None:
                continue
            start, ref, alt = variant_fields
            if (
                len(ref) != 1
                or len(alt) != 1
                or ref.upper() not in "ACGT"
                or alt.upper() not in "ACGT"
                or ref.upper() == alt.upper()
            ):
                continue
            identity = (chrom, start, ref, alt)

            gene_idx = col.get("GeneSymbol")
            gene = parts[gene_idx] if gene_idx is not None else None

            rec = {
                "stars": stars,
                "allele_id": int(parts[col["AlleleID"]]),
                "gene": gene if gene and gene != "-" else None,
                "raw_clinsig": clinsig_raw,
                "review_status": review_status,
            }

            existing = t0_vus.get(identity)
            if existing is None or rec["stars"] > existing["stars"]:
                t0_vus[identity] = rec

    return t0_vus, counts


def _load_t1_snapshots(
    path: str | Path,
    min_stars: int = MIN_REVIEW_STARS,
) -> tuple[dict[tuple[str, int, str, str], dict[str, Any]], dict[str, int]]:
    """Load t1 snapshot, collecting all germline SNV records.

    Returns (records_dict, counts).
    records_dict maps identity -> {stars, allele_id, gene, raw_clinsig, review_status, clinsig}
    """
    target = Path(path)
    t1_data: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    counts = {"total": 0, "germline_snv": 0, "grch38": 0}

    with gzip.open(target, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            return t1_data, counts
        header = parse_header(header_line)
        col = {name: header.idx(name) for name in header.columns}

        for line in handle:
            fields = line.rstrip("\n\r")
            if not fields.strip():
                continue
            parts = fields.split("\t")
            if len(parts) < len(col):
                continue
            counts["total"] += 1

            vtype = parts[col["Type"]]
            origin = parts[col["OriginSimple"]]
            is_snv = vtype in SNV_TYPES
            is_germline = "germline" in origin.lower()

            if not is_snv or not is_germline:
                continue

            counts["germline_snv"] += 1
            assembly = parts[col["Assembly"]]
            if assembly != "GRCh38":
                continue
            counts["grch38"] += 1

            clinsig_raw = parts[col["ClinicalSignificance"]]
            clinsig = CLINSIG_MAP.get(clinsig_raw, "OTHER")

            review_status = parts[col["ReviewStatus"]]
            stars = REVIEW_STARS.get(review_status.strip(), 0)

            chrom = parts[col["Chromosome"]]
            variant_fields = _variant_fields(parts, col)
            if variant_fields is None:
                continue
            start, ref, alt = variant_fields
            if (
                len(ref) != 1
                or len(alt) != 1
                or ref.upper() not in "ACGT"
                or alt.upper() not in "ACGT"
                or ref.upper() == alt.upper()
            ):
                continue
            identity = (chrom, start, ref, alt)

            gene_idx = col.get("GeneSymbol")
            gene = parts[gene_idx] if gene_idx is not None else None

            rec = {
                "stars": stars,
                "allele_id": int(parts[col["AlleleID"]]),
                "gene": gene if gene and gene != "-" else None,
                "raw_clinsig": clinsig_raw,
                "review_status": review_status,
                "clinsig": clinsig,
            }

            existing = t1_data.get(identity)
            if existing is None or rec["stars"] > existing["stars"]:
                t1_data[identity] = rec

    return t1_data, counts


def build_cohort_fast(
    t0_path: str | Path,
    t1_path: str | Path,
    t0_release_date: date | None = None,
    t1_release_date: date | None = None,
    min_review_stars: int = MIN_REVIEW_STARS,
) -> dict[str, Any]:
    """Build the temporal cohort efficiently from raw archives.

    Returns a dict with cohort results and flow counts.
    """
    flow = FastCohortFlow()

    # Pass 1: Load t0 VUS
    t0_vus, t0_counts = _load_t0_vus(t0_path)
    flow.total_t0_records = t0_counts["total"]
    flow.t0_germline_snv = t0_counts["germline_snv"]
    flow.t0_grch38 = t0_counts["grch38"]
    flow.t0_vus_meets_star_gate = len(t0_vus)
    flow.t0_vus_at_t0 = flow.t0_vus_meets_star_gate

    # Pass 2: Load t1 (all germline SNVs)
    t1_data, _ = _load_t1_snapshots(t1_path, min_review_stars)

    flow.t0_unique_variants = len(t0_vus)

    # Join
    resolved_pathogenic = 0
    resolved_benign = 0
    unresolved = 0
    excluded = 0

    for identity, _t0_rec in t0_vus.items():
        t1_rec = t1_data.get(identity)
        if t1_rec is None:
            excluded += 1
            flow.excluded_no_t1_record += 1
            continue

        if t1_rec["stars"] < min_review_stars:
            unresolved += 1
            flow.t1_unresolved += 1
            continue

        flow.t1_definitive_meets_star_gate += 1
        t1_clinSig = t1_rec["clinsig"]

        if t1_clinSig in PATH_SIGS:
            resolved_pathogenic += 1
            flow.t1_pathogenic += 1
        elif t1_clinSig in BENIGN_SIGS:
            resolved_benign += 1
            flow.t1_benign += 1
        else:
            unresolved += 1
            flow.t1_unresolved += 1

    flow.t1_resolved_from_t0_vus = len(t0_vus)

    return {
        "n_total": len(t0_vus),
        "n_resolved_pathogenic": resolved_pathogenic,
        "n_resolved_benign": resolved_benign,
        "n_unresolved": unresolved,
        "n_excluded": excluded,
        "class_counts": {
            "resolved_pathogenic": resolved_pathogenic,
            "resolved_benign": resolved_benign,
            "unresolved": unresolved,
            "excluded": excluded,
        },
        "flow": {
            "total_t0_records": flow.total_t0_records,
            "t0_germline_snv": flow.t0_germline_snv,
            "t0_grch38": flow.t0_grch38,
            "t0_vus_at_t0": flow.t0_vus_at_t0,
            "t0_vus_meets_star_gate": flow.t0_vus_meets_star_gate,
            "t0_unique_variants": flow.t0_unique_variants,
            "t1_definitive_meets_star_gate": flow.t1_definitive_meets_star_gate,
            "t1_resolved_from_t0_vus": flow.t1_resolved_from_t0_vus,
            "t1_pathogenic": flow.t1_pathogenic,
            "t1_benign": flow.t1_benign,
            "t1_unresolved": flow.t1_unresolved,
            "excluded_no_t1_record": flow.excluded_no_t1_record,
            "t0_release_date": t0_release_date.isoformat() if t0_release_date else None,
            "t1_release_date": t1_release_date.isoformat() if t1_release_date else None,
        },
    }

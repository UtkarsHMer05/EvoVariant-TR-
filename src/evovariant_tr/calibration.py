"""Calibration cohort construction for EvoVariant-TR (Milestone 38).

The calibration cohort consists of variants that are definitively classified
(at least 2 review stars) at t0 (Pathogenic/Likely_pathogenic or
Benign/Likely_benign). These serve as a known-outcome control set for
evaluating the temporal cohort's VUS-resolution predictions.
"""

from __future__ import annotations

import gzip
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

from evovariant_tr.clinvar_parser import parse_header
from evovariant_tr.cohort_fast import CLINSIG_MAP, REVIEW_STARS, SNV_TYPES

MIN_REVIEW_STARS = 2

PATH_SIGS = frozenset({"PATH", "LPATH", "PPATH"})
BENIGN_SIGS = frozenset({"BENIGN", "LBENIGN", "PBENIGN"})


class CalibrationOutcome(StrEnum):
    """Outcome for calibration variants."""

    STABLE = "stable"
    CHANGED_TO_PATHOGENIC = "changed_to_pathogenic"
    CHANGED_TO_BENIGN = "changed_to_benign"
    CHANGED_TO_VUS = "changed_to_vus"
    EXCLUDED = "excluded"


@dataclass
class CalibrationVariant:
    """A single variant in the calibration cohort."""

    chrom: str
    start: int
    ref: str
    alt: str
    t0_clinical_significance: str
    t0_review_status: str
    t0_review_stars: int
    t1_clinical_significance: str | None
    t1_review_status: str | None
    t1_review_stars: int | None
    outcome: CalibrationOutcome
    gene_symbol: str | None = None
    allele_id_t0: int | None = None
    allele_id_t1: int | None = None


@dataclass
class CalibrationCohort:
    """The complete calibration cohort with flow counts."""

    variants: list[CalibrationVariant] = field(default_factory=list)
    total_t0_records: int = 0
    t0_germline_snv: int = 0
    t0_grch38: int = 0
    t0_definitive: int = 0
    t1_definitive: int = 0
    stable: int = 0
    changed: int = 0
    excluded_no_t1: int = 0
    t0_release_date: date | None = None
    t1_release_date: date | None = None

    @property
    def n_total(self) -> int:
        return len(self.variants)

    @property
    def n_stable(self) -> int:
        return sum(1 for v in self.variants if v.outcome == CalibrationOutcome.STABLE)

    def class_counts(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for v in self.variants:
            counts[v.outcome.value] += 1
        return dict(counts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_total": self.n_total,
            "total_t0_records": self.total_t0_records,
            "t0_germline_snv": self.t0_germline_snv,
            "t0_grch38": self.t0_grch38,
            "t0_definitive": self.t0_definitive,
            "t1_definitive": self.t1_definitive,
            "n_stable": self.n_stable,
            "n_changed": self.changed,
            "n_excluded_no_t1": self.excluded_no_t1,
            "class_counts": self.class_counts(),
            "t0_release_date": self.t0_release_date.isoformat() if self.t0_release_date else None,
            "t1_release_date": self.t1_release_date.isoformat() if self.t1_release_date else None,
        }


def _load_definitive_snapshot(
    path: str | Path,
    min_stars: int = MIN_REVIEW_STARS,
) -> tuple[dict[tuple[str, int, str, str], dict[str, Any]], dict[str, int]]:
    """Load a snapshot, collecting only definitive (pathogenic/benign) germline SNVs.

    Returns (records_dict, counts).
    """
    target = Path(path)
    by_identity: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    counts = {"total": 0, "germline_snv": 0, "grch38": 0}

    with gzip.open(target, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            return by_identity, counts
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
            if assembly == "GRCh38":
                counts["grch38"] += 1

            clinsig_raw = parts[col["ClinicalSignificance"]]
            clinsig = CLINSIG_MAP.get(clinsig_raw)

            if clinsig not in PATH_SIGS and clinsig not in BENIGN_SIGS:
                continue

            review_status = parts[col["ReviewStatus"]]
            stars = REVIEW_STARS.get(review_status.strip(), 0)
            if stars < min_stars:
                continue

            chrom = parts[col["Chromosome"]]
            start = int(parts[col["Start"]])
            ref = parts[col["ReferenceAllele"]]
            alt = parts[col["AlternateAllele"]]
            identity = (chrom, start, ref, alt)

            gene_idx = col.get("GeneSymbol")
            gene = parts[gene_idx] if gene_idx is not None else None

            rec = {
                "allele_id": int(parts[col["AlleleID"]]),
                "stars": stars,
                "gene": gene if gene and gene != "-" else None,
                "raw_clinsig": clinsig_raw,
                "review_status": review_status,
                "clinsig": clinsig,
            }

            existing = by_identity.get(identity)
            if existing is None or rec["stars"] > existing["stars"]:
                by_identity[identity] = rec

    return by_identity, counts


def _load_all_snapshot(
    path: str | Path,
) -> dict[tuple[str, int, str, str], dict[str, Any]]:
    """Load t1 snapshot, collecting ALL germline SNVs (for calibration join).

    Returns (records_dict).
    """
    target = Path(path)
    by_identity: dict[tuple[str, int, str, str], dict[str, Any]] = {}

    with gzip.open(target, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            return by_identity

        header = parse_header(header_line)
        col = {name: header.idx(name) for name in header.columns}

        for line in handle:
            fields = line.rstrip("\n\r")
            if not fields.strip():
                continue
            parts = fields.split("\t")
            if len(parts) < len(col):
                continue

            vtype = parts[col["Type"]]
            origin = parts[col["OriginSimple"]]
            is_snv = vtype in SNV_TYPES
            is_germline = "germline" in origin.lower()

            if not is_snv or not is_germline:
                continue

            chrom = parts[col["Chromosome"]]
            start = int(parts[col["Start"]])
            ref = parts[col["ReferenceAllele"]]
            alt = parts[col["AlternateAllele"]]
            identity = (chrom, start, ref, alt)

            clinsig_raw = parts[col["ClinicalSignificance"]]
            clinsig = CLINSIG_MAP.get(clinsig_raw, "OTHER")
            review_status = parts[col["ReviewStatus"]]
            stars = REVIEW_STARS.get(review_status.strip(), 0)

            gene_idx = col.get("GeneSymbol")
            gene = parts[gene_idx] if gene_idx is not None else None

            rec = {
                "allele_id": int(parts[col["AlleleID"]]),
                "stars": stars,
                "gene": gene if gene and gene != "-" else None,
                "raw_clinsig": clinsig_raw,
                "review_status": review_status,
                "clinsig": clinsig,
            }

            existing = by_identity.get(identity)
            if existing is None or rec["stars"] > existing["stars"]:
                by_identity[identity] = rec

    return by_identity


def build_calibration_cohort(
    t0_path: str | Path,
    t1_path: str | Path,
    t0_release_date: date | None = None,
    t1_release_date: date | None = None,
    min_review_stars: int = MIN_REVIEW_STARS,
) -> CalibrationCohort:
    """Build the disjoint definitive-at-t0 calibration cohort.

    The calibration cohort is disjoint from the temporal VUS cohort because
    it only includes variants that are definitively classified at t0
    (not VUS).
    """
    t0_data, t0_counts = _load_definitive_snapshot(t0_path, min_review_stars)
    t1_data = _load_all_snapshot(t1_path)

    cohort = CalibrationCohort(
        total_t0_records=t0_counts["total"],
        t0_germline_snv=t0_counts["germline_snv"],
        t0_grch38=t0_counts["grch38"],
        t0_definitive=len(t0_data),
        t1_definitive=len(t1_data),
        t0_release_date=t0_release_date,
        t1_release_date=t1_release_date,
    )

    for identity, t0_rec in t0_data.items():
        t1_rec = t1_data.get(identity)
        chrom, start, ref, alt = identity

        if t1_rec is None:
            cohort.excluded_no_t1 += 1
            cohort.variants.append(
                CalibrationVariant(
                    chrom=chrom, start=start, ref=ref, alt=alt,
                    t0_clinical_significance=t0_rec["raw_clinsig"],
                    t0_review_status=t0_rec["review_status"],
                    t0_review_stars=t0_rec["stars"],
                    t1_clinical_significance=None,
                    t1_review_status=None,
                    t1_review_stars=None,
                    outcome=CalibrationOutcome.EXCLUDED,
                    gene_symbol=t0_rec.get("gene"),
                    allele_id_t0=t0_rec["allele_id"],
                    allele_id_t1=None,
                )
            )
            continue

        t0_sig = t0_rec["clinsig"]
        t1_sig = t1_rec["clinsig"]

        if t0_sig == t1_sig:
            outcome = CalibrationOutcome.STABLE
            cohort.stable += 1
        elif t1_sig in PATH_SIGS:
            outcome = CalibrationOutcome.CHANGED_TO_PATHOGENIC
            cohort.changed += 1
        elif t1_sig in BENIGN_SIGS:
            outcome = CalibrationOutcome.CHANGED_TO_BENIGN
            cohort.changed += 1
        else:
            outcome = CalibrationOutcome.CHANGED_TO_VUS
            cohort.changed += 1

        cohort.variants.append(
            CalibrationVariant(
                chrom=chrom, start=start, ref=ref, alt=alt,
                t0_clinical_significance=t0_rec["raw_clinsig"],
                t0_review_status=t0_rec["review_status"],
                t0_review_stars=t0_rec["stars"],
                t1_clinical_significance=t1_rec["raw_clinsig"],
                t1_review_status=t1_rec["review_status"],
                t1_review_stars=t1_rec["stars"],
                outcome=outcome,
                gene_symbol=t1_rec.get("gene"),
                allele_id_t0=t0_rec["allele_id"],
                allele_id_t1=t1_rec["allele_id"],
            )
        )

    return cohort


def check_disjoint(
    t0_path: str | Path,
    min_review_stars: int = MIN_REVIEW_STARS,
) -> dict[str, Any]:
    """Check that VUS and definitive cohorts are disjoint at t0.

    Uses a unified deduplication: first loads ALL germline SNVs at t0,
    deduplicates by identity keeping highest-star record, then splits
    into VUS vs definitive groups.

    Returns a dict with overlap counts.
    """

    target = Path(t0_path)
    vus_ids: set[tuple[str, int, str, str]] = set()
    def_ids: set[tuple[str, int, str, str]] = set()

    with gzip.open(target, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            return {
                "vus_count": 0,
                "definitive_count": 0,
                "overlap_count": 0,
                "is_disjoint": True,
            }

        header = parse_header(header_line)
        col = {name: header.idx(name) for name in header.columns}

        # Unified deduplication: keep best record per identity
        best: dict[tuple[str, int, str, str], dict[str, Any]] = {}

        for line in handle:
            fields = line.rstrip("\n\r")
            if not fields.strip():
                continue
            parts = fields.split("\t")
            if len(parts) < len(col):
                continue

            vtype = parts[col["Type"]]
            origin = parts[col["OriginSimple"]]
            if vtype not in SNV_TYPES or "germline" not in origin.lower():
                continue

            review_status = parts[col["ReviewStatus"]]
            stars = REVIEW_STARS.get(review_status.strip(), 0)
            if stars < min_review_stars:
                continue

            clinsig_raw = parts[col["ClinicalSignificance"]]
            clinsig = CLINSIG_MAP.get(clinsig_raw, "OTHER")
            chrom = parts[col["Chromosome"]]
            start = int(parts[col["Start"]])
            ref = parts[col["ReferenceAllele"]]
            alt = parts[col["AlternateAllele"]]
            identity = (chrom, start, ref, alt)

            existing = best.get(identity)
            if existing is None or stars > existing["stars"]:
                best[identity] = {
                    "stars": stars,
                    "clinsig": clinsig,
                    "raw_clinsig": clinsig_raw,
                }

        # Split into VUS and definitive based on best record
        for identity, rec in best.items():
            if rec["clinsig"] == "UNCERTAIN":
                vus_ids.add(identity)
            elif rec["clinsig"] in PATH_SIGS or rec["clinsig"] in BENIGN_SIGS:
                def_ids.add(identity)

    overlap = vus_ids & def_ids
    return {
        "vus_count": len(vus_ids),
        "definitive_count": len(def_ids),
        "overlap_count": len(overlap),
        "is_disjoint": len(overlap) == 0,
    }


def gene_group_splits(
    t0_path: str | Path,
    min_review_stars: int = MIN_REVIEW_STARS,
) -> dict[str, Any]:
    """Define gene-group splits for calibration analysis.

    Groups calibration variants by gene symbol and reports:
    - Number of genes with at least 1 definitive variant at t0
    - Distribution of variant counts per gene
    - Genes with the most stability changes

    Returns a dict with gene-group statistics.
    """
    from collections import Counter, defaultdict

    target = Path(t0_path)
    gene_variants: dict[str, list[str]] = defaultdict(list)

    with gzip.open(target, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            return {"genes": {}, "n_genes": 0}

        header = parse_header(header_line)
        col = {name: header.idx(name) for name in header.columns}

        for line in handle:
            fields = line.rstrip("\n\r")
            if not fields.strip():
                continue
            parts = fields.split("\t")
            if len(parts) < len(col):
                continue

            vtype = parts[col["Type"]]
            origin = parts[col["OriginSimple"]]
            if vtype not in SNV_TYPES or "germline" not in origin.lower():
                continue

            review_status = parts[col["ReviewStatus"]]
            stars = REVIEW_STARS.get(review_status.strip(), 0)
            if stars < min_review_stars:
                continue

            clinsig_raw = parts[col["ClinicalSignificance"]]
            clinsig = CLINSIG_MAP.get(clinsig_raw, "OTHER")
            if clinsig not in PATH_SIGS and clinsig not in BENIGN_SIGS:
                continue

            gene_idx = col.get("GeneSymbol")
            gene = parts[gene_idx] if gene_idx is not None else None
            if not gene or gene == "-":
                gene = "UNKNOWN"

            gene_variants[gene].append(clinsig)

    gene_stats = {}
    for gene, sigs in gene_variants.items():
        sig_counts = Counter(sigs)
        path_keys = frozenset({"PATH", "LPATH", "PPATH"})
        benign_keys = frozenset({"BENIGN", "LBENIGN", "PBENIGN"})
        p = sum(sig_counts.get(k, 0) for k in path_keys)
        b = sum(sig_counts.get(k, 0) for k in benign_keys)
        gene_stats[gene] = {
            "total_variants": len(sigs),
            "pathogenic": p,
            "benign": b,
        }

    return {
        "n_genes": len(gene_variants),
        "genes": gene_stats,
        "total_definitive_variants": sum(len(v) for v in gene_variants.values()),
    }

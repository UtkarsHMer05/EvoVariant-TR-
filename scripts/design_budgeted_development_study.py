#!/usr/bin/env python3
"""Audit the bounded prefix and design the formal budgeted ML study.

This is a local, no-spend control-plane command.  It does not invoke Modal,
load model predictions for subset selection, read locked-test labels, or
rewrite the authoritative development population.  It produces immutable
planning manifests and QC/cost artifacts for ``ML-DEV-BUDGETED-001``.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evovariant_tr.clinvar_parser import iter_variant_summary  # noqa: E402

STUDY_ID = "ML-DEV-BUDGETED-001"
DESIGN_DATE = "2026-09-21"
SAMPLING_SEED = f"{STUDY_ID}|{DESIGN_DATE}|sha256-v1"
TARGET_TOTAL = 4_000
MAX_TOTAL = 5_000

DEVELOPMENT_MANIFEST = REPO_ROOT / "data/derived/ml_extension/phase3/split_manifest.json"
LOCKED_MANIFEST = REPO_ROOT / (
    "research/ml_extension/splits/authoritative_locked_test_manifest.json"
)
PHASE6_PREDICTIONS = REPO_ROOT / (
    "research/runs/phase6_development_evo2_20260921/predictions.jsonl"
)
T0_ARCHIVE = REPO_ROOT / "data/raw/clinvar/variant_summary_2025-01.txt.gz"
PHASE6_ARTIFACT = REPO_ROOT / "artifacts/phase6/phase6_development_evo2_20260921.json"
PHASE6A_EVO2_ARTIFACT = REPO_ROOT / ("artifacts/phase6a/phase6a_evo2_throughput_20260921.json")
PHASE6A_REP_ARTIFACT = REPO_ROOT / (
    "artifacts/phase6a/phase6a_representation_throughput_20260921.json"
)
PHASE10_DEFERRAL = REPO_ROOT / ("artifacts/modal/phase10_adaptation_deferral_20260921.json")
COST_LEDGER = REPO_ROOT / "research/runs/cost_ledger.jsonl"
OUTPUT_DIR = REPO_ROOT / "research/ml_extension/splits/formal_budgeted_20260921"
SOURCE_METADATA_CACHE = OUTPUT_DIR / "source_metadata_aggregate.json"
PROTOCOL_HASHES = REPO_ROOT / "research/ml_extension/protocol_hashes.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def write_stable_json(path: Path, payload: Any) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if path.is_file():
        if path.read_text(encoding="utf-8") != encoded:
            try:
                path.resolve().relative_to(OUTPUT_DIR.resolve())
            except ValueError as exc:
                raise RuntimeError(
                    f"refusing to replace different planning artifact: {path}"
                ) from exc
            path.write_text(encoded, encoding="utf-8")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def current_ml_protocol_hash() -> str:
    document = read_json(PROTOCOL_HASHES)
    files = document.get("files") if isinstance(document, dict) else None
    value = files.get("research/ml_extension/protocol.yaml") if isinstance(files, dict) else None
    if not isinstance(value, str) or len(value) != 64:
        raise RuntimeError("protocol_hashes.json does not contain the current ML protocol hash")
    return value


def require_files(*paths: Path) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise RuntimeError("required no-spend input is missing: " + ", ".join(missing))


def normalize_key(chromosome: str, position: int, reference: str, alternate: str) -> str:
    chrom = chromosome.removeprefix("chr")
    return f"GRCh38:{chrom}:{position}:{reference}>{alternate}"


def load_development_records() -> tuple[list[dict[str, Any]], str]:
    document = read_json(DEVELOPMENT_MANIFEST)
    records = document.get("records")
    if not isinstance(records, list) or len(records) != 239_992:
        raise RuntimeError("frozen development manifest must contain 239,992 records")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in records:
        if not isinstance(raw, dict):
            raise RuntimeError("development manifest contains a non-object record")
        row = dict(raw)
        identity = str(row.get("normalized_variant_id", ""))
        if not identity or identity in seen:
            raise RuntimeError(f"development manifest has missing/duplicate ID: {identity!r}")
        if row.get("split") not in {"TRAIN", "VALIDATION"}:
            raise RuntimeError(f"development manifest has non-development split: {identity}")
        if row.get("label") not in {0, 1}:
            raise RuntimeError(f"development manifest has invalid label: {identity}")
        required = {
            "assembly",
            "chromosome",
            "position_1based",
            "reference",
            "alternate",
            "gene_symbol",
            "source_release",
        }
        missing = sorted(field for field in required if field not in row)
        if missing:
            raise RuntimeError(f"development record {identity} misses {missing}")
        if row.get("assembly") != "GRCh38":
            raise RuntimeError(f"development record {identity} is not GRCh38")
        seen.add(identity)
        normalized.append(row)

    locked = read_json(LOCKED_MANIFEST)
    locked_ids = {
        str(row["normalized_variant_id"])
        for row in locked.get("records", [])
        if isinstance(row, dict) and "normalized_variant_id" in row
    }
    overlap = seen & locked_ids
    if overlap:
        raise RuntimeError(f"development manifest overlaps LOCKED_TEST: {len(overlap)} IDs")
    return normalized, sha256_file(DEVELOPMENT_MANIFEST)


def load_prefix_ids() -> set[str]:
    rows: list[dict[str, Any]] = []
    with PHASE6_PREDICTIONS.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise RuntimeError(f"Phase 6 prediction line {line_number} is not an object")
            rows.append(value)
    ids = [str(row.get("normalized_variant_id", "")) for row in rows]
    if len(ids) != 2_848 or len(set(ids)) != len(ids) or "" in ids:
        raise RuntimeError(
            "the existing Phase 6 prediction artifact is not exactly 2,848 unique rows"
        )
    return set(ids)


def _hash_rank(identity: str) -> str:
    return hashlib.sha256(f"{identity}|{SAMPLING_SEED}".encode()).hexdigest()


def _old_hash_rank(identity: str) -> str:
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def allocate_strata(records: list[dict[str, Any]], target: int) -> dict[tuple[str, int], int]:
    counts = Counter((str(row["split"]), int(row["label"])) for row in records)
    if target > len(records) or target > MAX_TOTAL:
        raise RuntimeError(f"requested target {target} exceeds the permitted population/budget")
    exact = {key: value * target / len(records) for key, value in counts.items()}
    allocation = {key: math.floor(value) for key, value in exact.items()}
    remaining = target - sum(allocation.values())
    ranked_remainders = sorted(
        counts,
        key=lambda key: (-(exact[key] - allocation[key]), key[0], key[1]),
    )
    for key in ranked_remainders[:remaining]:
        allocation[key] += 1
    if sum(allocation.values()) != target:
        raise AssertionError("largest-remainder allocation did not reach the target")
    return allocation


def select_formal_records(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, int], int]]:
    allocation = allocate_strata(records, TARGET_TOTAL)
    by_stratum: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in records:
        key = (str(row["split"]), int(row["label"]))
        by_stratum.setdefault(key, []).append(row)

    selected: list[dict[str, Any]] = []
    for key, rows in sorted(by_stratum.items()):
        ranked = sorted(
            rows,
            key=lambda row: (
                _hash_rank(str(row["normalized_variant_id"])),
                str(row["normalized_variant_id"]),
            ),
        )
        for row in ranked[: allocation[key]]:
            selected_row = dict(row)
            selected_row["sampling_hash"] = _hash_rank(str(row["normalized_variant_id"]))
            selected_row["sampling_stratum"] = f"{key[0]}|label={key[1]}"
            selected.append(selected_row)

    selected.sort(
        key=lambda row: (
            0 if row["split"] == "TRAIN" else 1,
            int(row["label"]),
            str(row["sampling_hash"]),
            str(row["normalized_variant_id"]),
        )
    )
    ids = [str(row["normalized_variant_id"]) for row in selected]
    if len(selected) != TARGET_TOTAL or len(set(ids)) != TARGET_TOTAL:
        raise RuntimeError("formal selection did not produce the exact unique target size")
    return selected, allocation


def numeric_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = sorted(float(row[field]) for row in rows)
    if not values:
        return {"available": False, "reason": "no values"}

    def quantile(fraction: float) -> float:
        index = fraction * (len(values) - 1)
        lower = math.floor(index)
        upper = math.ceil(index)
        if lower == upper:
            return values[lower]
        return values[lower] + (values[upper] - values[lower]) * (index - lower)

    return {
        "available": True,
        "count": len(values),
        "min": values[0],
        "max": values[-1],
        "mean": mean(values),
        "p01": quantile(0.01),
        "p25": quantile(0.25),
        "p50": quantile(0.50),
        "p75": quantile(0.75),
        "p99": quantile(0.99),
    }


def distribution(
    population: list[dict[str, Any]],
    subset: list[dict[str, Any]],
    value: Callable[[dict[str, Any]], str],
) -> dict[str, Any]:
    population_counts = Counter(value(row) for row in population)
    subset_counts = Counter(value(row) for row in subset)
    population_total = len(population)
    subset_total = len(subset)
    categories: dict[str, dict[str, Any]] = {}
    for category in sorted(set(population_counts) | set(subset_counts)):
        population_count = population_counts.get(category, 0)
        subset_count = subset_counts.get(category, 0)
        population_fraction = population_count / population_total if population_total else 0.0
        subset_fraction = subset_count / subset_total if subset_total else 0.0
        categories[category] = {
            "population_count": population_count,
            "subset_count": subset_count,
            "population_fraction": population_fraction,
            "subset_fraction": subset_fraction,
            "absolute_fraction_difference": abs(subset_fraction - population_fraction),
        }
    total_variation = 0.5 * sum(
        entry["absolute_fraction_difference"] for entry in categories.values()
    )
    max_difference = max(
        (entry["absolute_fraction_difference"] for entry in categories.values()),
        default=0.0,
    )
    top_population = sorted(
        categories.items(), key=lambda item: (-item[1]["population_count"], item[0])
    )[:20]
    top_subset = sorted(categories.items(), key=lambda item: (-item[1]["subset_count"], item[0]))[
        :20
    ]
    return {
        "population_total": population_total,
        "subset_total": subset_total,
        "category_count": len(categories),
        "total_variation_distance": total_variation,
        "max_absolute_fraction_difference": max_difference,
        "top_population": [
            {"category": category, **payload} for category, payload in top_population
        ],
        "top_subset": [{"category": category, **payload} for category, payload in top_subset],
        "categories": categories,
    }


def raw_metadata_index(target_ids: set[str]) -> dict[str, dict[str, Any]]:
    """Aggregate source metadata without retaining the raw archive rows."""
    if SOURCE_METADATA_CACHE.is_file():
        cached = read_json(SOURCE_METADATA_CACHE)
        if (
            isinstance(cached, dict)
            and isinstance(cached.get("__audit__"), dict)
            and cached["__audit__"].get("target_variant_count") == len(target_ids)
            and cached["__audit__"].get("matched_variant_count") == len(cached) - 1
        ):
            return cached
    index: dict[str, dict[str, Any]] = {}
    matched_rows = 0
    for record in iter_variant_summary(T0_ARCHIVE, assembly="GRCh38"):
        identity = normalize_key(
            record.chromosome,
            record.start,
            record.reference_allele,
            record.alternate_allele,
        )
        if identity not in target_ids:
            continue
        matched_rows += 1
        payload = index.setdefault(
            identity,
            {
                "source_row_count": 0,
                "review_status_counts": Counter(),
                "review_stars_max": 0,
                "review_status_at_max_stars": set(),
                "last_evaluated_max": None,
                "variant_type_counts": Counter(),
            },
        )
        payload["source_row_count"] += 1
        status = record.review_status or "UNSPECIFIED"
        payload["review_status_counts"][status] += 1
        if record.review_stars > payload["review_stars_max"]:
            payload["review_stars_max"] = record.review_stars
            payload["review_status_at_max_stars"] = {status}
        elif record.review_stars == payload["review_stars_max"]:
            payload["review_status_at_max_stars"].add(status)
        if record.last_evaluated is not None:
            current = payload["last_evaluated_max"]
            value = record.last_evaluated.isoformat()
            if current is None or value > current:
                payload["last_evaluated_max"] = value
        payload["variant_type_counts"][record.variant_type or "UNSPECIFIED"] += 1
    for payload in index.values():
        payload["review_status_counts"] = dict(sorted(payload["review_status_counts"].items()))
        payload["review_status_at_max_stars"] = sorted(payload["review_status_at_max_stars"])
        payload["variant_type_counts"] = dict(sorted(payload["variant_type_counts"].items()))
    index["__audit__"] = {
        "matched_source_rows": matched_rows,
        "matched_variant_count": len(index),
        "target_variant_count": len(target_ids),
        "unmatched_variant_count": len(target_ids - (set(index) - {"__audit__"})),
        "unmatched_variant_examples": sorted(target_ids - (set(index) - {"__audit__"}))[:20],
        "archive_scan_note": (
            "iter_variant_summary filters the gzipped t0 archive to GRCh38; the counter "
            "retains only development IDs"
        ),
    }
    return index


def source_metadata_value(metadata: dict[str, dict[str, Any]], identity: str, field: str) -> str:
    payload = metadata.get(identity)
    if payload is None:
        return "UNMATCHED_SOURCE_METADATA"
    if field == "review_status":
        statuses = payload["review_status_at_max_stars"]
        return "|".join(statuses) if statuses else "UNSPECIFIED"
    if field == "last_evaluated":
        return str(payload["last_evaluated_max"] or "MISSING")
    if field == "variant_type":
        values = payload["variant_type_counts"]
        return sorted(values, key=lambda item: (-values[item], item))[0]
    raise KeyError(field)


def prefix_audit(
    population: list[dict[str, Any]], prefix_ids: set[str], metadata: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    population_by_id = {str(row["normalized_variant_id"]): row for row in population}
    if not prefix_ids <= set(population_by_id):
        raise RuntimeError(
            "existing Phase 6 prefix contains IDs outside the frozen development population"
        )
    hash_ranked = sorted(
        population, key=lambda row: _old_hash_rank(str(row["normalized_variant_id"]))
    )
    expected_prefix = {str(row["normalized_variant_id"]) for row in hash_ranked[: len(prefix_ids)]}
    manifest_first = {str(row["normalized_variant_id"]) for row in population[: len(prefix_ids)]}
    prefix_rows = [population_by_id[identity] for identity in sorted(prefix_ids)]
    distributions: dict[str, Any] = {
        "class": distribution(
            population,
            prefix_rows,
            lambda row: "POSITIVE" if int(row["label"]) else "NEGATIVE",
        ),
        "split": distribution(population, prefix_rows, lambda row: str(row["split"])),
        "gene": distribution(
            population, prefix_rows, lambda row: str(row["gene_symbol"] or "MISSING")
        ),
        "chromosome": distribution(population, prefix_rows, lambda row: str(row["chromosome"])),
        "source_release": distribution(
            population, prefix_rows, lambda row: str(row["source_release"])
        ),
        "variant_type": distribution(
            population,
            prefix_rows,
            lambda row: source_metadata_value(
                metadata, str(row["normalized_variant_id"]), "variant_type"
            ),
        ),
        "review_status": distribution(
            population,
            prefix_rows,
            lambda row: source_metadata_value(
                metadata, str(row["normalized_variant_id"]), "review_status"
            ),
        ),
        "last_evaluated": distribution(
            population,
            prefix_rows,
            lambda row: source_metadata_value(
                metadata, str(row["normalized_variant_id"]), "last_evaluated"
            ),
        ),
    }
    positions = {
        "population": numeric_summary(population, "position_1based"),
        "prefix": numeric_summary(prefix_rows, "position_1based"),
    }
    hash_rank_by_id = {
        str(row["normalized_variant_id"]): rank for rank, row in enumerate(hash_ranked)
    }
    prefix_ranks = sorted(hash_rank_by_id[identity] for identity in prefix_ids)
    return {
        "selection_reconstruction": {
            "prefix_size": len(prefix_ids),
            "matches_old_sha256_normalized_id_prefix": prefix_ids == expected_prefix,
            "matches_frozen_manifest_row_prefix": prefix_ids == manifest_first,
            "old_rule": "ascending SHA-256(normalized_variant_id), then budget stop",
            "old_rule_uses_model_predictions": False,
            "source_row_order_used": False,
            "frozen_manifest_row_order_used": False,
            "train_validation_ordering_used": False,
            "class_grouping_used": False,
            "selection_basis": "immutable normalized IDs and a paid-compute budget stop",
            "prefix_rank_min": min(prefix_ranks),
            "prefix_rank_max": max(prefix_ranks),
            "prefix_rank_mean": mean(prefix_ranks),
        },
        "distributions": distributions,
        "position": positions,
        "metadata_availability": {
            "class": "available in frozen development manifest",
            "split": "available in frozen development manifest",
            "gene": "available in frozen development manifest",
            "chromosome": "available in frozen development manifest",
            "position": "available in frozen development manifest",
            "source_release": "available in frozen development manifest",
            "review_status": (
                "aggregated from the archived t0 variant_summary source by normalized ID"
            ),
            "last_evaluated": (
                "aggregated from the archived t0 variant_summary source; "
                "this is not a submission date"
            ),
            "submission_date": (
                "not available in the frozen manifest or the archived variant_summary schema"
            ),
            "consequence_type": (
                "not available in the frozen manifest or the archived variant_summary schema"
            ),
        },
        "representativeness_conclusion": {
            "status": "NOT_ESTABLISHED",
            "answer": "The 2,848-row prefix is not promoted as representative.",
            "reason": (
                "It is an ascending hash-ranked prefix stopped by a paid-compute safety reserve, "
                "not a predeclared stratified sample. Metadata similarity is descriptive only and "
                "cannot establish representation of the full development population."
            ),
            "required_follow_on": (
                "Use the separately frozen ML-DEV-BUDGETED-001 subset for formal "
                "development experiments."
            ),
        },
        "archive_metadata_scan": metadata["__audit__"],
    }


def formal_qc(
    population: list[dict[str, Any]],
    formal_rows: list[dict[str, Any]],
    locked_ids: set[str],
    prefix_ids: set[str],
    metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    population_by_id = {str(row["normalized_variant_id"]): row for row in population}
    formal_ids = {str(row["normalized_variant_id"]) for row in formal_rows}
    train_ids = {
        str(row["normalized_variant_id"]) for row in formal_rows if row["split"] == "TRAIN"
    }
    validation_ids = {
        str(row["normalized_variant_id"]) for row in formal_rows if row["split"] == "VALIDATION"
    }
    gene_train = {str(row["gene_symbol"]) for row in formal_rows if row["split"] == "TRAIN"}
    gene_validation = {
        str(row["gene_symbol"]) for row in formal_rows if row["split"] == "VALIDATION"
    }
    distributions = {
        "class": distribution(
            population,
            formal_rows,
            lambda row: "POSITIVE" if int(row["label"]) else "NEGATIVE",
        ),
        "split": distribution(population, formal_rows, lambda row: str(row["split"])),
        "gene": distribution(
            population, formal_rows, lambda row: str(row["gene_symbol"] or "MISSING")
        ),
        "chromosome": distribution(population, formal_rows, lambda row: str(row["chromosome"])),
        "source_release": distribution(
            population, formal_rows, lambda row: str(row["source_release"])
        ),
        "variant_type": distribution(
            population,
            formal_rows,
            lambda row: source_metadata_value(
                metadata, str(row["normalized_variant_id"]), "variant_type"
            ),
        ),
        "review_status": distribution(
            population,
            formal_rows,
            lambda row: source_metadata_value(
                metadata, str(row["normalized_variant_id"]), "review_status"
            ),
        ),
        "last_evaluated": distribution(
            population,
            formal_rows,
            lambda row: source_metadata_value(
                metadata, str(row["normalized_variant_id"]), "last_evaluated"
            ),
        ),
    }
    return {
        "study_id": STUDY_ID,
        "target_total": TARGET_TOTAL,
        "actual_total": len(formal_rows),
        "population_counts": {
            "total": len(population),
            "TRAIN": sum(row["split"] == "TRAIN" for row in population),
            "VALIDATION": sum(row["split"] == "VALIDATION" for row in population),
            "NEGATIVE": sum(int(row["label"]) == 0 for row in population),
            "POSITIVE": sum(int(row["label"]) == 1 for row in population),
        },
        "subset_counts": {
            "total": len(formal_rows),
            "TRAIN": len(train_ids),
            "VALIDATION": len(validation_ids),
            "NEGATIVE": sum(int(row["label"]) == 0 for row in formal_rows),
            "POSITIVE": sum(int(row["label"]) == 1 for row in formal_rows),
            "unique_genes": len({str(row["gene_symbol"]) for row in formal_rows}),
        },
        "invariants": {
            "all_ids_in_authoritative_population": formal_ids <= set(population_by_id),
            "normalized_id_unique": len(formal_ids) == len(formal_rows),
            "locked_test_overlap": len(formal_ids & locked_ids) == 0,
            "train_validation_id_overlap": len(train_ids & validation_ids) == 0,
            "train_validation_gene_overlap": len(gene_train & gene_validation) == 0,
            "all_train_rows_remain_train": all(
                row["split"] == "TRAIN" for row in formal_rows if row["split"] == "TRAIN"
            ),
            "all_validation_rows_remain_validation": all(
                row["split"] == "VALIDATION" for row in formal_rows if row["split"] == "VALIDATION"
            ),
            "all_rows_are_grch38": all(row["assembly"] == "GRCh38" for row in formal_rows),
            "all_rows_are_snv_contract": all(
                len(str(row["reference"])) == 1
                and len(str(row["alternate"])) == 1
                and str(row["reference"]) in "ACGT"
                and str(row["alternate"]) in "ACGT"
                for row in formal_rows
            ),
        },
        "existing_prefix_overlap": {
            "count": len(formal_ids & prefix_ids),
            "sha256": canonical_sha256(sorted(formal_ids & prefix_ids)),
        },
        "distributions": distributions,
        "position": {
            "population": numeric_summary(population, "position_1based"),
            "subset": numeric_summary(formal_rows, "position_1based"),
        },
        "formal_tracks": {
            "same_exact_manifest_for_all_tracks": True,
            "zero_shot_raw_score": ["Evo2", "CADD", "PhyloP"],
            "eligible_subset_only": ["AlphaMissense"],
            "representations": ["Evo2 raw-score features", "Nucleotide Transformer", "Caduceus"],
            "classifiers": ["Logistic Regression", "tree/boosting classifier", "MLP"],
        },
    }


def capture_billing_snapshot(previous: dict[str, Any] | None = None) -> dict[str, Any]:
    if previous is not None:
        return previous
    binary = shutil.which("modal") or str(Path(sys.executable).with_name("modal"))
    if binary is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "modal CLI not found on PATH; no billing query was attempted",
        }
    try:
        result = subprocess.run(
            [binary, "billing", "summary"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "UNAVAILABLE", "reason": f"{type(exc).__name__}: {exc}"}
    return {
        "status": "READ_ONLY_SNAPSHOT" if result.returncode == 0 else "QUERY_FAILED",
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "command": "modal billing summary",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "interpretation": (
            "workspace-level provider summary, not a per-run invoice or a compute approval"
        ),
    }


def first_pass_config(results: list[dict[str, Any]], candidate: str) -> dict[str, Any]:
    valid = [
        row
        for row in results
        if row.get("candidate") == candidate
        and row.get("status") == "PASS"
        and row.get("cold_container") is False
    ]
    if not valid:
        raise RuntimeError(f"no warm Phase6A throughput result for {candidate}")
    return min(valid, key=lambda row: float(row["seconds_per_variant"]))


def cost_estimate(
    formal_rows: list[dict[str, Any]], prefix_ids: set[str], development_hash: str
) -> dict[str, Any]:
    phase6 = read_json(PHASE6_ARTIFACT)
    evo2 = read_json(PHASE6A_EVO2_ARTIFACT)
    rep = read_json(PHASE6A_REP_ARTIFACT)
    formal_ids = {str(row["normalized_variant_id"]) for row in formal_rows}
    overlap = len(formal_ids & prefix_ids)
    new_evo2 = len(formal_rows) - overlap
    gpu_rate = float(phase6["cost"]["gpu_rate_usd_per_hour"])
    prior_count = int(phase6["dataset"]["processed_records"])
    # The phase artifact's cost field is the observed approved development
    # estimate; the seconds field below is a client-wall estimate, not an
    # invoice. Scale only the uncached formal variants.
    prior_cost = float(phase6["cost"]["cumulative_client_wall_rate_estimate_usd"])
    ledger_entries = [
        json.loads(line)
        for line in COST_LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    phase6_ledger = next(
        entry
        for entry in ledger_entries
        if entry.get("run_id") == "phase6-development-evo2-20260921"
    )
    ledger_seconds = float(phase6_ledger["estimated_seconds"])
    phase6_effective_seconds_per_variant = ledger_seconds / prior_count
    evo2_cost = new_evo2 / prior_count * prior_cost
    evo2_config = min(
        (
            row
            for row in evo2["results"]
            if row.get("status") == "PASS" and row.get("gpu_type") == "H100"
        ),
        key=lambda row: float(row["seconds_per_variant"]),
    )
    evo2a_seconds = new_evo2 * float(evo2_config["seconds_per_variant"]) + float(
        evo2_config["model_load_seconds"]
    )
    evo2a_cost = evo2a_seconds / 3600.0 * gpu_rate
    rep_results = rep["results"]
    nt = first_pass_config(rep_results, "nucleotide_transformer")
    caduceus = first_pass_config(rep_results, "caduceus")

    def representation_cost(config: dict[str, Any]) -> dict[str, float]:
        seconds = len(formal_rows) * float(config["seconds_per_variant"]) + float(
            config["model_load_seconds"]
        )
        return {"seconds": seconds, "estimated_usd": seconds / 3600.0 * gpu_rate}

    nt_cost = representation_cost(nt)
    caduceus_cost = representation_cost(caduceus)
    total_cost = evo2_cost + nt_cost["estimated_usd"] + caduceus_cost["estimated_usd"]
    excess_over_previous_cap = max(total_cost - 5.0, 0.0)
    return {
        "study_id": STUDY_ID,
        "approval_status": "NO_NEW_MODAL_AUTHORIZATION",
        "protocol_hash": current_ml_protocol_hash(),
        "formal_counts": {
            "total": len(formal_rows),
            "cached_evo2_overlap": overlap,
            "new_evo2_variants_required": new_evo2,
        },
        "inputs": {
            "development_manifest_sha256": development_hash,
            "phase6_artifact": str(PHASE6_ARTIFACT.relative_to(REPO_ROOT)),
            "phase6_artifact_sha256": sha256_file(PHASE6_ARTIFACT),
            "phase6a_evo2_artifact": str(PHASE6A_EVO2_ARTIFACT.relative_to(REPO_ROOT)),
            "phase6a_evo2_artifact_sha256": sha256_file(PHASE6A_EVO2_ARTIFACT),
            "phase6a_representation_artifact": str(PHASE6A_REP_ARTIFACT.relative_to(REPO_ROOT)),
            "phase6a_representation_artifact_sha256": sha256_file(PHASE6A_REP_ARTIFACT),
        },
        "gpu_rate_usd_per_hour": gpu_rate,
        "evo2": {
            "basis": "conservative scaling of the approved Phase 6 effective wall-rate estimate",
            "phase6_processed_records": prior_count,
            "phase6_rate_estimate_usd": prior_cost,
            "phase6_effective_seconds_per_variant": phase6_effective_seconds_per_variant,
            "new_variants": new_evo2,
            "estimated_seconds": new_evo2 * phase6_effective_seconds_per_variant,
            "estimated_usd": evo2_cost,
            "phase6a_best_warm_config": {
                "sample_variants": evo2_config["sample_variants"],
                "model_sequence_batch_size": evo2_config["model_sequence_batch_size"],
                "seconds_per_variant": evo2_config["seconds_per_variant"],
                "model_load_seconds": evo2_config["model_load_seconds"],
                "lower_bound_estimated_usd": evo2a_cost,
            },
            "interpretation": "rate-based wall-time estimate; not an invoice",
        },
        "nucleotide_transformer": {
            "config": {
                "sample_variants": nt["sample_variants"],
                "variant_batch_size": nt["variant_batch_size"],
                "seconds_per_variant": nt["seconds_per_variant"],
                "model_load_seconds": nt["model_load_seconds"],
            },
            "estimated_seconds": nt_cost["seconds"],
            "estimated_usd": nt_cost["estimated_usd"],
            "interpretation": (
                "Phase6A warm throughput plus one model load; no cache exists for the formal subset"
            ),
        },
        "caduceus": {
            "config": {
                "sample_variants": caduceus["sample_variants"],
                "variant_batch_size": caduceus["variant_batch_size"],
                "seconds_per_variant": caduceus["seconds_per_variant"],
                "model_load_seconds": caduceus["model_load_seconds"],
            },
            "estimated_seconds": caduceus_cost["seconds"],
            "estimated_usd": caduceus_cost["estimated_usd"],
            "interpretation": (
                "Phase6A warm throughput plus one model load; no cache exists for the formal subset"
            ),
        },
        "estimated_total_phase6_7_usd": total_cost,
        "expected_reserve_after_run": {
            "status": "UNAVAILABLE_UNTIL_FRESH_APPROVAL",
            "reason": (
                f"Estimated workload exceeds the previous $5.00 cap by "
                f"${excess_over_previous_cap:.6f}; the prior approval is consumed and "
                "no new budget cap was authorized by the planning instruction."
            ),
            "previous_cap_usd": 5.0,
            "estimated_excess_over_previous_cap_usd": excess_over_previous_cap,
        },
        "current_modal_billing_snapshot": capture_billing_snapshot(
            read_json(OUTPUT_DIR / "cost_estimate.json").get("current_modal_billing_snapshot")
            if (OUTPUT_DIR / "cost_estimate.json").is_file()
            else None
        ),
    }


def main() -> int:
    require_files(
        DEVELOPMENT_MANIFEST,
        LOCKED_MANIFEST,
        PHASE6_PREDICTIONS,
        T0_ARCHIVE,
        PHASE6_ARTIFACT,
        PHASE6A_EVO2_ARTIFACT,
        PHASE6A_REP_ARTIFACT,
        PHASE10_DEFERRAL,
        COST_LEDGER,
    )
    population, development_hash = load_development_records()
    prefix_ids = load_prefix_ids()
    target_ids = {str(row["normalized_variant_id"]) for row in population}
    metadata = raw_metadata_index(target_ids)
    write_stable_json(OUTPUT_DIR / SOURCE_METADATA_CACHE.name, metadata)
    audit = prefix_audit(population, prefix_ids, metadata)
    formal_rows, allocation = select_formal_records(population)
    locked_document = read_json(LOCKED_MANIFEST)
    locked_ids = {
        str(row["normalized_variant_id"])
        for row in locked_document.get("records", [])
        if isinstance(row, dict) and "normalized_variant_id" in row
    }
    qc = formal_qc(population, formal_rows, locked_ids, prefix_ids, metadata)
    if qc["invariants"]["locked_test_overlap"] is not True:
        raise RuntimeError("formal subset overlaps LOCKED_TEST")
    if qc["invariants"]["train_validation_gene_overlap"] is not True:
        raise RuntimeError("formal subset violates train/validation gene disjointness")
    if not all(bool(value) for value in qc["invariants"].values()):
        raise RuntimeError(f"formal subset invariant failed: {qc['invariants']}")

    train_rows = [row for row in formal_rows if row["split"] == "TRAIN"]
    validation_rows = [row for row in formal_rows if row["split"] == "VALIDATION"]
    common_metadata = {
        "study_id": STUDY_ID,
        "design_date": DESIGN_DATE,
        "evidence_stage": "PRELIMINARY_PLANNING",
        "source_manifest_path": str(DEVELOPMENT_MANIFEST.relative_to(REPO_ROOT)),
        "source_manifest_sha256": development_hash,
        "locked_test_manifest_path": str(LOCKED_MANIFEST.relative_to(REPO_ROOT)),
        "locked_test_manifest_sha256": sha256_file(LOCKED_MANIFEST),
        "sampling_seed": SAMPLING_SEED,
        "sampling_rule": (
            "Within each frozen split and label stratum, rank by ascending "
            "SHA256(normalized_variant_id + '|' + sampling_seed); select the frozen "
            "largest-remainder allocation. No model predictions are read for selection."
        ),
        "allocation": {
            f"{split}|label={label}": count for (split, label), count in allocation.items()
        },
        "target_total": TARGET_TOTAL,
        "maximum_allowed_total_without_new_approval": MAX_TOTAL,
        "selection_does_not_rewrite_population": True,
        "selection_does_not_read_locked_labels": True,
        "selection_does_not_use_existing_model_predictions": True,
    }

    def manifest_payload(split: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            **common_metadata,
            "manifest_id": f"{STUDY_ID.lower()}-{split.lower()}-v1",
            "split": split,
            "record_count": len(rows),
            "class_counts": {
                "negative": sum(int(row["label"]) == 0 for row in rows),
                "positive": sum(int(row["label"]) == 1 for row in rows),
            },
            "unique_gene_count": len({str(row["gene_symbol"]) for row in rows}),
            "record_set_sha256": canonical_sha256(
                [
                    {
                        key: value
                        for key, value in row.items()
                        if key not in {"sampling_hash", "sampling_stratum"}
                    }
                    for row in rows
                ]
            ),
            "records": rows,
        }

    write_stable_json(
        OUTPUT_DIR / "formal_train_manifest.json", manifest_payload("TRAIN", train_rows)
    )
    write_stable_json(
        OUTPUT_DIR / "formal_validation_manifest.json",
        manifest_payload("VALIDATION", validation_rows),
    )
    write_stable_json(
        OUTPUT_DIR / "formal_development_manifest.json",
        {
            **common_metadata,
            "manifest_id": f"{STUDY_ID.lower()}-development-v1",
            "split": "TRAIN_AND_VALIDATION",
            "record_count": len(formal_rows),
            "class_counts": {
                "negative": sum(int(row["label"]) == 0 for row in formal_rows),
                "positive": sum(int(row["label"]) == 1 for row in formal_rows),
            },
            "split_counts": {"TRAIN": len(train_rows), "VALIDATION": len(validation_rows)},
            "unique_gene_count": len({str(row["gene_symbol"]) for row in formal_rows}),
            "record_set_sha256": canonical_sha256(
                [
                    {
                        key: value
                        for key, value in row.items()
                        if key not in {"sampling_hash", "sampling_stratum"}
                    }
                    for row in formal_rows
                ]
            ),
            "records": formal_rows,
        },
    )
    write_stable_json(
        OUTPUT_DIR / "prefix_audit.json",
        {
            "study_id": STUDY_ID,
            "design_date": DESIGN_DATE,
            "development_manifest_sha256": development_hash,
            "existing_phase6_prediction_artifact": str(PHASE6_PREDICTIONS.relative_to(REPO_ROOT)),
            "existing_phase6_prediction_artifact_sha256": sha256_file(PHASE6_PREDICTIONS),
            **audit,
        },
    )
    write_stable_json(OUTPUT_DIR / SOURCE_METADATA_CACHE.name, metadata)
    write_stable_json(OUTPUT_DIR / "population_vs_subset_QC.json", qc)
    write_stable_json(
        OUTPUT_DIR / "cost_estimate.json",
        cost_estimate(formal_rows, prefix_ids, development_hash),
    )

    hashes = {
        path.name: sha256_file(path)
        for path in sorted(OUTPUT_DIR.glob("*.json"))
        if path.name != "manifest_hashes.json"
    }
    write_stable_json(
        OUTPUT_DIR / "manifest_hashes.json",
        {
            "study_id": STUDY_ID,
            "generated_at_utc": f"{DESIGN_DATE}T00:00:00Z",
            "hashes": hashes,
            "hashing": (
                "SHA-256 over exact UTF-8 JSON bytes with stable indentation and sorted keys"
            ),
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS_NO_SPEND_FORMAL_DESIGN",
                "study_id": STUDY_ID,
                "formal_total": len(formal_rows),
                "train": len(train_rows),
                "validation": len(validation_rows),
                "existing_prefix_overlap": qc["existing_prefix_overlap"]["count"],
                "output_dir": str(OUTPUT_DIR.relative_to(REPO_ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

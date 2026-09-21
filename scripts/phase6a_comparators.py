#!/usr/bin/env python3
"""Qualify CPU comparator lookups for a frozen development or locked cohort.

This runner is deliberately separate from the model benchmark.  It performs
only public, CPU/network lookups for the explicitly supplied cohort and writes
complete row-level artifacts with explicit missingness. It never reads the
ClinVar label into a comparator row and never invokes Modal or a GPU.

The CADD API and UCSC REST API are used as reproducible lookup surfaces.  A
small on-disk cache makes interruptions resumable without silently accepting a
response for a different URL.  AlphaMissense is qualified for an explicitly
identified missense subset from the exact ClinVar source rows, but its public
prediction asset is not downloaded or used in this bounded stage.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import ssl
import tempfile
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi

LOCKED_MANIFEST = Path("research/ml_extension/splits/authoritative_locked_test_manifest.json")
T1_ARCHIVE = Path("data/raw/clinvar/variant_summary_2026-08.txt.gz")
DEFAULT_OUTPUT_DIR = Path("artifacts/phase6a/comparators")
DEFAULT_CACHE = Path("data/derived/ml_extension/phase6a/comparator_lookup_cache.json")
PROTOCOL_HASHES = Path("research/ml_extension/protocol_hashes.json")

CADD_VERSION = "GRCh38-v1.7"
CADD_API_VERSION = "v1.0"
CADD_API_TEMPLATE = (
    "https://cadd.gs.washington.edu/api/{api_version}/{version}/"
    "{chromosome}:{position_1based}_{reference}_{alternate}"
)
PHYLOP_TRACK = "phyloP100way"
PHYLOP_DATA_TIME = "2015-05-08T16:02:02"
PHYLOP_API_TEMPLATE = (
    "https://api.genome.ucsc.edu/getData/track?genome=hg38;track=phyloP100way;"
    "chrom=chr{chromosome};start={start_0based};end={end_0based_exclusive}"
)
MISSENSE_RE = re.compile(r"p\.(?:[A-Z][a-z]{2}|[A-Z])\d+(?:[A-Z][a-z]{2}|[A-Z])(?:$|[),;\s])")
NON_MISSENSE_RE = re.compile(r"p\.(?:=|[A-Za-z*]+(?:Ter|\*|fs|del|ins|dup|ext|\?))")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _current_protocol_hash(repo_root: Path) -> str:
    path = repo_root / PROTOCOL_HASHES
    document = _load_json(path, {})
    files = document.get("files") if isinstance(document, dict) else None
    value = files.get("research/ml_extension/protocol.yaml") if isinstance(files, dict) else None
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"current ML-extension protocol hash is unavailable: {path}")
    return value


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    """Write JSON atomically so a stopped lookup can be resumed safely."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _get_json(url: str) -> tuple[int, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "EvoVariant-TR/phase6a-comparator-qualification",
        },
    )
    with urlopen(request, context=_ssl_context(), timeout=45) as response:
        body = response.read()
        return int(response.status), json.loads(body.decode("utf-8"))


def _request_observation(url: str) -> dict[str, Any]:
    """Fetch one URL and preserve errors as row-level missingness."""
    try:
        status, payload = _get_json(url)
        return {
            "url": url,
            "status": "HTTP_OK" if status == 200 else "HTTP_ERROR",
            "http_status": status,
            "payload": payload,
        }
    except HTTPError as exc:
        return {
            "url": url,
            "status": "HTTP_ERROR",
            "http_status": int(exc.code),
            "error": f"HTTPError:{exc.code}",
        }
    except (OSError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {
            "url": url,
            "status": "REQUEST_ERROR",
            "http_status": None,
            "error": f"{type(exc).__name__}:{exc}",
        }


def _load_cache(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    value = _load_json(path, {"cache_version": 1, "entries": {}})
    if not isinstance(value, dict) or value.get("cache_version") != 1:
        return {"cadd": {}, "phylop": {}}
    entries = value.get("entries")
    if not isinstance(entries, dict):
        return {"cadd": {}, "phylop": {}}
    return {
        "cadd": dict(entries.get("cadd", {})),
        "phylop": dict(entries.get("phylop", {})),
    }


def _save_cache(path: Path, cache: dict[str, dict[str, dict[str, Any]]]) -> None:
    _write_json(path, {"cache_version": 1, "entries": cache})


def _lookup_many(
    *,
    kind: str,
    rows: list[dict[str, Any]],
    url_for: Callable[[dict[str, Any]], str],
    cache: dict[str, dict[str, dict[str, Any]]],
    cache_path: Path,
    max_workers: int,
) -> tuple[list[dict[str, Any]], dict[str, int], float]:
    """Fetch a deterministic row set with a bounded, resumable worker pool."""
    started = time.monotonic()
    entries = cache.setdefault(kind, {})
    observations: dict[str, dict[str, Any]] = {}
    pending: list[tuple[str, str]] = []
    cache_hits = 0
    for row in rows:
        identity = str(row["normalized_variant_id"])
        url = url_for(row)
        entry = entries.get(identity)
        if isinstance(entry, dict) and entry.get("url") == url:
            observations[identity] = entry
            cache_hits += 1
        else:
            pending.append((identity, url))

    print(
        json.dumps(
            {
                "comparator": kind,
                "total": len(rows),
                "cache_hits": cache_hits,
                "network_requests_required": len(pending),
            },
            sort_keys=True,
        )
    )
    completed = 0
    if pending:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures: dict[Future[dict[str, Any]], tuple[str, str]] = {
                executor.submit(_request_observation, url): (identity, url)
                for identity, url in pending
            }
            for future in as_completed(futures):
                identity, url = futures[future]
                try:
                    observation = future.result()
                except Exception as exc:  # pragma: no cover - executor guard
                    observation = {
                        "url": url,
                        "status": "REQUEST_ERROR",
                        "http_status": None,
                        "error": f"{type(exc).__name__}:{exc}",
                    }
                entries[identity] = observation
                observations[identity] = observation
                completed += 1
                if completed % 16 == 0 or completed == len(pending):
                    _save_cache(cache_path, cache)
                    print(
                        json.dumps(
                            {
                                "comparator": kind,
                                "completed": completed,
                                "remaining": len(pending) - completed,
                            },
                            sort_keys=True,
                        )
                    )

    ordered = [observations[str(row["normalized_variant_id"])] for row in rows]
    status_counts: dict[str, int] = {}
    for observation in ordered:
        status = str(observation.get("status", "UNKNOWN"))
        status_counts[status] = status_counts.get(status, 0) + 1
    return ordered, status_counts, time.monotonic() - started


def _manifest_rows(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    rows = manifest.get("records")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("cohort manifest records must be a list of objects")
    expected_total = manifest.get("record_count")
    if expected_total is None and isinstance(manifest.get("counts"), dict):
        expected_total = manifest["counts"].get("total")
    if expected_total is not None and len(rows) != int(expected_total):
        raise ValueError(
            f"cohort manifest record count does not match its metadata: "
            f"expected {expected_total}, got {len(rows)}"
        )
    record_rows = [
        {
            key: value
            for key, value in row.items()
            if key not in {"sampling_hash", "sampling_stratum"}
        }
        for row in rows
    ]
    record_hash = _canonical_hash(record_rows)
    if record_hash != manifest.get("record_set_sha256"):
        raise ValueError("cohort manifest record_set_sha256 does not match its records")
    assemblies = {str(row.get("assembly")) for row in rows}
    if assemblies != {"GRCh38"}:
        raise ValueError("cohort manifest assembly must be uniformly GRCh38")
    return manifest, rows, record_hash


def _cadd_url(row: dict[str, Any]) -> str:
    return CADD_API_TEMPLATE.format(
        api_version=CADD_API_VERSION,
        version=CADD_VERSION,
        chromosome=row["chromosome"],
        position_1based=row["position_1based"],
        reference=row["reference"],
        alternate=row["alternate"],
    )


def _phylop_url(row: dict[str, Any]) -> str:
    position = int(row["position_1based"])
    return PHYLOP_API_TEMPLATE.format(
        chromosome=row["chromosome"],
        start_0based=position - 1,
        end_0based_exclusive=position,
    )


def _base_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "normalized_variant_id": row["normalized_variant_id"],
        "assembly": row["assembly"],
        "chromosome": row["chromosome"],
        "position_1based": row["position_1based"],
        "reference": row["reference"],
        "alternate": row["alternate"],
    }


def _parse_cadd(row: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    result = _base_row(row)
    result.update({"raw_score": None, "scaled_phred": None, "status": "MISSING"})
    payload = observation.get("payload")
    expected = {
        "Chrom": str(row["chromosome"]),
        "Pos": str(row["position_1based"]),
        "Ref": str(row["reference"]),
        "Alt": str(row["alternate"]),
    }
    if observation.get("status") != "HTTP_OK" or not isinstance(payload, list):
        result["missing_reason"] = observation.get("error", "no_http_json_payload")
        return result
    match = next(
        (
            candidate
            for candidate in payload
            if isinstance(candidate, dict)
            and all(str(candidate.get(key)) == value for key, value in expected.items())
        ),
        None,
    )
    if not isinstance(match, dict):
        result["missing_reason"] = "requested_ref_alt_not_returned"
        return result
    try:
        raw_score = float(match["RawScore"])
        scaled_phred = float(match["PHRED"])
    except (KeyError, TypeError, ValueError):
        result["missing_reason"] = "returned_score_not_numeric"
        return result
    result.update(
        {
            "raw_score": raw_score,
            "scaled_phred": scaled_phred,
            "status": "AVAILABLE",
            "missing_reason": None,
        }
    )
    return result


def _parse_phylop(row: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    result = _base_row(row)
    result.update({"sitewise_score": None, "status": "MISSING"})
    payload = observation.get("payload")
    if observation.get("status") != "HTTP_OK" or not isinstance(payload, dict):
        result["missing_reason"] = observation.get("error", "no_http_json_payload")
        return result
    values = payload.get(PHYLOP_TRACK)
    if not isinstance(values, list):
        result["missing_reason"] = "track_value_array_missing"
        return result
    position = int(row["position_1based"])
    match = next(
        (
            candidate
            for candidate in values
            if isinstance(candidate, dict)
            and candidate.get("chrom") == f"chr{row['chromosome']}"
            and int(candidate.get("start", -1)) == position - 1
            and int(candidate.get("end", -1)) == position
        ),
        None,
    )
    if not isinstance(match, dict):
        result["missing_reason"] = "requested_coordinate_not_returned"
        return result
    try:
        score = float(match["value"])
    except (KeyError, TypeError, ValueError):
        result["missing_reason"] = "returned_score_not_numeric"
        return result
    result.update({"sitewise_score": score, "status": "AVAILABLE", "missing_reason": None})
    return result


def _source_record_lookup(
    archive: Path,
    target_hashes: set[str],
) -> dict[str, dict[str, str]]:
    """Recover only exact t1 source rows referenced by the locked manifest."""
    matches: dict[str, dict[str, str]] = {}
    with gzip.open(archive, "rt", encoding="utf-8", errors="replace") as handle:
        header_line = handle.readline()
        if not header_line:
            raise ValueError(f"empty ClinVar archive: {archive}")
        columns = header_line.rstrip("\r\n").split("\t")
        index = {name: position for position, name in enumerate(columns)}
        required = {
            "Type",
            "Name",
            "GeneSymbol",
            "Chromosome",
            "PositionVCF",
            "Start",
            "ReferenceAlleleVCF",
            "ReferenceAllele",
            "AlternateAlleleVCF",
            "AlternateAllele",
        }
        missing = sorted(required.difference(index))
        if missing:
            raise ValueError(f"ClinVar archive is missing columns: {missing}")
        for raw_line in handle:
            raw_hash = hashlib.sha256(raw_line.encode("utf-8")).hexdigest()
            if raw_hash not in target_hashes:
                continue
            parts = raw_line.rstrip("\r\n").split("\t")
            if len(parts) < len(columns):
                continue
            matches[raw_hash] = {
                "variant_type": parts[index["Type"]],
                "name": parts[index["Name"]],
                "gene_symbol": parts[index["GeneSymbol"]],
                "chromosome": parts[index["Chromosome"]],
                "position_vcf": parts[index["PositionVCF"]],
                "start": parts[index["Start"]],
                "reference_vcf": parts[index["ReferenceAlleleVCF"]],
                "reference_legacy": parts[index["ReferenceAllele"]],
                "alternate_vcf": parts[index["AlternateAlleleVCF"]],
                "alternate_legacy": parts[index["AlternateAllele"]],
            }
            if len(matches) == len(target_hashes):
                break
    return matches


def _is_missense(name: str) -> bool:
    if not name or name == "-":
        return False
    if NON_MISSENSE_RE.search(name):
        return False
    return MISSENSE_RE.search(name) is not None


def _alpha_missense_artifact(
    *,
    rows: list[dict[str, Any]],
    t1_archive: Path,
) -> dict[str, Any]:
    target_hashes = {str(row["source_record_hash"]) for row in rows}
    source_rows = _source_record_lookup(t1_archive, target_hashes)
    eligible = 0
    output_rows: list[dict[str, Any]] = []
    for row in rows:
        source_hash = str(row["source_record_hash"])
        source = source_rows.get(source_hash)
        name = source.get("name", "") if source else ""
        is_eligible = source is not None and _is_missense(name)
        if is_eligible:
            eligible += 1
        output_rows.append(
            {
                **_base_row(row),
                "eligible_missense": is_eligible,
                "score": None,
                "status": "DEFERRED_NO_PREDICTION_ASSET",
                "missing_reason": (
                    "AlphaMissense precomputed prediction asset and transcript-level mapping "
                    "were not acquired in Phase6A"
                ),
                "source_record_hash": source_hash,
                "source_row_found": source is not None,
                "source_variant_type": source.get("variant_type") if source else None,
                "source_name_has_missense_hgvs": is_eligible,
            }
        )
    return {
        "artifact_id": "phase6a-alphamissense-eligibility-20260921",
        "status": "ELIGIBILITY_QUALIFIED_ASSET_DEFERRED",
        "model": "AlphaMissense applicable missense subset",
        "source": "https://github.com/google-deepmind/alphamissense",
        "prediction_source": "https://console.cloud.google.com/storage/browser/dm_alphamissense",
        "assembly": "GRCh38",
        "selection_rule": (
            "eligible only when the exact locked t1 source row is recovered and its ClinVar "
            "Name contains a protein HGVS amino-acid substitution pattern; non-missense and "
            "unmapped rows remain missing"
        ),
        "source_archive": str(t1_archive),
        "source_archive_sha256": _sha256(t1_archive),
        "source_rows_found": len(source_rows),
        "total_locked_records": len(rows),
        "eligible_missense_n": eligible,
        "prediction_coverage_n": 0,
        "prediction_coverage_fraction_of_eligible": 0.0 if eligible else None,
        "scores_used": False,
        "records": output_rows,
        "decision": (
            "Do not include AlphaMissense in Phase6A metrics. The eligible denominator is "
            "measured from exact source annotations, but no prediction asset or approved "
            "transcript-level lookup was used."
        ),
    }


def _coverage(rows: list[dict[str, Any]], status_key: str = "status") -> dict[str, Any]:
    available = sum(row.get(status_key) == "AVAILABLE" for row in rows)
    return {
        "total": len(rows),
        "available": available,
        "missing": len(rows) - available,
        "coverage_fraction": available / len(rows) if rows else None,
    }


def run(
    *,
    repo_root: Path,
    manifest_path: Path,
    t1_archive: Path,
    output_dir: Path,
    cache_path: Path,
    max_workers: int,
) -> dict[str, Any]:
    manifest, rows, record_hash = _manifest_rows(manifest_path)
    expected_total = manifest.get("record_count")
    if expected_total is None and isinstance(manifest.get("counts"), dict):
        expected_total = manifest["counts"].get("total")
    if expected_total is not None and int(expected_total) != len(rows):
        raise ValueError("cohort manifest total does not match its records")
    if not t1_archive.is_file():
        raise FileNotFoundError(
            f"missing exact source archive for AlphaMissense eligibility: {t1_archive}"
        )
    cache = _load_cache(cache_path)

    cadd_observations, cadd_statuses, cadd_seconds = _lookup_many(
        kind="cadd",
        rows=rows,
        url_for=_cadd_url,
        cache=cache,
        cache_path=cache_path,
        max_workers=max_workers,
    )
    cadd_rows = [
        _parse_cadd(row, observation)
        for row, observation in zip(rows, cadd_observations, strict=True)
    ]
    cadd_coverage = _coverage(cadd_rows)

    phylop_observations, phylop_statuses, phylop_seconds = _lookup_many(
        kind="phylop",
        rows=rows,
        url_for=_phylop_url,
        cache=cache,
        cache_path=cache_path,
        max_workers=max_workers,
    )
    phylop_rows = [
        _parse_phylop(row, observation)
        for row, observation in zip(rows, phylop_observations, strict=True)
    ]
    phylop_coverage = _coverage(phylop_rows)

    alpha = _alpha_missense_artifact(rows=rows, t1_archive=t1_archive)
    output_dir.mkdir(parents=True, exist_ok=True)
    cadd_path = output_dir / "cadd_grch38_v1.7_20260921.json"
    phylop_path = output_dir / "phylop100way_hg38_20260921.json"
    alpha_path = output_dir / "alphamissense_eligibility_20260921.json"

    cadd_artifact = {
        "artifact_id": "phase6a-cadd-grch38-v1.7-20260921",
        "status": "COMPLETE" if cadd_coverage["missing"] == 0 else "COMPLETE_WITH_MISSINGNESS",
        "source": "https://github.com/kircherlab/CADD-scripts",
        "api_source": "https://cadd.bihealth.org/api",
        "api_version": CADD_API_VERSION,
        "cadd_version": CADD_VERSION,
        "assembly": "GRCh38/hg38",
        "score_semantics": (
            "CADD deleteriousness raw score and scaled PHRED score; higher is more deleterious"
        ),
        "license_note": (
            "CADD source states scores are freely available for non-commercial applications; "
            "redistribution/legal review is not asserted here."
        ),
        "request_template": CADD_API_TEMPLATE,
        "lookup_runtime_seconds": round(cadd_seconds, 6),
        "request_status_counts": cadd_statuses,
        "coverage": cadd_coverage,
        "rows": cadd_rows,
    }
    phylop_artifact = {
        "artifact_id": "phase6a-phylop100way-hg38-20260921",
        "status": "COMPLETE" if phylop_coverage["missing"] == 0 else "COMPLETE_WITH_MISSINGNESS",
        "source": "https://genome.ucsc.edu/cgi-bin/hgTrackUi?db=hg38&g=cons100way",
        "download_source": "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/phyloP100way/hg38.phyloP100way.bw",
        "api_source": "https://genome.ucsc.edu/goldenPath/help/api.html",
        "track": PHYLOP_TRACK,
        "assembly": "GRCh38/hg38",
        "track_data_time": PHYLOP_DATA_TIME,
        "score_semantics": (
            "basewise conservation/acceleration score at the reference coordinate; not an "
            "alternate-minus-reference variant-effect score"
        ),
        "coordinate_convention": (
            "UCSC 0-based half-open interval [position_1based-1, position_1based)"
        ),
        "request_template": PHYLOP_API_TEMPLATE,
        "lookup_runtime_seconds": round(phylop_seconds, 6),
        "request_status_counts": phylop_statuses,
        "coverage": phylop_coverage,
        "rows": phylop_rows,
    }
    _write_json(cadd_path, cadd_artifact)
    _write_json(phylop_path, phylop_artifact)
    _write_json(alpha_path, alpha)

    summary = {
        "artifact_id": "phase6a-comparator-qualification-20260921",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": "PASS_WITH_ALPHA_MISSENSE_DEFERRED",
        "execution": {
            "gpu_invoked": False,
            "modal_invoked": False,
            "labels_read_for_scoring": False,
            "locked_record_count": len(rows),
            "manifest_path": str(manifest_path.relative_to(repo_root)),
            "manifest_sha256": _sha256(manifest_path),
            "record_set_sha256": record_hash,
            "protocol_hash": _current_protocol_hash(repo_root),
        },
        "comparators": {
            "cadd": {
                "artifact": str(cadd_path.relative_to(repo_root)),
                "artifact_sha256": _sha256(cadd_path),
                "coverage": cadd_coverage,
                "lookup_status_counts": cadd_statuses,
            },
            "phylop": {
                "artifact": str(phylop_path.relative_to(repo_root)),
                "artifact_sha256": _sha256(phylop_path),
                "coverage": phylop_coverage,
                "lookup_status_counts": phylop_statuses,
            },
            "alphamissense": {
                "artifact": str(alpha_path.relative_to(repo_root)),
                "artifact_sha256": _sha256(alpha_path),
                "eligible_missense_n": alpha["eligible_missense_n"],
                "prediction_coverage_n": alpha["prediction_coverage_n"],
                "prediction_coverage_fraction_of_eligible": alpha[
                    "prediction_coverage_fraction_of_eligible"
                ],
            },
        },
        "decision": (
            "CADD and PhyloP are now available as full-cohort CPU comparator artifacts with "
            "row-level missingness. AlphaMissense has an auditable missense eligibility "
            "denominator but remains subset-only with zero prediction coverage. These artifacts "
            "do not authorize or constitute the Evo2 benchmark."
        ),
        "cache": {
            "path": str(cache_path.relative_to(repo_root)),
            "sha256": _sha256(cache_path),
            "purpose": "resumable raw API observations; not a scientific result registry entry",
        },
        "artifact_paths": [
            str(cadd_path.relative_to(repo_root)),
            str(phylop_path.relative_to(repo_root)),
            str(alpha_path.relative_to(repo_root)),
        ],
    }
    summary_path = output_dir.parent / "phase6a_comparator_qualification_20260921.json"
    summary["summary_artifact"] = str(summary_path.relative_to(repo_root))
    _write_json(summary_path, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, default=LOCKED_MANIFEST)
    parser.add_argument("--t1-archive", type=Path, default=T1_ARCHIVE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--max-workers", type=int, default=8)
    args = parser.parse_args()
    if args.max_workers < 1 or args.max_workers > 8:
        parser.error("--max-workers must be between 1 and 8")
    root = args.repo_root.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else root / args.manifest
    archive = args.t1_archive if args.t1_archive.is_absolute() else root / args.t1_archive
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    cache = args.cache if args.cache.is_absolute() else root / args.cache
    summary = run(
        repo_root=root,
        manifest_path=manifest,
        t1_archive=archive,
        output_dir=output_dir,
        cache_path=cache,
        max_workers=args.max_workers,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Exhaustively search repository history and local artifacts for the old Phase 3 target.

This is an evidence-producing search, not a cohort builder.  Aggregate target counts are
reported as hits, but they are never treated as a recovered identity set.  The resulting
JSON records the Git universe, local artifact roots, exact search terms, and candidate paths
so a later reviewer can distinguish target-side provenance from documentation of the target.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

SEARCH_TERMS = ("1024", "614", "410", "1403225", "1,403,225")
NAME_TERMS = (
    "cohort",
    "temporal",
    "clinvar",
    "locked",
    "split",
    "manifest",
    "variant",
    "parquet",
    "jsonl",
    "vcf",
    "report",
    "presentation",
    "slide",
    "log",
)
SKIP_PARTS = {
    ".git",
    ".venv",
    ".venv-baseline",
    "node_modules",
    ".next",
    ".agents",
    "__pycache__",
    "data/reference",
}


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def _lines(value: str) -> list[str]:
    return sorted({line.strip() for line in value.splitlines() if line.strip()})


def _walk_files(roots: Iterable[Path]) -> list[Path]:
    found: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                relative_parts = path.relative_to(root).parts
            except ValueError:
                relative_parts = path.parts
            if any(part in SKIP_PARTS for part in relative_parts):
                continue
            found.add(path.resolve())
    return sorted(found)


def _file_term_hits(path: Path) -> set[str]:
    hits: set[str] = set()
    try:
        if path.suffix.lower() == ".pptx":
            with zipfile.ZipFile(path) as archive:
                payload = b"\n".join(
                    archive.read(name)
                    for name in archive.namelist()
                    if name.endswith(".xml")
                )
        else:
            payload = path.read_bytes()
    except (OSError, ValueError, zipfile.BadZipFile):
        return hits
    for term in SEARCH_TERMS:
        if term.encode("utf-8") in payload:
            hits.add(term)
    return hits


def _candidate_paths(paths: Iterable[str]) -> list[str]:
    return [
        path
        for path in sorted(set(paths))
        if any(term in path.lower() for term in NAME_TERMS)
    ]


def build_report(root: Path, external_roots: list[Path]) -> dict[str, object]:
    refs = _lines(
        _run_git(
            root,
            "for-each-ref",
            "--format=%(refname) %(objectname) %(creatordate:iso8601)",
        )
    )
    reachable_commits = _lines(_run_git(root, "rev-list", "--all"))
    reflog_entries = _lines(_run_git(root, "reflog", "--all", "--format=%H %gs"))
    reflog_commits = sorted({entry.split(maxsplit=1)[0] for entry in reflog_entries})
    fsck_lines = _lines(
        _run_git(root, "fsck", "--full", "--no-reflogs", "--unreachable", "--no-progress")
    )
    unreachable_commits = sorted(
        line.split()[2]
        for line in fsck_lines
        if len(line.split()) >= 3 and line.split()[1] == "commit"
    )
    unreachable_blobs = sorted(
        line.split()[2]
        for line in fsck_lines
        if len(line.split()) >= 3 and line.split()[1] == "blob"
    )

    history_hits: dict[str, list[str]] = {}
    for term in SEARCH_TERMS:
        history_hits[term] = _lines(
            _run_git(
                root,
                "log",
                "--all",
                "--full-history",
                f"-S{term}",
                "--format=%H %ad %s",
                "--date=iso-strict",
                "--",
            )
        )

    deleted_paths = _lines(
        _run_git(
            root,
            "log",
            "--all",
            "--reflog",
            "--full-history",
            "--diff-filter=D",
            "--pretty=format:",
            "--name-only",
            "--",
        )
    )
    object_paths = _lines(_run_git(root, "rev-list", "--objects", "--all"))
    object_candidate_paths = _candidate_paths(
        [line.split(maxsplit=1)[1] for line in object_paths if " " in line]
    )

    files = _walk_files([root, *external_roots])
    local_hits: dict[str, list[str]] = {term: [] for term in SEARCH_TERMS}
    for path in files:
        for term in _file_term_hits(path):
            local_hits[term].append(str(path))

    remote_lines = _lines(_run_git(root, "remote", "-v"))
    remote_refs = _lines(_run_git(root, "ls-remote", "--heads", "--tags", "origin"))

    return {
        "artifact_id": "phase3-recovery-search-20260921",
        "checked_at": datetime.now(UTC).isoformat(),
        "target_counts_searched": {
            "t0_unique_vus": 1403225,
            "final_temporal_n": 1024,
            "n_blb": 614,
            "n_plp": 410,
        },
        "search_terms": list(SEARCH_TERMS),
        "git": {
            "refs": refs,
            "reachable_commit_count": len(reachable_commits),
            "reflog_entry_count": len(reflog_entries),
            "reflog_commit_count": len(reflog_commits),
            "unreachable_commit_ids": unreachable_commits,
            "unreachable_blob_ids": unreachable_blobs,
            "exact_count_history_hits": history_hits,
            "deleted_paths": deleted_paths,
            "candidate_paths_in_all_reachable_objects": object_candidate_paths,
        },
        "remote": {
            "configured_remotes": remote_lines,
            "fetched_heads_and_tags": remote_refs,
        },
        "local_artifact_roots": [str(path) for path in [root, *external_roots]],
        "local_exact_count_hits": {
            term: sorted(set(paths)) for term, paths in local_hits.items()
        },
        "interpretation": {
            "target_identity_manifest_recovered": False,
            "target_source_row_manifest_recovered": False,
            "reason": (
                "All exact-count hits are protocol/documentation/control-plane references, "
                "historical generic reports, or the current audit. No frozen normalized-ID "
                "set or source-row manifest reproducing the 1,024 target was found in the "
                "reachable history, reflog/unreachable objects, fetched remote refs, local "
                "worktrees, repository artifacts, presentations, or supplied attachments."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--external-root", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    report = build_report(root, [path.resolve() for path in args.external_root])
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "target_identity_manifest_recovered": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI entrypoint smoke tests (Milestone 16)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evovariant_tr import __version__
from evovariant_tr.cli import main
from evovariant_tr.manifest import build_entry, build_manifest, write_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = REPO_ROOT / "research" / "protocol" / "protocol.yaml"


def test_version_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["version"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"package": "evovariant-tr", "version": __version__}


def test_verify_model_registry_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["verify-model-registry"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert payload["manifest_count"] == 7
    assert payload["included_count"] == 1


def test_phase_status_command_writes_no_result_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "phase.json"
    assert main(
        [
            "phase-status",
            "--phase",
            "6",
            "--family",
            "ZS",
            "--output",
            str(output),
            "--blocker",
            "fixture gate",
        ]
    ) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "BLOCKED"
    assert "phase.json" in capsys.readouterr().out


def test_phase_status_command_can_record_formal_deferral(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "deferred-phase.json"
    assert main(
        [
            "phase-status",
            "--phase",
            "10",
            "--family",
            "FT",
            "--output",
            str(output),
            "--status",
            "DEFERRED",
            "--blocker",
            "training path requires separate approval",
        ]
    ) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "DEFERRED"
    assert "deferred-phase.json" in capsys.readouterr().out


def test_generate_figure_manifest_command_is_truthful_without_runs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "figure-manifest.json"
    assert main(
        [
            "generate-figure-manifest",
            "--registry",
            str(tmp_path / "registry"),
            "--repo-root",
            str(tmp_path),
            "--output",
            str(output),
        ]
    ) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "BLOCKED"
    assert payload["eligible_completed_run_count"] == 0
    assert "metrics" not in payload
    assert "BLOCKED" in capsys.readouterr().out


def test_render_figure_bundle_command_reports_blocked_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = tmp_path / "figure-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "status": "BLOCKED",
                "required_figures": [],
                "required_tables": [],
                "blockers": ["fixture blocker"],
            }
        ),
        encoding="utf-8",
    )
    assert main(
        [
            "render-figure-bundle",
            "--manifest",
            str(manifest),
            "--repo-root",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "figures"),
        ]
    ) == 0
    payload = json.loads(
        (tmp_path / "figures" / "bundle_manifest.json").read_text(encoding="utf-8")
    )
    assert payload["status"] == "BLOCKED"
    assert payload["outputs"] == []
    assert "BLOCKED" in capsys.readouterr().out


def test_validate_protocol_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate-protocol", "--protocol", str(PROTOCOL)]) == 0
    out = capsys.readouterr().out
    assert "OK: protocol 1.0.0 validated" in out
    assert "GRCh38" in out
    assert "8192bp" in out


def test_validate_protocol_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        main(["validate-protocol", "--protocol", str(tmp_path / "nope.yaml")])


def test_verify_manifest_command_clean_and_corrupt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = tmp_path / "assets"
    base.mkdir()
    asset = base / "data.txt"
    asset.write_text("hello\n", encoding="utf-8")
    manifest_path = write_manifest(
        build_manifest("cli_smoke", base, [build_entry("data.txt", base)]),
        tmp_path / "manifest.json",
    )

    assert main(["verify-manifest", "--manifest", str(manifest_path), "--base-dir", str(base)]) == 0
    assert "OK" in capsys.readouterr().out

    asset.write_text("tampered\n", encoding="utf-8")
    assert main(["verify-manifest", "--manifest", str(manifest_path), "--base-dir", str(base)]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_no_command_exits_with_error() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_build_cohort_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Smoke test for the build-cohort subcommand (Milestone 36)."""
    import gzip

    header = (
        "#AlleleID\tType\tClinicalSignificance\tReviewStatus\tAssembly\t"
        "Chromosome\tStart\tStop\tReferenceAllele\tAlternateAllele\t"
        "VariationID\tRCVaccession\tOriginSimple\tGeneSymbol\t"
        "RS# (dbSNP)\tLastEvaluated\n"
    )
    row = (
        "1\tSNV\tUncertain_significance\treviewed by expert panel\tGRCh38\t"
        "7\t100\t100\tA\tT\t101\tRCV000000001\tgermline\tBRCA1\t111\t2024-01-15\n"
    )

    t0 = tmp_path / "t0.txt.gz"
    t1 = tmp_path / "t1.txt.gz"
    with gzip.open(t0, "wt") as f:
        f.write(header + row)
    with gzip.open(t1, "wt") as f:
        f.write(header + row)  # Same variant, still VUS

    assert main(["build-cohort", "--t0", str(t0), "--t1", str(t1)]) == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "n_total" in data
    assert data["n_unresolved"] == 1

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

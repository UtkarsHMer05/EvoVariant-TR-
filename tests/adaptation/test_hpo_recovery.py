"""The live HPO database must stay local and survive a Drive snapshot round trip."""

import sqlite3
from pathlib import Path

import pytest

from evovariant_tr.adaptation.checkpointing import (
    check_sqlite_database,
    restore_hpo_database,
    snapshot_hpo_database,
)


def test_sqlite_snapshot_resume_keeps_trial_state(tmp_path: Path) -> None:
    drive = tmp_path / "drive" / "caduceus_hpo.sqlite3"
    drive.parent.mkdir()
    with sqlite3.connect(drive) as conn:
        conn.execute("CREATE TABLE trials (number INTEGER PRIMARY KEY, state TEXT)")
        conn.execute("INSERT INTO trials VALUES (0, 'RUNNING')")
    active = tmp_path / "content" / "caduceus_hpo.sqlite3"
    assert restore_hpo_database(drive, active) == drive
    with sqlite3.connect(active) as conn:
        conn.execute("UPDATE trials SET state = 'COMPLETE' WHERE number = 0")
    snapshot = snapshot_hpo_database(active, drive)
    assert snapshot != drive and drive.exists()
    active.unlink()
    assert restore_hpo_database(drive, active) == snapshot
    check_sqlite_database(active)
    with sqlite3.connect(active) as conn:
        assert conn.execute("SELECT number, state FROM trials").fetchall() == [(0, "COMPLETE")]
    with sqlite3.connect(drive) as conn:
        assert conn.execute("SELECT state FROM trials").fetchone() == ("RUNNING",)
    active.unlink()
    snapshot.write_bytes(b"invalid snapshot")
    assert restore_hpo_database(drive, active) == drive
    check_sqlite_database(active)
    assert list(drive.parent.glob("*.forensic_*"))
    active.write_bytes(b"invalid local database")
    assert restore_hpo_database(drive, active) == drive
    assert list(active.parent.glob("*.forensic_*"))
    active.unlink()
    drive.write_bytes(b"invalid legacy database")
    with pytest.raises(RuntimeError, match="no valid HPO SQLite snapshot"):
        restore_hpo_database(drive, active)

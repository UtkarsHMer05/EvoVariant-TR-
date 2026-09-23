#!/usr/bin/env python3
"""Build and syntax-check the canonical Colab adaptation notebook."""

from __future__ import annotations

import argparse
import ast
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks/EvoVariant_TR_Adaptation_Autonomous.ipynb"


def _markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def _code(source: str) -> dict:
    source = textwrap.dedent(source).strip() + "\n"
    ast.parse(source)
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


def _cells() -> list[dict]:
    return [
        _markdown(
            "## 1. Environment summary\n\n"
            "This is the frozen post-hoc adaptation study. The old "
            "EvoVariantTR_original path is optional recovery evidence; its "
            "absence never blocks destination verification or training."
        ),
        _code(
            """
            from pathlib import Path
            import json, os, platform, subprocess, sys

            ROOT = Path("/content/EvoVariant")
            DRIVE = Path("/content/drive/MyDrive/EvoVariantTR")
            REFERENCE = Path("/content/Homo_sapiens_assembly38.fasta")
            BRANCH = "research/posthoc-foundation-adaptation"
            try:
                import torch
                CUDA_READY = bool(torch.cuda.is_available())
                GPU = torch.cuda.get_device_name(0) if CUDA_READY else None
            except ImportError:
                CUDA_READY, GPU = False, None
            print(json.dumps({
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "cuda": CUDA_READY,
                "gpu": GPU,
            }, sort_keys=True))
            """
        ),
        _markdown(
            "## 2. Drive mount\n\n"
            "Mount Drive and use the owned EvoVariantTR directory as the writable root."
        ),
        _code(
            """
            from google.colab import drive
            import json

            if not Path("/content/drive/MyDrive").is_dir():
                drive.mount("/content/drive")
            MYDRIVE = Path("/content/drive/MyDrive")
            SOURCE = MYDRIVE / "EvoVariantTR_original"
            DRIVE.mkdir(parents=True, exist_ok=True)
            if DRIVE.is_symlink():
                raise RuntimeError(f"Writable destination must be an owned directory: {DRIVE}")
            (DRIVE / "state").mkdir(parents=True, exist_ok=True)
            visibility = {
                "source_status": (
                    "VISIBLE_OPTIONAL"
                    if SOURCE.is_dir()
                    else "MIGRATION_SOURCE_NOT_AVAILABLE"
                ),
                "source": str(SOURCE) if SOURCE.is_dir() else None,
                "destination": str(DRIVE),
                "old_source_used_as_gate": False,
            }
            (DRIVE / "state/source_visibility.json").write_text(
                json.dumps(visibility, indent=2, sort_keys=True) + "\\n",
                encoding="utf-8",
            )
            print(json.dumps(visibility, indent=2, sort_keys=True))
            """
        ),
        _markdown(
            "## 3. Repository and branch synchronization\n\n"
            "Preserve a dirty Colab checkout before fast-forwarding to the pushed "
            "adaptation branch."
        ),
        _code(
            """
            from datetime import datetime, timezone
            import shutil

            def git(*args, check=True):
                return subprocess.run(
                    ["git", "-C", str(ROOT), *args],
                    check=check,
                    capture_output=True,
                    text=True,
                )

            if not ROOT.exists():
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--branch",
                        BRANCH,
                        "https://github.com/UtkarsHMer05/EvoVariant-TR-.git",
                        str(ROOT),
                    ],
                    check=True,
                )
            else:
                dirty = git("status", "--porcelain").stdout
                if dirty.strip():
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    backup = DRIVE / "artifacts/adaptation" / f"colab_pre_sync_{stamp}"
                    backup.mkdir(parents=True, exist_ok=True)
                    (backup / "status.txt").write_text(dirty, encoding="utf-8")
                    diff = subprocess.run(
                        ["git", "-C", str(ROOT), "diff", "--binary"],
                        check=True,
                        capture_output=True,
                    ).stdout
                    (backup / "diff.patch").write_bytes(diff)
                    subprocess.run(
                        [
                            "git",
                            "-C",
                            str(ROOT),
                            "stash",
                            "push",
                            "--include-untracked",
                            "-m",
                            f"pre-adaptation-sync-{stamp}",
                        ],
                        check=True,
                    )
                git("fetch", "origin")
                branch = git("branch", "--list", BRANCH).stdout.strip()
                if not branch:
                    git("checkout", "-B", BRANCH, f"origin/{BRANCH}")
                else:
                    git("checkout", BRANCH)
                git("pull", "--ff-only", "origin", BRANCH)
            branch = git("branch", "--show-current").stdout.strip()
            head = git("rev-parse", "HEAD").stdout.strip()
            if branch != BRANCH or git("status", "--porcelain").stdout.strip():
                raise RuntimeError(f"checkout is not clean on {BRANCH}: {head}")
            os.environ["PYTHONPATH"] = str(ROOT / "src")
            print(json.dumps({"branch": branch, "HEAD": head, "status": "CLEAN"}, sort_keys=True))
            """
        ),
        _markdown(
            "## 4. Destination verification\n\n"
            "Verify manifests, writable state, protocol, reference when available, and the pinned "
            "Caduceus revision. Old-source visibility is reported, never required."
        ),
        _code(
            """
            VERIFICATION = DRIVE / "artifacts/adaptation/destination_verification.json"
            verify_env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
            verify_cmd = [
                sys.executable,
                str(ROOT / "scripts/adaptation/verify_destination.py"),
                "--root",
                str(ROOT),
                "--drive-root",
                str(DRIVE),
                "--reference",
                str(REFERENCE),
                "--output",
                str(VERIFICATION),
            ]
            result = subprocess.run(verify_cmd, env=verify_env, capture_output=True, text=True)
            print(result.stdout[-12000:])
            if result.stderr:
                print(result.stderr[-4000:], file=sys.stderr)
            report = (
                json.loads(VERIFICATION.read_text(encoding="utf-8"))
                if VERIFICATION.exists()
                else {}
            )
            print("destination status:", report.get("status", "MISSING"))
            """
        ),
        _markdown(
            "## 5. Isolated runtime activation\n\n"
            "Reuse the verified Python 3.11/CUDA environment. CPU-only sessions report "
            "WAITING_FOR_FREE_GPU and do not install or train."
        ),
        _code(
            """
            PY = None
            if CUDA_READY:
                subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/adaptation/bootstrap_environment.py"),
                        "--root",
                        str(ROOT),
                    ],
                    check=True,
                )
                PY = str(Path("/content/caduceus-env/bin/python"))
                if not Path(PY).is_file():
                    raise RuntimeError(f"isolated Python was not created: {PY}")
                print("isolated Python:", PY)
            else:
                print("WAITING_FOR_FREE_GPU: environment installation and training skipped")
            """
        ),
        _markdown(
            "## 6. Reference and model-cache verification\n\n"
            "Prepare the pinned GRCh38 reference from the destination cache or public archive, "
            "validate all 4,000 formal REF alleles, and record the Caduceus model revision."
        ),
        _code(
            """
            if PY:
                env = {
                    **os.environ,
                    "PYTHONPATH": str(ROOT / "src"),
                    "PYTHONUNBUFFERED": "1",
                }
                reference_cmd = [
                    PY,
                    str(ROOT / "scripts/adaptation/prepare_reference.py"),
                    "--root",
                    str(ROOT),
                    "--drive-root",
                    str(DRIVE),
                    "--output",
                    str(REFERENCE),
                ]
                if SOURCE.is_dir():
                    reference_cmd.extend(["--source-drive-root", str(SOURCE)])
                subprocess.run(reference_cmd, env=env, check=True)
                subprocess.run(
                    [
                        PY,
                        str(ROOT / "scripts/adaptation/verify_data.py"),
                        "--root",
                        str(ROOT),
                        "--reference",
                        str(REFERENCE),
                        "--output",
                        str(DRIVE / "state/data_ready.json"),
                        "--state",
                        str(DRIVE / "state/adaptation_state.json"),
                    ],
                    env=env,
                    check=True,
                )
                subprocess.run(
                    [
                        PY,
                        str(ROOT / "scripts/adaptation/verify_destination.py"),
                        "--root",
                        str(ROOT),
                        "--drive-root",
                        str(DRIVE),
                        "--reference",
                        str(REFERENCE),
                        "--output",
                        str(VERIFICATION),
                    ],
                    env=env,
                    check=True,
                )
                verified = json.loads(VERIFICATION.read_text(encoding="utf-8"))
                if verified.get("status") != "DESTINATION_READY_TO_RESUME":
                    raise RuntimeError(f"destination is not ready: {verified.get('status')}")
                print("reference/model cache: VERIFIED")
            else:
                print("Reference preparation waits for an eligible free GPU session")
            """
        ),
        _markdown(
            "## 7. Persisted state summary\n\n"
            "Read Drive state and a local read-only SQLite copy. A stale PID or stale notebook "
            "output is never treated as current evidence."
        ),
        _code(
            """
            STATE = DRIVE / "state/adaptation_state.json"

            def read_json(path):
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as error:
                    return {"read_error": f"{type(error).__name__}: {error}"}

            state = read_json(STATE) if STATE.exists() else {}
            print("last persisted stage:", state.get("stage", "MISSING"))
            frozen = DRIVE / "checkpoints/caduceus_frozen_head/run.json"
            frozen_report = read_json(frozen) if frozen.exists() else {}
            print("frozen-head baseline:", frozen_report.get("status", "PENDING"))
            db = DRIVE / "hpo/caduceus_hpo.sqlite3"
            snapshot = db.with_name(db.name + ".snapshot")
            local_db = Path("/content/evovariant_runtime/hpo/preflight.sqlite3")
            db_checked = False
            for source_db in (snapshot, db):
                if not source_db.exists():
                    continue
                try:
                    local_db.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source_db, local_db)
                    with sqlite3.connect(f"file:{local_db}?mode=ro", uri=True) as conn:
                        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                        trials = conn.execute(
                            "SELECT number,state FROM trials ORDER BY number"
                        ).fetchall()
                    print("HPO SQLite:", source_db.name, integrity, trials)
                    db_checked = integrity == "ok"
                    break
                except (OSError, sqlite3.Error) as error:
                    print("HPO SQLite read error:", source_db.name, type(error).__name__)
            print(
                "HPO database verified:",
                db_checked if (snapshot.exists() or db.exists()) else "NOT_PRESENT",
            )
            """
        ),
        _markdown(
            "## 8. Autonomous runner launch\n\n"
            "One guarded worker resumes persisted Caduceus stages in protocol order. It creates "
            "the log directory before launching and ignores stale PID files."
        ),
        _code(
            """
            PID_FILE = DRIVE / "state/autonomous_runner.pid"
            LOG = DRIVE / "logs/autonomous_runner.log"

            def active_runner_lines():
                result = subprocess.run(["ps", "-eo", "args="], capture_output=True, text=True)
                return [
                    line
                    for line in result.stdout.splitlines()
                    if "scripts/adaptation/run_autonomous.py" in line
                ]

            if not PY:
                print("WAITING_FOR_FREE_GPU; no worker launched")
            else:
                active = active_runner_lines()
                if active:
                    print("RUNNING:", active)
                else:
                    LOG.parent.mkdir(parents=True, exist_ok=True)
                    env = {
                        **os.environ,
                        "PYTHONPATH": str(ROOT / "src"),
                        "PYTHONUNBUFFERED": "1",
                    }
                    with LOG.open("a", encoding="utf-8") as log:
                        worker = subprocess.Popen(
                            [
                                PY,
                                str(ROOT / "scripts/adaptation/run_autonomous.py"),
                                "--root",
                                str(ROOT),
                                "--drive-root",
                                str(DRIVE),
                                "--reference",
                                str(REFERENCE),
                            ],
                            cwd=ROOT,
                            env=env,
                            stdout=log,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
                    PID_FILE.write_text(str(worker.pid), encoding="utf-8")
                    print("RUNNING:", worker.pid, "log:", LOG)
            """
        ),
        _markdown(
            "## 9. Non-throwing monitor\n\n"
            "A finished, signaled, waiting, or failed process is reported as evidence. Re-run "
            "this cell to refresh progress."
        ),
        _code(
            """
            STATUS = DRIVE / "state/autonomous_runner_status.json"
            active = active_runner_lines()
            if active:
                process_state = "RUNNING"
            elif STATUS.exists():
                runner = read_json(STATUS)
                saved = runner.get("status")
                process_state = "EXITED_UNKNOWN" if saved == "RUNNING" else (saved or "UNKNOWN")
            else:
                process_state = "NOT_STARTED"
            print("process:", process_state)
            print("runner:", read_json(STATUS) if STATUS.exists() else "PENDING")
            print(
                "log tail:",
                LOG.read_text(errors="replace")[-4000:] if LOG.exists() else "PENDING",
            )
            """
        ),
        _markdown(
            "## 10. Final persisted-state summary\n\n"
            "Report only persisted evidence. The historical 946-row temporal result remains "
            "prohibited for adaptation selection."
        ),
        _code(
            """
            current = read_json(STATE) if STATE.exists() else {}
            hpo_report_path = DRIVE / "hpo/caduceus_hpo.json"
            lock = DRIVE / "hpo/selection_closed.json"
            proof = DRIVE / "artifacts/adaptation/caduceus_partial_small_finetune_smoke.json"
            print(
                json.dumps(
                    {
                        "state": current.get("stage", "PENDING"),
                        "runner": read_json(STATUS) if STATUS.exists() else "PENDING",
                        "hpo": (
                            read_json(hpo_report_path).get("status", "PENDING")
                            if hpo_report_path.exists()
                            else "PENDING"
                        ),
                        "selection": "CLOSED" if lock.exists() else "OPEN",
                        "encoder_update_proof": (
                            read_json(proof).get("status", "MISSING")
                            if proof.exists()
                            else "MISSING"
                        ),
                        "801_holdout": (
                            "CLOSED_UNTIL_SELECTION_LOCK"
                            if not lock.exists()
                            else "OPENED_ONLY_BY_RUNNER"
                        ),
                        "946_temporal_cohort": "PROHIBITED_FOR_ADAPTATION_SELECTION",
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            """
        ),
    ]


def build() -> dict:
    cells = _cells()
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    notebook = build()
    if args.check:
        print(f"OK: {len(notebook['cells'])} canonical cells; all code cells parse")
        return 0
    NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {NOTEBOOK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

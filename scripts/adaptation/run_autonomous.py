#!/usr/bin/env python3
"""Resume the guarded Caduceus sequence from persisted TRAIN-only artifacts."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

from evovariant_tr.adaptation.data import sha256_file
from evovariant_tr.adaptation.models import MODEL_REVISIONS

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"
REFERENCE_HASH = "5be01555d98347fdb3714dc84c6f77c9d8bc774adcf32c6f7a8fa06f5baf5e51"
SEEDS = (42, 1337, 2026)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _status(path: Path, value: dict[str, str]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _run(root: Path, script: str, *arguments: str) -> None:
    command = [sys.executable, str(root / "scripts/adaptation" / script), *arguments]
    print("running", script, flush=True)
    subprocess.run(command, cwd=root, check=True)


def _verified_run(report_path: Path, checkpoint: Path, *, seed: int | None = None,
                  lock_hash: str | None = None) -> bool:
    if not report_path.exists():
        return False
    report = _read(report_path)
    if (report.get("status") != "PASS" or not checkpoint.is_file()
            or report.get("checkpoint_sha256") != sha256_file(checkpoint)
            or report.get("protocol_sha256") != PROTOCOL_HASH):
        raise RuntimeError(f"existing run failed checkpoint/protocol verification: {report_path}")
    if seed is not None and (report.get("seed") != seed or
                             report.get("config", {}).get("selection_lock_sha256") != lock_hash):
        raise RuntimeError(f"existing run failed selection/seed verification: {report_path}")
    return True


def _execute(root: Path, drive: Path, reference: Path) -> str:
    import torch

    if not torch.cuda.is_available():
        return "WAITING_FOR_FREE_GPU"
    if sha256_file(reference) != REFERENCE_HASH:
        raise RuntimeError("reference FASTA hash mismatch")
    state = drive / "state/adaptation_state.json"
    cache = drive / "model_cache"
    smoke = drive / "runs/caduceus_smoke.json"
    smoke_checkpoint = drive / "checkpoints/caduceus_smoke.pt"
    if smoke.exists():
        report = _read(smoke)
        if (report.get("status") != "PASS" or
                report.get("revision") != MODEL_REVISIONS["caduceus"] or
                report.get("checkpoint_sha256") != sha256_file(smoke_checkpoint)):
            raise RuntimeError("existing smoke report/checkpoint failed verification")
    else:
        _run(root, "smoke_caduceus.py", "--root", str(root), "--device", "cuda",
             "--cache-dir", str(cache), "--output", str(smoke),
             "--checkpoint", str(smoke_checkpoint), "--state", str(state))
    frozen = drive / "checkpoints/caduceus_frozen_head"
    frozen_checkpoint = frozen / "latest.pt"
    if not _verified_run(frozen / "run.json", frozen_checkpoint):
        args = ["--root", str(root), "--reference", str(reference), "--cache-dir", str(cache),
                "--output-dir", str(frozen), "--state", str(state), "--device", "cuda",
                "--stage", "frozen_head_only", "--epochs", "3", "--batch-size", "1",
                "--effective-batch-size", "16", "--dropout", "0.1", "--max-length", "8192",
                "--learning-rate", "2e-5", "--weight-decay", "0.01", "--seed", "42"]
        if frozen_checkpoint.exists():
            args += ["--resume", str(frozen_checkpoint)]
        _run(root, "train_caduceus.py", *args)
    hpo = drive / "hpo/caduceus_hpo.json"
    lock = drive / "hpo/selection_closed.json"
    if not lock.exists():
        _run(root, "run_caduceus_hpo.py", "--root", str(root), "--reference", str(reference),
             "--cache-dir", str(cache), "--checkpoint-dir", str(drive / "checkpoints/caduceus_hpo"),
             "--state", str(state), "--output", str(hpo), "--device", "cuda",
             "--trials", "8", "--microbatch-size", "2", "--max-length", "8192", "--seed", "42")
    if not lock.exists():
        return "HPO_INCOMPLETE"
    selection = _read(lock)
    if (selection.get("status") != "SELECTION_CLOSED" or
            selection.get("protocol_sha256") != PROTOCOL_HASH or
            selection.get("reference_sha256") != REFERENCE_HASH or
            selection.get("holdout_evaluated") is not False or
            selection.get("seed") != 42 or selection.get("trial_count", 0) < 8):
        raise RuntimeError("selection lock failed frozen TRAIN-only gates")
    oof = Path(selection["train_oof_csv"])
    if sha256_file(oof) != selection["train_oof_sha256"]:
        raise RuntimeError("selected TRAIN OOF hash mismatch")
    lock_hash = sha256_file(lock)
    calibration = drive / "analysis/caduceus_train_oof_calibration.json"
    if calibration.exists():
        cal = _read(calibration)
        if (cal.get("status") != "PASS" or cal.get("fit_scope") != "TRAIN_OOF_ONLY" or
                cal.get("holdout_used_for_fit") is not False or
                cal.get("oof_predictions_sha256") != selection["train_oof_sha256"]):
            raise RuntimeError("existing calibration failed TRAIN OOF verification")
    else:
        _run(root, "run_posthoc_analysis.py", "--root", str(root), "--predictions", str(oof),
             "--output", str(calibration), "--state", str(state))
    cal_hash = sha256_file(calibration)
    params = selection["selected_params"]
    runs: dict[int, Path] = {}
    for seed in SEEDS:
        run = drive / ("runs/caduceus_final" if seed == 42 else f"runs/caduceus_final_seed{seed}")
        runs[seed] = run
        checkpoint = run / "latest.pt"
        if _verified_run(run / "run.json", checkpoint, seed=seed, lock_hash=lock_hash):
            continue
        args = ["--root", str(root), "--reference", str(reference), "--cache-dir", str(cache),
                "--output-dir", str(run), "--state", str(state), "--selection-lock", str(lock),
                "--device", "cuda", "--stage", params["regime"], "--epochs",
                str(selection["final_epochs"]), "--batch-size", "1", "--effective-batch-size",
                str(params["effective_batch_size"]), "--dropout", str(params["dropout"]),
                "--max-length", "8192", "--learning-rate", str(params["learning_rate"]),
                "--weight-decay", str(params["weight_decay"]), "--seed", str(seed)]
        if seed != 42:
            args.append("--fixed-seed-robustness")
        if checkpoint.exists():
            args += ["--resume", str(checkpoint)]
        _run(root, "train_caduceus.py", *args)
        _verified_run(run / "run.json", checkpoint, seed=seed, lock_hash=lock_hash)
    for seed in SEEDS:
        suffix = "" if seed == 42 else f"_seed{seed}"
        output = drive / f"exports/caduceus_validation{suffix}.csv"
        report_path = output.with_suffix(".json")
        attempt = output.with_name(f"{output.stem}.attempt.json")
        existing = [path.exists() for path in (output, report_path, attempt)]
        if any(existing):
            if not all(existing):
                raise RuntimeError(
                    f"partial one-shot holdout artifact for seed {seed}; refusing rerun"
                )
            report = _read(report_path)
            if (report.get("status") != "PASS" or report.get("rows") != 801 or
                    report.get("selection_lock_sha256") != lock_hash or
                    report.get("calibration_report_sha256") != cal_hash or
                    report.get("evaluation_attempt_sha256") != sha256_file(attempt)):
                raise RuntimeError(f"existing holdout report failed verification for seed {seed}")
            continue
        args = ["--root", str(root), "--reference", str(reference), "--cache-dir", str(cache),
                "--checkpoint", str(runs[seed] / "latest.pt"), "--selection-lock", str(lock),
                "--calibration-report", str(calibration), "--state", str(state),
                "--output", str(output), "--split", "validation", "--device", "cuda",
                "--seed", str(seed)]
        if seed != 42:
            args.append("--fixed-seed-robustness")
        _run(root, "evaluate_caduceus.py", *args)
    return "CADUCEUS_HOLDOUT_DONE_OTHER_STAGES_PENDING"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/content/EvoVariant")
    parser.add_argument("--drive-root", default="/content/drive/MyDrive/EvoVariantTR")
    parser.add_argument("--reference", default="/content/Homo_sapiens_assembly38.fasta")
    args = parser.parse_args()
    root, drive, reference = Path(args.root), Path(args.drive_root), Path(args.reference)
    lock_path = Path("/content/evovariant_runtime/autonomous.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("RUNNING: an autonomous worker already owns the local lock")
            return
        status_path = drive / "state/autonomous_runner_status.json"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        _status(status_path, {"status": "RUNNING"})
        try:
            processes = subprocess.run(
                ["ps", "-eo", "args="], capture_output=True, text=True, check=True
            ).stdout.splitlines()
            if any(
                "scripts/adaptation/run_caduceus_hpo.py" in line
                or "scripts/adaptation/train_caduceus.py" in line
                for line in processes
            ):
                raise RuntimeError("an older HPO or TRAIN worker is active; stop duplicate launch")
            result = _execute(root, drive, reference)
        except Exception as exc:
            result = "EXITED_FAILURE"
            error = f"{type(exc).__name__}: {exc}"
            _status(status_path, {"status": result, "error": error})
            raise
        else:
            _status(status_path, {"status": result})
            print(result)


if __name__ == "__main__":
    main()

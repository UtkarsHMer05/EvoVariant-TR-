# Adaptation cleanup, 2026-09-23

No scientific artifact, checkpoint, run report, evidence hash, baseline code, or Drive file was deleted.

| Replaced execution path | Canonical path now used | Evidence and boundary |
|---|---|---|
| Ad hoc setup, download, and process cells in the old live Colab notebook | `scripts/adaptation/bootstrap_environment.py`, `prepare_reference.py`, and `run_autonomous.py`, invoked by the clean 10-section notebook | The downloaded 78-cell live notebook is retained under `notebooks/archive/`; no GPU execution was claimed. |
| Active Optuna SQLite on mounted Drive | Local SQLite plus verified atomic Drive `.snapshot` in `checkpointing.py` and `run_caduceus_hpo.py` | Legacy Drive DB retained intact; a downloaded copy passed `PRAGMA integrity_check`. |
| Fold pruning value reported during every epoch, including unfinished fold 1 | Completed-fold intermediate value before pruning | Original trial 0 step-1 value remains in the archived DB; resumed study corrects the local copy before its next pruning decision. |
| Failing `ps` monitor when an old PID exits | Non-throwing `RUNNING` / `EXITED_SUCCESS` / `EXITED_FAILURE` / `UNKNOWN` notebook monitor | A finished process is no longer a red cell. |

The train/evaluate/model/metrics/calibration implementations remain in their existing source modules. No speculative duplicate pipeline was added. The Judge notebook displays source with `inspect` where importable and preserves its evidence labels for pending results.

## Colab recovery repair, 2026-09-23

The existing Colab notebook was saved with the owned recovery folder as the writable run root and the original shared shortcut as a read-only source. Stale cell outputs and an embedded screenshot were cleared. A stale HPO child targeting the shared shortcut was stopped before it produced a runner log, fold-2 history, or new checkpoint. No scientific artifacts or Drive files were deleted, and the notebook was not executed after repair.

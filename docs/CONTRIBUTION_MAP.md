# Adaptation contribution map

| Contribution | Source | Artifact | Figure/result |
|---|---|---|---|
| Frozen post-hoc protocol and split boundary | `research/adaptation/PROTOCOL.md`, `research/adaptation/protocol.yaml` | protocol and manifest SHA-256 values | dataset/leakage table in Judge Demo |
| Verified GRCh38 ref/alt and reverse complements | `src/evovariant_tr/adaptation/data.py` | Drive `state/data_ready.json` (live Colab) | sequence construction section |
| Shared Caduceus paired head and orientation averaging | `src/evovariant_tr/adaptation/models.py` | Drive `runs/caduceus_smoke.json` and checkpoint (live Colab) | paired architecture section |
| TRAIN-only weighted fine-tuning | `src/evovariant_tr/adaptation/training.py`, `scripts/adaptation/train_caduceus.py` | Drive checkpoint/run report (pending baseline completion) | training curves pending |
| Gene-grouped TRAIN-only HPO | `src/evovariant_tr/adaptation/folds.py`, `scripts/adaptation/run_caduceus_hpo.py` | Drive SQLite study, trial summary, closed selection lock (not started) | HPO figures pending |
| Atomic, provenance-bound resume | `src/evovariant_tr/adaptation/checkpointing.py`, `src/evovariant_tr/adaptation/state.py` | Drive state/checkpoints | checkpoint/resume section |
| Metrics, calibration, uncertainty helpers | `src/evovariant_tr/adaptation/metrics.py`, `calibration.py`, `statistics.py` | OOF/holdout analysis artifacts pending | metrics, reliability, CI plots pending |

Empirical contribution claims remain conditional on completed, hash-bound artifacts. Missing figures or systems are not represented as measured results.

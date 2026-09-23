# Adaptation hyperparameter tuning status

The adaptation HPO design is frozen but incomplete. It is separate from the completed baseline HPO and uses only the 3,199-row TRAIN split.

## Search contract

- validation inside each trial: 3-fold `StratifiedGroupKFold`, `groups=gene`;
- mandatory queue prefix: `frozen_head_only`, `partial_small`, `partial_large`, `full_if_feasible`;
- total budget: 8–12 meaningful trials;
- search dimensions: learning rate `{1e-5, 3e-5, 1e-4}`, weight decay `{0, 0.01, 0.05}`, dropout `{0, 0.1, 0.2}`, effective batch size `{16, 32}`, and epoch cap `{4, 6, 8}`;
- fixed seeds: `42`, `1337`, and `2026`; no best-seed selection;
- primary selection metric: AUROC, followed by AUPRC, MCC, lower Brier, then lower compute/trainable parameter count when scientifically equivalent;
- OOF calibration and any final refit are permitted only after selection closes.

## Observed state

The persisted study opened trial 0 (`frozen_head_only`) and retained fold histories/checkpoints, but it did not complete trial 0. Trials 1–3 remained waiting. No adaptation configuration was selected, no final epoch count was frozen, and no 801-row result was produced. Therefore this repository records the HPO design and incomplete state, not an HPO winner.

The historical `research/tables/final/hpo_trials.csv` is the frozen baseline/development HPO table. It is not relabelled as post-hoc Caduceus HPO.

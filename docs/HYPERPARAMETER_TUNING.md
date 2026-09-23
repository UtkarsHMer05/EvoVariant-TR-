# Hyperparameter tuning

## Frozen baseline

The completed baseline HPO used formal TRAIN/VALIDATION development data only. The 801-row VALIDATION split was the declared selection split, and the 946-row temporal locked test was not accessed for tuning. The registered table is [research/tables/final/hpo_trials.csv](../research/tables/final/hpo_trials.csv), with its phase receipt at [research/runs/formal_cpu_20260922/phase9/summary.json](../research/runs/formal_cpu_20260922/phase9/summary.json).

The selected baseline downstream configuration is recorded by the formal phase artifacts. HPO is not foundation-model fine-tuning: it selects downstream model parameters against the declared development split.

## Post-hoc Caduceus adaptation

The separate adaptation study predeclared 3-fold gene-grouped CV inside the 3,199-row TRAIN split, a mandatory regime queue (`frozen_head_only`, `partial_small`, `partial_large`, `full_if_feasible`), and an 8–12 trial budget. Its search dimensions and fixed seeds are documented in [research/adaptation_attempt/HYPERPARAMETER_TUNING.md](../research/adaptation_attempt/HYPERPARAMETER_TUNING.md).

That study did not complete trial 0 or close selection. Trials 1–3 remained waiting; there is no selected adaptation configuration, final epoch count, TRAIN OOF set, or 801-row adaptation metric. The state is recorded as incomplete rather than reconstructed from stale notebook text.

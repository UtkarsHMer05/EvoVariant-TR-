# EvoVariant-TR — Project Handoff

This package is the authoritative handoff for extending **EvoVariant-TR** from a primarily
zero-shot temporal variant-scoring benchmark into a rigorous, reproducible ML research
platform with model comparison, representation learning, downstream training,
hyperparameter optimization, carefully gated fine-tuning, ensembles, calibration,
abstention, robustness analysis, error analysis, batch inference, and a research dashboard.

## Repository

- GitHub: `https://github.com/UtkarsHMer05/EvoVariant-TR-`
- Current working branch at handoff: `research/evovariant-tr`
- Primary package: `src/evovariant_tr/`
- Frontend: `apps/web/`
- Existing research protocol: `research/protocol/`
- Existing test suite: `tests/`
- Existing Modal entry point: `evo2_scorer_app.py`
- Planned compute provider: Modal
- User Modal workspace/app page: `https://modal.com/apps/utkarshmer05/main`

## Critical principle

The existing frozen zero-shot temporal protocol is **not to be rewritten or silently
reinterpreted**. The training/fine-tuning/ensemble work is a separately registered
ML-extension study. Its results may be compared with the frozen zero-shot primary result,
but the extension must not retroactively tune or contaminate the original temporal test set.

## Read order for every coding-agent session

1. `docs/agent/PROJECT_STATE.md`
2. `docs/agent/PRD.md`
3. `docs/agent/DECISIONS.md`
4. `research/ml_extension/PROTOCOL.md`
5. `docs/agent/ARCHITECTURE.md`
6. `docs/agent/EXPERIMENT_PLAN.md`
7. `docs/agent/METRICS_AND_STATISTICS.md`
8. `docs/agent/MODAL_COMPUTE_POLICY.md`
9. `docs/agent/TESTING_AND_VALIDATION.md`
10. `docs/agent/PHASE_LEDGER.md`
11. `docs/agent/RUNBOOK.md`

The agent must then inspect the repository and reconcile these documents with actual code.
Documentation is the control plane; code and registered artifacts are the evidence.

## Golden rules

- Never tune using the final temporal test labels.
- Never fabricate a metric, run, figure, cost, model result, or benchmark.
- Never claim a model is better unless the registered evidence supports the claim.
- Never silently change dataset filters to reproduce an expected count.
- Never overwrite the original frozen protocol.
- Never expose secrets.
- Never launch expensive GPU work without the cost gate.
- Never recompute expensive embeddings/scores if a valid cached artifact exists.
- Never make clinical-diagnostic claims. This remains research software.
- Every phase must pass its gate before the next dependent phase begins.

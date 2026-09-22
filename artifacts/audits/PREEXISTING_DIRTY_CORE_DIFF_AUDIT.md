# Pre-existing dirty core-code diff audit — 2026-09-22

This report covers the four modified tracked paths present before this audit. None was reset,
staged, deleted, or rewritten. The untracked approval/preflight artifacts and `.agents/` directory
are provenance/workspace additions, not core-code diffs, and remain untouched.

## Classification

| Path/hunk | Classification | Finding | Action taken |
|---|---|---|---|
| `src/evovariant_tr/abstention.py:102-111` `_confidences_from_scores` | `SCIENTIFICALLY_REQUIRED` | Signed log-likelihood deltas need confidence based on magnitude: a large negative score is confident in the negative direction. The absolute-`tanh` mapping matches the frozen Phase 14 confidence definition and does not alter the frozen artifact. | Preserved; no automatic commit or rewrite. |
| `src/evovariant_tr/abstention.py:168-178` risk-coverage AUC integration | `SCIENTIFICALLY_REQUIRED` | Points are generated from high to low coverage; integrating in that order can produce a negative area. Sorting by ascending coverage is the root-cause numerical correction and does not touch locked metrics. | Preserved; no automatic commit or rewrite. |
| `src/evovariant_tr/abstention.py:258` final newline | `OBSOLETE` | Formatting-only; no scientific or runtime effect. | Left in place because this audit must not discard pre-existing work. |
| `src/evovariant_tr/analysis_pipeline.py:145` explicit `positive_threshold=0.5` | `SCIENTIFICALLY_REQUIRED` | Downstream probability rows must be interpreted at their operating threshold, not the signed foundation-score threshold of zero. | Preserved; no automatic commit or rewrite. |
| `src/evovariant_tr/ensemble.py:55-96` optional `positive_threshold` | `SCIENTIFICALLY_REQUIRED` | The shared comparison helper serves both signed foundation deltas and probability rows. Default zero preserves signed-score semantics; an explicit threshold prevents probability disagreement/error counts from being silently wrong. | Preserved; no automatic commit or rewrite. |
| `tests/unit/test_experiment_framework.py:306-319` threshold regression test | `SCIENTIFICALLY_REQUIRED` | The test demonstrates the failure mode: signed `0.1/0.9` rows have no disagreement at threshold zero but do disagree at probability threshold `0.5`. | Preserved; no automatic commit or rewrite. |

## Conclusion

There is one obsolete format-only hunk and five scientifically required/correctness hunks. No
dirty core-code change was found to be safe to delete automatically. The scientific result
boundary remains closed: no Phase 14 artifact, threshold, calibration, raw metric, or final
prediction was changed by this audit.

Recommended follow-up is an owner-controlled commit that separates the format-only newline from
the correctness changes if desired. This report intentionally does not stage or commit anything.

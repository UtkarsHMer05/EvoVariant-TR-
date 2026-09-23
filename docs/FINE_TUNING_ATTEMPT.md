# Foundation-model fine-tuning attempt

The project contains a separate, explicitly incomplete Caduceus adaptation appendix at [research/adaptation_attempt](../research/adaptation_attempt/README.md). It is not part of the frozen baseline inference path and does not modify `main`'s primary science.

## Exact status

- Frozen Caduceus encoder plus trained task head: completed on TRAIN only.
- Partial-small encoder-update feasibility proof: PASS; blocks 12–15 were trainable and an encoder parameter changed.
- Partial-small complete fine-tuning trial: not completed.
- Partial-large complete fine-tuning trial: not started.
- Full Caduceus fine-tuning: not completed; resource-deferred.
- Adaptation HPO and selection: incomplete/open.
- 801-row adaptation evaluation: closed/unopened.
- 946-row temporal cohort: prohibited for adaptation selection.

The phrase “fine-tuning completed” is therefore not used. A one-step parameter delta is feasibility evidence, not a trained model result. The exact recovered record is [caduceus_partial_small_finetune_smoke.json](../research/adaptation_attempt/artifacts/caduceus_partial_small_finetune_smoke.json); it explicitly records that no completed experiment, holdout evaluation, or selection closure is claimed.

The implementation snapshot is [research/adaptation_attempt/source_snapshot](../research/adaptation_attempt/source_snapshot). The proof visualization is [encoder_update_proof.svg](../research/adaptation_attempt/figures/encoder_update_proof.svg).

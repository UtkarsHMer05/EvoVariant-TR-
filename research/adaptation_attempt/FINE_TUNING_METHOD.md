# Fine-tuning method and evidence boundary

## Model

The candidate foundation model is Caduceus-Ph:

- model: `kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16`
- revision: `b0477522ac5d044ad03578aa724ec8e4bdbd405b`
- total parameters: `7,728,385`
- protocol: `07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c`

Reference and alternate sequences are encoded as a paired input. The classifier uses the reference embedding, alternate embedding, their signed difference, and the absolute difference. When available, forward and reverse-complement logits are averaged. The task loss is fold-local `BCEWithLogitsLoss` with the declared class weighting.

## Trainability regimes

`configure_trainable()` freezes the backbone before applying the declared regime and keeps the classifier head trainable:

| regime | trainable backbone | status in this appendix |
|---|---|---|
| `frozen_head_only` | none | TRAIN-only baseline completed |
| `partial_small` | final four blocks, 12–15 | one-step update proof only |
| `partial_large` | final eight blocks, 8–15 | not started |
| `full_if_feasible` | all blocks, 0–15 | not started; resource-deferred |

The training loop contains the real gradient path (`backward()`, gradient clipping, and `optimizer.step()`). The source snapshot is provided so a judge can inspect the implementation without mistaking source code for a completed result.

## Evidence interpretation

The proof record shows a nonzero encoder parameter delta and zero frozen-control delta after one optimizer step. That is an implementation/feasibility check. A completed partial or full experiment would additionally require a complete TRAIN-only grouped-CV trial, persisted epoch/fold/checkpoint/OOF evidence, measured metrics, and a final status record. Those artifacts do not exist and are not inferred.

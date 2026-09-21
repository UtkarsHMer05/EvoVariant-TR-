# Modal Compute and Budget Policy

## Objective

Use Modal as the GPU execution layer while keeping the project viable on approximately
$30/month included compute whenever practical.

## Never hard-code pricing

Before material paid runs, consult current official Modal pricing/docs or billing information
available to the environment. Prices can change.

## Workload placement

Local/CPU preferred:
- parsing,
- split creation,
- metrics,
- plots,
- classical ML,
- calibration,
- bootstrap,
- ensemble fitting.

Modal GPU:
- Evo2 inference,
- other GPU-only model inference,
- embeddings,
- PEFT/fine-tuning,
- live model service.

## Cache policy

Cache key includes:
- model,
- exact checkpoint/revision,
- preprocessing revision,
- reference build,
- context,
- orientation,
- layer,
- variant ID.

Do not trust cache if any key field differs.

## Budget ledger fields

- run_id
- timestamp
- workload
- GPU type
- GPU count
- estimated seconds
- measured seconds
- estimated USD
- measured USD
- cache_hit
- approval artifact
- notes

## Default budget gates

These values are defaults and may be adjusted by explicit decision:

- reserve at least 15–20% of monthly included credits for final validation/demo;
- require a written approval artifact before any single run projected to cost more than
  a configured material threshold;
- never launch broad large-model HPO directly;
- never full-fine-tune a multi-billion-parameter model as a first experiment.

## Optimization strategy

1. Model-load smoke.
2. Measure one-item latency.
3. Measure safe batch size.
4. Run small multi-gene batch.
5. Calculate projected cohort cost.
6. Cache outputs.
7. Run only approved full batch.

## Idle control

Use small scaledown windows consistent with model reload cost.
Do not keep GPUs warm for convenience during inactive development.

## Failure control

Retry only idempotent jobs.
Do not blindly retry deterministic OOM or invalid-input failures.
Record spend from failed runs.

## Authorized pilot execution record — 2026-09-21

The dated user approval at `artifacts/approvals/phase2_4_pilot_20260921.json` authorized only a
tiny Phase 2/4 pilot and Phase 5 smoke/audit, capped at `$2.00`. The canonical app identity was
`evovariant-tr`, volume `hf_cache`, H100, the pinned NGC PyTorch image, and Evo2 revision
`4b509ec2a22d6de472659f908bcb0714265ad3a7`.

- Two failed requests are preserved, including their approximate workspace-cost observation;
  the first failure was a deterministic chromosome-prefix boundary bug, not a model-load failure.
- Corrected miss: HTTP 200, 36.2727 wall seconds, 3.914133089 GPU seconds, `cache_hit=false`.
- Equivalent hit: HTTP 200, 0.956 wall seconds, `cache_hit=true`, exact numeric equality, no new
  model-inference telemetry.
- Persistent prediction artifact was verified under the named volume. Model weights remain in
  that remote volume and are not copied into the repository.
- Modal summary was workspace-level: metered `$11.49` before remote requests and `$11.82` after
  the pilot family, billed `$0.00`. The cost ledger therefore records rate-based estimates,
  measured wall/runtime seconds, and `measured_usd: null` rather than inventing an invoice.
- No full benchmark, broad batch, HPO, training, fine-tuning, or locked-test work is authorized
  by this record. Any larger run needs a new explicit approval artifact.

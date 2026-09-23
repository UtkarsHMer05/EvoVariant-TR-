# Adaptation status

Status: `INCOMPLETE_RESOURCE_LIMITED_APPENDIX`

| gate | status | evidence |
|---|---|---|
| branch/protocol/data/reference verification | PASS | frozen manifests, GRCh38 hash, 4,000 REF-allele check |
| Caduceus smoke | PASS | prior verified Drive run record |
| frozen encoder + trained head | PASS | 3-epoch TRAIN-only run record |
| encoder-update feasibility proof | PASS | [proof record](artifacts/caduceus_partial_small_finetune_smoke.json) |
| adaptation HPO | INCOMPLETE | trial 0 persisted partial fold state; selection open |
| partial-small complete trial | NOT COMPLETED | no full trial artifact |
| partial-large trial | NOT STARTED | no artifact |
| full Caduceus fine-tuning | RESOURCE DEFERRED | no complete run or weight-change record |
| final refits/calibration | BLOCKED | no selection lock |
| 801-row adaptation evaluation | CLOSED/UNOPENED | selection never closed |
| 946-row temporal cohort for adaptation selection | PROHIBITED | locked boundary preserved |
| NT frozen/PEFT track | NOT STARTED | no artifact |

The old-account Drive source was optional recovery evidence. Its absence does
not block this appendix and is not falsely reported as a completed migration.
No new GPU run was launched during final project polish.

# Frozen protocol and manifest hash audit — 2026-09-22

The local protocol and ML-control-plane gates passed without changing any frozen scientific
artifact. The values below are the current SHA-256 hashes verified in this checkout.

| File | SHA-256 | Verification |
|---|---|---|
| `research/protocol/protocol.yaml` | `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525` | `make protocol-verify` PASS |
| `research/ml_extension/protocol.yaml` | `bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec` | `make ml-protocol-verify` PASS |
| `research/ml_extension/protocol_hashes.json` | `2ca17bd2f0ad0e18d831233a9a5adb7e759ce3e086903b4ed1cb05169edd21ef` | self-recorded control-plane hash |
| `research/ml_extension/splits/authoritative_locked_test_manifest.json` | `9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb` | frozen locked manifest |
| `research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json` | `f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782` | formal development manifest |
| `research/ml_extension/splits/formal_budgeted_20260921/formal_train_manifest.json` | `32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1` | frozen TRAIN manifest |
| `research/ml_extension/splits/formal_budgeted_20260921/formal_validation_manifest.json` | `b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b` | frozen VALIDATION manifest |
| `artifacts/approvals/phase14_locked_evo2_20260922.json` | `4b619747a73942e56e15fef4040db1591760ee5a7813fb8f14fcc4740050dae7` | Phase 14 approval |
| `artifacts/phase14/phase14_locked_evo2_20260922.json` | `4dd9b9229c47d65491345e87b70a6f6739432c24a7585966f4aea97a9d115499` | immutable Phase 14 result |
| `research/runs/formal_cpu_20260922/phase14_locked_evo2/raw_predictions.jsonl` | `ae288252a3f1bfc8a1754b1626ea6ff91a041df9ff09daf07d1411a242ba2508` | raw predictions before label join |
| `research/runs/formal_cpu_20260922/phase14_locked_evo2/predictions_with_local_labels.jsonl` | `77cbbb48032ac7852ff09f93ea448d1e98ca21457843c1feda16f31e8dc530e7` | local joined evaluation |

The audit is read-only with respect to the protocol, manifests, Phase 14 approval, raw
predictions, joined predictions, thresholds, calibration, and final metrics.

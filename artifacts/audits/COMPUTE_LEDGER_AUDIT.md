# Compute ledger audit — 2026-09-22

Status: `RECONCILED_NO_EXACT_PROVIDER_BALANCE`. No remote compute was launched by this audit.

The `$7.17` value is retained as the earlier user-provided Phase 6 checkpoint basis. It is not reset at Phase 15. A later user-provided `$5.94` basis was recorded before the final 32-row Phase 6 tail; neither balance is provider-confirmed.

## Evidence classes

- **Provider-confirmed:** raw workspace billing snapshots and container inventories recorded by the repository artifacts. The fresh read-only check at `artifacts/audits/modal_no_spend_snapshot_20260922.json` again returned `active_containers=[]`, metered `$31.69808745`, and billed `$0.00`; the provider did not expose an exact remaining free-credit balance.
- **Metered deltas:** subtraction between two named provider snapshots. These are workspace movements, not invoices, and the final meter is non-monotonic because of adjustments.
- **App measurements:** rows, cache hits, remote wall time, calls, and resume counters recorded by the execution artifacts.
- **Rate estimates:** client/H100 wall-rate estimates. They are not provider bills.

## Subsequent workload ledger

| Workload | New rows | Cache rows | Remote seconds | Rate estimate USD |
|---|---:|---:|---:|---:|
| Phase 6 Evo2 tail | 32 | 3968 | 7776.964792 | $0.111328 |
| Phase 7 Nucleotide Transformer | 1568 | 2432 | 379.794382 | $0.782194 |
| Phase 7 Caduceus | 4000 | 0 | 646.733672 | $0.601805 |
| Phase 14 locked Evo2 | 946 | 0 | 1304.297864 | $1.431104601 |
| Phase 15 batch/resume smoke | 8 | 56 | 57.525624 | $0.063118 |

The separately recorded rate estimates total **$2.989549601**. Starting from the later `$5.94` user basis yields an indicative `$2.950450399` arithmetic only; it is not an exact remaining credit balance.

## Phase 15 correction

Phase 15 is a 64-row batch/resume smoke with 56 cache-reused rows and 8 fresh remote parity rows. The old Phase-6 `$7.17` balance must not be subtracted only by the Phase-15 `$0.063118` rate estimate. The prior `modal_billing_final` snapshot is preserved as raw provider evidence, while its `user_stated_pre_phase15_headroom_usd` arithmetic is superseded by this dated reconciliation.

## Limits

Exact free-credit headroom cannot be reconstructed from workspace metering alone. No value in this audit is used to authorize more paid work. See the JSON sidecar for source hashes and the explicit non-monotonic meter comparison.

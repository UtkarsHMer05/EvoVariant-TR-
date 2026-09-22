#!/usr/bin/env python3
"""Reconcile recorded compute evidence without querying or launching Modal."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/audits"


def read(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha256(relative: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / relative).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def money(value: Any) -> str:
    return format(Decimal(str(value)), "f")


def stdout_snapshot(value: dict[str, Any], source: str, label: str) -> dict[str, Any]:
    text = str(value.get("stdout", ""))
    metered = re.search(r"Metered Cost:\s+([0-9.]+)", text)
    billed = re.search(r"Billed Cost:\s+\$([0-9.]+)", text)
    return {
        "label": label,
        "source": source,
        "captured_at_utc": value.get("captured_at_utc"),
        "metered_cost_usd": money(metered.group(1)) if metered else None,
        "billed_cost_usd": money(billed.group(1)) if billed else None,
        "active_containers": value.get("active_containers"),
        "interpretation": "provider-confirmed workspace snapshot; not a per-run invoice",
    }


def exact_snapshot(value: dict[str, Any], source: str, label: str) -> dict[str, Any]:
    return {
        "label": label,
        "source": source,
        "captured_at_utc": value.get("captured_at_utc"),
        "metered_cost_usd": money(value.get("metered_cost", value.get("metered_cost_usd"))),
        "billed_cost_usd": money(value.get("billed_cost", value.get("billed_cost_usd"))),
        "active_containers": value.get("active_containers"),
        "adjustments": value.get("adjustments"),
        "interpretation": "provider-confirmed workspace snapshot; not a per-run invoice",
    }


def delta(before: str, after: str, scope: str, note: str) -> dict[str, Any]:
    return {
        "scope": scope,
        "before_metered_usd": before,
        "after_metered_usd": after,
        "observed_metered_delta_usd": money(Decimal(after) - Decimal(before)),
        "note": note,
    }


def main() -> int:
    phase6_approval = read("artifacts/approvals/formal_phase6_resume_20260922.json")
    phase6_tail_approval = read("artifacts/approvals/formal_phase6_par_resume_20260922.json")
    phase6_tail_preflight = read(
        "artifacts/phase6/formal_phase6_par_resume_preflight_20260922.json"
    )
    phase6_final = read("artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json")
    phase6_partial = read(
        "artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922_partial.json"
    )
    phase7 = read("artifacts/phase7/formal_budgeted_representation_20260922.json")
    phase14 = read("artifacts/phase14/phase14_locked_evo2_20260922.json")
    phase15 = read("artifacts/phase15/phase15_parity_smoke_validation_20260922.json")
    phase15_approval = read("artifacts/approvals/phase15_parity_smoke_20260922.json")
    phase19 = read("artifacts/phase19/modal_billing_final_20260922.json")

    initial_user = phase6_approval["cost_baseline"]["user_credit_evidence"]
    later_user = phase6_tail_approval["cost_baseline"]["user_credit_evidence"]
    phase7_before = stdout_snapshot(phase7["billing"]["before"], "artifacts/phase7/formal_budgeted_representation_20260922.json", "Phase 7 before")
    phase7_after = stdout_snapshot(phase7["billing"]["after"], "artifacts/phase7/formal_budgeted_representation_20260922.json", "Phase 7 after")
    phase14_before = exact_snapshot(phase14["cost"]["billing_before"]["summary"], "artifacts/phase14/phase14_locked_evo2_20260922.json", "Phase 14 before")
    phase14_before["captured_at_utc"] = phase14["cost"]["billing_before"].get("captured_at_utc")
    phase14_after = exact_snapshot(phase14["cost"]["billing_after"]["summary"], "artifacts/phase14/phase14_locked_evo2_20260922.json", "Phase 14 after")
    phase14_after["captured_at_utc"] = phase14["cost"]["billing_after"].get("captured_at_utc")
    phase15_before_metered = str(phase15_approval["cost_baseline"]["metered_cost_usd"])
    phase15_before_billed = str(phase15_approval["cost_baseline"]["billed_cost_usd"])
    phase15_before = {
        "label": "Phase 15 before",
        "source": "artifacts/approvals/phase15_parity_smoke_20260922.json",
        "captured_at_utc": phase15_approval["cost_baseline"]["captured_at_utc"],
        "metered_cost_usd": money(phase15_before_metered),
        "billed_cost_usd": money(phase15_before_billed),
        "active_containers": phase15_approval["cost_baseline"].get("active_containers"),
        "interpretation": "provider-confirmed workspace snapshot; not a per-run invoice",
    }
    phase15_after = exact_snapshot(phase15["billing_after"]["snapshot"], "artifacts/phase15/phase15_parity_smoke_validation_20260922.json", "Phase 15 after")
    phase15_after["active_containers"] = phase15["billing_after"].get("active_containers")
    final_snapshot = exact_snapshot(phase19["snapshot"], "artifacts/phase19/modal_billing_final_20260922.json", "Final no-spend snapshot")
    final_snapshot["active_containers"] = phase19.get("active_containers")

    workloads = [
        {
            "phase": "Phase 6 Evo2 tail",
            "new_rows": 32,
            "cache_hits": 3968,
            "remote_runtime_seconds": phase6_final["runtime"]["total_remote_wall_seconds"],
            "rate_estimate_usd": phase6_final["cost"]["cumulative_client_wall_rate_estimate_usd"],
            "source": "artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json",
            "interpretation": "Execution-specific tail estimate; the aggregate remote runtime includes the complete stored-shard resume.",
        },
        {
            "phase": "Phase 7 Nucleotide Transformer",
            "new_rows": 1568,
            "cache_hits": 2432,
            "remote_runtime_seconds": phase7["model_tracks"]["nucleotide_transformer"]["runtime_seconds"],
            "rate_estimate_usd": phase7["model_tracks"]["nucleotide_transformer"]["cost"]["estimated_client_wall_rate_usd"],
            "source": "artifacts/phase7/formal_budgeted_representation_20260922.json",
            "interpretation": "Client wall-rate estimate, not a provider invoice.",
        },
        {
            "phase": "Phase 7 Caduceus",
            "new_rows": 4000,
            "cache_hits": 0,
            "remote_runtime_seconds": phase7["model_tracks"]["caduceus"]["runtime_seconds"],
            "rate_estimate_usd": phase7["model_tracks"]["caduceus"]["cost"]["estimated_client_wall_rate_usd"],
            "source": "artifacts/phase7/formal_budgeted_representation_20260922.json",
            "interpretation": "Client wall-rate estimate, not a provider invoice.",
        },
        {
            "phase": "Phase 14 locked Evo2",
            "new_rows": 946,
            "cache_hits": 0,
            "remote_runtime_seconds": phase14["runtime"]["remote_runtime_seconds"],
            "rate_estimate_usd": phase14["cost"]["estimated_run_cost_usd"],
            "source": "artifacts/phase14/phase14_locked_evo2_20260922.json",
            "interpretation": "Direct H100 rate estimate for the immutable locked subgate; not a provider invoice.",
        },
        {
            "phase": "Phase 15 batch/resume smoke",
            "new_rows": phase15["initial_paid_execution"]["new_remote_records"],
            "cache_hits": phase15["initial_paid_execution"]["historical_cache_hits"],
            "remote_runtime_seconds": phase15["initial_paid_execution"]["remote_runtime_seconds"],
            "rate_estimate_usd": phase15["initial_paid_execution"]["estimated_cost_usd"],
            "source": "artifacts/phase15/phase15_parity_smoke_validation_20260922.json",
            "interpretation": "Direct client-wall-rate estimate for one fresh 8-row remote invocation; the resume added zero calls.",
        },
    ]
    total_rate_estimate = sum((Decimal(str(row["rate_estimate_usd"])) for row in workloads), Decimal("0"))
    later_headroom = Decimal(str(later_user["credits_left_usd"]))
    indicative_after_later = later_headroom - total_rate_estimate

    source_paths = sorted({
        "artifacts/approvals/formal_phase6_resume_20260922.json",
        "artifacts/approvals/formal_phase6_par_resume_20260922.json",
        "artifacts/approvals/formal_phase7_continuation_20260922.json",
        "artifacts/approvals/phase15_parity_smoke_20260922.json",
        "artifacts/phase6/formal_phase6_par_resume_preflight_20260922.json",
        "artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json",
        "artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922_partial.json",
        "artifacts/phase7/formal_budgeted_representation_20260922.json",
        "artifacts/phase14/phase14_locked_evo2_20260922.json",
        "artifacts/phase15/phase15_parity_smoke_validation_20260922.json",
        "artifacts/phase17/modal_billing_recheck_20260922.json",
        "artifacts/phase19/modal_billing_final_20260922.json",
    })
    payload = {
        "schema_version": "compute-ledger-audit-v2",
        "status": "RECONCILED_NO_EXACT_PROVIDER_BALANCE",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "no_new_remote_compute": True,
        "scientific_boundary": {
            "phase14_frozen": True,
            "locked_inference_rerun": False,
            "fine_tuning": False,
            "new_paid_work_in_audit": False,
        },
        "user_credit_snapshots": [
            {
                "label": "Earlier Phase 6 checkpoint basis",
                "source": "artifacts/approvals/formal_phase6_resume_20260922.json",
                "captured_at_utc": phase6_approval["cost_baseline"]["captured_at_utc"],
                "monthly_credits_usd": initial_user["monthly_credits_usd"],
                "credits_used_usd": initial_user["credits_used_usd"],
                "credits_left_usd": initial_user["credits_left_usd"],
                "meaning": "User-provided balance at the 3,232-row Phase 6 checkpoint; it is historical and is not a Phase 15 reset point.",
            },
            {
                "label": "Later Phase 6 tail checkpoint basis",
                "source": "artifacts/approvals/formal_phase6_par_resume_20260922.json",
                "captured_at_utc": phase6_tail_approval["cost_baseline"]["captured_at_utc"],
                "monthly_credits_usd": later_user["monthly_credits_usd"],
                "credits_used_usd": later_user["credits_used_usd"],
                "credits_left_usd": later_user["credits_left_usd"],
                "meaning": "Later user-provided basis before the final 32-row Phase 6 tail; it is not provider-confirmed.",
            },
        ],
        "provider_confirmed_workspace_snapshots": [
            phase6_tail_preflight["billing_before"],
            phase7_before,
            phase7_after,
            phase14_before,
            phase14_after,
            phase15_before,
            phase15_after,
            final_snapshot,
        ],
        "metered_deltas": [
            delta("30.46", "31.82", "Phase 7 before/after workspace snapshots", "Observed workspace meter movement during the Phase 7 artifact window; not a per-run invoice."),
            delta("31.82187443", "33.50187443", "Phase 14 paid-run baseline/after snapshot", "Recorded alongside the locked run; workspace-level and not an invoice for Phase 14 alone."),
            delta("33.59808745", "33.65808745", "Phase 15 approval/validation snapshots", "Observed workspace meter movement across the 8-row remote smoke; the direct app estimate remains separate."),
            delta("31.82187443", "33.59808745", "Phase 17 cross-phase comparison", "The recheck compares a prior Phase 14 baseline with a later workspace total; it is not attributable to one phase."),
            delta("33.65808745", "31.69808745", "Phase 15 validation to final no-spend snapshot", "Negative movement reflects provider adjustments/non-monotonic workspace totals, not a computed refund or negative run cost."),
        ],
        "app_specific_measurements_and_rate_estimates": workloads,
        "subsequent_rate_estimate_total_usd": money(total_rate_estimate),
        "indicative_user_basis_arithmetic": {
            "earlier_phase6_checkpoint_usd": money(initial_user["credits_left_usd"]),
            "later_pre_tail_checkpoint_usd": money(later_headroom),
            "post_later_checkpoint_rate_estimate_total_usd": money(total_rate_estimate),
            "indicative_after_later_checkpoint_usd": money(indicative_after_later),
            "provider_confirmed": False,
            "why_not_exact": "The provider summary exposes workspace meter totals and adjustments, not a remaining free-credit balance; the raw totals are non-monotonic.",
            "phase15_old_7_17_subtraction_is_invalid": True,
        },
        "overlap_and_exclusions": [
            {
                "source": "artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922_partial.json",
                "reported_rows": phase6_partial.get("cache", {}).get("total_cache_hit_records", 3232),
                "reported_rate_estimate_usd": phase6_partial.get("cost", {}).get("cumulative_client_wall_rate_estimate_usd", 7.219897),
                "treatment": "Historical overlapping pre-$7.17 evidence; not added to the post-snapshot total.",
            },
            {
                "source": "artifacts/phase19/modal_billing_final_20260922.json",
                "treatment": "Raw provider snapshot preserved; its old pre-Phase-15 arithmetic is superseded by this reconciliation because it resets the earlier $7.17 basis.",
            },
        ],
        "source_sha256": {path: sha256(path) for path in source_paths},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    json_path = OUT / "compute_ledger_audit_20260922.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# Compute ledger audit — 2026-09-22",
        "",
        f"Status: `{payload['status']}`. No remote compute was launched by this audit.",
        "",
        "The `$7.17` value is retained as the earlier user-provided Phase 6 checkpoint basis. It is not reset at Phase 15. A later user-provided `$5.94` basis was recorded before the final 32-row Phase 6 tail; neither balance is provider-confirmed.",
        "",
        "## Evidence classes",
        "",
        "- **Provider-confirmed:** raw workspace billing snapshots and container inventories recorded by the repository artifacts. The provider did not expose an exact remaining free-credit balance.",
        "- **Metered deltas:** subtraction between two named provider snapshots. These are workspace movements, not invoices, and the final meter is non-monotonic because of adjustments.",
        "- **App measurements:** rows, cache hits, remote wall time, calls, and resume counters recorded by the execution artifacts.",
        "- **Rate estimates:** client/H100 wall-rate estimates. They are not provider bills.",
        "",
        "## Subsequent workload ledger",
        "",
        "| Workload | New rows | Cache rows | Remote seconds | Rate estimate USD |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in workloads:
        md.append(f"| {row['phase']} | {row['new_rows']} | {row['cache_hits']} | {row['remote_runtime_seconds']} | ${row['rate_estimate_usd']} |")
    md.extend([
        "",
        f"The separately recorded rate estimates total **${money(total_rate_estimate)}**. Starting from the later `$5.94` user basis yields an indicative `${money(indicative_after_later)}` arithmetic only; it is not an exact remaining credit balance.",
        "",
        "## Phase 15 correction",
        "",
        "Phase 15 is a 64-row batch/resume smoke with 56 cache-reused rows and 8 fresh remote parity rows. The old Phase-6 `$7.17` balance must not be subtracted only by the Phase-15 `$0.063118` rate estimate. The prior `modal_billing_final` snapshot is preserved as raw provider evidence, while its `user_stated_pre_phase15_headroom_usd` arithmetic is superseded by this dated reconciliation.",
        "",
        "## Limits",
        "",
        "Exact free-credit headroom cannot be reconstructed from workspace metering alone. No value in this audit is used to authorize more paid work. See the JSON sidecar for source hashes and the explicit non-monotonic meter comparison.",
        "",
    ])
    (OUT / "COMPUTE_LEDGER_AUDIT.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "rate_estimate_total_usd": money(total_rate_estimate), "output": str(json_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

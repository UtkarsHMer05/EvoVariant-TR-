#!/usr/bin/env python3
"""Evaluate deployed Modal Evo2 endpoint on BRCA1 benchmark rows.

This script does not modify project source code. It performs external evaluation by
sending HTTP requests to the deployed webhook endpoint and computing classification
and latency metrics.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


DEFAULT_URL = "https://utkarshmer05--variant-analysis-evo2-evo2model-analyze-si-b52940.modal.run"
DEFAULT_XLSX = "evo2-backend/evo2/notebooks/brca1/41586_2018_461_MOESM3_ESM.xlsx"


@dataclass
class EvalMetrics:
    total_candidates: int
    successful_calls: int
    failed_calls: int
    eval_wall_time_s: float
    avg_latency_s: float
    median_latency_s: float
    p95_latency_s: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auroc_from_delta: float
    confusion_matrix_tn_fp_fn_tp: list[list[int]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Modal Evo2 endpoint on BRCA1 variants")
    parser.add_argument("--url", default=DEFAULT_URL, help="Modal webhook URL for analyze_single_variant")
    parser.add_argument("--xlsx", default=DEFAULT_XLSX, help="Path to BRCA1 Excel dataset")
    parser.add_argument("--limit", type=int, default=500, help="Number of rows to evaluate (default: 500)")
    parser.add_argument("--genome", default="hg19", help="Genome build sent to endpoint")
    parser.add_argument("--chromosome", default="chr17", help="Chromosome sent to endpoint")
    parser.add_argument("--timeout", type=int, default=180, help="HTTP timeout per request in seconds")
    parser.add_argument(
        "--output-dir",
        default="evaluation/results/latest",
        help="Directory for metrics, CSVs, plots, and tensorboard logs",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50,
        help="Print progress every N requests",
    )
    parser.add_argument(
        "--no-tensorboard",
        action="store_true",
        help="Disable TensorBoard log generation",
    )
    return parser.parse_args()


def load_subset(xlsx_path: str, limit: int) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path, header=2)
    df = df[
        [
            "chromosome",
            "position (hg19)",
            "reference",
            "alt",
            "function.score.mean",
            "func.class",
        ]
    ].rename(
        columns={
            "chromosome": "chrom",
            "position (hg19)": "pos",
            "reference": "ref",
            "alt": "alt",
            "function.score.mean": "score",
            "func.class": "class",
        }
    )

    # Match project logic: merge FUNC and INT into FUNC/INT.
    df["class"] = df["class"].replace(["FUNC", "INT"], "FUNC/INT")

    subset = df.iloc[:limit].copy()
    subset = subset[
        subset["alt"].astype(str).str.len().eq(1)
        & subset["alt"].astype(str).str.upper().isin(list("ATGC"))
        & subset["pos"].notna()
    ].copy()

    return subset


def run_eval(
    args: argparse.Namespace, subset: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, float, str | None]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    fatal_error: str | None = None

    records = subset.to_dict(orient="records")
    start_all = time.time()

    for i, rec in enumerate(records, start=1):
        payload = {
            "variant_position": int(rec["pos"]),
            "alternative": str(rec["alt"]).upper(),
            "genome": args.genome,
            "chromosome": args.chromosome,
        }

        t0 = time.time()
        try:
            resp = requests.post(args.url, json=payload, timeout=args.timeout)
            latency = time.time() - t0

            if resp.status_code == 200:
                out = resp.json()
                pred_text = str(out.get("prediction", ""))
                y_pred = 1 if "pathogenic" in pred_text.lower() else 0
                y_true = 1 if str(rec["class"]) == "LOF" else 0

                rows.append(
                    {
                        "index": i,
                        "position": int(rec["pos"]),
                        "alt": str(rec["alt"]).upper(),
                        "true_class": str(rec["class"]),
                        "y_true": y_true,
                        "prediction_text": pred_text,
                        "y_pred": y_pred,
                        "delta_score": float(out.get("delta_score")),
                        "classification_confidence": float(out.get("classification_confidence")),
                        "latency_s": latency,
                    }
                )
            else:
                err_msg = resp.text[:500]
                failures.append(
                    {
                        "index": i,
                        "status": resp.status_code,
                        "error": err_msg,
                        "position": int(rec["pos"]),
                        "alt": str(rec["alt"]).upper(),
                    }
                )

                # Stop early if workspace spending limit is reached.
                if resp.status_code == 429 and "billing cycle spend limit reached" in err_msg.lower():
                    fatal_error = (
                        "Modal webhook is rate-limited due to workspace billing cycle spend limit reached. "
                        "Evaluation cannot proceed until billing limit is reset or increased."
                    )
                    print(f"\nFATAL: {fatal_error}")
                    break
        except Exception as exc:
            failures.append(
                {
                    "index": i,
                    "status": "EXC",
                    "error": str(exc)[:500],
                    "position": int(rec["pos"]),
                    "alt": str(rec["alt"]).upper(),
                }
            )

        if args.progress_every > 0 and i % args.progress_every == 0:
            elapsed = time.time() - start_all
            print(
                f"progress {i}/{len(records)} | success={len(rows)} fail={len(failures)} | elapsed_s={elapsed:.1f}"
            )

    elapsed_all = time.time() - start_all
    return pd.DataFrame(rows), pd.DataFrame(failures), elapsed_all, fatal_error


def build_diagnostics(
    total: int,
    pred_df: pd.DataFrame,
    failures_df: pd.DataFrame,
    elapsed_all: float,
    fatal_error: str | None,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    top_errors: list[dict[str, Any]] = []

    if not failures_df.empty:
        status_counts = (
            failures_df["status"].astype(str).value_counts().to_dict()
        )

        error_counts = failures_df["error"].astype(str).value_counts().head(5)
        top_errors = [
            {"error": err, "count": int(cnt)}
            for err, cnt in error_counts.items()
        ]

    return {
        "total_candidates": int(total),
        "successful_calls": int(len(pred_df)),
        "failed_calls": int(len(failures_df)),
        "eval_wall_time_s": float(elapsed_all),
        "fatal_error": fatal_error,
        "status_counts": status_counts,
        "top_errors": top_errors,
    }


def compute_metrics(pred_df: pd.DataFrame, failures_df: pd.DataFrame, elapsed_all: float, total: int) -> EvalMetrics:
    if pred_df.empty:
        raise RuntimeError("No successful calls, cannot compute metrics.")

    y_true = pred_df["y_true"].astype(int)
    y_pred = pred_df["y_pred"].astype(int)
    y_score = -pred_df["delta_score"].astype(float)

    cm = confusion_matrix(y_true, y_pred)

    return EvalMetrics(
        total_candidates=int(total),
        successful_calls=int(len(pred_df)),
        failed_calls=int(len(failures_df)),
        eval_wall_time_s=float(elapsed_all),
        avg_latency_s=float(pred_df["latency_s"].mean()),
        median_latency_s=float(pred_df["latency_s"].median()),
        p95_latency_s=float(pred_df["latency_s"].quantile(0.95)),
        accuracy=float(accuracy_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1_score=float(f1_score(y_true, y_pred, zero_division=0)),
        auroc_from_delta=float(roc_auc_score(y_true, y_score)),
        confusion_matrix_tn_fp_fn_tp=[[int(cm[0, 0]), int(cm[0, 1])], [int(cm[1, 0]), int(cm[1, 1])]],
    )


def save_plots(pred_df: pd.DataFrame, out_dir: Path) -> None:
    sns.set_theme(style="whitegrid")

    # Latency histogram
    plt.figure(figsize=(7, 4))
    sns.histplot(pred_df["latency_s"], bins=30, kde=True, color="#2a9d8f")
    plt.title("Latency Distribution")
    plt.xlabel("Latency (seconds)")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(out_dir / "latency_histogram.png", dpi=180)
    plt.close()

    # Latency boxplot
    plt.figure(figsize=(6, 3.5))
    sns.boxplot(x=pred_df["latency_s"], color="#457b9d")
    plt.title("Latency Boxplot")
    plt.xlabel("Latency (seconds)")
    plt.tight_layout()
    plt.savefig(out_dir / "latency_boxplot.png", dpi=180)
    plt.close()

    # Confusion matrix heatmap
    cm = confusion_matrix(pred_df["y_true"], pred_df["y_pred"])
    plt.figure(figsize=(5, 4))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Pred: FUNC/INT", "Pred: LOF"],
        yticklabels=["True: FUNC/INT", "True: LOF"],
    )
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(out_dir / "confusion_matrix.png", dpi=180)
    plt.close()

    # ROC curve
    fpr, tpr, _ = roc_curve(pred_df["y_true"], -pred_df["delta_score"])
    auroc = roc_auc_score(pred_df["y_true"], -pred_df["delta_score"])
    plt.figure(figsize=(5.5, 4.5))
    plt.plot(fpr, tpr, label=f"AUROC = {auroc:.3f}", color="#e76f51")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_dir / "roc_curve.png", dpi=180)
    plt.close()

    # Precision-recall curve
    precision, recall, _ = precision_recall_curve(pred_df["y_true"], -pred_df["delta_score"])
    plt.figure(figsize=(5.5, 4.5))
    plt.plot(recall, precision, color="#8d99ae")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.tight_layout()
    plt.savefig(out_dir / "precision_recall_curve.png", dpi=180)
    plt.close()


def save_tensorboard(pred_df: pd.DataFrame, metrics: EvalMetrics, out_dir: Path) -> str | None:
    try:
        from torch.utils.tensorboard import SummaryWriter
    except Exception:
        return None

    tb_dir = out_dir / "tensorboard"
    writer = SummaryWriter(log_dir=str(tb_dir))

    scalar_dict = {
        "metrics/accuracy": metrics.accuracy,
        "metrics/precision": metrics.precision,
        "metrics/recall": metrics.recall,
        "metrics/f1_score": metrics.f1_score,
        "metrics/auroc": metrics.auroc_from_delta,
        "latency/avg_s": metrics.avg_latency_s,
        "latency/median_s": metrics.median_latency_s,
        "latency/p95_s": metrics.p95_latency_s,
    }

    for tag, value in scalar_dict.items():
        writer.add_scalar(tag, value, 0)

    writer.add_histogram("latency/distribution", pred_df["latency_s"].values, 0)
    writer.add_histogram("scores/delta_score", pred_df["delta_score"].values, 0)

    writer.flush()
    writer.close()
    return str(tb_dir)


def write_summary(metrics: EvalMetrics, out_dir: Path, url: str, xlsx: str) -> None:
    lines = [
        "Modal Endpoint Evaluation Summary",
        "=" * 34,
        f"endpoint_url: {url}",
        f"dataset: {xlsx}",
        f"total_candidates: {metrics.total_candidates}",
        f"successful_calls: {metrics.successful_calls}",
        f"failed_calls: {metrics.failed_calls}",
        f"eval_wall_time_s: {metrics.eval_wall_time_s:.2f}",
        f"avg_latency_s: {metrics.avg_latency_s:.4f}",
        f"median_latency_s: {metrics.median_latency_s:.4f}",
        f"p95_latency_s: {metrics.p95_latency_s:.4f}",
        f"accuracy: {metrics.accuracy:.6f}",
        f"precision: {metrics.precision:.6f}",
        f"recall: {metrics.recall:.6f}",
        f"f1_score: {metrics.f1_score:.6f}",
        f"auroc_from_delta: {metrics.auroc_from_delta:.6f}",
        f"confusion_matrix_tn_fp_fn_tp: {metrics.confusion_matrix_tn_fp_fn_tp}",
    ]
    (out_dir / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_no_success_summary(diagnostics: dict[str, Any], out_dir: Path, url: str, xlsx: str) -> None:
    lines = [
        "Modal Endpoint Evaluation Summary (No Successful Calls)",
        "=" * 53,
        f"endpoint_url: {url}",
        f"dataset: {xlsx}",
        f"total_candidates: {diagnostics['total_candidates']}",
        f"successful_calls: {diagnostics['successful_calls']}",
        f"failed_calls: {diagnostics['failed_calls']}",
        f"eval_wall_time_s: {diagnostics['eval_wall_time_s']:.2f}",
    ]

    if diagnostics.get("fatal_error"):
        lines.append(f"fatal_error: {diagnostics['fatal_error']}")

    status_counts = diagnostics.get("status_counts", {})
    if status_counts:
        lines.append("status_counts: " + json.dumps(status_counts))

    top_errors = diagnostics.get("top_errors", [])
    if top_errors:
        lines.append("top_errors:")
        for row in top_errors:
            lines.append(f"- count={row['count']} error={row['error']}")

    lines.extend(
        [
            "",
            "No metrics/plots were generated because there were zero successful responses.",
            "Check failures.csv and diagnostics.json for details.",
        ]
    )

    (out_dir / "summary_no_success.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    subset = load_subset(args.xlsx, args.limit)
    pred_df, failures_df, elapsed_all, fatal_error = run_eval(args, subset)

    # Persist raw structured outputs first (always).
    pred_df.to_csv(out_dir / "predictions.csv", index=False)
    failures_df.to_csv(out_dir / "failures.csv", index=False)

    diagnostics = build_diagnostics(
        total=len(subset),
        pred_df=pred_df,
        failures_df=failures_df,
        elapsed_all=elapsed_all,
        fatal_error=fatal_error,
    )
    with open(out_dir / "diagnostics.json", "w", encoding="utf-8") as fp:
        json.dump(diagnostics, fp, indent=2)

    if pred_df.empty:
        write_no_success_summary(diagnostics, out_dir, args.url, args.xlsx)
        print("\nNo successful calls. Saved diagnostics only.")
        print(f"Saved outputs in: {out_dir}")
        print("Generated files:")
        print("- diagnostics.json")
        print("- summary_no_success.txt")
        print("- predictions.csv")
        print("- failures.csv")
        return

    # Success path: compute metrics and visual outputs.
    metrics = compute_metrics(pred_df, failures_df, elapsed_all, total=len(subset))

    with open(out_dir / "metrics.json", "w", encoding="utf-8") as fp:
        json.dump(asdict(metrics), fp, indent=2)
    write_summary(metrics, out_dir, args.url, args.xlsx)

    # Visual outputs
    save_plots(pred_df, out_dir)

    # Optional TensorBoard logs
    tb_dir = None
    if not args.no_tensorboard:
        tb_dir = save_tensorboard(pred_df, metrics, out_dir)

    print("\n=== FINAL METRICS ===")
    print(json.dumps(asdict(metrics), indent=2))
    print(f"\nSaved outputs in: {out_dir}")
    print("Generated files:")
    print("- metrics.json")
    print("- summary.txt")
    print("- predictions.csv")
    print("- failures.csv")
    print("- confusion_matrix.png")
    print("- roc_curve.png")
    print("- precision_recall_curve.png")
    print("- latency_histogram.png")
    print("- latency_boxplot.png")

    if tb_dir:
        print(f"- TensorBoard logs: {tb_dir}")
        print(
            "View TensorBoard with: "
            f"tensorboard --logdir {tb_dir} --port 6006"
        )
    elif not args.no_tensorboard:
        print(
            "- TensorBoard logs: not generated (missing dependency: torch.utils.tensorboard). "
            "Install PyTorch to enable this."
        )


if __name__ == "__main__":
    main()

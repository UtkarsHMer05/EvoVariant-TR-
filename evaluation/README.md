# Evaluation and Visualization Guide

This folder contains a standalone evaluator that computes quality and latency metrics
against the deployed Modal endpoint without modifying project source code.

## Script

- `evaluation/evaluate_modal_endpoint.py`

## What it saves

Under your chosen output directory (default: `evaluation/results/latest`):

- `metrics.json`
- `summary.txt`
- `predictions.csv`
- `failures.csv`
- `confusion_matrix.png`
- `roc_curve.png`
- `precision_recall_curve.png`
- `latency_histogram.png`
- `latency_boxplot.png`
- `tensorboard/` (if tensorboard is available and enabled)

## Run command (full 500)

```bash
/Users/utkarshkhajuria/Downloads/variant-analysis-evo2/.venv/bin/python evaluation/evaluate_modal_endpoint.py \
  --url "https://utkarshmer05--variant-analysis-evo2-evo2model-analyze-si-b52940.modal.run" \
  --xlsx "evo2-backend/evo2/notebooks/brca1/41586_2018_461_MOESM3_ESM.xlsx" \
  --limit 500 \
  --output-dir "evaluation/results/final_500"
```

## Fast test command (smaller run)

```bash
/Users/utkarshkhajuria/Downloads/variant-analysis-evo2/.venv/bin/python evaluation/evaluate_modal_endpoint.py \
  --limit 50 \
  --output-dir "evaluation/results/quick_50"
```

## View plots

Open the PNG files in the output directory.

## View TensorBoard (optional)

```bash
tensorboard --logdir evaluation/results/final_500/tensorboard --port 6006
```

Then open:

- http://localhost:6006

## Notes

- Metric values depend on the endpoint behavior at run time.
- Full 500-run can take substantial time depending on container warm/cold starts.

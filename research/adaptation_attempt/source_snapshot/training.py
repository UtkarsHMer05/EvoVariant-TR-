# Evidence snapshot from the incomplete adaptation branch.
# Source: research/posthoc-foundation-adaptation
# Snapshot commit: 196393636b069dfeaa8dbd43f41b543d0b20d91a
# Purpose: experimental fine-tuning evidence; not part of frozen baseline inference

"""Minimal resumable training loop for paired adaptation."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .data import VariantRow, paired_sequences
from .metrics import binary_metrics
from .models import tokenize_sequences


@dataclass(frozen=True)
class TrainConfig:
    batch_size: int = 2
    gradient_accumulation_steps: int = 1
    max_length: int = 8192
    epochs: int = 3
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    amp: bool = True


def _batches(
    rows: list[VariantRow], batch_size: int, *, shuffle: bool = False
) -> Iterator[list[VariantRow]]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    indices = list(range(len(rows)))
    if shuffle:
        import torch

        indices = torch.randperm(len(rows)).tolist()
    for start in range(0, len(indices), batch_size):
        yield [rows[index] for index in indices[start : start + batch_size]]


def _batch_inputs(
    tokenizer: Any,
    fasta: Any,
    rows: list[VariantRow],
    *,
    max_length: int,
    device: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    pairs = [paired_sequences(fasta, row, max_length) for row in rows]
    return (
        tokenize_sequences(
            tokenizer, [pair.reference for pair in pairs], max_length=max_length, device=device
        ),
        tokenize_sequences(
            tokenizer, [pair.alternate for pair in pairs], max_length=max_length, device=device
        ),
        tokenize_sequences(
            tokenizer, [pair.reference_rc for pair in pairs], max_length=max_length, device=device
        ),
        tokenize_sequences(
            tokenizer, [pair.alternate_rc for pair in pairs], max_length=max_length, device=device
        ),
    )


def _autocast(device: str, enabled: bool) -> Any:
    import torch

    return torch.autocast(
        device_type="cuda" if device.startswith("cuda") else "cpu", enabled=enabled
    )


def train_epoch(
    model: Any,
    tokenizer: Any,
    fasta: Any,
    rows: list[VariantRow],
    optimizer: Any,
    *,
    config: TrainConfig | None = None,
    device: str = "cuda",
) -> float:
    import torch

    config = config or TrainConfig()
    if not rows:
        raise ValueError("training rows must be non-empty")
    if config.gradient_accumulation_steps < 1:
        raise ValueError("gradient_accumulation_steps must be positive")
    model.train()
    if not any(parameter.requires_grad for parameter in model.backbone.parameters()):
        model.backbone.eval()
    positives = sum(row.label for row in rows)
    negatives = len(rows) - positives
    if not positives or not negatives:
        raise ValueError("training fold must contain both classes")
    pos_weight = torch.tensor(
        [negatives / positives if positives else 1.0],
        dtype=torch.float32,
        device=device,
    )
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    total_loss = 0.0
    scaler = torch.cuda.amp.GradScaler(enabled=config.amp and device.startswith("cuda"))
    batches = list(_batches(rows, config.batch_size, shuffle=True))
    for batch_index, batch_rows in enumerate(batches):
        reference, alternate, reference_rc, alternate_rc = _batch_inputs(
            tokenizer, fasta, batch_rows, max_length=config.max_length, device=device
        )
        labels = torch.tensor([row.label for row in batch_rows], dtype=torch.float32, device=device)
        if batch_index % config.gradient_accumulation_steps == 0:
            optimizer.zero_grad(set_to_none=True)
        with _autocast(device, config.amp):
            logits = model(reference, alternate, reference_rc, alternate_rc)
            loss = criterion(logits, labels)
        accumulation_start = batch_index - batch_index % config.gradient_accumulation_steps
        group_size = min(config.gradient_accumulation_steps, len(batches) - accumulation_start)
        scaler.scale(loss / group_size).backward()
        if (batch_index + 1) % config.gradient_accumulation_steps == 0 or batch_index == len(
            batches
        ) - 1:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            scaler.step(optimizer)
            scaler.update()
        total_loss += float(loss.detach().cpu()) * len(batch_rows)
    return total_loss / len(rows)


def evaluate(
    model: Any,
    tokenizer: Any,
    fasta: Any,
    rows: list[VariantRow],
    *,
    config: TrainConfig | None = None,
    device: str = "cuda",
) -> tuple[dict[str, Any], list[float]]:
    import torch

    config = config or TrainConfig()
    model.eval()
    labels: list[int] = []
    scores: list[float] = []
    with torch.no_grad():
        for batch_rows in _batches(rows, config.batch_size):
            reference, alternate, reference_rc, alternate_rc = _batch_inputs(
                tokenizer, fasta, batch_rows, max_length=config.max_length, device=device
            )
            logits = model(reference, alternate, reference_rc, alternate_rc)
            scores.extend(torch.sigmoid(logits).detach().cpu().tolist())
            labels.extend(row.label for row in batch_rows)
    return binary_metrics(labels, scores), scores

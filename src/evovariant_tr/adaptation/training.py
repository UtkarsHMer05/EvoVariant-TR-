"""Minimal resumable training loop for paired adaptation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data import VariantRow, paired_sequences
from .metrics import binary_metrics
from .models import tokenize_sequences


@dataclass(frozen=True)
class TrainConfig:
    batch_size: int = 2
    max_length: int = 8192
    epochs: int = 3
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    amp: bool = True


def _batches(rows: list[VariantRow], batch_size: int):
    for start in range(0, len(rows), batch_size):
        yield rows[start : start + batch_size]


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
        tokenize_sequences(tokenizer, [pair.reference for pair in pairs], max_length=max_length, device=device),
        tokenize_sequences(tokenizer, [pair.alternate for pair in pairs], max_length=max_length, device=device),
        tokenize_sequences(tokenizer, [pair.reference_rc for pair in pairs], max_length=max_length, device=device),
        tokenize_sequences(tokenizer, [pair.alternate_rc for pair in pairs], max_length=max_length, device=device),
    )


def _autocast(device: str, enabled: bool):
    import torch

    return torch.autocast(device_type="cuda" if device.startswith("cuda") else "cpu", enabled=enabled)


def train_epoch(
    model: Any,
    tokenizer: Any,
    fasta: Any,
    rows: list[VariantRow],
    optimizer: Any,
    *,
    config: TrainConfig = TrainConfig(),
    device: str = "cuda",
) -> float:
    import torch

    model.train()
    positives = sum(row.label for row in rows)
    negatives = len(rows) - positives
    pos_weight = torch.tensor(
        [negatives / positives if positives else 1.0],
        dtype=torch.float32,
        device=device,
    )
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    total_loss = 0.0
    scaler = torch.amp.GradScaler("cuda", enabled=config.amp and device.startswith("cuda"))
    for batch_rows in _batches(rows, config.batch_size):
        reference, alternate, reference_rc, alternate_rc = _batch_inputs(
            tokenizer, fasta, batch_rows, max_length=config.max_length, device=device
        )
        labels = torch.tensor([row.label for row in batch_rows], dtype=torch.float32, device=device)
        optimizer.zero_grad(set_to_none=True)
        with _autocast(device, config.amp):
            logits = model(reference, alternate, reference_rc, alternate_rc)
            loss = criterion(logits, labels)
        scaler.scale(loss).backward()
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
    config: TrainConfig = TrainConfig(),
    device: str = "cuda",
) -> tuple[dict[str, Any], list[float]]:
    import torch

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


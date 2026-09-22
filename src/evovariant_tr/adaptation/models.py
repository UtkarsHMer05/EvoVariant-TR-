"""Pinned Hugging Face backbones and paired ref/alt classification head."""

from __future__ import annotations

import re
from typing import Any

MODEL_IDS = {
    "caduceus": "kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16",
    "nucleotide_transformer": "InstaDeepAI/nucleotide-transformer-v2-500m-multi-species",
}
MODEL_REVISIONS = {
    "caduceus": "b0477522ac5d044ad03578aa724ec8e4bdbd405b",
    "nucleotide_transformer": "06615c1660c892fc199840c18123f8385b3542a8",
}


def load_backbone(
    model_key: str,
    *,
    device: str = "cuda",
    cache_dir: str | None = None,
) -> tuple[Any, Any, int]:
    """Load a pinned model and tokenizer; network/model code stays explicit."""
    if model_key not in MODEL_IDS:
        raise ValueError(f"unknown adaptation model: {model_key}")
    try:
        from transformers import AutoModelForMaskedLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("adaptation dependencies are not installed") from exc
    kwargs = {
        "revision": MODEL_REVISIONS[model_key],
        "trust_remote_code": True,
    }
    if cache_dir:
        kwargs["cache_dir"] = cache_dir
    tokenizer = AutoTokenizer.from_pretrained(MODEL_IDS[model_key], **kwargs)
    model = AutoModelForMaskedLM.from_pretrained(MODEL_IDS[model_key], **kwargs)
    model.to(device)
    model.train()
    hidden_size = getattr(model.config, "hidden_size", None) or getattr(
        model.config, "d_model", None
    )
    if hidden_size is None:
        raise RuntimeError("backbone config did not expose hidden_size or d_model")
    return tokenizer, model, int(hidden_size)


def tokenize_sequences(
    tokenizer: Any,
    sequences: list[str],
    *,
    max_length: int,
    device: str,
) -> dict[str, Any]:
    encoded = tokenizer(
        sequences,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    return {name: value.to(device) for name, value in encoded.items()}


def _last_hidden(outputs: Any) -> Any:
    hidden = getattr(outputs, "last_hidden_state", None)
    if hidden is not None:
        return hidden
    states = getattr(outputs, "hidden_states", None)
    if states:
        return states[-1]
    raise RuntimeError("backbone output did not contain hidden states")


def _mean_pool(hidden: Any, mask: Any) -> Any:
    weights = mask.to(hidden.dtype).unsqueeze(-1)
    return (hidden * weights).sum(dim=1) / weights.sum(dim=1).clamp_min(1)


class PairedClassifier:
    """Torch module kept as a class factory to avoid importing torch locally."""

    @staticmethod
    def build(backbone: Any, hidden_size: int, dropout: float = 0.1) -> Any:
        import torch
        from torch import nn

        class _Head(nn.Module):  # type: ignore[misc]
            def __init__(self) -> None:
                super().__init__()
                self.backbone = backbone
                self.classifier = nn.Sequential(
                    nn.LayerNorm(hidden_size * 4),
                    nn.Dropout(dropout),
                    nn.Linear(hidden_size * 4, 1),
                )

            def encode(self, encoded: dict[str, Any]) -> Any:
                outputs = self.backbone(
                    **encoded,
                    output_hidden_states=True,
                    return_dict=True,
                )
                mask = encoded.get("attention_mask")
                if mask is None:
                    mask = torch.ones(
                        outputs.last_hidden_state.shape[:2],
                        dtype=torch.long,
                        device=outputs.last_hidden_state.device,
                    )
                return _mean_pool(_last_hidden(outputs), mask)

            def pair_logits(self, reference: dict[str, Any], alternate: dict[str, Any]) -> Any:
                reference_embedding = self.encode(reference)
                alternate_embedding = self.encode(alternate)
                delta = alternate_embedding - reference_embedding
                features = torch.cat(
                    [reference_embedding, alternate_embedding, delta, delta.abs()], dim=-1
                )
                return self.classifier(features).squeeze(-1)

            def forward(
                self,
                reference: dict[str, Any],
                alternate: dict[str, Any],
                reference_rc: dict[str, Any] | None = None,
                alternate_rc: dict[str, Any] | None = None,
            ) -> Any:
                logits = self.pair_logits(reference, alternate)
                if reference_rc is not None and alternate_rc is not None:
                    logits = (logits + self.pair_logits(reference_rc, alternate_rc)) / 2
                return logits

        return _Head()


def configure_trainable(model: Any, regime: str) -> tuple[int, int]:
    """Freeze or unfreeze the pinned backbone while keeping the task head trainable."""
    backbone = model.backbone
    backbone.requires_grad_(False)
    if regime == "full":
        backbone.requires_grad_(True)
    elif regime in {"partial_small", "partial_large"}:
        layer_ids = {
            int(match.group(1))
            for name, _ in backbone.named_parameters()
            if (match := re.search(r"(?:^|\.)(?:layers|blocks)\.(\d+)(?:\.|$)", name))
        }
        if not layer_ids:
            raise RuntimeError("could not locate backbone layer blocks for partial fine-tuning")
        count = min(len(layer_ids), 4 if regime == "partial_small" else 8)
        first = sorted(layer_ids)[-count]
        for name, parameter in backbone.named_parameters():
            match = re.search(r"(?:^|\.)(?:layers|blocks)\.(\d+)(?:\.|$)", name)
            if match and int(match.group(1)) >= first:
                parameter.requires_grad_(True)
    elif regime != "frozen_head_only":
        raise ValueError(f"unknown fine-tuning regime: {regime}")
    total = sum(parameter.numel() for parameter in model.parameters())
    trainable = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    return total, trainable


def finite_tensor(value: Any) -> bool:
    import torch

    return bool(torch.isfinite(value).all().item())

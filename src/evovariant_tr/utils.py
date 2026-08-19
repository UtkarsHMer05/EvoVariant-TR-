"""Utility functions for EvoVariant-TR."""

from __future__ import annotations

import hashlib


def deterministic_hash(data: str) -> float:
    """Generate a deterministic float hash from a string in [0, 1)."""
    h = hashlib.sha256(data.encode()).hexdigest()
    val = int(h[:16], 16)
    return val / 0xFFFFFFFFFFFFFFFFFFFF


def normalize_gene_symbol(gene: str | None) -> str:
    """Normalize a gene symbol to uppercase, handling None and dashes."""
    if not gene or gene == "-" or gene == "NA":
        return "UNKNOWN"
    return gene.upper().replace(";", "|").split("|")[0].strip()


def format_variant_identity(chrom: str, start: int, ref: str, alt: str) -> str:
    """Format a variant identity in standard notation."""
    return f"{chrom}:g.{start}{ref}>{alt}"
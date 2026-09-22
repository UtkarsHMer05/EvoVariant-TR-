"""Research-only post-hoc adaptation pipeline."""

from .data import (
    EXPECTED_MANIFEST_SHA256,
    FORMAL_RECORD_COUNT,
    VariantRow,
    load_formal_rows,
    verify_formal_data,
)

PREDECLARED_SEEDS = (42, 1337, 2026)


def selection_seed_allowed(seed: int, primary_seed: int, robustness: bool = False) -> bool:
    if robustness:
        return seed in PREDECLARED_SEEDS and seed != primary_seed
    return seed == primary_seed

__all__ = [
    "EXPECTED_MANIFEST_SHA256",
    "FORMAL_RECORD_COUNT",
    "PREDECLARED_SEEDS",
    "VariantRow",
    "load_formal_rows",
    "selection_seed_allowed",
    "verify_formal_data",
]

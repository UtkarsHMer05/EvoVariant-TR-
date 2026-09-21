"""Canonical internal variant representation for all research routes."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, field_validator


def normalize_chromosome(value: str) -> str:
    """Return the UCSC-compatible chromosome spelling used by the API."""
    normalized = value.strip()
    if not normalized:
        raise ValueError("chromosome must be non-empty")
    return normalized if normalized.startswith("chr") else f"chr{normalized}"


@dataclass(frozen=True)
class CanonicalVariant:
    """A normalized GRCh38 variant identity used at scientific boundaries."""

    assembly: str
    chromosome: str
    position_1based: int
    reference: str
    alternate: str

    def __post_init__(self) -> None:
        if self.assembly != "GRCh38":
            raise ValueError("the frozen research protocol requires GRCh38")
        if self.position_1based < 1:
            raise ValueError("position_1based must be >= 1")
        if not self.chromosome:
            raise ValueError("chromosome must be non-empty")
        if not self.reference or not self.alternate:
            raise ValueError("reference and alternate alleles must be non-empty")
        if any(base not in "ACGT" for base in (self.reference + self.alternate).upper()):
            raise ValueError("research alleles must contain only A/C/G/T")
        if self.reference.upper() == self.alternate.upper():
            raise ValueError("reference and alternate alleles must differ")

    @property
    def normalized_variant_id(self) -> str:
        return (
            f"{self.assembly}:{self.chromosome}:{self.position_1based}:"
            f"{self.reference}>{self.alternate}"
        )

    @property
    def is_snv(self) -> bool:
        return len(self.reference) == 1 and len(self.alternate) == 1


class VariantPayload(BaseModel):
    """Strict transport-independent payload for API and batch contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assembly: str = "GRCh38"
    chromosome: str
    position_1based: int
    reference: str
    alternate: str

    @field_validator("assembly")
    @classmethod
    def validate_assembly(cls, value: str) -> str:
        if value != "GRCh38":
            raise ValueError("assembly must be GRCh38")
        return value

    @field_validator("chromosome")
    @classmethod
    def validate_chromosome(cls, value: str) -> str:
        return normalize_chromosome(value)

    @field_validator("reference", "alternate")
    @classmethod
    def validate_allele(cls, value: str) -> str:
        normalized = value.upper()
        if not normalized or any(base not in "ACGT" for base in normalized):
            raise ValueError("alleles must contain only A/C/G/T")
        return normalized

    def canonical(self) -> CanonicalVariant:
        return CanonicalVariant(
            assembly=self.assembly,
            chromosome=self.chromosome,
            position_1based=self.position_1based,
            reference=self.reference,
            alternate=self.alternate,
        )

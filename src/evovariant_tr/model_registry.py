"""Schema-validated registry for ML-extension model candidates.

The registry is deliberately separate from the run registry.  A model candidate is
not scientific evidence merely because a manifest exists: an ``INCLUDED`` or
``AVAILABLE`` manifest must carry verified provenance, while planned and deferred
models remain visible so exclusions cannot be mistaken for silent omission.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


class ModelRegistryError(ValueError):
    """Raised when a model manifest violates the registry contract."""


@dataclass(frozen=True)
class RegisteredModel:
    """One validated model manifest and its repository path."""

    path: Path
    data: dict[str, Any]

    @property
    def model_id(self) -> str:
        return str(self.data["model_id"])

    @property
    def status(self) -> str:
        return str(self.data["status"])

    @property
    def provenance_status(self) -> str:
        provenance = self.data.get("provenance", {})
        return str(provenance.get("verification_status", "NOT_VERIFIED"))

    def to_dict(self) -> dict[str, Any]:
        """Return a detached JSON-compatible copy of the manifest."""
        return cast(dict[str, Any], json.loads(json.dumps(self.data)))


def _validate_schema(data: dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - dev dependency is required
        raise ModelRegistryError("jsonschema is required for model registry verification") from exc

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(data)
    except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
        raise ModelRegistryError(f"invalid model schema {schema_path}: {exc}") from exc
    except jsonschema.ValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path)
        suffix = f" at {location}" if location else ""
        raise ModelRegistryError(
            f"manifest schema validation failed{suffix}: {exc.message}"
        ) from exc


def load_model_manifest(
    path: str | Path,
    *,
    schema_path: str | Path = "research/schemas/model_manifest.schema.json",
) -> RegisteredModel:
    """Load and validate one strict model manifest."""
    target = Path(path)
    if not target.is_file():
        raise ModelRegistryError(f"model manifest does not exist: {target}")
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelRegistryError(f"cannot read model manifest {target}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ModelRegistryError(f"model manifest must be a JSON object: {target}")
    schema = Path(schema_path)
    _validate_schema(raw, schema)
    return RegisteredModel(path=target, data=raw)


def load_model_registry(
    directory: str | Path = "research/ml_extension/models",
    *,
    schema_path: str | Path = "research/schemas/model_manifest.schema.json",
) -> tuple[RegisteredModel, ...]:
    """Load all JSON manifests in deterministic path order.

    Duplicate model IDs and an empty registry are errors: both conditions make a
    benchmark selection ambiguous or silently incomplete.
    """
    root = Path(directory)
    if not root.is_dir():
        raise ModelRegistryError(f"model registry directory does not exist: {root}")
    paths = sorted(root.glob("*.json"))
    if not paths:
        raise ModelRegistryError(f"model registry is empty: {root}")
    models = tuple(load_model_manifest(path, schema_path=schema_path) for path in paths)
    ids = [model.model_id for model in models]
    duplicates = sorted({model_id for model_id in ids if ids.count(model_id) > 1})
    if duplicates:
        raise ModelRegistryError(f"duplicate model_id values: {', '.join(duplicates)}")
    return models


def included_models(models: tuple[RegisteredModel, ...]) -> tuple[RegisteredModel, ...]:
    """Return only candidates that have passed the explicit inclusion gate."""
    included = tuple(model for model in models if model.status in {"INCLUDED", "AVAILABLE"})
    unverified = tuple(
        model.model_id for model in included if model.provenance_status != "VERIFIED"
    )
    if unverified:
        raise ModelRegistryError(
            "included models require VERIFIED provenance: " + ", ".join(unverified)
        )
    return included


def verify_model_registry(
    directory: str | Path = "research/ml_extension/models",
    *,
    schema_path: str | Path = "research/schemas/model_manifest.schema.json",
) -> list[str]:
    """Return human-readable verification failures; an empty list means PASS."""
    try:
        models = load_model_registry(directory, schema_path=schema_path)
        included_models(models)
    except ModelRegistryError as exc:
        return [str(exc)]
    return []

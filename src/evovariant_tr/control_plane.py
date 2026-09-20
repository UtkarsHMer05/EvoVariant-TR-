"""Validation helpers for the ML-extension control plane.

The original temporal protocol is immutable.  This module validates the
additive ML-extension control files and checks that their recorded hashes are
consistent before any experiment command is allowed to proceed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ORIGINAL_PROTOCOL_SHA256 = (
    "78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525"
)
EXTENSION_PROTOCOL_PATH = Path("research/ml_extension/protocol.yaml")
SPLIT_POLICY_PATH = Path("research/ml_extension/split_policy.yaml")
HASHES_PATH = Path("research/ml_extension/protocol_hashes.json")
SCHEMA_PATHS = (
    Path("research/schemas/model_manifest.schema.json"),
    Path("research/schemas/split_manifest.schema.json"),
    Path("research/schemas/experiment_config.schema.json"),
    Path("research/schemas/cost_ledger.schema.json"),
)


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping and reject non-mapping roots."""
    target = Path(path)
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected a YAML mapping at {target}")
    return raw


def _validate_json_schema(path: Path) -> str | None:
    """Validate a JSON Schema document when the dev dependency is available."""
    try:
        import jsonschema
    except ImportError:
        return "jsonschema is required for control-plane schema verification"

    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
        return f"{path}: invalid JSON Schema: {exc}"
    return None


def verify_ml_control_plane(repo_root: str | Path = ".") -> list[str]:
    """Return human-readable control-plane failures; an empty list means PASS."""
    root = Path(repo_root)
    failures: list[str] = []
    original = root / "research/protocol/protocol.yaml"
    extension = root / EXTENSION_PROTOCOL_PATH
    split_policy = root / SPLIT_POLICY_PATH
    hashes_path = root / HASHES_PATH

    if not original.is_file():
        failures.append(f"missing frozen original protocol: {original}")
    elif sha256_file(original) != ORIGINAL_PROTOCOL_SHA256:
        failures.append("frozen original protocol SHA-256 does not match the locked value")

    for path in (extension, split_policy):
        if not path.is_file():
            failures.append(f"missing ML control file: {path}")
        else:
            try:
                load_yaml_mapping(path)
            except (OSError, ValueError, yaml.YAMLError) as exc:
                failures.append(str(exc))

    if extension.is_file():
        try:
            extension_data = load_yaml_mapping(extension)
            original_data = extension_data.get("original_protocol")
            if not isinstance(original_data, dict):
                failures.append("ML protocol must contain original_protocol mapping")
            elif original_data.get("sha256") != ORIGINAL_PROTOCOL_SHA256:
                failures.append("ML protocol original_protocol.sha256 is stale or incorrect")
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(str(exc))

    for schema_path in SCHEMA_PATHS:
        target = root / schema_path
        if not target.is_file():
            failures.append(f"missing control-plane schema: {target}")
            continue
        error = _validate_json_schema(target)
        if error:
            failures.append(error)

    if not hashes_path.is_file():
        failures.append(f"missing control-plane hash record: {hashes_path}")
    else:
        try:
            recorded = json.loads(hashes_path.read_text(encoding="utf-8"))
            if not isinstance(recorded, dict):
                failures.append(f"hash record must be a JSON object: {hashes_path}")
            else:
                expected_original = recorded.get("original_protocol_sha256")
                if expected_original != ORIGINAL_PROTOCOL_SHA256:
                    failures.append("recorded original protocol hash is incorrect")
                files = recorded.get("files")
                if not isinstance(files, dict):
                    failures.append("hash record must contain a files mapping")
                else:
                    for relative, expected in files.items():
                        target = root / str(relative)
                        if not target.is_file():
                            failures.append(f"hashed control file is missing: {target}")
                        elif sha256_file(target) != expected:
                            failures.append(f"hash mismatch for control file: {target}")
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"cannot read {hashes_path}: {exc}")

    return failures

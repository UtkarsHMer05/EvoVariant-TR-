"""Content-addressed identity and storage for research cache artifacts.

Every model output, embedding, and prediction cache entry carries the full
scientific identity declared by the ML-extension protocol.  A cache hit is
valid only when every identity field matches byte-for-byte after canonical JSON
serialization.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CacheIdentity:
    """All dimensions that can change the meaning of a cached result."""

    model_id: str
    checkpoint: str
    model_revision: str
    preprocessing_revision: str
    assembly: str
    context_length_bp: int
    orientation: str
    layer: str
    normalized_variant_id: str

    def canonical(self) -> dict[str, Any]:
        return asdict(self)

    def key(self) -> str:
        payload = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class CacheHit:
    """A validated cache payload and its identity key."""

    key: str
    identity: CacheIdentity
    payload: dict[str, Any]
    payload_sha256: str
    created_at: str


class ContentAddressedCache:
    """Small JSON cache suitable for local tests and a mounted Modal volume."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    @staticmethod
    def _payload_hash(payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def get(self, identity: CacheIdentity) -> CacheHit | None:
        key = identity.key()
        path = self._path(key)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        stored_identity = CacheIdentity(**data["identity"])
        if stored_identity != identity or data.get("key") != key:
            return None
        payload = data["payload"]
        if data.get("payload_sha256") != self._payload_hash(payload):
            return None
        return CacheHit(
            key=key,
            identity=stored_identity,
            payload=payload,
            payload_sha256=data["payload_sha256"],
            created_at=str(data["created_at"]),
        )

    def put(self, identity: CacheIdentity, payload: dict[str, Any]) -> CacheHit:
        key = identity.key()
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload_hash = self._payload_hash(payload)
        data = {
            "key": key,
            "identity": identity.canonical(),
            "payload": payload,
            "payload_sha256": payload_hash,
            "created_at": datetime.now(UTC).isoformat(),
        }
        encoded = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
        fd, temporary = tempfile.mkstemp(prefix=f".{key}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return CacheHit(
            key=key,
            identity=identity,
            payload=payload,
            payload_sha256=payload_hash,
            created_at=str(data["created_at"]),
        )

    def get_or_put(
        self,
        identity: CacheIdentity,
        payload_factory: Any,
    ) -> tuple[CacheHit, bool]:
        """Return ``(entry, cache_hit)`` without rerunning a cached factory."""
        existing = self.get(identity)
        if existing is not None:
            return existing, True
        payload = payload_factory()
        if not isinstance(payload, dict):
            raise TypeError("cache payload factory must return a dictionary")
        return self.put(identity, payload), False

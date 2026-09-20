"""Runtime telemetry that is safe to collect locally or inside Modal."""

from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class RuntimeTelemetry:
    """Minimal provenance and resource sample for one workload."""

    started_at: str
    completed_at: str
    runtime_seconds: float
    gpu_type: str | None
    gpu_memory_peak_bytes: int | None
    host: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "runtime_seconds": self.runtime_seconds,
            "gpu_type": self.gpu_type,
            "gpu_memory_peak_bytes": self.gpu_memory_peak_bytes,
            "host": self.host,
        }


class TelemetryTimer:
    """Context manager for wall-clock and optional torch CUDA telemetry."""

    def __init__(self, gpu_type: str | None = None) -> None:
        self.gpu_type = gpu_type
        self._started = 0.0
        self._started_at = ""
        self.result: RuntimeTelemetry | None = None

    def __enter__(self) -> TelemetryTimer:
        self._started = time.perf_counter()
        self._started_at = datetime.now(UTC).isoformat()
        self._reset_cuda_peak()
        return self

    def __exit__(self, _exc_type: object, _exc: object, _traceback: object) -> None:
        completed_at = datetime.now(UTC).isoformat()
        self.result = RuntimeTelemetry(
            started_at=self._started_at,
            completed_at=completed_at,
            runtime_seconds=time.perf_counter() - self._started,
            gpu_type=self.gpu_type or self._detect_gpu_type(),
            gpu_memory_peak_bytes=self._read_cuda_peak(),
            host=platform.node(),
        )

    @staticmethod
    def _torch_cuda() -> Any:
        try:
            import torch
        except ImportError:
            return None
        return torch.cuda if torch.cuda.is_available() else None

    def _reset_cuda_peak(self) -> None:
        cuda = self._torch_cuda()
        if cuda is not None:
            cuda.reset_peak_memory_stats()

    def _read_cuda_peak(self) -> int | None:
        cuda = self._torch_cuda()
        if cuda is None:
            return None
        return int(cuda.max_memory_allocated())

    def _detect_gpu_type(self) -> str | None:
        cuda = self._torch_cuda()
        if cuda is None:
            return None
        return str(cuda.get_device_name(0))

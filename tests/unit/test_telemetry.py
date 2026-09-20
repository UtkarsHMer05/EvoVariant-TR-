"""Tests for CPU-safe runtime telemetry."""

from evovariant_tr.telemetry import TelemetryTimer


class _FakeCuda:
    def __init__(self) -> None:
        self.reset_calls = 0

    def reset_peak_memory_stats(self) -> None:
        self.reset_calls += 1

    def max_memory_allocated(self) -> int:
        return 4096

    def get_device_name(self, index: int) -> str:
        assert index == 0
        return "Fake H100"


def test_telemetry_timer_records_local_runtime() -> None:
    with TelemetryTimer(gpu_type="CPU") as timer:
        value = sum(range(10))
    assert value == 45
    assert timer.result is not None
    assert timer.result.runtime_seconds >= 0
    assert timer.result.gpu_type == "CPU"
    assert timer.result.gpu_memory_peak_bytes is None
    assert timer.result.to_dict()["host"]


def test_telemetry_timer_records_optional_cuda_metrics(monkeypatch) -> None:
    fake_cuda = _FakeCuda()
    monkeypatch.setattr(TelemetryTimer, "_torch_cuda", staticmethod(lambda: fake_cuda))
    with TelemetryTimer() as timer:
        pass
    assert fake_cuda.reset_calls == 1
    assert timer.result is not None
    assert timer.result.gpu_type == "Fake H100"
    assert timer.result.gpu_memory_peak_bytes == 4096

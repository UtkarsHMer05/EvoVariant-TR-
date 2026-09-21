"""No-spend source guard for the minimal H100 diagnostic."""

from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "modal_h100_diagnostic.py"


def test_h100_diagnostic_has_torch_and_only_the_cuda_probe_contract() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124" in source
    assert 'torch.tensor([1.0], device="cuda")' in source
    assert "torch.cuda.get_device_capability(0)" in source
    assert '"torch_version": str(torch.__version__)' in source
    assert '"cuda_runtime_version": str(torch.version.cuda)' in source
    assert '"tensor_result": float(result.item())' in source
    assert '"status": "PASS" if result["tensor_result"] == 2.0' in source
    assert "evo2" not in source.lower()
    assert "Volume" not in source

#!/usr/bin/env python3
"""Create or reuse the isolated Python 3.11 CUDA environment used by Colab."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path


def probe(python: Path) -> dict[str, object] | None:
    if not python.is_file():
        return None
    code = """
import json, sys
from importlib.metadata import version
import torch, transformers, mamba_ssm, causal_conv1d, pyfaidx
names = ('torch', 'numpy', 'transformers', 'mamba-ssm', 'causal-conv1d', 'optuna', 'pyfaidx')
print(json.dumps({'python': list(sys.version_info[:2]),
                  'packages': {name: version(name) for name in names},
                  'cuda_available': torch.cuda.is_available(),
                  'cuda_runtime': torch.version.cuda,
                  'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))
"""
    result = subprocess.run([str(python), "-c", code], capture_output=True, text=True)
    if result.returncode:
        return None
    details = json.loads(result.stdout)
    expected = {
        "torch": "2.2.0+cu121",
        "numpy": "1.26.4",
        "transformers": "4.38.1",
        "mamba-ssm": "1.2.0.post1",
        "causal-conv1d": "1.2.0.post2",
        "optuna": "5.0.0",
        "pyfaidx": "0.8.1.1",
    }
    if (
        details["python"] != [3, 11]
        or details["cuda_available"] is not True
        or details["cuda_runtime"] != "12.1"
        or any(details["packages"][name] != value for name, value in expected.items())
    ):
        return None
    return details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--env", default="/content/caduceus-env")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    env = Path(args.env).resolve()
    python = env / "bin" / "python"
    details = probe(python)
    if details is None:
        uv = shutil.which("uv")
        if uv is None:
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
            script = Path(sysconfig.get_path("scripts")) / "uv"
            uv = shutil.which("uv") or (str(script) if script.is_file() else None)
        if uv is None:
            raise RuntimeError("uv installation did not provide an executable")
        if not python.exists():
            subprocess.run([uv, "venv", "--python", "3.11", str(env)], check=True)
        subprocess.run(
            [uv, "pip", "install", "--python", str(python),
             "ninja", "packaging", "setuptools", "wheel"],
            check=True,
        )
        subprocess.run(
            [uv, "pip", "install", "--python", str(python), "--index-url",
             "https://download.pytorch.org/whl/cu121", "torch==2.2.0"],
            check=True,
        )
        subprocess.run(
            [uv, "pip", "install", "--python", str(python), "--no-build-isolation",
             "-r", str(root / "requirements-adaptation.txt")],
            check=True,
        )
        details = probe(python)
    if details is None:
        raise RuntimeError("isolated environment failed Python/CUDA/package verification")
    print(json.dumps({"python_executable": str(python), **details}, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Record the runtime boundary before model work."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--state")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "model_revisions": {
            "caduceus": "b0477522ac5d044ad03578aa724ec8e4bdbd405b",
            "nucleotide_transformer": "06615c1660c892fc199840c18123f8385b3542a8",
        },
        "packages": {},
    }
    for package in (
        "torch",
        "transformers",
        "peft",
        "optuna",
        "numpy",
        "pandas",
        "scikit-learn",
        "mamba-ssm",
        "causal-conv1d",
    ):
        try:
            report["packages"][package] = version(package)
        except PackageNotFoundError:
            report["packages"][package] = None
    try:
        import torch

        report.update(
            {
                "torch": torch.__version__,
                "cuda_runtime": torch.version.cuda,
                "cuda_available": bool(torch.cuda.is_available()),
                "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                "compute_capability": list(torch.cuda.get_device_capability(0))
                if torch.cuda.is_available()
                else None,
                "vram_bytes": (
                    int(torch.cuda.get_device_properties(0).total_memory)
                    if torch.cuda.is_available()
                    else None
                ),
            }
        )
    except ImportError as exc:
        report["torch_import_error"] = str(exc)
    try:
        report["nvidia_smi"] = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except OSError as exc:
        report["nvidia_smi_error"] = str(exc)
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(output)
    if args.state and report.get("cuda_available"):
        from evovariant_tr.adaptation.state import record_stage

        record_stage(
            args.state,
            project_root=args.root,
            stage="ENV_READY",
            artifacts=(output,) if args.output else (),
            details=report,
        )
    print(serialized, end="")


if __name__ == "__main__":
    main()

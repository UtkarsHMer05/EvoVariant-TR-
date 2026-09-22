#!/usr/bin/env python
"""Record the runtime boundary before model work."""

from __future__ import annotations

import json
import platform
import subprocess
import sys


def main() -> None:
    report = {
        "python": sys.version,
        "platform": platform.platform(),
    }
    try:
        import torch

        report.update(
            {
                "torch": torch.__version__,
                "cuda_available": bool(torch.cuda.is_available()),
                "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
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
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except OSError as exc:
        report["nvidia_smi_error"] = str(exc)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


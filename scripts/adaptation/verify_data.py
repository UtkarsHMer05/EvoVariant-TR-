#!/usr/bin/env python
"""Verify the frozen formal adaptation data contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evovariant_tr.adaptation.data import (
    load_formal_rows,
    sha256_file,
    verify_formal_data,
    verify_reference_rows,
)
from evovariant_tr.adaptation.state import record_stage

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--reference")
    parser.add_argument("--output")
    parser.add_argument("--state")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = verify_formal_data(root)
    if args.reference:
        from pyfaidx import Fasta

        train, validation = load_formal_rows(root)
        reference_path = Path(args.reference).resolve()
        fasta = Fasta(str(reference_path), as_raw=True, sequence_always_upper=True)
        report["reference"] = {
            "path": str(reference_path),
            "sha256": sha256_file(reference_path),
            "checked_formal_ref_alleles": verify_reference_rows(fasta, (*train, *validation)),
        }
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(output)
        if args.state:
            record_stage(
                args.state,
                project_root=root,
                stage="DATA_READY" if args.reference else "MANIFESTS_VERIFIED",
                artifacts=(output,),
                details=report,
            )
    print(serialized, end="")

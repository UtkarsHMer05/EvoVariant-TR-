#!/usr/bin/env python3
"""Reuse the verified Drive GRCh38 archive and check the formal REF alleles."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import urllib.request
from pathlib import Path

from evovariant_tr.adaptation.data import (
    load_formal_rows,
    sha256_file,
    verify_reference_rows,
)

REFERENCE_SHA256 = "5be01555d98347fdb3714dc84c6f77c9d8bc774adcf32c6f7a8fa06f5baf5e51"
REFERENCE_URL = "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--drive-root", default="/content/drive/MyDrive/EvoVariantTR")
    parser.add_argument("--output", default="/content/Homo_sapiens_assembly38.fasta")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    reference = Path(args.output)
    drive = Path(args.drive_root) / "reference"
    archive = drive / "hg38.fa.gz"
    provenance = drive / "provenance.json"
    reference.parent.mkdir(parents=True, exist_ok=True)
    drive.mkdir(parents=True, exist_ok=True)
    if not reference.exists() or sha256_file(reference) != REFERENCE_SHA256:
        drive_reference = drive / reference.name
        if drive_reference.exists() and sha256_file(drive_reference) == REFERENCE_SHA256:
            shutil.copyfile(drive / reference.name, reference)
        else:
            if not archive.exists():
                temporary = archive.with_name(archive.name + ".tmp")
                urllib.request.urlretrieve(REFERENCE_URL, temporary)
                os.replace(temporary, archive)
            temporary = reference.with_name(reference.name + ".tmp")
            try:
                with gzip.open(archive, "rb") as source, temporary.open("wb") as target:
                    shutil.copyfileobj(source, target)
                if sha256_file(temporary) != REFERENCE_SHA256:
                    raise RuntimeError("GRCh38 archive does not produce the verified FASTA")
                os.replace(temporary, reference)
            finally:
                temporary.unlink(missing_ok=True)
    if sha256_file(reference) != REFERENCE_SHA256:
        raise RuntimeError("GRCh38 FASTA hash mismatch")
    index = reference.with_suffix(reference.suffix + ".fai")
    drive_index = drive / index.name
    if not index.exists() and drive_index.exists():
        shutil.copyfile(drive_index, index)
    from pyfaidx import Fasta

    fasta = Fasta(str(reference), as_raw=True, sequence_always_upper=True)
    train, validation = load_formal_rows(root)
    checked = verify_reference_rows(fasta, (*train, *validation))
    if checked != 4000:
        raise RuntimeError(f"expected 4000 REF allele checks, got {checked}")
    if not drive_index.exists():
        shutil.copyfile(index, drive_index)
    report = {
        "status": "PASS",
        "source": REFERENCE_URL,
        "drive_archive": str(archive),
        "drive_archive_sha256": sha256_file(archive) if archive.exists() else None,
        "reference": str(reference),
        "reference_sha256": REFERENCE_SHA256,
        "index_sha256": sha256_file(index),
        "formal_ref_alleles_checked": checked,
    }
    temporary = provenance.with_name(provenance.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, provenance)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()

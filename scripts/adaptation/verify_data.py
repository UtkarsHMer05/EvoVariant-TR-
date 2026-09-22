#!/usr/bin/env python
"""Verify the frozen formal adaptation data contract."""

from __future__ import annotations

import json
from pathlib import Path

from evovariant_tr.adaptation.data import verify_formal_data


if __name__ == "__main__":
    print(json.dumps(verify_formal_data(Path(__file__).resolve().parents[2]), indent=2, sort_keys=True))


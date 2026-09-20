"""Compatibility entry point for registry-driven Phase 17 figure inputs.

The old M099 script read ignored historical snapshots and generated synthetic
scoring records for demonstration curves. That path could produce files that
looked like scientific results without a registered model run. The current
entry point delegates to the immutable registry manifest and therefore emits
only source metadata or an explicit ``BLOCKED`` status.

Usage:
    python -m research.scripts.generate_figures --output-dir research/figures
"""

from __future__ import annotations

import argparse
from pathlib import Path

from evovariant_tr.figure_artifacts import (
    build_registry_figure_manifest,
    write_figure_manifest,
)
from evovariant_tr.registry import Registry

REPO_ROOT = Path(__file__).resolve().parents[2]


def generate_figures(output_dir: Path) -> dict[str, str]:
    """Write the current registry manifest under ``output_dir``.

    The return shape is retained for callers of the historical helper. It is
    a manifest path, not a claim that plots or scientific metrics were made.
    """
    registry = Registry(REPO_ROOT / "experiments" / "registry", repo_root=REPO_ROOT)
    manifest = build_registry_figure_manifest(registry, repo_root=REPO_ROOT)
    output = write_figure_manifest(Path(output_dir) / "figure_manifest.json", manifest)
    return {"figure_manifest": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a registry-driven Phase 17 figure-input manifest"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("research/figures"),
        help="Output directory for the metadata manifest",
    )
    args = parser.parse_args()

    figures = generate_figures(Path(args.output_dir))
    print(f"Generated {len(figures)} registry manifest:")
    for name, path in figures.items():
        print(f"  {name} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Data Directory and Git Policy (M21)

## Policy statement

EvoVariant-TR manages public research data with a strict no-raw-data policy:
**no raw public archive is ever committed to git.** All data must be downloaded
at runtime from official sources and verified against tracked manifest files
(SHA-256 checksums, sizes, source URLs, retrieval timestamps).

## Directory layout

```
data/
  raw/              # Downloaded public archives (gitignored, never committed)
  derived/          # Computed datasets (gitignored; regenerate via commands)
  reference/        # Reference genome FASTA + index (gitignored; downloaded separately)
  model_cache/      # Evo 2 model weights cache (gitignored; downloaded at runtime)

research/
  data_manifests/   # JSON manifest files (TRACKED — the source of truth for data)
  configs/          # Runtime/experiment configs (some tracked, some local overrides)
  schemas/          # JSON Schema files for data formats (TRACKED)
  scripts/          # Data pipeline scripts (TRACKED)
  runs/             # Run outputs — registry records tracked, large outputs gitignored
  results/          # Final result artifacts (gitignored except small CSV summaries)
  figures/          # Plot outputs (gitignored except final publication figures)
  tables/           # Table outputs (gitignored except final publication tables)
```

## Rules

1. **Raw archives** (`data/raw/`) are downloaded by scripts from official URLs
   recorded in `research/data_manifests/`. They are never committed.

2. **Derived datasets** (`data/derived/`) are computed from raw archives. They
   are also gitignored. Any derived dataset that is small enough and
   appropriate to distribute lives in `research/results/` as a tracked CSV/JSON.

3. **Manifests** (`research/data_manifests/*.json`) record every downloaded file's
   SHA-256, size, source URL, release date, and retrieval timestamp. Manifests
   are tracked in git and serve as the single source of truth for data identity.

4. **Reference genomes** (`data/reference/`) are downloaded separately via a
   documented script. They are never committed.

5. **Model weights** (`data/model_cache/`) are downloaded at runtime via
   HuggingFace or official sources. They are never committed.

6. **Run outputs** in `research/runs/` are gitignored except for the registry
   manifest and small summary files. Use `experiments/registry/` for the
   immutable experiment registry.

7. **Git LFS** is not used. If large files are accidentally staged, they will
   be caught by `check_secrets.sh` (for sensitive patterns) and by the size
   pre-commit hook (if configured).

8. **Download never guesses URLs.** All ClinVar/NCBI URLs must be discovered
   programmatically or from official documentation (see M22).

## Verification

- `make data-verify MANIFEST=<path> BASE_DIR=data/raw` verifies files against
  a tracked manifest.
- The CI gate (future) will refuse builds that include raw archives.

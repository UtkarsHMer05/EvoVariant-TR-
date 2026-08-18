# NEW REPOSITORY ORIGIN — EvoVariant-TR

Date: 2026-08-18
Milestone: 001/100

## Statement of origin

This repository is a **brand-new, independent Git repository** for the project
**EvoVariant-TR** (temporal-resolution VUS benchmark with frozen Evo 2 scoring).

It was initialized fresh (`git init -b main`) on 2026-08-18 in the directory
`/Users/utkarshkhajuria/Desktop/EvoVariant`.

The local EvoVariant source snapshot that was present in this directory at
initialization time (see `docs/bootstrap/initial_file_inventory.txt`) is used
**only as an untrusted code starting point**. It may be inspected, refactored,
migrated, replaced, or deleted after its behavior is understood.

## What this repository is NOT

- It is **not** the previous EvoVariant repository
  (`https://github.com/UtkarsHMer05/EvoVariant`).
- It does **not** contain, inherit, fetch, cherry-pick, or depend on the Git
  history of the previous repository.
- It has **no** remote pointing at the previous repository, and none will be
  added. The only writable remote ever allowed is a NEW repository URL that the
  user explicitly provides and authorizes. As of this document, **no remote has
  been configured at all**.
- It does **not** reuse the previous repository's Modal deployment identity,
  endpoint URLs, or saved evaluation outputs as new research evidence.
- The old README (`README.md` at snapshot time) is treated as legacy
  documentation of the old system, **not** as the scientific specification of
  EvoVariant-TR.

## Snapshot facts at initialization

- The snapshot directory contained **no `.git` directory** and no Git worktree
  metadata at initialization time (verified with
  `git rev-parse --is-inside-work-tree` → not a work tree).
- The snapshot declared one Git submodule in `.gitmodules`
  (`evo2-backend/evo2` → `https://github.com/ArcInstitute/evo2`), but the
  submodule directory was **not present** in the snapshot and has **not** been
  initialized. It will not be initialized as part of the old design; the new
  project will pin the official Evo 2 source independently (see Milestone 51).
- The snapshot contained legacy evaluation outputs under
  `evaluation/results/final_100/`. These are labeled
  **LEGACY_BASELINE_ONLY** and are not EvoVariant-TR research evidence.

## Provenance chain

1. Original project: `variant-analysis-evo2` / EvoVariant (previous GitHub
   repository, not operated on by this project).
2. Local source snapshot copied to this directory by the user (no `.git`).
3. 2026-08-18: fresh `git init -b main` in this directory → this repository.
4. Initial file inventory recorded **before any refactor** in
   `docs/bootstrap/initial_file_inventory.txt`.

## Policy carried forward

- Never modify, push to, or fetch from the previous repository.
- Never add the previous repository URL as a remote.
- Never commit secrets, raw ClinVar archives, large GRCh38 FASTA files, model
  checkpoints, Hugging Face caches, `node_modules`, virtualenvs, or build
  outputs.
- Push only to a NEW repository remote explicitly supplied and authorized by the
  user. Until then, all commits are local only.

# ADR 0001 — Fresh-repository isolation

- Status: ACCEPTED
- Date: 2026-08-18

## Context

The user supplied a local EvoVariant source snapshot derived from a previous GitHub
repository. The new project (EvoVariant-TR) must be independently reproducible and
must never mutate, depend on, or inherit identity from the previous repository.

## Decision

Create a genuinely new Git repository with fresh history (`git init -b main`), zero
remotes until the user explicitly supplies and authorizes a NEW remote URL. Treat the
snapshot strictly as untrusted migration input. Never fetch/cherry-pick from the old
repository, never add it as a remote, never push to it, never reuse its deployment
identity or saved outputs as new evidence.

## Alternatives

1. Reuse the old repository with a new branch — rejected: history/identity coupling,
   risk of pushing to the old remote, old outputs would pollute evidence.
2. Fork the old repository — rejected: inherits history and remote linkage.
3. Copy files into a sibling directory — acceptable per protocol if the tree had
   been tied to old Git metadata; not needed here because the snapshot contained no
   `.git` directory (verified at Milestone 1).

## Consequences

- All provenance starts at the new root commit; snapshot origin is documented in
  `docs/bootstrap/NEW_REPOSITORY_ORIGIN.md`.
- Push is blocked until the user provides the new remote URL.
- Legacy files live in-tree as migration baseline only, with evidence-stage labels.

## Validation

- `git rev-parse --is-inside-work-tree` was false before init (no old worktree).
- `git remote -v` empty after init (Milestone 1, re-checked every milestone).
- No `.git/objects/info/alternates`; fresh object store.

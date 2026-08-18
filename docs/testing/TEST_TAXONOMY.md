# TEST TAXONOMY — EvoVariant-TR (Milestone 017)

Defines what must pass before each class of milestone can be considered complete.

## Tiers

| Directory | Purpose | Runs by default? |
|---|---|---|
| `tests/unit` | Pure logic, temp-file I/O only | Yes |
| `tests/contract` | Frozen external schemas and file contracts (protocol hash, JSON schemas) | Yes |
| `tests/integration` | Multi-module flows on tiny local fixtures; no network | Yes |
| `tests/modal` | Modal / paid GPU compute | **No — gated** |
| `tests/scientific` | Slow scientific validation (cohort recomputation, parity sweeps) | **No — gated** |
| `tests/e2e` | Browser end-to-end (lands at Milestone 97) | **No — gated** |

## Gates

Default runs deselect gated tiers via `addopts` in `pyproject.toml`
(`-m "not modal and not scientific and not e2e"`), and `tests/conftest.py`
adds a hard block on top, so even `pytest -m modal` cannot spend money by
accident.

- **modal:** requires `--run-modal` **and** `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS`.
- **scientific:** requires `--run-scientific`.
- **e2e:** requires `--run-e2e`.

## Quality gates

- Coverage floor for core deterministic modules: **95%** (`fail_under` in
  `pyproject.toml`; current: 98%).
- `ruff check` must be clean.
- `mypy` strict must be clean.

## Single local validation command

```bash
./scripts/validate_local.sh
```

Runs ruff → mypy → default pytest tiers → coverage floor. It never launches
paid compute. Every milestone that touches Python code must leave this command
green.

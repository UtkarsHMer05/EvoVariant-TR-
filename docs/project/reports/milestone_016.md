# Milestone 016 — Create the modern Python project scaffold

- **MILESTONE:** 016
- **TITLE:** Create the modern Python project scaffold
- **STATUS:** PASS
- **DATE:** 2026-08-18

## WHAT EXISTED BEFORE

- `src/evovariant_tr/` held four modules (`__init__.py`, `config.py`, `evidence.py`, `manifest.py`, `registry.py`) but no packaging metadata; tests relied on the `tests/conftest.py` sys.path shim and the ad-hoc `.venv-baseline` environment.
- No `pyproject.toml`, no CLI entrypoint, no lint/type-check configuration.
- Python 3.12.8 confirmed available at `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12`.

## WHAT CHANGED

- Created `pyproject.toml` (setuptools, src layout):
  - `requires-python = ">=3.12"`; core dependencies are only `pydantic` and `PyYAML`.
  - Optional extras kept separate: `modal` (GPU/cloud), `plotting` (matplotlib/seaborn), `comparators` (pandas/numpy), `dev` (pytest, pytest-cov, ruff, mypy, pyarrow, jsonschema). No GPU-only package is in the core environment.
  - Console script `evovariant-tr = evovariant_tr.cli:main`.
  - Tool config: pytest (`testpaths=["tests"]`), coverage (`source=["evovariant_tr"]`), ruff (line-length 100, py312, rules E/F/I/UP/B), mypy (strict, packages `evovariant_tr`).
- Created `src/evovariant_tr/cli.py` with subcommands `validate-protocol`, `verify-manifest`, `version`.
- Created the canonical `.venv` (Python 3.12.8) and installed `-e '.[dev]'`.
- Lint/type cleanup driven by the new tooling: ruff auto-fixed import ordering and `timezone`→`UTC`; converted `EvidenceStage`, `RunStatus`, `CompressionType` from `str, Enum` to `StrEnum` (UP042); wrapped four over-long lines; fixed one mypy list-invariance error by switching to `Sequence`.
- Added `tests/unit/test_cli.py` (5 tests) so the CLI is covered (package coverage 92% → 98%).
- Removed the now-redundant `src/evovariant_tr/.gitkeep`. The `tests/conftest.py` shim is kept harmlessly so tests also run without an editable install.

## FILES CREATED

- `pyproject.toml`
- `src/evovariant_tr/cli.py`
- `tests/unit/test_cli.py`
- `docs/project/reports/milestone_016.md` (this report)

## FILES MODIFIED

- `docs/project/MILESTONE_STATUS.md` (row 016 → PASS)
- `src/evovariant_tr/evidence.py`, `registry.py`, `manifest.py` (StrEnum, UTC, Sequence, import order)
- `tests/unit/test_manifest.py`, `test_config_schema.py`, `test_evidence_stage.py` (line-length fixes, import order)

## FILES REMOVED / MOVED

- `src/evovariant_tr/.gitkeep` (redundant once real modules existed)

## COMMANDS RUN

- `python3.12 -m venv .venv`
- `. .venv/bin/activate && python -m pip install -U pip` → pip 26.2.1
- `python -m pip install -e '.[dev]'` → clean install, `import evovariant_tr` OK (0.1.0)
- `python -m pytest -q` → **111 passed**
- `python -m ruff check src tests scripts` → **All checks passed!**
- `python -m mypy` → **Success: no issues found in 6 source files** (strict mode)
- `python -m pytest --cov -q` → **98% total coverage**
- `evovariant-tr version` / `evovariant-tr validate-protocol` → both OK

## TESTS

- Full suite: 111 passed (106 prior + 5 new CLI tests).
- CLI tests cover: version JSON output, protocol validation against the real frozen YAML, missing-protocol failure, verify-manifest clean/corrupt exit codes, and no-command exit.

## SCIENTIFIC VALIDATION

- The frozen protocol validates through the installed CLI (`OK: protocol 1.0.0 validated … GRCh38 … 8192bp`), confirming the packaged core still enforces the M11/M12 contract.
- No scientific behavior changed; StrEnum/UTC refactors are serialization-identical (all 106 prior tests pass unchanged).

## ENGINEERING VALIDATION

- **Validation 1:** fresh `.venv` installs without CUDA — pip resolved CPU-only wheels only.
- **Validation 2:** core package imports on macOS/CPU (`import evovariant_tr` → OK).
- **Validation 3:** GPU dependencies isolated — verified `torch`, `modal`, `transformers`, `evo2`, `flash_attn` are all absent from the core environment; `modal` exists only behind the `[modal]` extra.
- Lint (ruff), strict type check (mypy), and coverage (98%) all green.

## COST / EXTERNAL CALLS

- pip install from PyPI only (dev tooling). Zero GPU, zero Modal, zero cloud spend.

## EVIDENCE GENERATED

- Install log (pip 26.2.1, editable install), test run (111 passed), ruff/mypy clean outputs, coverage table (98%).
- Stage: ENGINEERING_PILOT-adjacent tooling evidence; no scientific outputs.

## GIT STATUS

- Files listed above; ledger updated. Local commit to follow; no remote configured, no push.

## RISKS / OPEN QUESTIONS

- `.venv-baseline` (M6) remains for baseline-evaluator evidence; `.venv` is now the canonical development environment. Both are gitignored.
- `comparators`/`plotting`/`modal` extras are declared but not yet installed locally — they will be exercised at M51+ (Modal) and M71+ (comparators) with version pins verified at that time.

## NEXT MILESTONE

- 017 — Create the test taxonomy and minimum quality gates.

## DO NOT CONTINUE IF

- The fresh environment fails to install without CUDA.
- The core package fails to import on macOS/CPU.
- Any GPU-only package appears in the core environment.

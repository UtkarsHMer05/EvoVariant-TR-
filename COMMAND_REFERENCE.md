# EvoVariant-TR — Command Reference

**Created:** Milestone 20
**Status:** Live control surface for free/local commands and gated GPU commands.

This file is the single source of truth for how to operate the EvoVariant-TR repository. The `Makefile` mirrors these commands and delegates to them.

## 1. Philosophy

- **Free by default.** Every command in this reference is CPU/local and costs nothing unless it is explicitly named `gpu-*` or `--run-modal` / `--run-scientific` / `--run-e2e`.
- **Opt-in paid compute.** GPU targets print a warning and refuse to run unless `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS` is exported. `gpu-full` additionally requires an on-disk approval artifact.
- **One entry point.** `make help` lists every target. `make validate` is the default gate.

## 2. Prerequisites

### Python (backend / research)

- Python **3.12** (required).
- Create and activate the environment:
  ```bash
  make bootstrap
  ```
  This creates `.venv`, installs the core package and `[dev]` extras (no CUDA/GPU packages by design).

### Frontend (Next.js app)

```bash
cd apps/web && npm ci
```

## 3. Validation gate (free, CPU/local)

Run the complete local gate:

```bash
make validate
```

This runs, in order:
1. Secret scan (`scripts/check_secrets.sh`)
2. `ruff check src tests scripts`
3. `mypy` (strict, 8 source files)
4. `pytest` (default tiers: unit, contract, integration)
5. Coverage with 95% floor on core deterministic modules

Individual gates:

| Command              | What it does                          |
|----------------------|----------------------------------------|
| `make secrets`       | Scan tracked files for credential patterns |
| `make lint`          | Ruff lint on src, tests, scripts       |
| `make typecheck`     | mypy strict on the core package        |
| `make test`          | Unit + contract + integration tests    |
| `make coverage`      | Tests with coverage report             |

### Test markers (gated tiers)

Gated tiers are **never** run by default. To enable:

| Marker        | Enable flag            | Cost acknowledgement env var required |
|---------------|------------------------|----------------------------------------|
| `modal`       | `--run-modal`          | `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS` |
| `scientific`  | `--run-scientific`     | No                                     |
| `e2e`         | `--run-e2e`            | No (lands at M97)                      |

Example:

```bash
.venv/bin/pytest --run-scientific tests/scientific/
```

## 4. Protocol and data verification (free, CPU/local)

```bash
make protocol-verify          # validate research/protocol/protocol.yaml
make registry-verify           # verify experiments/registry integrity
make data-verify MANIFEST=data/manifests/clinvar_t0.json BASE_DIR=data/raw
```

Or directly via the Python CLI:

```bash
evovariant-tr validate-protocol --protocol research/protocol/protocol.yaml
evovariant-tr verify-manifest --manifest data/manifests/clinvar_t0.json --base-dir data/raw
evovariant-tr version
```

Generate the Phase 17 registry-input manifest (free/local; it reports `BLOCKED` when no
eligible completed scientific runs exist and never invents metrics):

```bash
make figures
evovariant-tr generate-figure-manifest \
  --registry experiments/registry \
  --repo-root . \
  --output research/runs/phase17_fig_status.json
```

## 5. Frontend commands

```bash
cd apps/web
npm run dev        # Next.js dev server with turbo
npm run build      # production build
npx tsc --noEmit   # typecheck
npm run lint       # ESLint
```

Or via Make:

```bash
make frontend-install
make frontend-build
```

## 6. GPU / paid-compute targets

> **WARNING:** These targets may incur PAID GPU costs on Modal.

```bash
# Export the cost acknowledgement first
export EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS

make gpu-pilot      # small multi-gene pilot (lands at M55)
make gpu-full       # full primary scoring (lands at M69, requires approval artifact)
```

### Approval artifact (for `gpu-full`)

Create (or have a human create) `artifacts/approvals/full_run_approval.json`:

```json
{
  "max_budget_usd": 500.0,
  "gpu_type": "H100",
  "approved_by": "guide-or-panel",
  "justified_reason": "..."
}
```

This is **not** auto-generated. It is a human gate.

## 7. Script reference

| Script                          | Purpose                                        |
|---------------------------------|------------------------------------------------|
| `scripts/validate_local.sh`     | Full local validation gate                     |
| `scripts/check_secrets.sh`      | Secret scanner for tracked files               |
| `scripts/verify_manifest.py`    | Verify file manifests against on-disk assets   |
| `scripts/verify_registry.py`    | Verify experiment registry integrity           |

## 8. Quick start for a reviewer

1. `make bootstrap` — set up Python environment.
2. `make validate` — confirm everything passes (free).
3. `cd apps/web && npm ci && npm run build` — confirm frontend builds.
4. `make protocol-verify` — confirm the frozen protocol is valid.

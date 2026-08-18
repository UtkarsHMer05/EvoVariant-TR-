# BACKEND AUDIT — Legacy `evo2-backend/` (Milestone 004)

Date: 2026-08-18
Scope: implementation audit (coupling, lifecycle, infrastructure), complementing the
scientific audit in `docs/audit/LEGACY_SCIENTIFIC_AUDIT.md`. No code is edited at
this milestone; module boundaries are proposed only.

Syntax check: `python3 -m py_compile evo2-backend/main.py` → **PASS** (compiles on
Python 3.12.8; note: compiling does not import `modal`, so this only proves syntax).

---

## 1. Complete responsibility list for `evo2-backend/main.py` (376 lines)

One file performs **eleven** distinct responsibilities:

| # | Responsibility | Lines | Notes |
|---|---|---|---|
| 1 | Modal image creation | 13-31 | `nvidia/cuda:12.4.0-devel-ubuntu22.04` + Python 3.12 |
| 2 | Dependency installation | 17-30 | apt packages; torch 2.4.0 cu124 wheel; **unpinned** evo2 git clone; transformer-engine swap; flash-attn wheel |
| 3 | Compatibility monkey patch | 29 | in-image `run_commands` string-replacement of `vortex/ops/attn_interface.py` |
| 4 | Model initialization | 57, 291-302 | `Evo2('evo2_7b')` in `run_brca1_analysis` and in `@modal.enter()` |
| 5 | Live UCSC sequence download | 224-257 | `get_genome_sequence`, per-request, no timeout/retry |
| 6 | Reference/variant sequence construction | 260-262, 319-335 | window formula (8,193-base defect), single-base substitution |
| 7 | Evo 2 scoring | 264-265 | `model.score_sequences([seq])[0]` for ref and alt |
| 8 | BRCA1 analysis | 40-221 | `run_brca1_analysis` + `brca1_example` (GRCh37 data, plotting) |
| 9 | Threshold derivation/use | 133-158, 269-271 | ROC-Youden threshold + std constants |
| 10 | Confidence heuristic | 273-278 | distance-from-threshold / std |
| 11 | HTTP endpoint serving | 289-349, 352-376 | `@modal.fastapi_endpoint` + `@app.local_entrypoint()` demo client |

This is the monolith the master prompt §1 describes. It cannot be treated as final
research infrastructure because scientific semantics (window, mutation, scoring,
orientation) are inseparable from transport (Modal image, HTTP, UCSC fetch) and from
deprecated policy (threshold, labels).

## 2. The in-image monkey patch

`main.py:29` executes a Python one-liner inside the image build that rewrites
`/usr/local/lib/python3.12/site-packages/vortex/ops/attn_interface.py`:

- replaces `out, softmax_lse, S_dmask, rng_state = flash_attn_gpu.fwd(` with
  `res = flash_attn_gpu.fwd(` (and same for `varlen_fwd`);
- disables the `if torch.__version__ >= "2.4.0":` branch (`if False:`);
- inserts custom unpacking of `res` into `(out, softmax_lse, S_dmask, rng_state)`;
- deletes the `__pycache__` for the patched module.

The patch exists to absorb a return-value signature mismatch between the installed
flash-attn/vortex versions. The same patch text is duplicated across
`debug_flash_attn.py`, `debug_flash_attn2.py`, `debug_returns.py`, `test_import.py`,
`test_clone.py`, and the three `patched_attn_interface*.py` snapshots — evidence of
iterative trial-and-error rather than a pinned, justified fix.

**Policy:** per master prompt §9, this patch must NOT be carried forward unless
current official Evo 2 verification at execution time demonstrates it is still
necessary (Milestone 51). Official docs indicate the 7B light-install path avoids
Transformer Engine entirely, which likely removes the need for this patch.

## 3. Old stack assumptions (CUDA / PyTorch / Transformer Engine / FlashAttention)

| Component | Legacy assumption | Location |
|---|---|---|
| Base image | `nvidia/cuda:12.4.0-devel-ubuntu22.04` | main.py:14-16 |
| Python | 3.12 | main.py:15 |
| apt deps | build-essential, cmake, ninja-build, libcudnn8, libcudnn8-dev, git, gcc, g++ | main.py:17-20 |
| PyTorch | `torch==2.4.0` from `https://download.pytorch.org/whl/cu124` | main.py:25 |
| Evo 2 source | **unpinned** `git clone --recurse-submodules https://github.com/ArcInstitute/evo2.git` + `pip install .` | main.py:25 |
| Transformer Engine | uninstall then `transformer_engine[pytorch]==1.13 --no-build-isolation` | main.py:26-27 |
| FlashAttention | force-reinstall wheel `flash_attn-2.6.3+cu123torch2.4cxx11abiFALSE-cp312` | main.py:28 |
| GPU | `gpu="H100"` (non-strict) | main.py:39, 289 |
| Container policy | `max_containers=3, retries=2, scaledown_window=120`, `timeout=1000` (function) | main.py:39, 289 |
| Model cache | `modal.Volume.from_name("hf_cache")` mounted at `/root/.cache/huggingface` | main.py:35-36 |
| Misc | `torch.serialization.add_safe_globals([_codecs.encode])` wrapped in try/except | main.py:295-299 |

Note the wheel is a **cu123** wheel installed on a **cu124** torch — another sign of
version drift. None of these versions are recorded in a lock/constraints file.

## 4. Unpinned upstream clone and checkpoint ambiguity

- The evo2 package is cloned from `main` at image-build time with **no commit, tag,
  or release pin** (main.py:25). Rebuilding the image later can silently change model
  code and behavior.
- The model is referenced only as the string `'evo2_7b'` (main.py:57, 301). There is
  no recorded checkpoint hash, no HF revision, no official self-test result.
- `.gitmodules` declares `evo2-backend/evo2` → ArcInstitute/evo2, but the submodule
  is absent from the snapshot; the image build re-clones independently. Two
  different mechanisms point at the same upstream with no shared pin.

**Consequence:** model/checkpoint identity cannot be established from this codebase.
This is a stop-condition class issue (master prompt §16) and is resolved only by
Milestones 49/51 (parity spec + pinned clean environment).

## 5. Network calls made during inference

| Call | Location | Timeout | Retry | Provenance |
|---|---|---|---|---|
| UCSC `getData/sequence` | main.py:235-236 (`requests.get(api_url)`) | **none** | **none** | none |
| (client demo) POST to own web_url | main.py:373 | via requests default | none | none |

The evaluator (`evaluation/evaluate_modal_endpoint.py:138`) does set
`timeout=args.timeout` (default 180 s), but the production inference path itself has
no timeout on the UCSC call — a hung UCSC response would hold an H100 container.

## 6. Missing engineering properties

- **Timeouts/retries:** none on the inference-path UCSC call; Modal `retries=2` at
  container level only (retries the whole cold start, not the HTTP fetch).
- **Provenance fields:** the response contains no model/checkpoint identity, no
  sequence hashes, no window coordinates, no run ID, no software versions.
- **Batch semantics:** endpoint scores exactly one variant per request; two separate
  `score_sequences` calls (ref, alt) with no batching; no RC orientation at all.
- **Failure taxonomy:** any exception surfaces as a raw HTTP 500; no failure codes,
  no permanent-vs-transient distinction, no retained failure rows.
- **Input validation:** `VariantRequest` validates types only; no check that
  `alternative` ∈ {A,C,G,T}, no check that `alt != ref`, no chromosome whitelist, no
  position range check, no assembly verification. The reference base is read from the
  fetched window but never validated against a declared reference allele (the request
  does not carry one).
- **Determinism/reproducibility:** no seeds, no registered runs, no output hashes.
- **Cost control:** `max_containers=3` H100 with an unauthenticated public FastAPI
  endpoint — anyone with the URL can spend GPU budget.

## 7. Why the monolithic backend cannot be final research infrastructure

1. Scientific semantics are entangled with Modal transport and deprecated policy, so
   none of window/mutation/scoring can be unit-tested without GPUs or network.
2. Model identity is unpinned and unverifiable.
3. The inference path depends on live UCSC (non-reproducible, unversioned sequence).
4. No provenance, no failure retention, no batch/resume semantics — all required for
   a 1,024-variant frozen scoring run.
5. The compatibility patch is an unverified workaround whose necessity is unproven
   against current official Evo 2 requirements.
6. No reverse-complement path exists, while the frozen protocol requires
   `delta_primary = (delta_fwd + delta_rc) / 2` with all raw components retained.

## 8. Compatibility patches copied forward: NONE

No patch code has been copied into any new module. The new architecture will start
from the official light-install path and add a patch only if a documented upstream
issue at execution time requires it (Milestone 51 gate: patch count must be zero
unless justified).
